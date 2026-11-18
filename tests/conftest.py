"""Shared pytest fixtures."""

import pytest
from fastapi.testclient import TestClient

from app.db.database import database
from app.main import app


@pytest.fixture
def client(tmp_path) -> TestClient:
    """Provide a test client backed by an isolated temporary SQLite database."""

    database.set_path(tmp_path / "security-test.db")

    with TestClient(app) as test_client:
        yield test_client
