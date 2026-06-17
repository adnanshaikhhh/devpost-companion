"""
Application configuration loaded from environment variables.

We use pydantic-settings so values can be overridden in production
(Railway, Docker, etc.) without touching code.
"""
from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly-typed settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ────────────────────────────────────────────────────────────
    app_env: str = "development"
    log_level: str = "info"

    # ── OpenAI ─────────────────────────────────────────────────────────
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_temperature: float = 0.7

    # ── CORS ───────────────────────────────────────────────────────────
    cors_origins: str = "http://localhost:5173,http://localhost:8000"

    # ── Database ───────────────────────────────────────────────────────
    database_url: str = "sqlite:///./devpost_companion.db"

    # ── Derived helpers ────────────────────────────────────────────────
    @property
    def has_openai(self) -> bool:
        """True when a non-empty API key is configured."""
        return bool(self.openai_api_key and self.openai_api_key.strip())

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse the comma-separated CORS allowlist."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached settings instance."""
    return Settings()