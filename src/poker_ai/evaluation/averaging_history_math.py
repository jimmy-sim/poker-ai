"""Read-only suffix averages and fixed-opponent diagnostics, never a learner."""

import math
from typing import Any

import numpy as np

from poker_ai.evaluation.controlled_reply_math import Reply, require_tolerance, value
from poker_ai.finite import ArrayTree, FloatArray
from poker_ai.postflop.controlled_scoring import BoolArray


def validate_mass(tree: ArrayTree, weights: FloatArray) -> None:
    """Require finite legal mass and a valid normalization, including row totals."""
    tree.validate_policy(tree.normalize(weights))


def window_mass(tree: ArrayTree, earlier: FloatArray, later: FloatArray) -> FloatArray:
    """Subtract cumulative averages without resetting their original time weights.

    Stored masses are nonnegative legal weights. No learner array is modified,
    and negative differences are errors, not an invitation to clip or tune epsilons.
    A zero row is valid: normalization uses the frozen uniform legal fallback.
    """
    for weights in (earlier, later):
        validate_mass(tree, weights)
    mass = later - earlier
    validate_mass(tree, mass)
    mass.flags.writeable = False
    return mass


def uniform_information_reach(tree: ArrayTree) -> FloatArray:
    """Sum chance * both players' uniform-action reach over each information row.

    This is a diagnostic weighting measure, not a learned opponent belief. An info
    can contain several hidden histories; sum their reaches before normalization.
    It measures expected decision exposure and need not sum to one until weighted.
    """
    edges = tree.edges(tree.normalize(tree.legal))
    full = tree.chance_reach * tree.reaches(edges).prod(axis=1)
    nodes = np.flatnonzero(tree.player >= 0)
    mass = np.zeros(len(tree.keys), dtype=np.float64)
    np.add.at(mass, tree.information[nodes], full[nodes])
    if not np.all(np.isfinite(mass)) or np.any(mass < 0):
        raise ArithmeticError("invalid uniform information reach")
    return mass


def coverage(tree: ArrayTree, mass: FloatArray, river: BoolArray) -> dict[str, Any]:
    """Positive window mass coverage; warm-start whole-average coverage differs."""
    validate_mass(tree, mass)
    if river.dtype != np.bool_ or river.shape != (len(tree.keys),):
        raise ValueError("invalid window river mask")
    support = mass.sum(axis=1) > 0
    reaches = uniform_information_reach(tree)
    result: dict[str, Any] = {}
    for label, selected in (("all", np.ones_like(river)), ("river", river)):
        count = int(selected.sum())
        reached = math.fsum(float(r) for r in reaches[selected])
        result[label] = dict(
            rows=count,
            positive_rows=int((support & selected).sum()),
            row_fraction=float(support[selected].mean()) if count else None,
            uniform_reach_fraction=(
                math.fsum(float(r) for r in reaches[selected & support]) / reached
                if reached > 0
                else None
            ),
        )
    return result


def movement(
    tree: ArrayTree, earlier: FloatArray, later: FloatArray
) -> dict[str, float]:
    """Mean row L1 and uniform-decision-reach-weighted row L1, each in [0, 2]."""
    tree.validate_policy(earlier)
    tree.validate_policy(later)
    rows = np.abs(later - earlier).sum(axis=1)
    reaches = uniform_information_reach(tree)
    total = math.fsum(float(r) for r in reaches)
    return dict(
        mean_row_l1=float(rows.mean()),
        maximum_row_l1=float(rows.max(initial=0)),
        uniform_reach_weighted_l1=(
            math.fsum(
                float(r * distance) for r, distance in zip(reaches, rows, strict=True)
            )
            / total
            if total > 0
            else 0.0
        ),
    )


def fixed_match(
    tree: ArrayTree,
    candidate: FloatArray,
    opponent: FloatArray,
    reply: Reply,
    tolerance: float = 1e-9,
) -> dict[str, Any]:
    """Replace only the responder, evaluate a verified OWN reply to fixed opponent.

    Returns unilateral target chips, unlike half-summed self exploitability.
    The optimal root depends on the opponent, not the candidate's original rows.
    Its independent native check belongs to the isolated validation stage.
    """
    require_tolerance(tolerance)
    tree.validate_policy(candidate)
    tree.validate_policy(opponent)
    target = reply.target
    if type(target) is not int or target not in (0, 1):
        raise ValueError("fixed opponent requires target seat zero or one")
    mixed = np.where((tree.owners == target)[:, None], candidate, opponent)
    baseline = (1 if target == 0 else -1) * value(tree, mixed)
    achieved = (1 if target == 0 else -1) * value(tree, reply.apply(tree, mixed))
    gain = reply.root - baseline
    if (
        not math.isfinite(reply.root)
        or not math.isfinite(gain)
        or gain < -tolerance
        or abs(achieved - reply.root) > tolerance
    ):
        raise ArithmeticError("fixed-opponent own reply/root ordering changed")
    return dict(
        target=target,
        baseline_value_chips=baseline,
        restricted_reply_value_chips=reply.root,
        achieved_reply_value_chips=achieved,
        gain_chips=gain,
    )
