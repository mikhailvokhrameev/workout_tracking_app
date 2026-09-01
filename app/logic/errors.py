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
def storage_errors(operation: str, conn: sqlite3.Connection, **context) -> Iterator[None]:
    try:
        yield
    except sqlite3.Error as exc:
        # Repository methods commit individually rather than sharing one
        # transaction boundary, so a failure partway through a multi-step
        # operation (e.g. save_workout's per-set insert loop) can leave the
        # shared connection holding an open, uncommitted transaction. Without
        # an explicit rollback here, those orphaned partial writes stay
        # pending until some later, unrelated successful commit sweeps them
        # in silently. Always roll back on failure so a failed write is
        # fully discarded, never partially persisted later by accident.
        try:
            conn.rollback()
        except sqlite3.Error:
            # The connection itself may be closed/corrupted (the same
            # failure that triggered this handler, or a follow-on one) —
            # don't let a failed rollback mask the original error with an
            # unrelated crash.
            logger.error("Rollback also failed during %s", operation, exc_info=True)
        logger.error("Storage write failed during %s (%s): %s", operation, context, exc, exc_info=True)
        raise StorageWriteError(f"Couldn't save — try again ({operation})") from exc
