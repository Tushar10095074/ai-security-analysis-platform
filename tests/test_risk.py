"""Risk assessment API tests."""

from tests.test_events import VALID_EVENT


def submit_valid_event(client):
    """Submit a valid event and return its ID."""

    response = client.post("/api/v1/events", json=VALID_EVENT)
    assert response.status_code == 202
    return response.json()["event_id"]


def test_analyze_event_returns_risk_assessment(client):
    event_id = submit_valid_event(client)

    response = client.post(
        f"/api/v1/events/{event_id}/analyze",
        json={
            "exploit_available": True,
            "active_exploitation": True,
            "sensitive_data": True,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["event_id"] == event_id
    assert body["risk_score"] == 100
    assert body["risk_level"] == "critical"
    assert body["scoring_version"] == "1.0"
    assert len(body["factors"]) >= 5
    assert body["recommendations"]


def test_analyze_event_with_default_context(client):
    event_id = submit_valid_event(client)

    response = client.post(f"/api/v1/events/{event_id}/analyze")

    assert response.status_code == 200
    body = response.json()

    # High severity (55) + high business criticality (10)
    # + internet exposure (10) = 75.
    assert body["risk_score"] == 75
    assert body["risk_level"] == "high"


def test_get_risk_assessment(client):
    event_id = submit_valid_event(client)
    client.post(f"/api/v1/events/{event_id}/analyze")

    response = client.get(f"/api/v1/events/{event_id}/risk")

    assert response.status_code == 200
    assert response.json()["event_id"] == event_id


def test_analyze_unknown_event_returns_404(client):
    response = client.post(
        "/api/v1/events/00000000-0000-0000-0000-000000000000/analyze"
    )
    assert response.status_code == 404


def test_get_risk_before_analysis_returns_404(client):
    event_id = submit_valid_event(client)

    response = client.get(f"/api/v1/events/{event_id}/risk")

    assert response.status_code == 404
    assert response.json()["detail"] == "Risk assessment not found"


def test_invalid_risk_context_is_rejected(client):
    event_id = submit_valid_event(client)

    response = client.post(
        f"/api/v1/events/{event_id}/analyze",
        json={"active_exploitation": "possibly"},
    )

    assert response.status_code == 422
