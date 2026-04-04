"""Focus suggestion engine combining tasks, habits, metrics, AND schedules."""


def generate_focus_plan(task_data: dict, habit_data: dict, metrics_data: dict,
                        schedules: list = None, food_today: dict = None,
                        cycle_phase: dict = None) -> dict:
    """Generate a schedule-aware, cycle-aware focus plan for the day.

    Instead of generic morning/afternoon/evening blocks, this analyzes the
    actual schedule to find free windows and places tasks intelligently.
    """
    schedules = schedules or []

    sleep_quality = "average"
    focus_trend = "stable"
    latest_focus = 5

    if metrics_data.get("has_data"):
        sleep_quality = metrics_data["sleep"].get("quality", "average")
        focus_trend = metrics_data["focus"].get("trend", "stable")
        latest_focus = metrics_data["focus"].get("latest", 5)

    # Cycle-phase override: adjust effective energy level
    cycle_override = None
    if cycle_phase and cycle_phase.get("has_data") and cycle_phase.get("task_strategy"):
        cycle_override = cycle_phase["task_strategy"]
        # During menstrual phase, override to "poor" regardless of sleep
        if cycle_override == "poor" and sleep_quality != "poor":
            sleep_quality = "poor"

    tasks = [t for t in task_data.get("prioritized_tasks", []) if t.get("status") != "done"]
    habits = habit_data.get("habits", [])
    undone_habits = [h for h in habits if not h.get("done_today")]

    # Classify tasks by energy level
    high_energy = [t for t in tasks if t.get("energy") == "high" and t["quadrant"] in ("DO NOW", "SCHEDULE")]
    medium_energy = [t for t in tasks if t.get("energy") == "medium" and t["quadrant"] in ("DO NOW", "SCHEDULE")]
    low_energy = [t for t in tasks if t.get("energy") == "low"]

    # Build schedule-aware time blocks
    time_blocks = _build_schedule_aware_plan(
        sleep_quality, schedules, high_energy, medium_energy, low_energy, undone_habits
    )

    # Energy forecast
    if sleep_quality == "good":
        energy_forecast = "High energy expected. Great day for deep work."
    elif sleep_quality == "poor":
        energy_forecast = "Low energy expected. Go easy on yourself - focus on essentials only."
    else:
        energy_forecast = "Moderate energy expected. Pace yourself through the day."

    # Add cycle phase context
    if cycle_phase and cycle_phase.get("has_data") and cycle_phase.get("phase"):
        phase = cycle_phase["phase"]
        emoji = cycle_phase.get("emoji", "")
        day = cycle_phase.get("day_of_cycle", "?")
        best = ", ".join(cycle_phase.get("best_for", [])[:2])
        energy_forecast += f" {emoji} {cycle_phase.get('label', phase)} (day {day})"
        if best:
            energy_forecast += f" — good for {best}."

    # Add schedule context to forecast
    if schedules:
        sch_names = [s.get("title", "") for s in schedules[:3]]
        busy_count = len(schedules)
        if busy_count >= 3:
            energy_forecast += f" Busy day with {busy_count} scheduled events."
        elif busy_count > 0:
            energy_forecast += f" You have: {', '.join(sch_names)}."

    tip = _generate_tip(sleep_quality, focus_trend, habit_data, schedules, food_today, cycle_phase)

    return {
        "time_blocks": time_blocks,
        # Keep legacy keys for backward compat
        "morning": time_blocks[0] if len(time_blocks) > 0 else _empty_block("Morning"),
        "afternoon": time_blocks[1] if len(time_blocks) > 1 else _empty_block("Afternoon"),
        "evening": time_blocks[2] if len(time_blocks) > 2 else _empty_block("Evening"),
        "energy_forecast": energy_forecast,
        "tip": tip,
    }


def _build_schedule_aware_plan(sleep_quality: str, schedules: list,
                                high: list, medium: list, low: list,
                                undone_habits: list) -> list:
    """Build time blocks around the actual schedule."""

    # Parse schedule into occupied time ranges
    occupied = []
    for s in schedules:
        start = _time_to_minutes(s.get("time_start", ""))
        end = _time_to_minutes(s.get("time_end", ""))
        if start is not None and end is not None:
            occupied.append({
                "start": start, "end": end,
                "title": s.get("title", ""),
                "type": s.get("type", ""),
            })
    occupied.sort(key=lambda x: x["start"])

    # Define the day's window (7am - 10pm)
    DAY_START = 7 * 60   # 7:00
    DAY_END = 22 * 60    # 22:00

    # Find free windows
    free_windows = []
    current = DAY_START
    for occ in occupied:
        if occ["start"] > current:
            free_windows.append({"start": current, "end": occ["start"], "after": None})
        current = max(current, occ["end"])
        free_windows.append({"start": occ["start"], "end": occ["end"],
                              "is_scheduled": True, "title": occ["title"], "type": occ["type"]})
    if current < DAY_END:
        free_windows.append({"start": current, "end": DAY_END, "after": occupied[-1]["title"] if occupied else None})

    if not occupied:
        # No schedules — use classic 3-block plan
        return _build_classic_plan(sleep_quality, high, medium, low, undone_habits)

    # Build smart blocks from free windows
    blocks = []
    task_pool_high = list(high)
    task_pool_med = list(medium)
    task_pool_low = list(low)
    habit_pool = list(undone_habits)

    for window in free_windows:
        if window.get("is_scheduled"):
            # This is a scheduled event — show it as a fixed block
            blocks.append({
                "label": f"{_fmt_time(window['start'])} - {_fmt_time(window['end'])}  {window['title']}",
                "tasks": [],
                "habits": [],
                "schedules": [window["title"]],
                "note": f"[{window.get('type', 'event').title()}] - blocked",
                "is_scheduled": True,
                "duration": window["end"] - window["start"],
            })
            continue

        duration = window["end"] - window["start"]
        if duration < 15:
            continue  # Skip tiny gaps

        period = _get_period(window["start"])
        block_tasks = []
        block_habits = []

        if duration >= 90:
            # Long window — assign high-energy tasks
            if sleep_quality != "poor" and task_pool_high:
                block_tasks.append(task_pool_high.pop(0)["title"])
            if task_pool_med:
                block_tasks.append(task_pool_med.pop(0)["title"])
        elif duration >= 45:
            # Medium window
            if task_pool_med:
                block_tasks.append(task_pool_med.pop(0)["title"])
            elif task_pool_low:
                block_tasks.append(task_pool_low.pop(0)["title"])
        else:
            # Short window (15-45 min)
            if task_pool_low:
                block_tasks.append(task_pool_low.pop(0)["title"])
            # Good for habits
            if habit_pool:
                block_habits.append(habit_pool.pop(0)["name"])

        # If still no tasks assigned and we have any left
        if not block_tasks and duration >= 30:
            for pool in [task_pool_high, task_pool_med, task_pool_low]:
                if pool:
                    block_tasks.append(pool.pop(0)["title"])
                    break

        # Assign habits to morning/evening windows
        if period == "morning" and habit_pool:
            morning_habits = [h for h in habit_pool if h["name"] in ("Exercise", "Meditate")]
            for h in morning_habits:
                block_habits.append(h["name"])
                habit_pool.remove(h)
        elif period == "evening" and habit_pool:
            evening_habits = [h for h in habit_pool if h["name"] in ("Read 30min", "Journal", "Read")]
            for h in evening_habits:
                block_habits.append(h["name"])
                habit_pool.remove(h)

        # Generate note
        note = _generate_block_note(period, duration, sleep_quality, window.get("after"))

        label = f"{_fmt_time(window['start'])} - {_fmt_time(window['end'])}  Free ({duration}min)"

        blocks.append({
            "label": label,
            "tasks": block_tasks,
            "habits": block_habits,
            "schedules": [],
            "note": note,
            "is_scheduled": False,
            "duration": duration,
        })

    # If remaining tasks/habits weren't assigned, add them to the last free block
    remaining_tasks = [t["title"] for t in task_pool_high + task_pool_med + task_pool_low]
    remaining_habits = [h["name"] for h in habit_pool]
    if (remaining_tasks or remaining_habits) and blocks:
        last_free = None
        for b in reversed(blocks):
            if not b.get("is_scheduled"):
                last_free = b
                break
        if last_free:
            last_free["tasks"].extend(remaining_tasks)
            last_free["habits"].extend(remaining_habits)
            if remaining_tasks:
                last_free["note"] = (last_free.get("note", "") + " Also: " +
                                      ", ".join(remaining_tasks[:3])).strip()

    return blocks if blocks else _build_classic_plan(sleep_quality, high, medium, low, undone_habits)


def _build_classic_plan(sleep_quality: str, high: list, medium: list,
                         low: list, undone_habits: list) -> list:
    """Fallback: classic 3-block plan when no schedules exist."""
    if sleep_quality == "poor":
        return [
            {"label": "Morning (gentle start)", "tasks": [t["title"] for t in (medium[:1] + low[:1])],
             "habits": [h["name"] for h in undone_habits if h["name"] in ("Meditate", "Journal")],
             "schedules": [], "note": "Start slow. Coffee first, then one manageable task.",
             "is_scheduled": False, "duration": 240},
            {"label": "Afternoon (peak window)", "tasks": [t["title"] for t in high[:2]],
             "habits": [], "schedules": [],
             "note": "Your best focus window on tired days. Tackle the hardest thing here.",
             "is_scheduled": False, "duration": 240},
            {"label": "Evening (wind down)", "tasks": [t["title"] for t in low[:2]],
             "habits": [h["name"] for h in undone_habits if h["name"] not in ("Meditate", "Journal")],
             "schedules": [], "note": "Wrap up easy tasks. Prioritize sleep tonight.",
             "is_scheduled": False, "duration": 240},
        ]
    elif sleep_quality == "good":
        return [
            {"label": "Morning (deep work)", "tasks": [t["title"] for t in high[:2]],
             "habits": [h["name"] for h in undone_habits if h["name"] in ("Exercise", "Meditate")],
             "schedules": [], "note": "You're well-rested. Attack the hardest problems first.",
             "is_scheduled": False, "duration": 240},
            {"label": "Afternoon (execution)",
             "tasks": [t["title"] for t in (medium[:2] + high[2:3])],
             "habits": [h["name"] for h in undone_habits if h["name"] == "Read 30min"],
             "schedules": [], "note": "Keep the momentum.",
             "is_scheduled": False, "duration": 240},
            {"label": "Evening (review & reflect)", "tasks": [t["title"] for t in low[:2]],
             "habits": [h["name"] for h in undone_habits if h["name"] == "Journal"],
             "schedules": [], "note": "Review what you accomplished. Journal and plan tomorrow.",
             "is_scheduled": False, "duration": 240},
        ]
    else:
        return [
            {"label": "Morning (focus block)",
             "tasks": [t["title"] for t in high[:1] + medium[:1]],
             "habits": [h["name"] for h in undone_habits if h["name"] in ("Exercise", "Meditate")],
             "schedules": [], "note": "Start with one important task before distractions pile up.",
             "is_scheduled": False, "duration": 240},
            {"label": "Afternoon (productivity)",
             "tasks": [t["title"] for t in (medium[:2] + high[1:2])],
             "habits": [], "schedules": [],
             "note": "Batch similar tasks together for efficiency.",
             "is_scheduled": False, "duration": 240},
            {"label": "Evening (wrap up)", "tasks": [t["title"] for t in low[:2]],
             "habits": [h["name"] for h in undone_habits if h["name"] in ("Read 30min", "Journal")],
             "schedules": [], "note": "Finish easy tasks and unwind with habits.",
             "is_scheduled": False, "duration": 240},
        ]


def _time_to_minutes(time_str: str):
    """Convert 'HH:MM' to minutes since midnight."""
    if not time_str or ":" not in time_str:
        return None
    try:
        parts = time_str.split(":")
        return int(parts[0]) * 60 + int(parts[1])
    except (ValueError, IndexError):
        return None


def _fmt_time(minutes: int) -> str:
    """Format minutes since midnight to 'HH:MM'."""
    h = minutes // 60
    m = minutes % 60
    return f"{h:02d}:{m:02d}"


def _get_period(minutes: int) -> str:
    if minutes < 12 * 60:
        return "morning"
    if minutes < 17 * 60:
        return "afternoon"
    return "evening"


def _generate_block_note(period: str, duration: int, sleep_quality: str, after_event: str = None) -> str:
    """Generate contextual note for a time block."""
    notes = []
    if after_event:
        notes.append(f"After {after_event}.")

    if duration >= 120:
        if sleep_quality == "good":
            notes.append("Long free block - perfect for deep work.")
        elif sleep_quality == "poor":
            notes.append("Long block but low energy - tackle one thing well, then rest.")
        else:
            notes.append("Good chunk of time. Focus on your top priority.")
    elif duration >= 60:
        notes.append("Solid hour. Pick one important task.")
    elif duration >= 30:
        notes.append("Quick window. Knock out a small task or habit.")
    else:
        notes.append("Short break. Stretch, hydrate, or review notes.")

    return " ".join(notes)


def _empty_block(label: str) -> dict:
    return {"label": label, "tasks": [], "habits": [], "schedules": [],
            "note": "", "is_scheduled": False, "duration": 0}


def generate_sleep_recommendation(metrics_data: dict, tomorrow_schedules: list) -> dict:
    """Suggest optimal bedtime based on tomorrow's first event and sleep debt."""
    from datetime import timedelta

    # Find tomorrow's first event
    first_event = None
    first_time = None
    if tomorrow_schedules:
        for s in sorted(tomorrow_schedules, key=lambda x: x.get("time_start", "99:99")):
            t = _time_to_minutes(s.get("time_start", ""))
            if t is not None:
                first_event = s.get("title", "event")
                first_time = t
                break

    # Calculate sleep debt from past week
    sleep_debt = 0
    target = 7.5
    if metrics_data.get("has_data"):
        avg = metrics_data["sleep"].get("avg_7d", 7)
        sleep_debt = round(max(0, (target - avg) * 7), 1)

    # Suggest bedtime
    if first_time is not None:
        # Wake up 45min before first event (prep time)
        wake_time = first_time - 45
        # Need 8h sleep if debt, 7.5h otherwise
        sleep_needed = 8.0 if sleep_debt > 3 else 7.5
        bedtime_min = wake_time - int(sleep_needed * 60)
        if bedtime_min < 0:
            bedtime_min += 24 * 60
        suggested_bedtime = _fmt_time(bedtime_min)
        wake_str = _fmt_time(wake_time)
    else:
        suggested_bedtime = "23:00"
        wake_str = None

    recovery_tip = ""
    if sleep_debt > 5:
        recovery_tip = f"You have {sleep_debt}h of sleep debt. Try to sleep 30min earlier tonight."
    elif sleep_debt > 2:
        recovery_tip = f"Mild sleep debt ({sleep_debt}h). A consistent bedtime will help recover."
    else:
        recovery_tip = "Sleep is on track! Keep it consistent."

    return {
        "suggested_bedtime": suggested_bedtime,
        "wake_time": wake_str,
        "first_event": f"{_fmt_time(first_time)} {first_event}" if first_time else None,
        "sleep_debt": sleep_debt,
        "recovery_tip": recovery_tip,
    }


def generate_summary_card(metrics_data: dict, food_data: dict = None,
                          task_data: dict = None, journal_data: dict = None,
                          cycle_phase: dict = None) -> dict:
    """Generate yesterday's summary card for the Focus page."""
    insights = []
    score_parts = []

    if metrics_data.get("has_data"):
        sleep = metrics_data["sleep"]
        if sleep["latest"]:
            if sleep["latest"] < 6:
                insights.append(f"You only slept {sleep['latest']}h. Take it easy today and prioritize rest tonight.")
            elif sleep["latest"] >= 8:
                insights.append(f"Great sleep at {sleep['latest']}h! You should have solid energy today.")
            else:
                insights.append(f"You got {sleep['latest']}h of sleep. Decent - pace yourself well.")
            score_parts.append(min(sleep["latest"] / 8.0, 1.0))

        steps = metrics_data.get("steps", {})
        if steps.get("has_data") and steps.get("latest"):
            if steps["latest"] < 5000:
                insights.append(f"Only {steps['latest']:,} steps yesterday. Try to move more today!")
            elif steps["latest"] >= 10000:
                insights.append(f"Crushed it with {steps['latest']:,} steps yesterday!")
            score_parts.append(min(steps["latest"] / 10000, 1.0))

        water = metrics_data.get("water", {})
        if water.get("has_data") and water.get("latest"):
            if water["latest"] < 1500:
                insights.append(f"Low water intake ({water['latest']}ml). Stay hydrated today!")
            elif water["latest"] >= 2000:
                insights.append(f"Good hydration at {water['latest']}ml.")
            score_parts.append(min(water["latest"] / 2000, 1.0))

        coffee = metrics_data.get("coffee", {})
        if coffee.get("has_data") and coffee.get("latest"):
            if coffee["latest"] >= 4:
                insights.append(f"{coffee['latest']} coffees yesterday - maybe ease up today?")

        focus = metrics_data.get("focus", {})
        if focus.get("trend") == "declining":
            insights.append("Focus has been declining. Consider shorter, focused work blocks today.")
        elif focus.get("trend") == "improving":
            insights.append("Focus trending up! Great time to tackle challenging tasks.")

    if food_data and food_data.get("total_kcal"):
        kcal = food_data["total_kcal"]
        if kcal < 1200:
            insights.append(f"You only ate {kcal} kcal yesterday. Make sure to eat well today!")
        elif kcal > 2500:
            insights.append(f"High calorie day yesterday ({kcal} kcal). Maybe a lighter day today?")
        score_parts.append(min(kcal / 2000, 1.0) if kcal <= 2000 else max(1.0 - (kcal - 2000) / 2000, 0.5))

    if task_data:
        done = sum(1 for t in task_data.get("prioritized_tasks", []) if t.get("status") == "done")
        total = task_data.get("summary", {}).get("total", 0)
        if total > 0:
            completion_rate = done / total
            if completion_rate >= 0.8:
                insights.append(f"You completed {done}/{total} tasks. Productive day!")
            elif completion_rate < 0.3 and total > 2:
                insights.append(f"Only {done}/{total} tasks done. Focus on fewer, higher-impact tasks today.")

    if journal_data and journal_data.get("mood"):
        mood = journal_data["mood"]
        mood_labels = {1: "rough", 2: "meh", 3: "okay", 4: "good", 5: "great"}
        label = mood_labels.get(mood, "okay")
        if mood <= 2:
            insights.append(f"You felt {label} yesterday. Be gentle with yourself today.")
        elif mood >= 4:
            insights.append(f"You felt {label} yesterday! Keep that momentum going.")

    # Cycle phase context
    if cycle_phase and cycle_phase.get("has_data") and cycle_phase.get("phase"):
        phase = cycle_phase["phase"]
        emoji = cycle_phase.get("emoji", "")
        best = cycle_phase.get("best_for", [])
        insights.append(f"{emoji} You're in your {cycle_phase.get('label', phase)}. Best for: {', '.join(best[:3])}")

    overall_score = round(sum(score_parts) / len(score_parts) * 100) if score_parts else None

    if not insights:
        insights.append("Start logging your daily metrics to get personalized insights!")

    return {
        "insights": insights,
        "overall_score": overall_score,
        "has_data": bool(score_parts),
    }


def _generate_tip(sleep_quality: str, focus_trend: str, habit_data: dict,
                   schedules: list = None, food_today: dict = None,
                   cycle_phase: dict = None) -> str:
    """Generate one actionable focus tip for the day."""
    tips = []

    # Cycle-phase tips (highest priority)
    if cycle_phase and cycle_phase.get("phase"):
        phase = cycle_phase["phase"]
        if phase == "menstrual":
            tips.append("Be extra kind to yourself today. Warm drinks, lighter workload, more breaks.")
        elif phase == "ovulatory":
            tips.append("Peak energy phase! Schedule your most important meeting or presentation today.")
        elif phase == "luteal" and cycle_phase.get("day_of_cycle", 0) > 24:
            tips.append("Late luteal phase — PMS may affect focus. Stick to routine tasks and plan ahead.")
        avoid = cycle_phase.get("avoid", [])
        if avoid:
            tips.append(f"This phase: consider avoiding {', '.join(avoid[:2])}.")

    # Schedule-aware tips
    if schedules:
        count = len(schedules)
        if count >= 3:
            tips.append(f"You have {count} events today. Protect 30min between events for transitions and prep.")
        # Check for back-to-back
        for i in range(len(schedules) - 1):
            end = _time_to_minutes(schedules[i].get("time_end", ""))
            start = _time_to_minutes(schedules[i + 1].get("time_start", ""))
            if end and start and start - end < 15:
                tips.append("You have back-to-back events. Prepare materials in advance and take micro-breaks.")
                break

    if sleep_quality == "poor":
        tips.append("Consider a 20-minute power nap between events to recharge.")
    if focus_trend == "declining":
        tips.append("Focus has been declining. Try the Pomodoro technique: 25min work, 5min break.")
    if focus_trend == "improving":
        tips.append("Your focus is on an upswing! Capitalize by scheduling your hardest task in the morning.")

    if food_today and food_today.get("total_kcal", 0) == 0:
        tips.append("You haven't logged any food yet. Don't skip meals - your brain needs fuel!")

    for corr in habit_data.get("correlations", []):
        if "sleep more" in corr or "sleep better" in corr:
            tips.append("Your data shows a habit-sleep connection. Prioritize that habit today.")
            break

    if not tips:
        tips.append("Block 2 hours of uninterrupted time for your most important task today.")

    return tips[0]


def format_focus_section(focus_data: dict) -> str:
    """Format focus plan into a readable briefing section."""
    lines = []
    lines.append("## Focus Plan for Today")
    lines.append("")
    lines.append(f"*{focus_data['energy_forecast']}*")
    lines.append("")

    for block in focus_data.get("time_blocks", []):
        if block.get("is_scheduled"):
            lines.append(f"### [SCHEDULED] {block['label']}")
        else:
            lines.append(f"### {block['label']}")

        if block.get("tasks"):
            for t in block["tasks"]:
                lines.append(f"  - {t}")

        if block.get("habits"):
            for h in block["habits"]:
                lines.append(f"  - [Habit] {h}")

        if block.get("note"):
            lines.append(f"*{block['note']}*")
        lines.append("")

    lines.append(f"**Tip of the day**: {focus_data['tip']}")
    lines.append("")

    return "\n".join(lines)
