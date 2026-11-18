"""Health endpoint tests."""


def test_root_returns_service_metadata(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["name"] == "AI Security Analysis Platform"


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness(client):
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_openapi_is_available(client):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert "/api/v1/events" in response.json()["paths"]
