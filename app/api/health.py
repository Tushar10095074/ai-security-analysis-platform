"""Health and readiness endpoints."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health", summary="Liveness check")
async def health() -> dict[str, str]:
    """Indicate that the process is alive; no external dependency checks."""

    return {"status": "ok"}


@router.get("/ready", summary="Readiness check")
async def readiness() -> dict[str, str]:
    """Indicate that the API is ready to accept requests."""

    # Add dependency checks here when persistence and messaging are introduced.
    return {"status": "ready"}
