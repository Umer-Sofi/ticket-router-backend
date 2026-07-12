"""Central configuration, loaded once at startup.

Why one file? So secrets/settings live in exactly ONE place. If the API key
is missing, `Settings()` raises immediately when the app boots — a loud,
early failure instead of a mysterious crash on the first OpenAI call.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Reads OPENAI_API_KEY from the .env file (or the real environment).
    # No default => the app refuses to start if it's missing. That's intentional.
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"

    # Tells pydantic-settings where to load values from.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


# Import THIS object everywhere (e.g. `from app.core.config import settings`).
# Created once, reused across the whole app.
settings = Settings()
