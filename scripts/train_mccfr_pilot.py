"""Reproduce small multi-seed MCCFR pilots, checkpoints and compute measurements."""

import argparse
import csv
import hashlib
import json
import multiprocessing
import os
import platform
import time
import tracemalloc
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from pathlib import Path
from typing import Any, cast

import numpy as np
from numpy.random import PCG64, Generator

from poker_ai.toy.analysis import evaluate
from poker_ai.toy.games import GameName, ToyState
from poker_ai.toy.tree import Tree
from poker_ai.training.checkpoint import save_checkpoint
from poker_ai.training.holdem import LimitRules, sample_limit
from poker_ai.training.mccfr import MCCFR, Method, RootFactory
from poker_ai.validation.five_card import source_provenance


def toy_root(game: GameName, rng: Generator) -> ToyState:
    return ToyState(game)


def worker(task: dict[str, Any]) -> dict[str, Any]:
    config = task["config"]
    game, seed = task["game"], task["seed"]
    method = cast(Method, task["method"])
    root: RootFactory
    if game == "limit":
        limit = config["limit"]
        rules = LimitRules(
            stacks=tuple(limit["stacks"]),
            button=limit["button"],
            bet_cap=limit["bet_cap"],
        )
        root = partial(sample_limit, rules)
    else:
        root = partial(toy_root, game)
    solver = MCCFR(
        root, Generator(PCG64(seed)), method=method, epsilon=config["epsilon"]
    )
    tracemalloc.start()
    started = time.perf_counter()
    solver.train(config["iterations"][game])
    seconds = time.perf_counter() - started
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    path = Path(task["checkpoint_dir"]) / f"{game}-{method}-{seed}.json"
    run_config = {"pilot": config, "game": game, "seed": seed, "method": method}
    save_checkpoint(solver, path, config=run_config, provenance=task["source"])
    row: dict[str, Any] = {
        "game": game,
        "method": method,
        "seed": seed,
        "iterations": solver.iteration,
        "nodes_visited": solver.nodes_visited,
        "information_sets": len(solver.rows),
        "training_seconds": seconds,
        "traced_current_bytes": current,
        "traced_peak_bytes": peak,
        "checkpoint": str(path),
        "checkpoint_bytes": path.stat().st_size,
        "checkpoint_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "exploitability": None,
        "value_player_zero": None,
        "unseen_information_sets": None,
    }
    if game != "limit":
        tree = Tree.build(game)
        policy = np.zeros_like(tree.legal)
        unseen = sum(key not in solver.rows for key in tree.keys)
        for info, (key, actions) in enumerate(
            zip(tree.keys, tree.actions, strict=True)
        ):
            policy[info, : len(actions)] = solver.policy(key, actions, average=True)
        metrics = evaluate(tree, policy)
        row.update(
            exploitability=metrics.exploitability,
            value_player_zero=metrics.value_player_zero,
            unseen_information_sets=unseen,
        )
    return row


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    if (
        set(config)
        != {
            "seeds",
            "methods",
            "iterations",
            "epsilon",
            "workers",
            "limit",
            "kuhn_max_exploitability",
            "leduc_max_exploitability",
            "purpose",
        }
        or config["methods"] != ["external", "outcome"]
        or set(config["iterations"]) != {"kuhn", "leduc", "limit"}
    ):
        raise ValueError("invalid MCCFR pilot config")
    if (
        not config["seeds"]
        or len(set(config["seeds"])) != len(config["seeds"])
        or any(type(seed) is not int or seed < 0 for seed in config["seeds"])
        or type(config["workers"]) is not int
        or not 1 <= config["workers"] <= 4
        or any(type(t) is not int or t < 1 for t in config["iterations"].values())
        or not 0 < config["epsilon"] <= 1
    ):
        raise ValueError("invalid pilot seed/budget/exploration")
    root = Path(__file__).resolve().parents[1]
    source = source_provenance(
        root, args.config, entrypoints=("scripts/train_mccfr_pilot.py",)
    )
    checkpoint_dir = (args.output.parent / "runs" / "mccfr-pilot-checkpoints").resolve()
    tasks = [
        {
            "config": config,
            "game": game,
            "method": method,
            "seed": seed,
            "checkpoint_dir": str(checkpoint_dir),
            "source": source,
        }
        for game in config["iterations"]
        for method in config["methods"]
        for seed in config["seeds"]
    ]
    os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    started = time.perf_counter()
    rows = []
    # Independent seed runs, not shared asynchronous regret updates. Ordered map
    # makes the aggregate order independent of process scheduling.
    with ProcessPoolExecutor(
        max_workers=config["workers"], mp_context=multiprocessing.get_context("spawn")
    ) as pool:
        for row in pool.map(worker, tasks):
            rows.append(row)
            print(
                f"{row['game']}/{row['method']} seed={row['seed']}: "
                f"{row['iterations']} iterations, {row['training_seconds']:.2f}s, "
                f"exploitability={row['exploitability']}",
                flush=True,
            )
    failures = [
        f"{r['game']}/{r['method']}/{r['seed']}: pilot convergence"
        for r in rows
        if r["game"] != "limit"
        and r["exploitability"] > config[f"{r['game']}_max_exploitability"]
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    csv_path = args.output.with_suffix(".csv")
    with csv_path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    report = {
        "schema_version": 1,
        "status": "failed" if failures else "passed",
        "config": config,
        "rows": rows,
        "source": source,
        "failures": failures,
        "total_seconds": time.perf_counter() - started,
        "memory_convention": (
            "tracemalloc current/peak during training only, not whole-process RSS"
        ),
        "parallelism": (
            "spawn; independent seeds; no shared regrets; thread env recorded"
        ),
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "numpy": np.__version__,
            "cpu_count": os.cpu_count(),
            "OPENBLAS_NUM_THREADS": os.environ["OPENBLAS_NUM_THREADS"],
            "OMP_NUM_THREADS": os.environ["OMP_NUM_THREADS"],
        },
        "limitations": [
            "limit pilot uses exact cards and sparse table coverage",
            "no full Holdem exploitability or win-rate measurement",
            "timing includes tracing overhead and concurrent workers",
            "checkpoints retained under ignored results/runs; command reproduces them",
        ],
    }
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(report["status"], args.output)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
