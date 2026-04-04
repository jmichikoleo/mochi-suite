"""ArXiv paper search, tracking, and connection mapping."""

import json
import random
from datetime import date, datetime
from pathlib import Path

try:
    import arxiv
except ImportError:
    arxiv = None


def load_paper_history(data_path: str) -> dict:
    path = Path(data_path)
    if not path.exists():
        return {"read_papers": [], "topics_studied": [], "connections": [], "last_recommended": []}
    with open(path) as f:
        return json.load(f)


def save_paper_history(data_path: str, history: dict):
    with open(data_path, "w") as f:
        json.dump(history, f, indent=2)


def search_papers(queries: list, categories: list, history: dict, max_results: int = 2) -> list:
    """Search ArXiv for relevant papers, avoiding already-recommended ones."""
    if arxiv is None:
        return _fallback_papers()

    already_seen = set()
    for p in history.get("read_papers", []):
        already_seen.add(p.get("arxiv_id", ""))
    for p in history.get("last_recommended", []):
        already_seen.add(p.get("arxiv_id", ""))

    # Rotate through queries to get variety
    query = random.choice(queries)
    cat_filter = " OR ".join(f"cat:{c}" for c in categories)
    full_query = f"({query}) AND ({cat_filter})"

    client = arxiv.Client()
    search = arxiv.Search(
        query=full_query,
        max_results=20,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending,
    )

    papers = []
    try:
        for result in client.results(search):
            paper_id = result.entry_id.split("/")[-1]
            if paper_id in already_seen:
                continue

            papers.append({
                "arxiv_id": paper_id,
                "title": result.title,
                "authors": [a.name for a in result.authors[:3]],
                "abstract": result.summary[:300] + "..." if len(result.summary) > 300 else result.summary,
                "url": result.entry_id,
                "pdf_url": result.pdf_url,
                "published": result.published.strftime("%Y-%m-%d") if result.published else "",
                "categories": [c for c in result.categories],
                "search_query": query,
            })

            if len(papers) >= max_results:
                break
    except Exception as e:
        print(f"[Papers] ArXiv search error: {e}")
        return _fallback_papers()

    if len(papers) < max_results:
        # Try another query
        remaining = max_results - len(papers)
        other_queries = [q for q in queries if q != query]
        if other_queries:
            alt_query = random.choice(other_queries)
            full_query = f"({alt_query}) AND ({cat_filter})"
            search = arxiv.Search(
                query=full_query,
                max_results=10,
                sort_by=arxiv.SortCriterion.SubmittedDate,
            )
            try:
                for result in client.results(search):
                    paper_id = result.entry_id.split("/")[-1]
                    if paper_id in already_seen or any(p["arxiv_id"] == paper_id for p in papers):
                        continue
                    papers.append({
                        "arxiv_id": paper_id,
                        "title": result.title,
                        "authors": [a.name for a in result.authors[:3]],
                        "abstract": result.summary[:300] + "...",
                        "url": result.entry_id,
                        "pdf_url": result.pdf_url,
                        "published": result.published.strftime("%Y-%m-%d") if result.published else "",
                        "categories": [c for c in result.categories],
                        "search_query": alt_query,
                    })
                    if len(papers) >= max_results:
                        break
            except Exception as e:
                print(f"[Papers] ArXiv alt search error: {e}")

    return papers[:max_results]


def find_connections(new_papers: list, history: dict) -> list:
    """Find connections between new papers and previously read papers."""
    connections = []
    read_papers = history.get("read_papers", [])

    if not read_papers:
        return connections

    for new_paper in new_papers:
        new_authors = set(new_paper.get("authors", []))
        new_cats = set(new_paper.get("categories", []))
        new_title_words = set(new_paper.get("title", "").lower().split())

        for read_paper in read_papers:
            read_authors = set(read_paper.get("authors", []))
            read_cats = set(read_paper.get("categories", []))
            read_title_words = set(read_paper.get("title", "").lower().split())

            # Shared authors
            shared_authors = new_authors & read_authors
            if shared_authors:
                connections.append(
                    f"'{new_paper['title'][:50]}...' shares author(s) "
                    f"{', '.join(shared_authors)} with '{read_paper['title'][:50]}...'"
                )

            # Topic overlap via title keywords (excluding common words)
            stopwords = {"a", "an", "the", "of", "for", "in", "on", "to", "and", "with", "is", "are", "by"}
            meaningful_overlap = (new_title_words & read_title_words) - stopwords
            if len(meaningful_overlap) >= 2:
                connections.append(
                    f"'{new_paper['title'][:50]}...' is related to "
                    f"'{read_paper['title'][:50]}...' (shared topics: {', '.join(list(meaningful_overlap)[:3])})"
                )

    return connections


def suggest_next_topics(history: dict) -> list:
    """Suggest next research directions based on reading history."""
    topics_studied = history.get("topics_studied", [])
    read_papers = history.get("read_papers", [])

    # Topic adjacency map
    adjacency = {
        "LLM routing": ["load balancing", "expert selection", "adaptive computation"],
        "mixture of experts": ["sparse models", "conditional computation", "gating networks"],
        "inference optimization": ["quantization", "pruning", "knowledge distillation"],
        "AI agents": ["tool use", "multi-agent systems", "planning"],
        "transformer architecture": ["attention mechanisms", "positional encoding", "efficient transformers"],
    }

    suggestions = []
    for topic in topics_studied:
        related = adjacency.get(topic, [])
        for r in related:
            if r not in topics_studied:
                suggestions.append(f"Explore '{r}' (related to your study of '{topic}')")

    return suggestions[:3]


def get_paper_recommendations(data_path: str, search_queries: list, categories: list) -> dict:
    """Main entry point: get daily paper recommendations."""
    history = load_paper_history(data_path)

    papers = search_papers(search_queries, categories, history)
    connections = find_connections(papers, history)
    next_topics = suggest_next_topics(history)

    # Update history with today's recommendations (skip fallback entries)
    if papers and papers[0].get("arxiv_id") != "unavailable":
        history["last_recommended"] = papers
        save_paper_history(data_path, history)

    return {
        "papers": papers,
        "connections": connections,
        "next_topics": next_topics,
        "papers_read_total": len(history.get("read_papers", [])),
        "topics_studied": history.get("topics_studied", []),
    }


def mark_paper_read(data_path: str, arxiv_id: str, notes: str = "", key_findings: list = None):
    """Mark a paper as read and update history."""
    history = load_paper_history(data_path)

    # Find in last_recommended
    paper_data = None
    for p in history.get("last_recommended", []):
        if p["arxiv_id"] == arxiv_id:
            paper_data = p.copy()
            break

    if paper_data:
        paper_data["read_date"] = date.today().isoformat()
        paper_data["notes"] = notes
        paper_data["key_findings"] = key_findings or []
        history["read_papers"].append(paper_data)

    save_paper_history(data_path, history)


def _fallback_papers() -> list:
    """Return placeholder when ArXiv API is unavailable."""
    return [
        {
            "arxiv_id": "unavailable",
            "title": "[ArXiv API unavailable - install 'arxiv' package]",
            "authors": [],
            "abstract": "Run: pip install arxiv",
            "url": "https://arxiv.org",
            "pdf_url": "",
            "published": "",
            "categories": [],
            "search_query": "",
        }
    ]


def format_papers_section(paper_data: dict) -> str:
    """Format papers into a readable briefing section."""
    lines = []
    lines.append("## AI Paper Recommendations")
    lines.append("")
    lines.append(f"Papers read so far: {paper_data['papers_read_total']} | Topics: {', '.join(paper_data['topics_studied'])}")
    lines.append("")

    for i, paper in enumerate(paper_data["papers"], 1):
        lines.append(f"### Paper {i}: {paper['title']}")
        if paper["authors"]:
            lines.append(f"**Authors**: {', '.join(paper['authors'])}")
        if paper["published"]:
            lines.append(f"**Published**: {paper['published']}")
        lines.append(f"**Link**: {paper['url']}")
        if paper["pdf_url"]:
            lines.append(f"**PDF**: {paper['pdf_url']}")
        lines.append(f"\n{paper['abstract']}")
        lines.append("")

    if paper_data["connections"]:
        lines.append("### Research Connections")
        for c in paper_data["connections"]:
            lines.append(f"- {c}")
        lines.append("")

    if paper_data["next_topics"]:
        lines.append("### Suggested Next Topics")
        for t in paper_data["next_topics"]:
            lines.append(f"- {t}")
        lines.append("")

    return "\n".join(lines)
