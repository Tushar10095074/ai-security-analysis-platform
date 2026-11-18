"""Structured, secret-conscious logging configuration."""

import logging

from app.core.config import get_settings


def configure_logging() -> None:
    """Configure standard-library logging for local and container execution."""

    settings = get_settings()
    logging.basicConfig(
        level=settings.log_level.upper(),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
