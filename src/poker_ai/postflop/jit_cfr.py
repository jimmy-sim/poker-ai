"""Optional own CFR+ kernel with explicit IEEE fused operations, no fast-math.

The scalar arithmetic control found the pinned native solver contracts value and
average multiply/add expressions, but not its stored regret increment. Explicit
LLVM fma preserves that rounding choice without a tuned regret-zero threshold.
This is Python/Numba code; no native poker solver is imported or called here.
"""

import importlib
from typing import Any

import numpy as np

from poker_ai.finite import FloatArray, IntArray
from poker_ai.postflop.matrix import MatrixTree

numba: Any = importlib.import_module("numba")
extending: Any = importlib.import_module("numba.extending")


def _fma_type(typing_context: Any, a: Any, b: Any, c: Any) -> Any:
    if any(t != numba.types.float64 for t in (a, b, c)):
        raise TypeError("fma requires three float64 values")
    signature = numba.types.float64(a, b, c)

    def codegen(context: Any, builder: Any, sig: Any, values: Any) -> Any:
        return builder.fma(values[0], values[1], values[2])

    return signature, codegen


FMA: Any = extending.intrinsic(_fma_type)


def _normalize(weights: FloatArray, counts: IntArray, output: FloatArray) -> None:
    for info in range(len(counts)):
        total = 0.0
        for a in range(counts[info]):
            total += max(0.0, weights[info, a])
        for a in range(counts[info]):
            output[info, a] = (
                max(0.0, weights[info, a]) / total if total > 0 else 1.0 / counts[info]
            )


NORMALIZE: Any = numba.njit(cache=True, fastmath=False)(_normalize)


def _step(
    children: IntArray,
    degree: IntArray,
    player: IntArray,
    information: IntArray,
    owners: IntArray,
    counts: IntArray,
    chance_edges: FloatArray,
    chance_reach: FloatArray,
    terminal_values: FloatArray,
    regrets: FloatArray,
    averages: FloatArray,
    policy: FloatArray,
    iteration: int,
    fused_values: bool,
    fused_regrets: bool,
    fused_averages: bool,
) -> None:
    n = len(player)
    for target in range(2):
        NORMALIZE(regrets, counts, policy)
        reach_zero = np.ones(n)
        reach_one = np.ones(n)
        for node in range(n):
            actor = player[node]
            for column in range(degree[node]):
                child = children[node, column]
                probability = policy[information[node], column] if actor >= 0 else 1.0
                reach_zero[child] = reach_zero[node] * (
                    probability if actor == 0 else 1.0
                )
                reach_one[child] = reach_one[node] * (
                    probability if actor == 1 else 1.0
                )
        values = terminal_values.copy()
        for node in range(n - 1, -1, -1):
            actor = player[node]
            if actor == -2:
                continue
            if actor >= 0 and reach_zero[node] == 0 and reach_one[node] == 0:
                values[node] = 0.0
                continue
            value = 0.0
            for column in range(degree[node]):
                probability = (
                    chance_edges[node, column]
                    if actor == -1
                    else policy[information[node], column]
                )
                child_value = values[children[node, column]]
                value = (
                    FMA(probability, child_value, value)
                    if fused_values
                    else value + probability * child_value
                )
            values[node] = value
        for node in range(n):
            if player[node] != target:
                continue
            info = information[node]
            own = reach_zero[node] if target == 0 else reach_one[node]
            other = reach_one[node] if target == 0 else reach_zero[node]
            cf = chance_reach[node] * other
            for column in range(degree[node]):
                difference = (values[children[node, column]] - values[node]) * (
                    1.0 if target == 0 else -1.0
                )
                if fused_regrets:
                    regrets[info, column] = FMA(cf, difference, regrets[info, column])
                else:
                    increment = cf * difference
                    regrets[info, column] += increment
                if fused_averages:
                    averages[info, column] = FMA(
                        iteration * own, policy[info, column], averages[info, column]
                    )
                else:
                    averages[info, column] += iteration * own * policy[info, column]
        for info in range(len(counts)):
            if owners[info] == target:
                for column in range(counts[info]):
                    regrets[info, column] = max(0.0, regrets[info, column])
    NORMALIZE(regrets, counts, policy)


STEP: Any = numba.njit(cache=True, fastmath=False)(_step)


class FusedCFRPlus:
    """Same own alternating CFR+ equations, with explicit scalar rounding choices."""

    def __init__(
        self,
        tree: MatrixTree,
        *,
        fused_values: bool = True,
        fused_regrets: bool = False,
        fused_averages: bool = True,
    ) -> None:
        self.tree = tree
        self.iteration = 0
        self.regrets = np.zeros_like(tree.legal)
        self.strategy_sum = np.zeros_like(tree.legal)
        self._policy = tree.normalize(tree.legal)
        self.counts = np.array([len(a) for a in tree.actions], dtype=np.int64)
        self.degree = tree.valid.sum(axis=1).astype(np.int64)
        self.arithmetic = fused_values, fused_regrets, fused_averages

    @property
    def current_policy(self) -> FloatArray:
        return self._policy.copy()

    @property
    def average_policy(self) -> FloatArray:
        result = np.zeros_like(self.strategy_sum)
        NORMALIZE(self.strategy_sum, self.counts, result)
        return result

    def step(self) -> None:
        self.iteration += 1
        tree = self.tree
        STEP(
            tree.children,
            self.degree,
            tree.player,
            tree.information,
            tree.owners,
            self.counts,
            tree.chance_edges,
            tree.chance_reach,
            tree.terminal_values,
            self.regrets,
            self.strategy_sum,
            self._policy,
            self.iteration,
            *self.arithmetic,
        )

    def train(self, iterations: int) -> None:
        if type(iterations) is not int or iterations < 0:
            raise ValueError("iterations must be a nonnegative integer")
        for _ in range(iterations):
            self.step()
