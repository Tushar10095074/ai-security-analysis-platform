"""Security event API tests."""

from uuid import UUID

VALID_EVENT = {
    "source": "security_command_center",
    "source_event_id": "finding-123",
    "event_type": "vulnerability",
    "severity": "high",
    "title": "Publicly exposed vulnerable VM",
    "description": "A production VM has a publicly reachable vulnerable service.",
    "resource": {
        "provider": "gcp",
        "resource_type": "compute.googleapis.com/Instance",
        "resource_id": "projects/demo/zones/us-east1-b/instances/web-01",
        "project_id": "demo-project",
        "region": "us-east1",
        "display_name": "web-01",
        "internet_exposed": True,
        "business_criticality": "high",
    },
    "observed_at": "2026-11-17T10:00:00+05:30",
    "labels": {"environment": "production"},
    "evidence": {"port": 443},
}


def test_submit_event_returns_202_and_event_id(client):
    response = client.post("/api/v1/events", json=VALID_EVENT)
    assert response.status_code == 202
    body = response.json()
    assert UUID(body["event_id"])
    assert body["status"] == "ACCEPTED"


def test_get_submitted_event(client):
    submitted = client.post("/api/v1/events", json=VALID_EVENT)
    event_id = submitted.json()["event_id"]
    response = client.get(f"/api/v1/events/{event_id}")
    assert response.status_code == 200
    assert response.json()["event"]["source"] == "security_command_center"


def test_unknown_event_returns_404(client):
    response = client.get("/api/v1/events/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_invalid_event_is_rejected(client):
    invalid = {**VALID_EVENT, "severity": "urgent"}
    response = client.post("/api/v1/events", json=invalid)
    assert response.status_code == 422


def test_naive_timestamp_is_rejected(client):
    invalid = {**VALID_EVENT, "observed_at": "2026-11-17T10:00:00"}
    response = client.post("/api/v1/events", json=invalid)
    assert response.status_code == 422


def test_unknown_fields_are_rejected(client):
    invalid = {**VALID_EVENT, "unexpected": "not-allowed"}
    response = client.post("/api/v1/events", json=invalid)
    assert response.status_code == 422
