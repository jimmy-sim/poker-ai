"""Optional private-prefix stratification; unchanged target updater/dual books.

B1 delegates the old step exactly. B>1 changes joint private-deal sampling and
RNG consumption only; original external traversal counts both chance nodes.
This foundation provides no real-study admission or default-agent replacement.
"""

import hashlib
import json
import time
from collections.abc import Callable, Iterator, Sequence
from dataclasses import asdict, replace

from numpy.random import Generator

from poker_ai.finite import ArrayTree, FloatArray
from poker_ai.postflop.batch_reduction import (
    ReducedDispatchBatchTrainer,
    array_mean_updates,
)
from poker_ai.postflop.controlled_training import Rules
from poker_ai.postflop.frozen_batches import BatchPoint
from poker_ai.postflop.frozen_batches import guard as old_guard
from poker_ai.postflop.frozen_batches import observe as old_observe
from poker_ai.postflop.private_prefix import PrefixPlan, PrefixSelector, stratum_point
from poker_ai.postflop.river_study import Deadline
from poker_ai.training.mccfr import Updates, external_updates


class StratifiedBatchTrainer(ReducedDispatchBatchTrainer):
    def __init__(
        self,
        tree: ArrayTree,
        rng: Generator,
        *,
        batch_size: int,
        rules: Rules | None = None,
    ) -> None:
        if type(batch_size) is not int or not 1 <= batch_size <= 2**53:
            raise ValueError("invalid stratified batch size")
        super().__init__(tree, rng, batch_size=batch_size, rules=rules)
        started = time.perf_counter()
        self.prefix_plan = (
            PrefixPlan.build(self.cached_nodes[0]) if batch_size > 1 else None
        )
        self.prefix_setup_seconds = time.perf_counter() - started

    def step(self) -> None:
        if self.batch_size == 1:
            super().step()
            return
        if self.prefix_plan is None:
            raise ArithmeticError("stratified batch requires its checked prefix plan")
        plan = self.prefix_plan
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

            def samples(target: int = target) -> Iterator[Updates]:
                for i in range(self.batch_size):
                    selector = PrefixSelector(
                        plan,
                        stratum_point(i, self.batch_size, float(self.rng.random())),
                        self.rng,
                    )
                    update = external_updates(
                        self.cached_nodes[0], target, frozen, selector
                    )
                    selector.finish()
                    yield update

            update = array_mean_updates(samples(), self.batch_size)
            self._apply(update, target, t)
            self.nodes_visited += update.visited
            self.sampled_traversals += self.batch_size
            sizes.append(len(cache))
        self.last_pass_rows = sizes[0], sizes[1]
        self.iteration = t


def guard(solver: StratifiedBatchTrainer) -> str:
    """Old observable state plus immutable plan; timing is metadata, not state."""
    plan = asdict(solver.prefix_plan) if solver.prefix_plan is not None else None
    return hashlib.sha256(
        json.dumps([old_guard(solver), plan], sort_keys=True).encode()
    ).hexdigest()


def observe(
    solver: StratifiedBatchTrainer,
    labels: Sequence[int],
    capture: Callable[[BatchPoint], None],
    deadline: Deadline,
) -> None:
    """Old first-complete-crossing observer, additionally bind/check the plan."""

    def checked(point: BatchPoint) -> None:
        before = guard(solver)
        capture(replace(point, guard_sha256=before))
        if guard(solver) != before:
            raise ArithmeticError("stratified observer mutated training state or plan")

    old_observe(solver, labels, checked, deadline)
