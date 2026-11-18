"""Canonical security event contract shared by all event sources."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class EventSource(StrEnum):
    """Supported event producers."""

    SECURITY_COMMAND_CENTER = "security_command_center"
    CLOUD_LOGGING = "cloud_logging"
    CLOUD_MONITORING = "cloud_monitoring"
    AWS_SECURITY_HUB = "aws_security_hub"
    AZURE_DEFENDER = "azure_defender"
    CUSTOM = "custom"


class EventType(StrEnum):
    """Normalized security event categories."""

    VULNERABILITY = "vulnerability"
    THREAT = "threat"
    MISCONFIGURATION = "misconfiguration"
    IAM_CHANGE = "iam_change"
    DATA_EXPOSURE = "data_exposure"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    POLICY_VIOLATION = "policy_violation"
    OTHER = "other"


class Severity(StrEnum):
    """Source-reported severity; this is not the calculated risk level."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"
    UNKNOWN = "unknown"


class ResourceReference(BaseModel):
    """Cloud or external resource associated with a finding."""

    model_config = ConfigDict(extra="forbid")

    provider: str = Field(min_length=1, max_length=40, examples=["gcp"])
    resource_type: str = Field(min_length=1, max_length=120)
    resource_id: str = Field(min_length=1, max_length=1_024)
    project_id: str | None = Field(default=None, max_length=128)
    region: str | None = Field(default=None, max_length=128)
    display_name: str | None = Field(default=None, max_length=256)
    internet_exposed: bool | None = None
    business_criticality: str | None = Field(default=None, max_length=40)


class SecurityEventCreate(BaseModel):
    """Inbound event payload accepted by the platform."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    source: EventSource
    source_event_id: str | None = Field(default=None, max_length=256)
    event_type: EventType
    severity: Severity = Severity.UNKNOWN
    title: str = Field(min_length=3, max_length=256)
    description: str = Field(min_length=1, max_length=10_000)
    resource: ResourceReference
    observed_at: datetime
    labels: dict[str, str] = Field(default_factory=dict, max_length=50)
    evidence: dict[str, Any] = Field(default_factory=dict)
    source_url: HttpUrl | None = None

    @field_validator("observed_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        """Reject ambiguous timestamps without a timezone."""

        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("observed_at must include a timezone")
        return value


class SecurityEventRecord(BaseModel):
    """Accepted event envelope returned by the API."""

    model_config = ConfigDict(extra="forbid")

    event_id: UUID = Field(default_factory=uuid4)
    status: str = "RECEIVED"
    received_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    event: SecurityEventCreate


class EventAcceptedResponse(BaseModel):
    """Acknowledgement returned after successful validation."""

    event_id: UUID
    status: str = "ACCEPTED"
    message: str = "Security event accepted for processing"
