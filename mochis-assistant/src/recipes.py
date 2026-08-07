"""Recipe collection and meal planner."""

import json
import uuid
from datetime import date, timedelta
from pathlib import Path


def load_recipes(data_path: str) -> dict:
    path = Path(data_path)
    if not path.exists():
        return {"recipes": [], "meal_plans": {}}
    with open(path) as f:
        return json.load(f)


def save_recipes(data_path: str, data: dict):
    with open(data_path, "w") as f:
        json.dump(data, f, indent=2)


def add_recipe(data_path: str, title: str, ingredients: list = None,
               instructions: str = "", kcal: int = 0, tags: list = None,
               url: str = "", prep_time: str = "") -> str:
    data = load_recipes(data_path)
    rid = str(uuid.uuid4())[:8]
    data["recipes"].insert(0, {
        "id": rid,
        "title": title,
        "ingredients": ingredients or [],
        "instructions": instructions,
        "kcal": kcal,
        "tags": tags or [],
        "url": url,
        "prep_time": prep_time,
        "added_date": date.today().isoformat(),
    })
    save_recipes(data_path, data)
    return rid


def delete_recipe(data_path: str, rid: str) -> bool:
    data = load_recipes(data_path)
    n = len(data["recipes"])
    data["recipes"] = [r for r in data["recipes"] if r.get("id") != rid]
    if len(data["recipes"]) < n:
        save_recipes(data_path, data)
        return True
    return False


def plan_meal(data_path: str, meal_date: str, meal_type: str, recipe_id: str = None, custom: str = ""):
    data = load_recipes(data_path)
    data.setdefault("meal_plans", {}).setdefault(meal_date, {})[meal_type] = {
        "recipe_id": recipe_id,
        "custom": custom,
    }
    save_recipes(data_path, data)


def get_week_plan(data_path: str) -> dict:
    data = load_recipes(data_path)
    today = date.today()
    plan = {}
    recipe_lookup = {r["id"]: r["title"] for r in data.get("recipes", [])}

    for i in range(7):
        d = (today + timedelta(days=i)).isoformat()
        day_plan = data.get("meal_plans", {}).get(d, {})
        resolved = {}
        for meal, info in day_plan.items():
            if info.get("recipe_id") and info["recipe_id"] in recipe_lookup:
                resolved[meal] = recipe_lookup[info["recipe_id"]]
            elif info.get("custom"):
                resolved[meal] = info["custom"]
        plan[d] = resolved

    return {"plan": plan, "recipes": data.get("recipes", [])}
