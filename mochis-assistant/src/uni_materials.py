"""University materials library — organize files and links per class."""

import json
import uuid
import os
from datetime import date
from pathlib import Path


def load_materials(data_path: str) -> dict:
    path = Path(data_path)
    if not path.exists():
        return {"materials": []}
    with open(path) as f:
        return json.load(f)


def save_materials(data_path: str, data: dict):
    with open(data_path, "w") as f:
        json.dump(data, f, indent=2)


def add_material(data_path: str, course_id: str, title: str,
                 material_type: str = "link", url: str = "",
                 file_path: str = None, folder: str = "general") -> str:
    data = load_materials(data_path)
    mid = str(uuid.uuid4())[:8]
    data["materials"].insert(0, {
        "id": mid,
        "course_id": course_id,
        "title": title,
        "type": material_type,
        "file_path": file_path,
        "url": url,
        "folder": folder,
        "added_date": date.today().isoformat(),
    })
    save_materials(data_path, data)
    return mid


def delete_material(data_path: str, mid: str) -> bool:
    data = load_materials(data_path)
    n = len(data["materials"])
    for m in data["materials"]:
        if m["id"] == mid and m.get("file_path"):
            try:
                os.remove(m["file_path"])
            except OSError:
                pass
    data["materials"] = [m for m in data["materials"] if m["id"] != mid]
    if len(data["materials"]) < n:
        save_materials(data_path, data)
        return True
    return False


def get_by_course(data_path: str, course_id: str) -> list:
    data = load_materials(data_path)
    return [m for m in data["materials"] if m.get("course_id") == course_id]


def search_materials(data_path: str, query: str) -> list:
    data = load_materials(data_path)
    q = query.lower()
    return [m for m in data["materials"] if q in m.get("title", "").lower()]
