"""Complete fixed-cost timing, repeated states and unaltered compute forecast."""

import json
import math
import os
import time
from pathlib import Path
from typing import Any

from poker_ai.evaluation import frozen_batch_inputs as inputs
from poker_ai.finite import ArrayTree
from poker_ai.postflop import pipeline_cost
from poker_ai.postflop.cell_process import Send, partition, run_batch
from poker_ai.postflop.frozen_batches import BatchPoint, guard, observe
from poker_ai.postflop.learning_run import persist
from poker_ai.postflop.learning_validation import number
from poker_ai.postflop.parallel_profile import same
from poker_ai.postflop.river_study import Deadline
from poker_ai.reproducibility import runtime_environment


def measure(
    tree: ArrayTree,
    path: dict[str, Any],
    original: dict[str, dict[int, Any]],
    repetition: int,
    deadline: Deadline,
) -> dict[str, Any]:
    """No EV/BR scoring; prefix learning work is explicitly disclosed."""
    started, cpu = time.perf_counter(), time.process_time()
    solver = inputs.trainer(tree, path)
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


def profile_job(
    slot: int, indices: list[int], payload: dict[str, Any], send: Send
) -> dict[str, Any]:
    del slot
    started = time.perf_counter()
    contexts = pipeline_cost.contexts(Path(payload["root"]), payload["comparison"])
    deadline = Deadline(payload["remaining_seconds"])
    send(dict(kind="prepared", seconds=time.perf_counter() - started))
    for index in indices:
        path = payload["paths"][index]
        tree = contexts[path["spot_file"], path["representation"]].partition
        for repeat in range(3):
            deadline.check()
            row = measure(tree, path, payload["prefixes"][index], repeat, deadline)
            send(dict(kind="cell", index=index, row=row))
    return dict(paths=len(indices), timing_rows=3 * len(indices))


def forecast(rows: list[dict[str, Any]], config: dict[str, Any]) -> dict[str, Any]:
    """Recompute from every original row, never trust a stored favorable summary."""
    selected = inputs.paths(config)
    if len(selected) != 72 or len(rows) != 216:
        raise ArithmeticError("incomplete fixed timing grid")
    by_path: dict[int, list[dict[str, Any]]] = {}
    for row in rows:
        index, rep = row["index"], row["repetition"]
        hashes = [row["guard_sha256"], *row["readout_sha256"].values()]
        if set(row["readout_sha256"]) != {"uniform", "linear"} or any(
            not isinstance(h, str)
            or len(h) != 64
            or any(c not in "0123456789abcdef" for c in h)
            for h in hashes
        ):
            raise ArithmeticError("invalid timing state/readout fingerprints")
        if (
            type(index) is not int
            or not 0 <= index < 72
            or type(rep) is not int
            or rep not in (0, 1, 2)
            or not same(row["path"], selected[index])
        ):
            raise ArithmeticError("timing identity changed")
        for k in (
            "initialization_visits",
            "incremental_visits",
            "total_work",
            "previous_work",
            "last_iteration_visits",
            "iteration",
            "sampled_traversals",
            "overshoot",
        ):
            if type(row[k]) is not int or row[k] < 0:
                raise ArithmeticError("timing work must be typed nonnegative integers")
        initial, actual = row["initialization_visits"], row["incremental_visits"]
        if (
            not 0 < initial < 100000
            or not 100000 <= actual < 100000 + row["last_iteration_visits"]
            or row["overshoot"] != actual - 100000
            or row["total_work"] != initial + actual
            or not row["previous_work"] < initial + 100000 <= row["total_work"]
            or row["previous_work"] + row["last_iteration_visits"] != row["total_work"]
            or row["sampled_traversals"]
            != 2 * row["path"]["batch_size"] * (row["iteration"] - 1)
        ):
            raise ArithmeticError("timing did not charge first whole-batch crossing")
        for k in (
            "setup_and_warm_seconds",
            "incremental_seconds",
            "cpu_seconds",
            "projected_training_seconds",
        ):
            if not number(row[k], nonnegative=True) or row[k] <= 0:
                raise ArithmeticError("invalid batch timing duration")
        projected = (
            row["setup_and_warm_seconds"]
            + row["incremental_seconds"] * (10000000 - initial) / actual
        )
        if not math.isclose(
            projected, row["projected_training_seconds"], rel_tol=0, abs_tol=1e-9
        ):
            raise ArithmeticError("timing projection changed")
        by_path.setdefault(index, []).append(row)
    maxima = []
    count = 0
    repeat_keys = (
        "guard_sha256",
        "readout_sha256",
        "initialization_visits",
        "incremental_visits",
        "total_work",
        "previous_work",
        "last_iteration_visits",
        "iteration",
        "sampled_traversals",
        "overshoot",
        "prefix_checks",
    )
    for index in range(72):
        cell = by_path.get(index, [])
        if sorted(r["repetition"] for r in cell) != [0, 1, 2]:
            raise ArithmeticError("duplicate/missing timing repetition")
        for row in cell:
            if any(not same(row[k], cell[0][k]) for k in repeat_keys):
                raise ArithmeticError("repeated batch timing states changed")
            expected = 2 if selected[index]["batch_size"] == 1 else 0
            if len(row["prefix_checks"]) != expected:
                raise ArithmeticError("baseline timing prefix inventory changed")
            count += expected
        maxima.append(max(r["projected_training_seconds"] for r in cell))
    partitions = []
    for chosen in (list(range(24)), list(range(24, 72))):
        partitions.append(
            [
                math.fsum(maxima[chosen[i]] for i in part)
                for part in partition(len(chosen), 3)
            ]
        )
    training = math.fsum(max(p) for p in partitions)
    guarded = 2 * (2 * training + 600)
    return dict(
        paths=72,
        timing_rows=216,
        repeated_B1_readout_prefix_checks=count,
        baseline_partition_seconds=partitions[0],
        other_partition_seconds=partitions[1],
        training_barrier_forecast_seconds=training,
        guarded_own_seconds=guarded,
        cap_seconds=7200,
        decision="fits_requires_checked_admission"
        if guarded < 7200
        else "exceeds_cap_stop_before_long_learning",
        new_postflop_prefix_training=True,
        strength_scores_measured=False,
    )


def gather(batch: dict[str, Any], config: dict[str, Any]) -> list[dict[str, Any]]:
    if (
        batch["status"] != "completed"
        or batch["failure"] is not None
        or not same(batch["assignments"], partition(72, 3))
        or len(batch["workers"]) != 3
    ):
        raise ArithmeticError("incomplete timing worker batch")
    rows = []
    for slot, (worker, assigned) in enumerate(
        zip(batch["workers"], batch["assignments"], strict=True)
    ):
        if not same(worker["slot"], slot) or not same(worker["exitcode"], 0):
            raise ArithmeticError("timing worker failed")
        events = [e for e in worker["messages"] if e["kind"] == "cell"]
        for event in events:
            if type(event["index"]) is not int or event["index"] not in assigned:
                raise ArithmeticError("timing row assigned incorrectly")
            rows.append(dict(index=event["index"], **event["row"]))
        done = [e for e in worker["messages"] if e["kind"] == "done"]
        if len(done) != 1 or not same(
            done[0]["summary"], dict(paths=len(assigned), timing_rows=3 * len(assigned))
        ):
            raise ArithmeticError("timing worker completion incomplete")
    rows.sort(key=lambda r: (r["index"], r["repetition"]))
    forecast(rows, config)
    return rows


def run(root: Path, output: Path) -> dict[str, Any]:
    from poker_ai.evaluation.frozen_batch_protocol import require_code_checks

    if output.exists() or output.with_suffix(".tmp").exists():
        raise FileExistsError("retain batch timing attempt")
    started, cpu, children = time.perf_counter(), time.process_time(), os.times()
    config = inputs.config_inputs(root)
    current, binding = inputs.binding(root)
    require_code_checks(root, config)
    env = runtime_environment()
    if any(env[k] != config["prefix_runtime"][k] for k in ("python", "numpy")):
        raise ArithmeticError("batch prefix timing requires original runtime")
    deadline = Deadline(900)
    deadline.started = started
    saved: dict[str, Any] = dict(
        format=inputs.PROFILE,
        status="running",
        failure=None,
        config=config,
        source=current,
        source_sha256=binding,
        environment=env,
        batch={},
        rows=[],
        forecast=None,
        new_postflop_training_performed=True,
        strength_scores_measured=False,
        seconds=0.0,
    )
    persist(output, saved)
    try:
        data = inputs.prerequisites(root)
        selected = inputs.paths(config)
        comparison = json.loads((root / "configs/training-isolation.json").read_text())[
            "future_comparison"
        ]
        run_batch(
            72,
            3,
            profile_job,
            dict(
                root=str(root),
                comparison=comparison,
                paths=selected,
                prefixes=[inputs.prefix_map(data, p) for p in selected],
                remaining_seconds=900 - (time.perf_counter() - started),
            ),
            deadline,
            saved["batch"],
        )
        saved["rows"] = gather(saved["batch"], config)
        saved["forecast"] = forecast(saved["rows"], config)
        deadline.check()
        saved["status"] = "completed_timing_not_strength"
    except BaseException as error:
        saved.update(
            status="incomplete",
            failure=dict(type=type(error).__name__, reason=str(error)),
        )
        raise
    finally:
        saved["seconds"] = time.perf_counter() - started
        saved["parent_cpu_seconds"] = time.process_time() - cpu
        now = os.times()
        saved["reaped_children_cpu_seconds"] = (
            now.children_user
            + now.children_system
            - children.children_user
            - children.children_system
        )
        persist(output, saved)
    return saved
