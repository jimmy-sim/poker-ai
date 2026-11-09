"""Own external sampling with independent traversals at one frozen target policy.

The mean of B conditionally independent raw increments has the same conditional
expectation and 1/B component variance. Clipping is applied AFTER this mean; its
expectation need not equal clipping a full-pass expectation. At fixed work this
also changes update counts and iteration weights, so it is not a pure variance
intervention. Nothing here imports reference strategies or changes old trainers.
"""

import copy
import hashlib
import json
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass

import numpy as np
from numpy.random import Generator

from poker_ai.finite import ArrayTree, FloatArray
from poker_ai.postflop.cached_nodes import CachedNodeTrainer
from poker_ai.postflop.controlled_training import Rules, Weight
from poker_ai.postflop.river_study import Deadline
from poker_ai.postflop.row_profile import fingerprint
from poker_ai.training.mccfr import Updates, external_updates


def mean_updates(samples: Iterable[Updates], count: int) -> Updates:
    """Fresh sparse sums, traversal/key encounter order, divide once at the end.

    Missing rows contribute zero; averaging only the appearances would bias the
    estimator. Visits are SUMMED rather than averaged. Inputs are never mutated.
    Target ownership/menu validation remains the original updater's obligation.
    """
    if type(count) is not int or count <= 0:
        raise ValueError("batch count must be a positive integer")
    result = Updates({}, {})
    observed = 0
    for sample in samples:
        if type(sample.visited) is not int or sample.visited <= 0:
            raise ValueError("batch traversal must charge positive integer visits")
        observed += 1
        if observed > count:
            raise ValueError("too many batch traversals")
        for incoming, outgoing, average in (
            (sample.regrets, result.regrets, False),
            (sample.averages, result.averages, True),
        ):
            for key, values in incoming.items():
                if (
                    not isinstance(key, str)
                    or not key
                    or values.ndim != 1
                    or not values.size
                    or not np.all(np.isfinite(values))
                    or (average and np.any(values < 0))
                ):
                    raise ValueError("invalid raw batch increment")
                if key not in outgoing:
                    outgoing[key] = values.copy()
                elif outgoing[key].shape != values.shape:
                    raise ValueError("batch menu width changed")
                else:
                    outgoing[key] += values
                if not np.all(np.isfinite(outgoing[key])):
                    raise ArithmeticError("nonfinite batch sum")
        result.visited += sample.visited
    if observed != count:
        raise ValueError("incomplete batch traversals")
    for table in (result.regrets, result.averages):
        for values in table.values():
            values /= count
    return result


class FrozenBatchTrainer(CachedNodeTrainer):
    """Linear primary average plus uniform readout on one shared learning path.

    B1 delegates the unchanged old step, preserving every RNG/update operation.
    The extra ledger cannot affect regrets, current probabilities or selectors.
    Exact initialization writes both ledgers at t=1 and costs the old 2N visits.
    """

    def __init__(
        self,
        tree: ArrayTree,
        rng: Generator,
        *,
        batch_size: int,
        rules: Rules | None = None,
    ) -> None:
        if type(batch_size) is not int or batch_size <= 0:
            raise ValueError("batch size must be a positive integer")
        actual = rules or Rules(average_weight="linear")
        if actual.average_weight != "linear":
            raise ValueError("dual-book primary average must be linear")
        self.batch_size = batch_size
        self.uniform_sum = np.zeros_like(tree.legal)
        self.warm_sum = np.zeros_like(tree.legal)
        self.sampled_traversals = 0
        super().__init__(tree, rng, rules=actual)

    def _apply(self, updates: Updates, target: int, iteration: int) -> None:
        # Original whole-update validation and arithmetic occur first. These
        # additions are independent of all arrays used to choose actions.
        super()._apply(updates, target, iteration)
        for key, values in updates.averages.items():
            self.uniform_sum[self.lookup[key], : len(values)] += values

    def initialize_exact(self) -> None:
        if np.any(self.uniform_sum) or np.any(self.warm_sum):
            raise ValueError("exact initialization requires unused dual books")
        super().initialize_exact()
        self.warm_sum = self.strategy_sum.copy()

    def ledger(self, weight: Weight) -> FloatArray:
        """Independent read-only export; never expose writable trainer arrays."""
        if weight not in ("uniform", "linear"):
            raise ValueError("unknown batch average weight")
        result = (self.uniform_sum if weight == "uniform" else self.strategy_sum).copy()
        result.flags.writeable = False
        return result

    def readout_fingerprint(self, weight: Weight) -> str:
        # A private shallow projection is used only by the frozen old hasher.
        # Its selected ledger is copied; no projection escapes or trains.
        projection = copy.copy(self)
        projection.strategy_sum = self.ledger(weight)
        return fingerprint(projection)

    def step(self) -> None:
        if self.batch_size == 1:
            super().step()
            self.sampled_traversals += 2
            return
        t = self.iteration + 1
        sizes = []
        for target in (0, 1):
            cache: dict[int, FloatArray] = {}

            def frozen(
                key: str, actions: tuple[int, ...], cache: dict[int, FloatArray] = cache
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

            update = mean_updates(
                (
                    external_updates(self.cached_nodes[0], target, frozen, select)
                    for _ in range(self.batch_size)
                ),
                self.batch_size,
            )
            self._apply(update, target, t)
            self.nodes_visited += update.visited
            self.sampled_traversals += self.batch_size
            sizes.append(len(cache))
        self.last_pass_rows = sizes[0], sizes[1]
        self.iteration = t


def guard(solver: FrozenBatchTrainer) -> str:
    """Bind both ledgers/warm origin and every observable old/new counter."""
    digest = hashlib.sha256(fingerprint(solver).encode())
    for array in (solver.uniform_sum, solver.warm_sum):
        digest.update(np.asarray(array, dtype="<f8").tobytes())
    digest.update(
        json.dumps(
            [
                solver.iteration,
                solver.nodes_visited,
                solver.initialization_visits,
                solver.row_evaluations,
                solver.last_pass_rows,
                solver.sampled_traversals,
                solver.batch_size,
                [
                    solver.rules.regret_rule,
                    solver.rules.regret_weight,
                    solver.rules.average_weight,
                ],
                solver.average_phase,
                solver.average_mass,
                solver.traversal,
            ]
        ).encode()
    )
    return digest.hexdigest()


@dataclass(frozen=True)
class BatchPoint:
    labels: tuple[int, ...]
    iteration: int
    previous_work: int
    total_work: int
    last_iteration_visits: int
    guard_sha256: str


def observe(
    solver: FrozenBatchTrainer,
    labels: Sequence[int],
    capture: Callable[[BatchPoint], None],
    deadline: Deadline,
) -> None:
    """First complete iteration crossings, guarding both average books and RNG."""
    if (
        not labels
        or list(labels) != sorted(set(labels))
        or any(type(x) is not int or x <= 0 for x in labels)
        or solver.iteration != 1
        or solver.nodes_visited != solver.initialization_visits
    ):
        raise ValueError("batch observer requires fresh exact initialization/labels")
    pending = list(labels)
    previous, last = 0, solver.nodes_visited
    while pending:
        deadline.check()
        crossed = tuple(x for x in pending if x <= solver.nodes_visited)
        if crossed:
            if any(previous >= x for x in crossed):
                raise ArithmeticError("missed first batch work crossing")
            before = guard(solver)
            capture(
                BatchPoint(
                    crossed,
                    solver.iteration,
                    previous,
                    solver.nodes_visited,
                    last,
                    before,
                )
            )
            if guard(solver) != before:
                raise ArithmeticError("batch observer mutated training state")
            pending = [x for x in pending if x not in crossed]
        if pending:
            previous = solver.nodes_visited
            solver.step()
            last = solver.nodes_visited - previous
