"""Explicit nonuniform Kuhn IO exercises, never poker timing or strength evidence."""

import copy
import time
from pathlib import Path
from typing import Any

from numpy.random import PCG64, Generator

from poker_ai.evaluation.averaging_history_artifacts import array_sha
from poker_ai.evaluation.averaging_history_software import toy_context
from poker_ai.evaluation.batch_reduction_run import measure_paths
from poker_ai.evaluation.batch_reduction_validation import gather
from poker_ai.evaluation.frozen_batch_inputs import paths
from poker_ai.evaluation.frozen_batch_profile import measure
from poker_ai.postflop.cached_nodes import CachedNodeTrainer
from poker_ai.postflop.cell_process import Send, run_batch
from poker_ai.postflop.controlled_training import Rules, Weight
from poker_ai.postflop.river_study import Deadline
from poker_ai.postflop.row_profile import fingerprint

SCOPE = "EXPLICIT_NONUNIFORM_KUHN_SOFTWARE_NOT_POKER_RESULTS"


def prepare(
    config: dict[str, Any], deadline: Deadline
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    config = copy.deepcopy(config)
    config["status"] = SCOPE
    config["spot_files"] = [
        "EXPLICIT_TOY_" + Path(x).name for x in config["spot_files"]
    ]
    tree = toy_context().partition
    originals = {}
    weights: tuple[Weight, ...] = ("uniform", "linear")
    for seed in config["seeds"]:
        for clip in ("signed", "clipped"):
            original: dict[str, dict[int, Any]] = {}
            for weight in weights:
                solver = CachedNodeTrainer(
                    tree, Generator(PCG64(seed)), rules=Rules(clip, "linear", weight)
                )
                solver.initialize_exact()
                previous = 0
                while solver.nodes_visited < 100000:
                    deadline.check()
                    previous = solver.nodes_visited
                    solver.step()
                original[weight] = {
                    100000: dict(
                        id=f"EXPLICIT_TOY_{seed}_{clip}_{weight}",
                        iteration=solver.iteration,
                        previous_work=previous,
                        total_work=solver.nodes_visited,
                        last_iteration_visits=solver.nodes_visited - previous,
                        initialization_visits=solver.initialization_visits,
                        state_sha256=fingerprint(solver),
                        receipt=dict(policy_sha256=array_sha(solver.average_policy)),
                    )
                }
            originals[seed, clip] = original
    bases = {}
    rows = []
    for i, path in enumerate(paths(config)):
        key = path["seed"], path["batch_size"], path["regret_rule"]
        if key not in bases:
            bases[key] = measure(
                tree, path, originals[path["seed"], path["regret_rule"]], 0, deadline
            )
        row = copy.deepcopy(bases[key])
        row.update(index=i, path=path)
        rows.append(row)
    return config, rows


def job(
    slot: int, indices: list[int], payload: dict[str, Any], send: Send
) -> dict[str, Any]:
    del slot
    deadline = Deadline(payload["remaining_seconds"])
    context = toy_context()
    contexts = {
        (r["path"]["spot_file"], r["path"]["representation"]): context
        for r in payload["peers"]
    }
    return measure_paths(indices, payload, send, contexts, deadline)


def exercise(
    config: dict[str, Any],
    peers: list[dict[str, Any]],
    repeats: int,
    deadline: Deadline,
) -> dict[str, Any]:
    batch: dict[str, Any] = {}
    run_batch(
        72,
        3,
        job,
        dict(
            peers=peers,
            repeats=repeats,
            remaining_seconds=deadline.seconds
            - (time.perf_counter() - deadline.started),
        ),
        deadline,
        batch,
    )
    rows = gather(batch, peers, repeats, config)
    return dict(scope=SCOPE, batch=batch, rows=rows)
