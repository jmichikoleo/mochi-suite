"""Schedule management — classes, meetings, personal plans."""

import json
import uuid
from datetime import date
from pathlib import Path


def load_schedules(data_path: str) -> list:
    path = Path(data_path)
    if not path.exists():
        return []
    with open(path) as f:
        data = json.load(f)
    return data.get("schedules", [])


def get_today_schedules(data_path: str, target_date: str = None) -> list:
    target = target_date or date.today().isoformat()
    schedules = load_schedules(data_path)
    day_schedules = [s for s in schedules if s.get("date") == target]
    day_schedules.sort(key=lambda s: s.get("time_start", ""))
    return day_schedules


def get_month_data(data_path: str, tasks_data: dict, year: int, month: int) -> dict:
    """Return a dict of day -> {tasks: [...], schedules: [...]} for calendar."""
    import calendar
    schedules = load_schedules(data_path)
    tasks = tasks_data.get("tasks", [])

    month_str = f"{year}-{month:02d}"
    days = {}

    num_days = calendar.monthrange(year, month)[1]
    for d in range(1, num_days + 1):
        date_str = f"{month_str}-{d:02d}"
        day_tasks = [t for t in tasks if t.get("deadline", "").startswith(date_str) and t.get("status") != "done"]
        day_schedules = [s for s in schedules if s.get("date") == date_str]
        if day_tasks or day_schedules:
            days[d] = {"tasks": len(day_tasks), "schedules": len(day_schedules), "items": day_tasks + day_schedules}

    return {"year": year, "month": month, "days": days, "num_days": num_days,
            "first_weekday": calendar.monthrange(year, month)[0]}


def add_schedule(data_path: str, schedule: dict) -> str:
    path = Path(data_path)
    data = json.load(open(path)) if path.exists() else {"tasks": [], "reminders": [], "schedules": []}
    sid = str(uuid.uuid4())[:8]
    schedule["id"] = sid
    data.setdefault("schedules", []).append(schedule)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    return sid


def delete_schedule(data_path: str, schedule_id: str) -> bool:
    path = Path(data_path)
    data = json.load(open(path))
    original = len(data.get("schedules", []))
    data["schedules"] = [s for s in data.get("schedules", []) if s.get("id") != schedule_id]
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    return len(data["schedules"]) < original


def detect_commute_needs(day_schedules: list, commute_minutes: int = 30) -> list:
    """Detect when consecutive events are at different locations and flag commute time needed."""
    if len(day_schedules) < 2:
        return []

    sorted_scheds = sorted(day_schedules, key=lambda s: s.get("time_start", ""))
    warnings = []

    for i in range(len(sorted_scheds) - 1):
        curr = sorted_scheds[i]
        next_s = sorted_scheds[i + 1]

        curr_loc = curr.get("location", "")
        next_loc = next_s.get("location", "")

        # If both have locations and they differ → commute needed
        if curr_loc and next_loc and curr_loc != next_loc:
            curr_end = curr.get("time_end", "")
            next_start = next_s.get("time_start", "")

            if curr_end and next_start:
                # Calculate gap
                try:
                    end_mins = int(curr_end.split(":")[0]) * 60 + int(curr_end.split(":")[1])
                    start_mins = int(next_start.split(":")[0]) * 60 + int(next_start.split(":")[1])
                    gap = start_mins - end_mins
                except (ValueError, IndexError):
                    gap = 999

                if gap < commute_minutes:
                    warnings.append({
                        "type": "tight_commute",
                        "from_event": curr.get("title", ""),
                        "from_location": curr_loc,
                        "to_event": next_s.get("title", ""),
                        "to_location": next_loc,
                        "gap_minutes": gap,
                        "commute_needed": commute_minutes,
                        "message": f"Only {gap}min between '{curr.get('title','')}' ({curr_loc}) and '{next_s.get('title','')}' ({next_loc}). You need ~{commute_minutes}min commute!",
                    })
                else:
                    warnings.append({
                        "type": "commute_ok",
                        "from_event": curr.get("title", ""),
                        "to_event": next_s.get("title", ""),
                        "from_location": curr_loc,
                        "to_location": next_loc,
                        "gap_minutes": gap,
                        "message": f"Commute {curr_loc} → {next_loc}: {gap}min gap (OK)",
                    })

    return warnings
