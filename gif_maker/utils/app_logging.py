"""Application logging: rotating file sink, safe from worker threads.

Keeps logging plumbing out of the GUI. ``get_logger`` is idempotent so both
the entry point and the window can call it without stacking handlers.
"""

from __future__ import annotations

import logging
import logging.handlers
from pathlib import Path

LOG_DIR_NAME = ".gifmaker"
LOG_FILE_NAME = "gifmaker.log"
_LOGGER_NAME = "gifmaker"

# Keep logs small and bounded; this is a desktop app, not a server.
_MAX_BYTES = 250_000
_BACKUP_COUNT = 2


def log_dir() -> Path:
    """Directory holding rotating log files (created on first use)."""
    return Path.home() / LOG_DIR_NAME / "logs"


def get_logger() -> logging.Logger:
    """Return the shared app logger, configuring it on first call.

    Falls back to a NullHandler if the log directory cannot be created so
    logging setup can never crash the application.
    """
    logger = logging.getLogger(_LOGGER_NAME)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    logger.propagate = False
    try:
        directory = log_dir()
        directory.mkdir(parents=True, exist_ok=True)
        handler = logging.handlers.RotatingFileHandler(
            directory / LOG_FILE_NAME,
            maxBytes=_MAX_BYTES,
            backupCount=_BACKUP_COUNT,
            encoding="utf-8",
        )
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        )
        logger.addHandler(handler)
    except OSError:
        logger.addHandler(logging.NullHandler())
    return logger
