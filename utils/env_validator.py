"""Environment variable validation at startup."""

from __future__ import annotations

import logging
import os
import sys

logger = logging.getLogger(__name__)

# Required env vars (name, description)
REQUIRED_VARS: list[tuple[str, str]] = []

# Optional env vars with defaults (name, default, description)
OPTIONAL_VARS: list[tuple[str, str, str]] = [
    (
        "CORS_ORIGINS",
        "http://localhost:8501,http://localhost:3000,http://127.0.0.1:8501",
        "Comma-separated CORS origins",
    ),
    ("RATE_LIMIT", "60", "API rate limit per minute per IP"),
    ("LOG_LEVEL", "INFO", "Logging level"),
]


def validate_environment(strict: bool = False) -> bool:
    """Validate required environment variables.

    Args:
        strict: If True, exit on missing required vars. If False, just warn.

    Returns:
        True if all required vars present.
    """
    missing = []
    for name, description in REQUIRED_VARS:
        if not os.getenv(name):
            missing.append(f"  {name} — {description}")

    if missing:
        msg = "Missing required environment variables:\n" + "\n".join(missing)
        logger.error(msg)
        if strict:
            sys.exit(1)
        return False

    # Log optional vars with defaults
    for name, default, description in OPTIONAL_VARS:
        value = os.getenv(name, default)
        if value == default:
            logger.debug("Using default %s=%s (%s)", name, default, description)
        else:
            logger.info("Environment %s configured (%s)", name, description)

    return True
