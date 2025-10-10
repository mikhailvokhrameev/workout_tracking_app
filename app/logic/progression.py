from __future__ import annotations
from typing import Any, Dict, List


def calculate_next_target(exercise: Dict[str, Any], last_workout: Dict[str, Any], progression_type: str) -> Dict[str, Any]:
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


def check_goal_achievement(exercise: Dict[str, Any], new_working_sets: List[Dict[str, Any]], progression_type: str) -> bool:
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


def calculate_one_rep_max(working_sets: List[Dict[str, Any]]) -> float:
    if not working_sets:
        return 0.0
    max_orm = 0.0
    for s in working_sets:
        try:
            weight = float(s["weight"])
            reps = int(float(s["reps"]))
        except (ValueError, TypeError):
            continue
        if reps == 1:
            orm = weight
        elif reps > 1:
            orm = weight * (1 + reps / 30)
        else:
            orm = 0.0
        if orm > max_orm:
            max_orm = orm
    return max_orm
