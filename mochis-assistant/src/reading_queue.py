"""Reading queue — prioritized reading list with status tracking."""

import json
import uuid
from datetime import date
from pathlib import Path


def load_queue(data_path: str) -> dict:
    path = Path(data_path)
    if not path.exists():
        return {"items": []}
    with open(path) as f:
        return json.load(f)


def save_queue(data_path: str, data: dict):
    with open(data_path, "w") as f:
        json.dump(data, f, indent=2)


def add_item(data_path: str, item: dict) -> str:
    data = load_queue(data_path)
    iid = str(uuid.uuid4())[:8]
    item["id"] = iid
    item.setdefault("status", "unread")
    item.setdefault("added_date", date.today().isoformat())
    item.setdefault("priority", len(data["items"]) + 1)
    data["items"].append(item)
    save_queue(data_path, data)
    return iid


def delete_item(data_path: str, item_id: str) -> bool:
    data = load_queue(data_path)
    n = len(data["items"])
    data["items"] = [i for i in data["items"] if i.get("id") != item_id]
    if len(data["items"]) < n:
        save_queue(data_path, data)
        return True
    return False


def update_status(data_path: str, item_id: str, status: str) -> bool:
    data = load_queue(data_path)
    for item in data["items"]:
        if item["id"] == item_id:
            item["status"] = status
            if status == "done":
                item["completed_date"] = date.today().isoformat()
            save_queue(data_path, data)
            return True
    return False


def get_queue_summary(data_path: str) -> dict:
    data = load_queue(data_path)
    items = data["items"]
    by_status = {"unread": 0, "reading": 0, "done": 0}
    total_time = 0
    for i in items:
        st = i.get("status", "unread")
        by_status[st] = by_status.get(st, 0) + 1
        if st != "done":
            total_time += i.get("est_read_min", 0)

    # Sort: reading first, then unread by priority, then done
    status_order = {"reading": 0, "unread": 1, "done": 2}
    sorted_items = sorted(items, key=lambda x: (status_order.get(x.get("status", "unread"), 1), x.get("priority", 99)))

    return {
        "items": sorted_items,
        "counts": by_status,
        "total_remaining_min": total_time,
    }
