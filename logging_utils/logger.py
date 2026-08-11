"""
Logging & Error Handling Module (Module 8, partial)

Cross-cutting logging setup used by every other module. Only the
console+file handler setup needed by Module 1 exists so far; structured
error taxonomy and secret-scrubbing helpers will be expanded when Module 8
gets its own full implementation pass.

The app must keep working even if file logging itself fails - if the log
directory or file can't be created, logging falls back to console-only
instead of crashing.
"""

import logging
import logging.handlers
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_FILE = LOG_DIR / "app.log"
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(LOG_FORMAT)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            LOG_FILE, maxBytes=1_000_000, backupCount=3
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except OSError as exc:
        logger.warning(
            "File logging unavailable, continuing with console logging only: %s",
            exc,
        )

    return logger
