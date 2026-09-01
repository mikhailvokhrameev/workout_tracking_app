from __future__ import annotations
import sqlite3
from typing import List, Optional

from app.logic.dataclasses import (
    Exercise,
    NextTarget,
    Program,
    SessionExercise,
    SetEntry,
    WorkoutSession,
    row_to_exercise,
    row_to_program,
    row_to_set_entry,
)


class ProgramRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def _exercises_for_program(self, program_id: int) -> List[Exercise]:
        rows = self.conn.execute(
            "SELECT * FROM exercises WHERE program_id = ? ORDER BY id", (program_id,)
        ).fetchall()
        return [row_to_exercise(r) for r in rows]

    def list_programs(self) -> List[Program]:
        rows = self.conn.execute("SELECT * FROM programs ORDER BY id").fetchall()
        return [row_to_program(r, self._exercises_for_program(r["id"])) for r in rows]

    def get_program_by_id(self, program_id: int) -> Optional[Program]:
        row = self.conn.execute("SELECT * FROM programs WHERE id = ?", (program_id,)).fetchone()
        if not row:
            return None
        return row_to_program(row, self._exercises_for_program(row["id"]))

    def create_program(self, program_id: int, name: str, progression_type: str) -> Program:
        self.conn.execute(
            "INSERT INTO programs (id, name, progression_type) VALUES (?, ?, ?)",
            (program_id, name, progression_type),
        )
        self.conn.commit()
        return Program(id=program_id, name=name, progression_type=progression_type, exercises=[])

    def delete_program(self, program_id: int) -> None:
        exercise_ids = [
            r["id"]
            for r in self.conn.execute(
                "SELECT id FROM exercises WHERE program_id = ?", (program_id,)
            ).fetchall()
        ]
        for exercise_id in exercise_ids:
            self.delete_exercise(exercise_id, commit=False)
        self.conn.execute("DELETE FROM programs WHERE id = ?", (program_id,))
        self.conn.commit()

    def add_exercise(self, program_id: int, exercise_id: int, name: str) -> Exercise:
        self.conn.execute(
            "INSERT INTO exercises (id, program_id, name) VALUES (?, ?, ?)",
            (exercise_id, program_id, name),
        )
        self.conn.commit()
        return Exercise(id=exercise_id, program_id=program_id, name=name, next_target=None)

    def delete_exercise(self, exercise_id: int, commit: bool = True) -> None:
        self.conn.execute("DELETE FROM exercises WHERE id = ?", (exercise_id,))
        if commit:
            self.conn.commit()

    def get_exercise_by_id(self, exercise_id: int) -> Optional[Exercise]:
        row = self.conn.execute("SELECT * FROM exercises WHERE id = ?", (exercise_id,)).fetchone()
        return row_to_exercise(row) if row else None

    def update_next_target(self, exercise_id: int, next_target: Optional[NextTarget]) -> None:
        if next_target is None:
            self.conn.execute(
                """UPDATE exercises SET next_target_weight = NULL, next_target_sets = NULL,
                   next_target_reps = NULL, next_target_text = NULL WHERE id = ?""",
                (exercise_id,),
            )
        else:
            self.conn.execute(
                """UPDATE exercises SET next_target_weight = ?, next_target_sets = ?,
                   next_target_reps = ?, next_target_text = ? WHERE id = ?""",
                (next_target.weight, next_target.sets, next_target.reps, next_target.text, exercise_id),
            )
        self.conn.commit()


class WorkoutRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def _session_exercises_for_session(self, session_id: int) -> List[SessionExercise]:
        se_rows = self.conn.execute(
            "SELECT * FROM session_exercises WHERE session_id = ? ORDER BY id", (session_id,)
        ).fetchall()
        result = []
        for se_row in se_rows:
            set_rows = self.conn.execute(
                "SELECT * FROM sets WHERE session_exercise_id = ? ORDER BY set_order",
                (se_row["id"],),
            ).fetchall()
            result.append(
                SessionExercise(
                    exercise_id=se_row["exercise_id"],
                    exercise_name=se_row["exercise_name"],
                    sets=[row_to_set_entry(r) for r in set_rows],
                )
            )
        return result

    def list_workout_history(self) -> List[WorkoutSession]:
        rows = self.conn.execute("SELECT * FROM workout_sessions ORDER BY id").fetchall()
        return [
            WorkoutSession(
                id=r["id"],
                program_id=r["program_id"],
                program_name=r["program_name"],
                date=r["date"],
                exercises=self._session_exercises_for_session(r["id"]),
            )
            for r in rows
        ]

    def save_workout(self, session: WorkoutSession) -> None:
        self.conn.execute(
            "INSERT INTO workout_sessions (id, program_id, program_name, date) VALUES (?, ?, ?, ?)",
            (session.id, session.program_id, session.program_name, session.date),
        )
        for session_exercise in session.exercises:
            cursor = self.conn.execute(
                "INSERT INTO session_exercises (session_id, exercise_id, exercise_name) VALUES (?, ?, ?)",
                (session.id, session_exercise.exercise_id, session_exercise.exercise_name),
            )
            session_exercise_row_id = cursor.lastrowid
            for order, set_entry in enumerate(session_exercise.sets):
                self.conn.execute(
                    """INSERT INTO sets (session_exercise_id, set_order, set_id, type, weight, reps)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (session_exercise_row_id, order, set_entry.id, set_entry.type, set_entry.weight, set_entry.reps),
                )
        self.conn.commit()

    def delete_history_session(self, session_id: int) -> None:
        se_ids = [
            r["id"]
            for r in self.conn.execute(
                "SELECT id FROM session_exercises WHERE session_id = ?", (session_id,)
            ).fetchall()
        ]
        for se_id in se_ids:
            self.conn.execute("DELETE FROM sets WHERE session_exercise_id = ?", (se_id,))
        self.conn.execute("DELETE FROM session_exercises WHERE session_id = ?", (session_id,))
        self.conn.execute("DELETE FROM workout_sessions WHERE id = ?", (session_id,))
        self.conn.commit()

    def get_last_workout_for_exercise(self, exercise_id: int) -> Optional[SessionExercise]:
        row = self.conn.execute(
            """SELECT se.id FROM session_exercises se
               JOIN workout_sessions s ON se.session_id = s.id
               WHERE se.exercise_id = ?
               ORDER BY s.id DESC LIMIT 1""",
            (exercise_id,),
        ).fetchone()
        if not row:
            return None
        se_row = self.conn.execute(
            "SELECT * FROM session_exercises WHERE id = ?", (row["id"],)
        ).fetchone()
        set_rows = self.conn.execute(
            "SELECT * FROM sets WHERE session_exercise_id = ? ORDER BY set_order", (row["id"],)
        ).fetchall()
        return SessionExercise(
            exercise_id=se_row["exercise_id"],
            exercise_name=se_row["exercise_name"],
            sets=[row_to_set_entry(r) for r in set_rows],
        )

    def get_progress_chart_data(self, exercise_id: int) -> List[tuple]:
        """Returns [(date, [SetEntry, ...]), ...] ordered by date, one entry per session."""
        rows = self.conn.execute(
            """SELECT s.date AS date, se.id AS se_id
               FROM session_exercises se
               JOIN workout_sessions s ON se.session_id = s.id
               WHERE se.exercise_id = ?
               ORDER BY s.date""",
            (exercise_id,),
        ).fetchall()
        result = []
        for row in rows:
            set_rows = self.conn.execute(
                "SELECT * FROM sets WHERE session_exercise_id = ? ORDER BY set_order", (row["se_id"],)
            ).fetchall()
            result.append((row["date"], [row_to_set_entry(r) for r in set_rows]))
        return result


class SettingsRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def _get(self, key: str) -> Optional[str]:
        row = self.conn.execute("SELECT value FROM app_meta WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else None

    def _set(self, key: str, value: Optional[str]) -> None:
        self.conn.execute(
            "INSERT INTO app_meta (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )
        self.conn.commit()

    def get_active_program_id(self) -> Optional[int]:
        value = self._get("activeProgramId")
        return int(value) if value is not None else None

    def set_active_program_id(self, program_id: Optional[int]) -> None:
        self._set("activeProgramId", str(program_id) if program_id is not None else None)

    def get_user_setup_complete(self) -> bool:
        return self._get("userSetupComplete") == "1"

    def set_user_setup_complete(self, value: bool) -> None:
        self._set("userSetupComplete", "1" if value else "0")

    def reset_all(self) -> None:
        self.conn.execute("DELETE FROM sets")
        self.conn.execute("DELETE FROM session_exercises")
        self.conn.execute("DELETE FROM workout_sessions")
        self.conn.execute("DELETE FROM exercises")
        self.conn.execute("DELETE FROM programs")
        self.conn.execute(
            "UPDATE app_meta SET value = NULL WHERE key = 'activeProgramId'"
        )
        self.conn.execute(
            "UPDATE app_meta SET value = '0' WHERE key = 'userSetupComplete'"
        )
        self.conn.commit()
