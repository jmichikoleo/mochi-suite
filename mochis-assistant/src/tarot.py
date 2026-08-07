"""Tarot card daily spread with GPT-powered analysis (3-5 card spreads)."""

import json
import random
from datetime import date
from pathlib import Path

MAJOR_ARCANA = [
    "The Fool", "The Magician", "The High Priestess", "The Empress", "The Emperor",
    "The Hierophant", "The Lovers", "The Chariot", "Strength", "The Hermit",
    "Wheel of Fortune", "Justice", "The Hanged Man", "Death", "Temperance",
    "The Devil", "The Tower", "The Star", "The Moon", "The Sun",
    "Judgement", "The World"
]

MINOR_ARCANA_SUITS = ["Wands", "Cups", "Swords", "Pentacles"]
MINOR_ARCANA_RANKS = [
    "Ace", "Two", "Three", "Four", "Five", "Six", "Seven",
    "Eight", "Nine", "Ten", "Page", "Knight", "Queen", "King"
]

ALL_CARDS = MAJOR_ARCANA.copy()
for suit in MINOR_ARCANA_SUITS:
    for rank in MINOR_ARCANA_RANKS:
        ALL_CARDS.append(f"{rank} of {suit}")

# Spread positions and their meanings
SPREAD_LAYOUTS = {
    3: {
        "name": "Past, Present, Future",
        "positions": ["Past / What led here", "Present / Current energy", "Future / Where this leads"]
    },
    4: {
        "name": "Situation Spread",
        "positions": ["Current situation", "Challenge", "Advice", "Outcome"]
    },
    5: {
        "name": "Daily Cross",
        "positions": ["Theme of the day", "Challenge to face", "Hidden influence", "Advice to follow", "Likely outcome"]
    },
}


def get_all_cards() -> list:
    return ALL_CARDS


def get_spread_layouts() -> dict:
    return SPREAD_LAYOUTS


def load_readings(data_path: str) -> dict:
    path = Path(data_path)
    if not path.exists():
        return {"readings": []}
    with open(path) as f:
        return json.load(f)


def save_reading(data_path: str, reading: dict):
    data = load_readings(data_path)
    data["readings"].insert(0, reading)
    data["readings"] = data["readings"][:30]
    with open(data_path, "w") as f:
        json.dump(data, f, indent=2)


def draw_random_spread(num_cards: int = 3) -> list:
    """Draw random cards with random orientations (no duplicates)."""
    num_cards = max(3, min(5, num_cards))
    drawn = random.sample(ALL_CARDS, num_cards)
    return [{"card": c, "orientation": random.choice(["upright", "reversed"])} for c in drawn]


def generate_spread_reading(cards: list, api_key: str,
                             model: str = "gpt-4o-mini",
                             context: dict = None) -> str:
    """Generate a multi-card spread reading using OpenAI."""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        num = len(cards)
        layout = SPREAD_LAYOUTS.get(num, SPREAD_LAYOUTS[3])

        ctx_parts = []
        if context:
            if context.get("mood"):
                mood_labels = {1: "very low", 2: "low", 3: "neutral", 4: "good", 5: "great"}
                ctx_parts.append(f"Current mood: {mood_labels.get(context['mood'], 'neutral')}")
            if context.get("tasks_count"):
                ctx_parts.append(f"Has {context['tasks_count']} tasks today")
            if context.get("cycle_phase"):
                ctx_parts.append(f"Menstrual cycle phase: {context['cycle_phase']}")
            if context.get("energy"):
                ctx_parts.append(f"Energy level: {context['energy']}")

        context_str = "\n".join(ctx_parts) if ctx_parts else "No additional context."

        # Build card list for prompt
        card_lines = []
        for i, c in enumerate(cards):
            pos = layout["positions"][i] if i < len(layout["positions"]) else f"Position {i+1}"
            card_lines.append(f"Position {i+1} ({pos}): **{c['card']}** ({c['orientation']})")

        cards_str = "\n".join(card_lines)

        prompt = f"""You are a gentle, insightful tarot reader giving a daily {num}-card spread reading.
Spread type: {layout['name']}

Cards drawn:
{cards_str}

Querent's context:
{context_str}

Give a warm, insightful daily reading focused on how today will go.

For EACH card position:
- State the position meaning and card name (1 line)
- What this card means in this position for today (2-3 sentences)

Then give:
- Overall synthesis: how the cards connect (2-3 sentences)
- Practical advice for the day (1-2 sentences)

Use clear section headers with the position names. Be warm, supportive, and specific to their context. Use "you" language. Keep the total under 400 words."""

        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=800,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Could not generate reading: {e}"


def generate_reading(card: str, orientation: str, api_key: str,
                     model: str = "gpt-4o-mini", context: dict = None) -> str:
    """Single card reading (backward compat)."""
    cards = [{"card": card, "orientation": orientation}]
    return generate_spread_reading(cards, api_key, model, context)
