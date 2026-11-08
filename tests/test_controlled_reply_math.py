"""Asymmetric hand-computed hidden-action matrix checks signs and information."""

import itertools
import json
from typing import Any

import numpy as np
import pytest

from poker_ai.evaluation import controlled_reply_math as math
from poker_ai.finite import ArrayTree
from poker_ai.postflop.controlled_training import ControlledTrainer
from poker_ai.postflop.node_profile import trainer
from poker_ai.postflop.training_isolation import sentinel_tree


def asymmetric() -> ArrayTree:
    children = np.zeros((7, 2), dtype=np.int64)
    children[0], children[1], children[4] = (1, 4), (2, 3), (5, 6)
    valid = np.zeros((7, 2), dtype=np.bool_)
    valid[[0, 1, 4]] = True
    return ArrayTree(
        children,
        valid,
        np.array([0, 1, -2, -2, 1, -2, -2]),
        np.array([0, 1, -1, -1, 1, -1, -1]),
        ("player-zero", "player-one-hidden-action"),
        ((0, 1),) * 2,
        np.array([0, 1]),
        np.ones((2, 2)),
        np.zeros((7, 2)),
        np.ones(7),
        np.array([0, 0, 3, -1, 0, -2, 2], dtype=np.float64),
        (np.array([0]), np.array([1, 4])),
    )


def policy(p0: float, p1: float) -> np.ndarray[Any, np.dtype[np.float64]]:
    return np.array([[p0, 1 - p0], [p1, 1 - p1]])


def expected_value(p0: float, p1: float) -> float:
    return (
        p0 * p1 * 3
        + p0 * (1 - p1) * (-1)
        + (1 - p0) * p1 * (-2)
        + (1 - p0) * (1 - p1) * 2
    )


def test_manual_hidden_information_trace_and_telescope() -> None:
    tree = asymmetric()
    saved = policy(0.8, 0.3)
    before = saved.tobytes()
    first, _, a = math.trace(tree, saved, 0, ("TURN", "RIVER"), 1e-9)
    second, _, b = math.trace(tree, saved, 1, ("TURN", "RIVER"), 1e-9)
    assert math.value(tree, saved) == pytest.approx(0.32)
    assert first.value == pytest.approx(0.8)
    assert first.gain == pytest.approx(0.48)
    assert second.value == pytest.approx(0.4)
    assert second.gain == pytest.approx(0.72)
    assert b["street_losses_chips"]["RIVER"] == pytest.approx(0.72)
    assert a["street_losses_chips"]["TURN"] == pytest.approx(0.48)
    np.testing.assert_allclose(second.conditional_values[1], [-2, 0.4], atol=1e-12)
    # Maximizing separately after the hidden first action would incorrectly give 1.2.
    assert second.value != pytest.approx(1.2)
    assert (first.gain + second.gain) / 2 == pytest.approx(0.6)
    assert saved.tobytes() == before


def test_all_crosses_hold_opponent_roots_and_target_ev_identity() -> None:
    tree = asymmetric()
    probabilities = [(0.8, 0.3), (0.2, 0.9), (0.6, 0.7), (0.1, 0.4)]
    policies = [policy(*p) for p in probabilities]
    replies = {
        (i, t): math.trace(tree, p, t, ("TURN", "RIVER"), 1e-9)[1]
        for i, p in enumerate(policies)
        for t in (0, 1)
    }
    results = {}
    for i, j in itertools.product(range(4), repeat=2):
        result = math.cross(
            tree, policies[i], policies[j], replies[j, 0], replies[i, 1], tolerance=1e-9
        )
        results[i, j] = result
        p0, p1 = probabilities[i][0], probabilities[j][1]
        assert result["value_player_zero_chips"] == pytest.approx(
            expected_value(p0, p1)
        )
        assert result["responses"][0]["restricted_reply_value_chips"] == pytest.approx(
            max(4 * p1 - 1, 2 - 4 * p1)
        )
        assert result["responses"][1]["restricted_reply_value_chips"] == pytest.approx(
            max(2 - 5 * p0, 3 * p0 - 2)
        )
        assert sum(r["baseline_value_chips"] for r in result["responses"]) == 0
    assert (
        results[0, 1]["value_player_zero_chips"]
        != -results[1, 0]["value_player_zero_chips"]
    )
    for opponent in range(4):
        for first, second in itertools.product(range(4), repeat=2):
            for target in (0, 1):
                a = (
                    results[first, opponent]
                    if target == 0
                    else results[opponent, first]
                )
                b = (
                    results[second, opponent]
                    if target == 0
                    else results[opponent, second]
                )
                ra, rb = a["responses"][target], b["responses"][target]
                assert (
                    ra["restricted_reply_value_chips"]
                    == rb["restricted_reply_value_chips"]
                )
                assert rb["gain_chips"] - ra["gain_chips"] == pytest.approx(
                    -(rb["baseline_value_chips"] - ra["baseline_value_chips"]),
                    abs=1e-12,
                )


@pytest.mark.parametrize("choice", [(-1,), (2,), (True,), (), (0, 1)])
def test_compact_reply_refuses_invalid_columns_or_owner_inventory(
    choice: tuple[int, ...],
) -> None:
    with pytest.raises(ValueError):
        math.Reply(0, 0.0, choice).apply(asymmetric(), policy(0.8, 0.3))


@pytest.mark.parametrize("tolerance", [0, -1, True, float("nan"), float("inf"), 1e-8])
def test_bad_tolerances_do_not_silently_admit_broken_math(tolerance: float) -> None:
    tree, saved = asymmetric(), policy(0.8, 0.3)
    with pytest.raises(ValueError):
        math.trace(tree, saved, 0, ("TURN", "RIVER"), tolerance)


@pytest.mark.parametrize(
    "traversal,clip,rw,warm",
    list(
        itertools.product(
            ["full", "external"],
            ["signed", "clipped"],
            ["uniform", "linear"],
            [False, True],
        )
    ),
)
def test_average_weights_do_not_change_raw_learning_trajectory(
    traversal: str,
    clip: str,
    rw: str,
    warm: bool,
) -> None:
    tree = sentinel_tree()
    solvers: list[ControlledTrainer] = []
    for average in ("uniform", "linear"):
        cell = dict(
            traversal=traversal,
            seed=20261301,
            bridge="common",
            regret_rule=clip,
            regret_weight=rw,
            average_weight=average,
        )
        solver = trainer(tree, cell, "nodes" if traversal == "external" else "parent")
        if warm:
            solver.initialize_exact()
        solvers.append(solver)
    a, b = solvers
    for _ in range(64):
        a.step()
        b.step()
        assert a.regrets.tobytes() == b.regrets.tobytes()
        assert a.current_policy.tobytes() == b.current_policy.tobytes()
        assert json.dumps(a.rng.bit_generator.state, sort_keys=True) == json.dumps(
            b.rng.bit_generator.state, sort_keys=True
        )
        assert (a.nodes_visited, a.iteration, a.sampled_keys) == (
            b.nodes_visited,
            b.iteration,
            b.sampled_keys,
        )
    assert a.strategy_sum.tobytes() != b.strategy_sum.tobytes()
