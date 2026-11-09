"""Real profiling on explicit nonuniform Kuhn fixtures, never poker cost results."""

import copy
from pathlib import Path
from typing import Any

from numpy.random import PCG64, Generator

from poker_ai.evaluation.averaging_history_artifacts import array_sha
from poker_ai.evaluation.averaging_history_software import toy_context
from poker_ai.evaluation.batch_cost_profile import one
from poker_ai.evaluation.batch_cost_validation import gather
from poker_ai.evaluation.frozen_batch_profile import measure
from poker_ai.postflop.cached_nodes import CachedNodeTrainer
from poker_ai.postflop.cell_process import Send, run_batch
from poker_ai.postflop.controlled_training import Rules, Weight
from poker_ai.postflop.river_study import Deadline
from poker_ai.postflop.row_profile import fingerprint

ROOT = Path(__file__).resolve().parents[3]
SCOPE = "EXPLICIT_NONUNIFORM_KUHN_SOFTWARE_NOT_POKER_COST_RESULTS"


def prepare(
    config: dict[str, Any], source_rows: list[dict[str, Any]], deadline: Deadline
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    config = copy.deepcopy(config)
    config["status"] = SCOPE
    from poker_ai.reproducibility import runtime_environment

    config["prefix_runtime"] = runtime_environment()
    tree = toy_context().partition
    originals: dict[str, dict[str, dict[int, Any]]] = {}
    weights: tuple[Weight, ...] = ("uniform", "linear")
    for clip in ("signed", "clipped"):
        original: dict[str, dict[int, Any]] = {}
        for weight in weights:
            solver = CachedNodeTrainer(
                tree, Generator(PCG64(20261301)), rules=Rules(clip, "linear", weight)
            )
            solver.initialize_exact()
            previous = 0
            while solver.nodes_visited < 100000:
                deadline.check()
                previous = solver.nodes_visited
                solver.step()
            original[weight] = {
                100000: dict(
                    id=f"EXPLICIT_TOY_{clip}_{weight}",
                    iteration=solver.iteration,
                    previous_work=previous,
                    total_work=solver.nodes_visited,
                    last_iteration_visits=solver.nodes_visited - previous,
                    initialization_visits=solver.initialization_visits,
                    state_sha256=fingerprint(solver),
                    receipt=dict(policy_sha256=array_sha(solver.average_policy)),
                )
            }
        originals[clip] = original
    bases = {}
    selected = []
    for row in source_rows:
        path = copy.deepcopy(row["path"])
        path["spot_file"] = "EXPLICIT_TOY_" + Path(path["spot_file"]).stem
        key = path["batch_size"], path["regret_rule"]
        if key not in bases:
            bases[key] = measure(
                tree, path, originals[path["regret_rule"]], 0, deadline
            )
        source = copy.deepcopy(bases[key])
        source.update(index=row["index"], path=path)
        selected.append(source)
    return config, selected


def job(
    slot: int, indices: list[int], payload: dict[str, Any], send: Send
) -> dict[str, Any]:
    del slot
    tree = toy_context().partition
    deadline = Deadline(payload["remaining_seconds"])
    for index in indices:
        for mode in payload["config"]["modes"]:
            send(
                dict(
                    kind="prepared", phase="measurement_started", index=index, mode=mode
                )
            )
            send(
                dict(
                    kind="cell",
                    index=index,
                    row=one(
                        ROOT,
                        tree,
                        payload["selected"][index],
                        index,
                        mode,
                        payload["config"],
                        deadline,
                    ),
                )
            )
    return dict(
        paths=len(indices), endpoints=2 * len(indices), function_profiles=len(indices)
    )


def exercise(
    config: dict[str, Any], source_rows: list[dict[str, Any]], deadline: Deadline
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    import time

    config, selected = prepare(config, source_rows, deadline)
    batch: dict[str, Any] = {}
    run_batch(
        24,
        3,
        job,
        dict(
            config=config,
            selected=selected,
            remaining_seconds=deadline.seconds
            - (time.perf_counter() - deadline.started),
        ),
        deadline,
        batch,
    )
    rows = gather(batch, selected, config)
    return dict(scope=SCOPE, config=config, rows=rows, batch=batch), selected
