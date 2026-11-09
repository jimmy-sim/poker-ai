"""Independent dense batch updater and exact toy trajectory checks.

The dense reference deliberately does not use the batch combiner or row cache.
It shares the old external traversal, independently checked by exhaustive tape
expectations, and the old validated update operation. This is a software oracle,
not an external poker-strength reference.
"""

import itertools
from typing import Any, Literal

import numpy as np
from numpy.random import PCG64, Generator

from poker_ai.finite import FloatArray
from poker_ai.postflop.cached_nodes import CachedNodeTrainer
from poker_ai.postflop.controlled_training import (
    ArrayState,
    ControlledTrainer,
    Rules,
    Weight,
)
from poker_ai.postflop.frozen_batches import FrozenBatchTrainer
from poker_ai.postflop.row_profile import fingerprint
from poker_ai.postflop.training_isolation import sentinel_tree
from poker_ai.training.mccfr import Updates, external_updates


class DenseBatchReference(ControlledTrainer):
    """Full-policy exports, dense sums, deferred single update per target pass."""

    def batch_step(self, batch_size: int) -> None:
        t = self.iteration + 1
        for target in (0, 1):
            policy = self.current_policy
            regrets = np.zeros_like(self.regrets)
            averages = np.zeros_like(self.strategy_sum)
            found_r: set[str] = set()
            found_a: set[str] = set()
            visits = 0

            def frozen(
                key: str, actions: tuple[int, ...], policy: FloatArray = policy
            ) -> FloatArray:
                i = self.lookup[key]
                if actions != self.tree.actions[i]:
                    raise ValueError("dense batch menu mismatch")
                self.sampled_keys.add(key)
                return policy[i, : len(actions)].copy()

            def select(probabilities: FloatArray) -> int:
                return int(self.rng.choice(len(probabilities), p=probabilities))

            for _ in range(batch_size):
                sample = external_updates(ArrayState(self.tree), target, frozen, select)
                visits += sample.visited
                for table, sums, found in (
                    (sample.regrets, regrets, found_r),
                    (sample.averages, averages, found_a),
                ):
                    for key, values in table.items():
                        i, n = self.lookup[key], len(values)
                        if key in found:
                            sums[i, :n] += values
                        else:
                            sums[i, :n] = values
                            found.add(key)
            delta = Updates(
                {
                    k: regrets[self.lookup[k], : len(self.tree.actions[self.lookup[k]])]
                    / batch_size
                    for k in sorted(found_r)
                },
                {
                    k: averages[
                        self.lookup[k], : len(self.tree.actions[self.lookup[k]])
                    ]
                    / batch_size
                    for k in sorted(found_a)
                },
                visits,
            )
            self._apply(delta, target, t)
            self.nodes_visited += visits
        self.iteration = t


def parity() -> list[dict[str, Any]]:
    """B1 dual books vs old trainers; all B vs independent dense references."""
    clips: tuple[Literal["signed", "clipped"], ...] = ("signed", "clipped")
    weights: tuple[Weight, ...] = ("uniform", "linear")
    tree = sentinel_tree()
    rows = []
    for clip, regret_weight, seed, batch in itertools.product(
        clips, weights, (7, 19), (1, 4, 16)
    ):
        solver = FrozenBatchTrainer(
            tree,
            Generator(PCG64(seed)),
            batch_size=batch,
            rules=Rules(clip, regret_weight, "linear"),
        )
        peers = [
            DenseBatchReference(
                tree, Generator(PCG64(seed)), rules=Rules(clip, regret_weight, weight)
            )
            for weight in weights
        ]
        old = [
            CachedNodeTrainer(
                tree, Generator(PCG64(seed)), rules=Rules(clip, regret_weight, weight)
            )
            for weight in weights
        ]
        solver.initialize_exact()
        for p in [*peers, *old]:
            p.initialize_exact()
        for iteration in (1, 2, 3, 8, 17):
            while solver.iteration < iteration:
                solver.step()
                for peer in peers:
                    peer.batch_step(batch)
                if batch == 1:
                    for original in old:
                        original.step()
            hashes = {}
            for weight, peer, original in zip(weights, peers, old, strict=True):
                actual = solver.readout_fingerprint(weight)
                if actual != fingerprint(peer) or any(
                    getattr(solver, k) != getattr(peer, k)
                    for k in ("iteration", "nodes_visited", "initialization_visits")
                ):
                    raise ArithmeticError("dense frozen-batch trajectory mismatch")
                if batch == 1 and actual != fingerprint(original):
                    raise ArithmeticError("B1 dual-book original trajectory mismatch")
                hashes[weight] = actual
            if solver.sampled_traversals != 2 * batch * (iteration - 1):
                raise ArithmeticError("batch traversal accounting mismatch")
            rows.append(
                dict(
                    scope="TOY_SOFTWARE_NOT_HOLDEM_STRENGTH",
                    regret_rule=clip,
                    regret_weight=regret_weight,
                    seed=seed,
                    batch_size=batch,
                    iteration=iteration,
                    work=solver.nodes_visited,
                    readout_sha256=hashes,
                    old_B1_bit_match=batch == 1,
                )
            )
    return rows
