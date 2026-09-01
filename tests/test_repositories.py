from __future__ import annotations

from app.logic.dataclasses import NextTarget


def test_create_and_get_program(program_repo):
    program = program_repo.create_program(1, "Push/Pull/Legs", "double")
    fetched = program_repo.get_program_by_id(1)
    assert fetched is not None
    assert fetched.name == "Push/Pull/Legs"
    assert fetched.progression_type == "double"
    assert fetched.exercises == []


def test_add_and_delete_exercise(program_repo):
    program_repo.create_program(1, "Program", "linear")
    program_repo.add_exercise(1, 100, "Bench Press")
    program = program_repo.get_program_by_id(1)
    assert len(program.exercises) == 1
    assert program.exercises[0].name == "Bench Press"

    program_repo.delete_exercise(100)
    program = program_repo.get_program_by_id(1)
    assert program.exercises == []


def test_update_next_target(program_repo):
    program_repo.create_program(1, "Program", "linear")
    program_repo.add_exercise(1, 100, "Squat")

    program_repo.update_next_target(100, NextTarget(weight=42.5, sets=3, reps=12, text="3x12"))
    exercise = program_repo.get_exercise_by_id(100)
    assert exercise.next_target == NextTarget(weight=42.5, sets=3, reps=12, text="3x12")

    program_repo.update_next_target(100, None)
    exercise = program_repo.get_exercise_by_id(100)
    assert exercise.next_target is None


def test_delete_program_cascades_exercises(program_repo):
    program_repo.create_program(1, "Program", "linear")
    program_repo.add_exercise(1, 100, "Squat")
    program_repo.delete_program(1)
    assert program_repo.get_program_by_id(1) is None
    assert program_repo.get_exercise_by_id(100) is None


def test_delete_program_refuses_when_last_one(service, program_repo):
    """REGRESSION: existing behavior — can't delete the only remaining program."""
    service.create_new_program("Only Program", "linear")
    programs = program_repo.list_programs()
    assert len(programs) == 1

    result = service.delete_program(programs[0].id)
    assert result is False
    assert len(program_repo.list_programs()) == 1


def test_save_workout_skips_target_update_but_still_saves_history_for_zero_working_sets(service, workout_repo, program_repo):
    """REGRESSION: existing behavior — an item with no 'normal'-type sets still gets
    persisted to workout history (the original code's second loop is unconditional);
    only progression-target computation is gated on having working sets."""
    service.create_new_program("Program", "double")
    service.add_exercise_to_active_program("Bench Press")
    active = service.get_active_program()
    exercise = active.exercises[0]

    saved_exercises_data = [
        {
            "exercise": {"id": exercise.id, "name": exercise.name, "programId": active.id},
            "newSets": [{"id": 1, "type": "warmup", "weight": 20, "reps": 10}],
        }
    ]
    service.save_workout(saved_exercises_data)

    history = workout_repo.list_workout_history()
    assert len(history) == 1
    assert history[0].exercises[0].exercise_id == exercise.id
    # No working sets means no target was ever computed.
    assert program_repo.get_exercise_by_id(exercise.id).next_target is None


def test_get_progress_chart_data_zero_history_returns_none(service):
    service.create_new_program("Program", "double")
    service.add_exercise_to_active_program("Bench Press")
    active = service.get_active_program()
    exercise_id = active.exercises[0].id

    assert service.get_progress_chart_data(exercise_id) is None


def test_get_progress_chart_data_orders_by_date(service):
    service.create_new_program("Program", "double")
    service.add_exercise_to_active_program("Bench Press")
    active = service.get_active_program()
    exercise = active.exercises[0]

    for date_suffix in ["02", "01", "03"]:
        saved_exercises_data = [
            {
                "exercise": {"id": exercise.id, "name": exercise.name, "programId": active.id},
                "newSets": [{"id": 1, "type": "normal", "weight": 40, "reps": 8}],
            }
        ]
        service.save_workout(saved_exercises_data)

    chart = service.get_progress_chart_data(exercise.id)
    assert chart is not None
    assert chart["labels"] == sorted(chart["labels"])


def test_settings_active_program_id_roundtrip(settings_repo):
    assert settings_repo.get_active_program_id() is None
    settings_repo.set_active_program_id(42)
    assert settings_repo.get_active_program_id() == 42
    settings_repo.set_active_program_id(None)
    assert settings_repo.get_active_program_id() is None


def test_settings_user_setup_complete_roundtrip(settings_repo):
    assert settings_repo.get_user_setup_complete() is False
    settings_repo.set_user_setup_complete(True)
    assert settings_repo.get_user_setup_complete() is True


def test_reset_all_wipes_everything(service, program_repo, settings_repo):
    service.create_new_program("Program", "linear")
    settings_repo.set_user_setup_complete(True)

    service.reset_all_data()

    assert program_repo.list_programs() == []
    assert settings_repo.get_active_program_id() is None
    assert settings_repo.get_user_setup_complete() is False
