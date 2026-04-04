"""Task prioritization engine using Eisenhower matrix scoring."""

import json
from datetime import datetime, date
from pathlib import Path


def load_tasks(data_path: str) -> dict:
    path = Path(data_path)
    if not path.exists():
        return {"tasks": [], "reminders": []}
    with open(path) as f:
        return json.load(f)


def calculate_urgency(deadline_str: str, today: date) -> float:
    """Score urgency 0-10 based on deadline proximity."""
    if not deadline_str:
        return 3.0  # no deadline = medium-low urgency
    deadline = datetime.strptime(deadline_str, "%Y-%m-%d").date()
    days_left = (deadline - today).days
    if days_left < 0:
        return 10.0  # overdue
    if days_left == 0:
        return 9.5
    if days_left == 1:
        return 8.0
    if days_left <= 3:
        return 6.0
    if days_left <= 7:
        return 4.0
    return 2.0


def classify_eisenhower(urgency: float, importance: float) -> str:
    """Classify into Eisenhower quadrant."""
    urgent = urgency >= 6.0
    important = importance >= 6.0
    if urgent and important:
        return "DO NOW"
    if not urgent and important:
        return "SCHEDULE"
    if urgent and not important:
        return "DELEGATE"
    return "DROP/DEFER"


def prioritize_tasks(data_path: str, metrics_summary: dict = None) -> dict:
    """Return prioritized tasks with Eisenhower classifications.

    Args:
        data_path: Path to tasks.json
        metrics_summary: Optional dict with energy-related metrics for smarter ordering
    """
    data = load_tasks(data_path)
    today = date.today()

    prioritized = []
    for task in data.get("tasks", []):
        if task.get("status") == "done":
            continue

        urgency = calculate_urgency(task.get("deadline", ""), today)
        importance = float(task.get("impact", 5))

        # Combined priority score
        priority_score = (urgency * 0.4) + (importance * 0.6)

        # Energy-aware adjustment: if user slept poorly, boost low-energy tasks
        energy_level = task.get("energy", "medium")
        if metrics_summary and metrics_summary.get("sleep_quality") == "poor":
            if energy_level == "low":
                priority_score += 1.0  # boost easy tasks on tired days
            elif energy_level == "high":
                priority_score -= 0.5  # demote hard tasks

        quadrant = classify_eisenhower(urgency, importance)

        deadline = task.get("deadline", "no deadline")
        days_left = None
        if task.get("deadline"):
            dl = datetime.strptime(task["deadline"], "%Y-%m-%d").date()
            days_left = (dl - today).days

        prioritized.append({
            "title": task["title"],
            "category": task.get("category", "general"),
            "quadrant": quadrant,
            "priority_score": round(priority_score, 1),
            "urgency": round(urgency, 1),
            "importance": importance,
            "energy": energy_level,
            "deadline": deadline,
            "days_left": days_left,
            "notes": task.get("notes", ""),
        })

    # Sort by priority score descending
    prioritized.sort(key=lambda x: x["priority_score"], reverse=True)

    # Get today's reminders
    todays_reminders = []
    for reminder in data.get("reminders", []):
        reminder_time = reminder.get("time", "")
        if reminder_time and reminder_time.startswith(today.isoformat()):
            todays_reminders.append({
                "text": reminder["text"],
                "time": reminder_time[11:16] if len(reminder_time) > 11 else "",
            })

    return {
        "prioritized_tasks": prioritized,
        "reminders": todays_reminders,
        "summary": {
            "total": len(prioritized),
            "do_now": sum(1 for t in prioritized if t["quadrant"] == "DO NOW"),
            "overdue": sum(1 for t in prioritized if t.get("days_left") is not None and t["days_left"] < 0),
        }
    }


def format_tasks_section(task_data: dict) -> str:
    """Format tasks into a readable briefing section."""
    lines = []
    lines.append("## Today's Tasks & Priorities")
    lines.append("")

    summary = task_data["summary"]
    if summary["overdue"] > 0:
        lines.append(f"**!! {summary['overdue']} overdue task(s) !!**")
    lines.append(f"Total active tasks: {summary['total']} | Urgent+Important: {summary['do_now']}")
    lines.append("")

    # Group by quadrant
    quadrants = {"DO NOW": [], "SCHEDULE": [], "DELEGATE": [], "DROP/DEFER": []}
    for task in task_data["prioritized_tasks"]:
        quadrants[task["quadrant"]].append(task)

    for quadrant_name, tasks in quadrants.items():
        if not tasks:
            continue
        lines.append(f"### {quadrant_name}")
        for t in tasks:
            deadline_info = ""
            if t["days_left"] is not None:
                if t["days_left"] < 0:
                    deadline_info = f" (OVERDUE by {abs(t['days_left'])}d)"
                elif t["days_left"] == 0:
                    deadline_info = " (TODAY)"
                elif t["days_left"] == 1:
                    deadline_info = " (tomorrow)"
                else:
                    deadline_info = f" ({t['days_left']}d left)"
            lines.append(f"- [{t['energy']} energy] **{t['title']}**{deadline_info} [{t['category']}]")
        lines.append("")

    if task_data["reminders"]:
        lines.append("### Reminders")
        for r in task_data["reminders"]:
            time_str = f" at {r['time']}" if r["time"] else ""
            lines.append(f"- {r['text']}{time_str}")
        lines.append("")

    return "\n".join(lines)
