from tools import add_task, load_tasks
from datetime import datetime, timedelta
import re


# -----------------------------
# TASK COMMAND
# -----------------------------
def cmd_task(text):

    if not text:
        return "Please provide a task."

    date_match = re.search(r"\[(.*?)\]", text)

    due = None

    if date_match:
        due = date_match.group(1)
        text = text.replace(date_match.group(0), "").strip()

    add_task(text, due)

    return f"Task added: {text}"


# -----------------------------
# REMINDER COMMAND
# -----------------------------
def cmd_reminder(text):

    if not text:
        return "Please provide a reminder."

    date_match = re.search(r"\[(.*?)\]", text)

    due = None

    if date_match:
        due = date_match.group(1)
        text = text.replace(date_match.group(0), "").strip()

    add_task(text, due)

    return f"Reminder set: {text}"


# -----------------------------
# SAVE NOTE
# -----------------------------
def cmd_notes(text):

    if not text:
        return "Please write something after /mochi-notes."

    with open("notes.txt", "a") as f:
        f.write(text + "\n")

    return f"Note saved: {text}"


# -----------------------------
# VIEW NOTES
# -----------------------------
def cmd_notes_view(text):

    try:

        with open("notes.txt", "r") as f:
            notes = f.readlines()

        if len(notes) == 0:
            return "You have no saved notes."

        response = "Your notes:\n\n"

        for i, note in enumerate(notes, 1):
            response += f"{i}. {note.strip()}\n"

        return response

    except FileNotFoundError:
        return "No notes found yet."

# -----------------------------
# DELETE NOTE
# -----------------------------
def cmd_notes_delete(text):

    try:
        index = int(text.strip()) - 1
    except:
        return "Please provide the note number. Example: /mochi-notes-delete 2"

    try:

        with open("notes.txt", "r") as f:
            notes = f.readlines()

        if index < 0 or index >= len(notes):
            return "Invalid note number."

        removed = notes.pop(index)

        with open("notes.txt", "w") as f:
            f.writelines(notes)

        return f"Deleted note: {removed.strip()}"

    except FileNotFoundError:
        return "No notes found."

# -----------------------------
# TODAY TASKS
# -----------------------------
def cmd_today(text):

    tasks = load_tasks()

    today = datetime.now().strftime("%Y-%m-%d")

    today_tasks = []

    for t in tasks:

        if t.get("due") and t["due"].startswith(today):
            today_tasks.append(t)

    if not today_tasks:
        return "You have no tasks today."

    response = "Today's tasks:\n\n"

    for t in today_tasks:
        response += f"• {t['content']} ({t['due']})\n"

    return response


# -----------------------------
# WEEK TASKS
# -----------------------------
def cmd_week(text):

    tasks = load_tasks()

    today = datetime.now()
    week = today + timedelta(days=7)

    week_tasks = []

    for t in tasks:

        if not t.get("due"):
            continue

        due = datetime.fromisoformat(t["due"])

        if today <= due <= week:
            week_tasks.append(t)

    if not week_tasks:
        return "You have no tasks this week."

    response = "This week's tasks:\n\n"

    for t in week_tasks:
        response += f"• {t['content']} ({t['due']})\n"

    return response


# -----------------------------
# HELP COMMAND
# -----------------------------
def cmd_help(text):

    return """
Available commands:

/mochi-task <task> [YYYY-MM-DD]
/mochi-reminder <text> [YYYY-MM-DD]

/mochi-notes <text>
/mochi-notes-view

/mochi-today
/mochi-week

Example:
/mochi-task finish research paper [2026-03-15]
"""


# -----------------------------
# COMMAND ROUTER
# -----------------------------
COMMANDS = {

    "/mochi-task": cmd_task,
    "/mochi-reminder": cmd_reminder,
    "/mochi-notes-view": cmd_notes_view,
    "/mochi-notes-delete": cmd_notes_delete,
    "/mochi-notes": cmd_notes,
    "/mochi-today": cmd_today,
    "/mochi-week": cmd_week,
    "/mochi-help": cmd_help
}


# -----------------------------
# MAIN COMMAND HANDLER
# -----------------------------
def handle_command(message):

    # check longer commands first
    for command in sorted(COMMANDS.keys(), key=len, reverse=True):

        if message.startswith(command):

            text = message.replace(command, "").strip()

            return COMMANDS[command](text)

    return "Unknown command. Try /mochi-help"