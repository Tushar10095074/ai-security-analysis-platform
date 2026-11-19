"""Vertex AI provider tests. A fake client is used: no network or Vertex AI calls."""

import json
from types import SimpleNamespace

import pytest

from app.api import events as events_api
from app.core.config import Settings
from app.services.ai_analysis.factory import build_ai_analysis_provider
from app.services.ai_analysis.mock_provider import MockAIAnalysisProvider
from app.services.ai_analysis.vertex_provider import (
    AIProviderError,
    AIQuotaExceededError,
    VertexAIAnalysisProvider,
)
from tests.test_ai_analysis import create_risk_assessment, submit_event

VALID_OUTPUT = {
    "summary": "A storage bucket is publicly readable.",
    "threat_explanation": "Anyone on the internet can list and read objects.",
    "potential_impact": "Possible disclosure of sensitive data.",
    "key_observations": ["Resource is internet exposed."],
    "recommended_actions": ["Remove allUsers binding."],
    "investigation_steps": ["Review access logs for anonymous reads."],
}


class FakeModels:
    def __init__(self, text: str | None = None, error: Exception | None = None) -> None:
        self.text = text
        self.error = error
        self.calls: list[dict] = []

    def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        usage = SimpleNamespace(prompt_token_count=100, candidates_token_count=50)
        return SimpleNamespace(text=self.text, usage_metadata=usage)


def make_provider(text=None, error=None, max_calls=50):
    fake = FakeModels(text=text, error=error)
    provider = VertexAIAnalysisProvider(
        project="test-project",
        location="us-east1",
        model="gemini-test",
        max_calls=max_calls,
        client=SimpleNamespace(models=fake),
    )
    return provider, fake


@pytest.fixture
def use_provider(monkeypatch):
    def _use(provider):
        monkeypatch.setattr(events_api, "ai_analysis_provider", provider)

    return _use


def test_factory_defaults_to_mock():
    assert isinstance(build_ai_analysis_provider(Settings()), MockAIAnalysisProvider)


def test_factory_vertex_requires_project():
    with pytest.raises(ValueError, match="VERTEX_PROJECT"):
        build_ai_analysis_provider(Settings(ai_provider="vertex", vertex_project=None))


def test_vertex_analysis_via_api(client, use_provider):
    provider, fake = make_provider(text=json.dumps(VALID_OUTPUT))
    use_provider(provider)
    event_id = submit_event(client)
    risk = create_risk_assessment(client, event_id)

    response = client.post(f"/api/v1/events/{event_id}/ai-analysis")

    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "vertex_ai"
    assert body["model"] == "gemini-test"
    assert body["summary"] == VALID_OUTPUT["summary"]
    assert body["recommended_actions"] == VALID_OUTPUT["recommended_actions"]
    assert any("authoritative" in item for item in body["limitations"])
    assert len(fake.calls) == 1
    config = fake.calls[0]["config"]
    assert config.response_mime_type == "application/json"
    assert config.thinking_config.thinking_budget == 0

    # Prompt wraps untrusted event data and carries the deterministic score.
    prompt = fake.calls[0]["contents"]
    assert "<security_event>" in prompt
    assert f'"risk_score": {risk["risk_score"]}' in prompt

    # Risk assessment is unchanged and the analysis is persisted.
    assert client.get(f"/api/v1/events/{event_id}/risk").json() == risk
    assert client.get(f"/api/v1/events/{event_id}/ai-analysis").json() == body


def test_vertex_invalid_output_returns_502(client, use_provider):
    provider, _ = make_provider(text="not json")
    use_provider(provider)
    event_id = submit_event(client)
    create_risk_assessment(client, event_id)

    response = client.post(f"/api/v1/events/{event_id}/ai-analysis")

    assert response.status_code == 502
    assert client.get(f"/api/v1/events/{event_id}/ai-analysis").status_code == 404


def test_vertex_call_failure_returns_502(client, use_provider):
    provider, _ = make_provider(error=TimeoutError("timed out"))
    use_provider(provider)
    event_id = submit_event(client)
    create_risk_assessment(client, event_id)

    response = client.post(f"/api/v1/events/{event_id}/ai-analysis")

    assert response.status_code == 502
    assert response.json()["detail"] == "AI analysis provider unavailable"


def test_vertex_call_budget_returns_429(client, use_provider):
    provider, fake = make_provider(text=json.dumps(VALID_OUTPUT), max_calls=1)
    use_provider(provider)
    event_id = submit_event(client)
    create_risk_assessment(client, event_id)

    assert client.post(f"/api/v1/events/{event_id}/ai-analysis").status_code == 200
    second = client.post(f"/api/v1/events/{event_id}/ai-analysis")

    assert second.status_code == 429
    assert len(fake.calls) == 1


def test_vertex_output_is_clipped():
    long_output = dict(VALID_OUTPUT, summary="x" * 5000, key_observations=["o"] * 30)
    provider, _ = make_provider(text=json.dumps(long_output))
    from app.models.risk_assessment import RiskAssessment, RiskLevel
    from app.models.security_event import SecurityEventCreate, SecurityEventRecord
    from tests.test_events import VALID_EVENT

    record = SecurityEventRecord(event=SecurityEventCreate(**VALID_EVENT))
    risk = RiskAssessment(
        event_id=record.event_id,
        risk_score=50,
        risk_level=RiskLevel.MEDIUM,
        factors=[],
        recommendations=[],
    )

    analysis = provider.analyze(record, risk)

    assert len(analysis.summary) <= 2000
    assert len(analysis.key_observations) == 10


def test_quota_error_is_provider_error():
    assert issubclass(AIQuotaExceededError, AIProviderError)
