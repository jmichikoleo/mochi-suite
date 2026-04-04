"""Mood tracking and daily journal."""

import json
from datetime import date, timedelta
from pathlib import Path


def load_journal(data_path: str) -> dict:
    path = Path(data_path)
    if not path.exists():
        return {"entries": []}
    with open(path) as f:
        return json.load(f)


def save_journal(data_path: str, data: dict):
    with open(data_path, "w") as f:
        json.dump(data, f, indent=2)


def get_entry(data_path: str, date_str: str) -> dict:
    data = load_journal(data_path)
    for e in data["entries"]:
        if e["date"] == date_str:
            return e
    return None


def upsert_entry(data_path: str, date_str: str, mood: int, entry_text: str):
    data = load_journal(data_path)
    for e in data["entries"]:
        if e["date"] == date_str:
            e["mood"] = mood
            e["entry"] = entry_text
            save_journal(data_path, data)
            return
    data["entries"].append({"date": date_str, "mood": mood, "entry": entry_text})
    data["entries"].sort(key=lambda e: e["date"], reverse=True)
    save_journal(data_path, data)


def get_mood_trend(data_path: str, days: int = 7) -> list:
    data = load_journal(data_path)
    today = date.today()
    trend = []
    for i in range(days):
        d = (today - timedelta(days=i)).isoformat()
        mood = None
        for e in data["entries"]:
            if e["date"] == d:
                mood = e.get("mood")
                break
        trend.append({"date": d, "mood": mood})
    return trend


def get_recent_entries(data_path: str, limit: int = 10) -> list:
    data = load_journal(data_path)
    entries = sorted(data["entries"], key=lambda e: e["date"], reverse=True)
    return entries[:limit]
