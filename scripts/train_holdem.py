"""Reproduce bounded own Hold'em training, checkpoint/resume and compute reports."""

import argparse
import csv
import hashlib
import json
import multiprocessing
import os
import platform
import resource
import subprocess
import time
import tracemalloc
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from pathlib import Path
from typing import Any, cast

import numpy as np
from numpy.random import PCG64, Generator

from poker_ai.abstraction.actions import ActionAbstraction
from poker_ai.abstraction.model import CardAbstraction
from poker_ai.postflop.sampling import (
    PostflopMCCFR,
    load_learning_checkpoint,
    save_learning_checkpoint,
)
from poker_ai.training.budget import NodeBudgetExceeded, bounded_sample
from poker_ai.training.checkpoint import load_checkpoint, save_checkpoint
from poker_ai.training.holdem import LimitRules, sample_limit
from poker_ai.training.mccfr import MCCFR, Method, RootFactory
from poker_ai.training.no_limit import NoLimitRules, sample_no_limit
from poker_ai.validation.five_card import source_provenance


def implementation_hash(root: Path) -> str:
    files = sorted((root / "src/poker_ai/training").glob("*.py"))
    files += sorted((root / "src/poker_ai/abstraction").glob("*.py"))
    files += [
        root / f"src/poker_ai/{name}.py"
        for name in ("cards", "engine", "equity", "evaluator")
    ]
    files.append(root / "src/poker_ai/postflop/sampling.py")
    digest = hashlib.sha256()
    for path in files:
        digest.update(str(path.relative_to(root)).encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def worker(task: dict[str, Any]) -> dict[str, Any]:
    config = task["config"]
    model_path = Path(task["root"]) / task["model"]
    model = CardAbstraction.load(model_path, cache_size=config["cache_size"])
    raw_rules = config["rules"]
    factory: RootFactory
    if config["game"] == "limit":
        rules = LimitRules(
            stacks=tuple(raw_rules["stacks"]),
            button=raw_rules["button"],
            bet_cap=raw_rules["bet_cap"],
        )
        factory = partial(sample_limit, rules, information_builder=model.information)
    else:
        abstraction = ActionAbstraction(
            fractions=tuple(tuple(pair) for pair in raw_rules["fractions"]),
            include_minimum=raw_rules["include_minimum"],
            include_all_in=raw_rules["include_all_in"],
        )
        nl_rules = NoLimitRules(
            stacks=tuple(raw_rules["stacks"]),
            button=raw_rules["button"],
            action_abstraction=abstraction,
        )
        factory = partial(
            sample_no_limit, nl_rules, information_builder=model.information
        )
    if config.get("max_nodes_per_pass") is not None:
        factory = partial(bounded_sample, factory, config["max_nodes_per_pass"])
    run_config = {
        "training": config,
        "model": task["model"],
        "model_sha256": hashlib.sha256(model_path.read_bytes()).hexdigest(),
        "implementation_sha256": task["implementation_sha256"],
        "method": task["method"],
        "seed": task["seed"],
    }
    model_hash = run_config["model_sha256"]
    run_name = f"{model_path.stem}-{model_hash[:10]}-{task['method']}-{task['seed']}"
    starting_iteration = 0
    resumed_from = None
    if task["resume_dir"] is not None:
        candidates = sorted(
            (
                p
                for p in Path(task["resume_dir"]).glob(f"{run_name}-t*.json")
                if not p.name.endswith(".visits.json")
            ),
            key=lambda p: int(p.stem.rsplit("-t", 1)[1]),
        )
        if not candidates:
            raise ValueError(f"no own resume checkpoint for {run_name}")
        resumed_from = str(candidates[-1])
        solver = (
            load_learning_checkpoint(
                candidates[-1],
                factory,
                expected_config={**run_config, "learning": config},
            )
            if config.get("sampling_weighting", "uniform") == "linear"
            else load_checkpoint(candidates[-1], factory, expected_config=run_config)
        )
        starting_iteration = solver.iteration
    else:
        if config.get("sampling_weighting", "uniform") == "linear":
            solver = PostflopMCCFR(factory, Generator(PCG64(task["seed"])), "linear")
            solver.epsilon = config["epsilon"]
        else:
            solver = MCCFR(
                factory,
                Generator(PCG64(task["seed"])),
                method=cast(Method, task["method"]),
                epsilon=config["epsilon"],
            )
    if config["trace_memory"]:
        tracemalloc.start()
    started = time.perf_counter()
    rows: list[dict[str, Any]] = []
    training_seconds = 0.0
    training_peak = 0
    targets = [t for t in config["checkpoints"] if t > starting_iteration]
    if not targets:
        raise ValueError(
            "resume checkpoint already reached the configured final budget"
        )
    for iteration in targets:
        if config["trace_memory"]:
            tracemalloc.reset_peak()
        tick = time.perf_counter()
        try:
            while solver.iteration < iteration:
                if (
                    config.get("max_training_seconds") is not None
                    and time.perf_counter() - started >= config["max_training_seconds"]
                ):
                    raise TimeoutError("run exceeded declared session time budget")
                solver.train(1)
        except (NodeBudgetExceeded, TimeoutError) as error:
            if config["trace_memory"]:
                tracemalloc.stop()
            # A target-1 abort may follow target-0 updates. Never export or reuse
            # that partially completed iteration; retain only prior checkpoints.
            return {
                "rows": rows,
                "error": {
                    "model": task["model"],
                    "method": task["method"],
                    "seed": task["seed"],
                    "reason": str(error),
                    "exception": type(error).__name__,
                    "last_saved_iteration": rows[-1]["iteration"]
                    if rows
                    else starting_iteration,
                    "last_checkpoint": rows[-1]["checkpoint"] if rows else resumed_from,
                },
            }
        training_seconds += time.perf_counter() - tick
        seconds = time.perf_counter() - started
        current, peak = (
            tracemalloc.get_traced_memory() if config["trace_memory"] else (None, None)
        )
        if peak is not None:
            training_peak = max(training_peak, peak)
        path = Path(task["checkpoint_dir"]) / f"{run_name}-t{iteration}.json"
        if isinstance(solver, PostflopMCCFR):
            save_learning_checkpoint(
                solver,
                path,
                config={**run_config, "learning": config},
                provenance=task["source"],
            )
        else:
            save_checkpoint(solver, path, config=run_config, provenance=task["source"])
        rss_native = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        rss_bytes = int(
            rss_native if platform.system() == "Darwin" else rss_native * 1024
        )
        nonuniform = 0
        entropy_sum = 0.0
        for row in solver.rows.values():
            total = float(row.strategy_sum.sum())
            if total <= 0:
                continue
            probabilities = row.strategy_sum / total
            nonuniform += int(
                np.abs(probabilities - 1 / len(probabilities)).sum() > 1e-8
            )
            positive = probabilities[probabilities > 0]
            entropy_sum += float(-(positive * np.log(positive)).sum())
        cache = model.cached_bucket.cache_info()
        rows.append(
            {
                "model": task["model"],
                "method": task["method"],
                "sampling_weighting": config.get("sampling_weighting", "uniform"),
                "seed": task["seed"],
                "iteration": iteration,
                "starting_iteration": starting_iteration,
                "session_training_seconds": training_seconds,
                "session_elapsed_seconds": seconds,
                "nodes_visited": solver.nodes_visited,
                "information_sets": len(solver.rows),
                "nonuniform_average_rows": nonuniform,
                "average_entropy_sum_nats": entropy_sum,
                "traced_current_bytes": current,
                "traced_peak_bytes": training_peak if config["trace_memory"] else None,
                "process_lifetime_peak_rss_bytes": rss_bytes,
                "feature_cache_hits": cache.hits,
                "feature_cache_misses": cache.misses,
                "feature_cache_entries": cache.currsize,
                "checkpoint": str(path),
                "checkpoint_bytes": path.stat().st_size,
                "checkpoint_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "resumed_from": resumed_from,
            }
        )
    if config["trace_memory"]:
        tracemalloc.stop()
    return {"rows": rows, "error": None}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--resume-dir", type=Path)
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    required = {
        "game",
        "seeds",
        "methods",
        "models",
        "checkpoints",
        "epsilon",
        "workers",
        "cache_size",
        "rules",
        "trace_memory",
        "purpose",
    }
    if (
        not required <= set(config)
        or set(config)
        - required
        - {"max_nodes_per_pass", "max_training_seconds", "sampling_weighting"}
        or config["game"] not in ("limit", "no_limit")
        or not config["methods"]
        or len(set(config["methods"])) != len(config["methods"])
        or any(m not in ("external", "outcome") for m in config["methods"])
    ):
        raise ValueError("invalid Holdem training config")
    weighting = config.get("sampling_weighting", "uniform")
    if weighting not in ("uniform", "linear") or (
        weighting == "linear" and config["methods"] != ["external"]
    ):
        raise ValueError("linear weighting requires external sampling only")
    rule_fields = (
        {"stacks", "button", "bet_cap"}
        if config["game"] == "limit"
        else {"stacks", "button", "fractions", "include_minimum", "include_all_in"}
    )
    if set(config["rules"]) != rule_fields:
        raise ValueError("invalid betting rules config")
    if config["game"] == "no_limit" and not {
        "max_nodes_per_pass",
        "max_training_seconds",
    } <= set(config):
        raise ValueError("no-limit experiments require node and time budgets")
    node_limit = config.get("max_nodes_per_pass")
    time_limit = config.get("max_training_seconds")
    if config["game"] == "no_limit" and (node_limit is None or time_limit is None):
        raise ValueError("no-limit node/time budgets cannot be null")
    if node_limit is not None and (type(node_limit) is not int or node_limit < 1):
        raise ValueError("invalid node limit")
    if time_limit is not None and (
        type(time_limit) not in (int, float)
        or not np.isfinite(time_limit)
        or time_limit <= 0
    ):
        raise ValueError("invalid time limit")
    for key in ("seeds", "checkpoints"):
        values = config[key]
        if (
            not values
            or any(
                type(v) is not int or v < (0 if key == "seeds" else 1) for v in values
            )
            or len(set(values)) != len(values)
            or (key == "checkpoints" and values != sorted(values))
        ):
            raise ValueError("invalid training seed/checkpoint list")
    if (
        type(config["workers"]) is not int
        or not 1 <= config["workers"] <= 4
        or type(config["cache_size"]) is not int
        or config["cache_size"] < 1
        or not 0 < config["epsilon"] <= 1
        or type(config["trace_memory"]) is not bool
        or not config["models"]
        or len(set(config["models"])) != len(config["models"])
    ):
        raise ValueError("invalid training compute/feature settings")
    root = Path(__file__).resolve().parents[1]
    for model_path in config["models"]:
        CardAbstraction.load(root / model_path, cache_size=1)
    source = source_provenance(
        root, args.config, entrypoints=("scripts/train_holdem.py",)
    )
    code_hash = implementation_hash(root)
    tasks = [
        {
            "config": config,
            "root": str(root),
            "model": model,
            "method": method,
            "seed": seed,
            "source": source,
            "implementation_sha256": code_hash,
            "checkpoint_dir": str(
                (
                    args.output.parent / "runs" / args.output.stem / "checkpoints"
                ).resolve()
            ),
            "resume_dir": None
            if args.resume_dir is None
            else str(args.resume_dir.resolve()),
        }
        for model in config["models"]
        for method in config["methods"]
        for seed in config["seeds"]
    ]
    os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    started = time.perf_counter()
    rows: list[dict[str, Any]] = []
    failures = []
    with ProcessPoolExecutor(
        max_workers=config["workers"],
        mp_context=multiprocessing.get_context("spawn"),
        max_tasks_per_child=1,
    ) as pool:
        for result in pool.map(worker, tasks):
            batch = result["rows"]
            rows.extend(batch)
            if result["error"] is not None:
                failures.append(result["error"])
                print(f"aborted: {result['error']}", flush=True)
                continue
            last = batch[-1]
            print(
                f"{Path(last['model']).stem}/{last['method']} seed={last['seed']}: "
                f"t={last['iteration']}, {last['information_sets']} information sets, "
                f"{last['session_training_seconds']:.2f}s",
                flush=True,
            )
    cpu = platform.processor()
    if platform.system() == "Darwin":
        cpu = subprocess.run(
            ["sysctl", "-n", "machdep.cpu.brand_string"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    csv_path = args.output.with_suffix(".csv")
    with csv_path.open("w", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=list(rows[0])
            if rows
            else ["model", "method", "seed", "iteration"],
        )
        writer.writeheader()
        writer.writerows(rows)
    report = {
        "schema_version": 1,
        "status": "failed" if failures else "completed",
        "failures": failures,
        "worker_reuse": "one spawned process per run",
        "config": config,
        "source": source,
        "rows": rows,
        "seconds": time.perf_counter() - started,
        "implementation_sha256": code_hash,
        "model_sha256": {
            p: hashlib.sha256((root / p).read_bytes()).hexdigest()
            for p in config["models"]
        },
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "cpu_model": cpu,
            "logical_cpus": os.cpu_count(),
            "numpy": np.__version__,
            "OPENBLAS_NUM_THREADS": os.environ["OPENBLAS_NUM_THREADS"],
            "OMP_NUM_THREADS": os.environ["OMP_NUM_THREADS"],
        },
        "limitations": [
            "No win rate or full-game exploitability measured",
            "Independent worker tables, not shared asynchronous training",
            "Tracing/concurrent execution affects timings",
            "Tracemalloc interval peaks exclude transient checkpoint serialization",
            "Models load before tracing; RSS is process-lifetime peak",
            "Entropy and nonuniform row counts are not strength metrics",
            "Own checkpoints retained in ignored results/runs; command recreates them",
        ],
    }
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(report["status"], args.output)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
