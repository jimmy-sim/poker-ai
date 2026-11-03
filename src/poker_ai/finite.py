"""Shared array algebra for small finite extensive-form games."""

from dataclasses import dataclass
from typing import cast

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]
IntArray = NDArray[np.int64]


@dataclass(frozen=True)
class ArrayTree:
    children: IntArray
    valid: NDArray[np.bool_]
    player: IntArray  # -2 terminal, -1 chance, otherwise 0/1.
    information: IntArray
    keys: tuple[str, ...]
    actions: tuple[tuple[int, ...], ...]
    owners: IntArray
    legal: FloatArray
    chance_edges: FloatArray
    chance_reach: FloatArray
    terminal_values: FloatArray
    levels: tuple[IntArray, ...]

    def normalize(self, weights: FloatArray) -> FloatArray:
        """Normalize nonnegative legal action weights, falling back to uniform."""
        if weights.shape != self.legal.shape or not np.all(np.isfinite(weights)):
            raise ValueError("invalid strategy weights")
        if np.any(weights < 0) or np.any(weights * (1 - self.legal)):
            raise ValueError("negative or illegal action weight")
        total = weights.sum(axis=1, keepdims=True)
        return cast(
            FloatArray,
            np.divide(
                weights,
                total,
                out=self.legal / self.legal.sum(axis=1, keepdims=True),
                where=total > 0,
            ),
        )

    def validate_policy(self, policy: FloatArray) -> None:
        if (
            policy.shape != self.legal.shape
            or not np.all(np.isfinite(policy))
            or np.any(policy < 0)
            or np.any(policy * (1 - self.legal))
            or not np.allclose(policy.sum(axis=1), 1, atol=1e-12, rtol=0)
        ):
            raise ValueError("policy must assign normalized legal probabilities")

    def edges(self, policy: FloatArray) -> FloatArray:
        self.validate_policy(policy)
        probabilities = self.chance_edges.copy()
        decision = np.flatnonzero(self.player >= 0)
        probabilities[decision] = policy[self.information[decision]]
        return probabilities

    def values(self, probabilities: FloatArray) -> FloatArray:
        values = self.terminal_values.copy()
        for nodes in reversed(self.levels):
            values[nodes] = (values[self.children[nodes]] * probabilities[nodes]).sum(
                axis=1
            )
        return values

    def reaches(self, probabilities: FloatArray) -> FloatArray:
        """Each player's own realization reach; deliberately excludes chance."""
        reach = np.ones((len(self.player), 2))
        for nodes in self.levels:
            for player in (0, 1):
                factors = np.where(
                    self.player[nodes, None] == player, probabilities[nodes], 1.0
                )
                contributions = reach[nodes, player, None] * factors
                active = self.valid[nodes]
                reach[self.children[nodes][active], player] = contributions[active]
        return reach
