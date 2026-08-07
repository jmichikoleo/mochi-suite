from datetime import datetime
from tools import load_json, TASKS_FILE


def generate_daily_briefing():

    tasks = load_json(TASKS_FILE)

    today = datetime.now().strftime("%Y-%m-%d")

    todays_tasks = [
        t for t in tasks
        if t["due"] and t["due"].startswith(today)
    ]

    message = "☀️ Good morning.\n\n"

    if todays_tasks:

        message += f"You have {len(todays_tasks)} tasks today:\n"

        for t in todays_tasks:
            message += f"• {t['content']}\n"

    else:
        message += "You have no scheduled tasks today."

    return message