"""Goals tracker — one-time goals like TOPIK, thesis, certifications."""

import json
import uuid
from datetime import date, timedelta
from pathlib import Path


def load_goals(data_path: str) -> dict:
    path = Path(data_path)
    if not path.exists():
        return {"goals": []}
    with open(path) as f:
        return json.load(f)


def save_goals(data_path: str, data: dict):
    with open(data_path, "w") as f:
        json.dump(data, f, indent=2)


def add_goal(data_path: str, goal: dict) -> str:
    data = load_goals(data_path)
    gid = goal.get("id") or str(uuid.uuid4())[:8]
    goal["id"] = gid
    goal.setdefault("status", "active")
    goal.setdefault("daily_log", {})
    goal.setdefault("practice_tests", [])
    goal.setdefault("study_plan", {})
    goal.setdefault("created", date.today().isoformat())
    data["goals"].append(goal)
    save_goals(data_path, data)
    return gid


def delete_goal(data_path: str, gid: str) -> bool:
    data = load_goals(data_path)
    n = len(data["goals"])
    data["goals"] = [g for g in data["goals"] if g["id"] != gid]
    if len(data["goals"]) < n:
        save_goals(data_path, data)
        return True
    return False


def log_daily(data_path: str, gid: str, log_date: str, entry: dict):
    """Log daily study for a goal."""
    data = load_goals(data_path)
    for g in data["goals"]:
        if g["id"] == gid:
            g.setdefault("daily_log", {})[log_date] = entry
            save_goals(data_path, data)
            return True
    return False


def add_practice_test(data_path: str, gid: str, test: dict):
    """Log a practice test score."""
    data = load_goals(data_path)
    for g in data["goals"]:
        if g["id"] == gid:
            test["id"] = str(uuid.uuid4())[:8]
            test.setdefault("date", date.today().isoformat())
            g.setdefault("practice_tests", []).insert(0, test)
            save_goals(data_path, data)
            return True
    return False


def get_goal_summary(goal: dict) -> dict:
    """Calculate progress stats for a goal."""
    today = date.today()
    target = goal.get("target_date", "")

    days_left = None
    if target:
        try:
            target_date = date.fromisoformat(target)
            days_left = (target_date - today).days
        except ValueError:
            pass

    # Study streak
    daily_log = goal.get("daily_log", {})
    streak = 0
    check = today
    while daily_log.get(check.isoformat()):
        streak += 1
        check -= timedelta(days=1)
    # Also check if yesterday was logged but not today yet
    if not daily_log.get(today.isoformat()):
        streak_from_yesterday = 0
        check = today - timedelta(days=1)
        while daily_log.get(check.isoformat()):
            streak_from_yesterday += 1
            check -= timedelta(days=1)
        streak = streak_from_yesterday

    # Total stats
    total_words = sum(d.get("words_learned", 0) for d in daily_log.values())
    total_minutes = sum(d.get("minutes", 0) for d in daily_log.values())
    total_grammar = sum(d.get("grammar_points", 0) for d in daily_log.values())
    days_studied = len(daily_log)

    # Study plan targets
    plan = goal.get("study_plan", {})
    vocab_target = plan.get("total_vocab_target", 1000)
    daily_target = plan.get("daily_vocab_target", 20)

    # Adjusted daily target based on remaining
    remaining_vocab = max(0, vocab_target - total_words)
    adjusted_daily = round(remaining_vocab / max(1, days_left)) if days_left and days_left > 0 else daily_target

    # Practice test trend
    tests = goal.get("practice_tests", [])
    latest_score = tests[0] if tests else None

    return {
        "days_left": days_left,
        "streak": streak,
        "total_words": total_words,
        "total_minutes": total_minutes,
        "total_grammar": total_grammar,
        "days_studied": days_studied,
        "remaining_vocab": remaining_vocab,
        "adjusted_daily_target": adjusted_daily,
        "latest_test": latest_score,
        "test_count": len(tests),
        "vocab_progress_pct": min(100, round(total_words / max(1, vocab_target) * 100)),
    }


def generate_topik_flashcards(level: str, category: str, api_key: str,
                                model: str = "gpt-4o-mini", num_cards: int = 15) -> list:
    """Generate TOPIK vocabulary flashcards using GPT."""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        prompt = f"""Generate {num_cards} Korean vocabulary flashcards for TOPIK II Level {level} preparation.
Category: {category}

For each card, provide:
- question: The Korean word/phrase (in 한글)
- answer: English meaning + example sentence in Korean with translation

Return ONLY valid JSON array:
[{{"question": "한국어 단어", "answer": "English meaning\\n예: 한국어 예문 (English translation)"}}]

Focus on high-frequency TOPIK vocabulary. Include a mix of nouns, verbs, adjectives, and grammar patterns."""

        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2000,
        )
        result = response.choices[0].message.content.strip()
        if result.startswith("```"):
            result = result.split("\n", 1)[1]
            if result.endswith("```"):
                result = result[:-3]
        return json.loads(result)
    except Exception as e:
        return [{"question": f"Error: {e}", "answer": "Check API key"}]


def generate_hsk_flashcards(level: str, category: str, api_key: str,
                             model: str = "gpt-4o-mini", num_cards: int = 10) -> list:
    """Generate HSK Mandarin vocabulary flashcards using GPT."""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        prompt = f"""Generate {num_cards} Mandarin Chinese vocabulary flashcards for HSK Level {level} preparation.
Category: {category}

For each card, provide:
- question: The Chinese character(s) with pinyin
- answer: English meaning + example sentence in Chinese with pinyin and translation

Return ONLY valid JSON array:
[{{"question": "你好 (nǐ hǎo)", "answer": "Hello\\n例: 你好，我叫小明。(Nǐ hǎo, wǒ jiào Xiǎo Míng.) - Hello, my name is Xiao Ming."}}]

Focus on high-frequency HSK {level} vocabulary. Include a mix of nouns, verbs, adjectives, and common phrases."""

        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2000,
        )
        result = response.choices[0].message.content.strip()
        if result.startswith("```"):
            result = result.split("\n", 1)[1]
            if result.endswith("```"):
                result = result[:-3]
        return json.loads(result)
    except Exception as e:
        return [{"question": f"Error: {e}", "answer": "Check API key"}]
