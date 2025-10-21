from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

def calculate_next_target(exercise: Dict[str, Any], last_workout: Optional[Dict[str, Any]], progression_type: str) -> Dict[str, Any]:

    last_working_sets = [s for s in last_workout.get("sets", []) if s.get("type") == "normal"] if last_workout else []

    if not last_working_sets:
        if progression_type == "linear":
            return {
                "weight": None, "sets": 3, "reps": 12,
                "text": "3 подх. по 12 повт. с макс. весом"
            }
        else:
            return {
                "weight": None, "sets": 3, "reps": 8,
                "text": "3 подх. по 8 повт. с макс. весом"
            }
    
    if progression_type == "linear":
        qualifying_weights = [float(s["weight"]) for s in last_working_sets if s.get("reps", 0) >= 12]
        if qualifying_weights:
            base_weight = max(qualifying_weights)
        else:
            all_weights = [float(s.get("weight", 0)) for s in last_working_sets]
            base_weight = max(all_weights) if all_weights else 0

        has_existing_target = exercise.get("nextTarget") and exercise["nextTarget"].get("weight")

        if not has_existing_target:
            new_weight = base_weight
        else:
            weight_increment = 2.5 if base_weight > 40 else 1.25
            new_weight = round((base_weight + weight_increment) * 4) / 4
        
        return {
            "weight": new_weight, "sets": 3, "reps": 12, "text": "3 подхода по 12 повторений"
        }
        
    elif progression_type == "double":
        INCREMENT_KG = 1.25
        current_target = exercise.get("nextTarget") or {}
        has_target = "weight" in current_target

        if has_target:
            current_weight = float(current_target.get("weight", 0.0))
            current_reps = int(current_target.get("reps", 8))
        else:
            candidates_r8 = [float(s.get("weight", 0.0)) for s in last_working_sets if int(float(s.get("reps", 0))) >= 8]
            if candidates_r8:
                current_weight = max(candidates_r8)
            else:
                max_reps = max(int(float(s.get("reps", 0))) for s in last_working_sets)
                ties = [float(s.get("weight", 0.0)) for s in last_working_sets if int(float(s.get("reps", 0))) == max_reps]
                current_weight = min(ties) if ties else 20.0
            current_reps = 8

        first_three = last_working_sets[:3]
        if len(first_three) < 3:
            return {
                "weight": float(current_weight), "sets": 3, "reps": int(current_reps),
                "text": f"3 подх. x {current_reps} повт.",
            }
            
        achieved_current = all(
            int(float(s.get("reps", 0))) >= current_reps and float(s.get("weight", 0.0)) >= current_weight
            for s in first_three
        )

        if not achieved_current:
            next_reps, next_weight = current_reps, current_weight
        else:
            min_reps_achieved = min(int(float(s.get("reps", 0))) for s in first_three)

            if min_reps_achieved >= 10:
                next_weight = round((current_weight + INCREMENT_KG) * 4) / 4
                next_reps = 8
            else:
                next_reps = min_reps_achieved + 1
                next_weight = current_weight

        return {
            "weight": float(next_weight), "sets": 3, "reps": int(next_reps),
            "text": f"3 подх. x {int(next_reps)} повт.",
        }



def check_goal_achievement(exercise: Dict[str, Any], new_working_sets: List[Dict[str, Any]], progression_type: str) -> bool:
    if not exercise.get("nextTarget"):
        return True

    try:
        target = exercise["nextTarget"]
        target_weight = float(target.get("weight", 0.0))
        if progression_type == "linear":
            target_reps = 12
        else:
            target_reps = int(target.get("reps", 8))

        sets = [s for s in new_working_sets if s.get("type") == "normal"]
        if len(sets) < 3:
            return False

        first_three = sets[:3]
        return all(
            int(float(s.get("reps", 0))) >= target_reps and float(s.get("weight", 0)) >= target_weight
            for s in first_three
        )
    except (ValueError, TypeError, KeyError):
        return True


def calculate_one_rep_max(working_sets: List[Dict[str, Any]]) -> float:
    if not working_sets:
        return 0.0

    max_orm = 0.0
    for s in working_sets:
        try:
            weight = float(s.get("weight", 0))
            reps = int(float(s.get("reps", 0)))
        except (ValueError, TypeError):
            continue

        if reps <= 0 or weight <= 0:
            orm = 0.0
        elif reps == 1:
            orm = weight
        else:
            orm = weight * (1 + reps / 30)

        if orm > max_orm:
            max_orm = orm

    return max_orm

