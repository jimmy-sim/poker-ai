"""Hand-computed hidden-world gains check units, signs and river semantics."""

from dataclasses import replace

import numpy as np
import pytest

from poker_ai.finite import ArrayTree
from poker_ai.postflop.controlled_scoring import ScoringContext


def hidden_context(target: int = 0, *, river: bool = True) -> ScoringContext:
    # Chance left/right=.25/.75. Target payoffs left=(4,0), right=(0,2).
    # Uniform target EV=1.25; restricted BR=1.5; revealed BR=2.5.
    children = np.zeros((7, 2), dtype=np.int64)
    children[0], children[1], children[4] = (1, 4), (2, 3), (5, 6)
    valid = np.zeros((7, 2), dtype=np.bool_)
    valid[[0, 1, 4]] = True
    edges = np.zeros((7, 2))
    edges[0] = (0.25, 0.75)
    limited = ArrayTree(
        children,
        valid,
        np.array([-1, target, -2, -2, target, -2, -2]),
        np.array([-1, 0, -1, -1, 0, -1, -1]),
        ("limited",),
        ((0, 1),),
        np.array([target]),
        np.ones((1, 2)),
        edges,
        np.array([1, 0.25, 0.25, 0.25, 0.75, 0.75, 0.75]),
        np.array([0, 0, 4, 0, 0, 0, 2], dtype=np.float64) * (1 if target == 0 else -1),
        (np.array([0]), np.array([1, 4])),
    )
    exact = replace(
        limited,
        information=np.array([-1, 0, -1, -1, 1, -1, -1]),
        keys=("left", "right"),
        actions=((0, 1),) * 2,
        owners=np.array([target, target]),
        legal=np.ones((2, 2)),
    )
    masks = tuple(
        np.full(2, river and owner == target, dtype=np.bool_) for owner in (0, 1)
    )
    return ScoringContext(exact, limited, np.array([0, 0]), (masks[0], masks[1]))


@pytest.mark.parametrize("target", [0, 1])
def test_hand_computed_seat_balanced_hidden_world_gains(target: int) -> None:
    context = hidden_context(target)
    policy = np.array([[0.5, 0.5]])
    before = policy.tobytes()
    result = context.score(policy)
    assert policy.tobytes() == before
    assert result.metrics == {
        "exact_exploitability_chips": 0.625,
        "within_partition_gain_chips": 0.125,
        "extra_information_gap_chips": 0.5,
        "river_only_gain_exact_prefix_chips": 0.5,
        "value_player_zero_chips": 1.25 if target == 0 else -1.25,
    }
    assert result.maximum_accounting_error == 0
    assert result.responses[target]["exact_reply_value_chips"] == 2.5
    assert result.responses[target]["restricted_reply_value_chips"] == 1.5
    for row in result.replies:
        for profile in row.values():
            context.exact.validate_policy(profile)


def test_exact_encoding_has_no_extra_information_or_river_gap() -> None:
    old = hidden_context()
    context = ScoringContext(old.exact, old.exact, np.arange(2), old.river_masks)
    result = context.score(np.full((2, 2), 0.5))
    assert result.metrics["exact_exploitability_chips"] == 0.625
    assert result.metrics["within_partition_gain_chips"] == 0.625
    assert result.metrics["extra_information_gap_chips"] == 0
    assert result.metrics["river_only_gain_exact_prefix_chips"] == 0


def test_no_river_is_zero_switch_and_optimal_restricted_has_zero_within_gain() -> None:
    context = hidden_context(river=False)
    result = context.score(np.array([[0.0, 1.0]]))
    assert result.metrics["within_partition_gain_chips"] == 0
    assert result.metrics["extra_information_gap_chips"] == 0.5
    assert result.metrics["river_only_gain_exact_prefix_chips"] == 0


@pytest.mark.parametrize(
    "change", ["mapping", "payoff", "menu", "owner", "street", "mask_owner"]
)
def test_reject_context_that_changes_game_or_information_contract(change: str) -> None:
    context = hidden_context()
    exact, limited, mapping, masks = (
        context.exact,
        context.partition,
        context.exact_to_partition,
        context.river_masks,
    )
    if change == "mapping":
        mapping = np.array([0, 1])
    elif change == "payoff":
        limited = replace(limited, terminal_values=limited.terminal_values + 1)
    elif change == "menu":
        limited = replace(limited, actions=((1, 0),))
    elif change == "owner":
        limited = replace(limited, owners=np.array([1]))
    elif change == "street":
        masks = (np.array([True, False]), masks[1])
    else:
        masks = (masks[0], np.ones(2, dtype=np.bool_))
    with pytest.raises(ValueError):
        ScoringContext(exact, limited, mapping, masks)


@pytest.mark.parametrize("tolerance", [0, -1, 1e-8, float("nan"), True])
def test_reject_invalid_score_tolerance(tolerance: float) -> None:
    with pytest.raises(ValueError):
        hidden_context().score(np.array([[0.5, 0.5]]), tolerance=tolerance)
