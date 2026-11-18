"""Deterministic and explainable security event risk scoring."""

from datetime import UTC, datetime

from app.models.risk_assessment import (
    RiskAssessment,
    RiskContext,
    RiskFactor,
    RiskLevel,
)
from app.models.security_event import (
    EventType,
    SecurityEventRecord,
    Severity,
)

SEVERITY_POINTS = {
    Severity.CRITICAL: 70,
    Severity.HIGH: 55,
    Severity.MEDIUM: 35,
    Severity.LOW: 15,
    Severity.INFO: 5,
    Severity.UNKNOWN: 10,
}

BUSINESS_CRITICALITY_POINTS = {
    "low": 0,
    "medium": 5,
    "high": 10,
    "critical": 15,
}


def classify_risk(score: int) -> RiskLevel:
    """Convert a numeric score into a risk classification."""

    if score >= 80:
        return RiskLevel.CRITICAL
    if score >= 60:
        return RiskLevel.HIGH
    if score >= 30:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW


def build_recommendations(
    event: SecurityEventRecord,
    context: RiskContext,
) -> list[str]:
    """Generate actionable recommendations from confirmed event context."""

    recommendations: list[str] = []
    resource = event.event.resource

    if context.active_exploitation is True:
        recommendations.append(
            "Initiate incident response immediately and investigate active exploitation."
        )

    if resource.internet_exposed is True:
        recommendations.append(
            "Review external exposure and restrict unnecessary public network access."
        )

    if context.exploit_available is True:
        recommendations.append(
            "Prioritize vendor mitigation or patching because an exploit is available."
        )

    if context.sensitive_data is True:
        recommendations.append(
            "Assess potential data exposure and review access to sensitive information."
        )

    if event.event.event_type == EventType.IAM_CHANGE:
        recommendations.append(
            "Review the identity change, validate authorization, and audit affected permissions."
        )

    if event.event.event_type == EventType.VULNERABILITY:
        recommendations.append(
            "Validate the vulnerability and prioritize remediation based on asset criticality."
        )

    if event.event.event_type == EventType.DATA_EXPOSURE:
        recommendations.append(
            "Investigate the scope of exposed data and contain unauthorized access."
        )

    if not recommendations:
        recommendations.append(
            "Investigate the event, validate affected resources, and document remediation."
        )

    return recommendations


def assess_risk(
    event: SecurityEventRecord,
    context: RiskContext | None = None,
) -> RiskAssessment:
    """Calculate an explainable risk score for an accepted security event."""

    context = context or RiskContext()
    resource = event.event.resource
    factors: list[RiskFactor] = []

    severity_points = SEVERITY_POINTS[event.event.severity]
    factors.append(
        RiskFactor(
            name="severity",
            points=severity_points,
            explanation=f"Source-reported severity is {event.event.severity.value}.",
        )
    )

    criticality = (
        resource.business_criticality.lower()
        if resource.business_criticality
        else None
    )
    asset_points = BUSINESS_CRITICALITY_POINTS.get(criticality, 0)

    if criticality in BUSINESS_CRITICALITY_POINTS and asset_points > 0:
        factors.append(
            RiskFactor(
                name="business_criticality",
                points=asset_points,
                explanation=f"Asset business criticality is {criticality}.",
            )
        )

    if resource.internet_exposed is True:
        factors.append(
            RiskFactor(
                name="internet_exposure",
                points=10,
                explanation="The affected resource is reported as internet exposed.",
            )
        )

    context_factors = (
        (
            "exploit_available",
            context.exploit_available,
            15,
            "An exploit is reported as available.",
        ),
        (
            "active_exploitation",
            context.active_exploitation,
            20,
            "Active exploitation is reported.",
        ),
        (
            "sensitive_data",
            context.sensitive_data,
            10,
            "Sensitive data is reported as involved.",
        ),
    )

    for name, confirmed, points, explanation in context_factors:
        if confirmed is True:
            factors.append(
                RiskFactor(
                    name=name,
                    points=points,
                    explanation=explanation,
                )
            )

    score = min(sum(factor.points for factor in factors), 100)

    return RiskAssessment(
        event_id=event.event_id,
        risk_score=score,
        risk_level=classify_risk(score),
        factors=factors,
        recommendations=build_recommendations(event, context),
        evaluated_at=datetime.now(UTC),
    )
