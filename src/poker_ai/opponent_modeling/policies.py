"""Scripted own hypotheses and realization-equivalent root mixtures."""

from dataclasses import dataclass

import numpy as np

from poker_ai.toy.analysis import best_response
from poker_ai.toy.games import Move
from poker_ai.toy.tree import FloatArray, Tree


def scripted_policy(tree: Tree, name: str, floor_mass: float = 0.1) -> FloatArray:
    """Full-support own toy policies; `value` uses its OWN private/public rank."""
    if name not in ("uniform", "calling_station", "aggressive", "value"):
        raise ValueError("unknown scripted hypothesis")
    if not np.isfinite(floor_mass) or not 0 < floor_mass <= 1:
        raise ValueError("floor mass must be in (0,1]")
    uniform = tree.normalize(tree.legal)
    answer = uniform.copy()
    seen: set[int] = set()
    for node, state in enumerate(tree.states):
        info = int(tree.information[node])
        if info < 0 or info in seen:
            continue
        seen.add(info)
        actions = tree.actions[info]
        preferred = int(Move.CALL)
        if name == "aggressive":
            preferred = int(Move.RAISE) if int(Move.RAISE) in actions else preferred
        elif name == "value":
            rank = state.cards[state.actor]
            public_rank = state.board
            if state.game == "leduc":
                rank //= 2
                public_rank = None if public_rank is None else public_rank // 2
            strong = rank == 2 or (public_rank is not None and rank == public_rank)
            if strong and int(Move.RAISE) in actions:
                preferred = int(Move.RAISE)
            elif rank == 0 and int(Move.FOLD) in actions:
                preferred = int(Move.FOLD)
        if name != "uniform":
            answer[info] = floor_mass * uniform[info]
            answer[info, actions.index(preferred)] += 1 - floor_mass
    tree.validate_policy(answer)
    return answer


def root_mixture(
    tree: Tree, policies: tuple[FloatArray, ...], weights: FloatArray, player: int
) -> FloatArray:
    """Convert a type sampled ONCE per hand to its behavioral policy.

    At I, P(type|own previous actions) is proportional to weight*own_reach(I).
    Chance/opponent reach are excluded. Perfect recall makes own reach identical
    for every node in I. Local unweighted interpolation is generally different.
    Other player's rows are copied from policies[0] and not changed.
    """
    if player not in (0, 1) or not policies:
        raise ValueError("requires a player and nonempty policy family")
    if (
        weights.shape != (len(policies),)
        or not np.all(np.isfinite(weights))
        or np.any(weights < 0)
        or not np.isclose(weights.sum(), 1, atol=1e-12, rtol=0)
    ):
        raise ValueError("mixture weights must be normalized nonnegative probabilities")
    own_reaches = np.array(
        [tree.reaches(tree.edges(policy))[:, player] for policy in policies]
    )
    answer = policies[0].copy()
    for info in np.flatnonzero(tree.owners == player):
        nodes = np.flatnonzero(tree.information == info)
        reach = own_reaches[:, nodes[0]]
        if not np.allclose(own_reaches[:, nodes], reach[:, None], atol=1e-12, rtol=0):
            raise ValueError("root mixture requires perfect recall")
        conditional = weights * reach
        if conditional.sum() == 0:
            answer[info] = tree.legal[info] / tree.legal[info].sum()
        else:
            answer[info] = (
                conditional[:, None] * np.array([policy[info] for policy in policies])
            ).sum(axis=0) / conditional.sum()
    tree.validate_policy(answer)
    return answer


def response_policy(tree: Tree, opponent: FloatArray, target: int) -> FloatArray:
    """Return one exact information-set-constrained pure best response profile."""
    if target not in (0, 1):
        raise ValueError("invalid responding player")
    edges = tree.edges(opponent)
    cf = tree.chance_reach * tree.reaches(edges)[:, 1 - target]
    values = tree.terminal_values.copy() * (1 if target == 0 else -1)
    result = opponent.copy()
    for nodes in reversed(tree.levels):
        own = nodes[tree.player[nodes] == target]
        others = nodes[tree.player[nodes] != target]
        values[others] = (values[tree.children[others]] * edges[others]).sum(axis=1)
        if len(own):
            scores = np.zeros_like(tree.legal)
            infos = tree.information[own]
            np.add.at(
                scores,
                infos,
                cf[own, None] * values[tree.children[own]] * tree.valid[own],
            )
            scores[tree.legal == 0] = -np.inf
            choices = scores.argmax(axis=1)
            for info in np.unique(infos):
                result[info] = 0
                result[info, choices[info]] = 1
            values[own] = values[tree.children[own, choices[infos]]]
    tree.validate_policy(result)
    return result


def profile_value(
    tree: Tree, own: FloatArray, opponent: FloatArray, seat: int
) -> float:
    if seat not in (0, 1):
        raise ValueError("invalid seat")
    profile = opponent.copy()
    profile[tree.owners == seat] = own[tree.owners == seat]
    return float(tree.values(tree.edges(profile))[0]) * (1 if seat == 0 else -1)


def security(tree: Tree, own: FloatArray, seat: int) -> float:
    """Minimum expected payoff against any legal opponent, in ante chips/hand."""
    if seat not in (0, 1):
        raise ValueError("invalid seat")
    return -best_response(tree, own, 1 - seat)


@dataclass(frozen=True)
class GuardedResponse:
    policy: FloatArray
    unrestricted: FloatArray
    fraction: float
    baseline_security: float
    candidate_security: float
    certified_lower_bound: float
    actual_security: float


def guarded_response(
    tree: Tree,
    blueprint: FloatArray,
    predictive: FloatArray,
    seat: int,
    budget: float,
    tolerance: float = 1e-10,
) -> GuardedResponse:
    """Bound expected degradation relative to blueprint, NOT realized losses.

    min_tau [(1-lambda)V(base,tau)+lambda V(candidate,tau)] is at least
    (1-lambda)min_tau V(base,tau)+lambda min_tau V(candidate,tau).
    This uses a root mixture with realization conversion, never a fresh coin at
    every node. It does not guarantee game value or safety in abstracted Hold'em.
    """
    if not np.isfinite(budget) or budget < 0 or not 0 < tolerance <= 1e-8:
        raise ValueError("invalid degradation budget/tolerance")
    candidate = response_policy(tree, predictive, seat)
    s0, s1 = security(tree, blueprint, seat), security(tree, candidate, seat)
    fraction = min(1.0, budget / (s0 - s1)) if s1 < s0 else 1.0
    policy = root_mixture(
        tree, (blueprint, candidate), np.array([1 - fraction, fraction]), seat
    )
    lower = (1 - fraction) * s0 + fraction * s1
    actual = security(tree, policy, seat)
    if actual < lower - tolerance or lower < s0 - budget - tolerance:
        raise ArithmeticError("root-mixture security certificate failed")
    return GuardedResponse(policy, candidate, fraction, s0, s1, lower, actual)
