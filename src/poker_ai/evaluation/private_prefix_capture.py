"""Own capture before scoring: all three readouts and both books, fixed work."""

import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np
from numpy.random import PCG64, Generator

from poker_ai.evaluation.averaging_history_artifacts import array_sha, write_mass
from poker_ai.evaluation.averaging_history_math import coverage, movement, window_mass
from poker_ai.evaluation.private_prefix_design import READOUTS, WEIGHTS, Design
from poker_ai.finite import FloatArray
from poker_ai.postflop.cell_process import Send
from poker_ai.postflop.controlled_checkpoints import write_snapshot
from poker_ai.postflop.controlled_scoring import ScoringContext
from poker_ai.postflop.controlled_training import Rules
from poker_ai.postflop.frozen_batches import BatchPoint
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.river_study import Deadline
from poker_ai.postflop.stratified_batches import StratifiedBatchTrainer, observe


def collect(
    context: ScoringContext,
    design: Design,
    index: int,
    scratch: Path,
    binding: str,
    send: Send,
    deadline: Deadline,
) -> dict[str, Any]:
    """No score/reference or external strategy is supplied to the learner."""
    started, cpu = time.perf_counter(), time.process_time()
    path = design.paths[index]
    deadline.check()
    solver = StratifiedBatchTrainer(
        context.partition,
        Generator(PCG64(path["seed"])),
        batch_size=path["batch_size"],
        rules=Rules(path["regret_rule"], "linear", "linear"),
    )
    solver.initialize_exact()
    setup = time.perf_counter() - started
    send(
        dict(
            kind="cell",
            phase="training_initialized",
            index=index,
            total_work=solver.nodes_visited,
            iteration=solver.iteration,
        )
    )
    assert solver.prefix_plan is not None
    plan_hash = sha(asdict(solver.prefix_plan))
    first = np.unique(context.exact_to_partition, return_index=True)[1]
    river = (context.river_masks[0] | context.river_masks[1])[first]
    previous: FloatArray | None = None
    count = 0
    previous_guard: str | None = None

    def capture(point: BatchPoint) -> None:
        nonlocal previous, count, previous_guard
        current = solver.current_policy
        changes = (
            movement(context.partition, previous, current)
            if previous is not None
            else None
        )
        common = dict(
            iteration=point.iteration,
            previous_work=point.previous_work,
            total_work=point.total_work,
            last_iteration_visits=point.last_iteration_visits,
            initialization_visits=solver.initialization_visits,
            sampled_traversals=solver.sampled_traversals,
            guard_sha256=point.guard_sha256,
            current_sha256=array_sha(current),
            prefix_plan_sha256=plan_hash,
            source_sha256=binding,
            current_movement=changes,
            previous_capture_guard_sha256=previous_guard,
            initialization_seconds=setup,
            prefix_setup_seconds=solver.prefix_setup_seconds,
        )
        policies = {"current": current}
        support = {}
        for label in point.labels:
            per_label = dict(common, overshoot=point.total_work - label)
            for weight in WEIGHTS:
                deadline.check()
                mass = solver.ledger(weight)  # type: ignore[arg-type]
                metadata = dict(**design.mass(index, label, weight), **per_label)
                filename = "masses/" + metadata["id"] + ".json.gz"
                receipt = write_mass(
                    scratch / filename, context.partition, mass, metadata
                )
                send(
                    dict(
                        kind="cell",
                        phase="mass",
                        index=index,
                        row=dict(
                            **metadata,
                            file=filename,
                            receipt=receipt,
                            metadata_sha256=sha(metadata),
                        ),
                    )
                )
                policies[weight + "_average"] = context.partition.normalize(mass)
                support[weight + "_average"] = dict(
                    whole=coverage(context.partition, mass, river),
                    post_warm=coverage(
                        context.partition,
                        window_mass(context.partition, solver.warm_sum, mass),
                        river,
                    ),
                )
            for readout in READOUTS:
                deadline.check()
                metadata = dict(
                    **design.profile(index, label, readout),
                    **per_label,
                    coverage=support.get(readout),
                )
                filename = "captures/" + metadata["id"] + ".json.gz"
                receipt = write_snapshot(
                    scratch / filename, context.partition, policies[readout], metadata
                )
                send(
                    dict(
                        kind="cell",
                        phase="capture",
                        index=index,
                        row=dict(
                            **metadata,
                            file=filename,
                            receipt=receipt,
                            metadata_sha256=sha(metadata),
                        ),
                    )
                )
                count += 1
        previous = current.copy()
        previous_guard = point.guard_sha256

    observe(solver, design.labels, capture, deadline)
    if count != 9:
        raise ArithmeticError("complete private-prefix readout capture required")
    deadline.check()
    return dict(
        paths=1,
        captures=count,
        masses=6,
        iteration=solver.iteration,
        nodes_visited=solver.nodes_visited,
        seconds=time.perf_counter() - started,
        cpu_seconds=time.process_time() - cpu,
    )
