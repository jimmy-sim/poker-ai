"""Separate dense, recursive toy oracle; no production traversal or updater.

The oracle computes its own warm expectations, policy rows, joint inverse CDF,
sampled recursion, dense sums and update equations. Shared dependencies are the
explicit toy tree, NumPy generator and rule declaration, not learner arithmetic.
Only tiny software fixtures are used. RNG identity and every endpoint are checked.
"""

import itertools
from typing import Any

import numpy as np
from numpy.random import PCG64, Generator

from poker_ai.finite import ArrayTree, FloatArray
from poker_ai.postflop.batch_reduction import ReducedDispatchBatchTrainer
from poker_ai.postflop.controlled_training import Rules
from poker_ai.postflop.frozen_batches import guard as old_guard
from poker_ai.postflop.stratified_batches import StratifiedBatchTrainer
from poker_ai.postflop.training_isolation import sentinel_tree


class DenseOracle:
    def __init__(self, tree: ArrayTree, seed: int, rules: Rules) -> None:
        self.tree, self.rng, self.rules = tree, Generator(PCG64(seed)), rules
        self.regrets, self.linear, self.uniform = (
            np.zeros_like(tree.legal) for _ in range(3)
        )
        self.nodes = 2 * len(tree.player)
        self.iteration = 1
        self.sampled: set[str] = set()
        self.row_evaluations = 0
        self.last_rows = (0, 0)
        # Independent simultaneous uniform full expectations.
        policy = self.policy()
        for target in (0, 1):
            r, a = self.warm(policy, target)
            self.apply(r, a, 1)
        self.warm_mass = self.linear.copy()

    def policy(self) -> FloatArray:
        result = np.zeros_like(self.tree.legal)
        for i, moves in enumerate(self.tree.actions):
            row = np.maximum(self.regrets[i : i + 1], 0)
            total = row.sum(axis=1, keepdims=True)
            result[i] = (
                row[0] / total[0, 0] if total[0, 0] else self.tree.legal[i] / len(moves)
            )
        return result

    def warm(self, policy: FloatArray, target: int) -> tuple[FloatArray, FloatArray]:
        tree = self.tree
        r, a = np.zeros_like(tree.legal), np.zeros_like(tree.legal)

        def visit(node: int, chance: float, own: tuple[float, float]) -> float:
            actor = int(tree.player[node])
            if actor == -2:
                return float(tree.terminal_values[node]) * (1 if target == 0 else -1)
            n = int(tree.valid[node].sum())
            row = (
                tree.chance_edges[node, :n]
                if actor == -1
                else policy[tree.information[node], :n]
            )
            values = []
            for j, p in enumerate(row):
                reach = tuple(own[k] * (float(p) if k == actor else 1) for k in (0, 1))
                values.append(
                    visit(
                        int(tree.children[node, j]),
                        chance * float(p) if actor == -1 else chance,
                        (reach[0], reach[1]),
                    )
                )
            values_array = np.array(values)
            value = float(row @ values_array)
            if actor >= 0:
                info = int(tree.information[node])
                if actor == target:
                    r[info, :n] += (chance * own[1 - target]) * (values_array - value)
                else:
                    a[info, :n] += (chance * own[actor]) * row
            return value

        visit(0, 1, (1, 1))
        return r, a

    def apply(self, r: FloatArray, a: FloatArray, t: int) -> None:
        rw = t if self.rules.regret_weight == "linear" else 1
        self.regrets += rw * r
        if self.rules.regret_rule == "clipped":
            self.regrets = np.maximum(self.regrets, 0)
        self.linear += t * a
        self.uniform += a

    def step(self, batch: int) -> None:
        tree = self.tree
        t = self.iteration + 1
        sizes = []
        for target in (0, 1):
            policy = self.policy()
            r, a = np.zeros_like(tree.legal), np.zeros_like(tree.legal)
            rows: set[int] = set()

            def visit(
                node: int,
                target: int = target,
                policy: FloatArray = policy,
                r: FloatArray = r,
                a: FloatArray = a,
                rows: set[int] = rows,
            ) -> float:
                self.nodes += 1
                actor = int(tree.player[node])
                if actor == -2:
                    return float(tree.terminal_values[node]) * (
                        1 if target == 0 else -1
                    )
                n = int(tree.valid[node].sum())
                if actor == -1:
                    j = int(self.rng.choice(n, p=tree.chance_edges[node, :n]))
                    return visit(int(tree.children[node, j]))
                info = int(tree.information[node])
                rows.add(info)
                self.sampled.add(tree.keys[info])
                sigma = policy[info, :n]
                if actor != target:
                    a[info, :n] += sigma
                    return visit(
                        int(tree.children[node, int(self.rng.choice(n, p=sigma))])
                    )
                values = np.array(
                    [visit(int(tree.children[node, j])) for j in range(n)]
                )
                value = float(sigma @ values)
                r[info, :n] += values - value
                return value

            # Separate inverse CDF, reconstructed from the explicit game arrays.
            law = []
            for i in range(int(tree.valid[0].sum())):
                child = int(tree.children[0, i])
                for j in range(int(tree.valid[child].sum())):
                    law.append(
                        (
                            int(tree.children[child, j]),
                            float(
                                tree.chance_edges[0, i] * tree.chance_edges[child, j]
                            ),
                        )
                    )
            for i in range(batch):
                u = (i + float(self.rng.random())) / batch
                total = sum(p for _, p in law)
                cumulative = 0.0
                chosen = None
                for node, p in law:
                    cumulative += p / total
                    if u < cumulative:
                        chosen = node
                        break
                if chosen is None:
                    raise ArithmeticError("oracle joint selection failed")
                self.nodes += 2  # Two private chance nodes, not skipped work.
                visit(chosen)
            self.apply(r / batch, a / batch, t)
            self.row_evaluations += len(rows)
            sizes.append(len(rows))
        self.last_rows = sizes[0], sizes[1]
        self.iteration = t


def parity() -> list[dict[str, Any]]:
    tree = sentinel_tree()
    rows = []
    for clip, weight, seed, batch in itertools.product(
        ("signed", "clipped"), ("uniform", "linear"), (7, 19), (1, 4, 16)
    ):
        rules = Rules(clip, weight, "linear")  # type: ignore[arg-type]
        own = StratifiedBatchTrainer(
            tree, Generator(PCG64(seed)), batch_size=batch, rules=rules
        )
        own.initialize_exact()
        oracle = DenseOracle(tree, seed, rules) if batch > 1 else None
        old = ReducedDispatchBatchTrainer(
            tree, Generator(PCG64(seed)), batch_size=1, rules=rules
        )
        old.initialize_exact()
        for endpoint in (1, 2, 3, 8, 17):
            while own.iteration < endpoint:
                own.step()
                if oracle is not None:
                    oracle.step(batch)
                else:
                    old.step()
            if oracle is None:
                if old_guard(own) != old_guard(old):
                    raise ArithmeticError("stratified B1 changed original state")
                error = 0.0
            else:
                error = max(
                    float(np.max(np.abs(actual - expected)))
                    for actual, expected in (
                        (own.regrets, oracle.regrets),
                        (own.strategy_sum, oracle.linear),
                        (own.uniform_sum, oracle.uniform),
                        (own.warm_sum, oracle.warm_mass),
                    )
                )
                if (
                    error > 1e-12
                    or not np.isfinite(error)
                    or own.rng.bit_generator.state != oracle.rng.bit_generator.state
                    or own.nodes_visited != oracle.nodes
                    or own.sampled_keys != oracle.sampled
                    or own.last_pass_rows != oracle.last_rows
                    or own.row_evaluations != oracle.row_evaluations
                ):
                    raise ArithmeticError("independent stratified trajectory mismatch")
            if own.sampled_traversals != 2 * batch * (endpoint - 1):
                raise ArithmeticError("stratified traversal count mismatch")
            rows.append(
                dict(
                    scope="TOY_ADAPTIVE_SOFTWARE_NOT_HOLDEM_STRENGTH",
                    batch_size=batch,
                    seed=seed,
                    regret_rule=clip,
                    regret_weight=weight,
                    iteration=endpoint,
                    maximum_array_error=error,
                    nodes_visited=own.nodes_visited,
                    B1_original_bit_match=batch == 1,
                )
            )
    return rows
