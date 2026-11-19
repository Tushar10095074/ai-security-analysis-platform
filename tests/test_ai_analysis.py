"""AI security analysis API tests."""

from tests.test_events import VALID_EVENT


def submit_event(client):
    """Submit a valid security event and return its ID."""
    response = client.post("/api/v1/events", json=VALID_EVENT)
    assert response.status_code == 202
    return response.json()["event_id"]


def create_risk_assessment(client, event_id):
    """Create the deterministic risk assessment required for AI analysis."""
    response = client.post(f"/api/v1/events/{event_id}/analyze")
    assert response.status_code == 200
    return response.json()


def test_generate_ai_analysis(client):
    event_id = submit_event(client)
    risk = create_risk_assessment(client, event_id)

    response = client.post(
        f"/api/v1/events/{event_id}/ai-analysis"
    )

    assert response.status_code == 200

    body = response.json()
    assert body["event_id"] == event_id
    assert body["provider"] == "mock"
    assert body["analysis_version"] == "1.0"
    assert body["summary"]
    assert body["threat_explanation"]
    assert body["potential_impact"]
    assert body["key_observations"]
    assert body["recommended_actions"]
    assert body["investigation_steps"]
    assert body["limitations"]
    assert "risk_score" not in body

    # AI analysis must not change the deterministic risk assessment.
    risk_after = client.get(f"/api/v1/events/{event_id}/risk")
    assert risk_after.status_code == 200
    assert risk_after.json()["risk_score"] == risk["risk_score"]
    assert risk_after.json()["risk_level"] == risk["risk_level"]


def test_get_persisted_ai_analysis(client):
    event_id = submit_event(client)
    create_risk_assessment(client, event_id)

    generated = client.post(
        f"/api/v1/events/{event_id}/ai-analysis"
    )
    assert generated.status_code == 200

    retrieved = client.get(
        f"/api/v1/events/{event_id}/ai-analysis"
    )

    assert retrieved.status_code == 200
    assert retrieved.json() == generated.json()


def test_generate_ai_analysis_without_risk_returns_404(client):
    event_id = submit_event(client)

    response = client.post(
        f"/api/v1/events/{event_id}/ai-analysis"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Risk assessment not found"


def test_generate_ai_analysis_for_unknown_event_returns_404(client):
    response = client.post(
        "/api/v1/events/00000000-0000-0000-0000-000000000000/ai-analysis"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Event not found"


def test_get_ai_analysis_before_generation_returns_404(client):
    event_id = submit_event(client)

    response = client.get(
        f"/api/v1/events/{event_id}/ai-analysis"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "AI analysis not found"


def test_get_ai_analysis_for_unknown_event_returns_404(client):
    response = client.get(
        "/api/v1/events/00000000-0000-0000-0000-000000000000/ai-analysis"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Event not found"


def test_regenerating_ai_analysis_updates_persisted_result(client):
    event_id = submit_event(client)
    create_risk_assessment(client, event_id)

    first = client.post(
        f"/api/v1/events/{event_id}/ai-analysis"
    )
    second = client.post(
        f"/api/v1/events/{event_id}/ai-analysis"
    )

    assert first.status_code == 200
    assert second.status_code == 200

    retrieved = client.get(
        f"/api/v1/events/{event_id}/ai-analysis"
    )

    assert retrieved.status_code == 200
    assert retrieved.json() == second.json()
