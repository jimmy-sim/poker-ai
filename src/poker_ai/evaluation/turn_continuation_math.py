"""Own masked responses: freeze every unselected decision, never train."""

from dataclasses import dataclass

import numpy as np

from poker_ai.finite import ArrayTree, FloatArray
from poker_ai.postflop.collision_diagnosis import conditional_actions
from poker_ai.postflop.controlled_scoring import BoolArray, ScoringContext
from poker_ai.postflop.reply_trace import require_recall, response_profile

PANELS = ("saved", "restricted_river", "fine_river", "full_fine_reply")


def masked_reply(
    tree: ArrayTree, policy: FloatArray, target: int, selected: BoolArray
) -> FloatArray:
    """Optimize selected own infos, keeping ALL other probabilities unchanged.

    Sum chance times fixed-opponent reach over hidden histories before choosing
    each information-set action. Perfect recall makes own prior reach constant
    within that info, so it must not enter this maximization. At unselected own
    decisions, back up the SAVED probabilities, even when they occur later.
    Slicing a full best reply is not valid for a generic selection mask.
    """
    if type(target) is not int or target not in (0, 1):
        raise ValueError("masked reply needs responding seat zero or one")
    if (
        selected.dtype != np.bool_
        or selected.shape != (len(tree.keys),)
        or np.any(selected & (tree.owners != target))
    ):
        raise ValueError("boolean information mask must select only owned rows")
    tree.validate_policy(policy)
    require_recall(tree)
    edges = tree.edges(policy)
    cf = tree.chance_reach * tree.reaches(edges)[:, 1 - target]
    values = tree.terminal_values.copy() * (1 if target == 0 else -1)
    result = policy.copy()
    for nodes in reversed(tree.levels):
        active = (tree.player[nodes] == target) & selected[
            np.maximum(tree.information[nodes], 0)
        ]
        responding, fixed = nodes[active], nodes[~active]
        values[fixed] = (values[tree.children[fixed]] * edges[fixed]).sum(axis=1)
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
        owned = np.unique(infos)
        result[owned] = 0
        result[owned, choices[owned]] = 1
        values[responding] = values[tree.children[responding, choices[infos]]]
    tree.validate_policy(result)
    if result[~selected].tobytes() != policy[~selected].tobytes():
        raise ArithmeticError("masked response changed an unselected row")
    result.flags.writeable = False
    return result


@dataclass(frozen=True)
class Continuations:
    policies: tuple[FloatArray, ...]
    root_values: tuple[float, ...]
    conditional_values: tuple[FloatArray, ...]
    support: FloatArray
    increments: tuple[float, ...]
    maximum_error: float


def continuations(
    context: ScoringContext,
    saved: FloatArray,
    target: int,
    *,
    tolerance: float = 1e-9,
) -> Continuations:
    """Four saved/fixed-turn river/full-reply panels in responding-seat chips.

    Root feasible sets are nested. Individual fine-row/action Q values under a
    constrained river response need not improve: information sharing can trade
    off hidden histories. Only root ordering is an acceptance criterion.
    """
    if type(target) is not int or target not in (0, 1):
        raise ValueError("continuation target must be zero or one")
    if not np.isfinite(tolerance) or not 0 < tolerance <= 1e-9:
        raise ValueError("invalid continuation tolerance")
    fine, limited = context.exact, context.partition
    limited.validate_policy(saved)
    expanded = context.expand(saved)
    original = saved.tobytes()
    mapping = context.exact_to_partition
    first = np.unique(mapping, return_index=True)[1]
    river = context.river_masks[target]
    restricted = context.expand(masked_reply(limited, saved, target, river[first]))
    precise = masked_reply(fine, expanded, target, river)
    full = response_profile(fine, expanded, target)
    policies = (expanded, restricted, precise, full)
    for p in policies[:3]:
        if p[~river].tobytes() != expanded[~river].tobytes():
            raise ArithmeticError("river-only control changed turn/opponent rows")
    if (
        full[fine.owners != target].tobytes()
        != expanded[fine.owners != target].tobytes()
    ):
        raise ArithmeticError("full response changed the fixed opponent")
    roots, qs, supports = [], [], []
    sign = 1 if target == 0 else -1
    for p in policies:
        p.flags.writeable = False
        roots.append(sign * float(fine.values(fine.edges(p))[0]))
        q, support = conditional_actions(fine, p)
        qs.append(q)
        supports.append(support)
    owned = fine.owners == target
    if any(not np.array_equal(supports[0][owned], s[owned]) for s in supports[1:]):
        raise ArithmeticError("fixed-opponent counterfactual support changed")
    increments = tuple(float(b - a) for a, b in zip(roots, roots[1:], strict=False))
    error = abs(sum(increments) - (roots[-1] - roots[0]))
    if (
        not np.all(np.isfinite(roots))
        or any(gain < -tolerance for gain in increments)
        or error > tolerance
        or saved.tobytes() != original
    ):
        raise ArithmeticError("continuation root ordering/accounting/mutation failed")
    if fine is limited and (
        restricted.tobytes() != precise.tobytes()
        or abs(roots[1] - roots[2]) > tolerance
    ):
        raise ArithmeticError("fine-self river controls differ")
    return Continuations(
        policies,
        tuple(roots),
        tuple(qs),
        supports[0],
        increments,
        error,
    )
