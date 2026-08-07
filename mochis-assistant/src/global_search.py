"""Cross-reference global search across all data sources."""

import json
from pathlib import Path


def search_all(data_dir: str, query: str) -> dict:
    """Search across all data sources and return grouped results."""
    q = query.lower().strip()
    if not q:
        return {"results": [], "total": 0}

    results = []

    def _load(*parts):
        path = Path(data_dir).joinpath(*parts)
        if path.exists():
            with open(path) as f:
                return json.load(f)
        return {}

    def _match(text):
        return q in (text or "").lower()

    # Tasks
    tasks = _load("tasks.json")
    for t in tasks.get("tasks", []):
        if _match(t.get("title")) or _match(t.get("notes")):
            results.append({"source": "tasks", "icon": "✅", "title": t["title"],
                            "detail": t.get("notes", ""), "status": t.get("status", "")})

    # Reminders
    for r in tasks.get("reminders", []):
        if _match(r.get("text")):
            results.append({"source": "reminders", "icon": "🔔", "title": r["text"],
                            "detail": r.get("time", "")})

    # Journal
    journal = _load("journal.json")
    for e in journal.get("entries", []):
        if _match(e.get("entry")):
            results.append({"source": "journal", "icon": "📝", "title": f"Journal {e['date']}",
                            "detail": _snippet(e.get("entry", ""), q),
                            "date": e.get("date")})

    # Lab papers
    papers = _load("lab", "papers.json")
    for p in papers.get("papers", []):
        if _match(p.get("title")) or _match(p.get("abstract")) or any(_match(t) for t in p.get("tags", [])):
            results.append({"source": "papers", "icon": "📄", "title": p["title"],
                            "detail": _snippet(p.get("abstract", ""), q),
                            "url": p.get("url"), "id": p.get("id")})

    # Lab notes
    notes = _load("lab", "notes.json")
    for n in notes.get("notes", []):
        if _match(n.get("title")) or _match(n.get("content")):
            results.append({"source": "research_notes", "icon": "🔬", "title": n["title"],
                            "detail": _snippet(n.get("content", ""), q)})

    # Bookmarks
    bookmarks = _load("bookmarks.json")
    for b in bookmarks.get("bookmarks", []):
        if _match(b.get("title")) or _match(b.get("url")) or _match(b.get("note")) or any(_match(t) for t in b.get("tags", [])):
            results.append({"source": "bookmarks", "icon": "🔗", "title": b["title"],
                            "detail": b.get("note", ""), "url": b.get("url")})

    # Reading queue
    rq = _load("reading_queue.json")
    for i in rq.get("items", []):
        if _match(i.get("title")):
            results.append({"source": "reading", "icon": "📖", "title": i["title"],
                            "detail": f"{i.get('type','')} - {i.get('status','')}",
                            "url": i.get("url")})

    # Class notes
    cnotes = _load("uni", "class_notes.json")
    for n in cnotes.get("notes", []):
        if _match(n.get("title")) or _match(n.get("content")):
            results.append({"source": "class_notes", "icon": "🎓", "title": n.get("title", ""),
                            "detail": _snippet(n.get("content", ""), q),
                            "date": n.get("date")})

    # Materials
    mats = _load("uni", "materials.json")
    for m in mats.get("materials", []):
        if _match(m.get("title")):
            results.append({"source": "materials", "icon": "📁", "title": m["title"],
                            "detail": m.get("folder", ""), "url": m.get("url")})

    # Media log
    media = _load("media_log.json")
    for e in media.get("entries", []):
        if _match(e.get("title")) or _match(e.get("notes")):
            results.append({"source": "media", "icon": "🎬", "title": e["title"],
                            "detail": e.get("notes", ""), "url": e.get("link")})

    # Brain dump
    dump = _load("brain_dump.json")
    for i in dump.get("items", []):
        if _match(i.get("original_text")) or _match(i.get("text")):
            results.append({"source": "brain_dump", "icon": "🧠",
                            "title": i.get("original_text", i.get("text", "")),
                            "detail": i.get("type", "")})

    # Paper summaries
    sums = _load("paper_summaries.json")
    for s in sums.get("summaries", []):
        if _match(s.get("title")) or _match(s.get("problem")) or _match(s.get("idea")):
            results.append({"source": "paper_summaries", "icon": "📋", "title": s["title"],
                            "detail": _snippet(s.get("idea", ""), q),
                            "url": s.get("source_url")})

    # Recipes
    recipes = _load("recipes.json")
    for r in recipes.get("recipes", []):
        if _match(r.get("title")) or any(_match(t) for t in r.get("tags", [])):
            results.append({"source": "recipes", "icon": "🍱", "title": r["title"],
                            "detail": ", ".join(r.get("ingredients", [])[:5])})

    # Paper history
    ph = _load("paper_history.json")
    for p in ph.get("read_papers", []) + ph.get("last_recommended", []):
        if _match(p.get("title")) or _match(p.get("abstract")):
            if not any(r.get("title") == p.get("title") for r in results):
                results.append({"source": "paper_recs", "icon": "📚", "title": p["title"],
                                "detail": _snippet(p.get("abstract", ""), q),
                                "url": p.get("url")})

    return {"results": results, "total": len(results), "query": query}


def _snippet(text: str, query: str, length: int = 80) -> str:
    """Extract a snippet around the query match."""
    if not text:
        return ""
    lower = text.lower()
    idx = lower.find(query.lower())
    if idx == -1:
        return text[:length] + ("..." if len(text) > length else "")
    start = max(0, idx - 30)
    end = min(len(text), idx + len(query) + 50)
    snippet = ("..." if start > 0 else "") + text[start:end] + ("..." if end < len(text) else "")
    return snippet
