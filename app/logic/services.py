from __future__ import annotations
import time
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from app.logic.dataclasses import Exercise, NextTarget, Program, SessionExercise, SetEntry, WorkoutSession
from app.logic.errors import StorageWriteError, storage_errors
from app.logic.progression import calculate_next_target, check_goal_achievement, calculate_one_rep_max
from app.logic.repositories import ProgramRepository, SettingsRepository, WorkoutRepository
from app.logic.session_state import SessionState


def _next_target_to_dict(nt: Optional[NextTarget]) -> Optional[Dict[str, Any]]:
    if nt is None:
        return None
    return {"weight": nt.weight, "sets": nt.sets, "reps": nt.reps, "text": nt.text}


def _dict_to_next_target(d: Optional[Dict[str, Any]]) -> Optional[NextTarget]:
    if d is None:
        return None
    return NextTarget(weight=d.get("weight"), sets=d.get("sets", 3), reps=d.get("reps", 8), text=d.get("text", ""))


def exercise_to_dict(ex: Exercise) -> Dict[str, Any]:
    return {"id": ex.id, "name": ex.name, "nextTarget": _next_target_to_dict(ex.next_target)}


def program_to_dict(program: Program) -> Dict[str, Any]:
    return {
        "id": program.id,
        "name": program.name,
        "progressionType": program.progression_type,
        "exercises": [exercise_to_dict(ex) for ex in program.exercises],
    }


def _set_entry_to_dict(s: SetEntry) -> Dict[str, Any]:
    return {"id": s.id, "type": s.type, "weight": s.weight, "reps": s.reps}


def session_exercise_to_dict(se: SessionExercise) -> Dict[str, Any]:
    return {
        "exerciseId": se.exercise_id,
        "exerciseName": se.exercise_name,
        "sets": [_set_entry_to_dict(s) for s in se.sets],
    }


def workout_session_to_dict(session: WorkoutSession) -> Dict[str, Any]:
    return {
        "id": session.id,
        "programId": session.program_id,
        "programName": session.program_name,
        "date": session.date,
        "exercises": [session_exercise_to_dict(se) for se in session.exercises],
    }


class WorkoutService:
    def __init__(
        self,
        program_repo: ProgramRepository,
        workout_repo: WorkoutRepository,
        settings_repo: SettingsRepository,
        session: SessionState,
        on_error: Optional[Callable[[str], None]] = None,
    ) -> None:
        self.program_repo = program_repo
        self.workout_repo = workout_repo
        self.settings_repo = settings_repo
        self.session = session
        self.on_error = on_error or (lambda message: None)
        # All three repositories share one connection (see repositories.py) —
        # kept here directly so storage_errors can roll it back on failure.
        self.conn = program_repo.conn

    def _handle_write_error(self, exc: StorageWriteError) -> None:
        self.on_error(str(exc))

    # active program helpers

    def get_active_program(self) -> Optional[Program]:
        active_id = self.settings_repo.get_active_program_id()
        if not active_id:
            return None
        return self.program_repo.get_program_by_id(active_id)

    def get_active_program_dict(self) -> Optional[Dict[str, Any]]:
        program = self.get_active_program()
        return program_to_dict(program) if program else None

    def get_program_by_id_dict(self, program_id: int) -> Optional[Dict[str, Any]]:
        program = self.program_repo.get_program_by_id(program_id)
        return program_to_dict(program) if program else None

    def find_exercise_by_id_dict(self, exercise_id: int) -> Optional[Dict[str, Any]]:
        exercise = self.program_repo.get_exercise_by_id(exercise_id)
        if not exercise:
            return None
        return {**exercise_to_dict(exercise), "programId": exercise.program_id}

    def get_last_workout_for_exercise_dict(self, exercise_id: int) -> Optional[Dict[str, Any]]:
        se = self.workout_repo.get_last_workout_for_exercise(exercise_id)
        return session_exercise_to_dict(se) if se else None

    def list_programs_dicts(self) -> List[Dict[str, Any]]:
        return [program_to_dict(p) for p in self.program_repo.list_programs()]

    def list_workout_history_dicts(self) -> List[Dict[str, Any]]:
        return [workout_session_to_dict(s) for s in self.workout_repo.list_workout_history()]

    # CRUD

    def create_new_program(self, name: str, progression_type: str) -> None:
        if len(name) > 30:
            return
        program_id = int(time.time() * 1000)
        try:
            with storage_errors("create_new_program", self.conn, name=name):
                self.program_repo.create_program(program_id, name, progression_type)
                self.settings_repo.set_active_program_id(program_id)
        except StorageWriteError as exc:
            self._handle_write_error(exc)
            return
        self.session.init_for_program(self.get_active_program_dict())

    def delete_program(self, program_id: int) -> bool:
        programs = self.program_repo.list_programs()
        if len(programs) <= 1:
            return False
        try:
            with storage_errors("delete_program", self.conn, program_id=program_id):
                self.program_repo.delete_program(program_id)
                if self.settings_repo.get_active_program_id() == program_id:
                    remaining = self.program_repo.list_programs()
                    self.settings_repo.set_active_program_id(remaining[0].id if remaining else None)
        except StorageWriteError as exc:
            self._handle_write_error(exc)
            return False
        self.session.init_for_program(self.get_active_program_dict())
        return True

    def select_program(self, program_id: int) -> None:
        try:
            with storage_errors("select_program", self.conn, program_id=program_id):
                self.settings_repo.set_active_program_id(program_id)
        except StorageWriteError as exc:
            self._handle_write_error(exc)
            return
        self.session.init_for_program(self.get_active_program_dict())

    def add_exercise_to_active_program(self, name: str) -> None:
        active_program = self.get_active_program()
        if not active_program:
            return
        exercise_id = int(time.time() * 1000)
        try:
            with storage_errors("add_exercise_to_active_program", self.conn, name=name):
                self.program_repo.add_exercise(active_program.id, exercise_id, name)
        except StorageWriteError as exc:
            self._handle_write_error(exc)
            return
        if exercise_id not in self.session.current_workout_state:
            self.session.current_workout_state[exercise_id] = []

    def delete_exercise_from_active(self, exercise_id: int) -> None:
        active_program = self.get_active_program()
        if not active_program:
            return
        try:
            with storage_errors("delete_exercise_from_active", self.conn, exercise_id=exercise_id):
                self.program_repo.delete_exercise(exercise_id)
        except StorageWriteError as exc:
            self._handle_write_error(exc)
            return
        if exercise_id in self.session.current_workout_state:
            del self.session.current_workout_state[exercise_id]

    def init_current_workout(self) -> None:
        self.session.init_for_program(self.get_active_program_dict())

    def add_set_to_workout(self, exercise_id: int) -> None:
        self.session.add_set(exercise_id)

    def delete_set_from_workout(self, exercise_id: int, set_id: int) -> None:
        self.session.delete_set(exercise_id, set_id)

    def update_set_in_workout(self, exercise_id: int, set_id: int, prop: str, value: str) -> None:
        self.session.update_set(exercise_id, set_id, prop, value)

    def update_set_error_state(self, exercise_id: int, set_id: int, prop: str, has_error: bool) -> None:
        self.session.update_set_error(exercise_id, set_id, prop, has_error)

    def has_validation_errors(self) -> bool:
        return self.session.has_validation_errors()

    # save and summarize workouts

    def save_workout(self, saved_exercises_data: List[Dict[str, Any]]) -> None:
        active_program = self.get_active_program()
        if not active_program:
            return

        exercises_by_id = {ex.id: ex for ex in active_program.exercises}
        target_updates: Dict[int, Optional[NextTarget]] = {}

        # Pass 1: update progression targets — only for items with working sets.
        # (Matches original behavior: target computation is gated on working sets,
        # but history persistence below is NOT — every item is saved regardless.)
        for item in saved_exercises_data:
            exercise_data = item["exercise"]
            new_sets = item["newSets"]
            new_working_sets = [s for s in new_sets if s.get("type") == "normal"]
            if not new_working_sets:
                continue

            program_exercise = exercises_by_id.get(exercise_data.get("id"))
            if not program_exercise:
                continue

            progression_type = active_program.progression_type
            has_target = program_exercise.next_target is not None

            new_target_dict = None
            if not has_target:
                new_target_dict = calculate_next_target(
                    exercise_to_dict(program_exercise), {"sets": new_working_sets}, progression_type
                )
            elif check_goal_achievement(exercise_to_dict(program_exercise), new_working_sets, progression_type):
                new_target_dict = calculate_next_target(
                    exercise_to_dict(program_exercise), {"sets": new_working_sets}, progression_type
                )
            if new_target_dict is not None:
                target_updates[program_exercise.id] = _dict_to_next_target(new_target_dict)

        # Pass 2: persist history — every item, unconditionally (matches original).
        session_exercises: List[SessionExercise] = [
            SessionExercise(
                exercise_id=item["exercise"]["id"],
                exercise_name=item["exercise"]["name"],
                sets=[
                    SetEntry(id=s.get("id"), type=s.get("type"), weight=s.get("weight"), reps=s.get("reps"))
                    for s in item["newSets"]
                ],
            )
            for item in saved_exercises_data
        ]

        workout_session = WorkoutSession(
            id=int(time.time() * 1000),
            program_id=active_program.id,
            program_name=active_program.name,
            date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            exercises=session_exercises,
        )

        try:
            with storage_errors("save_workout", self.conn, program_id=active_program.id):
                for exercise_id, next_target in target_updates.items():
                    self.program_repo.update_next_target(exercise_id, next_target)
                self.workout_repo.save_workout(workout_session)
        except StorageWriteError as exc:
            self._handle_write_error(exc)
            return

        self.init_current_workout()

    def generate_workout_summary(self, saved_exercises_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        all_goals_achieved = True
        summary_details: List[Dict[str, Any]] = []

        for item in saved_exercises_data:
            exercise_data = item["exercise"]
            new_sets = item["newSets"]
            new_working_sets = [s for s in new_sets if s.get("type") == "normal"]
            if not new_working_sets:
                continue

            active_program = self.program_repo.get_program_by_id(exercise_data["programId"])
            if not active_program:
                continue

            program_exercise = next((ex for ex in active_program.exercises if ex.id == exercise_data.get("id")), None)
            if not program_exercise:
                continue

            progression_type = active_program.progression_type
            has_target = program_exercise.next_target is not None
            exercise_dict = exercise_to_dict(program_exercise)

            detail = {"exercise_name": program_exercise.name}
            if not has_target:
                detail["status"] = "success"
                detail["message"] = "Отличное начало! "
                potential = calculate_next_target(exercise_dict, {"sets": new_working_sets}, progression_type)
                detail["next_target_text"] = (
                    f"Цель на следующую тренировку: {potential['text']}"
                    f"{f' с весом {potential['weight']} кг' if 'weight' in potential else ''}"
                )
            else:
                is_goal = check_goal_achievement(exercise_dict, new_working_sets, progression_type)
                if is_goal:
                    detail["status"] = "success"
                    detail["message"] = "Цель достигнута! "
                    potential = calculate_next_target(exercise_dict, {"sets": new_working_sets}, progression_type)
                    detail["next_target_text"] = (
                        f"Следующая цель: {potential['text']}"
                        f"{f' с весом {potential['weight']} кг' if 'weight' in potential else ''}"
                    )
                else:
                    all_goals_achieved = False
                    detail["status"] = "failure"
                    detail["message"] = "Цель не достигнута. "
                    nt = exercise_dict["nextTarget"]
                    detail["next_target_text"] = (
                        f"Повторите: {nt['text']}"
                        f"{f' с весом {nt['weight']} кг' if 'weight' in nt else ''}"
                    )

            summary_details.append(detail)

        return {"all_goals_achieved": all_goals_achieved, "details": summary_details}

    def delete_history_session(self, session_id: int) -> None:
        try:
            with storage_errors("delete_history_session", self.conn, session_id=session_id):
                self.workout_repo.delete_history_session(session_id)

                active_program = self.get_active_program()
                if active_program:
                    progression_type = active_program.progression_type
                    for prog_ex in active_program.exercises:
                        last_workout_se = self.workout_repo.get_last_workout_for_exercise(prog_ex.id)
                        last_workout_dict = None
                        if last_workout_se:
                            working_sets = [
                                _set_entry_to_dict(s) for s in last_workout_se.sets if s.type == "normal"
                            ]
                            last_workout_dict = {"sets": working_sets}

                        new_target_dict = calculate_next_target(
                            exercise_to_dict(Exercise(prog_ex.id, prog_ex.program_id, prog_ex.name, None)),
                            last_workout_dict,
                            progression_type,
                        )
                        self.program_repo.update_next_target(prog_ex.id, _dict_to_next_target(new_target_dict))
        except StorageWriteError as exc:
            self._handle_write_error(exc)

    def get_progress_chart_data(self, exercise_id: int) -> Optional[Dict[str, List]]:
        rows = self.workout_repo.get_progress_chart_data(exercise_id)
        if not rows:
            return None

        labels = [date for date, _ in rows]
        data = [
            calculate_one_rep_max([_set_entry_to_dict(s) for s in sets if s.type == "normal"])
            for _, sets in rows
        ]
        return {"labels": labels, "data": data}

    def reset_all_data(self) -> None:
        try:
            with storage_errors("reset_all_data", self.conn):
                self.settings_repo.reset_all()
        except StorageWriteError as exc:
            self._handle_write_error(exc)
            return
        self.session.reset()
