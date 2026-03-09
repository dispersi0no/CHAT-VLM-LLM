"""Centralized logging configuration."""

from __future__ import annotations

import logging
import sys


def setup_logging(level: str = "INFO") -> None:
    """Configure root logger with consistent format."""
    log_level = getattr(logging, level.upper(), logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(log_level)

    # Avoid duplicate handlers
    if not root.handlers:
        root.addHandler(handler)

    # Quiet noisy third-party loggers
    for noisy in ("urllib3", "docker", "httpx", "httpcore"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
