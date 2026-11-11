"""Local range reweighting with fixed continuation values; never a strategy."""

from dataclasses import dataclass

import numpy as np

from poker_ai.finite import ArrayTree, FloatArray, IntArray
from poker_ai.postflop.collision_diagnosis import conditional_actions, sharing_cost
from poker_ai.postflop.controlled_scoring import BoolArray
from poker_ai.postflop.reply_trace import require_recall


@dataclass(frozen=True)
class RangeMixture:
    posterior: FloatArray
    prior: FloatArray
    combo_values: FloatArray  # Information row x declared combo x padded action.
    actual_values: FloatArray
    prior_values: FloatArray
    support: FloatArray
    uniform_weights: FloatArray
    maximum_chip_error: float
    maximum_unitless_error: float


def decompose(
    tree: ArrayTree,
    profile: FloatArray,
    target: int,
    river: BoolArray,
    node_combo: IntArray,
    compatible: BoolArray,
    declared_weights: FloatArray,
    *,
    chip_tolerance: float = 1e-9,
    unitless_tolerance: float = 1e-12,
) -> RangeMixture:
    """Integrate every compatible world BEFORE interpreting local action values.

    Combo-specific values use chance-only weights and a frozen continuation.
    Require values to agree across aliases with identical information/combo;
    otherwise replacing just range weights would not isolate the intended factor.
    Posterior uses chance*opponent PREFIX reach, excluding own reach. The prior
    uses declared positive weights and blockers only. The latter is a LOCAL
    intervention, not a globally consistent replacement policy or root EV.
    """
    if type(target) is not int or target not in (0, 1):
        raise ValueError("range mixture needs responding seat zero or one")
    if (
        not np.isfinite(chip_tolerance)
        or not 0 < chip_tolerance <= 1e-9
        or not np.isfinite(unitless_tolerance)
        or not 0 < unitless_tolerance <= 1e-12
    ):
        raise ValueError("invalid fixed mixture tolerances")
    n, width = tree.legal.shape
    if (
        river.dtype != np.bool_
        or river.shape != (n,)
        or np.any(river & (tree.owners != target))
        or node_combo.dtype != np.int64
        or node_combo.shape != tree.player.shape
        or declared_weights.ndim != 1
        or declared_weights.dtype != np.float64
        or not len(declared_weights)
        or np.any(declared_weights <= 0)
        or not np.all(np.isfinite(declared_weights))
        or compatible.dtype != np.bool_
        or compatible.shape != (n, len(declared_weights))
        or np.any(compatible[~river])
    ):
        raise ValueError("invalid river/combo/blocker/declared-weight inventory")
    tree.validate_policy(profile)
    require_recall(tree)
    nodes = np.flatnonzero(
        (tree.player == target) & river[np.maximum(tree.information, 0)]
    )
    infos, combos = tree.information[nodes], node_combo[nodes]
    count = len(declared_weights)
    if np.any(combos < 0) or np.any(combos >= count):
        raise ArithmeticError("river history has an invalid declared range index")
    edges = tree.edges(profile)
    cf = tree.chance_reach[nodes] * tree.reaches(edges)[nodes, 1 - target]
    masses, chance = np.zeros((n, count)), np.zeros((n, count))
    np.add.at(masses, (infos, combos), cf)
    np.add.at(chance, (infos, combos), tree.chance_reach[nodes])
    if not np.array_equal(chance > 0, compatible) or np.any(
        compatible[river].sum(axis=1) == 0
    ):
        raise ArithmeticError("complete compatible-combo history coverage required")
    support = masses.sum(axis=1)
    posterior = np.divide(
        masses, support[:, None], out=np.zeros_like(masses), where=support[:, None] > 0
    )
    raw_prior = compatible * declared_weights
    prior = np.divide(
        raw_prior,
        raw_prior.sum(axis=1, keepdims=True),
        out=np.zeros_like(raw_prior),
        where=raw_prior.sum(axis=1, keepdims=True) > 0,
    )
    chance_prior = np.divide(
        chance,
        chance.sum(axis=1, keepdims=True),
        out=np.zeros_like(chance),
        where=chance.sum(axis=1, keepdims=True) > 0,
    )
    sign = 1 if target == 0 else -1
    values = sign * tree.values(edges)
    action_values = values[tree.children[nodes]] * tree.valid[nodes]
    combo_values = np.zeros((n, count, width))
    np.add.at(
        combo_values,
        (infos, combos),
        tree.chance_reach[nodes, None] * action_values,
    )
    combo_values = np.divide(
        combo_values,
        chance[:, :, None],
        out=np.zeros_like(combo_values),
        where=chance[:, :, None] > 0,
    )
    low, high = np.full_like(combo_values, np.inf), np.full_like(combo_values, -np.inf)
    possible = tree.chance_reach[nodes] > 0
    np.minimum.at(low, (infos[possible], combos[possible]), action_values[possible])
    np.maximum.at(high, (infos[possible], combos[possible]), action_values[possible])
    spread = float(np.max(np.abs(high[compatible] - low[compatible]), initial=0))
    actual = (posterior[:, :, None] * combo_values).sum(axis=1)
    prior_values = (prior[:, :, None] * combo_values).sum(axis=1)
    direct, direct_support = conditional_actions(tree, profile)
    chip_error = max(
        spread, float(np.max(np.abs(actual[river] - direct[river]), initial=0))
    )
    active = support > 0
    errors = [
        float(np.max(np.abs(support[river] - direct_support[river]), initial=0)),
        float(np.max(np.abs(posterior[active].sum(axis=1) - 1), initial=0)),
        float(np.max(np.abs(prior[river].sum(axis=1) - 1), initial=0)),
        float(np.max(np.abs(chance_prior[river] - prior[river]), initial=0)),
    ]
    uniform_edges = tree.edges(tree.normalize(tree.legal))
    full_reach = tree.chance_reach * tree.reaches(uniform_edges).prod(axis=1)
    weights = np.zeros(n)
    np.add.at(weights, infos, full_reach[nodes])
    if weights.sum() > 0:
        weights /= weights.sum()  # Deliberately BEFORE actual-support filtering.
    arrays = (posterior, prior, combo_values, actual, prior_values, support, weights)
    if (
        any(not np.all(np.isfinite(a)) for a in arrays)
        or np.any(posterior[~compatible] != 0)
        or np.any(prior[~compatible] != 0)
        or np.any(actual[~active] != 0)
        or chip_error > chip_tolerance
        or max(errors) > unitless_tolerance
    ):
        raise ArithmeticError("range mixture/history/support reconstruction failed")
    for array in arrays:
        array.flags.writeable = False
    return RangeMixture(*arrays, chip_error, max(errors))


def conflict(q: FloatArray, tolerance: float = 1e-9) -> bool:
    if (
        q.ndim != 2
        or not q.shape[1]
        or not np.all(np.isfinite(q))
        or not np.isfinite(tolerance)
        or not 0 < tolerance <= 1e-9
    ):
        raise ValueError("finite legal action values and fixed tolerance required")
    if len(q) < 2:
        return False
    near = q.max(axis=1, keepdims=True) - q <= tolerance
    return not bool(np.any(near.all(axis=0)))


def total_variation(weights: FloatArray) -> float:
    """Maximum pairwise TV over supported normalized range vectors, not a CI."""
    if (
        weights.ndim != 2
        or not np.all(np.isfinite(weights))
        or np.any(weights < 0)
        or (
            len(weights) and not np.allclose(weights.sum(axis=1), 1, atol=1e-12, rtol=0)
        )
    ):
        raise ValueError("normalized supported range vectors required")
    return max(
        (
            float(np.max(np.abs(weights[i + 1 :] - weights[i]).sum(axis=1), initial=0))
            / 2
            for i in range(len(weights))
        ),
        default=0.0,
    )


def local_group(q: FloatArray, weights: FloatArray) -> dict[str, float | int | bool]:
    """All legal columns only; caller fixes common support and original weights."""
    if (
        q.ndim != 2
        or not q.shape[1]
        or weights.shape != (len(q),)
        or not np.all(np.isfinite(q))
        or not np.all(np.isfinite(weights))
        or np.any(weights < 0)
    ):
        raise ValueError(
            "finite legal values and nonnegative matching weights required"
        )
    if not len(q):
        return dict(local_cost=0.0, strict_conflict=False, supported_rows=0, weight=0.0)
    return dict(
        local_cost=sharing_cost(q, weights),
        strict_conflict=conflict(q),
        supported_rows=len(q),
        weight=float(weights.sum()),
    )
