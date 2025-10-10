import json
import time
from datetime import datetime
from typing import List, Dict, Any, Optional


class ProgressiveOverloadLogic:
    def __init__(self, data_file: str = "app_data.json"):
        self.data_file = data_file
        self.app_data: Dict[str, Any] = {
            "programs": [],
            "workoutHistory": [],
            "userSetupComplete": False,
            "activeProgramId": None,
        }
        self.current_workout_state: Dict[int, List[Dict[str, Any]]] = {}
        self.load_data()

    def load_data(self) -> None:
        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                saved_data = json.load(f)
            self.app_data.update(saved_data)
            if "workoutHistory" not in self.app_data:
                self.app_data["workoutHistory"] = []
        except (FileNotFoundError, json.JSONDecodeError):
            pass

        if self.app_data["userSetupComplete"]:
            if self.app_data["programs"] and not self.app_data["activeProgramId"]:
                self.app_data["activeProgramId"] = self.app_data["programs"][0]["id"]
        self.init_current_workout()

    def save_data(self) -> None:
        try:
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(self.app_data, f, indent=4, ensure_ascii=False)
        except IOError:
            pass

    def get_active_program(self) -> Optional[Dict[str, Any]]:
        if not self.app_data["activeProgramId"]:
            return None
        return next(
            (p for p in self.app_data["programs"] if p["id"] == self.app_data["activeProgramId"]),
            None,
        )

    def get_program_by_id(self, program_id: int) -> Optional[Dict[str, Any]]:
        return next((p for p in self.app_data["programs"] if p["id"] == program_id), None)

    def find_exercise_by_id(self, exercise_id: int) -> Optional[Dict[str, Any]]:
        for p in self.app_data["programs"]:
            for ex in p["exercises"]:
                if ex["id"] == exercise_id:
                    return {**ex, "programId": p["id"]}
        return None

    def create_new_program(self, name: str, progression_type: str) -> None:
        new_program = {
            "id": int(time.time() * 1000),
            "name": name,
            "progressionType": progression_type,
            "exercises": [],
        }
        if len(name) <= 30:
            self.app_data["programs"].append(new_program)
            self.app_data["activeProgramId"] = new_program["id"]
            self.save_data()
            self.init_current_workout()

    def delete_program(self, program_id: int) -> bool:
        if len(self.app_data["programs"]) <= 1:
            return False
        self.app_data["programs"] = [p for p in self.app_data["programs"] if p["id"] != program_id]
        if self.app_data["activeProgramId"] == program_id:
            self.app_data["activeProgramId"] = self.app_data["programs"][0]["id"] if self.app_data["programs"] else None
        self.save_data()
        self.init_current_workout()
        return True

    def select_program(self, program_id: int) -> None:
        self.app_data["activeProgramId"] = program_id
        self.init_current_workout()
        self.save_data()

    def add_exercise_to_program(self, name: str) -> None:
        active_program = self.get_active_program()
        if not active_program:
            return
        new_exercise = {
            "id": int(time.time() * 1000),
            "name": name,
            "history": [],
            "nextTarget": None,
        }
        active_program["exercises"].append(new_exercise)
        if new_exercise["id"] not in self.current_workout_state:
            self.current_workout_state[new_exercise["id"]] = []
        self.save_data()

    def delete_exercise(self, exercise_id: int) -> None:
        active_program = self.get_active_program()
        if not active_program:
            return
        active_program["exercises"] = [ex for ex in active_program["exercises"] if ex["id"] != exercise_id]
        if exercise_id in self.current_workout_state:
            del self.current_workout_state[exercise_id]
        self.save_data()

    def init_current_workout(self) -> None:
        self.current_workout_state = {}
        active_program = self.get_active_program()
        if active_program:
            for ex in active_program["exercises"]:
                self.current_workout_state[ex["id"]] = []

    def add_set_to_workout(self, exercise_id: int) -> None:
        if exercise_id not in self.current_workout_state:
            self.current_workout_state[exercise_id] = []
        self.current_workout_state[exercise_id].append(
            {
                "id": int(time.time() * 1000),
                "type": "normal",
                "weight": "",
                "reps": "",
            }
        )

    def delete_set_from_workout(self, exercise_id: int, set_id: int) -> None:
        self.current_workout_state[exercise_id] = [
            s for s in self.current_workout_state.get(exercise_id, []) if s["id"] != set_id
        ]

    def update_set_in_workout(self, exercise_id: int, set_id: int, property_name: str, value: str) -> None:
        for s in self.current_workout_state.get(exercise_id, []):
            if s["id"] == set_id:
                s[property_name] = value
                break

    def update_set_error_state(self, exercise_id: int, set_id: int, property_name: str, has_error: bool) -> None:
        for s in self.current_workout_state.get(exercise_id, []):
            if s["id"] == set_id:
                if "errors" not in s:
                    s["errors"] = {}
                s["errors"][property_name] = has_error
                break

    def has_validation_errors(self) -> bool:
        for _, sets in self.current_workout_state.items():
            for s in sets:
                errors = s.get("errors", {})
                if errors.get("weight", False) or errors.get("reps", False):
                    return True
        return False

    def _calculate_next_target(self, exercise: Dict, last_workout: Dict, progression_type: str) -> Dict:
        last_working_sets = [s for s in last_workout.get("sets", []) if s.get("type") == "normal"]
        if not last_working_sets:
            base_text = {
                "linear": "5 подходов по 5 повторений",
                "double": "3 подхода по 6-10 повторений",
                "rep_range": "3 подхода по 8-12 повторений",
            }
            return {
                "weight": 20,
                "sets": 5 if progression_type == "linear" else 3,
                "reps": 5 if progression_type == "linear" else ("8-12" if progression_type == "rep_range" else 6),
                "text": base_text.get(progression_type, base_text["double"]),
            }

        last_weight = float(last_working_sets[0]["weight"])
        weight_increment = 2.5 if last_weight > 40 else 1.25
        new_weight = round((last_weight + weight_increment) * 4) / 4

        targets = {
            "linear": {"weight": new_weight, "sets": 5, "reps": 5, "text": "5 подходов по 5 повторений"},
            "double": {"weight": new_weight, "sets": 3, "reps": 6, "text": "3 подхода по 6-10 повторений"},
            "rep_range": {"weight": new_weight, "sets": 3, "reps": "8-12", "text": "3 подхода по 8-12 повторений"},
        }
        return targets.get(progression_type, targets["rep_range"])

    def _check_goal_achievement(self, exercise: Dict, new_working_sets: List[Dict], progression_type: str) -> bool:
        if not exercise.get("nextTarget"):
            return True
        try:
            target_weight = float(exercise["nextTarget"]["weight"])
            if progression_type == "linear":
                linear_sets = new_working_sets[:5]
                return len(linear_sets) >= 5 and all(
                    float(s["reps"]) >= 5 and float(s["weight"]) >= target_weight for s in linear_sets
                )
            elif progression_type == "double":
                double_sets = new_working_sets[:3]
                return len(double_sets) >= 3 and all(
                    float(s["reps"]) >= 10 and float(s["weight"]) >= target_weight for s in double_sets
                )
            elif progression_type == "rep_range":
                main_set = new_working_sets[0] if new_working_sets else None
                return bool(main_set) and float(main_set["reps"]) >= 12 and float(main_set["weight"]) >= target_weight
            return True
        except (ValueError, TypeError, KeyError):
            return True

    def _calculate_one_rep_max(self, working_sets: List[Dict]) -> float:
        if not working_sets:
            return 0.0
        max_one_rep_max = 0.0
        for s in working_sets:
            try:
                weight = float(s["weight"])
                reps = int(float(s["reps"]))
            except (ValueError, TypeError):
                continue
            if reps == 1:
                one_rep_max = weight
            elif reps > 1:
                one_rep_max = weight * (1 + reps / 30)
            else:
                one_rep_max = 0.0
            if one_rep_max > max_one_rep_max:
                max_one_rep_max = one_rep_max
        return max_one_rep_max

    def save_workout(self, saved_exercises_data: List[Dict]) -> None:
        active_program = self.get_active_program()
        if not active_program:
            return

        for item in saved_exercises_data:
            exercise_data = item["exercise"]
            new_sets = item["newSets"]
            new_working_sets = [s for s in new_sets if s.get("type") == "normal"]
            if not new_working_sets:
                continue

            program_exercise = next(
                (ex for ex in active_program["exercises"] if ex["id"] == exercise_data["id"]), None
            )
            if not program_exercise:
                continue

            progression_type = active_program.get("progressionType", "double")
            has_previous_target = program_exercise.get("nextTarget") is not None
            if not has_previous_target:
                program_exercise["nextTarget"] = self._calculate_next_target(
                    program_exercise, {"sets": new_working_sets}, progression_type
                )
            else:
                if self._check_goal_achievement(program_exercise, new_working_sets, progression_type):
                    program_exercise["nextTarget"] = self._calculate_next_target(
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
            workout_entry["exercises"].append(
                {
                    "exerciseId": item["exercise"]["id"],
                    "exerciseName": item["exercise"]["name"],
                    "sets": item["newSets"],
                }
            )
        self.app_data["workoutHistory"].append(workout_entry)

        self.init_current_workout()
        self.save_data()

    def generate_workout_summary(self, saved_exercises_data: List[Dict]) -> Dict[str, Any]:
        all_goals_achieved = True
        summary_details = []

        for item in saved_exercises_data:
            exercise_data = item["exercise"]
            new_sets = item["newSets"]
            new_working_sets = [s for s in new_sets if s.get("type") == "normal"]
            if not new_working_sets:
                continue

            active_program = self.get_program_by_id(exercise_data["programId"])
            if not active_program:
                continue

            program_exercise = next(
                (ex for ex in active_program["exercises"] if ex["id"] == exercise_data["id"]), None
            )
            if not program_exercise:
                continue

            progression_type = active_program.get("progressionType", "double")
            has_previous_target = program_exercise.get("nextTarget") is not None

            detail = {"exercise_name": program_exercise["name"]}
            if not has_previous_target:
                detail["status"] = "success"
                detail["message"] = "Отличное начало! "
                potential_next_target = self._calculate_next_target(
                    program_exercise, {"sets": new_working_sets}, progression_type
                )
                detail["next_target_text"] = (
                    f"Цель на следующую тренировку: {potential_next_target['text']}"
                    f"{f' с весом {potential_next_target['weight']} кг' if 'weight' in potential_next_target else ''}"
                )
            else:
                is_goal_achieved = self._check_goal_achievement(
                    program_exercise, new_working_sets, progression_type
                )
                if is_goal_achieved:
                    detail["status"] = "success"
                    detail["message"] = "Цель достигнута! "
                    potential_next_target = self._calculate_next_target(
                        program_exercise, {"sets": new_working_sets}, progression_type
                    )
                    detail["next_target_text"] = (
                        f"Следующая цель: {potential_next_target['text']}"
                        f"{f' с весом {potential_next_target['weight']} кг' if 'weight' in potential_next_target else ''}"
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
        session_to_delete = next((s for s in self.app_data["workoutHistory"] if s["id"] == session_id), None)
        if not session_to_delete:
            return
        self.app_data["workoutHistory"] = [s for s in self.app_data["workoutHistory"] if s["id"] != session_id]

        for program in self.app_data["programs"]:
            for exercise in program["exercises"]:
                is_exercise_in_session = any(
                    ex["exerciseId"] == exercise["id"] for ex in session_to_delete.get("exercises", [])
                )
                if is_exercise_in_session:
                    exercise["history"] = [h for h in exercise.get("history", []) if h.get("date") != session_to_delete["date"]]

        self.save_data()

    def get_progress_chart_data(self, exercise_id: int) -> Optional[Dict[str, List]]:
        history_for_exercise = []
        for workout_session in self.app_data.get("workoutHistory", []):
            for exercise_entry in workout_session.get("exercises", []):
                if exercise_entry.get("exerciseId") == exercise_id:
                    history_for_exercise.append(
                        {"date": workout_session["date"], "sets": exercise_entry["sets"]}
                    )

        if not history_for_exercise:
            return None

        history_for_exercise.sort(key=lambda x: x["date"])

        labels = [h["date"] for h in history_for_exercise]
        one_rep_max_data = [
            self._calculate_one_rep_max([s for s in h["sets"] if s.get("type") == "normal"])
            for h in history_for_exercise
        ]
        return {"labels": labels, "data": one_rep_max_data}

    def reset_all_data(self) -> None:
        self.app_data = {
            "programs": [],
            "workoutHistory": [],
            "userSetupComplete": False,
            "activeProgramId": None,
        }
        self.current_workout_state = {}
        self.save_data()
