"""Mochi AI — interactive chatbot with full data context."""

import json
from datetime import date
from pathlib import Path


def load_chat_history(data_path: str) -> dict:
    path = Path(data_path)
    if not path.exists():
        return {"conversations": []}
    with open(path) as f:
        return json.load(f)


def save_chat_history(data_path: str, data: dict):
    with open(data_path, "w") as f:
        json.dump(data, f, indent=2)


def build_context(data_dir: str) -> str:
    """Build a context string from all user data for the chatbot."""
    ctx_parts = []

    def _load(*parts):
        path = Path(data_dir).joinpath(*parts)
        if path.exists():
            with open(path) as f:
                return json.load(f)
        return {}

    # Tasks
    tasks = _load("tasks.json")
    active_tasks = [t for t in tasks.get("tasks", []) if t.get("status") != "done"]
    if active_tasks:
        ctx_parts.append(f"Active tasks ({len(active_tasks)}):")
        for t in active_tasks[:5]:
            ctx_parts.append(f"  - {t['title']} (deadline: {t.get('deadline','none')}, energy: {t.get('energy','medium')})")

    # Today's schedules
    today_str = date.today().isoformat()
    schedules = [s for s in tasks.get("schedules", []) if s.get("date") == today_str]
    if schedules:
        ctx_parts.append(f"\nToday's schedule ({len(schedules)} events):")
        for s in schedules:
            ctx_parts.append(f"  - {s.get('time_start','')}-{s.get('time_end','')} {s['title']}")

    # Habits
    habits = _load("habits.json")
    if habits.get("habits"):
        ctx_parts.append(f"\nHabits ({len(habits['habits'])}):")
        for h in habits["habits"]:
            done = h.get("history", {}).get(today_str, False)
            ctx_parts.append(f"  - {h['name']}: {'done' if done else 'not done'} today")

    # Latest metrics
    metrics = _load("metrics.json")
    entries = metrics.get("entries", [])
    if entries:
        latest = sorted(entries, key=lambda e: e["date"], reverse=True)[0]
        ctx_parts.append(f"\nLatest metrics ({latest['date']}):")
        if latest.get("sleep_hours"): ctx_parts.append(f"  Sleep: {latest['sleep_hours']}h")
        if latest.get("focus_score"): ctx_parts.append(f"  Focus: {latest['focus_score']}/10")
        if latest.get("steps"): ctx_parts.append(f"  Steps: {latest['steps']}")

    # Period
    period = _load("period.json")
    if period.get("cycles"):
        from src.period_tracker import get_current_phase
        phase = get_current_phase(str(Path(data_dir) / "period.json"))
        if phase.get("has_data"):
            ctx_parts.append(f"\nCycle: {phase.get('label','')} (day {phase.get('day_of_cycle')}, {phase.get('energy','')} energy)")

    # Grades
    grades = _load("grades.json")
    if grades.get("courses"):
        ctx_parts.append(f"\nCourses ({len(grades['courses'])}):")
        for c in grades["courses"]:
            ctx_parts.append(f"  - {c['name']} ({c.get('credits',3)} credits)")

    # Reading queue
    rq = _load("reading_queue.json")
    unread = sum(1 for i in rq.get("items", []) if i.get("status") == "unread")
    reading = sum(1 for i in rq.get("items", []) if i.get("status") == "reading")
    if unread or reading:
        ctx_parts.append(f"\nReading queue: {unread} unread, {reading} in progress")

    # Journal mood
    journal = _load("journal.json")
    today_j = None
    for e in journal.get("entries", []):
        if e.get("date") == today_str:
            today_j = e
            break
    if today_j:
        mood_labels = {1: "very low", 2: "low", 3: "neutral", 4: "good", 5: "great"}
        ctx_parts.append(f"\nToday's mood: {mood_labels.get(today_j.get('mood',3), 'neutral')}")

    return "\n".join(ctx_parts) if ctx_parts else "No data available yet."


def chat(message: str, api_key: str, model: str, data_dir: str,
         chat_history_path: str) -> str:
    """Send a message to Mochi AI and get a response."""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        context = build_context(data_dir)
        history = load_chat_history(chat_history_path)

        # Get recent conversation for context
        today_str = date.today().isoformat()
        recent_msgs = []
        for conv in history.get("conversations", []):
            if conv.get("date") == today_str:
                recent_msgs = conv.get("messages", [])[-10:]  # Last 10 messages
                break

        system_prompt = f"""You are Mochi, a warm, supportive AI assistant for a university student and researcher.
You know their schedule, tasks, habits, grades, and wellbeing data. Be concise, practical, and encouraging.
You can suggest what to study, how to prioritize, or just chat. Use casual, friendly language.

Current user context:
{context}

Today is {today_str}."""

        messages = [{"role": "system", "content": system_prompt}]
        for msg in recent_msgs:
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": message})

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=500,
        )

        reply = response.choices[0].message.content.strip()

        # Save conversation
        found = False
        for conv in history.get("conversations", []):
            if conv.get("date") == today_str:
                conv["messages"].append({"role": "user", "content": message})
                conv["messages"].append({"role": "assistant", "content": reply})
                found = True
                break
        if not found:
            history.setdefault("conversations", []).insert(0, {
                "date": today_str,
                "messages": [
                    {"role": "user", "content": message},
                    {"role": "assistant", "content": reply},
                ],
            })

        save_chat_history(chat_history_path, history)
        return reply
    except Exception as e:
        return f"Sorry, I'm having trouble connecting right now: {e}"
