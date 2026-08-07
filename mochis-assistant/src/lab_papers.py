"""Lab paper library — upload PDFs or paste links, organize by project/tags."""

import json
import uuid
import os
import shutil
from datetime import date
from pathlib import Path

import requests
from bs4 import BeautifulSoup


def load_papers(data_path: str) -> dict:
    path = Path(data_path)
    if not path.exists():
        return {"papers": [], "projects": ["General"]}
    with open(path) as f:
        return json.load(f)


def save_papers(data_path: str, data: dict):
    with open(data_path, "w") as f:
        json.dump(data, f, indent=2)


def fetch_paper_metadata(url: str) -> dict:
    """Auto-fetch title, authors, abstract from a paper URL."""
    try:
        # Convert arXiv PDF URLs to abstract page URLs for proper metadata
        fetch_url = url
        if "arxiv.org/pdf/" in url:
            arxiv_id = url.split("/pdf/")[-1].replace(".pdf", "")
            fetch_url = f"https://arxiv.org/abs/{arxiv_id}"
        elif "arxiv.org/pdf" in url:
            fetch_url = url.replace("/pdf", "/abs")

        headers = {"User-Agent": "Mozilla/5.0 (compatible; MochiBot/1.0)"}
        r = requests.get(fetch_url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        # ArXiv special handling
        if "arxiv.org" in fetch_url or "arxiv.org" in url:
            title_tag = soup.find("h1", class_="title")
            title = title_tag.get_text().replace("Title:", "").strip() if title_tag else ""
            abstract_tag = soup.find("blockquote", class_="abstract")
            abstract = abstract_tag.get_text().replace("Abstract:", "").strip() if abstract_tag else ""
            authors_tag = soup.find("div", class_="authors")
            authors = [a.get_text().strip() for a in authors_tag.find_all("a")] if authors_tag else []
            year_tag = soup.find("div", class_="dateline")
            year = ""
            if year_tag:
                text = year_tag.get_text()
                import re
                m = re.search(r"(\d{4})", text)
                if m:
                    year = m.group(1)
            # Build PDF URL if we have abs URL
            pdf_url = url if "/pdf/" in url else fetch_url.replace("/abs/", "/pdf/")
            return {"title": title, "authors": authors, "abstract": abstract[:500], "year": year,
                    "abs_url": fetch_url, "pdf_url": pdf_url}

        # Generic: use og tags
        def og(prop):
            tag = soup.find("meta", property=f"og:{prop}") or soup.find("meta", attrs={"name": f"og:{prop}"})
            return tag["content"].strip() if tag and tag.get("content") else ""

        title = og("title") or (soup.title.string.strip() if soup.title and soup.title.string else url)
        description = og("description")
        author_tag = soup.find("meta", attrs={"name": "author"})
        authors = [author_tag["content"]] if author_tag and author_tag.get("content") else []

        return {"title": title, "authors": authors, "abstract": description[:500], "year": ""}
    except Exception:
        return {"title": url, "authors": [], "abstract": "", "year": ""}


def add_paper(data_path: str, url: str = "", pdf_path: str = None,
              metadata: dict = None, project: str = "General", tags: list = None) -> str:
    data = load_papers(data_path)
    pid = str(uuid.uuid4())[:8]

    if metadata is None and url:
        metadata = fetch_paper_metadata(url)

    metadata = metadata or {}

    paper = {
        "id": pid,
        "title": metadata.get("title", url or "Untitled"),
        "authors": metadata.get("authors", []),
        "abstract": metadata.get("abstract", ""),
        "url": metadata.get("abs_url", url),
        "pdf_url": metadata.get("pdf_url", url if "/pdf/" in (url or "") else ""),
        "pdf_path": pdf_path,
        "year": metadata.get("year", ""),
        "tags": tags or [],
        "project": project,
        "status": "unread",
        "added_date": date.today().isoformat(),
        "notes": [],
        "highlights": [],
        "rating": 0,
    }

    data["papers"].insert(0, paper)
    if project and project not in data.get("projects", []):
        data.setdefault("projects", []).append(project)

    save_papers(data_path, data)
    return pid


def update_paper(data_path: str, pid: str, updates: dict) -> bool:
    data = load_papers(data_path)
    for p in data["papers"]:
        if p["id"] == pid:
            p.update(updates)
            save_papers(data_path, data)
            return True
    return False


def delete_paper(data_path: str, pid: str) -> bool:
    data = load_papers(data_path)
    n = len(data["papers"])
    # Also delete PDF if exists
    for p in data["papers"]:
        if p["id"] == pid and p.get("pdf_path"):
            try:
                os.remove(p["pdf_path"])
            except OSError:
                pass
    data["papers"] = [p for p in data["papers"] if p["id"] != pid]
    if len(data["papers"]) < n:
        save_papers(data_path, data)
        return True
    return False


def add_note_to_paper(data_path: str, pid: str, note: dict) -> bool:
    data = load_papers(data_path)
    for p in data["papers"]:
        if p["id"] == pid:
            note["id"] = str(uuid.uuid4())[:8]
            note["created"] = date.today().isoformat()
            p.setdefault("notes", []).append(note)
            save_papers(data_path, data)
            return True
    return False


def add_highlight(data_path: str, pid: str, highlight: dict) -> bool:
    data = load_papers(data_path)
    for p in data["papers"]:
        if p["id"] == pid:
            highlight["id"] = str(uuid.uuid4())[:8]
            p.setdefault("highlights", []).append(highlight)
            save_papers(data_path, data)
            return True
    return False


def get_connections(data_path: str) -> dict:
    """Build connections graph: papers by shared tags, authors."""
    data = load_papers(data_path)
    papers = data["papers"]

    by_tag = {}
    by_author = {}
    for p in papers:
        for tag in p.get("tags", []):
            by_tag.setdefault(tag, []).append({"id": p["id"], "title": p["title"]})
        for author in p.get("authors", []):
            by_author.setdefault(author, []).append({"id": p["id"], "title": p["title"]})

    # Find related pairs
    related = []
    for tag, tag_papers in by_tag.items():
        if len(tag_papers) > 1:
            related.append({"type": "tag", "label": tag, "papers": tag_papers})

    for author, auth_papers in by_author.items():
        if len(auth_papers) > 1:
            related.append({"type": "author", "label": author, "papers": auth_papers})

    return {"by_tag": by_tag, "by_author": by_author, "related": related}


def search_papers(data_path: str, query: str) -> list:
    data = load_papers(data_path)
    q = query.lower()
    return [p for p in data["papers"]
            if q in p.get("title", "").lower()
            or q in p.get("abstract", "").lower()
            or q in " ".join(p.get("tags", [])).lower()
            or q in " ".join(p.get("authors", [])).lower()]


def get_lab_meeting_prep(data_path: str, days: int = 7) -> dict:
    """Generate lab meeting prep from papers read this week."""
    from datetime import timedelta
    data = load_papers(data_path)
    cutoff = (date.today() - timedelta(days=days)).isoformat()

    recent_read = []
    for p in data["papers"]:
        if p.get("status") == "done" and p.get("added_date", "") >= cutoff:
            recent_read.append({
                "title": p["title"],
                "authors": p.get("authors", []),
                "notes": p.get("notes", []),
                "tags": p.get("tags", []),
            })

    recent_added = [p for p in data["papers"] if p.get("added_date", "") >= cutoff]

    return {
        "papers_read": len(recent_read),
        "papers_added": len(recent_added),
        "read_details": recent_read,
        "summary": f"Read {len(recent_read)} papers, added {len(recent_added)} to library this week.",
    }
