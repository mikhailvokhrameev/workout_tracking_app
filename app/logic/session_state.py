from __future__ import annotations
import time
from typing import Any, Dict, List


class SessionState:
    def __init__(self) -> None:
        self.current_workout_state: Dict[int, List[Dict[str, Any]]] = {}

    def reset(self) -> None:
        self.current_workout_state = {}

    def init_for_program(self, program: Dict[str, Any]) -> None:
        self.reset()
        if not program:
            return
        for ex in program.get("exercises", []):
            self.current_workout_state[ex["id"]] = []

    def add_set(self, exercise_id: int) -> None:
        if exercise_id not in self.current_workout_state:
            self.current_workout_state[exercise_id] = []
        self.current_workout_state[exercise_id].append({
            "id": int(time.time() * 1000),
            "type": "normal",
            "weight": "",
            "reps": "",
        })

    def delete_set(self, exercise_id: int, set_id: int) -> None:
        self.current_workout_state[exercise_id] = [
            s for s in self.current_workout_state.get(exercise_id, []) if s["id"] != set_id
        ]

    def update_set(self, exercise_id: int, set_id: int, prop: str, value: str) -> None:
        for s in self.current_workout_state.get(exercise_id, []):
            if s["id"] == set_id:
                s[prop] = value
                break

    def update_set_error(self, exercise_id: int, set_id: int, prop: str, has_error: bool) -> None:
        for s in self.current_workout_state.get(exercise_id, []):
            if s["id"] == set_id:
                if "errors" not in s:
                    s["errors"] = {}
                s["errors"][prop] = has_error
                break

    def has_validation_errors(self) -> bool:
        for _, sets in self.current_workout_state.items():
            for s in sets:
                errors = s.get("errors", {})
                if errors.get("weight", False) or errors.get("reps", False):
                    return True
        return False
