"""Hand-computed suffix mass, hidden information and fixed-opponent seat signs."""

import itertools
from typing import Any

import numpy as np
import pytest

from poker_ai.evaluation import averaging_history_math as history
from poker_ai.evaluation.controlled_reply_math import trace
from poker_ai.finite import ArrayTree


def hidden_game() -> ArrayTree:
    children = np.zeros((7, 2), dtype=np.int64)
    children[0], children[1], children[4] = (1, 4), (2, 3), (5, 6)
    valid = np.zeros((7, 2), dtype=np.bool_)
    valid[[0, 1, 4]] = True
    return ArrayTree(
        children,
        valid,
        np.array([0, 1, -2, -2, 1, -2, -2]),
        np.array([0, 1, -1, -1, 1, -1, -1]),
        ("first", "hidden-first-action"),
        ((0, 1),) * 2,
        np.array([0, 1]),
        np.ones((2, 2)),
        np.zeros((7, 2)),
        np.ones(7),
        np.array([0, 0, 3, -1, 0, -2, 2], dtype=np.float64),
        (np.array([0]), np.array([1, 4])),
    )


def test_suffix_removes_warm_mass_and_retains_actual_increment_weights() -> None:
    tree = hidden_game()
    earlier = np.array([[1.0, 1.0], [3.0, 1.0]])
    # Later contributions already carry their original time weights, not a reset.
    later = np.array([[1.0, 1.0], [3.0, 4.0]])
    before = earlier.tobytes(), later.tobytes()
    mass = history.window_mass(tree, earlier, later)
    np.testing.assert_array_equal(mass, [[0, 0], [0, 3]])
    np.testing.assert_array_equal(tree.normalize(mass), [[0.5, 0.5], [0, 1]])
    assert not mass.flags.writeable
    assert (earlier.tobytes(), later.tobytes()) == before
    report = history.coverage(tree, mass, np.array([False, True]))
    assert report["all"] == dict(
        rows=2, positive_rows=1, row_fraction=0.5, uniform_reach_fraction=0.5
    )
    assert report["river"] == dict(
        rows=1, positive_rows=1, row_fraction=1.0, uniform_reach_fraction=1.0
    )


def test_zero_window_keeps_uniform_fallback_and_reports_no_support() -> None:
    tree = hidden_game()
    zero = history.window_mass(tree, tree.legal, tree.legal)
    np.testing.assert_array_equal(tree.normalize(zero), tree.normalize(tree.legal))
    report = history.coverage(tree, zero, np.zeros(2, dtype=np.bool_))
    assert report["all"]["uniform_reach_fraction"] == 0
    assert report["river"]["uniform_reach_fraction"] is None


@pytest.mark.parametrize("mode", ["negative", "nan", "infinite", "shape"])
def test_invalid_or_decreasing_cumulative_mass_fails_without_repair(mode: str) -> None:
    tree = hidden_game()
    earlier, later = tree.legal.copy(), tree.legal.copy()
    if mode == "negative":
        later[0, 0] -= 1e-15
    elif mode == "nan":
        later[0, 0] = np.nan
    elif mode == "infinite":
        earlier[0, 0] = np.inf
    else:
        later = later[:1]
    with pytest.raises(ValueError):
        history.window_mass(tree, earlier, later)


def test_current_movement_uses_row_l1_and_uniform_exposure_not_opponent_cards() -> None:
    tree = hidden_game()
    uniform = tree.normalize(tree.legal)
    pure = np.array([[1.0, 0.0], [0.0, 1.0]])
    np.testing.assert_array_equal(history.uniform_information_reach(tree), [1, 1])
    assert history.movement(tree, uniform, uniform) == dict(
        mean_row_l1=0.0, maximum_row_l1=0.0, uniform_reach_weighted_l1=0.0
    )
    assert history.movement(tree, uniform, pure) == dict(
        mean_row_l1=1.0, maximum_row_l1=1.0, uniform_reach_weighted_l1=1.0
    )


@pytest.mark.parametrize("target", [0, 1])
def test_fixed_opponent_manual_signs_root_and_gain_ev_identity(target: int) -> None:
    tree = hidden_game()
    opponent = np.array([[0.8, 0.2], [0.3, 0.7]])
    _, reply, _ = trace(tree, opponent, target, ("TURN", "RIVER"), 1e-9)
    before = opponent.tobytes()
    rows = []
    for first, second in itertools.product((0.2, 0.8), (0.3, 0.9)):
        own = np.array([[first, 1 - first], [second, 1 - second]])
        row = history.fixed_match(tree, own, opponent, reply)
        p0, p1 = (first, 0.3) if target == 0 else (0.8, second)
        ev = p0 * p1 * 3 - p0 * (1 - p1) - (1 - p0) * p1 * 2 + (1 - p0) * (1 - p1) * 2
        assert row["baseline_value_chips"] == pytest.approx((1 - 2 * target) * ev)
        assert row["restricted_reply_value_chips"] == pytest.approx(
            0.8 if target == 0 else 0.4
        )
        # A hidden-history peek would produce 1.2 for seat one, not 0.4.
        assert row["achieved_reply_value_chips"] == pytest.approx(reply.root)
        rows.append(row)
    for row in rows[1:]:
        assert row["gain_chips"] - rows[0]["gain_chips"] == pytest.approx(
            rows[0]["baseline_value_chips"] - row["baseline_value_chips"]
        )
    assert opponent.tobytes() == before


@pytest.mark.parametrize("river", [np.zeros(1, dtype=np.bool_), np.zeros(2)])
def test_window_coverage_rejects_malformed_river_masks(river: Any) -> None:
    tree = hidden_game()
    with pytest.raises(ValueError):
        history.coverage(tree, tree.legal, river)
