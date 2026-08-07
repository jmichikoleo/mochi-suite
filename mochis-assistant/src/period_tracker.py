"""Period tracker with cycle phase detection and energy profile integration."""

import json
from datetime import date, timedelta
from pathlib import Path


PHASE_PROFILES = {
    "menstrual": {
        "energy": "low",
        "focus": "low",
        "label": "Menstrual Phase",
        "emoji": "🌙",
        "color": "#FFB3B3",
        "best_for": ["light tasks", "rest", "reflection", "self-care"],
        "avoid": ["presentations", "high-pressure deadlines", "intense exercise"],
        "task_strategy": "poor",  # maps to sleep_quality equivalent for focus.py
        "wellness_adjustments": {
            "steps_target": 5000,   # lowered from 8000
            "sleep_target": 8.0,    # raised from 7.5
            "focus_lenient": True,
        },
    },
    "follicular": {
        "energy": "rising",
        "focus": "medium-high",
        "label": "Follicular Phase",
        "emoji": "🌱",
        "color": "#B8E6CC",
        "best_for": ["creative work", "learning new things", "planning", "brainstorming"],
        "avoid": [],
        "task_strategy": "good",
        "wellness_adjustments": {
            "steps_target": 8000,
            "sleep_target": 7.5,
            "focus_lenient": False,
        },
    },
    "ovulatory": {
        "energy": "peak",
        "focus": "high",
        "label": "Ovulatory Phase",
        "emoji": "☀️",
        "color": "#FFE4C4",
        "best_for": ["presentations", "social tasks", "hard problems", "interviews", "networking"],
        "avoid": [],
        "task_strategy": "good",  # even better than good — we boost high-energy tasks
        "wellness_adjustments": {
            "steps_target": 10000,
            "sleep_target": 7.0,
            "focus_lenient": False,
        },
    },
    "luteal": {
        "energy": "declining",
        "focus": "medium",
        "label": "Luteal Phase",
        "emoji": "🍂",
        "color": "#D4B8FF",
        "best_for": ["detail work", "routine tasks", "organization", "editing", "review"],
        "avoid": ["starting big new projects", "major decisions late in phase"],
        "task_strategy": "average",
        "wellness_adjustments": {
            "steps_target": 6000,
            "sleep_target": 8.0,
            "focus_lenient": True,
        },
    },
}


def load_period_data(data_path: str) -> dict:
    path = Path(data_path)
    if not path.exists():
        return {"cycles": [], "settings": {"avg_cycle_length": 28, "avg_period_length": 5}}
    with open(path) as f:
        return json.load(f)


def save_period_data(data_path: str, data: dict):
    with open(data_path, "w") as f:
        json.dump(data, f, indent=2)


def log_period(data_path: str, start_date: str, end_date: str = None,
               symptoms: list = None, notes: str = "") -> None:
    data = load_period_data(data_path)

    cycle = {
        "start_date": start_date,
        "end_date": end_date or "",
        "symptoms": symptoms or [],
        "notes": notes,
    }

    # Update or add
    for i, c in enumerate(data["cycles"]):
        if c["start_date"] == start_date:
            data["cycles"][i] = cycle
            break
    else:
        data["cycles"].append(cycle)

    # Sort by date descending
    data["cycles"].sort(key=lambda c: c["start_date"], reverse=True)

    # Recalculate averages
    _update_averages(data)
    save_period_data(data_path, data)


def _update_averages(data: dict):
    """Recalculate average cycle and period length from history."""
    cycles = data["cycles"]
    if len(cycles) < 2:
        return

    # Cycle lengths (days between consecutive start dates)
    cycle_lengths = []
    sorted_cycles = sorted(cycles, key=lambda c: c["start_date"])
    for i in range(1, len(sorted_cycles)):
        prev = date.fromisoformat(sorted_cycles[i - 1]["start_date"])
        curr = date.fromisoformat(sorted_cycles[i]["start_date"])
        length = (curr - prev).days
        if 20 <= length <= 40:  # filter out outliers
            cycle_lengths.append(length)

    if cycle_lengths:
        # Weight recent cycles more
        if len(cycle_lengths) >= 3:
            recent = cycle_lengths[-3:]
            data["settings"]["avg_cycle_length"] = round(sum(recent) / len(recent))
        else:
            data["settings"]["avg_cycle_length"] = round(sum(cycle_lengths) / len(cycle_lengths))

    # Period lengths
    period_lengths = []
    for c in cycles:
        if c.get("end_date") and c.get("start_date"):
            start = date.fromisoformat(c["start_date"])
            end = date.fromisoformat(c["end_date"])
            length = (end - start).days + 1
            if 2 <= length <= 10:
                period_lengths.append(length)

    if period_lengths:
        data["settings"]["avg_period_length"] = round(sum(period_lengths) / len(period_lengths))


def get_current_phase(data_path: str) -> dict:
    """Determine current cycle phase and predictions."""
    data = load_period_data(data_path)
    cycles = data["cycles"]
    settings = data["settings"]
    today_date = date.today()

    if not cycles:
        return {
            "has_data": False,
            "phase": None,
            "message": "No period data logged yet. Log your first period to get started.",
        }

    # Find most recent cycle start
    sorted_cycles = sorted(cycles, key=lambda c: c["start_date"], reverse=True)
    last_start = date.fromisoformat(sorted_cycles[0]["start_date"])
    last_end = None
    if sorted_cycles[0].get("end_date"):
        last_end = date.fromisoformat(sorted_cycles[0]["end_date"])

    avg_cycle = settings.get("avg_cycle_length", 28)
    avg_period = settings.get("avg_period_length", 5)

    day_of_cycle = (today_date - last_start).days + 1

    # If we're past the expected cycle length, a new cycle might have started
    if day_of_cycle > avg_cycle + 7:
        return {
            "has_data": True,
            "phase": "unknown",
            "day_of_cycle": day_of_cycle,
            "message": f"Day {day_of_cycle} of cycle — your period may be late. Consider logging if it has started.",
            "next_period_start": "overdue",
            "profile": PHASE_PROFILES.get("luteal"),
        }

    # Determine phase
    if day_of_cycle <= avg_period:
        phase = "menstrual"
    elif day_of_cycle <= 13:
        phase = "follicular"
    elif day_of_cycle <= 16:
        phase = "ovulatory"
    else:
        phase = "luteal"

    # Prediction
    next_start = last_start + timedelta(days=avg_cycle)
    days_until_next = (next_start - today_date).days

    profile = PHASE_PROFILES[phase]

    return {
        "has_data": True,
        "phase": phase,
        "day_of_cycle": day_of_cycle,
        "label": profile["label"],
        "emoji": profile["emoji"],
        "color": profile["color"],
        "energy": profile["energy"],
        "focus_level": profile["focus"],
        "best_for": profile["best_for"],
        "avoid": profile["avoid"],
        "task_strategy": profile["task_strategy"],
        "wellness_adjustments": profile["wellness_adjustments"],
        "next_period_start": next_start.isoformat(),
        "days_until_next": max(0, days_until_next),
        "avg_cycle_length": avg_cycle,
        "cycle_count": len(cycles),
    }


def get_cycle_stats(data_path: str) -> dict:
    """Get overall cycle statistics."""
    data = load_period_data(data_path)
    cycles = data["cycles"]

    if len(cycles) < 2:
        return {"has_stats": False}

    sorted_cycles = sorted(cycles, key=lambda c: c["start_date"])
    lengths = []
    for i in range(1, len(sorted_cycles)):
        prev = date.fromisoformat(sorted_cycles[i - 1]["start_date"])
        curr = date.fromisoformat(sorted_cycles[i]["start_date"])
        length = (curr - prev).days
        if 20 <= length <= 40:
            lengths.append(length)

    if not lengths:
        return {"has_stats": False}

    return {
        "has_stats": True,
        "avg_length": round(sum(lengths) / len(lengths), 1),
        "shortest": min(lengths),
        "longest": max(lengths),
        "total_cycles": len(cycles),
        "regularity": "regular" if max(lengths) - min(lengths) <= 5 else "somewhat irregular" if max(lengths) - min(lengths) <= 10 else "irregular",
    }
