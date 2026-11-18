"""Shared pytest fixtures."""

import pytest
from fastapi.testclient import TestClient

from app.api.events import _EVENTS, _RISK_ASSESSMENTS
from app.main import app


@pytest.fixture
def client() -> TestClient:
    """Provide an isolated test client and clear temporary stores."""

    _EVENTS.clear()
    _RISK_ASSESSMENTS.clear()

    with TestClient(app) as test_client:
        yield test_client

    _EVENTS.clear()
    _RISK_ASSESSMENTS.clear()
