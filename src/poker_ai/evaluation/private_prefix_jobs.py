"""Fixed spawned own-prefix/trajectory jobs, no reference or strategy inputs."""

import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

from numpy.random import PCG64, Generator

from poker_ai.evaluation.private_prefix_capture import collect
from poker_ai.evaluation.private_prefix_design import Design
from poker_ai.evaluation.private_prefix_sources import load, source
from poker_ai.postflop.cell_process import Send
from poker_ai.postflop.controlled_training import Rules
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.river_study import Deadline, digest
from poker_ai.postflop.stratified_batches import StratifiedBatchTrainer, guard


def timing(
    slot: int, indices: list[int], payload: dict[str, Any], send: Send
) -> dict[str, Any]:
    del slot
    root = Path(payload["root"])
    if sha(source(root)["sha256"]) != payload["binding"]:
        raise ArithmeticError("profiling worker source differs from checked source")
    deadline = Deadline(payload["remaining_seconds"])
    sources = load(root)
    send(dict(kind="prepared", phase="complete_original_sources_loaded"))
    count = 0
    for global_index in indices:
        deadline.check()
        rep, index = divmod(global_index, 48)
        context = sources.context(index)
        path = sources.design.paths[index]
        started, cpu = time.perf_counter(), time.process_time()
        learner = StratifiedBatchTrainer(
            context.partition,
            Generator(PCG64(path["seed"])),
            batch_size=path["batch_size"],
            rules=Rules(path["regret_rule"], "linear", "linear"),
        )
        learner.initialize_exact()
        setup = time.perf_counter() - started
        before = learner.nodes_visited
        target = before + 100000
        sampled = time.perf_counter()
        previous, last = before, 0
        while learner.nodes_visited < target:
            deadline.check()
            previous = learner.nodes_visited
            learner.step()
            last = learner.nodes_visited - previous
        incremental = time.perf_counter() - sampled
        row = dict(
            repeat=rep,
            index=index,
            global_index=global_index,
            path=path,
            source_sha256=payload["binding"],
            backend="StratifiedBatchTrainer",
            initialization_visits=learner.initialization_visits,
            incremental_visits=learner.nodes_visited - before,
            total_work=learner.nodes_visited,
            previous_work=previous,
            last_iteration_visits=last,
            iteration=learner.iteration,
            sampled_traversals=learner.sampled_traversals,
            guard_sha256=guard(learner),
            prefix_plan_sha256=sha(asdict(learner.prefix_plan))
            if learner.prefix_plan
            else None,
            setup_seconds=setup,
            incremental_seconds=incremental,
            seconds=time.perf_counter() - started,
            cpu_seconds=time.process_time() - cpu,
            reference_constructed=False,
        )
        send(dict(kind="cell", phase="timing", index=global_index, row=row))
        count += 1
    return dict(paths=len(indices), timing_rows=count)


def training(
    slot: int, indices: list[int], payload: dict[str, Any], send: Send
) -> dict[str, Any]:
    del slot
    root = Path(payload["root"])
    from poker_ai.evaluation.private_prefix_admission import ADMISSION

    if (
        digest(root / ADMISSION) != payload["admission_sha256"]
        or sha(source(root)["sha256"]) != payload["binding"]
    ):
        raise ArithmeticError(
            "worker admission/source changed after parent verification"
        )
    deadline = Deadline(payload["remaining_seconds"])
    sources = load(root)
    design = Design.build(payload["config"], mode="real")
    send(dict(kind="prepared", phase="complete_original_sources_loaded"))
    count = 0
    for index in indices:
        deadline.check()
        send(dict(kind="cell", phase="training_started", index=index))
        result = collect(
            sources.context(index),
            design,
            index,
            Path(payload["scratch"]),
            payload["binding"],
            send,
            deadline,
        )
        send(dict(kind="cell", phase="trained", index=index, result=result))
        count += 1
    return dict(paths=count, captures=count * 9, masses=count * 6)
