# -*- coding: utf-8 -*-

from __future__ import annotations
from typing import Any, Dict, List, Optional


def get_active_program(app_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    active_id = app_data.get("activeProgramId")
    if not active_id:
        return None
    return next((p for p in app_data.get("programs", []) if p.get("id") == active_id), None)


def get_program_by_id(app_data: Dict[str, Any], program_id: int) -> Optional[Dict[str, Any]]:
    return next((p for p in app_data.get("programs", []) if p.get("id") == program_id), None)


def find_exercise_by_id(app_data: Dict[str, Any], exercise_id: int) -> Optional[Dict[str, Any]]:
    for p in app_data.get("programs", []):
        for ex in p.get("exercises", []):
            if ex.get("id") == exercise_id:
                return {**ex, "programId": p.get("id")}
    return None

def get_last_workout_for_exercise(app_data: Dict[str, Any], exercise_id: int) -> Optional[Dict[str, Any]]:
    workout_history = app_data.get("workoutHistory", [])

    for workout_session in reversed(workout_history):
        for exercise_in_session in workout_session.get("exercises", []):
            if exercise_in_session.get("exerciseId") == exercise_id:
                return exercise_in_session
    
    return None
