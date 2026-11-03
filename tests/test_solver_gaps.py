"""Analytical gap conventions and required strategy-to-itself zero sanity."""

import numpy as np
import pytest

from poker_ai.solver_validation.gaps import (
    action_frequency_gap,
    ev_gap,
    range_frequencies,
)


def test_strategy_self_comparison_yields_zero_action_and_ev_gap() -> None:
    policy = np.array([[0.2, 0.8, 0], [0.1, 0.3, 0.6]])
    legal = np.array([[True, True, False], [True, True, True]])
    reach = np.array([0.2, 0.8])
    assert action_frequency_gap(policy, policy, reach, legal) == 0
    result = ev_gap(np.array([2.0, -3.0]), np.array([2.0, -3.0]), reach)
    assert result.signed == result.mean_absolute == 0


def test_per_node_legal_action_counts_and_reach_weights_are_correct() -> None:
    first = np.array([[1.0, 0, 0], [0.5, 0.5, 0]])
    second = np.array([[0.0, 1, 0], [0.25, 0.25, 0.5]])
    legal = np.array([[True, True, False], [True, True, True]])
    reach = np.array([1.0, 3.0])
    # Node MAEs are 1 and 1/3; weighted mean is .25*1+.75*(1/3)=.5.
    assert action_frequency_gap(first, second, reach, legal) == pytest.approx(0.5)
    assert action_frequency_gap(first, second, 100 * reach, legal) == pytest.approx(0.5)
    np.testing.assert_allclose(
        range_frequencies(first, reach, legal), [0.625, 0.375, 0]
    )
    np.testing.assert_allclose(
        range_frequencies(second, reach, legal), [0.1875, 0.4375, 0.375]
    )


def test_signed_and_absolute_ev_gaps_are_not_conflated() -> None:
    gap = ev_gap(np.array([2.0, -2.0]), np.array([0.0, 0.0]), np.array([1.0, 3.0]))
    assert gap.signed == -1 and gap.mean_absolute == 2


@pytest.mark.parametrize(
    "bad", ["negative", "zero_reach", "nan", "illegal", "unnormalized"]
)
def test_invalid_metric_inputs_are_rejected(bad: str) -> None:
    p = np.array([[0.5, 0.5, 0.0]])
    legal = np.array([[True, True, False]])
    reach = np.array([1.0])
    if bad == "negative":
        reach[0] = -1
    elif bad == "zero_reach":
        reach[0] = 0
    elif bad == "nan":
        p[0, 0] = np.nan
    elif bad == "illegal":
        p[0] = [0.25, 0.25, 0.5]
    else:
        p[0] = [0.2, 0.2, 0]
    with pytest.raises(ValueError):
        action_frequency_gap(p, p, reach, legal)
