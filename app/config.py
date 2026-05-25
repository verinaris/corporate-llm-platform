"""
Zentrale Konfiguration.

Liest alle Einstellungen aus der .env-Datei und stellt sie typsicher zur
Verfügung. Pydantic validiert die Werte automatisch beim Start.
"""

from functools import lru_cache

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
    openai_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434"

    # --- App ---
    app_name: str = "Corporate LLM Platform"
    app_env: str = "development"
    app_debug: bool = True
    default_model: str = "claude-sonnet-4-6"
    default_max_tokens: int = 1024

    # --- Datenbank ---
    database_url: str = "sqlite:///./data/platform.db"

    # --- Server ---
    host: str = "0.0.0.0"
    port: int = 8000

    # --- Auth ---
    jwt_secret: str = "change-me-in-production"
    jwt_expire_hours: int = 24
    bootstrap_admin_email: str | None = None
    bootstrap_admin_password: str | None = None


@lru_cache
def get_settings() -> Settings:
    """Singleton-Zugriff auf Settings."""
    return Settings()  # type: ignore[call-arg]
