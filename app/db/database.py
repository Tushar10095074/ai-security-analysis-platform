"""SQLite database initialization and connection management."""

import sqlite3
from contextlib import closing
from pathlib import Path

from app.core.config import get_settings


class Database:
    """Manage short-lived SQLite connections and schema initialization."""

    def __init__(self, database_path: str) -> None:
        self.database_path = database_path

    def set_path(self, database_path: str | Path) -> None:
        """Set the database path, primarily for isolated tests."""
        self.database_path = str(database_path)

    def connect(self) -> sqlite3.Connection:
        """Create a new connection to the configured database."""
        if self.database_path != ":memory:":
            Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)

        connection = sqlite3.connect(
            self.database_path,
            timeout=10,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize(self) -> None:
        """Create database tables when they do not already exist."""
        with closing(self.connect()) as connection:
            with connection:
                connection.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS security_events (
                        event_id TEXT PRIMARY KEY,
                        status TEXT NOT NULL,
                        received_at TEXT NOT NULL,
                        event_json TEXT NOT NULL
                    );

                    CREATE TABLE IF NOT EXISTS risk_assessments (
                        event_id TEXT PRIMARY KEY,
                        assessment_json TEXT NOT NULL,
                        FOREIGN KEY (event_id)
                            REFERENCES security_events(event_id)
                            ON DELETE CASCADE
                    );

                    CREATE INDEX IF NOT EXISTS idx_events_received_at
                        ON security_events(received_at);
                    """
                )


database = Database(get_settings().database_path)
