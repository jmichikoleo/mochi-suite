"""Smart nudge generator — contextual reminders from all data sources."""

import json
from datetime import date, timedelta, datetime
from pathlib import Path


def generate_nudges(data_dir: str) -> list:
    """Generate smart nudges by scanning all data sources."""
    nudges = []
    today = date.today()
    today_str = today.isoformat()

    # 1. Upcoming assignment deadlines
    nudges.extend(_check_assignments(data_dir, today))

    # 2. Unread papers in queue
    nudges.extend(_check_reading_queue(data_dir))

    # 3. Missing daily logs
    nudges.extend(_check_missing_logs(data_dir, today_str))

    # 4. Habit streaks at risk
    nudges.extend(_check_habits(data_dir, today))

    # 5. Upcoming schedules
    nudges.extend(_check_schedules(data_dir, today))

    # 6. Study session reminders
    nudges.extend(_check_study(data_dir, today))

    # 7. Flashcard reviews due
    nudges.extend(_check_flashcards(data_dir))

    # 7.5 Goals (TOPIK etc)
    nudges.extend(_check_goals(data_dir, today))

    # 8. Lab meeting prep
    nudges.extend(_check_lab(data_dir, today))

    # Sort by priority
    priority_order = {"urgent": 0, "important": 1, "reminder": 2, "suggestion": 3}
    nudges.sort(key=lambda n: priority_order.get(n.get("priority", "suggestion"), 3))

    return nudges[:8]  # Top 8 nudges


def _load(data_dir, *path_parts):
    path = Path(data_dir).joinpath(*path_parts)
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


def _check_assignments(data_dir, today):
    nudges = []
    grades = _load(data_dir, "grades.json")
    for course in grades.get("courses", []):
        for a in course.get("assignments", []):
            if a.get("date"):
                try:
                    due = date.fromisoformat(a["date"])
                    days = (due - today).days
                    if 0 <= days <= 3 and not a.get("grade"):
                        nudges.append({
                            "icon": "📝", "priority": "urgent",
                            "text": f"'{a['name']}' for {course['name']} due in {days} day{'s' if days != 1 else ''}!",
                        })
                except ValueError:
                    pass
    return nudges


def _check_reading_queue(data_dir):
    nudges = []
    rq = _load(data_dir, "reading_queue.json")
    unread = sum(1 for i in rq.get("items", []) if i.get("status") == "unread")
    if unread >= 3:
        nudges.append({"icon": "📚", "priority": "reminder",
                       "text": f"You have {unread} unread items in your reading queue."})
    return nudges


def _check_missing_logs(data_dir, today_str):
    nudges = []
    metrics = _load(data_dir, "metrics.json")
    has_today = any(e.get("date") == today_str for e in metrics.get("entries", []))
    if not has_today:
        now_hour = datetime.now().hour
        if now_hour >= 20:
            nudges.append({"icon": "📊", "priority": "reminder",
                           "text": "You haven't logged today's metrics yet!"})

    journal = _load(data_dir, "journal.json")
    has_journal = any(e.get("date") == today_str for e in journal.get("entries", []))
    if not has_journal and datetime.now().hour >= 19:
        nudges.append({"icon": "📝", "priority": "suggestion",
                       "text": "Take a moment to journal how you're feeling today."})

    food = _load(data_dir, "food_log.json")
    food_today = food.get("entries", {}).get(today_str, [])
    if not food_today and datetime.now().hour >= 12:
        nudges.append({"icon": "🍽️", "priority": "suggestion",
                       "text": "Don't forget to log your meals!"})

    return nudges


def _check_habits(data_dir, today):
    nudges = []
    habits = _load(data_dir, "habits.json")
    for h in habits.get("habits", []):
        history = h.get("history", {})
        # Check if streak is about to break
        yesterday = (today - timedelta(days=1)).isoformat()
        two_days_ago = (today - timedelta(days=2)).isoformat()
        if history.get(yesterday) and history.get(two_days_ago) and not history.get(today.isoformat()):
            nudges.append({"icon": "🔥", "priority": "important",
                           "text": f"Don't break your '{h['name']}' streak!"})
    return nudges


def _check_schedules(data_dir, today):
    nudges = []
    tomorrow = (today + timedelta(days=1)).isoformat()
    tasks = _load(data_dir, "tasks.json")
    tomorrow_scheds = [s for s in tasks.get("schedules", []) if s.get("date") == tomorrow]
    if tomorrow_scheds:
        first = sorted(tomorrow_scheds, key=lambda s: s.get("time_start", ""))[0]
        nudges.append({"icon": "📅", "priority": "reminder",
                       "text": f"Tomorrow starts with '{first['title']}' at {first.get('time_start', '')}."})
    return nudges


def _check_study(data_dir, today):
    nudges = []
    study = _load(data_dir, "study_log.json")
    week_start = today - timedelta(days=today.weekday())
    week_mins = sum(s.get("duration_min", 0) for s in study.get("sessions", [])
                    if s.get("date", "") >= week_start.isoformat())
    if week_mins < 120 and today.weekday() >= 3:  # Thursday+
        nudges.append({"icon": "📖", "priority": "important",
                       "text": f"Only {round(week_mins/60,1)}h studied this week. Try to fit in a session!"})
    return nudges


def _check_flashcards(data_dir):
    nudges = []
    fc = _load(data_dir, "uni", "flashcards.json")
    today_str = date.today().isoformat()
    due = 0
    for deck in fc.get("decks", []):
        for card in deck.get("cards", []):
            if card.get("next_review", "") <= today_str:
                due += 1
    if due > 0:
        nudges.append({"icon": "🃏", "priority": "reminder",
                       "text": f"{due} flashcard{'s' if due != 1 else ''} due for review!"})
    return nudges


def _check_lab(data_dir, today):
    nudges = []
    tasks = _load(data_dir, "tasks.json")
    tomorrow = (today + timedelta(days=1)).isoformat()
    for s in tasks.get("schedules", []):
        if s.get("date") == tomorrow and "lab" in s.get("title", "").lower():
            nudges.append({"icon": "🔬", "priority": "important",
                           "text": "Lab meeting tomorrow! Prep your weekly update."})
            break
    return nudges


def _check_goals(data_dir, today):
    nudges = []
    data = _load(data_dir, "goals.json")
    for g in data.get("goals", []):
        if g.get("status") != "active":
            continue
        target = g.get("target_date", "")
        if not target:
            continue
        try:
            target_date = date.fromisoformat(target)
            days_left = (target_date - today).days
        except ValueError:
            continue

        title = g.get("title", "Goal")
        daily_log = g.get("daily_log", {})
        studied_today = today.isoformat() in daily_log

        if days_left <= 0:
            nudges.append({"icon": "🎯", "priority": "urgent",
                           "text": f"{title} is TODAY! You've got this! 화이팅!"})
        elif days_left <= 7:
            nudges.append({"icon": "🔥", "priority": "urgent",
                           "text": f"{title} in {days_left} days! Focus on weak areas."})
        elif days_left <= 30 and not studied_today:
            plan = g.get("study_plan", {})
            daily_target = plan.get("daily_vocab_target", 20)
            nudges.append({"icon": "🇰🇷", "priority": "important",
                           "text": f"{title} in {days_left} days — study {daily_target} words today!"})
        elif not studied_today:
            nudges.append({"icon": "📚", "priority": "reminder",
                           "text": f"{title} in {days_left} days. Keep your study streak going!"})
    return nudges
