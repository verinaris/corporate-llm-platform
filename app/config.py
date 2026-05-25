"""
Zentrale Konfiguration.

Liest alle Einstellungen aus der .env-Datei und stellt sie typsicher zur
Verfügung. Pydantic validiert die Werte automatisch beim Start.
"""

import secrets
from functools import lru_cache

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Alle App-Einstellungen, gelesen aus .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- LLM Provider ---
    anthropic_api_key: str
    anthropic_base_url: str | None = None  # für EU-Region z.B. https://api.eu.anthropic.com
    openai_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434"

    # --- App ---
    app_name: str = "Corporate LLM Platform"
    app_env: str = "development"  # development | staging | production
    app_debug: bool = True
    default_model: str = "claude-sonnet-4-6"
    default_max_tokens: int = 1024

    # --- Datenbank ---
    database_url: str = "sqlite:///./data/platform.db"

    # --- Server ---
    host: str = "0.0.0.0"
    port: int = 8000

    # --- CORS (für später, wenn Frontend auf anderem Host läuft) ---
    cors_allowed_origins: str = ""  # komma-separiert

    # --- Auth ---
    jwt_secret: str = "change-me-in-production"
    jwt_expire_hours: int = 24
    bootstrap_admin_email: str | None = None
    bootstrap_admin_password: str | None = None

    # ------------------------------------------------------------------ #
    # Validators
    # ------------------------------------------------------------------ #
    @field_validator("app_env")
    @classmethod
    def _validate_env(cls, v: str) -> str:
        v = v.lower().strip()
        if v not in {"development", "staging", "production"}:
            raise ValueError(
                "APP_ENV must be one of: development, staging, production"
            )
        return v

    @model_validator(mode="after")
    def _check_production_requirements(self) -> "Settings":
        """In production-Mode: keine Default-Werte tolerieren."""
        if self.app_env == "production":
            problems: list[str] = []
            if self.jwt_secret in {"change-me-in-production", ""}:
                problems.append("JWT_SECRET ist Default — bitte generieren!")
            if len(self.jwt_secret) < 32:
                problems.append("JWT_SECRET zu kurz (mindestens 32 Zeichen)")
            if self.app_debug:
                problems.append("APP_DEBUG=true in Production ist gefährlich")
            if problems:
                raise ValueError(
                    "Production-Setup unsicher:\n  - "
                    + "\n  - ".join(problems)
                )
        return self

    @property
    def cors_origins_list(self) -> list[str]:
        """CORS-Origins als Liste, leere Strings entfernt."""
        return [o.strip() for o in self.cors_allowed_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """Singleton-Zugriff auf Settings."""
    return Settings()  # type: ignore[call-arg]
