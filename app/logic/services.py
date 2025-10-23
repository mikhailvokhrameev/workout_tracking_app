from __future__ import annotations
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from app.logic.models import get_active_program, get_program_by_id
from app.logic.progression import calculate_next_target, check_goal_achievement, calculate_one_rep_max
from app.logic.session_state import SessionState
from app.logic.storage import AppStorage


class WorkoutService:
    def __init__(self, storage: AppStorage, session: SessionState) -> None:
        self.storage = storage
        self.session = session


    def create_new_program(self, name: str, progression_type: str) -> None:
        app_data = self.storage.get()
        new_program = {
            "id": int(time.time() * 1000),
            "name": name,
            "progressionType": progression_type,
            "exercises": [],
        }
        if len(name) <= 30:
            app_data["programs"].append(new_program)
            app_data["activeProgramId"] = new_program["id"]
            self.storage.save()
            self.session.init_for_program(new_program)

    def delete_program(self, program_id: int) -> bool:
        app_data = self.storage.get()
        if len(app_data.get("programs", [])) <= 1:
            return False
        app_data["programs"] = [p for p in app_data["programs"] if p.get("id") != program_id]
        if app_data.get("activeProgramId") == program_id:
            app_data["activeProgramId"] = app_data["programs"][0]["id"] if app_data["programs"] else None
        self.storage.save()
        self.session.init_for_program(get_active_program(app_data))
        return True

    def select_program(self, program_id: int) -> None:
        app_data = self.storage.get()
        app_data["activeProgramId"] = program_id
        self.session.init_for_program(get_active_program(app_data))
        self.storage.save()

    def add_exercise_to_active_program(self, name: str) -> None:
        app_data = self.storage.get()
        active_program = get_active_program(app_data)
        if not active_program:
            return
        new_exercise = {
            "id": int(time.time() * 1000),
            "name": name,
            "history": [],
            "nextTarget": None,
        }
        active_program["exercises"].append(new_exercise)
        if new_exercise["id"] not in self.session.current_workout_state:
            self.session.current_workout_state[new_exercise["id"]] = []
        self.storage.save()

    def delete_exercise_from_active(self, exercise_id: int) -> None:
        app_data = self.storage.get()
        active_program = get_active_program(app_data)
        if not active_program:
            return
        active_program["exercises"] = [ex for ex in active_program["exercises"] if ex.get("id") != exercise_id]
        if exercise_id in self.session.current_workout_state:
            del self.session.current_workout_state[exercise_id]
        self.storage.save()


    def init_current_workout(self) -> None:
        app_data = self.storage.get()
        self.session.init_for_program(get_active_program(app_data))

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


    def save_workout(self, saved_exercises_data: List[Dict[str, Any]]) -> None:
        app_data = self.storage.get()
        active_program = get_active_program(app_data)
        if not active_program:
            return

        for item in saved_exercises_data:
            exercise_data = item["exercise"]
            new_sets = item["newSets"]
            new_working_sets = [s for s in new_sets if s.get("type") == "normal"]
            if not new_working_sets:
                continue

            program_exercise = next(
                (ex for ex in active_program["exercises"] if ex.get("id") == exercise_data.get("id")), None
            )
            if not program_exercise:
                continue

            progression_type = active_program.get("progressionType", "double")
            has_target = program_exercise.get("nextTarget") is not None

            if not has_target:
                program_exercise["nextTarget"] = calculate_next_target(
                    program_exercise, {"sets": new_working_sets}, progression_type
                )
            else:
                if check_goal_achievement(program_exercise, new_working_sets, progression_type):
                    program_exercise["nextTarget"] = calculate_next_target(
                        program_exercise, {"sets": new_working_sets}, progression_type
                    )

        workout_entry = {
            "id": int(time.time() * 1000),
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "programId": active_program["id"],
            "programName": active_program["name"],
            "exercises": [],
        }
        for item in saved_exercises_data:
            workout_entry["exercises"].append({
                "exerciseId": item["exercise"]["id"],
                "exerciseName": item["exercise"]["name"],
                "sets": item["newSets"],
            })

        app_data["workoutHistory"].append(workout_entry)
        self.init_current_workout()
        self.storage.save()

    def generate_workout_summary(self, saved_exercises_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        app_data = self.storage.get()
        all_goals_achieved = True
        summary_details: List[Dict[str, Any]] = []

        for item in saved_exercises_data:
            exercise_data = item["exercise"]
            new_sets = item["newSets"]
            new_working_sets = [s for s in new_sets if s.get("type") == "normal"]
            if not new_working_sets:
                continue

            active_program = get_program_by_id(app_data, exercise_data["programId"])
            if not active_program:
                continue

            program_exercise = next(
                (ex for ex in active_program["exercises"] if ex.get("id") == exercise_data.get("id")), None
            )
            if not program_exercise:
                continue

            progression_type = active_program.get("progressionType", "double")
            has_target = program_exercise.get("nextTarget") is not None

            detail = {"exercise_name": program_exercise["name"]}
            if not has_target:
                detail["status"] = "success"
                detail["message"] = "Отличное начало! "
                potential = calculate_next_target(program_exercise, {"sets": new_working_sets}, progression_type)
                detail["next_target_text"] = (
                    f"Цель на следующую тренировку: {potential['text']}"
                    f"{f' с весом {potential['weight']} кг' if 'weight' in potential else ''}"
                )
            else:
                is_goal = check_goal_achievement(program_exercise, new_working_sets, progression_type)
                if is_goal:
                    detail["status"] = "success"
                    detail["message"] = "Цель достигнута! "
                    potential = calculate_next_target(program_exercise, {"sets": new_working_sets}, progression_type)
                    detail["next_target_text"] = (
                        f"Следующая цель: {potential['text']}"
                        f"{f' с весом {potential['weight']} кг' if 'weight' in potential else ''}"
                    )
                else:
                    all_goals_achieved = False
                    detail["status"] = "failure"
                    detail["message"] = "Цель не достигнута. "
                    nt = program_exercise["nextTarget"]
                    detail["next_target_text"] = (
                        f"Повторите: {nt['text']}"
                        f"{f' с весом {nt['weight']} кг' if 'weight' in nt else ''}"
                    )

            summary_details.append(detail)

        return {"all_goals_achieved": all_goals_achieved, "details": summary_details}

    def delete_history_session(self, session_id: int) -> None:
        app_data = self.storage.get()

        history = app_data.get("workoutHistory", [])
        session_to_delete = next((s for s in history if s.get("id") == session_id), None)
        if not session_to_delete:
            return

        app_data["workoutHistory"] = [s for s in history if s.get("id") != session_id]

        active_program = get_active_program(app_data)
        if active_program:
            progression_type = active_program.get("progressionType", "double")
            history_after = app_data.get("workoutHistory", [])

            for prog_ex in active_program.get("exercises", []):
                ex_id = prog_ex.get("id")

                last_workout_for_ex = None
                for workout_session in reversed(history_after):
                    for ex_entry in workout_session.get("exercises", []):
                        if ex_entry.get("exerciseId") == ex_id:
                            working_sets = [s for s in ex_entry.get("sets", []) if s.get("type") == "normal"]
                            last_workout_for_ex = {"sets": working_sets}
                            break
                    if last_workout_for_ex is not None:
                        break

                prev_target = prog_ex.get("nextTarget")
                prog_ex["nextTarget"] = None

                new_target = calculate_next_target(
                    prog_ex,
                    last_workout_for_ex,
                    progression_type
                )

                prog_ex["nextTarget"] = new_target

        self.storage.save()
        print("цель обновлена, теперь: ", prog_ex["nextTarget"])




    def get_progress_chart_data(self, exercise_id: int) -> Optional[Dict[str, List]]:
        app_data = self.storage.get()
        history_for_exercise: List[Dict[str, Any]] = []
        for workout_session in app_data.get("workoutHistory", []):
            for exercise_entry in workout_session.get("exercises", []):
                if exercise_entry.get("exerciseId") == exercise_id:
                    history_for_exercise.append({
                        "date": workout_session["date"],
                        "sets": exercise_entry["sets"],
                    })
        if not history_for_exercise:
            return None

        history_for_exercise.sort(key=lambda x: x["date"])
        labels = [h["date"] for h in history_for_exercise]
        data = [
            calculate_one_rep_max([s for s in h["sets"] if s.get("type") == "normal"])
            for h in history_for_exercise
        ]
        return {"labels": labels, "data": data}
    

    def reset_all_data(self) -> None:
        self.storage.set({
            "programs": [],
            "workoutHistory": [],
            "userSetupComplete": False,
            "activeProgramId": None,
        })
        self.session.reset()
        self.storage.save()
