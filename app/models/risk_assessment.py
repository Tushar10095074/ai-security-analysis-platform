"""Risk assessment models and supporting context."""

from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RiskLevel(StrEnum):
    """Calculated risk classification."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskContext(BaseModel):
    """Additional investigation context supplied by an analyst or integration."""

    model_config = ConfigDict(extra="forbid")

    exploit_available: bool | None = None
    active_exploitation: bool | None = None
    sensitive_data: bool | None = None


class RiskFactor(BaseModel):
    """An explainable contribution to the risk score."""

    name: str
    points: int
    explanation: str


class RiskAssessment(BaseModel):
    """Calculated risk assessment for a security event."""

    model_config = ConfigDict(extra="forbid")

    event_id: UUID
    risk_score: int = Field(ge=0, le=100)
    risk_level: RiskLevel
    factors: list[RiskFactor]
    recommendations: list[str]
    scoring_version: str = "1.0"
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
