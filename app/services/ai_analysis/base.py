"""Interface for pluggable security analysis providers."""

from typing import Protocol

from app.models.ai_analysis import AIAnalysis
from app.models.risk_assessment import RiskAssessment
from app.models.security_event import SecurityEventRecord


class AIAnalysisProvider(Protocol):
    """Contract implemented by local and future hosted analysis providers."""

    def analyze(
        self,
        event: SecurityEventRecord,
        risk_assessment: RiskAssessment,
    ) -> AIAnalysis:
        """Generate explanatory analysis for an event and its risk assessment."""
        ...
