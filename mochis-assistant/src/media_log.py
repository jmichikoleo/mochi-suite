"""Media consumption log with auto-fetch metadata."""

import json
import re
import uuid
from datetime import date
from pathlib import Path

import requests
from bs4 import BeautifulSoup


def load_media(data_path: str) -> dict:
    path = Path(data_path)
    if not path.exists():
        return {"entries": []}
    with open(path) as f:
        return json.load(f)


def save_media(data_path: str, data: dict):
    with open(data_path, "w") as f:
        json.dump(data, f, indent=2)


def detect_source_type(url: str) -> str:
    url_lower = url.lower()
    if "youtube.com" in url_lower or "youtu.be" in url_lower:
        return "youtube"
    if "substack.com" in url_lower:
        return "substack"
    if "goodreads.com" in url_lower:
        return "goodreads"
    if "netflix.com" in url_lower:
        return "netflix"
    if "doi.org" in url_lower or "arxiv.org" in url_lower:
        return "journal"
    if "scholar.google" in url_lower:
        return "journal"
    return "other"


def fetch_metadata(url: str) -> dict:
    """Fetch metadata from a URL. Returns title, thumbnail, author, description."""
    source_type = detect_source_type(url)

    if source_type == "youtube":
        return _fetch_youtube(url)

    # For everything else, use og:tags
    return _fetch_og_tags(url, source_type)


def _fetch_youtube(url: str) -> dict:
    """Use YouTube oEmbed API."""
    try:
        oembed_url = f"https://www.youtube.com/oembed?url={url}&format=json"
        r = requests.get(oembed_url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            # Build thumbnail URL from video ID
            video_id = ""
            if "v=" in url:
                video_id = url.split("v=")[1].split("&")[0]
            elif "youtu.be/" in url:
                video_id = url.split("youtu.be/")[1].split("?")[0]
            thumb = f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg" if video_id else data.get("thumbnail_url", "")
            return {
                "title": data.get("title", ""),
                "author": data.get("author_name", ""),
                "thumbnail_url": thumb,
                "description": "",
                "type": "youtube",
            }
    except Exception:
        pass
    return {"title": url, "author": "", "thumbnail_url": "", "description": "", "type": "youtube"}


def _fetch_og_tags(url: str, source_type: str) -> dict:
    """Fetch Open Graph meta tags from any URL."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; MochiBot/1.0)"}
        r = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        soup = BeautifulSoup(r.text, "html.parser")

        def og(prop):
            tag = soup.find("meta", property=f"og:{prop}") or soup.find("meta", attrs={"name": f"og:{prop}"})
            return tag["content"] if tag and tag.get("content") else ""

        title = og("title") or (soup.title.string if soup.title else url)
        image = og("image")
        description = og("description")
        author = ""

        # Try to find author
        author_tag = soup.find("meta", attrs={"name": "author"}) or soup.find("meta", property="article:author")
        if author_tag and author_tag.get("content"):
            author = author_tag["content"]

        return {
            "title": title.strip() if title else url,
            "author": author,
            "thumbnail_url": image,
            "description": description[:200] if description else "",
            "type": source_type,
        }
    except Exception:
        return {"title": url, "author": "", "thumbnail_url": "", "description": "", "type": source_type}


def add_entry(data_path: str, link: str, metadata: dict, notes: str = "", rating: int = 0) -> str:
    data = load_media(data_path)
    entry_id = str(uuid.uuid4())[:8]
    entry = {
        "id": entry_id,
        "date": date.today().isoformat(),
        "type": metadata.get("type", "other"),
        "title": metadata.get("title", link),
        "thumbnail_url": metadata.get("thumbnail_url", ""),
        "author": metadata.get("author", ""),
        "description": metadata.get("description", ""),
        "link": link,
        "notes": notes,
        "rating": rating,
    }
    data["entries"].insert(0, entry)
    save_media(data_path, data)
    return entry_id


def delete_entry(data_path: str, entry_id: str) -> bool:
    data = load_media(data_path)
    original = len(data["entries"])
    data["entries"] = [e for e in data["entries"] if e.get("id") != entry_id]
    if len(data["entries"]) < original:
        save_media(data_path, data)
        return True
    return False


def update_entry(data_path: str, entry_id: str, updates: dict) -> bool:
    data = load_media(data_path)
    for e in data["entries"]:
        if e.get("id") == entry_id:
            e.update(updates)
            save_media(data_path, data)
            return True
    return False
