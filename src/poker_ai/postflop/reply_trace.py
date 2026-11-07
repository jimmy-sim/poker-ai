"""Own information-constrained replies and additive fixed-profile loss accounting."""

from dataclasses import dataclass

import numpy as np

from poker_ai.finite import ArrayTree, FloatArray
from poker_ai.postflop.collision_diagnosis import conditional_actions


def require_recall(tree: ArrayTree) -> None:
    """Reject merged own histories or unequal-depth infos before response DP."""
    paths: list[tuple[tuple[tuple[int, int], ...], ...]] = [
        ((), ()) for _ in tree.player
    ]
    signatures: dict[int, tuple[int, tuple[tuple[int, int], ...]]] = {}
    for depth, nodes in enumerate(tree.levels):
        for raw in nodes:
            node = int(raw)
            actor, info = int(tree.player[node]), int(tree.information[node])
            if actor >= 0:
                signature = depth, paths[node][actor]
                if signatures.setdefault(info, signature) != signature:
                    raise ValueError("response requires equal-depth perfect recall")
            for column in np.flatnonzero(tree.valid[node]):
                child = int(tree.children[node, column])
                past = list(paths[node])
                if actor >= 0:
                    past[actor] += ((info, int(column)),)
                paths[child] = tuple(past)


def response_profile(tree: ArrayTree, policy: FloatArray, target: int) -> FloatArray:
    """Replace only target rows with an own deterministic exact-partition reply.

    At each depth sum chance*opponent reach across every hidden history BEFORE
    maximizing each information row. Future target play is optimized recursively.
    Unsupported infos choose the first legal maximizer; no epsilon tie rounding.
    Requires perfect recall and equal-depth information sets, checked explicitly.
    """
    if target not in (0, 1):
        raise ValueError("target must be zero or one")
    require_recall(tree)
    edges = tree.edges(policy)
    cf = tree.chance_reach * tree.reaches(edges)[:, 1 - target]
    values = tree.terminal_values.copy() * (1 if target == 0 else -1)
    result = policy.copy()
    for nodes in reversed(tree.levels):
        responding = nodes[tree.player[nodes] == target]
        other = nodes[tree.player[nodes] != target]
        values[other] = (values[tree.children[other]] * edges[other]).sum(axis=1)
        if not len(responding):
            continue
        infos = tree.information[responding]
        scores = np.zeros_like(tree.legal)
        np.add.at(
            scores,
            infos,
            cf[responding, None]
            * values[tree.children[responding]]
            * tree.valid[responding],
        )
        scores[tree.legal == 0] = -np.inf
        choices = scores.argmax(axis=1)
        active = np.unique(infos)
        result[active] = 0
        result[active, choices[active]] = 1
        values[responding] = values[tree.children[responding, choices[infos]]]
    tree.validate_policy(result)
    return result


@dataclass(frozen=True)
class LossTrace:
    profile: FloatArray
    value: float  # Target chips, not always player zero.
    gain: float
    losses: FloatArray
    conditional_values: FloatArray
    counterfactual_mass: FloatArray
    saved_reach_mass: FloatArray
    accounting_error: float


def trace_losses(
    tree: ArrayTree, policy: FloatArray, target: int, *, tolerance: float = 1e-9
) -> LossTrace:
    """Additive unilateral gain using SAVED prefix reach and optimal reply suffix.

    W is the target's value under (best reply, saved opponent). Each target node
    contributes saved full reach * [W(h) - sum_a saved(a|I) W(ha)]. Sum hidden
    histories into infos. The total telescopes to BR_i - saved_value_i. Perfect
    recall makes aggregated losses nonnegative; hidden-node terms can be signed.
    This is a fixed-profile decomposition, not causal abstraction/retraining EV.
    """
    if not np.isfinite(tolerance) or not 0 < tolerance <= 1e-8:
        raise ValueError("invalid accounting tolerance")
    profile = response_profile(tree, policy, target)
    sign = 1 if target == 0 else -1
    saved_edges = tree.edges(policy)
    values = sign * tree.values(tree.edges(profile))
    baseline = sign * float(tree.values(saved_edges)[0])
    full_reach = tree.chance_reach * tree.reaches(saved_edges).prod(axis=1)
    nodes = np.flatnonzero(tree.player == target)
    infos = tree.information[nodes]
    deviation = values[nodes] - (values[tree.children[nodes]] * saved_edges[nodes]).sum(
        axis=1
    )
    losses, mass = np.zeros(len(tree.keys)), np.zeros(len(tree.keys))
    np.add.at(losses, infos, full_reach[nodes] * deviation)
    np.add.at(mass, infos, full_reach[nodes])
    q, support = conditional_actions(tree, profile)
    # Invalid padded Q columns are zero, so max only over legal actions.
    local = np.where(tree.legal > 0, q, -np.inf).max(axis=1) - (q * policy).sum(axis=1)
    owned = tree.owners == target
    error = max(
        abs(float(losses.sum()) - (float(values[0]) - baseline)),
        float(np.max(np.abs(losses[owned] - mass[owned] * local[owned]), initial=0)),
    )
    if error > tolerance or float(losses.min(initial=0)) < -tolerance:
        raise ArithmeticError("reply loss accounting mismatch")
    return LossTrace(
        profile,
        float(values[0]),
        float(values[0]) - baseline,
        losses,
        q,
        support,
        mass,
        error,
    )
