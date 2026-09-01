from __future__ import annotations
import logging
import sqlite3
from contextlib import contextmanager
from typing import Iterator

logger = logging.getLogger("workout_tracker.storage")


class StorageWriteError(Exception):
    """Raised when a repository write fails. Callers should show the user a
    visible message instead of silently losing the write."""


@contextmanager
def storage_errors(operation: str, **context) -> Iterator[None]:
    try:
        yield
    except sqlite3.Error as exc:
        logger.error("Storage write failed during %s (%s): %s", operation, context, exc, exc_info=True)
        raise StorageWriteError(f"Couldn't save — try again ({operation})") from exc
