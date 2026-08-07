"""Achievement badge system — gamify progress tracking."""

import json
from datetime import date, timedelta
from pathlib import Path

# Badge definitions
BADGES = {
    # Habit streaks
    "streak_3": {"name": "Getting Started", "emoji": "🌱", "desc": "3-day habit streak", "category": "habits"},
    "streak_7": {"name": "On Fire", "emoji": "🔥", "desc": "7-day habit streak", "category": "habits"},
    "streak_14": {"name": "Unstoppable", "emoji": "⚡", "desc": "14-day habit streak", "category": "habits"},
    "streak_30": {"name": "Legendary", "emoji": "👑", "desc": "30-day habit streak", "category": "habits"},

    # Study
    "papers_1": {"name": "First Paper", "emoji": "📄", "desc": "Read your first paper", "category": "research"},
    "papers_5": {"name": "Bookworm", "emoji": "📚", "desc": "Read 5 papers", "category": "research"},
    "papers_20": {"name": "Scholar", "emoji": "🎓", "desc": "Read 20 papers", "category": "research"},
    "study_10h": {"name": "Dedicated", "emoji": "📖", "desc": "10 hours of study this week", "category": "study"},

    # TOPIK
    "topik_50": {"name": "한국어 초보", "emoji": "🇰🇷", "desc": "50 TOPIK words learned", "category": "topik"},
    "topik_100": {"name": "한국어 중급", "emoji": "🇰🇷", "desc": "100 TOPIK words learned", "category": "topik"},
    "topik_500": {"name": "한국어 고급", "emoji": "🇰🇷", "desc": "500 TOPIK words learned", "category": "topik"},
    "topik_streak_7": {"name": "매일 공부", "emoji": "📝", "desc": "7-day TOPIK study streak", "category": "topik"},

    # Health
    "hydration_3": {"name": "Hydration Hero", "emoji": "💧", "desc": "3 days of 2000ml+ water", "category": "health"},
    "hydration_7": {"name": "Water Champion", "emoji": "🌊", "desc": "7 days of 2000ml+ water", "category": "health"},
    "steps_10k": {"name": "Step Master", "emoji": "🏃", "desc": "10k steps 3 days in a row", "category": "health"},
    "sleep_7": {"name": "Well Rested", "emoji": "😴", "desc": "7 days of 7h+ sleep", "category": "health"},

    # Journal
    "journal_3": {"name": "Reflector", "emoji": "✍️", "desc": "3 days journaled", "category": "journal"},
    "journal_14": {"name": "Journaling Queen", "emoji": "📔", "desc": "14 days journaled", "category": "journal"},
    "journal_30": {"name": "Dear Diary", "emoji": "💕", "desc": "30 days journaled", "category": "journal"},

    # Tasks
    "tasks_10": {"name": "Productive", "emoji": "✅", "desc": "Completed 10 tasks", "category": "tasks"},
    "tasks_50": {"name": "Task Crusher", "emoji": "💪", "desc": "Completed 50 tasks", "category": "tasks"},

    # Misc
    "first_expense": {"name": "Money Tracker", "emoji": "💰", "desc": "Logged first expense", "category": "misc"},
    "first_recipe": {"name": "Home Chef", "emoji": "👩‍🍳", "desc": "Saved first recipe", "category": "misc"},
    "first_watch": {"name": "Binge Watcher", "emoji": "📺", "desc": "Added first show to watchlist", "category": "misc"},
}


def load_achievements(data_path: str) -> dict:
    path = Path(data_path)
    if not path.exists():
        return {"unlocked": [], "seen": []}
    with open(path) as f:
        return json.load(f)


def save_achievements(data_path: str, data: dict):
    with open(data_path, "w") as f:
        json.dump(data, f, indent=2)


def check_and_unlock(data_dir: str) -> list:
    """Scan all data and unlock any new achievements. Returns newly unlocked."""
    ach_path = str(Path(data_dir) / "achievements.json")
    data = load_achievements(ach_path)
    already = set(data.get("unlocked", []))
    newly_unlocked = []

    def _load(*parts):
        path = Path(data_dir).joinpath(*parts)
        if path.exists():
            with open(path) as f:
                return json.load(f)
        return {}

    today = date.today()

    # --- Habit streaks ---
    habits = _load("habits.json")
    for habit in habits.get("habits", []):
        history = habit.get("history", {})
        streak = 0
        check = today
        while history.get(check.isoformat(), False):
            streak += 1
            check -= timedelta(days=1)
        if not history.get(today.isoformat()):
            streak = 0
            check = today - timedelta(days=1)
            while history.get(check.isoformat(), False):
                streak += 1
                check -= timedelta(days=1)

        if streak >= 3 and "streak_3" not in already:
            newly_unlocked.append("streak_3")
        if streak >= 7 and "streak_7" not in already:
            newly_unlocked.append("streak_7")
        if streak >= 14 and "streak_14" not in already:
            newly_unlocked.append("streak_14")
        if streak >= 30 and "streak_30" not in already:
            newly_unlocked.append("streak_30")

    # --- Papers read ---
    paper_hist = _load("paper_history.json")
    read_count = len(paper_hist.get("read_papers", []))
    lab_papers = _load("lab", "papers.json")
    read_count += sum(1 for p in lab_papers.get("papers", []) if p.get("status") == "done")
    if read_count >= 1 and "papers_1" not in already:
        newly_unlocked.append("papers_1")
    if read_count >= 5 and "papers_5" not in already:
        newly_unlocked.append("papers_5")
    if read_count >= 20 and "papers_20" not in already:
        newly_unlocked.append("papers_20")

    # --- TOPIK words ---
    goals = _load("goals.json")
    for g in goals.get("goals", []):
        if g.get("id") == "topik":
            total_words = sum(d.get("words_learned", 0) for d in g.get("daily_log", {}).values())
            if total_words >= 50 and "topik_50" not in already:
                newly_unlocked.append("topik_50")
            if total_words >= 100 and "topik_100" not in already:
                newly_unlocked.append("topik_100")
            if total_words >= 500 and "topik_500" not in already:
                newly_unlocked.append("topik_500")
            # TOPIK study streak
            streak = 0
            check = today
            dl = g.get("daily_log", {})
            while dl.get(check.isoformat()):
                streak += 1
                check -= timedelta(days=1)
            if streak >= 7 and "topik_streak_7" not in already:
                newly_unlocked.append("topik_streak_7")

    # --- Health ---
    metrics = _load("metrics.json")
    entries = sorted(metrics.get("entries", []), key=lambda e: e.get("date", ""), reverse=True)

    def _consecutive_days(entries, key, threshold, count_needed):
        c = 0
        for e in entries:
            if e.get(key, 0) >= threshold:
                c += 1
                if c >= count_needed:
                    return True
            else:
                c = 0
        return False

    if _consecutive_days(entries, "water_ml", 2000, 3) and "hydration_3" not in already:
        newly_unlocked.append("hydration_3")
    if _consecutive_days(entries, "water_ml", 2000, 7) and "hydration_7" not in already:
        newly_unlocked.append("hydration_7")
    if _consecutive_days(entries, "steps", 10000, 3) and "steps_10k" not in already:
        newly_unlocked.append("steps_10k")
    if _consecutive_days(entries, "sleep_hours", 7, 7) and "sleep_7" not in already:
        newly_unlocked.append("sleep_7")

    # --- Journal ---
    journal = _load("journal.json")
    journal_count = len(journal.get("entries", []))
    if journal_count >= 3 and "journal_3" not in already:
        newly_unlocked.append("journal_3")
    if journal_count >= 14 and "journal_14" not in already:
        newly_unlocked.append("journal_14")
    if journal_count >= 30 and "journal_30" not in already:
        newly_unlocked.append("journal_30")

    # --- Tasks ---
    tasks = _load("tasks.json")
    done_count = sum(1 for t in tasks.get("tasks", []) if t.get("status") == "done")
    if done_count >= 10 and "tasks_10" not in already:
        newly_unlocked.append("tasks_10")
    if done_count >= 50 and "tasks_50" not in already:
        newly_unlocked.append("tasks_50")

    # --- Misc firsts ---
    exp = _load("expenses.json")
    if exp.get("entries") and "first_expense" not in already:
        newly_unlocked.append("first_expense")
    rec = _load("recipes.json")
    if rec.get("recipes") and "first_recipe" not in already:
        newly_unlocked.append("first_recipe")
    wl = _load("watchlist.json")
    if wl.get("items") and "first_watch" not in already:
        newly_unlocked.append("first_watch")

    # Study hours
    study = _load("study_log.json")
    week_start = today - timedelta(days=today.weekday())
    week_mins = sum(s.get("duration_min", 0) for s in study.get("sessions", [])
                    if s.get("date", "") >= week_start.isoformat())
    if week_mins >= 600 and "study_10h" not in already:
        newly_unlocked.append("study_10h")

    # Save newly unlocked
    if newly_unlocked:
        data["unlocked"].extend(newly_unlocked)
        data["unlocked"] = list(set(data["unlocked"]))
        save_achievements(ach_path, data)

    return newly_unlocked


def get_all_achievements(data_dir: str) -> dict:
    """Get all badges with unlock status."""
    ach_path = str(Path(data_dir) / "achievements.json")
    data = load_achievements(ach_path)
    unlocked = set(data.get("unlocked", []))

    all_badges = []
    for bid, badge in BADGES.items():
        all_badges.append({
            "id": bid,
            "unlocked": bid in unlocked,
            **badge,
        })

    return {
        "badges": all_badges,
        "unlocked_count": len(unlocked),
        "total_count": len(BADGES),
    }
