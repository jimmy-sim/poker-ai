"""Plain/instrumented copies of the frozen measurement, without a new forecast."""

import cProfile
import time
from pathlib import Path
from typing import Any

from poker_ai.evaluation import batch_cost_stats
from poker_ai.evaluation.frozen_batch_profile import measure
from poker_ai.finite import ArrayTree
from poker_ai.postflop import pipeline_cost
from poker_ai.postflop.cell_process import Send
from poker_ai.postflop.parallel_profile import same
from poker_ai.postflop.river_study import Deadline


def original_prefixes(source: dict[str, Any]) -> dict[str, dict[int, Any]]:
    """Repackage already validated OWN prefix checks, never reference values."""
    if source["path"]["batch_size"] != 1:
        return {}
    result = {}
    for row in source["prefix_checks"]:
        result[row["average_weight"]] = {
            100000: dict(
                id=row["original_id"],
                receipt=dict(policy_sha256=row["policy_sha256"]),
                **{
                    k: row[k]
                    for k in (
                        "iteration",
                        "previous_work",
                        "total_work",
                        "last_iteration_visits",
                        "initialization_visits",
                        "state_sha256",
                    )
                },
            )
        }
    if set(result) != {"uniform", "linear"}:
        raise ArithmeticError("archived own B1 prefix checks incomplete")
    return result


def one(
    root: Path,
    tree: ArrayTree,
    source: dict[str, Any],
    index: int,
    mode: str,
    config: dict[str, Any],
    deadline: Deadline,
) -> dict[str, Any]:
    if mode not in ("plain", "instrumented"):
        raise ValueError("unknown cost mode")
    before = time.perf_counter()
    stats = None
    if mode == "instrumented":
        profiler = cProfile.Profile()
        endpoint = profiler.runcall(
            measure, tree, source["path"], original_prefixes(source), 0, deadline
        )
        seconds = time.perf_counter() - before
        stats = batch_cost_stats.extract(profiler, root)
        calls = batch_cost_stats.call_accounting(stats, endpoint)
    else:
        endpoint = measure(tree, source["path"], original_prefixes(source), 0, deadline)
        seconds = time.perf_counter() - before
        calls = None
    if any(
        not same(endpoint[k], source[k]) for k in config["expected_endpoint_fields"]
    ):
        raise ArithmeticError(
            "profiling changed archived state/RNG/work/prefix endpoint"
        )
    # This helper's extrapolation is invalid for instrumented cost attribution.
    # Omit that DERIVED value in both modes; all raw durations remain retained.
    endpoint.pop("projected_training_seconds")
    deadline.check()
    return dict(
        index=index,
        source_index=source["index"],
        mode=mode,
        endpoint=endpoint,
        whole_measure_seconds=seconds,
        stats=stats,
        call_accounting=calls,
    )


def job(
    slot: int, indices: list[int], payload: dict[str, Any], send: Send
) -> dict[str, Any]:
    del slot
    before = time.perf_counter()
    root = Path(payload["root"])
    contexts = pipeline_cost.contexts(root, payload["comparison"])
    deadline = Deadline(payload["remaining_seconds"])
    send(dict(kind="prepared", seconds=time.perf_counter() - before))
    for index in indices:
        source = payload["selected"][index]
        context = contexts[
            source["path"]["spot_file"], source["path"]["representation"]
        ]
        for mode in payload["config"]["modes"]:
            deadline.check()
            send(
                dict(
                    kind="prepared", phase="measurement_started", index=index, mode=mode
                )
            )
            row = one(
                root,
                context.partition,
                source,
                index,
                mode,
                payload["config"],
                deadline,
            )
            send(dict(kind="cell", index=index, row=row))
    return dict(
        paths=len(indices), endpoints=2 * len(indices), function_profiles=len(indices)
    )
