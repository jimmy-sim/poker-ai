"""Fixed complete 72-row max-per-context forecast; no favorable subset/retry."""

import math
import time
from pathlib import Path
from typing import Any

from poker_ai.evaluation import matched_update_inputs as inputs
from poker_ai.evaluation import reduced_study_inputs as study
from poker_ai.evaluation.matched_update_capture import checkpoint
from poker_ai.postflop.cell_process import Send
from poker_ai.postflop.coordinate_observer import CoordinatePoint, observe
from poker_ai.postflop.frozen_batches import guard
from poker_ai.postflop.parallel_profile import same
from poker_ai.postflop.river_study import Deadline


def measure(
    sources: inputs.Sources, index: int, repetition: int, deadline: Deadline
) -> dict[str, Any]:
    context, path = sources.context(index), sources.paths[index]
    started, cpu = time.perf_counter(), time.process_time()
    solver = study.trainer(context.partition, path)
    solver.initialize_exact()
    setup = time.perf_counter() - started
    initialization = solver.initialization_visits
    if initialization >= 100000:
        raise ArithmeticError("fixed prefix timing requires warm work below100k")
    checked: list[dict[str, Any]] = []
    endpoint: CoordinatePoint | None = None

    def capture(point: CoordinatePoint) -> None:
        nonlocal endpoint
        if 100000 in point.work_labels:
            checked.append(checkpoint(solver, point, sources.original(index, 100000)))
        if initialization + 100000 in point.work_labels:
            endpoint = point

    before = time.perf_counter()
    observe(
        solver,
        iterations=[],
        work=[100000, initialization + 100000],
        capture=capture,
        deadline=deadline,
    )
    elapsed = time.perf_counter() - before
    if endpoint is None or len(checked) != 1:
        raise ArithmeticError("complete short-prefix timing observation missing")
    incremental = solver.nodes_visited - initialization
    return dict(
        path_index=index,
        path=path,
        repetition=repetition,
        initialization_visits=initialization,
        setup_and_warm_seconds=setup,
        incremental_seconds=elapsed,
        incremental_visits=incremental,
        total_work=solver.nodes_visited,
        iteration=solver.iteration,
        guard_sha256=guard(solver),
        readout_sha256={w: solver.readout_fingerprint(w) for w in study.WEIGHTS},
        original_checkpoint=checked[0],
        cpu_seconds=time.process_time() - cpu,
        projected_training_seconds=setup
        + elapsed * (10000000 - initialization) / incremental,
    )


def job(
    slot: int, indices: list[int], payload: dict[str, Any], send: Send
) -> dict[str, Any]:
    del slot
    deadline = Deadline(payload["remaining_seconds"])
    sources = inputs.load(Path(payload["root"]))
    send(dict(kind="prepared", phase="profile_sources_loaded"))
    for repetition in range(3):
        for index in indices:
            deadline.check()
            row = measure(sources, index, repetition, deadline)
            send(dict(kind="cell", phase="timing", index=index, row=row))
    return dict(paths=len(indices), timing_rows=3 * len(indices))


def forecast(
    rows: list[dict[str, Any]],
    paths: list[dict[str, Any]],
    expected: list[dict[str, Any]],
) -> dict[str, Any]:
    identities = [(r["path_index"], r["repetition"]) for r in rows]
    if (
        len(paths) != 24
        or len(rows) != 72
        or set(identities) != {(i, r) for i in range(24) for r in range(3)}
    ):
        raise ArithmeticError("all72 fixed context/repetition timings required")
    original = {r["path_index"]: r for r in expected}
    if len(original) != 24:
        raise ArithmeticError("all24 source100k checks required")
    maxima = []
    for index, path in enumerate(paths):
        members = [r for r in rows if r["path_index"] == index]
        for row in members:
            if (
                type(row["path_index"]) is not int
                or type(row["repetition"]) is not int
                or not same(row["path"], path)
                or not same(row["original_checkpoint"], original[index])
            ):
                raise ArithmeticError("timing source context/checkpoint changed")
            for key in (
                "initialization_visits",
                "incremental_visits",
                "total_work",
                "iteration",
            ):
                if type(row[key]) is not int or row[key] <= 0:
                    raise ArithmeticError("invalid integer timing work")
            if (
                row["initialization_visits"] >= 100000
                or row["incremental_visits"] < 100000
                or row["total_work"]
                != row["initialization_visits"] + row["incremental_visits"]
            ):
                raise ArithmeticError("short-prefix timing work changed")
            for key in (
                "setup_and_warm_seconds",
                "incremental_seconds",
                "projected_training_seconds",
                "cpu_seconds",
            ):
                if (
                    type(row[key]) not in (int, float)
                    or not math.isfinite(row[key])
                    or row[key] <= 0
                ):
                    raise ArithmeticError("invalid finite positive timing")
            projection = (
                row["setup_and_warm_seconds"]
                + row["incremental_seconds"]
                * (10000000 - row["initialization_visits"])
                / row["incremental_visits"]
            )
            if not same(projection, row["projected_training_seconds"]):
                raise ArithmeticError("timing projection arithmetic changed")
        if any(
            not same(members[0][k], r[k])
            for r in members
            for k in ("total_work", "iteration", "guard_sha256", "readout_sha256")
        ):
            raise ArithmeticError("repeated short trajectory changed bits/work")
        maxima.append(max(r["projected_training_seconds"] for r in members))
    partitions = [math.fsum(maxima[i] for i in range(slot, 24, 3)) for slot in range(3)]
    training = max(partitions)
    guarded = 2 * (2 * training + 600)
    return dict(
        context_maxima_seconds=maxima,
        worker_partition_seconds=partitions,
        training_forecast_seconds=training,
        guarded_own_seconds=guarded,
        strict_below7200=guarded < 7200,
        timing_rows=72,
        rule="2*(2*max_fixed_partition_sum_of_context_maxima+600)",
        causal_speedup_claim=False,
        strength_results=False,
    )
