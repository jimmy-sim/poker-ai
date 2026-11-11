"""Independent finite-mixture controls; fictional units, no poker learning."""

from dataclasses import replace
from typing import Any

import numpy as np
import pytest

from poker_ai.evaluation.river_range_math import (
    conflict,
    decompose,
    local_group,
    total_variation,
)
from poker_ai.finite import ArrayTree, FloatArray


def fixture(target: int = 0) -> tuple[ArrayTree, FloatArray, Any, Any, Any, FloatArray]:
    """Chance prior1:3; opponent bets4/5 vs1/5; actor cannot see the combo.

    Posterior after bet is4/7:3/7. Action values by combo are[4,0] and[0,2].
    Correct actual Q=[16/7,6/7], compatible-prior Q=[1,3/2]. The preference
    changes because weights change, not because the actor sees the hidden deal.
    """
    children = np.zeros((11, 2), dtype=np.int64)
    children[0], children[1], children[2] = (1, 2), (3, 4), (5, 6)
    children[4], children[6] = (7, 8), (9, 10)
    valid = np.zeros((11, 2), dtype=np.bool_)
    valid[[0, 1, 2, 4, 6]] = True
    chance = np.zeros((11, 2))
    chance[0] = [0.25, 0.75]
    opponent = 1 - target
    tree = ArrayTree(
        children,
        valid,
        np.array([-1, opponent, opponent, -2, target, -2, target, -2, -2, -2, -2]),
        np.array([-1, 1, 2, -1, 0, -1, 0, -1, -1, -1, -1]),
        ("own/shared_river", "opponent/combo0", "opponent/combo1"),
        ((0, 1),) * 3,
        np.array([target, opponent, opponent]),
        np.ones((3, 2)),
        chance,
        np.array([1, 0.25, 0.75, 0.25, 0.25, 0.75, 0.75, 0.25, 0.25, 0.75, 0.75]),
        (1 if target == 0 else -1) * np.array([0.0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 2]),
        (np.array([0]), np.array([1, 2]), np.array([4, 6])),
    )
    profile = np.array([[0.5, 0.5], [0.2, 0.8], [0.8, 0.2]])
    river = np.array([True, False, False])
    combos = np.full(11, -1, dtype=np.int64)
    combos[[4, 6]] = [0, 1]
    compatible = np.zeros((3, 2), dtype=np.bool_)
    compatible[0] = True
    return tree, profile, river, combos, compatible, np.array([1.0, 3.0])


def scalar(tree: ArrayTree, policy: FloatArray, node: int = 0) -> float:
    """Independent recursive terminal sum, no matrix/DP/conditional helper."""
    actor = int(tree.player[node])
    if actor == -2:
        return float(tree.terminal_values[node])
    p = tree.chance_edges[node] if actor == -1 else policy[tree.information[node]]
    return sum(
        float(p[a]) * scalar(tree, policy, int(tree.children[node, a]))
        for a in range(2)
        if tree.valid[node, a]
    )


@pytest.mark.parametrize("target", [0, 1])
def test_analytic_posterior_and_independent_terminal_deviations(target: int) -> None:
    args = fixture(target)
    tree, profile, *_ = args
    before = profile.tobytes()
    result = decompose(tree, profile, target, *args[2:])
    np.testing.assert_allclose(result.posterior[0], [4 / 7, 3 / 7], atol=1e-15, rtol=0)
    np.testing.assert_allclose(result.prior[0], [0.25, 0.75], atol=1e-15, rtol=0)
    np.testing.assert_allclose(
        result.actual_values[0], [16 / 7, 6 / 7], atol=1e-15, rtol=0
    )
    np.testing.assert_allclose(result.prior_values[0], [1, 1.5], atol=1e-15, rtol=0)
    assert np.argmax(result.actual_values[0]) == 0
    assert np.argmax(result.prior_values[0]) == 1
    assert result.support[0] == pytest.approx(7 / 20)
    assert result.uniform_weights.tolist() == [1.0, 0.0, 0.0]
    for action in (0, 1):
        p = profile.copy()
        p[0] = 0
        p[0, action] = 1
        actual = (1 if target == 0 else -1) * scalar(tree, p) / (7 / 20)
        assert actual == pytest.approx(result.actual_values[0, action], abs=1e-15)
        # In this tiny fixture, equal betting likelihood reproduces the prior
        # via an independently summed complete terminal tree.
        p[1:] = 0.5
        prior = (1 if target == 0 else -1) * scalar(tree, p) / 0.5
        assert prior == pytest.approx(result.prior_values[0, action], abs=1e-15)
    clairvoyant = float(result.posterior[0] @ result.combo_values[0].max(axis=1))
    assert clairvoyant > result.actual_values[0].max()
    assert profile.tobytes() == before
    assert all(
        not a.flags.writeable
        for a in (
            result.posterior,
            result.prior,
            result.combo_values,
            result.actual_values,
            result.prior_values,
            result.support,
            result.uniform_weights,
        )
    )


def test_own_prefix_reach_does_not_change_posterior_or_conditional_values() -> None:
    tree, p, river, combos, compatible, prior = fixture()
    n = len(tree.player)
    children = np.zeros((n + 2, 2), dtype=np.int64)
    children[0] = [1, 2]
    children[2:] = np.where(tree.valid, tree.children + 2, 0)
    valid = np.vstack(([True, True], [False, False], tree.valid))
    extended = replace(
        tree,
        children=children,
        valid=valid,
        player=np.r_[0, -2, tree.player],
        information=np.r_[3, -1, tree.information],
        keys=tree.keys + ("own_turn",),
        actions=tree.actions + ((0, 1),),
        owners=np.r_[tree.owners, 0],
        legal=np.ones((4, 2)),
        chance_edges=np.vstack((np.zeros((2, 2)), tree.chance_edges)),
        chance_reach=np.r_[1.0, 1.0, tree.chance_reach],
        terminal_values=np.r_[0.0, 0.0, tree.terminal_values],
        levels=(np.array([0]),) + tuple(level + 2 for level in tree.levels),
    )
    mask = np.r_[river, False]
    combo = np.r_[-1, -1, combos]
    compat = np.vstack((compatible, [False, False]))
    a = decompose(extended, np.vstack((p, [0.99, 0.01])), 0, mask, combo, compat, prior)
    b = decompose(extended, np.vstack((p, [0.01, 0.99])), 0, mask, combo, compat, prior)
    assert a.posterior.tobytes() == b.posterior.tobytes()
    assert a.support.tobytes() == b.support.tobytes()
    assert a.actual_values.tobytes() == b.actual_values.tobytes()


def test_support_filter_keeps_original_weights_and_explicit_zero_rows() -> None:
    tree, p, river, combos, compatible, prior = fixture()
    info = tree.information.copy()
    info[6] = 3
    tree = replace(
        tree,
        information=info,
        keys=tree.keys + ("own/public_signal1",),
        actions=tree.actions + ((0, 1),),
        owners=np.r_[tree.owners, 0],
        legal=np.ones((4, 2)),
    )
    p = np.vstack((p, [0.5, 0.5]))
    p[2] = [1.0, 0.0]
    river = np.r_[river, True]
    compatible = np.zeros((4, 2), dtype=np.bool_)
    compatible[0, 0] = compatible[3, 1] = True
    r = decompose(tree, p, 0, river, combos, compatible, prior)
    assert r.uniform_weights.tolist() == [0.25, 0, 0, 0.75]
    assert r.uniform_weights[r.support > 0].sum() == 0.25
    assert r.support[3] == 0 and r.posterior[3].tolist() == [0.0, 0.0]
    assert r.actual_values[3].tolist() == [0.0, 0.0]
    assert r.prior[3].tolist() == [0.0, 1.0] and r.prior_values[3].tolist() == [
        0.0,
        2.0,
    ]


@pytest.mark.parametrize(
    "change",
    [
        "combo_index",
        "combo_dtype",
        "blocker",
        "prior_zero",
        "prior_nan",
        "prior_dtype",
        "prior_order",
        "mask_owner",
        "mask_dtype",
        "mask_shape",
        "target",
        "policy",
        "alias_values",
    ],
)
def test_bad_range_history_support_or_policy_is_rejected(change: str) -> None:
    tree, p, river, combos, compatible, prior = fixture()
    target: Any = 0
    if change == "combo_index":
        combos[4] = 2
    elif change == "combo_dtype":
        combos = combos.astype(np.int32)
    elif change == "blocker":
        compatible[0, 1] = False
    elif change == "prior_zero":
        prior[0] = 0
    elif change == "prior_nan":
        prior[0] = np.nan
    elif change == "prior_dtype":
        prior = prior.astype(np.int64)
    elif change == "prior_order":
        prior = prior[::-1]
    elif change == "mask_owner":
        river[1] = True
    elif change == "mask_dtype":
        river = river.astype(np.int64)
    elif change == "mask_shape":
        river = np.array([True])
    elif change == "target":
        target = True
    elif change == "policy":
        p[0, 0] = np.nan
    else:
        # Wrongly identify two distinct payoff worlds as the same physical combo.
        combos[6] = 0
        compatible = compatible[:, :1]
        prior = np.array([1.0])
    with pytest.raises((ArithmeticError, ValueError)):
        decompose(tree, p, target, river, combos, compatible, prior)


def test_same_likelihood_gives_identical_prior_and_posterior_values() -> None:
    tree, p, *rest = fixture()
    p[1:] = 0.5
    r = decompose(tree, p, 0, *rest)
    np.testing.assert_array_equal(r.posterior, r.prior)
    np.testing.assert_array_equal(r.actual_values, r.prior_values)


def test_local_cost_conflicts_refinement_and_range_distance() -> None:
    q = np.array([[4.0, 0.0], [0.0, 2.0]])
    w = np.array([0.25, 0.75])
    r = local_group(q, w)
    assert r == dict(local_cost=1.0, strict_conflict=True, supported_rows=2, weight=1.0)
    assert (
        sum(
            float(local_group(q[i : i + 1], w[i : i + 1])["local_cost"])
            for i in range(2)
        )
        == 0
    )
    assert local_group(np.array([[2.0, 1.0], [2.0, 1.0]]), w)["local_cost"] == 0
    assert not conflict(np.array([[1.0, 1.0 - 5e-10], [0.0, 1.0]]))
    assert conflict(np.array([[1.0, 1.0 - 2e-9], [0.0, 1.0]]))
    assert total_variation(np.array([[0.25, 0.75], [0.75, 0.25]])) == 0.5
    assert total_variation(np.array([[0.25, 0.75], [0.25, 0.75]])) == 0
    assert total_variation(np.array([[0.25, 0.75]])) == 0
    assert local_group(np.zeros((0, 2)), np.zeros(0))["local_cost"] == 0


@pytest.mark.parametrize(
    "q,w",
    [
        (np.array([[np.nan, 0.0]]), np.array([1.0])),
        (np.ones((1, 2)), np.array([-1.0])),
        (np.ones((1, 2)), np.ones(2)),
    ],
)
def test_invalid_local_values_or_weights(q: FloatArray, w: FloatArray) -> None:
    with pytest.raises(ValueError):
        local_group(q, w)


@pytest.mark.parametrize(
    "weights",
    [np.array([[0.2, 0.2]]), np.array([[np.nan, 0.0]]), np.array([[-1.0, 2.0]])],
)
def test_invalid_supported_range_vectors(weights: FloatArray) -> None:
    with pytest.raises(ValueError):
        total_variation(weights)
