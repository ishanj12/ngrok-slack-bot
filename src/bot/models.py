"""
Model preferences module for per-user model selection.
Persists preferences to disk so they survive server restarts.
"""

import json
import os

PREFS_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "data", "model_prefs.json")

AVAILABLE_MODELS = [
    {"id": "gpt-4o-mini", "name": "GPT-4o Mini (default)", "provider": "openai"},
    {"id": "gpt-4o", "name": "GPT-4o", "provider": "openai"},
    {"id": "o3-mini", "name": "o3-mini", "provider": "openai"},
    {"id": "claude-sonnet-4-20250514", "name": "Claude Sonnet 4", "provider": "anthropic"},
    {"id": "claude-3-5-haiku-20241022", "name": "Claude 3.5 Haiku", "provider": "anthropic"},
    {"id": "gemini-2.5-flash", "name": "Gemini 2.5 Flash", "provider": "gemini"},
    {"id": "gemini-2.5-pro", "name": "Gemini 2.5 Pro", "provider": "gemini"},
]

VALID_MODEL_IDS = {m["id"] for m in AVAILABLE_MODELS}


def get_model_provider(model_id: str) -> str:
    for m in AVAILABLE_MODELS:
        if m["id"] == model_id:
            return m["provider"]
    return "openai"


def _load_preferences() -> dict[str, str]:
    try:
        with open(PREFS_FILE) as f:
            data = json.load(f)
            return {k: v for k, v in data.items() if v in VALID_MODEL_IDS}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_preferences(prefs: dict[str, str]) -> None:
    os.makedirs(os.path.dirname(PREFS_FILE), exist_ok=True)
    with open(PREFS_FILE, "w") as f:
        json.dump(prefs, f)


_user_preferences: dict[str, str] | None = None


def _get_prefs() -> dict[str, str]:
    global _user_preferences
    if _user_preferences is None:
        _user_preferences = _load_preferences()
    return _user_preferences


def get_user_model(user_id: str) -> str:
    return _get_prefs().get(user_id, "gpt-4o-mini")


def set_user_model(user_id: str, model: str) -> None:
    prefs = _get_prefs()
    prefs[user_id] = model
    _save_preferences(prefs)


def get_available_models() -> list[dict[str, str]]:
    return AVAILABLE_MODELS
