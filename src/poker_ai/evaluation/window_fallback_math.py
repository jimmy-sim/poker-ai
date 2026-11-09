"""Own saved-policy interventions; zero mass is exact, not a tuned threshold."""

import math
from dataclasses import dataclass
from typing import Any

import numpy as np

from poker_ai.evaluation.averaging_history_math import (
    uniform_information_reach,
    validate_mass,
)
from poker_ai.evaluation.controlled_reply_math import require_tolerance
from poker_ai.finite import ArrayTree, FloatArray
from poker_ai.postflop.controlled_scoring import BoolArray
from poker_ai.postflop.parallel_profile import same

LABELS = ("raw", "fill_0", "fill_1", "fill_both")
MASKS = ((), (0,), (1,), (0, 1))
ADDITIVE_METRICS = (
    "exact_exploitability_chips",
    "within_partition_gain_chips",
    "extra_information_gap_chips",
)


@dataclass(frozen=True)
class Filled:
    policy: FloatArray
    eligible: BoolArray
    changed: BoolArray
    support: list[dict[str, Any]]
    maximum_realization_change: float


def fill_rows(
    tree: ArrayTree,
    window: FloatArray,
    mass: FloatArray,
    whole: FloatArray,
    targets: tuple[int, ...],
    river: BoolArray,
) -> Filled:
    """Replace only selected own zero-mass rows, leaving every other bit intact.

    The mask is fixed by archived OWN weights and information-row ownership. It
    never depends on a live hidden hand, future card, reference output or score.
    In particular, a tiny positive mass is not eligible. A zero row normalizes
    with the frozen uniform legal fallback before the intervention.
    """
    if not any(same(list(targets), list(t)) for t in MASKS):
        raise ValueError("fill targets must be one of the four fixed seat masks")
    tree.validate_policy(window)
    tree.validate_policy(whole)
    validate_mass(tree, mass)
    if window.tobytes() != tree.normalize(mass).tobytes():
        raise ArithmeticError("window policy does not reconstruct from its mass")
    if river.dtype != np.bool_ or river.shape != (len(tree.keys),):
        raise ValueError("invalid window fallback river mask")
    eligible = mass.sum(axis=1) == 0
    selected = eligible & np.isin(tree.owners, targets)
    policy = window.copy()
    policy[selected] = whole[selected]
    tree.validate_policy(policy)
    changed = np.any(policy.view(np.uint64) != window.view(np.uint64), axis=1)
    if (
        np.any(changed & ~selected)
        or policy[~selected].tobytes() != window[~selected].tobytes()
    ):
        raise ArithmeticError("fallback changed a learned or unselected row")
    raw_reach = tree.reaches(tree.edges(window))
    new_reach = tree.reaches(tree.edges(policy))
    weighted = uniform_information_reach(tree)
    support = []
    for target in (0, 1):
        owned = tree.owners == target
        total = math.fsum(float(x) for x in weighted[owned])
        nodes = np.flatnonzero(tree.player == target)
        missing_nodes = nodes[eligible[tree.information[nodes]]]
        missing_river_nodes = nodes[(eligible & river)[tree.information[nodes]]]
        river_total = math.fsum(float(x) for x in weighted[owned & river])
        support.append(
            dict(
                target=target,
                selected=target in targets,
                owned_rows=int(owned.sum()),
                eligible_rows=int((owned & eligible).sum()),
                eligible_river_rows=int((owned & eligible & river).sum()),
                changed_rows=int((owned & changed).sum()),
                changed_river_rows=int((owned & changed & river).sum()),
                eligible_uniform_reach_fraction=(
                    math.fsum(float(x) for x in weighted[owned & eligible]) / total
                    if total
                    else None
                ),
                maximum_own_reach_at_eligible_histories=float(
                    raw_reach[missing_nodes, target].max(initial=0)
                ),
                eligible_river_uniform_reach_fraction=(
                    math.fsum(float(x) for x in weighted[owned & eligible & river])
                    / river_total
                    if river_total
                    else None
                ),
                maximum_own_reach_at_eligible_river_histories=float(
                    raw_reach[missing_river_nodes, target].max(initial=0)
                ),
            )
        )
    maximum = float(np.abs(raw_reach - new_reach).max(initial=0))
    for array in (policy, eligible, changed):
        array.flags.writeable = False
    return Filled(policy, eligible, changed, support, maximum)


def full_equivalence(
    filled: Filled,
    raw_score: dict[str, Any],
    new_score: dict[str, Any],
    tolerance_chips: float = 1e-9,
    tolerance_unitless: float = 1e-12,
) -> float:
    """Unreachable full-average rows must not alter realized strategy or scores.

    Do not apply this invariant to sampled zero mass: a finite sample can miss a
    reachable row. River-only diagnostics are not pure full-game BR metrics.
    """
    require_tolerance(tolerance_chips)
    if (
        type(tolerance_unitless) not in (int, float)
        or not 0 < tolerance_unitless <= 1e-12
    ):
        raise ValueError("invalid unitless realization tolerance")
    errors = [
        abs(new_score["metrics"][k] - raw_score["metrics"][k])
        for k in (*ADDITIVE_METRICS, "value_player_zero_chips")
    ]
    maximum = max(errors)
    if (
        not all(math.isfinite(x) for x in errors)
        or not math.isfinite(filled.maximum_realization_change)
        or filled.maximum_realization_change > tolerance_unitless
        or maximum > tolerance_chips
    ):
        raise ArithmeticError("full zero-mass fill changed realization or value")
    return float(maximum)


def panel_identity(
    scores: dict[str, dict[str, Any]],
    tolerance: float = 1e-9,
) -> dict[str, float]:
    """The 2x2 self BR metrics are additive; baseline EV may have interaction.

    BR_0 depends only on seat one's strategy and BR_1 only on seat zero's.
    NashConv/2 cancels the two opposite baseline values. River-only prefix
    probes do not satisfy this full-game root argument and are excluded.
    """
    require_tolerance(tolerance)
    if set(scores) != set(LABELS):
        raise ArithmeticError("incomplete seat-fill accounting panel")
    residuals = [
        abs(
            scores["fill_both"]["metrics"][k]
            - scores["fill_0"]["metrics"][k]
            - scores["fill_1"]["metrics"][k]
            + scores["raw"]["metrics"][k]
        )
        for k in ADDITIVE_METRICS
    ]
    for target in (0, 1):
        own, other = f"fill_{target}", f"fill_{1 - target}"
        for a, b in (("raw", own), (other, "fill_both")):
            for key in ("exact_reply_value_chips", "restricted_reply_value_chips"):
                residuals.append(
                    abs(
                        scores[a]["responses"][target][key]
                        - scores[b]["responses"][target][key]
                    )
                )
    if not all(math.isfinite(x) for x in residuals) or max(residuals) > tolerance:
        raise ArithmeticError("seat-fill BR root/additivity identity failed")
    ev = "value_player_zero_chips"
    interaction = (
        scores["fill_both"]["metrics"][ev]
        - scores["fill_0"]["metrics"][ev]
        - scores["fill_1"]["metrics"][ev]
        + scores["raw"]["metrics"][ev]
    )
    if not math.isfinite(interaction):
        raise ArithmeticError("nonfinite seat-fill baseline EV interaction")
    return dict(
        maximum_error_chips=max(residuals), baseline_ev_interaction_chips=interaction
    )
