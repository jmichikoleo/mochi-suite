#!/usr/bin/env python3
"""Standalone email digest sender — works without Flask server running."""

import sys
from pathlib import Path
from datetime import date, timedelta

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import yaml
from src import tasks, habits, metrics, focus, schedules, food_log, journal
from src import period_tracker, nudges, goals, weather as weather_mod
from src.email_digest import send_digest


def dp(filename):
    return str(PROJECT_ROOT / "data" / filename)


def main():
    # Load config
    with open(PROJECT_ROOT / "config" / "settings.yaml") as f:
        config = yaml.safe_load(f)

    email_cfg = config.get("email", {})
    if not email_cfg.get("sender_email") or email_cfg.get("sender_email") == "YOUR_EMAIL@gmail.com":
        print("[Digest] No email configured. Set it in config/settings.yaml")
        return

    print("[Digest] Generating briefing...")

    # Build briefing data (same as /api/briefing + /api/send-digest)
    cycle_data = period_tracker.get_current_phase(dp("period.json"))
    cycle_phase = cycle_data if cycle_data and cycle_data.get("has_data") else None

    metrics_data = metrics.analyze_metrics(dp("metrics.json"), cycle_phase)
    task_data = tasks.prioritize_tasks(dp("tasks.json"), metrics_data)

    today_schedules = schedules.get_today_schedules(dp("tasks.json"))
    food_today_data = food_log.get_food_summary(dp("food_log.json"))

    yesterday = (date.today() - timedelta(days=1)).isoformat()
    food_yesterday = food_log.get_food_summary(dp("food_log.json"), yesterday)
    journal_yesterday = journal.get_entry(dp("journal.json"), yesterday)
    summary_card = focus.generate_summary_card(
        metrics_data, food_yesterday, task_data, journal_yesterday, cycle_phase)

    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    tomorrow_schedules = schedules.get_today_schedules(dp("tasks.json"), tomorrow)
    sleep_rec = focus.generate_sleep_recommendation(metrics_data, tomorrow_schedules)

    focus_data = focus.generate_focus_plan(
        task_data, {}, metrics_data,
        schedules=today_schedules, food_today=food_today_data, cycle_phase=cycle_phase)

    wc = config.get("weather", {})
    weather_data = weather_mod.fetch_weather(
        wc.get("api_key", ""), wc.get("city", "Busan"), wc.get("country", "KR"))

    # Goals
    goals_data = goals.load_goals(dp("goals.json"))
    goals_list = []
    for g in goals_data.get("goals", []):
        if g.get("status") == "active":
            summary = goals.get_goal_summary(g)
            goals_list.append({**g, "summary": summary})

    briefing = {
        "date": date.today().isoformat(),
        "focus": focus_data,
        "summary_card": summary_card,
        "sleep_rec": sleep_rec,
        "tasks": task_data,
        "schedules_today": today_schedules,
        "weather": weather_data,
        "nudges": nudges.generate_nudges(str(PROJECT_ROOT / "data")),
        "goals": goals_list,
    }

    # Send email
    print("[Digest] Sending email...")
    success = send_digest(
        email_cfg.get("smtp_host", "smtp.gmail.com"),
        email_cfg.get("smtp_port", 587),
        email_cfg["sender_email"],
        email_cfg["sender_password"],
        email_cfg.get("recipient_email", email_cfg["sender_email"]),
        briefing
    )

    if success:
        print("[Digest] Email sent successfully!")
    else:
        print("[Digest] Failed to send email.")


if __name__ == "__main__":
    main()
