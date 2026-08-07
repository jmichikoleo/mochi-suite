"""Weekly review generator — aggregates all data sources."""

import json
from datetime import date, timedelta
from pathlib import Path


def generate_weekly_review(data_dir: str) -> dict:
    """Generate a comprehensive weekly review from all data sources."""
    today = date.today()
    week_start = today - timedelta(days=today.weekday())  # Monday
    week_end = week_start + timedelta(days=6)

    review = {
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
    }

    # Tasks
    review["tasks"] = _review_tasks(data_dir, week_start)

    # Habits
    review["habits"] = _review_habits(data_dir, week_start, today)

    # Metrics
    review["metrics"] = _review_metrics(data_dir, week_start, today)

    # Food
    review["food"] = _review_food(data_dir, week_start, today)

    # Journal/Mood
    review["mood"] = _review_mood(data_dir, week_start, today)

    # Papers
    review["papers"] = _review_papers(data_dir)

    # Study
    review["study"] = _review_study(data_dir, week_start)

    # Generate highlights and improvements
    review["highlights"] = _generate_highlights(review)
    review["improvements"] = _generate_improvements(review)

    return review


def _load_json(data_dir, filename):
    path = Path(data_dir) / filename
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


def _review_tasks(data_dir, week_start):
    data = _load_json(data_dir, "tasks.json")
    tasks = data.get("tasks", [])
    done = sum(1 for t in tasks if t.get("status") == "done")
    total = len(tasks)
    return {"completed": done, "total": total, "completion_rate": round(done / total * 100) if total > 0 else 0}


def _review_habits(data_dir, week_start, today):
    data = _load_json(data_dir, "habits.json")
    results = {}
    for habit in data.get("habits", []):
        name = habit["name"]
        history = habit.get("history", {})
        days_in_week = min(7, (today - week_start).days + 1)
        completed = 0
        for i in range(days_in_week):
            d = (week_start + timedelta(days=i)).isoformat()
            if history.get(d, False):
                completed += 1
        results[name] = round(completed / days_in_week * 100) if days_in_week > 0 else 0
    return results


def _review_metrics(data_dir, week_start, today):
    data = _load_json(data_dir, "metrics.json")
    entries = [e for e in data.get("entries", []) if e.get("date", "") >= week_start.isoformat() and e.get("date", "") <= today.isoformat()]

    if not entries:
        return {"has_data": False}

    avg = lambda key: round(sum(e.get(key, 0) for e in entries if e.get(key)) / max(1, sum(1 for e in entries if e.get(key))), 1)

    total_spending = 0
    for e in entries:
        sp = e.get("spending", {})
        total_spending += sum(sp.values()) if isinstance(sp, dict) else 0

    return {
        "has_data": True,
        "avg_sleep": avg("sleep_hours"),
        "avg_focus": avg("focus_score"),
        "avg_steps": avg("steps"),
        "avg_water": avg("water_ml"),
        "avg_coffee": avg("coffee_cups"),
        "total_spending": total_spending,
        "days_logged": len(entries),
    }


def _review_food(data_dir, week_start, today):
    data = _load_json(data_dir, "food_log.json")
    entries = data.get("entries", {})
    total_kcal = 0
    days = 0
    for d_str, foods in entries.items():
        if d_str >= week_start.isoformat() and d_str <= today.isoformat():
            day_kcal = sum(f.get("kcal_estimate", 0) for f in foods)
            total_kcal += day_kcal
            days += 1
    return {"avg_kcal": round(total_kcal / days) if days > 0 else 0, "days_logged": days}


def _review_mood(data_dir, week_start, today):
    data = _load_json(data_dir, "journal.json")
    moods = []
    for e in data.get("entries", []):
        if e.get("date", "") >= week_start.isoformat() and e.get("date", "") <= today.isoformat():
            if e.get("mood"):
                moods.append(e["mood"])
    return {"avg_mood": round(sum(moods) / len(moods), 1) if moods else None, "entries": len(moods)}


def _review_papers(data_dir):
    data = _load_json(data_dir, "paper_history.json")
    return {"read": len(data.get("read_papers", []))}


def _review_study(data_dir, week_start):
    data = _load_json(data_dir, "study_log.json")
    total_min = 0
    by_subject = {}
    for s in data.get("sessions", []):
        if s.get("date", "") >= week_start.isoformat():
            dur = s.get("duration_min", 0)
            total_min += dur
            subj = s.get("subject", "Other")
            by_subject[subj] = by_subject.get(subj, 0) + dur
    return {"total_hours": round(total_min / 60, 1), "by_subject": by_subject}


def _generate_highlights(review):
    highlights = []
    if review["tasks"]["completion_rate"] >= 70:
        highlights.append(f"Completed {review['tasks']['completion_rate']}% of tasks")
    m = review.get("metrics", {})
    if m.get("has_data"):
        if m.get("avg_sleep", 0) >= 7.5:
            highlights.append(f"Consistent sleep at {m['avg_sleep']}h average")
        if m.get("avg_focus", 0) >= 7:
            highlights.append(f"Strong focus at {m['avg_focus']}/10 average")
    for habit, rate in review.get("habits", {}).items():
        if rate >= 80:
            highlights.append(f"{habit}: {rate}% completion")
    if review.get("study", {}).get("total_hours", 0) >= 10:
        highlights.append(f"Solid {review['study']['total_hours']}h of study time")
    mood = review.get("mood", {}).get("avg_mood")
    if mood and mood >= 4:
        highlights.append(f"Great mood averaging {mood}/5")
    return highlights[:5]


def _generate_improvements(review):
    improvements = []
    if review["tasks"]["completion_rate"] < 50 and review["tasks"]["total"] > 2:
        improvements.append("Low task completion — try setting fewer, more realistic tasks")
    m = review.get("metrics", {})
    if m.get("has_data"):
        if m.get("avg_sleep", 99) < 6.5:
            improvements.append(f"Sleep averaged only {m['avg_sleep']}h — prioritize rest")
        if m.get("avg_water", 99999) < 1500:
            improvements.append(f"Water intake low at {m['avg_water']}ml — aim for 2000ml")
        if m.get("avg_steps", 99999) < 5000:
            improvements.append("Steps are low — try a 15min walk between study sessions")
    for habit, rate in review.get("habits", {}).items():
        if rate < 30:
            improvements.append(f"{habit} only {rate}% — consider simplifying or rescheduling")
    mood = review.get("mood", {}).get("avg_mood")
    if mood and mood < 3:
        improvements.append("Mood was low this week — consider what drained your energy")
    return improvements[:5]
