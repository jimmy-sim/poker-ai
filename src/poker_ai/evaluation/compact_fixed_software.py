"""Analytic seven-node hidden-world fixture; not poker experiment evidence."""

from dataclasses import replace
from typing import Any

import numpy as np

from poker_ai.finite import ArrayTree
from poker_ai.postflop.compact_fixed import detail
from poker_ai.postflop.compact_full_context import Context
from poker_ai.postflop.controlled_scoring import ScoringContext


def hidden_scoring(target: int = 0, *, river: bool = True) -> ScoringContext:
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


def coarse_context(target: int = 0) -> Context:
    return Context("fixture", "coarse", "f" * 64, hidden_scoring(target), 2.0, {})


def analytical_fixture() -> tuple[dict[str, Any], dict[str, Any]]:
    """Literal independent terminal sums: v=1.25,R0=1.5,B0=2.5,B1=-1.25."""
    c = coarse_context()
    own = detail(
        c,
        np.array([[0.5, 0.5]]),
        dict(spot_file="fixture", representation="coarse", seed=17, mixture="SS"),
    )
    native = dict(
        native_metrics=dict(
            value_player_zero_chips=1.25,
            exact_exploitability_chips=0.625,
            within_partition_gain_chips=0.125,
            extra_information_gap_chips=0.5,
            river_only_gain_exact_prefix_chips=0.5,
        ),
        responses=[
            dict(
                target=0,
                exact_root_chips=2.5,
                restricted_root_chips=1.5,
                achieved_exact_chips=2.5,
                achieved_restricted_chips=1.5,
                achieved_river_before_chips=1.5,
            ),
            dict(
                target=1,
                exact_root_chips=-1.25,
                restricted_root_chips=-1.25,
                achieved_exact_chips=-1.25,
                achieved_restricted_chips=-1.25,
                achieved_river_before_chips=-1.25,
            ),
        ],
        maximum_error_chips=0.0,
    )
    return own, native
