"""Typed application settings."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings loaded from environment variables or a local .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "AI Security Analysis Platform"
    app_version: str = "0.1.0"
    environment: str = "local"
    log_level: str = "INFO"
    max_event_payload_bytes: int = Field(default=262_144, ge=1_024)
    api_key_enabled: bool = False


@lru_cache

def get_settings() -> Settings:
    """Return cached application settings."""

    return Settings()
