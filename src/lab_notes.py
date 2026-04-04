"""Research notes — Zettelkasten-lite with paper linking."""

import json
import uuid
from datetime import date
from pathlib import Path


def load_notes(data_path: str) -> dict:
    path = Path(data_path)
    if not path.exists():
        return {"notes": []}
    with open(path) as f:
        return json.load(f)


def save_notes(data_path: str, data: dict):
    with open(data_path, "w") as f:
        json.dump(data, f, indent=2)


def add_note(data_path: str, title: str, content: str,
             linked_papers: list = None, tags: list = None) -> str:
    data = load_notes(data_path)
    nid = str(uuid.uuid4())[:8]
    data["notes"].insert(0, {
        "id": nid,
        "title": title,
        "content": content,
        "linked_papers": linked_papers or [],
        "tags": tags or [],
        "created": date.today().isoformat(),
        "updated": date.today().isoformat(),
    })
    save_notes(data_path, data)
    return nid


def update_note(data_path: str, nid: str, updates: dict) -> bool:
    data = load_notes(data_path)
    for n in data["notes"]:
        if n["id"] == nid:
            n.update(updates)
            n["updated"] = date.today().isoformat()
            save_notes(data_path, data)
            return True
    return False


def delete_note(data_path: str, nid: str) -> bool:
    data = load_notes(data_path)
    n_len = len(data["notes"])
    data["notes"] = [n for n in data["notes"] if n["id"] != nid]
    if len(data["notes"]) < n_len:
        save_notes(data_path, data)
        return True
    return False


def search_notes(data_path: str, query: str) -> list:
    data = load_notes(data_path)
    q = query.lower()
    return [n for n in data["notes"]
            if q in n.get("title", "").lower()
            or q in n.get("content", "").lower()
            or q in " ".join(n.get("tags", [])).lower()]


def get_connections(data_path: str, papers_path: str) -> dict:
    """Map notes to their linked papers."""
    notes = load_notes(data_path)
    from src.lab_papers import load_papers
    papers = load_papers(papers_path)

    paper_lookup = {p["id"]: p["title"] for p in papers.get("papers", [])}

    connections = []
    for note in notes["notes"]:
        for pid in note.get("linked_papers", []):
            if pid in paper_lookup:
                connections.append({
                    "note_id": note["id"],
                    "note_title": note["title"],
                    "paper_id": pid,
                    "paper_title": paper_lookup[pid],
                })

    return {"connections": connections, "total_notes": len(notes["notes"])}
