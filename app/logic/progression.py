from __future__ import annotations
from typing import Any, Dict, List, Optional

from typing import Dict, Any, Optional

def calculate_next_target(exercise: Dict[str, Any], last_workout: Optional[Dict[str, Any]], progression_type: str) -> Dict[str, Any]:
    """
    Рассчитывает следующую цель для 'linear' или 'double' прогрессии.
    
    - Если у упражнения нет цели, устанавливает ее на основе лучшего сета из last_workout (без инкремента).
    - Если у упражнения уже есть цель, рассчитывает новую цель с инкрементом веса.
    """
    last_working_sets = []
    if last_workout:
        last_working_sets = [s for s in last_workout.get("sets", []) if s.get("type") == "normal"]

    if not last_working_sets:
        # Стартовая цель, если данных нет
        base_text = {
            "linear": "3 подхода по 12 повторений",
            "double": "3 подхода по 6-10 повторений",
        }
        return {
            "weight": 20, "sets": 3,
            "reps": 12 if progression_type == "linear" else 6,
            "text": base_text.get(progression_type, base_text["double"]),
        }

    if progression_type == "linear":
        # 1. Определяем базовый вес из последней тренировки
        qualifying_weights = [float(s["weight"]) for s in last_working_sets if s.get("reps", 0) >= 12]
        if qualifying_weights:
            base_weight = max(qualifying_weights)
        else:
            all_weights = [float(s.get("weight", 0)) for s in last_working_sets]
            base_weight = max(all_weights) if all_weights else 0

        # Проверяем наличие существующей цели
        has_existing_target = exercise.get("nextTarget") and exercise["nextTarget"].get("weight")

        if not has_existing_target:
            # ЦЕЛИ НЕТ (ПЕРВАЯ ТРЕНИРОВКА): Устанавливаем цель без инкремента.
            new_weight = base_weight
        else:
            # ЦЕЛЬ ЕСТЬ: Увеличиваем вес.
            weight_increment = 2.5 if base_weight > 40 else 1.25
            new_weight = round((base_weight + weight_increment) * 4) / 4
        
        return {
            "weight": new_weight, "sets": 3, "reps": 12, "text": "3 подхода по 12 повторений"
        }

    # --- ИЗМЕНЕННАЯ ЛОГИКА ДЛЯ ДРУГИХ ТИПОВ ПРОГРЕССИИ ---
    elif progression_type == "double":
        # Логика расчета для двойной прогрессии
        base_weight = float(last_working_sets[0]["weight"])
        weight_increment = 2.5 if base_weight > 40 else 1.25
        new_weight = round((base_weight + weight_increment) * 4) / 4
        return {
            "weight": new_weight, "sets": 3, "reps": 6, "text": "3 подхода по 6-10 повторений"
        }
    
    else:
        # Безопасный fallback на случай, если придет неизвестный тип прогрессии.
        # Возвращаем стартовую цель для двойной прогрессии.
        return {
            "weight": 20, "sets": 3, "reps": 6, "text": "3 подхода по 6-10 повторений"
        }





def check_goal_achievement(exercise: Dict[str, Any], new_working_sets: List[Dict[str, Any]], progression_type: str) -> bool:
    """
    Проверяет, была ли достигнута текущая цель в выполненной тренировке.
    """
    if not exercise.get("nextTarget"):
        return True  # Если цели не было, считаем ее достигнутой.

    try:
        target_weight = float(exercise["nextTarget"]["weight"])

        if progression_type == "linear":
            target_reps = 12
            target_sets_count = 3
            linear_sets = [s for s in new_working_sets if s.get("type") == "normal"]
            
            # Цель достигнута, если есть как минимум 3 подхода, и все они
            # соответствуют целевому весу и повторениям.
            if len(linear_sets) < target_sets_count:
                return False

            # Проверяем первые 3 подхода
            return all(
                s.get("reps", 0) >= target_reps and float(s.get("weight", 0)) >= target_weight
                for s in linear_sets[:target_sets_count]
            )

        elif progression_type == "double":
            double_sets = new_working_sets[:3]
            return len(double_sets) >= 3 and all(
                float(s["reps"]) >= 10 and float(s["weight"]) >= target_weight for s in double_sets
            )
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
