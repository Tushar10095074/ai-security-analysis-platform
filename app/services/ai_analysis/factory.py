"""Select the AI analysis provider from configuration."""

from app.core.config import Settings
from app.services.ai_analysis.base import AIAnalysisProvider
from app.services.ai_analysis.mock_provider import MockAIAnalysisProvider


def build_ai_analysis_provider(settings: Settings) -> AIAnalysisProvider:
    """Return the configured provider. Defaults to the local mock (no external calls)."""

    if settings.ai_provider == "vertex":
        if not settings.vertex_project:
            raise ValueError("VERTEX_PROJECT must be set when AI_PROVIDER=vertex")

        from app.services.ai_analysis.vertex_provider import VertexAIAnalysisProvider

        return VertexAIAnalysisProvider(
            project=settings.vertex_project,
            location=settings.vertex_location,
            model=settings.vertex_model,
            timeout_seconds=settings.vertex_timeout_seconds,
            max_output_tokens=settings.vertex_max_output_tokens,
            thinking_budget=settings.vertex_thinking_budget,
            max_calls=settings.vertex_max_calls_per_instance,
        )

    return MockAIAnalysisProvider()
