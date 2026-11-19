"""Structured security event analysis response model."""

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AIAnalysis(BaseModel):
    """Store explanatory analysis separately from deterministic risk scoring."""

    model_config = ConfigDict(extra="forbid")

    event_id: str
    provider: Literal["mock", "vertex_ai"] = "mock"
    model: str | None = None
    analysis_version: str = "1.0"
    summary: str = Field(min_length=1, max_length=2000)
    threat_explanation: str = Field(min_length=1, max_length=4000)
    potential_impact: str = Field(min_length=1, max_length=4000)
    key_observations: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    investigation_steps: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )
