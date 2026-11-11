"""Independent tiny controls for frozen-turn continuation diagnostics."""

import itertools
from dataclasses import replace
from typing import Any

import numpy as np
import pytest

from poker_ai.evaluation.turn_continuation_math import continuations, masked_reply
from poker_ai.finite import ArrayTree, FloatArray
from poker_ai.postflop.collision_diagnosis import conditional_actions
from poker_ai.postflop.controlled_scoring import BoolArray, ScoringContext
from poker_ai.postflop.reply_trace import response_profile


def signal_turn(target: int = 0) -> ScoringContext:
    """Hidden type becomes observable on river; own TURN info stays shared.

    Call pays [6,-2] in type0 and [-4,2] in type1. Fold pays0. Saved call
    probability1/2 and uniform rivers give root1/4. Shared river chooses action0
    (call value1, root1/2); fine river chooses0/1 (call value4, root2).
    Full reply also calls with certainty, worth4. Fictional, not poker evidence.
    """
    children = np.zeros((11, 2), dtype=np.int64)
    children[0], children[1], children[2] = (1, 2), (3, 5), (4, 6)
    children[5], children[6] = (7, 8), (9, 10)
    valid = np.zeros((11, 2), dtype=np.bool_)
    valid[[0, 1, 2, 5, 6]] = True
    chance = np.zeros((11, 2))
    chance[0] = (0.5, 0.5)
    fine = ArrayTree(
        children,
        valid,
        np.array([-1, target, target, -2, -2, target, target, -2, -2, -2, -2]),
        np.array([-1, 0, 0, -1, -1, 1, 2, -1, -1, -1, -1]),
        ("turn", "river0", "river1"),
        ((0, 1),) * 3,
        np.full(3, target, dtype=np.int64),
        np.ones((3, 2)),
        chance,
        np.array([1.0] + [0.5] * 10),
        (1 if target == 0 else -1) * np.array([0.0, 0, 0, 0, 0, 0, 0, 6, -2, -4, 2]),
        (np.array([0]), np.array([1, 2]), np.array([5, 6])),
    )
    mapping = np.array([0, 1, 1], dtype=np.int64)
    info = fine.information.copy()
    active = fine.player >= 0
    info[active] = mapping[info[active]]
    coarse = replace(
        fine,
        information=info,
        keys=("turn", "river_shared"),
        actions=((0, 1),) * 2,
        owners=np.full(2, target, dtype=np.int64),
        legal=np.ones((2, 2)),
    )
    own_river = np.array([False, True, True])
    empty = np.zeros(3, dtype=np.bool_)
    masks = (own_river, empty) if target == 0 else (empty, own_river)
    return ScoringContext(fine, coarse, mapping, masks)


def scalar_value(tree: ArrayTree, policy: FloatArray, node: int = 0) -> float:
    """Independent recursive terminal sum; no DP/reaches/library value call."""
    actor = int(tree.player[node])
    if actor == -2:
        return float(tree.terminal_values[node])
    weights = tree.chance_edges[node] if actor == -1 else policy[tree.information[node]]
    return sum(
        float(weights[a]) * scalar_value(tree, policy, int(tree.children[node, a]))
        for a in range(len(weights))
        if tree.valid[node, a]
    )


def enumerate_masked(
    tree: ArrayTree, policy: FloatArray, target: int, mask: BoolArray
) -> float:
    rows = np.flatnonzero(mask)
    values = []
    for choices in itertools.product(*(tree.actions[i] for i in rows)):
        p = policy.copy()
        for info, choice in zip(rows, choices, strict=True):
            p[info] = 0
            p[info, choice] = 1
        values.append((1 if target == 0 else -1) * scalar_value(tree, p))
    return max(values)


@pytest.mark.parametrize("target", [0, 1])
def test_closed_form_four_panels_and_independent_pure_enumeration(target: int) -> None:
    context = signal_turn(target)
    saved = np.full((2, 2), 0.5)
    before = saved.tobytes()
    result = continuations(context, saved, target)
    assert result.root_values == (0.25, 0.5, 2.0, 4.0)
    assert result.increments == (0.25, 1.5, 2.0)
    assert result.maximum_error == 0
    assert saved.tobytes() == before
    assert result.conditional_values[0][0].tolist() == [0.0, 0.5]
    assert result.conditional_values[1][0].tolist() == [0.0, 1.0]
    assert result.conditional_values[2][0].tolist() == [0.0, 4.0]
    for tree, p, mask, expected in (
        (context.partition, saved, np.array([False, True]), 0.5),
        (context.exact, context.expand(saved), context.river_masks[target], 2.0),
        (context.exact, context.expand(saved), context.exact.owners == target, 4.0),
    ):
        assert enumerate_masked(tree, p, target, mask) == expected
        actual = masked_reply(tree, p, target, mask)
        assert (1 if target == 0 else -1) * scalar_value(tree, actual) == expected
    # A restricted river is not allowed to choose separately by hidden type.
    assert result.policies[1][1:].tolist() == [[1.0, 0.0], [1.0, 0.0]]
    assert result.policies[2][1:].tolist() == [[1.0, 0.0], [0.0, 1.0]]


def fork(target: int = 0, opponent_root: bool = False) -> ArrayTree:
    children = np.zeros((7, 2), dtype=np.int64)
    children[0], children[1], children[4] = (1, 4), (2, 3), (5, 6)
    valid = np.zeros((7, 2), dtype=np.bool_)
    valid[[0, 1, 4]] = True
    root_actor = 1 - target if opponent_root else target
    return ArrayTree(
        children,
        valid,
        np.array([root_actor, target, -2, -2, target, -2, -2]),
        np.array([0, 1, -1, -1, 2, -1, -1]),
        ("root", "left", "right"),
        ((0, 1),) * 3,
        np.array([root_actor, target, target]),
        np.ones((3, 2)),
        np.zeros((7, 2)),
        np.ones(7),
        (1 if target == 0 else -1) * np.array([0.0, 0, 0, 4, 0, 3, 2]),
        (np.array([0]), np.array([1, 4])),
    )


def test_shared_river_root_improvement_can_hurt_a_finer_turn_action_value() -> None:
    original = signal_turn()
    # The fine own view knows its type on TURN too. The restricted view merges
    # both turn types and hence has the same own remembered history on river.
    fine = replace(
        original.exact,
        information=np.array([-1, 0, 1, -1, -1, 2, 3, -1, -1, -1, -1]),
        keys=("turn0", "turn1", "river0", "river1"),
        actions=((0, 1),) * 4,
        owners=np.zeros(4, dtype=np.int64),
        legal=np.ones((4, 2)),
    )
    context = ScoringContext(
        fine,
        original.partition,
        np.array([0, 0, 1, 1]),
        (np.array([False, False, True, True]), np.zeros(4, dtype=np.bool_)),
    )
    result = continuations(context, np.full((2, 2), 0.5), 0)
    assert result.root_values == (0.25, 0.5, 2.0, 4.0)
    assert result.conditional_values[0][1, 1] == -1
    assert result.conditional_values[1][1, 1] == -4
    assert result.conditional_values[2][1, 1] == 2


@pytest.mark.parametrize("target", [0, 1])
def test_generic_mask_does_not_slice_full_reply_with_unselected_future(
    target: int,
) -> None:
    tree = fork(target)
    saved = np.array([[0.5, 0.5], [1.0, 0.0], [1.0, 0.0]])
    mask = np.array([True, False, False])
    actual = masked_reply(tree, saved, target, mask)
    full = response_profile(tree, saved, target)
    shortcut = saved.copy()
    shortcut[mask] = full[mask]
    assert actual[0].tolist() == [0.0, 1.0]
    assert shortcut[0].tolist() == [1.0, 0.0]
    assert (1 if target == 0 else -1) * scalar_value(tree, actual) == 3
    assert (1 if target == 0 else -1) * scalar_value(tree, shortcut) == 0
    assert enumerate_masked(tree, saved, target, mask) == 3
    assert actual[~mask].tobytes() == saved[~mask].tobytes()


@pytest.mark.parametrize("target", [0, 1])
def test_zero_opponent_support_is_zero_and_opponent_unchanged(target: int) -> None:
    tree = fork(target, opponent_root=True)
    saved = np.array([[0.0, 1.0], [0.0, 1.0], [0.5, 0.5]])
    actual = masked_reply(tree, saved, target, np.array([False, True, True]))
    q, support = conditional_actions(tree, actual)
    assert actual[0].tobytes() == saved[0].tobytes()
    assert actual[1].tolist() == [1.0, 0.0]  # First legal exact zero-support tie.
    assert support[1] == 0 and q[1].tolist() == [0.0, 0.0]
    assert (1 if target == 0 else -1) * scalar_value(tree, actual) == 3


def test_exact_tie_rule_does_not_round_a_small_strict_improvement() -> None:
    tree = fork()
    terminal = tree.terminal_values.copy()
    terminal[2:4] = [1.0, 1.0 + 1e-14]
    tree = replace(tree, terminal_values=terminal)
    saved = np.array([[1.0, 0.0], [1.0, 0.0], [0.5, 0.5]])
    actual = masked_reply(tree, saved, 0, np.array([False, True, True]))
    assert actual[1].tolist() == [0.0, 1.0]


@pytest.mark.parametrize(
    "change", ["dtype", "shape", "seat", "target", "nan", "negative", "recall"]
)
def test_mask_policy_and_recall_guards(change: str) -> None:
    tree = fork(opponent_root=True)
    saved = np.full((3, 2), 0.5)
    mask: Any = np.array([False, True, True])
    target: Any = 0
    if change == "dtype":
        mask = np.array([0, 1, 1])
    elif change == "shape":
        mask = np.array([True])
    elif change == "seat":
        mask[0] = True
    elif change == "target":
        target = True
    elif change == "nan":
        saved[1, 0] = np.nan
    elif change == "negative":
        saved[1] = [-1, 2]
    else:
        # Merge rows after distinct own histories in an all-own fork.
        tree = fork()
        tree = replace(tree, information=np.array([0, 1, -1, -1, 1, -1, -1]))
    with pytest.raises(ValueError):
        masked_reply(tree, saved, target, mask)


def test_empty_mask_identity_and_fine_self_river_equality() -> None:
    context = signal_turn()
    tree = context.exact
    saved = np.full((3, 2), 0.5)
    assert (
        masked_reply(tree, saved, 0, np.zeros(3, dtype=np.bool_)).tobytes()
        == saved.tobytes()
    )
    fine = ScoringContext(tree, tree, np.arange(3), context.river_masks)
    result = continuations(fine, saved, 0)
    assert result.root_values == (0.25, 2.0, 2.0, 4.0)
    assert result.policies[1].tobytes() == result.policies[2].tobytes()


@pytest.mark.parametrize("tolerance", [0, -1, float("nan"), float("inf"), 1e-8])
def test_bad_tolerance(tolerance: float) -> None:
    with pytest.raises(ValueError):
        continuations(signal_turn(), np.full((2, 2), 0.5), 0, tolerance=tolerance)
