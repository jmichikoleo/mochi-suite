"""Personal metrics loader and analysis."""

import json
from datetime import date, timedelta
from pathlib import Path
from collections import defaultdict


def load_metrics(data_path: str) -> dict:
    path = Path(data_path)
    if not path.exists():
        return {"entries": []}
    with open(path) as f:
        return json.load(f)


def analyze_metrics(data_path: str, cycle_phase: dict = None) -> dict:
    """Analyze personal metrics and return summary with trends."""
    data = load_metrics(data_path)
    entries = data.get("entries", [])
    today = date.today()

    if not entries:
        return {"has_data": False}

    # Sort by date descending
    entries.sort(key=lambda e: e["date"], reverse=True)

    # Latest entry
    latest = entries[0]

    # Last 7 days
    week_entries = [e for e in entries if _days_ago(e["date"], today) < 7]

    # Sleep analysis
    sleep_data = _analyze_sleep(entries, week_entries, latest)

    # Focus analysis
    focus_data = _analyze_focus(entries, week_entries, latest)

    # Spending analysis
    spending_data = _analyze_spending(week_entries)

    # Body & wellness metrics
    weight_data = _analyze_simple_metric(week_entries, latest, "weight_kg", "kg")
    steps_data = _analyze_simple_metric(week_entries, latest, "steps", "")
    kcal_data = _analyze_simple_metric(week_entries, latest, "kcal", "kcal")
    water_data = _analyze_simple_metric(week_entries, latest, "water_ml", "ml")
    coffee_data = _analyze_simple_metric(week_entries, latest, "coffee_cups", "")

    # Wellness score
    wellness = calculate_wellness_score(sleep_data, steps_data, water_data, kcal_data, cycle_phase)

    return {
        "has_data": True,
        "latest_date": latest["date"],
        "sleep": sleep_data,
        "focus": focus_data,
        "spending": spending_data,
        "weight": weight_data,
        "steps": steps_data,
        "kcal": kcal_data,
        "water": water_data,
        "coffee": coffee_data,
        "sleep_quality": sleep_data.get("quality", "average"),
        "wellness": wellness,
    }


def _days_ago(date_str: str, today: date) -> int:
    d = date.fromisoformat(date_str)
    return (today - d).days


def _analyze_sleep(all_entries: list, week_entries: list, latest: dict) -> dict:
    latest_sleep = latest.get("sleep_hours", 0)

    week_sleep = [e.get("sleep_hours", 0) for e in week_entries if e.get("sleep_hours")]
    avg_week = sum(week_sleep) / len(week_sleep) if week_sleep else 0

    if latest_sleep >= 7.5:
        quality = "good"
    elif latest_sleep >= 6.5:
        quality = "average"
    else:
        quality = "poor"

    if len(week_sleep) >= 6:
        recent_avg = sum(week_sleep[:3]) / 3
        prev_avg = sum(week_sleep[3:6]) / 3
        if recent_avg > prev_avg + 0.3:
            trend = "improving"
        elif recent_avg < prev_avg - 0.3:
            trend = "declining"
        else:
            trend = "stable"
    else:
        trend = "insufficient data"

    return {
        "latest": latest_sleep,
        "avg_7d": round(avg_week, 1),
        "quality": quality,
        "trend": trend,
        "min_7d": min(week_sleep) if week_sleep else 0,
        "max_7d": max(week_sleep) if week_sleep else 0,
    }


def _analyze_focus(all_entries: list, week_entries: list, latest: dict) -> dict:
    latest_focus = latest.get("focus_score", 0)

    week_focus = [e.get("focus_score", 0) for e in week_entries if e.get("focus_score")]
    avg_week = sum(week_focus) / len(week_focus) if week_focus else 0

    if len(week_focus) >= 6:
        recent_avg = sum(week_focus[:3]) / 3
        prev_avg = sum(week_focus[3:6]) / 3
        if recent_avg > prev_avg + 0.5:
            trend = "improving"
        elif recent_avg < prev_avg - 0.5:
            trend = "declining"
        else:
            trend = "stable"
    else:
        trend = "insufficient data"

    return {
        "latest": latest_focus,
        "avg_7d": round(avg_week, 1),
        "trend": trend,
    }


def _analyze_simple_metric(week_entries: list, latest: dict, key: str, unit: str) -> dict:
    """Generic analyzer for simple numeric metrics (weight, steps, kcal, water, coffee)."""
    latest_val = latest.get(key)
    week_vals = [e.get(key) for e in week_entries if e.get(key) is not None]

    if not week_vals:
        return {"has_data": False, "key": key, "unit": unit}

    avg_week = sum(week_vals) / len(week_vals)
    return {
        "has_data": True,
        "key": key,
        "unit": unit,
        "latest": latest_val,
        "avg_7d": round(avg_week, 1),
        "total_7d": round(sum(week_vals), 1),
    }


def _analyze_spending(week_entries: list) -> dict:
    total = 0
    by_category = defaultdict(int)

    for entry in week_entries:
        spending = entry.get("spending", {})
        for cat, amount in spending.items():
            total += amount
            by_category[cat] += amount

    sorted_cats = sorted(by_category.items(), key=lambda x: x[1], reverse=True)
    daily_avg = total / len(week_entries) if week_entries else 0

    return {
        "total_7d": total,
        "daily_avg": round(daily_avg),
        "by_category": dict(sorted_cats),
        "top_category": sorted_cats[0][0] if sorted_cats else "none",
    }


def load_budgets(data_path: str) -> dict:
    """Load monthly budgets from metrics.json."""
    data = load_metrics(data_path)
    return data.get("budgets", {})


def set_budget(data_path: str, category: str, amount: int):
    """Set monthly budget for a spending category."""
    data = load_metrics(data_path)
    data.setdefault("budgets", {})[category] = amount
    with open(data_path, "w") as f:
        json.dump(data, f, indent=2)


def calculate_wellness_score(sleep_data: dict, steps_data: dict,
                             water_data: dict, kcal_data: dict,
                             cycle_phase: dict = None) -> dict:
    """Calculate overall wellness score (0-100) from latest metrics.
    Adjusts targets based on cycle phase for fairer scoring."""
    scores = []

    # Get cycle-adjusted targets
    adj = {}
    if cycle_phase and cycle_phase.get("wellness_adjustments"):
        adj = cycle_phase["wellness_adjustments"]

    sleep_target_low = 7 if not adj.get("sleep_target") else adj["sleep_target"] - 0.5
    sleep_target_high = 9
    steps_target = adj.get("steps_target", 8000)

    # Sleep
    if sleep_data.get("latest"):
        s = sleep_data["latest"]
        if sleep_target_low <= s <= sleep_target_high:
            scores.append(100)
        elif s >= sleep_target_low - 1:
            scores.append(70)
        elif s >= sleep_target_low - 2:
            scores.append(40)
        else:
            scores.append(20)

    # Steps (adjusted by cycle phase)
    if steps_data.get("has_data") and steps_data.get("latest"):
        scores.append(min(100, int(steps_data["latest"] / (steps_target / 100))))

    # Water: target 2000ml
    if water_data.get("has_data") and water_data.get("latest"):
        scores.append(min(100, int(water_data["latest"] / 20)))

    # Kcal: target 1600-2200
    if kcal_data.get("has_data") and kcal_data.get("latest"):
        k = kcal_data["latest"]
        if 1600 <= k <= 2200:
            scores.append(100)
        elif 1200 <= k < 1600 or 2200 < k <= 2800:
            scores.append(65)
        else:
            scores.append(30)

    if not scores:
        return {"score": None, "rating": "No data", "has_data": False}

    avg = sum(scores) / len(scores)
    if avg >= 80:
        rating = "Great day"
    elif avg >= 60:
        rating = "Good"
    elif avg >= 40:
        rating = "Needs attention"
    else:
        rating = "Take care of yourself"

    return {"score": round(avg), "rating": rating, "has_data": True}


def format_metrics_section(metrics_data: dict) -> str:
    """Format metrics into a readable briefing section."""
    if not metrics_data.get("has_data"):
        return "## Personal Metrics\n\nNo data available. Add entries to data/metrics.json.\n"

    lines = []
    lines.append("## Personal Metrics")
    lines.append("")

    s = metrics_data["sleep"]
    quality_icon = {"good": "++", "average": "~", "poor": "--"}[s["quality"]]
    lines.append(f"### Sleep {quality_icon}")
    lines.append(f"- Last night: **{s['latest']}h** | 7d avg: {s['avg_7d']}h | Trend: {s['trend']}")
    lines.append(f"- Range: {s['min_7d']}h - {s['max_7d']}h")
    lines.append("")

    f = metrics_data["focus"]
    lines.append("### Focus")
    lines.append(f"- Latest: **{f['latest']}/10** | 7d avg: {f['avg_7d']} | Trend: {f['trend']}")
    lines.append("")

    # Body metrics
    for key, label in [("weight", "Weight"), ("steps", "Steps"), ("kcal", "Calories"), ("water", "Water"), ("coffee", "Coffee")]:
        m = metrics_data.get(key, {})
        if m.get("has_data"):
            lines.append(f"### {label}")
            lines.append(f"- Latest: **{m['latest']}{m['unit']}** | 7d avg: {m['avg_7d']}{m['unit']}")
            lines.append("")

    sp = metrics_data["spending"]
    lines.append("### Spending (7d)")
    lines.append(f"- Total: **{sp['total_7d']:,}** | Daily avg: {sp['daily_avg']:,}")
    if sp["by_category"]:
        cats = " | ".join(f"{k}: {v:,}" for k, v in sp["by_category"].items())
        lines.append(f"- Breakdown: {cats}")
    lines.append("")

    return "\n".join(lines)
