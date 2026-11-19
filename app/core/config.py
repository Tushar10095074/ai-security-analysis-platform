"""Typed application settings."""

from functools import lru_cache
from typing import Literal

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
    database_path: str = "data/security.db"

    # AI analysis provider. "mock" (default) never calls an external service.
    ai_provider: Literal["mock", "vertex"] = "mock"
    vertex_project: str | None = None
    vertex_location: str = "us-east1"
    vertex_model: str = "gemini-2.5-flash-lite"
    vertex_timeout_seconds: int = Field(default=30, ge=5, le=120)
    vertex_max_output_tokens: int = Field(default=2_048, ge=256, le=8_192)
    # Cost guard: maximum Vertex AI calls per running instance (process lifetime).
    vertex_max_calls_per_instance: int = Field(default=50, ge=1)


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
