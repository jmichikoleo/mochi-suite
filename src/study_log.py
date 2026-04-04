"""Study session logger — track study hours per subject."""

import json
import uuid
from datetime import date, timedelta, datetime
from pathlib import Path


def load_study_log(data_path: str) -> dict:
    path = Path(data_path)
    if not path.exists():
        return {"sessions": []}
    with open(path) as f:
        return json.load(f)


def save_study_log(data_path: str, data: dict):
    with open(data_path, "w") as f:
        json.dump(data, f, indent=2)


def add_session(data_path: str, session: dict) -> str:
    data = load_study_log(data_path)
    sid = str(uuid.uuid4())[:8]
    session["id"] = sid
    session.setdefault("date", date.today().isoformat())
    session.setdefault("created_at", datetime.now().isoformat())
    data["sessions"].insert(0, session)
    save_study_log(data_path, data)
    return sid


def delete_session(data_path: str, session_id: str) -> bool:
    data = load_study_log(data_path)
    n = len(data["sessions"])
    data["sessions"] = [s for s in data["sessions"] if s.get("id") != session_id]
    if len(data["sessions"]) < n:
        save_study_log(data_path, data)
        return True
    return False


def get_weekly_summary(data_path: str) -> dict:
    """Get study hours per subject for current week."""
    data = load_study_log(data_path)
    today = date.today()
    week_start = today - timedelta(days=today.weekday())  # Monday

    by_subject = {}
    total_min = 0
    daily = {}

    for s in data["sessions"]:
        try:
            d = date.fromisoformat(s["date"])
        except (ValueError, KeyError):
            continue
        if d < week_start:
            continue

        subj = s.get("subject", "Other")
        dur = s.get("duration_min", 0)
        by_subject[subj] = by_subject.get(subj, 0) + dur
        total_min += dur
        day_key = s["date"]
        daily[day_key] = daily.get(day_key, 0) + dur

    return {
        "sessions": [s for s in data["sessions"] if s.get("date", "") >= week_start.isoformat()],
        "by_subject": dict(sorted(by_subject.items(), key=lambda x: x[1], reverse=True)),
        "total_hours": round(total_min / 60, 1),
        "total_min": total_min,
        "daily": daily,
    }
