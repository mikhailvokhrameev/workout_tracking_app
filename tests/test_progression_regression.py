from __future__ import annotations

from app.logic.progression import calculate_next_target, calculate_one_rep_max, check_goal_achievement


def test_calculate_next_target_linear_first_workout_matches_pre_refactor_shape():
    result = calculate_next_target({"nextTarget": None}, None, "linear")
    assert result == {"weight": None, "sets": 3, "reps": 12, "text": "3 подх. по 12 повт. с макс. весом"}


def test_calculate_next_target_double_first_workout_matches_pre_refactor_shape():
    result = calculate_next_target({"nextTarget": None}, None, "double")
    assert result == {"weight": None, "sets": 3, "reps": 8, "text": "3 подх. по 8 повт. с макс. весом"}


def test_calculate_next_target_linear_progresses_weight_on_all_12s():
    last_workout = {"sets": [{"type": "normal", "weight": 40.0, "reps": 12}] * 3}
    result = calculate_next_target({}, last_workout, "linear")
    assert result["weight"] == 41.25  # 40 + 1.25 step, rounded to nearest 0.25
    assert result["reps"] == 12


def test_calculate_next_target_double_holds_target_until_achieved():
    exercise = {"nextTarget": {"weight": 40.0, "sets": 3, "reps": 8, "text": "3x8"}}
    last_workout = {"sets": [{"type": "normal", "weight": 40.0, "reps": 6}] * 3}
    result = calculate_next_target(exercise, last_workout, "double")
    assert result["weight"] == 40.0
    assert result["reps"] == 8  # not achieved yet, target unchanged


def test_check_goal_achievement_no_target_is_always_true():
    assert check_goal_achievement({"nextTarget": None}, [], "linear") is True


def test_check_goal_achievement_requires_three_working_sets():
    exercise = {"nextTarget": {"weight": 40.0, "sets": 3, "reps": 8, "text": "3x8"}}
    sets = [{"type": "normal", "weight": 40.0, "reps": 8}]  # only 1 set
    assert check_goal_achievement(exercise, sets, "double") is False


def test_calculate_one_rep_max_empty_sets_returns_zero():
    assert calculate_one_rep_max([]) == 0.0


def test_calculate_one_rep_max_uses_epley_formula():
    result = calculate_one_rep_max([{"weight": 100.0, "reps": 5}])
    assert result == 100.0 * (1 + 5 / 30)


def test_generate_workout_summary_success_message_when_no_prior_target(service):
    service.create_new_program("Program", "double")
    service.add_exercise_to_active_program("Bench Press")
    active = service.get_active_program()
    exercise = active.exercises[0]

    saved_exercises_data = [
        {
            "exercise": {"id": exercise.id, "name": exercise.name, "programId": active.id},
            "newSets": [{"id": 1, "type": "normal", "weight": 40, "reps": 8}] * 3,
        }
    ]
    summary = service.generate_workout_summary(saved_exercises_data)
    assert summary["all_goals_achieved"] is True
    assert summary["details"][0]["status"] == "success"
    assert "Отличное начало" in summary["details"][0]["message"]


def test_generate_workout_summary_failure_message_when_goal_not_met(service):
    service.create_new_program("Program", "double")
    service.add_exercise_to_active_program("Bench Press")
    active = service.get_active_program()
    exercise = active.exercises[0]

    # First workout sets an initial target.
    first_pass = [
        {
            "exercise": {"id": exercise.id, "name": exercise.name, "programId": active.id},
            "newSets": [{"id": 1, "type": "normal", "weight": 20, "reps": 12}] * 3,
        }
    ]
    service.save_workout(first_pass)

    # Second attempt deliberately falls short of the now-set target.
    second_pass = [
        {
            "exercise": {"id": exercise.id, "name": exercise.name, "programId": active.id},
            "newSets": [{"id": 2, "type": "normal", "weight": 1.0, "reps": 1}] * 3,
        }
    ]
    summary = service.generate_workout_summary(second_pass)
    assert summary["all_goals_achieved"] is False
    assert summary["details"][0]["status"] == "failure"
    assert "не достигнута" in summary["details"][0]["message"]
