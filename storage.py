import json
import os

STORE_PATH = os.path.join(os.path.dirname(__file__), "data", "recipes.json")


def load_recipes() -> dict:
    if not os.path.exists(STORE_PATH):
        return {}
    with open(STORE_PATH, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def save_recipes(recipes: dict) -> None:
    os.makedirs(os.path.dirname(STORE_PATH), exist_ok=True)
    with open(STORE_PATH, "w", encoding="utf-8") as f:
        json.dump(recipes, f, indent=2, ensure_ascii=False)
