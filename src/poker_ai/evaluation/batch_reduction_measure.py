"""Explicit reduction backend measurement; original prefix observer is unchanged."""

import time
from typing import Any

from numpy.random import PCG64, Generator

from poker_ai.evaluation import frozen_batch_inputs as inputs
from poker_ai.finite import ArrayTree
from poker_ai.postflop.batch_reduction import ReducedDispatchBatchTrainer
from poker_ai.postflop.controlled_training import Rules
from poker_ai.postflop.frozen_batches import BatchPoint, guard, observe
from poker_ai.postflop.river_study import Deadline


def trainer(tree: ArrayTree, path: dict[str, Any]) -> ReducedDispatchBatchTrainer:
    return ReducedDispatchBatchTrainer(
        tree,
        Generator(PCG64(path["seed"])),
        batch_size=path["batch_size"],
        rules=Rules(path["regret_rule"], "linear", "linear"),
    )


def measure(
    tree: ArrayTree,
    path: dict[str, Any],
    original: dict[str, dict[int, Any]],
    repetition: int,
    deadline: Deadline,
) -> dict[str, Any]:
    """No EV/BR scoring; prefix learning work is explicitly disclosed."""
    started, cpu = time.perf_counter(), time.process_time()
    solver = trainer(tree, path)
    solver.initialize_exact()
    setup = time.perf_counter() - started
    initialization = solver.nodes_visited
    if initialization >= 100000:
        raise ArithmeticError("declared prefix timing assumes warm work below 100k")
    checks: list[dict[str, Any]] = []
    endpoint: BatchPoint | None = None

    def capture(point: BatchPoint) -> None:
        nonlocal endpoint
        if 100000 in point.labels and path["batch_size"] == 1:
            checks.extend(inputs.check_prefix(solver, point, 100000, original))
        if initialization + 100000 in point.labels:
            endpoint = point

    before = time.perf_counter()
    observe(solver, [100000, initialization + 100000], capture, deadline)
    seconds = time.perf_counter() - before
    if endpoint is None:
        raise ArithmeticError("missing prefix timing endpoint")
    incremental = solver.nodes_visited - initialization
    return dict(
        path=path,
        repetition=repetition,
        initialization_visits=initialization,
        setup_and_warm_seconds=setup,
        incremental_seconds=seconds,
        incremental_visits=incremental,
        total_work=solver.nodes_visited,
        previous_work=endpoint.previous_work,
        last_iteration_visits=endpoint.last_iteration_visits,
        iteration=solver.iteration,
        sampled_traversals=solver.sampled_traversals,
        overshoot=incremental - 100000,
        guard_sha256=guard(solver),
        readout_sha256={w: solver.readout_fingerprint(w) for w in inputs.WEIGHTS},
        prefix_checks=checks,
        cpu_seconds=time.process_time() - cpu,
        projected_training_seconds=setup
        + seconds * (10000000 - initialization) / incremental,
    )
