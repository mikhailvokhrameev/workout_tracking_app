from __future__ import annotations
import json
import os
import sqlite3
from typing import Any, Dict


def migration_complete(conn: sqlite3.Connection) -> bool:
    row = conn.execute("SELECT value FROM app_meta WHERE key = 'migration_complete'").fetchone()
    return row is not None and row["value"] == "1"


def migrate_json_to_db(conn: sqlite3.Connection, json_path: str) -> None:
    """Import legacy app_data.json into the SQLite schema, once, atomically.

    Safe to call on every startup: no-ops if migration already completed, and
    no-ops if there is no legacy JSON file to migrate from (fresh install).
    Uses defensive .get(key, default) access throughout, matching the
    tolerance the original dict-based code already had for partially-populated
    records (e.g. an exercise with no nextTarget yet).
    """
    if migration_complete(conn):
        return
    if not os.path.exists(json_path):
        conn.execute(
            "INSERT OR REPLACE INTO app_meta (key, value) VALUES ('migration_complete', '1')"
        )
        conn.commit()
        return

    with open(json_path, "r", encoding="utf-8") as f:
        data: Dict[str, Any] = json.load(f)

    try:
        conn.execute("BEGIN")
        for program in data.get("programs", []):
            conn.execute(
                "INSERT INTO programs (id, name, progression_type) VALUES (?, ?, ?)",
                (program.get("id"), program.get("name", ""), program.get("progressionType", "double")),
            )
            for exercise in program.get("exercises", []):
                next_target = exercise.get("nextTarget") or {}
                conn.execute(
                    """INSERT INTO exercises
                       (id, program_id, name, next_target_weight, next_target_sets,
                        next_target_reps, next_target_text)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        exercise.get("id"),
                        program.get("id"),
                        exercise.get("name", ""),
                        next_target.get("weight"),
                        next_target.get("sets"),
                        next_target.get("reps"),
                        next_target.get("text"),
                    ),
                )

        for session in data.get("workoutHistory", []):
            conn.execute(
                "INSERT INTO workout_sessions (id, program_id, program_name, date) VALUES (?, ?, ?, ?)",
                (
                    session.get("id"),
                    session.get("programId"),
                    session.get("programName", ""),
                    session.get("date", ""),
                ),
            )
            for exercise_entry in session.get("exercises", []):
                cursor = conn.execute(
                    "INSERT INTO session_exercises (session_id, exercise_id, exercise_name) VALUES (?, ?, ?)",
                    (session.get("id"), exercise_entry.get("exerciseId"), exercise_entry.get("exerciseName", "")),
                )
                session_exercise_row_id = cursor.lastrowid
                for order, set_entry in enumerate(exercise_entry.get("sets", [])):
                    conn.execute(
                        """INSERT INTO sets (session_exercise_id, set_order, set_id, type, weight, reps)
                           VALUES (?, ?, ?, ?, ?, ?)""",
                        (
                            session_exercise_row_id,
                            order,
                            set_entry.get("id"),
                            set_entry.get("type"),
                            set_entry.get("weight"),
                            set_entry.get("reps"),
                        ),
                    )

        conn.execute(
            "INSERT OR REPLACE INTO app_meta (key, value) VALUES ('userSetupComplete', ?)",
            ("1" if data.get("userSetupComplete") else "0",),
        )
        active_program_id = data.get("activeProgramId")
        conn.execute(
            "INSERT OR REPLACE INTO app_meta (key, value) VALUES ('activeProgramId', ?)",
            (str(active_program_id) if active_program_id is not None else None,),
        )
        conn.execute(
            "INSERT OR REPLACE INTO app_meta (key, value) VALUES ('migration_complete', '1')"
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise

    os.rename(json_path, json_path + ".bak")
