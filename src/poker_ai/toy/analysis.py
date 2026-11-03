"""Exact profile values and information-set-constrained best responses."""

from dataclasses import dataclass

import numpy as np

from poker_ai.toy.tree import FloatArray, Tree


@dataclass(frozen=True, slots=True)
class Metrics:
    value_player_zero: float
    best_response_zero: float
    best_response_one: float
    nash_conv: float
    exploitability: float


def best_response(tree: Tree, policy: FloatArray, target: int) -> float:
    """Net chip value for target's exact best response to the other policy.

    Counterfactual weights exclude the responder's reach. At each information
    set, sum chance*opponent-reach-weighted continuation values over ALL hidden
    histories before choosing ONE action. Never maximize separately per hidden
    state. Equal-depth information sets and perfect recall hold for these trees.
    Unreachable information sets can choose any maximizing action; ties use the
    first legal action. The returned value is for target, not always player zero.
    """
    if target not in (0, 1):
        raise ValueError("target must be player zero or one")
    edges = tree.edges(policy)
    reach = tree.reaches(edges)
    counterfactual = tree.chance_reach * reach[:, 1 - target]
    sign = 1 if target == 0 else -1
    values = tree.terminal_values.copy() * sign
    for nodes in reversed(tree.levels):
        responding = nodes[tree.player[nodes] == target]
        other = nodes[tree.player[nodes] != target]
        values[other] = (values[tree.children[other]] * edges[other]).sum(axis=1)
        if len(responding):
            scores = np.zeros_like(tree.legal)
            infos = tree.information[responding]
            np.add.at(
                scores,
                infos,
                counterfactual[responding, None]
                * values[tree.children[responding]]
                * tree.valid[responding],
            )
            scores[tree.legal == 0] = -np.inf
            choices = scores.argmax(axis=1)
            values[responding] = values[tree.children[responding, choices[infos]]]
    return float(values[0])


def evaluate(tree: Tree, policy: FloatArray) -> Metrics:
    """Exploitability = NashConv/2 in ante chips per hand, NOT mbb/hand.

    NashConv = (BR_0 - v_0) + (BR_1 - v_1) = BR_0 + BR_1 since v_1=-v_0.
    It is not head-to-head loss against a single fixed equilibrium strategy.
    """
    edges = tree.edges(policy)
    value = float(tree.values(edges)[0])
    zero = best_response(tree, policy, 0)
    one = best_response(tree, policy, 1)
    nash_conv = zero + one
    if nash_conv < -1e-10:
        raise ArithmeticError("negative NashConv indicates an implementation error")
    return Metrics(value, zero, one, max(0.0, nash_conv), max(0.0, nash_conv) / 2)
