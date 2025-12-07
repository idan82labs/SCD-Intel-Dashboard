"""Logging utilities."""

import logging
import sys
from typing import Optional

from app.config import settings


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a configured logger.

    Args:
        name: Logger name (defaults to root)

    Returns:
        Configured logger
    """
    logger = logging.getLogger(name or "ci_research")

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        )
        logger.addHandler(handler)

    logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)

    return logger
