"""Food intake logging and daily kcal tracking."""

import json
from datetime import date
from pathlib import Path


def load_food_log(data_path: str) -> dict:
    path = Path(data_path)
    if not path.exists():
        return {"entries": {}}
    with open(path) as f:
        return json.load(f)


def save_food_log(data_path: str, data: dict):
    with open(data_path, "w") as f:
        json.dump(data, f, indent=2)


def get_day_entries(data_path: str, date_str: str = None) -> list:
    date_str = date_str or date.today().isoformat()
    data = load_food_log(data_path)
    return data.get("entries", {}).get(date_str, [])


def get_daily_total(entries: list) -> int:
    return sum(e.get("kcal_estimate", 0) for e in entries)


def add_entry(data_path: str, date_str: str, entry: dict):
    data = load_food_log(data_path)
    data.setdefault("entries", {}).setdefault(date_str, []).append(entry)
    save_food_log(data_path, data)


def delete_entry(data_path: str, date_str: str, index: int) -> bool:
    data = load_food_log(data_path)
    entries = data.get("entries", {}).get(date_str, [])
    if 0 <= index < len(entries):
        entries.pop(index)
        save_food_log(data_path, data)
        return True
    return False


def get_food_summary(data_path: str, date_str: str = None) -> dict:
    date_str = date_str or date.today().isoformat()
    entries = get_day_entries(data_path, date_str)
    total = get_daily_total(entries)
    by_meal = {}
    for e in entries:
        meal = e.get("meal", "other")
        by_meal.setdefault(meal, []).append(e)
    return {
        "date": date_str,
        "entries": entries,
        "total_kcal": total,
        "by_meal": by_meal,
        "meal_count": len(entries),
    }
