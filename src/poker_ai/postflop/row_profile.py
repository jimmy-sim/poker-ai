"""Exact trajectory gate and paired timing for the opt-in policy-row cache."""

import argparse
import cProfile
import csv
import hashlib
import json
import math
import statistics
import time
from pathlib import Path
from typing import Any, cast

import numpy as np
from numpy.random import PCG64, Generator

from poker_ai.abstraction.model import CardAbstraction
from poker_ai.finite import ArrayTree
from poker_ai.postflop import controlled_profile as baseline
from poker_ai.postflop.controlled_training import ControlledTrainer, Mass, Phase, Rules
from poker_ai.postflop.game import load_spot
from poker_ai.postflop.range_protocol import build_representation_control
from poker_ai.postflop.river_study import Deadline, digest
from poker_ai.postflop.row_policy import RowPolicyTrainer
from poker_ai.postflop.tree import SpotTree
from poker_ai.reproducibility import runtime_environment
from poker_ai.validation.five_card import source_provenance

CONFIG = "configs/row-policy-profile.json"
ENTRY = "scripts/profile_policy_rows.py"
FORMAT = "poker-ai-policy-row-profile-v1"
PARITY = [1, 2, 16, 64, 128, 1001]


def inputs(root: Path, config: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    if (
        type(config["schema_version"]) is not int
        or config["schema_version"] != 1
        or config["status"] != "opt_in_execution_optimization_only"
        or config["base_profile_config"] != baseline.CONFIG
        or config["base_profile"] != "results/controlled-training-profile/profile.json"
        or set(config["input_sha256"])
        != {
            baseline.CONFIG,
            config["base_profile"],
            "results/controlled-training-profile/report/summary.json",
        }
        or config["parity_iterations"] != PARITY
        or any(type(t) is not int for t in config["parity_iterations"])
        or any(
            type(config[k]) is not int or config[k] != v
            for k, v in {
                "repetitions": 3,
                "external_iterations_after_initialization": 1000,
                "full_iterations_after_initialization": 16,
                "maximum_seconds": 1200,
                "forecast_target_node_work": 10000000,
            }.items()
        )
        or type(config["forecast_guard_multiplier"]) is not float
        or config["forecast_guard_multiplier"] != 2.0
    ):
        raise ValueError("invalid policy-row profile config")
    if any(digest(root / p) != sha for p, sha in config["input_sha256"].items()):
        raise ArithmeticError("policy-row prerequisite changed")
    old = json.loads((root / baseline.CONFIG).read_text())
    protocol = baseline.load_inputs(root, old)
    baseline.report(root, root / config["base_profile"])
    baseline.replay_correctness(root, root / old["baseline_receipt"])
    return old, protocol


def trainer(tree: ArrayTree, cell: dict[str, Any], engine: str) -> ControlledTrainer:
    if engine not in ("dense", "rows") or (
        engine == "rows" and cell["traversal"] != "external"
    ):
        raise ValueError("invalid paired backend")
    phase: Phase = "opponent_pass" if cell["bridge"] == "common" else "target_pass"
    mass: Mass = (
        "own_reach" if cell["bridge"].endswith("history_mass") else "chance_own_reach"
    )
    cls = ControlledTrainer if engine == "dense" else RowPolicyTrainer
    return cls(
        tree,
        Generator(PCG64(cell["seed"] or 20261301)),
        traversal=cell["traversal"],
        rules=Rules(cell["regret_rule"], cell["regret_weight"], cell["average_weight"]),
        average_phase=phase,
        average_mass=mass,
    )


def fingerprint(solver: ControlledTrainer) -> str:
    sha = hashlib.sha256()
    for array in (
        solver.regrets,
        solver.strategy_sum,
        solver.current_policy,
        solver.average_policy,
    ):
        sha.update(np.asarray(array, dtype="<f8").tobytes())
    sha.update(json.dumps(solver.rng.bit_generator.state, sort_keys=True).encode())
    sha.update(json.dumps(sorted(solver.sampled_keys)).encode())
    return sha.hexdigest()


def assert_equal(a: ControlledTrainer, b: ControlledTrainer) -> str:
    for name in ("iteration", "nodes_visited", "initialization_visits", "sampled_keys"):
        if getattr(a, name) != getattr(b, name):
            raise ArithmeticError(f"row-cache parity mismatch: {name}")
    for name in ("regrets", "strategy_sum", "current_policy", "average_policy"):
        if getattr(a, name).tobytes() != getattr(b, name).tobytes():
            raise ArithmeticError(f"row-cache parity mismatch: {name}")
    if a.rng.bit_generator.state != b.rng.bit_generator.state:
        raise ArithmeticError("row-cache parity mismatch: RNG")
    ah, bh = fingerprint(a), fingerprint(b)
    if ah != bh:
        raise ArithmeticError("row-cache fingerprint mismatch")
    return ah


def parity(
    tree: ArrayTree, cell: dict[str, Any], checkpoints: list[int], deadline: Deadline
) -> list[dict[str, Any]]:
    a, b = trainer(tree, cell, "dense"), trainer(tree, cell, "rows")
    a.initialize_exact()
    b.initialize_exact()
    rows = []
    for checkpoint in checkpoints:
        while a.iteration < checkpoint:
            deadline.check()
            a.step()
            b.step()
        try:
            matched_hash = assert_equal(a, b)
        except ArithmeticError as error:
            raise ArithmeticError(
                f"{baseline.identity(cell)} at checkpoint {checkpoint}: {error}"
            ) from error
        rows.append(
            {
                **cell,
                "iteration": checkpoint,
                "state_sha256": matched_hash,
                "total_visits": a.nodes_visited,
            }
        )
    return rows


def measure(
    tree: ArrayTree,
    cell: dict[str, Any],
    engine: str,
    steps: int,
    deadline: Deadline,
    instrument: cProfile.Profile | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    started = time.perf_counter()
    solver = trainer(tree, cell, engine)
    if cell["bridge"] != "cold_target_history_mass":
        solver.initialize_exact()
    initialization_seconds = time.perf_counter() - started
    initial = solver.nodes_visited
    started = time.perf_counter()
    if instrument is not None:
        instrument.enable()
    try:
        for _ in range(steps):
            deadline.check()
            solver.step()
    finally:
        if instrument is not None:
            instrument.disable()
    seconds = time.perf_counter() - started
    deadline.check()
    row = {
        **cell,
        "iterations": solver.iteration,
        "initialization_visits": initial,
        "incremental_visits": solver.nodes_visited - initial,
        "total_visits": solver.nodes_visited,
        "initialization_seconds": initialization_seconds,
        "incremental_seconds": seconds,
        "state_sha256": fingerprint(solver),
        "tree_nodes": len(tree.player),
        "information_sets": len(tree.keys),
        "width": tree.legal.shape[1],
    }
    cache = (
        {
            "row_evaluations": solver.row_evaluations,
            "last_pass_rows": list(solver.last_pass_rows),
        }
        if isinstance(solver, RowPolicyTrainer)
        else {}
    )
    return row, cache


def run(root: Path, config_path: Path, output: Path) -> dict[str, Any]:
    if output.exists():
        raise FileExistsError("retain paired profile evidence")
    started = time.perf_counter()
    config: dict[str, Any] = json.loads(config_path.read_text())
    old, protocol = inputs(root, config)
    source = source_provenance(root, config_path, entrypoints=(ENTRY,))
    if source["dirty"] is not False:
        raise ValueError("publish checked row-cache code first")
    deadline = Deadline(config["maximum_seconds"])
    deadline.started = started
    result: dict[str, Any] = dict(
        format=FORMAT,
        status="running",
        failure=None,
        config=config,
        source=source,
        environment=runtime_environment(),
        parity=[],
        timings={"dense": [], "rows": []},
        profiles=[],
        cache_diagnostics=[],
        pair_orders=[],
        seconds=0.0,
        strength_comparison_performed=False,
    )
    output.parent.mkdir(parents=True, exist_ok=True)

    def persist() -> None:
        result["seconds"] = time.perf_counter() - started
        tmp = output.with_suffix(".tmp")
        tmp.write_text(
            json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n"
        )
        tmp.replace(output)

    try:
        original = json.loads((root / "configs/range-mass-protocol.json").read_text())
        model = CardAbstraction.load(root / original["model"])
        trees = {}
        workload = baseline.cells(protocol["future_comparison"])
        external = [c for c in workload if c["traversal"] == "external"]
        for game in protocol["future_comparison"]["spot_files"]:
            source_tree = SpotTree.build(load_spot(root / game))
            for name in protocol["future_comparison"]["representations"]:
                trees[game, name] = build_representation_control(
                    source_tree, name, model
                )
        for i, cell in enumerate(external):
            result["parity"].extend(
                parity(
                    trees[cell["spot_file"], cell["representation"]],
                    cell,
                    PARITY,
                    deadline,
                )
            )
            print(f"parity {i + 1}/96", flush=True)
            persist()
        for cell in workload:
            tree = trees[cell["spot_file"], cell["representation"]]
            steps = config[f"{cell['traversal']}_iterations_after_initialization"]
            for repeat in range(config["repetitions"]):
                if cell["traversal"] == "external":
                    index = external.index(cell)
                    order = (
                        ["dense", "rows"]
                        if (index + repeat) % 2 == 0
                        else ["rows", "dense"]
                    )
                    result["pair_orders"].append(
                        {**cell, "repeat": repeat, "order": order}
                    )
                else:
                    order = ["dense"]
                for engine in order:
                    row, cache = measure(tree, cell, engine, steps, deadline)
                    result["timings"][engine].append({**row, "repeat": repeat})
                    if cache:
                        result["cache_diagnostics"].append(
                            {**cell, "repeat": repeat, **cache}
                        )
            count = len(result["timings"]["dense"]) + len(result["timings"]["rows"])
            print(f"timed {count}/708", flush=True)
            persist()
        for cell in old["profiler_cases"]:
            tree = trees[cell["spot_file"], cell["representation"]]
            for engine in (
                ["dense", "rows"] if cell["traversal"] == "external" else ["dense"]
            ):
                profiler = cProfile.Profile()
                row, _ = measure(
                    tree,
                    cell,
                    engine,
                    config[f"{cell['traversal']}_iterations_after_initialization"],
                    deadline,
                    profiler,
                )
                result["profiles"].append(
                    {
                        **row,
                        "engine": engine,
                        "hotspots": baseline.hotspots(profiler, root, 25),
                    }
                )
        validate(result, protocol)
        inputs(root, config)
        if any(
            digest(root / p) != sha
            for p, sha in cast(dict[str, str], source["sha256"]).items()
        ):
            raise ArithmeticError("paired profile source changed")
        deadline.check()
        result["status"] = "completed"
    except (Exception, KeyboardInterrupt) as error:
        result["status"] = "incomplete"
        result["failure"] = dict(type=type(error).__name__, reason=str(error))
    finally:
        persist()
    return result


def validate(saved: dict[str, Any], protocol: dict[str, Any]) -> None:
    config = saved["config"]
    all_cells = baseline.cells(protocol["future_comparison"])
    external = [c for c in all_cells if c["traversal"] == "external"]
    for engine, expected in (("dense", all_cells), ("rows", external)):
        baseline.validate_rows(saved["timings"][engine], expected, config)
    parity_rows = saved["parity"]
    expected_parity = {(baseline.identity(c), t) for c in external for t in PARITY}
    ids = [(baseline.identity(r), r["iteration"]) for r in parity_rows]
    if (
        len(ids) != len(set(ids))
        or set(ids) != expected_parity
        or any(
            type(r["iteration"]) is not int
            or type(r["total_visits"]) is not int
            or r["total_visits"] <= 0
            or len(r["state_sha256"]) != 64
            for r in parity_rows
        )
    ):
        raise ArithmeticError("partial/changed parity grid")
    dense = {(baseline.identity(r), r["repeat"]): r for r in saved["timings"]["dense"]}
    cached = {(baseline.identity(r), r["repeat"]): r for r in saved["timings"]["rows"]}
    for key, row in cached.items():
        if any(row[k] != dense[key][k] for k in baseline.STABLE):
            raise ArithmeticError("paired state/work mismatch")
        final = next(
            p
            for p in parity_rows
            if baseline.identity(p) == key[0] and p["iteration"] == 1001
        )
        if (row["state_sha256"], row["total_visits"]) != (
            final["state_sha256"],
            final["total_visits"],
        ):
            raise ArithmeticError("timing differs from parity trajectory")
    orders = saved["pair_orders"]
    keys = [(baseline.identity(o), o["repeat"]) for o in orders]
    if len(keys) != len(set(keys)) or set(keys) != set(cached):
        raise ArithmeticError("paired order grid changed")
    for o in orders:
        i = next(
            i
            for i, c in enumerate(external)
            if baseline.identity(c) == baseline.identity(o)
        )
        expected_order = (
            ["dense", "rows"] if (i + o["repeat"]) % 2 == 0 else ["rows", "dense"]
        )
        if type(o["repeat"]) is not int or o["order"] != expected_order:
            raise ArithmeticError("backend order changed")
    diagnostics = saved["cache_diagnostics"]
    dkeys = [(baseline.identity(d), d["repeat"]) for d in diagnostics]
    if len(dkeys) != len(set(dkeys)) or set(dkeys) != set(cached):
        raise ArithmeticError("cache diagnostics grid changed")
    for d in diagnostics:
        row = cached[baseline.identity(d), d["repeat"]]
        if (
            type(d["repeat"]) is not int
            or type(d["row_evaluations"]) is not int
            or d["row_evaluations"] <= 0
            or d["row_evaluations"] > 2000 * row["information_sets"]
            or len(d["last_pass_rows"]) != 2
            or any(
                type(n) is not int or not 0 <= n <= row["information_sets"]
                for n in d["last_pass_rows"]
            )
        ):
            raise ArithmeticError("invalid cache diagnostic")
    profiles = saved["profiles"]
    original = json.loads(
        (Path(__file__).resolve().parents[3] / baseline.CONFIG).read_text()
    )
    wanted = {
        (baseline.identity(c), engine)
        for c in original["profiler_cases"]
        for engine in (["dense", "rows"] if c["traversal"] == "external" else ["dense"])
    }
    ids_p = [(baseline.identity(p), p["engine"]) for p in profiles]
    if len(ids_p) != len(set(ids_p)) or set(ids_p) != wanted:
        raise ArithmeticError("profiler grid changed")
    for p in profiles:
        peers = dense if p["engine"] == "dense" else cached
        base = peers[baseline.identity(p), 0]
        if any(p[k] != base[k] for k in baseline.STABLE) or len(p["hotspots"]) != 25:
            raise ArithmeticError("instrumentation changed state")
        for h in p["hotspots"]:
            if any(
                type(h[k]) not in (int, float) or not math.isfinite(h[k]) or h[k] < 0
                for k in (
                    "calls",
                    "primitive_calls",
                    "self_seconds",
                    "cumulative_seconds",
                )
            ):
                raise ArithmeticError("invalid paired hotspot")


def report(root: Path, path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    saved: dict[str, Any] = json.loads(path.read_text())
    json.dumps(saved, allow_nan=False)
    old, protocol = inputs(root, saved["config"])
    if (
        saved["format"] != FORMAT
        or saved["status"] != "completed"
        or saved["failure"] is not None
        or saved["strength_comparison_performed"] is not False
        or saved["source"]["dirty"] is not False
        or not {
            ENTRY,
            CONFIG,
            "src/poker_ai/postflop/row_policy.py",
            "src/poker_ai/postflop/row_profile.py",
        }.issubset(saved["source"]["sha256"])
        or any(digest(root / p) != sha for p, sha in saved["source"]["sha256"].items())
        or json.loads((root / CONFIG).read_text()) != saved["config"]
    ):
        raise ArithmeticError("partial/changed paired evidence/source")
    validate(saved, protocol)
    measured = math.fsum(
        r["initialization_seconds"] + r["incremental_seconds"]
        for r in saved["timings"]["dense"]
        + saved["timings"]["rows"]
        + saved["profiles"]
    )
    if (
        type(saved["seconds"]) not in (int, float)
        or not math.isfinite(saved["seconds"])
        or measured > saved["seconds"] + 1e-6
    ):
        raise ArithmeticError("invalid paired elapsed time")
    forecasts = {}
    dense = saved["timings"]["dense"]
    mixed = [r for r in dense if r["traversal"] == "full"] + saved["timings"]["rows"]
    for engine, rows in (("dense", dense), ("rows", mixed)):
        forecasts[engine] = baseline.forecast(
            rows,
            old["forecast_target_node_work"],
            old["forecast_guard_multiplier"],
            protocol["future_comparison"]["maximum_own_seconds"],
        )
    by_dense = {(baseline.identity(r), r["repeat"]): r for r in dense}
    ratios = [
        {
            **{k: r[k] for k in baseline.KEY},
            "repeat": r["repeat"],
            "dense_over_rows": by_dense[baseline.identity(r), r["repeat"]][
                "incremental_seconds"
            ]
            / r["incremental_seconds"],
        }
        for r in saved["timings"]["rows"]
    ]
    summary = dict(
        input_sha256=digest(path),
        forecasts=forecasts,
        paired_ratios=ratios,
        median_paired_ratio=statistics.median(r["dense_over_rows"] for r in ratios),
        parity_cells=len(saved["parity"]) // len(PARITY),
        parity_checkpoints=len(saved["parity"]),
        timing_rows=len(dense) + len(saved["timings"]["rows"]),
        seconds=saved["seconds"],
        strength_comparison_performed=False,
    )
    return saved, summary


def tables(summary: dict[str, Any]) -> str:
    lines = [
        "# Policy-row paired profile",
        "",
        "Exact valid-state parity; timing estimates only.",
        "",
        f"Parity: {summary['parity_cells']} cells / "
        f"{summary['parity_checkpoints']} checkpoints; "
        f"{summary['timing_rows']} timing rows.",
        "Median paired dense / row-cache loop time: "
        f"{summary['median_paired_ratio']:.3f}×.",
        "",
        "| Backend | Training forecast (s) | 2× guard (s) | Decision |",
        "|---|---:|---:|---|",
    ]
    for engine, f in summary["forecasts"].items():
        lines.append(
            f"| {engine} | {f['training_only_forecast_seconds']:.3f} | "
            f"{f['guarded_training_seconds']:.3f} | {f['decision']} |"
        )
    lines += [
        "",
        "Full cells are shared. Setup/scoring/checkpoint/audit remain unestimated.",
        "No learning sweep, default change or playing-strength claim.",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path(CONFIG))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/runs/row-policy-profile/profile.json"),
    )
    parser.add_argument("--report", type=Path)
    parser.add_argument("--tables", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    if args.report:
        saved, summary = report(root, root / args.report)
        print(tables(summary))
        if args.tables:
            directory = root / args.tables
            directory.mkdir(parents=True, exist_ok=False)
            (directory / "summary.json").write_text(
                json.dumps(summary, sort_keys=True, indent=2) + "\n"
            )
            (directory / "tables.md").write_text(tables(summary))
            for name, rows in (
                ("dense", saved["timings"]["dense"]),
                ("rows", saved["timings"]["rows"]),
                ("ratios", summary["paired_ratios"]),
            ):
                with (directory / (name + ".csv")).open("w", newline="") as stream:
                    writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
                    writer.writeheader()
                    writer.writerows(rows)
        return 0
    result = run(root, root / args.config, root / args.output)
    print(
        f"{result['status']}: {len(result['parity'])} parity checkpoints, "
        f"{sum(len(r) for r in result['timings'].values())} timing rows"
    )
    return 0 if result["status"] == "completed" else 1
