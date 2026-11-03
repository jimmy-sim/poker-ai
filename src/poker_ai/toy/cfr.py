"""Full-tree alternating CFR variants; no reference outputs enter training."""

from typing import Literal

import numpy as np

from poker_ai.toy.tree import FloatArray, Tree

Variant = Literal["cfr", "cfr_plus", "linear", "discounted"]


class CFR:
    """Counterfactual regret minimization in two-player zero-sum games.

    R_i(I,a) += sum_{h in I} chance(h)*opponent_reach(h)*
        (v_i(h,a)-v_i(h)). Own reach is excluded from regrets, but included in
    strategy averaging. Each target player's complete traversal uses one frozen
    joint policy. Aggregate by information set before CFR+ clips regrets.
    Alternate target 0 then 1, refreshing policy after each target update.

    Vanilla uses unit weights; CFR+ clips accumulated regrets and averages with
    weight t; Linear uses the equivalent regret recurrence (R+delta)*t/(t+1)
    and averaging weight t; Discounted uses
    alpha=1.5,beta=0,gamma=2, multiplying updated positive/negative regrets by
    t^alpha/(1+t^alpha) and t^beta/(1+t^beta), and averaging with weight t^gamma.
    No averaging delay. One iteration comprises both player traversals.
    """

    def __init__(self, tree: Tree, variant: Variant = "cfr") -> None:
        if variant not in ("cfr", "cfr_plus", "linear", "discounted"):
            raise ValueError("unknown CFR variant")
        self.tree = tree
        self.variant = variant
        self.iteration = 0
        self.regrets = np.zeros_like(tree.legal)
        self.strategy_sum = np.zeros_like(tree.legal)

    @property
    def current_policy(self) -> FloatArray:
        return self.tree.normalize(np.maximum(self.regrets, 0))

    @property
    def average_policy(self) -> FloatArray:
        return self.tree.normalize(self.strategy_sum)

    def step(self) -> None:
        self.iteration += 1
        t = self.iteration
        for target in (0, 1):
            policy = self.current_policy
            edges = self.tree.edges(policy)
            reach = self.tree.reaches(edges)
            values = self.tree.values(edges)
            nodes = np.flatnonzero(self.tree.player == target)
            infos = self.tree.information[nodes]
            advantage = values[self.tree.children[nodes]] - values[nodes, None]
            advantage *= self.tree.valid[nodes] * (1 if target == 0 else -1)
            counterfactual = self.tree.chance_reach[nodes] * reach[nodes, 1 - target]
            delta = counterfactual[:, None] * advantage
            np.add.at(self.regrets, infos, delta)
            weight = (
                t**2
                if self.variant == "discounted"
                else (t if self.variant in ("cfr_plus", "linear") else 1)
            )
            np.add.at(
                self.strategy_sum,
                infos,
                weight * reach[nodes, target, None] * policy[infos],
            )
            owned = self.tree.owners == target
            if self.variant == "cfr_plus":
                self.regrets[owned] = np.maximum(self.regrets[owned], 0)
            elif self.variant == "linear":
                # Positive rescaling preserves regret matching. This recurrence
                # matches the reference arithmetic, avoiding amplified rounding
                # differences in the equivalent raw t-weighted regret sum.
                self.regrets[owned] *= t / (t + 1)
            elif self.variant == "discounted":
                regret = self.regrets[owned]
                self.regrets[owned] = regret * np.where(
                    regret >= 0, t**1.5 / (1 + t**1.5), 0.5
                )

    def train(self, iterations: int) -> None:
        if type(iterations) is not int or iterations < 0:
            raise ValueError("iterations must be a nonnegative integer")
        for _ in range(iterations):
            self.step()
