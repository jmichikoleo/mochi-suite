"""Monthly report card — auto-generated end-of-month summary."""

import json
from datetime import date, timedelta
from pathlib import Path
from collections import defaultdict


def generate_monthly_report(data_dir: str, year: int = None, month: int = None) -> dict:
    """Generate comprehensive monthly report card."""
    today = date.today()
    year = year or today.year
    month = month or today.month
    month_str = f"{year}-{month:02d}"

    def _load(*parts):
        path = Path(data_dir).joinpath(*parts)
        if path.exists():
            with open(path) as f:
                return json.load(f)
        return {}

    report = {"year": year, "month": month, "month_str": month_str}

    # Habits
    habits = _load("habits.json")
    habit_rates = {}
    for h in habits.get("habits", []):
        history = h.get("history", {})
        month_days = {k: v for k, v in history.items() if k.startswith(month_str)}
        if month_days:
            rate = round(sum(1 for v in month_days.values() if v) / len(month_days) * 100)
            habit_rates[h["name"]] = rate
    report["habits"] = habit_rates

    # Metrics
    metrics = _load("metrics.json")
    month_entries = [e for e in metrics.get("entries", []) if e.get("date", "").startswith(month_str)]
    if month_entries:
        avg = lambda k: round(sum(e.get(k, 0) for e in month_entries if e.get(k)) / max(1, sum(1 for e in month_entries if e.get(k))), 1)
        report["metrics"] = {
            "avg_sleep": avg("sleep_hours"),
            "avg_focus": avg("focus_score"),
            "avg_steps": avg("steps"),
            "avg_water": avg("water_ml"),
            "avg_coffee": avg("coffee_cups"),
            "days_logged": len(month_entries),
        }
    else:
        report["metrics"] = {"days_logged": 0}

    # Spending
    expenses = _load("expenses.json")
    month_exp = [e for e in expenses.get("entries", []) if e.get("date", "").startswith(month_str)]
    total_spent = sum(e.get("amount", 0) for e in month_exp)
    by_cat = defaultdict(int)
    for e in month_exp:
        by_cat[e.get("category", "other")] += e.get("amount", 0)
    report["spending"] = {"total": total_spent, "by_category": dict(by_cat), "count": len(month_exp)}

    # Tasks
    tasks = _load("tasks.json")
    done = sum(1 for t in tasks.get("tasks", []) if t.get("status") == "done")
    report["tasks"] = {"completed": done, "total": len(tasks.get("tasks", []))}

    # Journal
    journal = _load("journal.json")
    month_journals = [e for e in journal.get("entries", []) if e.get("date", "").startswith(month_str)]
    moods = [e.get("mood") for e in month_journals if e.get("mood")]
    report["journal"] = {
        "entries": len(month_journals),
        "avg_mood": round(sum(moods) / len(moods), 1) if moods else None,
    }

    # Study
    study = _load("study_log.json")
    month_study = [s for s in study.get("sessions", []) if s.get("date", "").startswith(month_str)]
    total_mins = sum(s.get("duration_min", 0) for s in month_study)
    report["study"] = {"total_hours": round(total_mins / 60, 1), "sessions": len(month_study)}

    # Papers
    lab_papers = _load("lab", "papers.json")
    month_papers = [p for p in lab_papers.get("papers", []) if p.get("added_date", "").startswith(month_str)]
    read_papers = [p for p in month_papers if p.get("status") == "done"]
    report["papers"] = {"added": len(month_papers), "read": len(read_papers)}

    # TOPIK
    goals = _load("goals.json")
    for g in goals.get("goals", []):
        if g.get("id") == "topik":
            month_logs = {k: v for k, v in g.get("daily_log", {}).items() if k.startswith(month_str)}
            words = sum(v.get("words_learned", 0) for v in month_logs.values())
            mins = sum(v.get("minutes", 0) for v in month_logs.values())
            report["topik"] = {"words_learned": words, "study_minutes": mins, "days_studied": len(month_logs)}

    # Food
    food = _load("food_log.json")
    month_food = {k: v for k, v in food.get("entries", {}).items() if k.startswith(month_str)}
    if month_food:
        daily_kcals = [sum(f.get("kcal_estimate", 0) for f in foods) for foods in month_food.values()]
        report["food"] = {"avg_kcal": round(sum(daily_kcals) / len(daily_kcals)), "days_logged": len(month_food)}
    else:
        report["food"] = {"avg_kcal": 0, "days_logged": 0}

    # Achievements
    from src.achievements import get_all_achievements
    ach = get_all_achievements(data_dir)
    report["achievements"] = {"unlocked": ach["unlocked_count"], "total": ach["total_count"]}

    # Grades
    grades = _load("grades.json")
    from src.grades import calculate_gpa
    gpa_data = calculate_gpa(str(Path(data_dir) / "grades.json"))
    report["gpa"] = gpa_data.get("cumulative_gpa")

    return report
