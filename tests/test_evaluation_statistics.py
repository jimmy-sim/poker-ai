import math

import numpy as np
import pytest

from poker_ai.evaluation.statistics import summarize_pairs


def test_duplicate_cancellation_is_not_counted_as_two_independent_hands() -> None:
    result = summarize_pairs(
        np.array([[2.0, -2.0], [4.0, -4.0], [-6.0, 6.0]]), big_blind=2, maximum_loss=200
    )
    assert result["mbb_per_hand"] == 0
    assert result["paired_to_unpaired_variance_ratio"] == 0
    assert result["empirical_zero_variance"]
    assert result["hoeffding_interval_mbb_per_hand"][0] < 0
    assert result["hoeffding_interval_mbb_per_hand"][1] > 0
    assert not result["positive_mean_significant"]


def test_positive_covariance_can_increase_variance() -> None:
    result = summarize_pairs(
        np.array([[0.0, 2.0], [2.0, 4.0], [4.0, 6.0]]), big_blind=2, maximum_loss=200
    )
    assert result["mean_chips_per_hand"] == 3
    assert result["mbb_per_hand"] == 1500
    assert result["cluster_se_mbb_per_hand"] == pytest.approx(500 * math.sqrt(4 / 3))
    assert result["paired_to_unpaired_variance_ratio"] == pytest.approx(2)


def test_declared_family_changes_the_positive_mean_test() -> None:
    data = np.full((100, 2), 60.0)
    one = summarize_pairs(data, big_blind=2, maximum_loss=200)
    five = summarize_pairs(data, big_blind=2, maximum_loss=200, family_size=5)
    assert one["two_sided_p_bound"] == pytest.approx(2 * math.exp(-4.5))
    assert one["positive_mean_significant"]
    assert not five["positive_mean_significant"]
    assert five["family_adjusted_two_sided_p_bound"] == pytest.approx(
        5 * 2 * math.exp(-4.5)
    )


def test_unbounded_or_single_deal_inputs_fail() -> None:
    for data in (
        np.zeros((1, 2)),
        np.array([[201.0, 0], [0, 0]]),
        np.full((2, 2), np.nan),
    ):
        with pytest.raises(ValueError):
            summarize_pairs(data, big_blind=2, maximum_loss=200)


def test_tiny_tail_bound_keeps_positive_display_and_correct_direction() -> None:
    result = summarize_pairs(
        np.full((100000, 2), -200.0), big_blind=2, maximum_loss=200
    )
    assert result["two_sided_p_bound"] > 0
    assert result["log_two_sided_p_bound"] < -1000
    assert result["nonzero_mean_significant"]
    assert not result["positive_mean_significant"]
