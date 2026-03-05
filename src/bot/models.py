"""
Model preferences module for per-user model selection.
"""

AVAILABLE_MODELS = [
    {"id": "gpt-4o-mini", "name": "GPT-4o Mini (default)", "provider": "openai"},
    {"id": "gpt-4o", "name": "GPT-4o", "provider": "openai"},
    {"id": "o3-mini", "name": "o3-mini", "provider": "openai"},
    {"id": "claude-sonnet-4-20250514", "name": "Claude Sonnet 4", "provider": "anthropic"},
    {"id": "claude-3-5-haiku-20241022", "name": "Claude 3.5 Haiku", "provider": "anthropic"},
    {"id": "gemini-2.5-flash", "name": "Gemini 2.5 Flash", "provider": "gemini"},
    {"id": "gemini-2.5-pro", "name": "Gemini 2.5 Pro", "provider": "gemini"},
]


def get_model_provider(model_id: str) -> str:
    for m in AVAILABLE_MODELS:
        if m["id"] == model_id:
            return m["provider"]
    return "openai"

_user_preferences: dict[str, str] = {}


def get_user_model(user_id: str) -> str:
    return _user_preferences.get(user_id, "gpt-4o-mini")


def set_user_model(user_id: str, model: str) -> None:
    _user_preferences[user_id] = model


def get_available_models() -> list[dict[str, str]]:
    return AVAILABLE_MODELS
