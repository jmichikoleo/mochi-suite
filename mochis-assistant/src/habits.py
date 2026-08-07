"""Habit tracking, streaks, and behavior intelligence."""

import json
from datetime import date, timedelta
from pathlib import Path
from collections import defaultdict


def load_habits(data_path: str) -> dict:
    path = Path(data_path)
    if not path.exists():
        return {"habits": []}
    with open(path) as f:
        return json.load(f)


def calculate_streak(history: dict, today: date) -> int:
    """Calculate current consecutive day streak ending today or yesterday."""
    streak = 0
    check_date = today
    # Allow checking from today or yesterday (in case today not logged yet)
    if not history.get(check_date.isoformat(), False):
        check_date = today - timedelta(days=1)

    while history.get(check_date.isoformat(), False):
        streak += 1
        check_date -= timedelta(days=1)
    return streak


def completion_rate(history: dict, days: int, today: date) -> float:
    """Calculate completion rate over last N days."""
    completed = 0
    for i in range(days):
        d = (today - timedelta(days=i)).isoformat()
        if history.get(d, False):
            completed += 1
    return completed / days if days > 0 else 0.0


def detect_trend(history: dict, today: date) -> str:
    """Compare last 3 days vs previous 3 days to detect trend."""
    recent = sum(1 for i in range(3) if history.get((today - timedelta(days=i)).isoformat(), False))
    previous = sum(1 for i in range(3, 6) if history.get((today - timedelta(days=i)).isoformat(), False))

    if recent > previous:
        return "improving"
    if recent < previous:
        return "declining"
    return "stable"


def analyze_habits(data_path: str, metrics_entries: list = None) -> dict:
    """Analyze all habits and generate insights.

    Args:
        data_path: Path to habits.json
        metrics_entries: Optional list of metric entries for correlation analysis
    """
    data = load_habits(data_path)
    today = date.today()

    habit_reports = []
    for habit in data.get("habits", []):
        history = habit.get("history", {})
        streak = calculate_streak(history, today)
        rate_7d = completion_rate(history, 7, today)
        trend = detect_trend(history, today)
        done_today = history.get(today.isoformat(), False)

        habit_reports.append({
            "name": habit["name"],
            "done_today": done_today,
            "streak": streak,
            "rate_7d": round(rate_7d * 100),
            "trend": trend,
            "frequency": habit.get("frequency", "daily"),
        })

    # Behavior correlations with metrics
    correlations = []
    if metrics_entries:
        correlations = _find_correlations(data.get("habits", []), metrics_entries, today)

    # Generate suggestions
    suggestions = _generate_suggestions(habit_reports, today)

    return {
        "habits": habit_reports,
        "correlations": correlations,
        "suggestions": suggestions,
    }


def _find_correlations(habits: list, metrics: list, today: date) -> list:
    """Find correlations between habit completion and metrics."""
    correlations = []

    # Build metrics lookup by date
    metrics_by_date = {e["date"]: e for e in metrics}

    for habit in habits:
        history = habit.get("history", {})

        # Compare sleep on habit-done days vs habit-missed days
        done_sleep = []
        missed_sleep = []
        done_focus = []
        missed_focus = []

        for date_str, completed in history.items():
            if date_str in metrics_by_date:
                m = metrics_by_date[date_str]
                if completed:
                    done_sleep.append(m.get("sleep_hours", 0))
                    done_focus.append(m.get("focus_score", 0))
                else:
                    missed_sleep.append(m.get("sleep_hours", 0))
                    missed_focus.append(m.get("focus_score", 0))

        if done_sleep and missed_sleep:
            avg_done = sum(done_sleep) / len(done_sleep)
            avg_missed = sum(missed_sleep) / len(missed_sleep)
            if abs(avg_done - avg_missed) >= 0.5:
                better = "more" if avg_done > avg_missed else "less"
                correlations.append(
                    f"You sleep {better} on days you do '{habit['name']}' "
                    f"({avg_done:.1f}h vs {avg_missed:.1f}h)"
                )

        if done_focus and missed_focus:
            avg_done = sum(done_focus) / len(done_focus)
            avg_missed = sum(missed_focus) / len(missed_focus)
            if abs(avg_done - avg_missed) >= 1.0:
                better = "higher" if avg_done > avg_missed else "lower"
                correlations.append(
                    f"Focus is {better} on '{habit['name']}' days "
                    f"({avg_done:.1f} vs {avg_missed:.1f})"
                )

    return correlations


def _generate_suggestions(habit_reports: list, today: date) -> list:
    """Generate actionable habit suggestions for today."""
    suggestions = []

    declining = [h for h in habit_reports if h["trend"] == "declining"]
    if declining:
        names = ", ".join(h["name"] for h in declining)
        suggestions.append(f"Focus on rebuilding: {names} (trending down)")

    # Highlight strong streaks to maintain
    strong_streaks = [h for h in habit_reports if h["streak"] >= 3]
    if strong_streaks:
        names = ", ".join(f"{h['name']} ({h['streak']}d)" for h in strong_streaks)
        suggestions.append(f"Keep the momentum: {names}")

    # Low completion rate habits
    struggling = [h for h in habit_reports if h["rate_7d"] < 50 and h["trend"] != "improving"]
    if struggling:
        for h in struggling:
            suggestions.append(f"Consider simplifying '{h['name']}' - only {h['rate_7d']}% completion this week")

    return suggestions


def format_habits_section(habit_data: dict) -> str:
    """Format habits into a readable briefing section."""
    lines = []
    lines.append("## Habit Status")
    lines.append("")

    for h in habit_data["habits"]:
        status = "done" if h["done_today"] else "not yet"
        trend_icon = {"improving": "^", "declining": "v", "stable": "="}[h["trend"]]
        lines.append(
            f"- **{h['name']}**: {status} | "
            f"Streak: {h['streak']}d | "
            f"7d rate: {h['rate_7d']}% | "
            f"Trend: {trend_icon} {h['trend']}"
        )
    lines.append("")

    if habit_data["correlations"]:
        lines.append("### Behavior Insights")
        for c in habit_data["correlations"]:
            lines.append(f"- {c}")
        lines.append("")

    if habit_data["suggestions"]:
        lines.append("### Suggestions")
        for s in habit_data["suggestions"]:
            lines.append(f"- {s}")
        lines.append("")

    return "\n".join(lines)
