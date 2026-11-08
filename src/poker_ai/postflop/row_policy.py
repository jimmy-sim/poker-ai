"""Opt-in external sampling with policy rows cached for one frozen target pass."""

from typing import cast

import numpy as np

from poker_ai.finite import FloatArray
from poker_ai.postflop.controlled_training import ArrayState, ControlledTrainer
from poker_ai.training.mccfr import external_updates


class RowPolicyTrainer(ControlledTrainer):
    """Same valid-state update equations and RNG calls as ControlledTrainer.

    Regrets never change during a target pass, so a visited row can be normalized
    once and reused until that pass commits. Keep the original padded width and
    axis-1 reductions: summing only legal actions can change floating rounding.
    Dense current/average exports and exact initialization stay inherited.
    """

    row_evaluations: int = 0
    last_pass_rows: tuple[int, int] = (0, 0)

    def _policy_row(self, info: int) -> FloatArray:
        legal = self.tree.legal[info : info + 1]
        weights = np.maximum(self.regrets[info : info + 1], 0)
        if not np.all(np.isfinite(weights)) or np.any(weights * (1 - legal)):
            raise ValueError("invalid visited strategy weights")
        total = weights.sum(axis=1, keepdims=True)
        # np.maximum guarantees nonnegative weights. With one row the mask is
        # constant across columns; avoid computing a fallback that is overwritten.
        if total[0, 0] > 0:
            return cast(FloatArray, np.divide(weights, total)[0])
        return cast(FloatArray, (legal / legal.sum(axis=1, keepdims=True))[0])

    def step(self) -> None:
        if self.traversal != "external":
            raise ValueError("policy-row backend supports external sampling only")
        t = self.iteration + 1
        sizes = []
        for target in (0, 1):
            cache: dict[int, FloatArray] = {}

            def frozen(
                key: str,
                actions: tuple[int, ...],
                cache: dict[int, FloatArray] = cache,
            ) -> FloatArray:
                info = self.lookup[key]
                if actions != self.tree.actions[info]:
                    raise ValueError("controlled action menu mismatch")
                self.sampled_keys.add(key)
                if info not in cache:
                    cache[info] = self._policy_row(info)
                    self.row_evaluations += 1
                return cache[info][: len(actions)].copy()

            def select(probabilities: FloatArray) -> int:
                return int(self.rng.choice(len(probabilities), p=probabilities))

            update = external_updates(ArrayState(self.tree), target, frozen, select)
            self._apply(update, target, t)
            self.nodes_visited += update.visited
            sizes.append(len(cache))
        self.last_pass_rows = sizes[0], sizes[1]
        self.iteration = t
