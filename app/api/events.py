"""Security event ingestion and risk assessment API."""

import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, status

from app.core.config import get_settings
from app.models.risk_assessment import RiskAssessment, RiskContext
from app.models.security_event import (
    EventAcceptedResponse,
    SecurityEventCreate,
    SecurityEventRecord,
)
from app.services.risk_engine import assess_risk

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/events", tags=["security-events"])

# Temporary in-memory stores for local foundation development only.
# Replace with durable repository implementations in a later phase.
_EVENTS: dict[UUID, SecurityEventRecord] = {}
_RISK_ASSESSMENTS: dict[UUID, RiskAssessment] = {}


@router.post(
    "",
    response_model=EventAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit a security event",
)
async def submit_event(
    payload: SecurityEventCreate,
    request: Request,
) -> EventAcceptedResponse:
    """Validate and acknowledge an event without invoking cloud services."""

    content_length = request.headers.get("content-length")
    max_bytes = get_settings().max_event_payload_bytes
    if content_length and int(content_length) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Request payload exceeds configured limit",
        )

    record = SecurityEventRecord(event=payload)
    _EVENTS[record.event_id] = record
    logger.info(
        "security_event_accepted event_id=%s source=%s event_type=%s severity=%s",
        record.event_id,
        payload.source.value,
        payload.event_type.value,
        payload.severity.value,
    )
    return EventAcceptedResponse(event_id=record.event_id)


@router.get("/{event_id}", response_model=SecurityEventRecord, summary="Get an event")
async def get_event(event_id: UUID) -> SecurityEventRecord:
    """Retrieve an event accepted by this local process."""

    record = _EVENTS.get(event_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return record


@router.post(
    "/{event_id}/analyze",
    response_model=RiskAssessment,
    summary="Analyze event risk",
)
async def analyze_event(
    event_id: UUID,
    context: RiskContext | None = None,
) -> RiskAssessment:
    """Calculate and store a deterministic risk assessment."""

    event = _EVENTS.get(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")

    assessment = assess_risk(event, context)
    _RISK_ASSESSMENTS[event_id] = assessment

    logger.info(
        "security_event_analyzed event_id=%s score=%s level=%s",
        event_id,
        assessment.risk_score,
        assessment.risk_level.value,
    )
    return assessment


@router.get(
    "/{event_id}/risk",
    response_model=RiskAssessment,
    summary="Get event risk assessment",
)
async def get_event_risk(event_id: UUID) -> RiskAssessment:
    """Retrieve the latest risk assessment for an event."""

    if event_id not in _EVENTS:
        raise HTTPException(status_code=404, detail="Event not found")

    assessment = _RISK_ASSESSMENTS.get(event_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Risk assessment not found")

    return assessment
