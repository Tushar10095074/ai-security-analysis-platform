"""Security event ingestion and risk assessment API."""

import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, status

from app.core.config import get_settings
from app.db.database import database
from app.models.ai_analysis import AIAnalysis
from app.models.risk_assessment import RiskAssessment, RiskContext
from app.models.security_event import (
    EventAcceptedResponse,
    SecurityEventCreate,
    SecurityEventRecord,
)
from app.repositories.ai_analysis_repository import AIAnalysisRepository
from app.repositories.event_repository import EventRepository
from app.repositories.risk_repository import RiskAssessmentRepository
from app.services.ai_analysis.mock_provider import MockAIAnalysisProvider
from app.services.risk_engine import assess_risk

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/events", tags=["security-events"])

event_repository = EventRepository(database)
risk_repository = RiskAssessmentRepository(database)
ai_analysis_repository = AIAnalysisRepository(database)
ai_analysis_provider = MockAIAnalysisProvider()


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
    """Validate and persist an event without invoking cloud services."""

    content_length = request.headers.get("content-length")
    max_bytes = get_settings().max_event_payload_bytes
    if content_length and int(content_length) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Request payload exceeds configured limit",
        )

    record = SecurityEventRecord(event=payload)
    event_repository.save(record)

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
    """Retrieve a persisted security event."""

    record = event_repository.get(event_id)
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
    """Calculate and persist a deterministic risk assessment."""

    event = event_repository.get(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")

    assessment = assess_risk(event, context)
    risk_repository.save(assessment)

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
    """Retrieve the latest persisted risk assessment."""

    if event_repository.get(event_id) is None:
        raise HTTPException(status_code=404, detail="Event not found")

    assessment = risk_repository.get(event_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Risk assessment not found")

    return assessment

@router.post(
    "/{event_id}/ai-analysis",
    response_model=AIAnalysis,
    summary="Generate explanatory AI analysis",
)
async def analyze_event_with_ai(event_id: UUID) -> AIAnalysis:
    """Generate and persist explanatory analysis using the local mock provider."""

    event = event_repository.get(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")

    assessment = risk_repository.get(event_id)
    if assessment is None:
        raise HTTPException(
            status_code=404,
            detail="Risk assessment not found",
        )

    analysis = ai_analysis_provider.analyze(event, assessment)
    ai_analysis_repository.save(analysis)

    logger.info(
        "security_event_ai_analyzed event_id=%s provider=%s",
        event_id,
        analysis.provider,
    )
    return analysis


@router.get(
    "/{event_id}/ai-analysis",
    response_model=AIAnalysis,
    summary="Get persisted AI analysis",
)
async def get_event_ai_analysis(event_id: UUID) -> AIAnalysis:
    """Retrieve the latest persisted explanatory analysis."""

    if event_repository.get(event_id) is None:
        raise HTTPException(status_code=404, detail="Event not found")

    analysis = ai_analysis_repository.get(event_id)
    if analysis is None:
        raise HTTPException(
            status_code=404,
            detail="AI analysis not found",
        )

    return analysis

