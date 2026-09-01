from __future__ import annotations
import json
import os
import sqlite3

import pytest

from app.logic.migration import migrate_json_to_db, migration_complete
from app.logic.schema import create_schema

SAMPLE_DATA = {
    "programs": [
        {
            "id": 1,
            "name": "PPL",
            "progressionType": "double",
            "exercises": [
                {"id": 100, "name": "Bench Press", "history": [], "nextTarget": {"weight": 42.5, "sets": 3, "reps": 8, "text": "3x8"}},
            ],
        }
    ],
    "workoutHistory": [
        {
            "id": 1000,
            "date": "2026-08-01 10:00:00",
            "programId": 1,
            "programName": "PPL",
            "exercises": [
                {"exerciseId": 100, "exerciseName": "Bench Press", "sets": [{"id": 1, "type": "normal", "weight": 40, "reps": 8}]},
            ],
        }
    ],
    "userSetupComplete": True,
    "activeProgramId": 1,
}


@pytest.fixture
def db_conn():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_schema(connection)
    yield connection
    connection.close()


def _write_json(tmp_path, data):
    path = tmp_path / "app_data.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return str(path)


def test_migration_happy_path(db_conn, tmp_path):
    json_path = _write_json(tmp_path, SAMPLE_DATA)

    migrate_json_to_db(db_conn, json_path)

    assert migration_complete(db_conn)
    programs = db_conn.execute("SELECT * FROM programs").fetchall()
    assert len(programs) == 1
    assert programs[0]["name"] == "PPL"

    exercises = db_conn.execute("SELECT * FROM exercises").fetchall()
    assert len(exercises) == 1
    assert exercises[0]["next_target_weight"] == 42.5

    sessions = db_conn.execute("SELECT * FROM workout_sessions").fetchall()
    assert len(sessions) == 1

    assert not os.path.exists(json_path)
    assert os.path.exists(json_path + ".bak")


def test_migration_skips_if_already_complete(db_conn, tmp_path):
    json_path = _write_json(tmp_path, SAMPLE_DATA)
    migrate_json_to_db(db_conn, json_path)
    assert not os.path.exists(json_path)

    # Second call must no-op even with a fresh json at the same path (idempotent).
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(SAMPLE_DATA, f)
    migrate_json_to_db(db_conn, json_path)

    programs = db_conn.execute("SELECT * FROM programs").fetchall()
    assert len(programs) == 1  # not duplicated


def test_migration_no_json_file_marks_complete(db_conn, tmp_path):
    json_path = str(tmp_path / "does_not_exist.json")
    migrate_json_to_db(db_conn, json_path)
    assert migration_complete(db_conn)
    assert db_conn.execute("SELECT * FROM programs").fetchall() == []


def test_migration_rejects_malformed_json_and_keeps_file(db_conn, tmp_path):
    path = tmp_path / "app_data.json"
    path.write_text("{not valid json", encoding="utf-8")

    with pytest.raises(json.JSONDecodeError):
        migrate_json_to_db(db_conn, str(path))

    assert path.exists()
    assert not migration_complete(db_conn)
    assert db_conn.execute("SELECT * FROM programs").fetchall() == []


class _FlakyConnection(sqlite3.Connection):
    """Fails the Nth execute() call to simulate a crash partway through a
    transaction — sqlite3.Connection.execute is a read-only slot, so this
    must be a real subclass rather than a monkeypatched attribute."""

    fail_on_call: int = 0
    _call_count = 0

    def execute(self, sql, *args, **kwargs):
        self._call_count += 1
        if self.fail_on_call and self._call_count == self.fail_on_call:
            raise sqlite3.OperationalError("simulated crash")
        return super().execute(sql, *args, **kwargs)


def test_migration_crash_mid_import_leaves_no_partial_state(tmp_path):
    """A crash mid-transaction must not leave partially-imported rows behind,
    and migration_complete must remain unset so the next launch retries."""
    json_path = _write_json(tmp_path, SAMPLE_DATA)

    conn = sqlite3.connect(":memory:", factory=_FlakyConnection)
    conn.row_factory = sqlite3.Row
    create_schema(conn)
    conn.fail_on_call = 4  # fail partway through (after the program insert, before the rest)

    with pytest.raises(sqlite3.OperationalError):
        migrate_json_to_db(conn, json_path)

    assert not migration_complete(conn)
    conn.fail_on_call = 0
    assert conn.execute("SELECT * FROM programs").fetchall() == []
    assert os.path.exists(json_path)  # never renamed since commit never happened

    # Retry on "next launch" succeeds cleanly.
    migrate_json_to_db(conn, json_path)
    assert migration_complete(conn)
    assert len(conn.execute("SELECT * FROM programs").fetchall()) == 1
    conn.close()


def test_migration_handles_missing_next_target(db_conn, tmp_path):
    data = {
        "programs": [
            {
                "id": 1,
                "name": "Program",
                "progressionType": "linear",
                "exercises": [{"id": 100, "name": "Squat"}],  # no nextTarget key at all
            }
        ],
        "workoutHistory": [],
        "userSetupComplete": False,
        "activeProgramId": None,
    }
    json_path = _write_json(tmp_path, data)

    migrate_json_to_db(db_conn, json_path)

    exercise = db_conn.execute("SELECT * FROM exercises WHERE id = 100").fetchone()
    assert exercise["next_target_text"] is None
    assert exercise["next_target_weight"] is None


def test_migration_handles_program_with_no_exercises(db_conn, tmp_path):
    data = {
        "programs": [{"id": 1, "name": "Empty Program", "progressionType": "linear"}],  # no exercises key
        "workoutHistory": [],
        "userSetupComplete": False,
        "activeProgramId": None,
    }
    json_path = _write_json(tmp_path, data)

    migrate_json_to_db(db_conn, json_path)

    program = db_conn.execute("SELECT * FROM programs WHERE id = 1").fetchone()
    assert program is not None
    assert db_conn.execute("SELECT * FROM exercises WHERE program_id = 1").fetchall() == []
