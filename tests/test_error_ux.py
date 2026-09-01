from __future__ import annotations
import sqlite3

from app.logic.repositories import ProgramRepository, SettingsRepository, WorkoutRepository
from app.logic.schema import create_schema
from app.logic.services import WorkoutService
from app.logic.session_state import SessionState


class _FlakyConnection(sqlite3.Connection):
    """Fails the Nth execute() whose SQL contains fail_on_sql_containing, to
    simulate a write erroring partway through a multi-statement operation
    (e.g. save_workout's per-set insert loop) without depending on a brittle
    global call-count offset."""

    fail_on_sql_containing: str = ""
    fail_after_matches: int = 1
    _match_count = 0

    def execute(self, sql, *args, **kwargs):
        if self.fail_on_sql_containing and self.fail_on_sql_containing in sql:
            self._match_count += 1
            if self._match_count == self.fail_after_matches:
                raise sqlite3.OperationalError("simulated failure mid-write")
        return super().execute(sql, *args, **kwargs)


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


def test_failed_write_rolls_back_and_is_not_swept_in_by_a_later_commit():
    """A write that fails partway through a multi-statement operation must
    not leave orphaned uncommitted rows that a later, unrelated successful
    write silently commits alongside itself."""
    conn = sqlite3.connect(":memory:", factory=_FlakyConnection)
    conn.row_factory = sqlite3.Row
    create_schema(conn)

    program_repo = ProgramRepository(conn)
    workout_repo = WorkoutRepository(conn)
    settings_repo = SettingsRepository(conn)
    service = WorkoutService(program_repo, workout_repo, settings_repo, SessionState())

    service.create_new_program("Program", "double")
    service.add_exercise_to_active_program("Bench Press")
    active = service.get_active_program()
    exercise = active.exercises[0]

    # Fail on the deepest insert in save_workout's loop (the set row) — by
    # then, workout_sessions and session_exercises rows are already staged
    # uncommitted, proving rollback discards the whole partial write, not
    # just the last statement.
    conn.fail_on_sql_containing = "INSERT INTO sets"

    saved_exercises_data = [
        {
            "exercise": {"id": exercise.id, "name": exercise.name, "programId": active.id},
            "newSets": [{"id": 1, "type": "normal", "weight": 40, "reps": 8}],
        }
    ]
    service.save_workout(saved_exercises_data)  # fails, degrades gracefully

    conn.fail_on_sql_containing = ""  # stop injecting failures
    assert workout_repo.list_workout_history() == []  # nothing orphaned mid-commit

    # An unrelated successful write afterward must not sweep in any
    # leftover partial state from the failed attempt.
    service.add_exercise_to_active_program("Squat")
    assert workout_repo.list_workout_history() == []

    conn.close()
