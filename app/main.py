"""FastAPI application entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import events, health
from app.core.config import get_settings
from app.core.logging import configure_logging


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Initialize application-level facilities."""

    configure_logging()
    yield


settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Reusable API foundation for normalized security event ingestion. "
        "AI analysis and cloud integrations are introduced in later phases."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)
app.include_router(health.router)
app.include_router(events.router)


@app.get("/", tags=["service"], summary="Service information")
async def root() -> dict[str, str]:
    """Return basic service metadata."""

    return {"name": settings.app_name, "version": settings.app_version}
