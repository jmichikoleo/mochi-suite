"""Watchlist tracker — K-dramas, anime, movies, TV shows."""

import json
import uuid
from datetime import date
from pathlib import Path

import requests
from bs4 import BeautifulSoup


def load_watchlist(data_path: str) -> dict:
    path = Path(data_path)
    if not path.exists():
        return {"items": []}
    with open(path) as f:
        return json.load(f)


def save_watchlist(data_path: str, data: dict):
    with open(data_path, "w") as f:
        json.dump(data, f, indent=2)


def add_item(data_path: str, title: str, media_type: str = "kdrama",
             status: str = "watching", rating: int = 0, episodes_total: int = 0,
             episodes_watched: int = 0, notes: str = "", url: str = "",
             thumbnail: str = "") -> str:
    data = load_watchlist(data_path)
    wid = str(uuid.uuid4())[:8]

    # Try to fetch thumbnail if URL provided and no thumbnail
    if url and not thumbnail:
        thumbnail = _fetch_poster(url)

    data["items"].insert(0, {
        "id": wid,
        "title": title,
        "type": media_type,
        "status": status,
        "rating": rating,
        "episodes_total": episodes_total,
        "episodes_watched": episodes_watched,
        "notes": notes,
        "url": url,
        "thumbnail": thumbnail,
        "added_date": date.today().isoformat(),
    })
    save_watchlist(data_path, data)
    return wid


def update_item(data_path: str, wid: str, updates: dict) -> bool:
    data = load_watchlist(data_path)
    for item in data["items"]:
        if item["id"] == wid:
            item.update(updates)
            # Auto-set status to "completed" if episodes match
            if item.get("episodes_watched") and item.get("episodes_total"):
                if item["episodes_watched"] >= item["episodes_total"]:
                    item["status"] = "completed"
            save_watchlist(data_path, data)
            return True
    return False


def delete_item(data_path: str, wid: str) -> bool:
    data = load_watchlist(data_path)
    n = len(data["items"])
    data["items"] = [i for i in data["items"] if i.get("id") != wid]
    if len(data["items"]) < n:
        save_watchlist(data_path, data)
        return True
    return False


def get_by_status(data_path: str, status: str = None) -> dict:
    data = load_watchlist(data_path)
    items = data["items"]
    if status:
        items = [i for i in items if i.get("status") == status]

    by_status = {"watching": [], "plan_to_watch": [], "completed": [], "dropped": []}
    for i in data["items"]:
        s = i.get("status", "plan_to_watch")
        by_status.setdefault(s, []).append(i)

    return {"items": items, "by_status": by_status,
            "total": len(data["items"]),
            "watching": len(by_status.get("watching", [])),
            "completed": len(by_status.get("completed", []))}


def _fetch_poster(url: str) -> str:
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; MochiBot/1.0)"}
        r = requests.get(url, headers=headers, timeout=8)
        soup = BeautifulSoup(r.text, "html.parser")
        og = soup.find("meta", property="og:image")
        return og["content"] if og and og.get("content") else ""
    except Exception:
        return ""
