from __future__ import annotations

from app.logic.progression import calculate_next_target, calculate_one_rep_max, check_goal_achievement


def _sets(*pairs):
    """Build a list of normal working sets from (weight, reps) pairs."""
    return [{"type": "normal", "weight": w, "reps": r} for w, r in pairs]


# ---------------------------------------------------------------------------
# calculate_next_target — linear progression
# ---------------------------------------------------------------------------

class TestCalculateNextTargetLinear:
    def test_no_last_workout_returns_starting_target(self):
        result = calculate_next_target({}, None, "linear")
        assert result == {"weight": None, "sets": 3, "reps": 12, "text": "3 подх. по 12 повт. с макс. весом"}

    def test_last_workout_with_no_working_sets_returns_starting_target(self):
        last_workout = {"sets": [{"type": "warmup", "weight": 20, "reps": 5}]}
        result = calculate_next_target({}, last_workout, "linear")
        assert result["weight"] is None
        assert result["reps"] == 12

    def test_fewer_than_three_sets_holds_at_max_weight_seen(self):
        last_workout = {"sets": _sets((40.0, 10), (42.5, 8))}
        result = calculate_next_target({}, last_workout, "linear")
        assert result == {"weight": 42.5, "sets": 3, "reps": 12, "text": "3 подхода по 12 повторений"}

    def test_fewer_than_three_sets_all_zero_weight_returns_none(self):
        last_workout = {"sets": _sets((0.0, 10), (0.0, 8))}
        result = calculate_next_target({}, last_workout, "linear")
        assert result["weight"] is None

    def test_all_three_hit_12_reps_same_weight_at_exactly_40kg_uses_small_step(self):
        last_workout = {"sets": _sets((40.0, 12), (40.0, 12), (40.0, 12))}
        result = calculate_next_target({}, last_workout, "linear")
        # step = 2.5 only when max_w > 40 (strictly); 40 itself is the small-step boundary
        assert result["weight"] == 41.25
        assert result["reps"] == 12

    def test_all_three_hit_12_reps_same_weight_increases_by_small_step_at_or_below_40kg(self):
        last_workout = {"sets": _sets((30.0, 12), (30.0, 12), (30.0, 12))}
        result = calculate_next_target({}, last_workout, "linear")
        assert result["weight"] == 31.25

    def test_all_three_hit_12_reps_same_weight_above_40_uses_large_step(self):
        last_workout = {"sets": _sets((45.0, 12), (45.0, 12), (45.0, 12))}
        result = calculate_next_target({}, last_workout, "linear")
        assert result["weight"] == 47.5

    def test_all_three_hit_12_reps_mixed_weight_targets_max_weight_no_increase(self):
        last_workout = {"sets": _sets((40.0, 12), (42.5, 12), (45.0, 12))}
        result = calculate_next_target({}, last_workout, "linear")
        assert result["weight"] == 45.0

    def test_not_all_12_but_some_sets_hit_12_targets_max_weight_among_those(self):
        last_workout = {"sets": _sets((40.0, 12), (42.5, 10), (37.5, 12))}
        result = calculate_next_target({}, last_workout, "linear")
        assert result["weight"] == 40.0  # max among the sets that DID hit 12 reps

    def test_no_set_hits_12_holds_at_max_weight_among_first_three(self):
        last_workout = {"sets": _sets((40.0, 8), (42.5, 9), (37.5, 10))}
        result = calculate_next_target({}, last_workout, "linear")
        assert result["weight"] == 42.5

    def test_no_set_hits_12_all_zero_weight_returns_none(self):
        last_workout = {"sets": _sets((0.0, 8), (0.0, 9), (0.0, 10))}
        result = calculate_next_target({}, last_workout, "linear")
        assert result["weight"] is None

    def test_only_first_three_sets_considered_even_with_more_logged(self):
        last_workout = {"sets": _sets((10.0, 12), (10.0, 12), (10.0, 12), (100.0, 12))}
        result = calculate_next_target({}, last_workout, "linear")
        # 4th set (100kg) must not influence the result
        assert result["weight"] == 11.25


# ---------------------------------------------------------------------------
# calculate_next_target — double progression
# ---------------------------------------------------------------------------

class TestCalculateNextTargetDouble:
    def test_no_last_workout_returns_starting_target(self):
        result = calculate_next_target({}, None, "double")
        assert result == {"weight": None, "sets": 3, "reps": 8, "text": "3 подх. по 8 повт. с макс. весом"}

    def test_existing_target_used_as_baseline(self):
        exercise = {"nextTarget": {"weight": 50.0, "reps": 8}}
        last_workout = {"sets": _sets((50.0, 5))}  # only 1 set, hold path
        result = calculate_next_target(exercise, last_workout, "double")
        assert result["weight"] == 50.0
        assert result["reps"] == 8

    def test_no_existing_target_derives_baseline_from_sets_with_at_least_8_reps(self):
        last_workout = {"sets": _sets((30.0, 8), (35.0, 9))}
        result = calculate_next_target({}, last_workout, "double")
        # only 2 sets -> hold path, but baseline should be max of the >=8-rep candidates (35.0)
        assert result["weight"] == 35.0
        assert result["reps"] == 8

    def test_no_existing_target_no_sets_with_8_reps_falls_back_to_min_weight_at_max_reps(self):
        last_workout = {"sets": _sets((20.0, 5), (25.0, 5), (30.0, 3))}
        result = calculate_next_target({}, last_workout, "double")
        # max_reps=5, tied at weights 20/25 -> min of those = 20.0
        assert result["weight"] == 20.0

    def test_fewer_than_three_sets_holds_current_target(self):
        exercise = {"nextTarget": {"weight": 40.0, "reps": 8}}
        last_workout = {"sets": _sets((40.0, 8), (40.0, 8))}
        result = calculate_next_target(exercise, last_workout, "double")
        assert result == {"weight": 40.0, "sets": 3, "reps": 8, "text": "3 подх. x 8 повт."}

    def test_goal_not_achieved_holds_current_target(self):
        exercise = {"nextTarget": {"weight": 40.0, "reps": 8}}
        last_workout = {"sets": _sets((40.0, 6), (40.0, 6), (40.0, 6))}
        result = calculate_next_target(exercise, last_workout, "double")
        assert result["weight"] == 40.0
        assert result["reps"] == 8

    def test_goal_achieved_but_reps_below_10_increments_reps_not_weight(self):
        exercise = {"nextTarget": {"weight": 40.0, "reps": 8}}
        last_workout = {"sets": _sets((40.0, 9), (40.0, 8), (40.0, 8))}
        result = calculate_next_target(exercise, last_workout, "double")
        # min reps achieved among first three = 8, < 10 -> reps += 1, weight unchanged
        assert result["weight"] == 40.0
        assert result["reps"] == 9

    def test_goal_achieved_with_min_reps_at_least_10_increases_weight_and_resets_reps(self):
        exercise = {"nextTarget": {"weight": 40.0, "reps": 8}}
        last_workout = {"sets": _sets((40.0, 10), (40.0, 11), (40.0, 12))}
        result = calculate_next_target(exercise, last_workout, "double")
        assert result["weight"] == 41.25
        assert result["reps"] == 8

    def test_weight_not_meeting_current_weight_counts_as_not_achieved(self):
        exercise = {"nextTarget": {"weight": 40.0, "reps": 8}}
        last_workout = {"sets": _sets((35.0, 12), (35.0, 12), (35.0, 12))}
        result = calculate_next_target(exercise, last_workout, "double")
        # reps are high but weight is below target -> not achieved, hold
        assert result["weight"] == 40.0
        assert result["reps"] == 8


# ---------------------------------------------------------------------------
# check_goal_achievement
# ---------------------------------------------------------------------------

class TestCheckGoalAchievement:
    def test_no_target_always_true(self):
        assert check_goal_achievement({}, [], "double") is True
        assert check_goal_achievement({"nextTarget": None}, [], "linear") is True

    def test_fewer_than_three_working_sets_is_false(self):
        exercise = {"nextTarget": {"weight": 40.0, "reps": 8}}
        sets = _sets((40.0, 8), (40.0, 8))
        assert check_goal_achievement(exercise, sets, "double") is False

    def test_linear_always_targets_12_reps_regardless_of_target_reps_field(self):
        exercise = {"nextTarget": {"weight": 40.0, "reps": 8}}  # reps field ignored for linear
        sets = _sets((40.0, 8), (40.0, 8), (40.0, 8))
        assert check_goal_achievement(exercise, sets, "linear") is False
        sets_12 = _sets((40.0, 12), (40.0, 12), (40.0, 12))
        assert check_goal_achievement(exercise, sets_12, "linear") is True

    def test_double_uses_target_reps_field(self):
        exercise = {"nextTarget": {"weight": 40.0, "reps": 10}}
        sets = _sets((40.0, 9), (40.0, 9), (40.0, 9))
        assert check_goal_achievement(exercise, sets, "double") is False
        sets_ok = _sets((40.0, 10), (40.0, 10), (40.0, 10))
        assert check_goal_achievement(exercise, sets_ok, "double") is True

    def test_only_first_three_working_sets_considered(self):
        exercise = {"nextTarget": {"weight": 40.0, "reps": 8}}
        # first three fail, a 4th set passing must not matter
        sets = _sets((40.0, 5), (40.0, 5), (40.0, 5), (40.0, 20))
        assert check_goal_achievement(exercise, sets, "double") is False

    def test_non_normal_sets_are_excluded_before_counting(self):
        exercise = {"nextTarget": {"weight": 40.0, "reps": 8}}
        sets = [
            {"type": "warmup", "weight": 20, "reps": 20},
            {"type": "normal", "weight": 40.0, "reps": 8},
            {"type": "normal", "weight": 40.0, "reps": 8},
            {"type": "normal", "weight": 40.0, "reps": 8},
        ]
        assert check_goal_achievement(exercise, sets, "double") is True

    def test_weight_below_target_fails_even_with_enough_reps(self):
        exercise = {"nextTarget": {"weight": 40.0, "reps": 8}}
        sets = _sets((35.0, 20), (35.0, 20), (35.0, 20))
        assert check_goal_achievement(exercise, sets, "double") is False

    def test_malformed_target_data_defaults_to_true(self):
        exercise = {"nextTarget": {"weight": "not-a-number"}}
        sets = _sets((40.0, 8), (40.0, 8), (40.0, 8))
        assert check_goal_achievement(exercise, sets, "double") is True

    def test_malformed_set_data_defaults_to_true(self):
        exercise = {"nextTarget": {"weight": 40.0, "reps": 8}}
        sets = [
            {"type": "normal", "weight": "oops", "reps": 8},
            {"type": "normal", "weight": 40.0, "reps": 8},
            {"type": "normal", "weight": 40.0, "reps": 8},
        ]
        assert check_goal_achievement(exercise, sets, "double") is True


# ---------------------------------------------------------------------------
# calculate_one_rep_max
# ---------------------------------------------------------------------------

class TestCalculateOneRepMax:
    def test_empty_sets_returns_zero(self):
        assert calculate_one_rep_max([]) == 0.0

    def test_single_rep_returns_weight_directly(self):
        assert calculate_one_rep_max([{"weight": 100.0, "reps": 1}]) == 100.0

    def test_multi_rep_uses_epley_formula(self):
        result = calculate_one_rep_max([{"weight": 100.0, "reps": 5}])
        assert result == 100.0 * (1 + 5 / 30)

    def test_zero_reps_contributes_zero(self):
        assert calculate_one_rep_max([{"weight": 100.0, "reps": 0}]) == 0.0

    def test_zero_weight_contributes_zero(self):
        assert calculate_one_rep_max([{"weight": 0.0, "reps": 10}]) == 0.0

    def test_negative_reps_contributes_zero(self):
        assert calculate_one_rep_max([{"weight": 100.0, "reps": -1}]) == 0.0

    def test_picks_the_maximum_across_multiple_sets(self):
        sets = [
            {"weight": 40.0, "reps": 10},
            {"weight": 60.0, "reps": 3},
            {"weight": 20.0, "reps": 1},
        ]
        expected = max(
            40.0 * (1 + 10 / 30),
            60.0 * (1 + 3 / 30),
            20.0,
        )
        assert calculate_one_rep_max(sets) == expected

    def test_invalid_weight_is_skipped_not_crashed(self):
        sets = [{"weight": "not-a-number", "reps": 10}, {"weight": 50.0, "reps": 5}]
        result = calculate_one_rep_max(sets)
        assert result == 50.0 * (1 + 5 / 30)

    def test_invalid_reps_is_skipped_not_crashed(self):
        sets = [{"weight": 50.0, "reps": "not-a-number"}, {"weight": 30.0, "reps": 5}]
        result = calculate_one_rep_max(sets)
        assert result == 30.0 * (1 + 5 / 30)

    def test_missing_fields_default_to_zero_and_are_skipped(self):
        assert calculate_one_rep_max([{}]) == 0.0
