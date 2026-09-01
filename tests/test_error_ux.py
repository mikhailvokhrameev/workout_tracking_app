from __future__ import annotations
import sqlite3

from app.logic.repositories import ProgramRepository, SettingsRepository, WorkoutRepository
from app.logic.services import WorkoutService
from app.logic.session_state import SessionState


def test_write_failure_calls_on_error_with_visible_message(conn):
    program_repo = ProgramRepository(conn)
    workout_repo = WorkoutRepository(conn)
    settings_repo = SettingsRepository(conn)

    errors_shown = []
    service = WorkoutService(
        program_repo, workout_repo, settings_repo, SessionState(), on_error=errors_shown.append
    )

    # Close the underlying connection to force every subsequent write to fail,
    # simulating a real disk/permission failure without needing real disk I/O.
    conn.close()

    service.create_new_program("Program", "linear")

    assert len(errors_shown) == 1
    assert errors_shown[0]  # non-empty, user-visible message
    assert "create_new_program" in errors_shown[0]


def test_write_failure_does_not_raise_to_caller(conn):
    """The facade must degrade gracefully, not crash the app — screens have no
    try/except around these calls today."""
    program_repo = ProgramRepository(conn)
    workout_repo = WorkoutRepository(conn)
    settings_repo = SettingsRepository(conn)
    service = WorkoutService(program_repo, workout_repo, settings_repo, SessionState())

    conn.close()

    # Must not raise, even with no on_error callback provided.
    service.create_new_program("Program", "linear")


def test_write_failure_is_logged(conn, caplog):
    import logging

    program_repo = ProgramRepository(conn)
    workout_repo = WorkoutRepository(conn)
    settings_repo = SettingsRepository(conn)
    service = WorkoutService(program_repo, workout_repo, settings_repo, SessionState())

    conn.close()

    with caplog.at_level(logging.ERROR, logger="workout_tracker.storage"):
        service.create_new_program("Program", "linear")

    assert any("create_new_program" in record.message for record in caplog.records)
