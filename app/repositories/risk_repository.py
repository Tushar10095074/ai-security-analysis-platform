"""Persistent repository for risk assessments."""

from contextlib import closing
from uuid import UUID

from app.db.database import Database
from app.models.risk_assessment import RiskAssessment


class RiskAssessmentRepository:
    """Store and retrieve risk assessments using SQLite."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def save(self, assessment: RiskAssessment) -> None:
        """Insert or replace an event's latest risk assessment."""
        with closing(self.db.connect()) as connection:
            with connection:
                connection.execute(
                    """
                    INSERT INTO risk_assessments (event_id, assessment_json)
                    VALUES (?, ?)
                    ON CONFLICT(event_id) DO UPDATE SET
                        assessment_json = excluded.assessment_json
                    """,
                    (
                        str(assessment.event_id),
                        assessment.model_dump_json(),
                    ),
                )

    def get(self, event_id: UUID) -> RiskAssessment | None:
        """Retrieve the latest assessment for an event."""
        with closing(self.db.connect()) as connection:
            with connection:
                row = connection.execute(
                    """
                    SELECT assessment_json
                    FROM risk_assessments
                    WHERE event_id = ?
                    """,
                    (str(event_id),),
                ).fetchone()

        if row is None:
            return None

        return RiskAssessment.model_validate_json(row["assessment_json"])
