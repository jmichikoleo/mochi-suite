#!/usr/bin/env python3
"""Mochi's Assistant - Flask Web Dashboard

Run: python3 src/app.py
Open: http://localhost:5050
"""

import json
import sys
from datetime import date, timedelta
from pathlib import Path

from flask import Flask, render_template, jsonify, request

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import yaml
from src import tasks, habits, metrics, papers, news, substack, focus
from src import schedules, food_log, journal, media_log, paper_summarizer, stocks, bookmarks
from src import tarot, weather as weather_mod
from src import study_log, reading_queue, grades, period_tracker, weekly_review
from src import lab_papers, lab_notes, uni_materials, flashcards, chatbot, nudges, goals
from src import expenses, watchlist, wishlist, recipes
from src import brain_dump, achievements, monthly_report
from src import global_search, email_digest

app = Flask(__name__, template_folder=str(PROJECT_ROOT / "templates"))


def get_config():
    with open(PROJECT_ROOT / "config" / "settings.yaml") as f:
        return yaml.safe_load(f)

def get_interests():
    with open(PROJECT_ROOT / "config" / "interests.yaml") as f:
        return yaml.safe_load(f)

def dp(filename):
    return str(PROJECT_ROOT / "data" / filename)


# ─── Pages ───────────────────────────────────────────────────────────

@app.route("/")
def dashboard():
    return render_template("dashboard.html")

@app.route("/lab")
def lab_page():
    return render_template("lab.html")

@app.route("/uni")
def uni_page():
    return render_template("uni.html")

@app.route("/chat")
def chat_page():
    return render_template("chat.html")


# ─── Briefing API ────────────────────────────────────────────────────

@app.route("/api/briefing")
def api_briefing():
    """Fast briefing — local data only. External data loaded lazily by frontend."""
    cycle_data = period_tracker.get_current_phase(dp("period.json"))
    cycle_phase = cycle_data if cycle_data and cycle_data.get("has_data") else None

    metrics_data = metrics.analyze_metrics(dp("metrics.json"), cycle_phase)
    task_data = tasks.prioritize_tasks(dp("tasks.json"), metrics_data)
    metrics_raw = metrics.load_metrics(dp("metrics.json"))
    habit_data = habits.analyze_habits(dp("habits.json"), metrics_raw.get("entries", []))

    today_schedules = schedules.get_today_schedules(dp("tasks.json"))
    food_today_data = food_log.get_food_summary(dp("food_log.json"))

    focus_data = focus.generate_focus_plan(
        task_data, habit_data, metrics_data,
        schedules=today_schedules, food_today=food_today_data,
        cycle_phase=cycle_phase
    )

    yesterday = (date.today() - timedelta(days=1)).isoformat()
    food_yesterday = food_log.get_food_summary(dp("food_log.json"), yesterday)
    journal_yesterday = journal.get_entry(dp("journal.json"), yesterday)
    summary_card = focus.generate_summary_card(
        metrics_data, food_yesterday, task_data, journal_yesterday, cycle_phase
    )

    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    tomorrow_schedules = schedules.get_today_schedules(dp("tasks.json"), tomorrow)
    sleep_rec = focus.generate_sleep_recommendation(metrics_data, tomorrow_schedules)

    return jsonify({
        "date": date.today().isoformat(),
        "focus": focus_data,
        "summary_card": summary_card,
        "sleep_rec": sleep_rec,
        "cycle": cycle_data,
        "tasks": task_data,
        "habits": habit_data,
        "metrics": metrics_data,
        "schedules_today": today_schedules,
        "food_today": food_today_data,
        "nudges": nudges.generate_nudges(str(PROJECT_ROOT / "data")),
        "goals": _get_goals_summary(),
        "commute_warnings": schedules.detect_commute_needs(today_schedules),
        "new_badges": achievements.check_and_unlock(str(PROJECT_ROOT / "data")),
        # Placeholders — loaded lazily by frontend
        "papers": {"papers": [], "papers_read_total": 0, "topics_studied": [], "connections": [], "next_topics": []},
        "substack": {},
        "news": {"political": [], "finance": {"korean": [], "indonesian": [], "american": []}},
        "weather": {"has_data": False},
    })


@app.route("/api/external")
def api_external():
    """Slow external data — papers, news, substack, weather, stocks. Loaded lazily."""
    config = get_config()
    interests = get_interests()

    paper_config = config.get("papers", {})
    paper_data = papers.get_paper_recommendations(
        dp("paper_history.json"),
        paper_config.get("search_queries", ["LLM routing"]),
        paper_config.get("categories", ["cs.CL", "cs.AI"]),
    )

    news_config = config.get("news", {})
    news_data = news.fetch_all_news(news_config)

    substack_feeds = interests.get("substack", {}).get("feeds", [])
    substack_topics = interests.get("substack", {}).get("topics", [])
    substack_post = substack.recommend_post(substack_feeds, substack_topics)

    wc = config.get("weather", {})
    weather_data = weather_mod.fetch_weather(
        wc.get("api_key", ""), wc.get("city", "Busan"), wc.get("country", "KR"))

    return jsonify({
        "papers": paper_data,
        "substack": substack_post,
        "news": news_data,
        "weather": weather_data,
    })


def _get_goals_summary():
    """Get active goals with summaries for briefing."""
    data = goals.load_goals(dp("goals.json"))
    result = []
    for g in data.get("goals", []):
        if g.get("status") == "active":
            summary = goals.get_goal_summary(g)
            result.append({**g, "summary": summary})
    return result


# ─── Tasks API ───────────────────────────────────────────────────────

@app.route("/api/tasks")
def api_get_tasks():
    return jsonify(tasks.load_tasks(dp("tasks.json")))

@app.route("/api/tasks", methods=["POST"])
def api_add_task():
    data = tasks.load_tasks(dp("tasks.json"))
    data["tasks"].append(request.json)
    _save_json("tasks.json", data)
    return jsonify({"ok": True})

@app.route("/api/tasks/<int:index>", methods=["PUT"])
def api_update_task(index):
    data = tasks.load_tasks(dp("tasks.json"))
    if 0 <= index < len(data["tasks"]):
        data["tasks"][index].update(request.json)
        _save_json("tasks.json", data)
        return jsonify({"ok": True})
    return jsonify({"error": "Invalid index"}), 404

@app.route("/api/tasks/<int:index>", methods=["DELETE"])
def api_delete_task(index):
    data = tasks.load_tasks(dp("tasks.json"))
    if 0 <= index < len(data["tasks"]):
        data["tasks"].pop(index)
        _save_json("tasks.json", data)
        return jsonify({"ok": True})
    return jsonify({"error": "Invalid index"}), 404


# ─── Reminders API ──────────────────────────────────────────────────

@app.route("/api/reminders", methods=["POST"])
def api_add_reminder():
    data = tasks.load_tasks(dp("tasks.json"))
    data.setdefault("reminders", []).append(request.json)
    _save_json("tasks.json", data)
    return jsonify({"ok": True})

@app.route("/api/reminders/<int:index>", methods=["DELETE"])
def api_delete_reminder(index):
    data = tasks.load_tasks(dp("tasks.json"))
    if 0 <= index < len(data.get("reminders", [])):
        data["reminders"].pop(index)
        _save_json("tasks.json", data)
        return jsonify({"ok": True})
    return jsonify({"error": "Invalid index"}), 404


# ─── Schedules API ──────────────────────────────────────────────────

@app.route("/api/schedules")
def api_get_schedules():
    target = request.args.get("date")
    if target:
        return jsonify(schedules.get_today_schedules(dp("tasks.json"), target))
    return jsonify(schedules.load_schedules(dp("tasks.json")))

@app.route("/api/schedules", methods=["POST"])
def api_add_schedule():
    sid = schedules.add_schedule(dp("tasks.json"), request.json)
    return jsonify({"ok": True, "id": sid})

@app.route("/api/schedules/<schedule_id>", methods=["PUT"])
def api_update_schedule(schedule_id):
    data = tasks.load_tasks(dp("tasks.json"))
    for s in data.get("schedules", []):
        if s.get("id") == schedule_id:
            s.update(request.json)
            with open(dp("tasks.json"), "w") as f:
                json.dump(data, f, indent=2)
            return jsonify({"ok": True})
    return jsonify({"error": "Not found"}), 404

@app.route("/api/schedules/<schedule_id>", methods=["DELETE"])
def api_delete_schedule(schedule_id):
    if schedules.delete_schedule(dp("tasks.json"), schedule_id):
        return jsonify({"ok": True})
    return jsonify({"error": "Not found"}), 404

@app.route("/api/calendar")
def api_calendar():
    y = int(request.args.get("year", date.today().year))
    m = int(request.args.get("month", date.today().month))
    task_data = tasks.load_tasks(dp("tasks.json"))
    return jsonify(schedules.get_month_data(dp("tasks.json"), task_data, y, m))


# ─── Habits API ──────────────────────────────────────────────────────

@app.route("/api/habits")
def api_get_habits():
    metrics_raw = metrics.load_metrics(dp("metrics.json"))
    return jsonify(habits.analyze_habits(dp("habits.json"), metrics_raw.get("entries", [])))

@app.route("/api/habits", methods=["POST"])
def api_add_habit():
    data = habits.load_habits(dp("habits.json"))
    name = request.json.get("name", "")
    if not name:
        return jsonify({"error": "Name required"}), 400
    for h in data["habits"]:
        if h["name"].lower() == name.lower():
            return jsonify({"error": "Already exists"}), 400
    data["habits"].append({"name": name, "frequency": request.json.get("frequency", "daily"), "history": {}})
    _save_json("habits.json", data)
    return jsonify({"ok": True})

@app.route("/api/habits/<name>", methods=["DELETE"])
def api_delete_habit(name):
    data = habits.load_habits(dp("habits.json"))
    n = len(data["habits"])
    data["habits"] = [h for h in data["habits"] if h["name"] != name]
    if len(data["habits"]) < n:
        _save_json("habits.json", data)
        return jsonify({"ok": True})
    return jsonify({"error": "Not found"}), 404

@app.route("/api/habits/<name>/toggle", methods=["PUT"])
def api_toggle_habit(name):
    data = habits.load_habits(dp("habits.json"))
    today = date.today().isoformat()
    for h in data["habits"]:
        if h["name"] == name:
            cur = h["history"].get(today, False)
            h["history"][today] = not cur
            _save_json("habits.json", data)
            return jsonify({"ok": True, "done": not cur})
    return jsonify({"error": "Not found"}), 404


# ─── Metrics API ─────────────────────────────────────────────────────

@app.route("/api/metrics")
def api_get_metrics():
    return jsonify(metrics.analyze_metrics(dp("metrics.json")))

@app.route("/api/metrics", methods=["POST"])
def api_add_metrics():
    data = metrics.load_metrics(dp("metrics.json"))
    entry = request.json
    target_date = entry.get("date", date.today().isoformat())
    entry["date"] = target_date
    data["entries"] = [e for e in data["entries"] if e["date"] != target_date]
    data["entries"].append(entry)
    _save_json("metrics.json", data)
    return jsonify({"ok": True})


# ─── Food Log API ───────────────────────────────────────────────────

@app.route("/api/food")
def api_get_food():
    d = request.args.get("date", date.today().isoformat())
    return jsonify(food_log.get_food_summary(dp("food_log.json"), d))

@app.route("/api/food", methods=["POST"])
def api_add_food():
    entry = request.json
    d = entry.pop("date", date.today().isoformat())
    food_log.add_entry(dp("food_log.json"), d, entry)
    return jsonify({"ok": True})

@app.route("/api/food/<date_str>/<int:index>", methods=["DELETE"])
def api_delete_food(date_str, index):
    if food_log.delete_entry(dp("food_log.json"), date_str, index):
        return jsonify({"ok": True})
    return jsonify({"error": "Not found"}), 404


# ─── Journal API ────────────────────────────────────────────────────

@app.route("/api/journal")
def api_get_journal():
    return jsonify({"entries": journal.get_recent_entries(dp("journal.json"), 30),
                     "mood_trend": journal.get_mood_trend(dp("journal.json"))})

@app.route("/api/journal/<date_str>")
def api_get_journal_entry(date_str):
    entry = journal.get_entry(dp("journal.json"), date_str)
    return jsonify(entry or {"date": date_str, "mood": None, "entry": ""})

@app.route("/api/journal", methods=["POST"])
def api_save_journal():
    d = request.json
    journal.upsert_entry(dp("journal.json"), d.get("date", date.today().isoformat()),
                          d.get("mood", 3), d.get("entry", ""))
    return jsonify({"ok": True})


# ─── Media Log API ──────────────────────────────────────────────────

@app.route("/api/media")
def api_get_media():
    return jsonify(media_log.load_media(dp("media_log.json")))

@app.route("/api/media/fetch-meta", methods=["POST"])
def api_fetch_meta():
    url = request.json.get("url", "")
    if not url:
        return jsonify({"error": "URL required"}), 400
    meta = media_log.fetch_metadata(url)
    return jsonify(meta)

@app.route("/api/media", methods=["POST"])
def api_add_media():
    d = request.json
    link = d.get("link", "")
    meta = d.get("metadata") or media_log.fetch_metadata(link)
    eid = media_log.add_entry(dp("media_log.json"), link, meta, d.get("notes", ""), d.get("rating", 0))
    return jsonify({"ok": True, "id": eid})

@app.route("/api/media/<entry_id>", methods=["PUT"])
def api_update_media(entry_id):
    if media_log.update_entry(dp("media_log.json"), entry_id, request.json):
        return jsonify({"ok": True})
    return jsonify({"error": "Not found"}), 404

@app.route("/api/media/<entry_id>", methods=["DELETE"])
def api_delete_media(entry_id):
    if media_log.delete_entry(dp("media_log.json"), entry_id):
        return jsonify({"ok": True})
    return jsonify({"error": "Not found"}), 404


# ─── Paper Summarizer API ───────────────────────────────────────────

@app.route("/api/papers/summarize", methods=["POST"])
def api_summarize_paper():
    config = get_config()
    api_key = config.get("openai", {}).get("api_key", "")
    model = config.get("openai", {}).get("model", "gpt-4o-mini")
    if not api_key or api_key == "YOUR_OPENAI_API_KEY_HERE":
        return jsonify({"error": "Set your OpenAI API key in config/settings.yaml"}), 400
    url = request.json.get("url", "")
    if not url:
        return jsonify({"error": "URL required"}), 400
    text = paper_summarizer.fetch_paper_text(url)
    summary = paper_summarizer.summarize_paper(text, api_key, model)
    sid = paper_summarizer.save_summary(dp("paper_summaries.json"), url, summary)
    summary["id"] = sid
    return jsonify(summary)

@app.route("/api/paper-summaries")
def api_get_summaries():
    return jsonify(paper_summarizer.load_summaries(dp("paper_summaries.json")))

@app.route("/api/paper-summaries/<sid>", methods=["DELETE"])
def api_delete_summary(sid):
    if paper_summarizer.delete_summary(dp("paper_summaries.json"), sid):
        return jsonify({"ok": True})
    return jsonify({"error": "Not found"}), 404


# ─── Stocks API ─────────────────────────────────────────────────────

@app.route("/api/stocks")
def api_get_stocks():
    config = get_config()
    symbols = config.get("stocks", {}).get("symbols", [])
    if not symbols:
        return jsonify({"stocks": [], "count": 0})
    return jsonify(stocks.get_portfolio_summary(symbols))


# ─── Papers API ─────────────────────────────────────────────────────

@app.route("/api/papers")
def api_get_papers():
    config = get_config()
    pc = config.get("papers", {})
    return jsonify(papers.get_paper_recommendations(
        dp("paper_history.json"), pc.get("search_queries", ["LLM routing"]),
        pc.get("categories", ["cs.CL", "cs.AI"])))

@app.route("/api/papers/mark-read", methods=["POST"])
def api_mark_paper_read():
    papers.mark_paper_read(dp("paper_history.json"), request.json.get("arxiv_id", ""), request.json.get("notes", ""))
    return jsonify({"ok": True})


# ─── Bookmarks API ──────────────────────────────────────────────────

@app.route("/api/bookmarks")
def api_get_bookmarks():
    data = bookmarks.load_bookmarks(dp("bookmarks.json"))
    q = request.args.get("q")
    if q:
        data["bookmarks"] = bookmarks.search_bookmarks(dp("bookmarks.json"), q)
    folder = request.args.get("folder")
    if folder and folder != "All":
        data["bookmarks"] = [b for b in data["bookmarks"] if b.get("folder") == folder]
    return jsonify(data)

@app.route("/api/bookmarks", methods=["POST"])
def api_add_bookmark():
    d = request.json
    url = d.get("url", "")
    if not url:
        return jsonify({"error": "URL required"}), 400
    bid = bookmarks.add_bookmark(
        dp("bookmarks.json"), url,
        folder=d.get("folder", "General"),
        tags=d.get("tags", []),
        note=d.get("note", ""),
    )
    return jsonify({"ok": True, "id": bid})

@app.route("/api/bookmarks/<bid>", methods=["PUT"])
def api_update_bookmark(bid):
    if bookmarks.update_bookmark(dp("bookmarks.json"), bid, request.json):
        return jsonify({"ok": True})
    return jsonify({"error": "Not found"}), 404

@app.route("/api/bookmarks/<bid>", methods=["DELETE"])
def api_delete_bookmark(bid):
    if bookmarks.delete_bookmark(dp("bookmarks.json"), bid):
        return jsonify({"ok": True})
    return jsonify({"error": "Not found"}), 404

@app.route("/api/bookmarks/<bid>/pin", methods=["PUT"])
def api_pin_bookmark(bid):
    pinned = bookmarks.toggle_pin(dp("bookmarks.json"), bid)
    return jsonify({"ok": True, "pinned": pinned})

@app.route("/api/bookmarks/folders", methods=["POST"])
def api_add_folder():
    name = request.json.get("name", "")
    if not name:
        return jsonify({"error": "Name required"}), 400
    bookmarks.add_folder(dp("bookmarks.json"), name)
    return jsonify({"ok": True})


# ─── Study Log API ──────────────────────────────────────────────────

@app.route("/api/study")
def api_get_study():
    return jsonify(study_log.get_weekly_summary(dp("study_log.json")))

@app.route("/api/study", methods=["POST"])
def api_add_study():
    sid = study_log.add_session(dp("study_log.json"), request.json)
    return jsonify({"ok": True, "id": sid})

@app.route("/api/study/<sid>", methods=["DELETE"])
def api_delete_study(sid):
    if study_log.delete_session(dp("study_log.json"), sid):
        return jsonify({"ok": True})
    return jsonify({"error": "Not found"}), 404


# ─── Reading Queue API ─────────────────────────────────────────────

@app.route("/api/reading-queue")
def api_get_reading_queue():
    return jsonify(reading_queue.get_queue_summary(dp("reading_queue.json")))

@app.route("/api/reading-queue", methods=["POST"])
def api_add_reading():
    iid = reading_queue.add_item(dp("reading_queue.json"), request.json)
    return jsonify({"ok": True, "id": iid})

@app.route("/api/reading-queue/<iid>/status", methods=["PUT"])
def api_update_reading_status(iid):
    status = request.json.get("status", "unread")
    if reading_queue.update_status(dp("reading_queue.json"), iid, status):
        return jsonify({"ok": True})
    return jsonify({"error": "Not found"}), 404

@app.route("/api/reading-queue/<iid>", methods=["DELETE"])
def api_delete_reading(iid):
    if reading_queue.delete_item(dp("reading_queue.json"), iid):
        return jsonify({"ok": True})
    return jsonify({"error": "Not found"}), 404


# ─── Grades API ────────────────────────────────────────────────────

@app.route("/api/courses")
def api_get_courses():
    return jsonify(grades.calculate_gpa(dp("grades.json")))

@app.route("/api/courses", methods=["POST"])
def api_add_course():
    cid = grades.add_course(dp("grades.json"), request.json)
    return jsonify({"ok": True, "id": cid})

@app.route("/api/courses/<cid>", methods=["DELETE"])
def api_delete_course(cid):
    if grades.delete_course(dp("grades.json"), cid):
        return jsonify({"ok": True})
    return jsonify({"error": "Not found"}), 404

@app.route("/api/courses/<cid>/assignments", methods=["POST"])
def api_add_assignment(cid):
    aid = grades.add_assignment(dp("grades.json"), cid, request.json)
    if aid:
        return jsonify({"ok": True, "id": aid})
    return jsonify({"error": "Course not found"}), 404

@app.route("/api/courses/<cid>/assignments/<aid>", methods=["DELETE"])
def api_delete_assignment(cid, aid):
    if grades.delete_assignment(dp("grades.json"), cid, aid):
        return jsonify({"ok": True})
    return jsonify({"error": "Not found"}), 404


# ─── Budget API ────────────────────────────────────────────────────

@app.route("/api/budgets")
def api_get_budgets():
    return jsonify(metrics.load_budgets(dp("metrics.json")))

@app.route("/api/budgets", methods=["POST"])
def api_set_budget():
    cat = request.json.get("category", "")
    amt = request.json.get("amount", 0)
    if not cat:
        return jsonify({"error": "Category required"}), 400
    metrics.set_budget(dp("metrics.json"), cat, amt)
    return jsonify({"ok": True})


# ─── Period Tracker API ────────────────────────────────────────────

@app.route("/api/period")
def api_get_period():
    phase = period_tracker.get_current_phase(dp("period.json"))
    stats = period_tracker.get_cycle_stats(dp("period.json"))
    return jsonify({"phase": phase, "stats": stats})

@app.route("/api/period/log", methods=["POST"])
def api_log_period():
    d = request.json
    period_tracker.log_period(
        dp("period.json"),
        d.get("start_date", ""),
        d.get("end_date", ""),
        d.get("symptoms", []),
        d.get("notes", ""),
    )
    return jsonify({"ok": True})


# ─── Pomodoro API ──────────────────────────────────────────────────

@app.route("/api/metrics/pomodoro", methods=["POST"])
def api_log_pomodoro():
    data = metrics.load_metrics(dp("metrics.json"))
    today_str = date.today().isoformat()
    for entry in data["entries"]:
        if entry["date"] == today_str:
            entry["pomodoros"] = entry.get("pomodoros", 0) + 1
            break
    else:
        data["entries"].append({"date": today_str, "pomodoros": 1})
    _save_json("metrics.json", data)
    return jsonify({"ok": True})


# ─── Weekly Review API ─────────────────────────────────────────────

@app.route("/api/weekly-review")
def api_weekly_review():
    return jsonify(weekly_review.generate_weekly_review(str(PROJECT_ROOT / "data")))


# ─── Tarot API ─────────────────────────────────────────────────────

@app.route("/api/tarot/cards")
def api_tarot_cards():
    return jsonify({"cards": tarot.get_all_cards()})

@app.route("/api/tarot/read", methods=["POST"])
def api_tarot_read():
    config = get_config()
    api_key = config.get("openai", {}).get("api_key", "")
    model = config.get("openai", {}).get("model", "gpt-4o-mini")
    d = request.json

    # Support multi-card spread or single card
    cards = d.get("cards")  # [{card, orientation}, ...]
    num_cards = d.get("num_cards", 3)

    if not cards:
        # If user provided individual cards, build the list
        if d.get("card"):
            cards = [{"card": d["card"], "orientation": d.get("orientation", "upright")}]
        else:
            # Random draw
            cards = tarot.draw_random_spread(num_cards)

    # Build context
    context = {}
    try:
        journal_today = journal.get_entry(dp("journal.json"), date.today().isoformat())
        if journal_today and journal_today.get("mood"):
            context["mood"] = journal_today["mood"]
        task_data = tasks.load_tasks(dp("tasks.json"))
        context["tasks_count"] = len([t for t in task_data.get("tasks", []) if t.get("status") != "done"])
        cycle = period_tracker.get_current_phase(dp("period.json"))
        if cycle and cycle.get("has_data"):
            context["cycle_phase"] = cycle.get("label", "")
            context["energy"] = cycle.get("energy", "")
    except Exception:
        pass

    if api_key and api_key != "YOUR_OPENAI_API_KEY_HERE":
        reading = tarot.generate_spread_reading(cards, api_key, model, context)
    else:
        reading = "Set your OpenAI API key for personalized readings."

    # Get spread layout info
    num = len(cards)
    layout = tarot.SPREAD_LAYOUTS.get(num, tarot.SPREAD_LAYOUTS[3])

    # Save
    tarot.save_reading(dp("tarot_readings.json"), {
        "date": date.today().isoformat(),
        "spread": layout["name"],
        "cards": cards,
        "reading": reading,
    })

    return jsonify({"cards": cards, "spread": layout["name"],
                     "positions": layout["positions"][:num], "reading": reading})

@app.route("/api/tarot/draw")
def api_tarot_draw():
    """Draw random cards for a spread."""
    num = int(request.args.get("num", 3))
    cards = tarot.draw_random_spread(num)
    num = len(cards)
    layout = tarot.SPREAD_LAYOUTS.get(num, tarot.SPREAD_LAYOUTS[3])
    return jsonify({"cards": cards, "spread": layout["name"],
                     "positions": layout["positions"][:num]})

@app.route("/api/tarot/history")
def api_tarot_history():
    return jsonify(tarot.load_readings(dp("tarot_readings.json")))


# ─── Weather API ───────────────────────────────────────────────────

@app.route("/api/weather")
def api_get_weather():
    config = get_config()
    wc = config.get("weather", {})
    return jsonify(weather_mod.fetch_weather(
        wc.get("api_key", ""), wc.get("city", "Busan"), wc.get("country", "KR")))


# ─── Lab Papers API ────────────────────────────────────────────────

@app.route("/api/lab/papers")
def api_lab_papers():
    q = request.args.get("q")
    project = request.args.get("project")
    data = lab_papers.load_papers(dp("lab/papers.json"))
    papers_list = data["papers"]
    if q:
        papers_list = lab_papers.search_papers(dp("lab/papers.json"), q)
    if project and project != "All":
        papers_list = [p for p in papers_list if p.get("project") == project]
    return jsonify({"papers": papers_list, "projects": data.get("projects", [])})

@app.route("/api/lab/papers", methods=["POST"])
def api_lab_add_paper():
    d = request.json
    pid = lab_papers.add_paper(dp("lab/papers.json"), url=d.get("url", ""),
                                project=d.get("project", "General"), tags=d.get("tags", []))
    return jsonify({"ok": True, "id": pid})

@app.route("/api/lab/papers/<pid>", methods=["PUT"])
def api_lab_update_paper(pid):
    if lab_papers.update_paper(dp("lab/papers.json"), pid, request.json):
        return jsonify({"ok": True})
    return jsonify({"error": "Not found"}), 404

@app.route("/api/lab/papers/<pid>", methods=["DELETE"])
def api_lab_delete_paper(pid):
    if lab_papers.delete_paper(dp("lab/papers.json"), pid):
        return jsonify({"ok": True})
    return jsonify({"error": "Not found"}), 404

@app.route("/api/lab/papers/<pid>/notes", methods=["POST"])
def api_lab_paper_note(pid):
    if lab_papers.add_note_to_paper(dp("lab/papers.json"), pid, request.json):
        return jsonify({"ok": True})
    return jsonify({"error": "Not found"}), 404

@app.route("/api/lab/papers/<pid>/highlight", methods=["POST"])
def api_lab_paper_highlight(pid):
    if lab_papers.add_highlight(dp("lab/papers.json"), pid, request.json):
        return jsonify({"ok": True})
    return jsonify({"error": "Not found"}), 404

@app.route("/api/lab/papers/upload", methods=["POST"])
def api_lab_upload_pdf():
    if "file" not in request.files:
        return jsonify({"error": "No file"}), 400
    f = request.files["file"]
    filename = f"{uuid.uuid4().hex[:8]}_{f.filename}"
    save_path = str(PROJECT_ROOT / "data" / "lab" / "pdfs" / filename)
    f.save(save_path)
    pid = lab_papers.add_paper(dp("lab/papers.json"), pdf_path=save_path,
                                metadata={"title": f.filename},
                                project=request.form.get("project", "General"))
    return jsonify({"ok": True, "id": pid, "path": save_path})

@app.route("/api/lab/connections")
def api_lab_connections():
    return jsonify(lab_papers.get_connections(dp("lab/papers.json")))

@app.route("/api/lab/meeting-prep")
def api_lab_meeting_prep():
    return jsonify(lab_papers.get_lab_meeting_prep(dp("lab/papers.json")))


# ─── Lab Notes API ─────────────────────────────────────────────────

@app.route("/api/lab/notes")
def api_lab_notes():
    return jsonify(lab_notes.load_notes(dp("lab/notes.json")))

@app.route("/api/lab/notes", methods=["POST"])
def api_lab_add_note():
    d = request.json
    nid = lab_notes.add_note(dp("lab/notes.json"), d.get("title", ""), d.get("content", ""),
                              d.get("linked_papers", []), d.get("tags", []))
    return jsonify({"ok": True, "id": nid})

@app.route("/api/lab/notes/<nid>", methods=["PUT"])
def api_lab_update_note(nid):
    if lab_notes.update_note(dp("lab/notes.json"), nid, request.json):
        return jsonify({"ok": True})
    return jsonify({"error": "Not found"}), 404

@app.route("/api/lab/notes/<nid>", methods=["DELETE"])
def api_lab_delete_note(nid):
    if lab_notes.delete_note(dp("lab/notes.json"), nid):
        return jsonify({"ok": True})
    return jsonify({"error": "Not found"}), 404

@app.route("/api/lab/notes/connections")
def api_lab_note_connections():
    return jsonify(lab_notes.get_connections(dp("lab/notes.json"), dp("lab/papers.json")))


# ─── Uni Materials API ─────────────────────────────────────────────

@app.route("/api/uni/materials")
def api_uni_materials():
    course_id = request.args.get("course_id")
    if course_id:
        return jsonify({"materials": uni_materials.get_by_course(dp("uni/materials.json"), course_id)})
    return jsonify(uni_materials.load_materials(dp("uni/materials.json")))

@app.route("/api/uni/materials", methods=["POST"])
def api_uni_add_material():
    d = request.json
    mid = uni_materials.add_material(dp("uni/materials.json"), d.get("course_id", ""),
                                      d.get("title", ""), d.get("type", "link"),
                                      d.get("url", ""), folder=d.get("folder", "general"))
    return jsonify({"ok": True, "id": mid})

@app.route("/api/uni/materials/upload", methods=["POST"])
def api_uni_upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file"}), 400
    f = request.files["file"]
    filename = f"{uuid.uuid4().hex[:8]}_{f.filename}"
    save_path = str(PROJECT_ROOT / "data" / "uni" / "files" / filename)
    f.save(save_path)
    mid = uni_materials.add_material(dp("uni/materials.json"),
                                      request.form.get("course_id", ""),
                                      f.filename, "pdf", file_path=save_path,
                                      folder=request.form.get("folder", "general"))
    return jsonify({"ok": True, "id": mid, "path": save_path})

@app.route("/api/uni/materials/<mid>", methods=["DELETE"])
def api_uni_delete_material(mid):
    if uni_materials.delete_material(dp("uni/materials.json"), mid):
        return jsonify({"ok": True})
    return jsonify({"error": "Not found"}), 404


# ─── Flashcards API ────────────────────────────────────────────────

@app.route("/api/uni/flashcards")
def api_uni_flashcards():
    return jsonify(flashcards.load_flashcards(dp("uni/flashcards.json")))

@app.route("/api/uni/flashcards", methods=["POST"])
def api_uni_create_deck():
    d = request.json
    did = flashcards.create_deck(dp("uni/flashcards.json"), d.get("title", ""),
                                  d.get("course_id", ""), d.get("cards", []))
    return jsonify({"ok": True, "id": did})

@app.route("/api/uni/flashcards/<did>", methods=["DELETE"])
def api_uni_delete_deck(did):
    if flashcards.delete_deck(dp("uni/flashcards.json"), did):
        return jsonify({"ok": True})
    return jsonify({"error": "Not found"}), 404

@app.route("/api/uni/flashcards/<did>/cards", methods=["POST"])
def api_uni_add_card(did):
    d = request.json
    cid = flashcards.add_card(dp("uni/flashcards.json"), did, d.get("question", ""), d.get("answer", ""))
    if cid:
        return jsonify({"ok": True, "id": cid})
    return jsonify({"error": "Deck not found"}), 404

@app.route("/api/uni/flashcards/<did>/cards/<cid>/review", methods=["PUT"])
def api_uni_review_card(did, cid):
    rating = request.json.get("rating", "medium")
    if flashcards.review_card(dp("uni/flashcards.json"), did, cid, rating):
        return jsonify({"ok": True})
    return jsonify({"error": "Not found"}), 404

@app.route("/api/uni/flashcards/<did>/cards/<cid>", methods=["DELETE"])
def api_uni_delete_card(did, cid):
    data = flashcards.load_flashcards(dp("uni/flashcards.json"))
    for deck in data["decks"]:
        if deck["id"] == did:
            n = len(deck["cards"])
            deck["cards"] = [c for c in deck["cards"] if c["id"] != cid]
            if len(deck["cards"]) < n:
                flashcards.save_flashcards(dp("uni/flashcards.json"), data)
                return jsonify({"ok": True})
    return jsonify({"error": "Not found"}), 404

@app.route("/api/uni/flashcards/<did>/cards/<cid>", methods=["PUT"])
def api_uni_update_card(did, cid):
    data = flashcards.load_flashcards(dp("uni/flashcards.json"))
    for deck in data["decks"]:
        if deck["id"] == did:
            for card in deck["cards"]:
                if card["id"] == cid:
                    card.update(request.json)
                    flashcards.save_flashcards(dp("uni/flashcards.json"), data)
                    return jsonify({"ok": True})
    return jsonify({"error": "Not found"}), 404

@app.route("/api/uni/flashcards/generate", methods=["POST"])
def api_uni_generate_flashcards():
    config = get_config()
    api_key = config.get("openai", {}).get("api_key", "")
    model = config.get("openai", {}).get("model", "gpt-4o-mini")
    if not api_key or api_key == "YOUR_OPENAI_API_KEY_HERE":
        return jsonify({"error": "Set OpenAI API key"}), 400
    d = request.json
    cards = flashcards.generate_flashcards_from_text(
        d.get("text", ""), api_key, model, d.get("num_cards", 10))
    return jsonify({"cards": cards})

@app.route("/api/uni/flashcards/due")
def api_uni_due_cards():
    deck_id = request.args.get("deck_id")
    return jsonify({"cards": flashcards.get_due_cards(dp("uni/flashcards.json"), deck_id)})


# ─── Class Notes API ──────────────────────────────────────────────

@app.route("/api/uni/class-notes")
def api_uni_class_notes():
    path = Path(dp("uni/class_notes.json"))
    data = json.load(open(path)) if path.exists() else {"notes": []}
    course_id = request.args.get("course_id")
    if course_id:
        data["notes"] = [n for n in data["notes"] if n.get("course_id") == course_id]
    return jsonify(data)

@app.route("/api/uni/class-notes", methods=["POST"])
def api_uni_add_class_note():
    import uuid as _uuid
    path = Path(dp("uni/class_notes.json"))
    data = json.load(open(path)) if path.exists() else {"notes": []}
    d = request.json
    nid = str(_uuid.uuid4())[:8]
    d["id"] = nid
    d.setdefault("date", date.today().isoformat())
    data["notes"].insert(0, d)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    return jsonify({"ok": True, "id": nid})

@app.route("/api/uni/class-notes/<nid>", methods=["DELETE"])
def api_uni_delete_class_note(nid):
    path = Path(dp("uni/class_notes.json"))
    data = json.load(open(path)) if path.exists() else {"notes": []}
    n = len(data["notes"])
    data["notes"] = [x for x in data["notes"] if x.get("id") != nid]
    if len(data["notes"]) < n:
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        return jsonify({"ok": True})
    return jsonify({"error": "Not found"}), 404


# ─── Exams API ─────────────────────────────────────────────────────

@app.route("/api/uni/exams")
def api_uni_exams():
    path = Path(dp("uni/exams.json"))
    data = json.load(open(path)) if path.exists() else {"exams": []}
    return jsonify(data)

@app.route("/api/uni/exams", methods=["POST"])
def api_uni_add_exam():
    import uuid as _uuid
    path = Path(dp("uni/exams.json"))
    data = json.load(open(path)) if path.exists() else {"exams": []}
    d = request.json
    d["id"] = str(_uuid.uuid4())[:8]
    data["exams"].append(d)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    return jsonify({"ok": True, "id": d["id"]})

@app.route("/api/uni/exams/<eid>", methods=["DELETE"])
def api_uni_delete_exam(eid):
    path = Path(dp("uni/exams.json"))
    data = json.load(open(path)) if path.exists() else {"exams": []}
    n = len(data["exams"])
    data["exams"] = [e for e in data["exams"] if e.get("id") != eid]
    if len(data["exams"]) < n:
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        return jsonify({"ok": True})
    return jsonify({"error": "Not found"}), 404


# ─── Chat API ──────────────────────────────────────────────────────

@app.route("/api/chat", methods=["POST"])
def api_chat():
    config = get_config()
    api_key = config.get("openai", {}).get("api_key", "")
    model = config.get("openai", {}).get("model", "gpt-4o-mini")
    if not api_key or api_key == "YOUR_OPENAI_API_KEY_HERE":
        return jsonify({"reply": "Set your OpenAI API key in config/settings.yaml"})
    message = request.json.get("message", "")
    reply = chatbot.chat(message, api_key, model, str(PROJECT_ROOT / "data"),
                          dp("chat_history.json"))
    return jsonify({"reply": reply})

@app.route("/api/chat/history")
def api_chat_history():
    return jsonify(chatbot.load_chat_history(dp("chat_history.json")))


# ─── Goals API ─────────────────────────────────────────────────────

@app.route("/api/goals")
def api_get_goals():
    data = goals.load_goals(dp("goals.json"))
    result = []
    for g in data.get("goals", []):
        summary = goals.get_goal_summary(g)
        result.append({**g, "summary": summary})
    return jsonify({"goals": result})

@app.route("/api/goals", methods=["POST"])
def api_add_goal():
    gid = goals.add_goal(dp("goals.json"), request.json)
    return jsonify({"ok": True, "id": gid})

@app.route("/api/goals/<gid>", methods=["DELETE"])
def api_delete_goal(gid):
    if goals.delete_goal(dp("goals.json"), gid):
        return jsonify({"ok": True})
    return jsonify({"error": "Not found"}), 404

@app.route("/api/goals/<gid>/log", methods=["POST"])
def api_goal_log(gid):
    d = request.json
    log_date = d.pop("date", date.today().isoformat())
    goals.log_daily(dp("goals.json"), gid, log_date, d)
    return jsonify({"ok": True})

@app.route("/api/goals/<gid>/test", methods=["POST"])
def api_goal_test(gid):
    goals.add_practice_test(dp("goals.json"), gid, request.json)
    return jsonify({"ok": True})

@app.route("/api/goals/topik/flashcards", methods=["POST"])
def api_topik_flashcards():
    config = get_config()
    api_key = config.get("openai", {}).get("api_key", "")
    model = config.get("openai", {}).get("model", "gpt-4o-mini")
    if not api_key or api_key == "YOUR_OPENAI_API_KEY_HERE":
        return jsonify({"error": "Set OpenAI API key"}), 400
    d = request.json
    cards = goals.generate_topik_flashcards(
        d.get("level", "5-6"), d.get("category", "general vocabulary"),
        api_key, model, d.get("num_cards", 15))
    return jsonify({"cards": cards})


# ─── Nudges API ────────────────────────────────────────────────────

@app.route("/api/nudges")
def api_get_nudges():
    return jsonify({"nudges": nudges.generate_nudges(str(PROJECT_ROOT / "data"))})


# ─── Expenses API ──────────────────────────────────────────────────

@app.route("/api/expenses")
def api_get_expenses():
    d = request.args.get("date")
    if d:
        return jsonify(expenses.get_daily_summary(dp("expenses.json"), d))
    return jsonify(expenses.get_monthly_summary(dp("expenses.json")))

@app.route("/api/expenses", methods=["POST"])
def api_add_expense():
    d = request.json
    eid = expenses.add_expense(dp("expenses.json"), d.get("amount", 0), d.get("category", "other"),
                                d.get("description", ""), d.get("date"))
    return jsonify({"ok": True, "id": eid})

@app.route("/api/expenses/<eid>", methods=["DELETE"])
def api_delete_expense(eid):
    if expenses.delete_expense(dp("expenses.json"), eid):
        return jsonify({"ok": True})
    return jsonify({"error": "Not found"}), 404


# ─── Watchlist API ─────────────────────────────────────────────────

@app.route("/api/watchlist")
def api_get_watchlist():
    return jsonify(watchlist.get_by_status(dp("watchlist.json")))

@app.route("/api/watchlist", methods=["POST"])
def api_add_watchlist():
    d = request.json
    wid = watchlist.add_item(dp("watchlist.json"), d.get("title", ""), d.get("type", "kdrama"),
                              d.get("status", "watching"), d.get("rating", 0),
                              d.get("episodes_total", 0), d.get("episodes_watched", 0),
                              d.get("notes", ""), d.get("url", ""), d.get("thumbnail", ""))
    return jsonify({"ok": True, "id": wid})

@app.route("/api/watchlist/<wid>", methods=["PUT"])
def api_update_watchlist(wid):
    if watchlist.update_item(dp("watchlist.json"), wid, request.json):
        return jsonify({"ok": True})
    return jsonify({"error": "Not found"}), 404

@app.route("/api/watchlist/<wid>", methods=["DELETE"])
def api_delete_watchlist(wid):
    if watchlist.delete_item(dp("watchlist.json"), wid):
        return jsonify({"ok": True})
    return jsonify({"error": "Not found"}), 404


# ─── Wishlist API ──────────────────────────────────────────────────

@app.route("/api/wishlist")
def api_get_wishlist():
    return jsonify(wishlist.get_summary(dp("wishlist.json")))

@app.route("/api/wishlist", methods=["POST"])
def api_add_wishlist():
    d = request.json
    wid = wishlist.add_item(dp("wishlist.json"), d.get("title", ""), d.get("price", 0),
                             d.get("url", ""), d.get("category", "general"),
                             d.get("notes", ""), d.get("priority", "want"))
    return jsonify({"ok": True, "id": wid})

@app.route("/api/wishlist/<wid>", methods=["DELETE"])
def api_delete_wishlist(wid):
    if wishlist.delete_item(dp("wishlist.json"), wid):
        return jsonify({"ok": True})
    return jsonify({"error": "Not found"}), 404

@app.route("/api/wishlist/<wid>/toggle", methods=["PUT"])
def api_toggle_wishlist(wid):
    purchased = wishlist.toggle_purchased(dp("wishlist.json"), wid)
    return jsonify({"ok": True, "purchased": purchased})


# ─── Recipes API ───────────────────────────────────────────────────

@app.route("/api/recipes")
def api_get_recipes():
    return jsonify(recipes.get_week_plan(dp("recipes.json")))

@app.route("/api/recipes", methods=["POST"])
def api_add_recipe():
    d = request.json
    rid = recipes.add_recipe(dp("recipes.json"), d.get("title", ""),
                              d.get("ingredients", []), d.get("instructions", ""),
                              d.get("kcal", 0), d.get("tags", []),
                              d.get("url", ""), d.get("prep_time", ""))
    return jsonify({"ok": True, "id": rid})

@app.route("/api/recipes/<rid>", methods=["DELETE"])
def api_delete_recipe(rid):
    if recipes.delete_recipe(dp("recipes.json"), rid):
        return jsonify({"ok": True})
    return jsonify({"error": "Not found"}), 404

@app.route("/api/recipes/plan", methods=["POST"])
def api_plan_meal():
    d = request.json
    recipes.plan_meal(dp("recipes.json"), d.get("date", date.today().isoformat()),
                       d.get("meal_type", "lunch"), d.get("recipe_id"), d.get("custom", ""))
    return jsonify({"ok": True})


# ─── Global Search API ─────────────────────────────────────────────

@app.route("/api/search")
def api_search():
    q = request.args.get("q", "")
    if not q or len(q) < 2:
        return jsonify({"results": [], "total": 0})
    return jsonify(global_search.search_all(str(PROJECT_ROOT / "data"), q))


# ─── Email Digest API ─────────────────────────────────────────────

@app.route("/api/send-digest", methods=["POST"])
def api_send_digest():
    config = get_config()
    email_cfg = config.get("email", {})
    if not email_cfg.get("sender_email") or email_cfg.get("sender_email") == "YOUR_EMAIL@gmail.com":
        return jsonify({"error": "Set email config in config/settings.yaml"}), 400

    # Generate full briefing data
    cycle_data = period_tracker.get_current_phase(dp("period.json"))
    cycle_phase = cycle_data if cycle_data and cycle_data.get("has_data") else None
    metrics_data = metrics.analyze_metrics(dp("metrics.json"), cycle_phase)
    task_data = tasks.prioritize_tasks(dp("tasks.json"), metrics_data)
    today_schedules = schedules.get_today_schedules(dp("tasks.json"))
    food_today_data = food_log.get_food_summary(dp("food_log.json"))

    yesterday = (date.today() - timedelta(days=1)).isoformat()
    food_yesterday = food_log.get_food_summary(dp("food_log.json"), yesterday)
    journal_yesterday = journal.get_entry(dp("journal.json"), yesterday)
    summary_card = focus.generate_summary_card(metrics_data, food_yesterday, task_data, journal_yesterday, cycle_phase)

    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    tomorrow_schedules = schedules.get_today_schedules(dp("tasks.json"), tomorrow)
    sleep_rec = focus.generate_sleep_recommendation(metrics_data, tomorrow_schedules)

    focus_data = focus.generate_focus_plan(
        task_data, {}, metrics_data,
        schedules=today_schedules, food_today=food_today_data, cycle_phase=cycle_phase)

    wc = config.get("weather", {})
    weather_data = weather_mod.fetch_weather(wc.get("api_key", ""), wc.get("city", "Busan"), wc.get("country", "KR"))

    briefing = {
        "date": date.today().isoformat(),
        "focus": focus_data,
        "summary_card": summary_card,
        "sleep_rec": sleep_rec,
        "tasks": task_data,
        "schedules_today": today_schedules,
        "weather": weather_data,
        "nudges": nudges.generate_nudges(str(PROJECT_ROOT / "data")),
        "goals": _get_goals_summary(),
    }

    success = email_digest.send_digest(
        email_cfg.get("smtp_host", "smtp.gmail.com"),
        email_cfg.get("smtp_port", 587),
        email_cfg["sender_email"],
        email_cfg["sender_password"],
        email_cfg.get("recipient_email", email_cfg["sender_email"]),
        briefing
    )

    if success:
        return jsonify({"ok": True, "message": "Digest sent!"})
    return jsonify({"error": "Failed to send email"}), 500


# ─── Brain Dump API ────────────────────────────────────────────────

@app.route("/api/capture", methods=["POST"])
def api_capture():
    text = request.json.get("text", "")
    if not text:
        return jsonify({"error": "Text required"}), 400
    result = brain_dump.add_capture(dp("brain_dump.json"), text)
    # Auto-create the thing if categorized
    if result["type"] == "task":
        tasks.load_tasks(dp("tasks.json"))
        data = tasks.load_tasks(dp("tasks.json"))
        data["tasks"].append({"title": result["title"], "deadline": "", "category": "personal",
                               "energy": "medium", "impact": 5, "status": "pending", "notes": "From quick capture"})
        with open(dp("tasks.json"), "w") as f:
            json.dump(data, f, indent=2)
    elif result["type"] == "expense" and result.get("amount"):
        expenses.add_expense(dp("expenses.json"), result["amount"], "other", result.get("description", ""))
    elif result["type"] == "reminder":
        data = tasks.load_tasks(dp("tasks.json"))
        data.setdefault("reminders", []).append({"text": result["text"], "time": "", "recurring": False})
        with open(dp("tasks.json"), "w") as f:
            json.dump(data, f, indent=2)
    return jsonify(result)

@app.route("/api/capture")
def api_get_captures():
    return jsonify({"items": brain_dump.get_unprocessed(dp("brain_dump.json"))})

@app.route("/api/capture/<item_id>", methods=["DELETE"])
def api_delete_capture(item_id):
    if brain_dump.delete_item(dp("brain_dump.json"), item_id):
        return jsonify({"ok": True})
    return jsonify({"error": "Not found"}), 404


# ─── Achievements API ─────────────────────────────────────────────

@app.route("/api/achievements")
def api_get_achievements():
    return jsonify(achievements.get_all_achievements(str(PROJECT_ROOT / "data")))


# ─── Monthly Report API ───────────────────────────────────────────

@app.route("/api/monthly-report")
def api_monthly_report():
    y = request.args.get("year", type=int)
    m = request.args.get("month", type=int)
    return jsonify(monthly_report.generate_monthly_report(str(PROJECT_ROOT / "data"), y, m))


# ─── Static Files (PDFs) ──────────────────────────────────────────

@app.route("/files/lab/<path:filename>")
def serve_lab_file(filename):
    from flask import send_from_directory
    return send_from_directory(str(PROJECT_ROOT / "data" / "lab" / "pdfs"), filename)

@app.route("/files/uni/<path:filename>")
def serve_uni_file(filename):
    from flask import send_from_directory
    return send_from_directory(str(PROJECT_ROOT / "data" / "uni" / "files"), filename)

@app.route("/files/uploads/<path:filename>")
def serve_upload(filename):
    from flask import send_from_directory
    return send_from_directory(str(PROJECT_ROOT / "data" / "uploads"), filename)

@app.route("/api/upload", methods=["POST"])
def api_upload_file():
    """General file upload for assignments and tasks."""
    if "file" not in request.files:
        return jsonify({"error": "No file"}), 400
    f = request.files["file"]
    if not f.filename:
        return jsonify({"error": "Empty filename"}), 400
    filename = f"{uuid.uuid4().hex[:8]}_{f.filename}"
    save_path = str(PROJECT_ROOT / "data" / "uploads" / filename)
    f.save(save_path)
    return jsonify({"ok": True, "path": save_path, "filename": filename})


# ─── Helpers ─────────────────────────────────────────────────────────

import uuid

def _save_json(filename, data):
    with open(dp(filename), "w") as f:
        json.dump(data, f, indent=2)


if __name__ == "__main__":
    print("Mochi's Assistant Dashboard")
    print("Open http://localhost:5050")
    app.run(host="0.0.0.0", port=5050, debug=True)
