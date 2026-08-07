"""Bookmark manager — link dumps with folders, tags, and auto-metadata."""

import json
import uuid
from datetime import date
from pathlib import Path

import requests
from bs4 import BeautifulSoup


def load_bookmarks(data_path: str) -> dict:
    path = Path(data_path)
    if not path.exists():
        return {"bookmarks": [], "folders": ["General", "Research", "Articles", "Tools", "Inspiration"]}
    with open(path) as f:
        return json.load(f)


def save_bookmarks(data_path: str, data: dict):
    with open(data_path, "w") as f:
        json.dump(data, f, indent=2)


def fetch_link_meta(url: str) -> dict:
    """Fetch title, description, favicon from a URL."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; MochiBot/1.0)"}
        r = requests.get(url, headers=headers, timeout=8, allow_redirects=True)
        soup = BeautifulSoup(r.text, "html.parser")

        def og(prop):
            tag = soup.find("meta", property=f"og:{prop}") or soup.find("meta", attrs={"name": f"og:{prop}"})
            return tag["content"].strip() if tag and tag.get("content") else ""

        title = og("title") or (soup.title.string.strip() if soup.title and soup.title.string else url)
        description = og("description")
        image = og("image")

        # Favicon
        icon_tag = soup.find("link", rel=lambda r: r and "icon" in r)
        favicon = ""
        if icon_tag and icon_tag.get("href"):
            fav = icon_tag["href"]
            if fav.startswith("//"):
                favicon = "https:" + fav
            elif fav.startswith("/"):
                from urllib.parse import urlparse
                parsed = urlparse(url)
                favicon = f"{parsed.scheme}://{parsed.netloc}{fav}"
            elif fav.startswith("http"):
                favicon = fav
        if not favicon:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            favicon = f"{parsed.scheme}://{parsed.netloc}/favicon.ico"

        # Detect domain
        from urllib.parse import urlparse
        domain = urlparse(url).netloc.replace("www.", "")

        return {
            "title": title[:200] if title else url,
            "description": description[:300] if description else "",
            "image": image,
            "favicon": favicon,
            "domain": domain,
        }
    except Exception:
        from urllib.parse import urlparse
        domain = urlparse(url).netloc.replace("www.", "") if "://" in url else url
        return {"title": url, "description": "", "image": "", "favicon": "", "domain": domain}


def add_bookmark(data_path: str, url: str, metadata: dict = None,
                  folder: str = "General", tags: list = None, note: str = "") -> str:
    data = load_bookmarks(data_path)
    if metadata is None:
        metadata = fetch_link_meta(url)

    bid = str(uuid.uuid4())[:8]
    bookmark = {
        "id": bid,
        "url": url,
        "title": metadata.get("title", url),
        "description": metadata.get("description", ""),
        "favicon": metadata.get("favicon", ""),
        "image": metadata.get("image", ""),
        "domain": metadata.get("domain", ""),
        "folder": folder,
        "tags": tags or [],
        "note": note,
        "date": date.today().isoformat(),
        "pinned": False,
    }
    data["bookmarks"].insert(0, bookmark)

    # Ensure folder exists
    if folder and folder not in data.get("folders", []):
        data.setdefault("folders", []).append(folder)

    save_bookmarks(data_path, data)
    return bid


def update_bookmark(data_path: str, bid: str, updates: dict) -> bool:
    data = load_bookmarks(data_path)
    for b in data["bookmarks"]:
        if b["id"] == bid:
            b.update(updates)
            if "folder" in updates and updates["folder"] not in data.get("folders", []):
                data.setdefault("folders", []).append(updates["folder"])
            save_bookmarks(data_path, data)
            return True
    return False


def delete_bookmark(data_path: str, bid: str) -> bool:
    data = load_bookmarks(data_path)
    n = len(data["bookmarks"])
    data["bookmarks"] = [b for b in data["bookmarks"] if b["id"] != bid]
    if len(data["bookmarks"]) < n:
        save_bookmarks(data_path, data)
        return True
    return False


def toggle_pin(data_path: str, bid: str) -> bool:
    data = load_bookmarks(data_path)
    for b in data["bookmarks"]:
        if b["id"] == bid:
            b["pinned"] = not b.get("pinned", False)
            save_bookmarks(data_path, data)
            return b["pinned"]
    return False


def add_folder(data_path: str, name: str) -> bool:
    data = load_bookmarks(data_path)
    if name not in data.get("folders", []):
        data.setdefault("folders", []).append(name)
        save_bookmarks(data_path, data)
        return True
    return False


def search_bookmarks(data_path: str, query: str) -> list:
    data = load_bookmarks(data_path)
    q = query.lower()
    return [b for b in data["bookmarks"]
            if q in b.get("title", "").lower()
            or q in b.get("url", "").lower()
            or q in b.get("note", "").lower()
            or q in " ".join(b.get("tags", [])).lower()
            or q in b.get("domain", "").lower()]
