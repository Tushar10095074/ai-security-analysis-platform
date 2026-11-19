"""Persistent repository for AI security analyses."""

from contextlib import closing
from uuid import UUID

from app.db.database import Database
from app.models.ai_analysis import AIAnalysis


class AIAnalysisRepository:
    """Store and retrieve the latest AI analysis using SQLite."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def save(self, analysis: AIAnalysis) -> None:
        """Insert or replace an event's latest AI analysis."""
        with closing(self.db.connect()) as connection:
            with connection:
                connection.execute(
                    """
                    INSERT INTO ai_analyses (event_id, analysis_json)
                    VALUES (?, ?)
                    ON CONFLICT(event_id) DO UPDATE SET
                        analysis_json = excluded.analysis_json
                    """,
                    (
                        analysis.event_id,
                        analysis.model_dump_json(),
                    ),
                )

    def get(self, event_id: UUID) -> AIAnalysis | None:
        """Retrieve the latest analysis for an event."""
        with closing(self.db.connect()) as connection:
            with connection:
                row = connection.execute(
                    """
                    SELECT analysis_json
                    FROM ai_analyses
                    WHERE event_id = ?
                    """,
                    (str(event_id),),
                ).fetchone()

        if row is None:
            return None

        return AIAnalysis.model_validate_json(row["analysis_json"])
