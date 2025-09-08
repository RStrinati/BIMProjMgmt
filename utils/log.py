"""Application-wide logging configuration.

Usage:
- Call `setup_logging()` once from your entry point.
- In modules, use `logger = logging.getLogger(__name__)`.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

_CONFIGURED = False


def _level_from_env(default: str = "INFO") -> int:
    level_name = os.getenv("LOG_LEVEL", default).upper()
    return getattr(logging, level_name, logging.INFO)


def setup_logging(level: Optional[int] = None) -> None:
    """Configure root logging once with a sensible format.

    The log level can be controlled via the LOG_LEVEL env var (DEBUG, INFO, WARNING...).
    """
    global _CONFIGURED
    if _CONFIGURED:
        return

    resolved_level = level if level is not None else _level_from_env()
    logging.basicConfig(
        level=resolved_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Reduce verbosity of noisy third-party libs if needed
    logging.getLogger("pyodbc").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)

    _CONFIGURED = True

