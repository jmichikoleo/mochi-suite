"""Flashcard system with GPT generation and spaced repetition."""

import json
import uuid
from datetime import date, timedelta
from pathlib import Path


def load_flashcards(data_path: str) -> dict:
    path = Path(data_path)
    if not path.exists():
        return {"decks": []}
    with open(path) as f:
        return json.load(f)


def save_flashcards(data_path: str, data: dict):
    with open(data_path, "w") as f:
        json.dump(data, f, indent=2)


def create_deck(data_path: str, title: str, course_id: str = "",
                cards: list = None) -> str:
    data = load_flashcards(data_path)
    did = str(uuid.uuid4())[:8]
    deck = {
        "id": did,
        "title": title,
        "course_id": course_id,
        "cards": [],
        "created": date.today().isoformat(),
    }
    for card in (cards or []):
        card["id"] = str(uuid.uuid4())[:8]
        card.setdefault("ease", 2.5)
        card.setdefault("interval", 1)
        card.setdefault("next_review", date.today().isoformat())
        card.setdefault("reviews", 0)
        deck["cards"].append(card)

    data["decks"].insert(0, deck)
    save_flashcards(data_path, data)
    return did


def add_card(data_path: str, deck_id: str, question: str, answer: str) -> str:
    data = load_flashcards(data_path)
    for deck in data["decks"]:
        if deck["id"] == deck_id:
            cid = str(uuid.uuid4())[:8]
            deck["cards"].append({
                "id": cid,
                "question": question,
                "answer": answer,
                "ease": 2.5,
                "interval": 1,
                "next_review": date.today().isoformat(),
                "reviews": 0,
            })
            save_flashcards(data_path, data)
            return cid
    return None


def delete_deck(data_path: str, deck_id: str) -> bool:
    data = load_flashcards(data_path)
    n = len(data["decks"])
    data["decks"] = [d for d in data["decks"] if d["id"] != deck_id]
    if len(data["decks"]) < n:
        save_flashcards(data_path, data)
        return True
    return False


def review_card(data_path: str, deck_id: str, card_id: str, rating: str) -> bool:
    """Rate a card: easy, medium, hard. Updates spaced repetition schedule.

    SM-2 simplified:
    - hard: interval stays same, ease decreases
    - medium: interval * ease, ease stays
    - easy: interval * ease * 1.3, ease increases
    """
    data = load_flashcards(data_path)
    for deck in data["decks"]:
        if deck["id"] != deck_id:
            continue
        for card in deck["cards"]:
            if card["id"] != card_id:
                continue

            ease = card.get("ease", 2.5)
            interval = card.get("interval", 1)

            if rating == "hard":
                interval = max(1, interval)
                ease = max(1.3, ease - 0.2)
            elif rating == "medium":
                interval = max(1, round(interval * ease))
                # ease stays
            elif rating == "easy":
                interval = max(1, round(interval * ease * 1.3))
                ease = min(3.0, ease + 0.1)

            card["ease"] = round(ease, 2)
            card["interval"] = interval
            card["next_review"] = (date.today() + timedelta(days=interval)).isoformat()
            card["reviews"] = card.get("reviews", 0) + 1

            save_flashcards(data_path, data)
            return True
    return False


def get_due_cards(data_path: str, deck_id: str = None) -> list:
    """Get all cards due for review today."""
    data = load_flashcards(data_path)
    today_str = date.today().isoformat()
    due = []

    for deck in data["decks"]:
        if deck_id and deck["id"] != deck_id:
            continue
        for card in deck["cards"]:
            if card.get("next_review", "") <= today_str:
                due.append({
                    "deck_id": deck["id"],
                    "deck_title": deck["title"],
                    **card,
                })

    return due


def generate_flashcards_from_text(text: str, api_key: str,
                                   model: str = "gpt-4o-mini",
                                   num_cards: int = 10) -> list:
    """Use GPT to generate flashcards from text content."""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        prompt = f"""Generate {num_cards} flashcards from this study material. Each flashcard should test a key concept.

Material:
{text[:4000]}

Return ONLY valid JSON array:
[
  {{"question": "What is X?", "answer": "X is..."}},
  ...
]

Make questions specific and answers concise (1-3 sentences). Focus on key concepts, definitions, and important relationships."""

        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=2000,
        )

        result = response.choices[0].message.content.strip()
        if result.startswith("```"):
            result = result.split("\n", 1)[1]
            if result.endswith("```"):
                result = result[:-3]

        return json.loads(result)
    except Exception as e:
        return [{"question": f"Error generating cards: {e}", "answer": "Check your API key and try again."}]
