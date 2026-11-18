"""Persistent repository for security events."""

from contextlib import closing
from uuid import UUID

from app.db.database import Database
from app.models.security_event import SecurityEventRecord


class EventRepository:
    """Store and retrieve security events using SQLite."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def save(self, record: SecurityEventRecord) -> None:
        """Insert or replace a security event."""
        with closing(self.db.connect()) as connection:
            with connection:
                connection.execute(
                    """
                    INSERT INTO security_events (
                        event_id, status, received_at, event_json
                    )
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(event_id) DO UPDATE SET
                        status = excluded.status,
                        received_at = excluded.received_at,
                        event_json = excluded.event_json
                    """,
                    (
                        str(record.event_id),
                        record.status,
                        record.received_at.isoformat(),
                        record.model_dump_json(),
                    ),
                )

    def get(self, event_id: UUID) -> SecurityEventRecord | None:
        """Retrieve a security event by ID."""
        with closing(self.db.connect()) as connection:
            with connection:
                row = connection.execute(
                    "SELECT event_json FROM security_events WHERE event_id = ?",
                    (str(event_id),),
                ).fetchone()

        if row is None:
            return None

        return SecurityEventRecord.model_validate_json(row["event_json"])
