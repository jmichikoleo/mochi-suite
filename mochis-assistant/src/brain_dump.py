"""Quick capture / brain dump — fast input that auto-categorizes."""

import json
import uuid
import re
from datetime import date
from pathlib import Path


def load_dump(data_path: str) -> dict:
    path = Path(data_path)
    if not path.exists():
        return {"items": []}
    with open(path) as f:
        return json.load(f)


def save_dump(data_path: str, data: dict):
    with open(data_path, "w") as f:
        json.dump(data, f, indent=2)


def auto_categorize(text: str) -> dict:
    """Detect what the quick capture should become."""
    lower = text.lower().strip()

    # Expense: has ₩ or 원 or a number pattern like "4500"
    money_match = re.search(r'(\d{3,})\s*(?:원|won|₩)?', lower)
    if money_match and any(w in lower for w in ['bought', 'spent', 'paid', '샀', '결제', '구매', 'buy']):
        amount = int(money_match.group(1))
        desc = re.sub(r'\d{3,}\s*(?:원|won|₩)?', '', text).strip()
        return {"type": "expense", "amount": amount, "description": desc}

    # Task: starts with task-like words
    if any(lower.startswith(w) for w in ['todo ', 'task ', 'do ', 'need to ', 'must ', 'should ', '해야', '할일']):
        cleaned = re.sub(r'^(todo|task|do|need to|must|should|해야|할일)\s*:?\s*', '', text, flags=re.IGNORECASE)
        return {"type": "task", "title": cleaned}

    # Wishlist: want/buy patterns
    if any(w in lower for w in ['want to buy', 'wish', 'i want', '사고싶', '갖고싶']):
        return {"type": "wishlist", "title": text}

    # Reminder
    if any(lower.startswith(w) for w in ['remind ', 'remember ', 'don\'t forget', '잊지마', '기억']):
        cleaned = re.sub(r'^(remind|remember|don\'t forget)\s*:?\s*', '', text, flags=re.IGNORECASE)
        return {"type": "reminder", "text": cleaned}

    # Default: brain dump
    return {"type": "brain_dump", "text": text}


def add_capture(data_path: str, text: str) -> dict:
    """Add a quick capture and return what it was categorized as."""
    categorized = auto_categorize(text)
    categorized["original_text"] = text
    categorized["date"] = date.today().isoformat()
    categorized["id"] = str(uuid.uuid4())[:8]
    categorized["processed"] = False

    data = load_dump(data_path)
    data["items"].insert(0, categorized)
    # Keep last 100
    data["items"] = data["items"][:100]
    save_dump(data_path, data)

    return categorized


def mark_processed(data_path: str, item_id: str):
    data = load_dump(data_path)
    for item in data["items"]:
        if item["id"] == item_id:
            item["processed"] = True
            save_dump(data_path, data)
            return True
    return False


def delete_item(data_path: str, item_id: str) -> bool:
    data = load_dump(data_path)
    n = len(data["items"])
    data["items"] = [i for i in data["items"] if i.get("id") != item_id]
    if len(data["items"]) < n:
        save_dump(data_path, data)
        return True
    return False


def get_unprocessed(data_path: str) -> list:
    data = load_dump(data_path)
    return [i for i in data["items"] if not i.get("processed")]
