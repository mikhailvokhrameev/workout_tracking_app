from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.logic.models import get_active_program, get_program_by_id, find_exercise_by_id
from app.logic.services import WorkoutService
from app.logic.session_state import SessionState
from app.logic.storage import AppStorage


class ProgressiveOverloadLogic:
    def __init__(self, data_file: str = "app_data.json") -> None:
        self.storage = AppStorage(data_file)
        self.storage.load()

        app_data = self.storage.get()
        if app_data.get("userSetupComplete"):
            if app_data.get("programs") and not app_data.get("activeProgramId"):
                app_data["activeProgramId"] = app_data["programs"][0]["id"]

        self.session = SessionState()
        self.service = WorkoutService(self.storage, self.session)

        self.service.init_current_workout()

    # helpers

    def get_active_program(self) -> Optional[Dict[str, Any]]:
        return get_active_program(self.storage.get())

    def get_program_by_id(self, program_id: int) -> Optional[Dict[str, Any]]:
        return get_program_by_id(self.storage.get(), program_id)

    def find_exercise_by_id(self, exercise_id: int) -> Optional[Dict[str, Any]]:
        return find_exercise_by_id(self.storage.get(), exercise_id)

    # CRUD

    def create_new_program(self, name: str, progression_type: str) -> None:
        self.service.create_new_program(name, progression_type)

    def delete_program(self, program_id: int) -> bool:
        return self.service.delete_program(program_id)

    def select_program(self, program_id: int) -> None:
        self.service.select_program(program_id)

    def add_exercise_to_program(self, name: str) -> None:
        self.service.add_exercise_to_active_program(name)

    def delete_exercise(self, exercise_id: int) -> None:
        self.service.delete_exercise_from_active(exercise_id)

    # current workout state

    def init_current_workout(self) -> None:
        self.service.init_current_workout()

    def add_set_to_workout(self, exercise_id: int) -> None:
        self.service.add_set_to_workout(exercise_id)

    def delete_set_from_workout(self, exercise_id: int, set_id: int) -> None:
        self.service.delete_set_from_workout(exercise_id, set_id)

    def update_set_in_workout(self, exercise_id: int, set_id: int, property_name: str, value: str) -> None:
        self.service.update_set_in_workout(exercise_id, set_id, property_name, value)
    
    def get_current_workout_state(self):
        state = self.service.session.current_workout_state
        return {ex_id: list(sets) for ex_id, sets in state.items()}
    
    def list_programs(self):
        return [dict(p) for p in self.storage.get().get("programs", [])]
    
    def list_workout_history(self):
        return [dict(s) for s in self.storage.get().get("workoutHistory", [])]

    # validation support for ui

    def update_set_error_state(self, exercise_id: int, set_id: int, property_name: str, has_error: bool) -> None:
        self.service.update_set_error_state(exercise_id, set_id, property_name, has_error)

    def has_validation_errors(self) -> bool:
        return self.service.has_validation_errors()

    # save and summarize workouts

    def save_workout(self, saved_exercises_data: List[Dict[str, Any]]) -> None:
        self.service.save_workout(saved_exercises_data)

    def generate_workout_summary(self, saved_exercises_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        return self.service.generate_workout_summary(saved_exercises_data)

    # maintenance

    def delete_history_session(self, session_id: int) -> None:
        self.service.delete_history_session(session_id)
        
    def reset_all_data(self) -> None:
        self.service.reset_all_data()

    # chart

    def get_progress_chart_data(self, exercise_id: int) -> Optional[Dict[str, List]]:
        return self.service.get_progress_chart_data(exercise_id)


    
