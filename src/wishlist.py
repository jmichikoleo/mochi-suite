"""Wish list / shopping list tracker."""

import json
import uuid
from datetime import date
from pathlib import Path

import requests
from bs4 import BeautifulSoup


def load_wishlist(data_path: str) -> dict:
    path = Path(data_path)
    if not path.exists():
        return {"items": []}
    with open(path) as f:
        return json.load(f)


def save_wishlist(data_path: str, data: dict):
    with open(data_path, "w") as f:
        json.dump(data, f, indent=2)


def add_item(data_path: str, title: str, price: int = 0, url: str = "",
             category: str = "general", notes: str = "", priority: str = "want") -> str:
    data = load_wishlist(data_path)
    wid = str(uuid.uuid4())[:8]

    thumbnail = ""
    if url:
        try:
            headers = {"User-Agent": "Mozilla/5.0 (compatible; MochiBot/1.0)"}
            r = requests.get(url, headers=headers, timeout=8)
            soup = BeautifulSoup(r.text, "html.parser")
            og = soup.find("meta", property="og:image")
            if og and og.get("content"):
                thumbnail = og["content"]
            # Auto-fill title from page if empty
            if not title:
                og_title = soup.find("meta", property="og:title")
                title = og_title["content"] if og_title and og_title.get("content") else (soup.title.string if soup.title else url)
        except Exception:
            pass

    data["items"].insert(0, {
        "id": wid,
        "title": title or url,
        "price": price,
        "url": url,
        "thumbnail": thumbnail,
        "category": category,
        "notes": notes,
        "priority": priority,
        "purchased": False,
        "added_date": date.today().isoformat(),
    })
    save_wishlist(data_path, data)
    return wid


def update_item(data_path: str, wid: str, updates: dict) -> bool:
    data = load_wishlist(data_path)
    for item in data["items"]:
        if item["id"] == wid:
            item.update(updates)
            save_wishlist(data_path, data)
            return True
    return False


def delete_item(data_path: str, wid: str) -> bool:
    data = load_wishlist(data_path)
    n = len(data["items"])
    data["items"] = [i for i in data["items"] if i.get("id") != wid]
    if len(data["items"]) < n:
        save_wishlist(data_path, data)
        return True
    return False


def toggle_purchased(data_path: str, wid: str) -> bool:
    data = load_wishlist(data_path)
    for item in data["items"]:
        if item["id"] == wid:
            item["purchased"] = not item.get("purchased", False)
            save_wishlist(data_path, data)
            return item["purchased"]
    return False


def get_summary(data_path: str) -> dict:
    data = load_wishlist(data_path)
    items = data["items"]
    unpurchased = [i for i in items if not i.get("purchased")]
    total_cost = sum(i.get("price", 0) for i in unpurchased)
    return {"items": items, "unpurchased_count": len(unpurchased),
            "total_cost": total_cost, "total_items": len(items)}
