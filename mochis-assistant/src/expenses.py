"""Quick expense tracker with categories and monthly analytics."""

import json
import uuid
from datetime import date, timedelta
from pathlib import Path
from collections import defaultdict


def load_expenses(data_path: str) -> dict:
    path = Path(data_path)
    if not path.exists():
        return {"entries": [], "categories": ["food", "transport", "coffee", "shopping", "entertainment", "groceries", "other"]}
    with open(path) as f:
        return json.load(f)


def save_expenses(data_path: str, data: dict):
    with open(data_path, "w") as f:
        json.dump(data, f, indent=2)


def add_expense(data_path: str, amount: int, category: str, description: str = "", expense_date: str = None) -> str:
    data = load_expenses(data_path)
    eid = str(uuid.uuid4())[:8]
    data["entries"].insert(0, {
        "id": eid,
        "date": expense_date or date.today().isoformat(),
        "amount": amount,
        "category": category,
        "description": description,
    })
    if category and category not in data.get("categories", []):
        data.setdefault("categories", []).append(category)
    save_expenses(data_path, data)
    return eid


def delete_expense(data_path: str, eid: str) -> bool:
    data = load_expenses(data_path)
    n = len(data["entries"])
    data["entries"] = [e for e in data["entries"] if e.get("id") != eid]
    if len(data["entries"]) < n:
        save_expenses(data_path, data)
        return True
    return False


def get_daily_summary(data_path: str, target_date: str = None) -> dict:
    data = load_expenses(data_path)
    target = target_date or date.today().isoformat()
    day_entries = [e for e in data["entries"] if e.get("date") == target]
    total = sum(e.get("amount", 0) for e in day_entries)
    by_cat = defaultdict(int)
    for e in day_entries:
        by_cat[e.get("category", "other")] += e.get("amount", 0)
    return {"date": target, "entries": day_entries, "total": total, "by_category": dict(by_cat)}


def get_monthly_summary(data_path: str, year: int = None, month: int = None) -> dict:
    data = load_expenses(data_path)
    today = date.today()
    year = year or today.year
    month = month or today.month
    month_str = f"{year}-{month:02d}"

    month_entries = [e for e in data["entries"] if e.get("date", "").startswith(month_str)]
    total = sum(e.get("amount", 0) for e in month_entries)
    by_cat = defaultdict(int)
    by_day = defaultdict(int)
    for e in month_entries:
        by_cat[e.get("category", "other")] += e.get("amount", 0)
        by_day[e.get("date", "")] += e.get("amount", 0)

    sorted_cats = sorted(by_cat.items(), key=lambda x: x[1], reverse=True)

    return {
        "year": year, "month": month,
        "total": total,
        "by_category": dict(sorted_cats),
        "by_day": dict(sorted(by_day.items())),
        "entry_count": len(month_entries),
        "daily_avg": round(total / max(1, len(by_day))),
        "categories": data.get("categories", []),
    }
