"""Profile the fixed controlled-training workload; never measure playing strength.

This is experiment orchestration around the unchanged library trainer. Timing
receipts cannot reproduce wall time; --report validates recorded rows and source
bindings and recomputes forecasts. Re-running measurements uses a fresh output.
"""

import argparse
import cProfile
import csv
import hashlib
import itertools
import json
import math
import pstats
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, cast

import numpy as np
from numpy.random import PCG64, Generator

from poker_ai.abstraction.model import CardAbstraction
from poker_ai.finite import ArrayTree
from poker_ai.postflop import training_isolation as prior
from poker_ai.postflop.controlled_training import ControlledTrainer, Mass, Phase, Rules
from poker_ai.postflop.game import load_spot
from poker_ai.postflop.range_protocol import build_representation_control
from poker_ai.postflop.range_reply import compare
from poker_ai.postflop.river_study import Deadline, digest
from poker_ai.postflop.training_isolation import check_inputs
from poker_ai.postflop.tree import SpotTree
from poker_ai.reproducibility import runtime_environment
from poker_ai.validation.five_card import source_provenance

CONFIG = "configs/controlled-training-profile.json"
ENTRYPOINT = "scripts/profile_controlled_training.py"
FORMAT = "poker-ai-controlled-training-profile-v1"
KEY = (
    "spot_file",
    "representation",
    "traversal",
    "regret_rule",
    "regret_weight",
    "average_weight",
    "seed",
    "bridge",
)
BRIDGES = (
    "cold_target_history_mass",
    "warm_target_history_mass",
    "warm_target_chance_mass",
)
STABLE = (
    "iterations",
    "initialization_visits",
    "incremental_visits",
    "total_visits",
    "state_sha256",
    "tree_nodes",
    "information_sets",
    "width",
)


def identity(cell: dict[str, Any]) -> str:
    return json.dumps({k: cell[k] for k in KEY}, sort_keys=True)


def replay_correctness(root: Path, path: Path) -> dict[str, Any]:
    """Versioned bridge for PR22's closed source-inventory check.

    Pin the ENTIRE reviewed old receipt. Check every old source hash except its
    entrypoint, whose old/new hashes are explicitly pinned. No old mathematical
    implementation or recorded value is changed. New receipts use old replay.
    """
    config: dict[str, Any] = json.loads((root / CONFIG).read_text())
    if digest(path) != config["input_sha256"][config["baseline_receipt"]]:
        return prior.replay(root, path)
    saved: dict[str, Any] = json.loads(path.read_text())
    bridge = config["correctness_cli_bridge"]
    source = saved["source"]
    if (
        source["dirty"] is not False
        or source["sha256"].get(prior.ENTRYPOINT) != bridge["old_sha256"]
        or digest(root / prior.ENTRYPOINT) != bridge["new_sha256"]
        or any(
            digest(root / p) != sha
            for p, sha in source["sha256"].items()
            if p != prior.ENTRYPOINT
        )
    ):
        raise ArithmeticError("correctness compatibility source changed")
    actual = prior.evidence(root, saved["config"])
    error = compare(actual, {k: saved[k] for k in actual})
    if error > saved["config"]["sentinel"]["tolerance"]:
        raise ArithmeticError("prior correctness values changed")
    return saved


def cells(comparison: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for game, representation, traversal, clip, rw, aw in itertools.product(
        comparison["spot_files"],
        comparison["representations"],
        comparison["traversal"],
        comparison["regret_rule"],
        comparison["regret_weight"],
        comparison["average_weight"],
    ):
        for seed in comparison["seeds"] if traversal == "external" else [None]:
            rows.append(
                dict(
                    zip(
                        KEY,
                        (game, representation, traversal, clip, rw, aw, seed, "common"),
                        strict=True,
                    )
                )
            )
    for game, representation, bridge in itertools.product(
        comparison["spot_files"], comparison["representations"], BRIDGES
    ):
        rows.append(
            dict(
                zip(
                    KEY,
                    (
                        game,
                        representation,
                        "full",
                        "clipped",
                        "uniform",
                        "linear",
                        None,
                        bridge,
                    ),
                    strict=True,
                )
            )
        )
    return rows


def load_inputs(root: Path, config: dict[str, Any]) -> dict[str, Any]:
    if (
        type(config["schema_version"]) is not int
        or config["schema_version"] != 1
        or config["status"] != "profile_only_no_strength_comparison"
        or config["comparison_config"] != "configs/training-isolation.json"
        or config["baseline_receipt"] != "results/training-isolation/correctness.json"
        or set(config["input_sha256"])
        != {config["comparison_config"], config["baseline_receipt"]}
        or any(
            type(config[k]) is not int or config[k] != v
            for k, v in {
                "repetitions": 3,
                "external_iterations_after_initialization": 1000,
                "full_iterations_after_initialization": 16,
                "maximum_profile_seconds": 900,
                "forecast_target_node_work": 10000000,
                "hotspot_rows": 25,
            }.items()
        )
        or type(config["forecast_guard_multiplier"]) is not float
        or config["forecast_guard_multiplier"] != 2.0
    ):
        raise ValueError("invalid fixed profile config")
    if any(digest(root / p) != sha for p, sha in config["input_sha256"].items()):
        raise ArithmeticError("profile prerequisite changed")
    protocol: dict[str, Any] = json.loads(
        (root / config["comparison_config"]).read_text()
    )
    check_inputs(root, protocol)
    expected = [
        {**c}
        for c in cells(protocol["future_comparison"])
        if c["representation"] == "texture_range_q8_b8"
        and c["bridge"] == "common"
        and (
            c["traversal"],
            c["regret_rule"],
            c["regret_weight"],
            c["average_weight"],
            c["seed"],
        )
        in [
            ("full", "clipped", "uniform", "linear", None),
            ("external", "signed", "linear", "linear", 20261301),
        ]
    ]
    if {identity(c) for c in config["profiler_cases"]} != {
        identity(c) for c in expected
    } or len(config["profiler_cases"]) != 4:
        raise ValueError("profiler cases changed")
    return protocol


def measure(
    tree: ArrayTree,
    cell: dict[str, Any],
    iterations: int,
    deadline: Deadline,
    instrument: cProfile.Profile | None = None,
) -> dict[str, Any]:
    started = time.perf_counter()
    phase: Phase = "opponent_pass" if cell["bridge"] == "common" else "target_pass"
    mass: Mass = (
        "own_reach" if cell["bridge"].endswith("history_mass") else "chance_own_reach"
    )
    solver = ControlledTrainer(
        tree,
        Generator(PCG64(cell["seed"] or 20261301)),
        traversal=cell["traversal"],
        rules=Rules(cell["regret_rule"], cell["regret_weight"], cell["average_weight"]),
        average_phase=phase,
        average_mass=mass,
    )
    if cell["bridge"] != "cold_target_history_mass":
        solver.initialize_exact()
    initial_seconds = time.perf_counter() - started
    initial_work = solver.nodes_visited
    started = time.perf_counter()
    if instrument is not None:
        instrument.enable()
    try:
        for _ in range(iterations):
            deadline.check()
            solver.step()
    finally:
        if instrument is not None:
            instrument.disable()
    seconds = time.perf_counter() - started
    deadline.check()
    fingerprint = hashlib.sha256()
    for array in (
        solver.regrets,
        solver.strategy_sum,
        solver.current_policy,
        solver.average_policy,
    ):
        fingerprint.update(np.asarray(array, dtype="<f8").tobytes())
    fingerprint.update(
        json.dumps(solver.rng.bit_generator.state, sort_keys=True).encode()
    )
    fingerprint.update(json.dumps(sorted(solver.sampled_keys)).encode())
    return {
        **cell,
        "iterations": solver.iteration,
        "initialization_visits": initial_work,
        "incremental_visits": solver.nodes_visited - initial_work,
        "total_visits": solver.nodes_visited,
        "initialization_seconds": initial_seconds,
        "incremental_seconds": seconds,
        "state_sha256": fingerprint.hexdigest(),
        "tree_nodes": len(tree.player),
        "information_sets": len(tree.keys),
        "width": tree.legal.shape[1],
    }


def hotspots(profiler: cProfile.Profile, root: Path, top: int) -> list[dict[str, Any]]:
    stats = cast(Any, pstats.Stats(profiler))
    rows = []
    for (filename, line, name), (
        primitive,
        calls,
        self_time,
        cumulative,
        _,
    ) in stats.stats.items():
        path = Path(filename)
        label = str(path.relative_to(root)) if path.is_relative_to(root) else path.name
        rows.append(
            dict(
                file=label,
                line=line,
                function=name,
                primitive_calls=primitive,
                calls=calls,
                self_seconds=self_time,
                cumulative_seconds=cumulative,
            )
        )
    return sorted(
        rows,
        key=lambda r: (-r["cumulative_seconds"], r["file"], r["line"], r["function"]),
    )[:top]


def forecast(
    rows: list[dict[str, Any]], target: int, guard: float, cap: int
) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[identity(row)].append(row)
    predictions = []
    for group in grouped.values():
        estimates = [
            r["initialization_seconds"]
            + max(0, target - r["initialization_visits"])
            * r["incremental_seconds"]
            / r["incremental_visits"]
            for r in group
        ]
        predictions.append(
            {**{k: group[0][k] for k in KEY}, "training_seconds": max(estimates)}
        )
    total = math.fsum(p["training_seconds"] for p in predictions)
    return {
        "cells": predictions,
        "training_only_forecast_seconds": total,
        "guarded_training_seconds": guard * total,
        "planning_guard": guard,
        "own_stage_cap_seconds": cap,
        "decision": "training_only_guarded_forecast_exceeds_cap"
        if guard * total > cap
        else "unresolved_unmeasured_pipeline_cost",
        "scoring_checkpoint_setup_audit_cost": "not estimated here",
        "strength_comparison_performed": False,
    }


def validate_rows(
    rows: list[dict[str, Any]], expected: list[dict[str, Any]], config: dict[str, Any]
) -> None:
    wanted = {(identity(c), r) for c in expected for r in range(config["repetitions"])}
    ids = [(identity(r), r["repeat"]) for r in rows]
    if (
        len(ids) != len(set(ids))
        or set(ids) != wanted
        or any(type(r["repeat"]) is not int for r in rows)
    ):
        raise ArithmeticError("missing/duplicate/changed timing grid")
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if set(row) != set(KEY) | set(STABLE) | {
            "repeat",
            "initialization_seconds",
            "incremental_seconds",
        }:
            raise ArithmeticError("timing fields changed")
        groups[identity(row)].append(row)
        steps = config[f"{row['traversal']}_iterations_after_initialization"]
        warm = row["bridge"] != "cold_target_history_mass"
        if (
            any(
                type(row[k]) is not int or row[k] < 0
                for k in STABLE
                if k != "state_sha256"
            )
            or row["tree_nodes"] <= 0
            or row["information_sets"] <= 0
            or row["width"] <= 0
            or row["iterations"] != steps + int(warm)
            or row["initialization_visits"] != (2 * row["tree_nodes"] if warm else 0)
            or row["incremental_visits"] <= 0
            or row["total_visits"]
            != row["initialization_visits"] + row["incremental_visits"]
            or not 0 < row["incremental_visits"] <= 2 * row["tree_nodes"] * steps
            or (
                row["traversal"] == "full"
                and row["incremental_visits"] != 2 * row["tree_nodes"] * steps
            )
            or not isinstance(row["state_sha256"], str)
            or len(row["state_sha256"]) != 64
            or any(c not in "0123456789abcdef" for c in row["state_sha256"])
            or any(
                type(row[k]) not in (int, float)
                or not math.isfinite(row[k])
                or row[k] <= 0
                for k in ("initialization_seconds", "incremental_seconds")
            )
        ):
            raise ArithmeticError("invalid timing/work/state receipt")
    for group in groups.values():
        if any(
            tuple(r[k] for k in STABLE) != tuple(group[0][k] for k in STABLE)
            for r in group
        ):
            raise ArithmeticError("timing repeats changed learning trajectory")


def run(root: Path, config_path: Path, output: Path) -> dict[str, Any]:
    if output.exists():
        raise FileExistsError("retain prior profiling evidence")
    started = time.perf_counter()
    config: dict[str, Any] = json.loads(config_path.read_text())
    protocol = load_inputs(root, config)
    source = source_provenance(root, config_path, entrypoints=(ENTRYPOINT,))
    if source["dirty"] is not False:
        raise ValueError("publish checked profiling code first")
    deadline = Deadline(config["maximum_profile_seconds"])
    deadline.started = started
    replay_correctness(root, root / config["baseline_receipt"])
    original = json.loads((root / "configs/range-mass-protocol.json").read_text())
    model = CardAbstraction.load(root / original["model"])
    result: dict[str, Any] = {
        "format": FORMAT,
        "status": "running",
        "failure": None,
        "config": config,
        "source": source,
        "environment": runtime_environment(),
        "rows": [],
        "profiles": [],
        "setup_seconds": 0.0,
        "seconds": 0.0,
        "strength_comparison_performed": False,
    }
    output.parent.mkdir(parents=True, exist_ok=True)

    def persist() -> None:
        result["seconds"] = time.perf_counter() - started
        tmp = output.with_suffix(".tmp")
        tmp.write_text(
            json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n"
        )
        tmp.replace(output)

    try:
        workload = cells(protocol["future_comparison"])
        for game in protocol["future_comparison"]["spot_files"]:
            setup = time.perf_counter()
            source_tree = SpotTree.build(load_spot(root / game))
            for representation in protocol["future_comparison"]["representations"]:
                tree = build_representation_control(source_tree, representation, model)
                result["setup_seconds"] += time.perf_counter() - setup
                selected = [
                    c
                    for c in workload
                    if c["spot_file"] == game and c["representation"] == representation
                ]
                for cell in selected:
                    count = config[
                        f"{cell['traversal']}_iterations_after_initialization"
                    ]
                    for repeat in range(config["repetitions"]):
                        row = measure(tree, cell, count, deadline)
                        result["rows"].append({**row, "repeat": repeat})
                    print(
                        f"timed {len(result['rows'])}/420: {identity(cell)}", flush=True
                    )
                    persist()
                for cell in config["profiler_cases"]:
                    if (
                        cell["spot_file"] == game
                        and cell["representation"] == representation
                    ):
                        profiler = cProfile.Profile()
                        row = measure(
                            tree,
                            cell,
                            config[
                                f"{cell['traversal']}_iterations_after_initialization"
                            ],
                            deadline,
                            profiler,
                        )
                        result["profiles"].append(
                            {
                                **row,
                                "hotspots": hotspots(
                                    profiler, root, config["hotspot_rows"]
                                ),
                            }
                        )
                setup = time.perf_counter()
        validate_rows(result["rows"], workload, config)
        load_inputs(root, config)
        if any(
            digest(root / p) != s
            for p, s in cast(dict[str, str], source["sha256"]).items()
        ):
            raise ArithmeticError("profile source changed")
        deadline.check()
        result["status"] = "completed"
    except (Exception, KeyboardInterrupt) as error:
        result["status"] = "incomplete"
        result["failure"] = dict(type=type(error).__name__, reason=str(error))
    finally:
        persist()
    return result


def report(root: Path, path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    saved: dict[str, Any] = json.loads(path.read_text())
    json.dumps(saved, allow_nan=False)
    config = saved["config"]
    protocol = load_inputs(root, config)
    if (
        saved["format"] != FORMAT
        or saved["status"] != "completed"
        or saved["failure"] is not None
        or saved["strength_comparison_performed"] is not False
        or saved["source"]["dirty"] is not False
        or not {
            ENTRYPOINT,
            CONFIG,
            "uv.lock",
            "pyproject.toml",
            "src/poker_ai/postflop/controlled_profile.py",
            "src/poker_ai/postflop/controlled_training.py",
        }.issubset(saved["source"]["sha256"])
        or any(digest(root / p) != s for p, s in saved["source"]["sha256"].items())
        or json.loads((root / CONFIG).read_text()) != config
    ):
        raise ArithmeticError("partial/changed profile evidence or source")
    if any(
        type(saved[k]) not in (int, float)
        or not math.isfinite(saved[k])
        or saved[k] < 0
        for k in ("seconds", "setup_seconds")
    ):
        raise ArithmeticError("invalid total profile time")
    validate_rows(saved["rows"], cells(protocol["future_comparison"]), config)
    profiles = saved["profiles"]
    if len(profiles) != 4 or {identity(c) for c in profiles} != {
        identity(c) for c in config["profiler_cases"]
    }:
        raise ArithmeticError("missing/duplicate profiler grid")
    for row in profiles:
        peers = [r for r in saved["rows"] if identity(r) == identity(row)]
        if any(row[k] != peers[0][k] for k in STABLE):
            raise ArithmeticError("instrumentation changed trajectory")
        if len(row["hotspots"]) != config["hotspot_rows"] or any(
            not math.isfinite(h[k]) or h[k] < 0
            for h in row["hotspots"]
            for k in ("self_seconds", "cumulative_seconds", "calls", "primitive_calls")
        ):
            raise ArithmeticError("invalid hotspot receipt")
    measured = math.fsum(
        r["initialization_seconds"] + r["incremental_seconds"]
        for r in saved["rows"] + profiles
    )
    if measured + saved["setup_seconds"] > saved["seconds"] + 1e-6:
        raise ArithmeticError("measured time exceeds profile wall time")
    return saved, forecast(
        saved["rows"],
        config["forecast_target_node_work"],
        config["forecast_guard_multiplier"],
        protocol["future_comparison"]["maximum_own_seconds"],
    )


def tables(summary: dict[str, Any]) -> str:
    lines = [
        "# Controlled-training cost forecast",
        "",
        "Timing extrapolation only; no strength comparison.",
        "",
        f"Decision: `{summary['decision']}`.",
        f"Training only: {summary['training_only_forecast_seconds']:.3f}s; "
        f"with {summary['planning_guard']:.0f}× guard: "
        f"{summary['guarded_training_seconds']:.3f}s; "
        f"cap: {summary['own_stage_cap_seconds']}s.",
        "",
        "Setup, scoring, checkpoint and audit costs are unestimated; "
        "this is not a bound.",
        "",
        "| Game | Groups | Traversal | Bridge | Cells | Forecast seconds |",
        "|---|---|---|---|---:|---:|",
    ]
    groups: dict[tuple[str, ...], list[float]] = defaultdict(list)
    for row in summary["cells"]:
        groups[
            (
                Path(row["spot_file"]).stem,
                row["representation"],
                row["traversal"],
                row["bridge"],
            )
        ].append(row["training_seconds"])
    for key, values in sorted(groups.items()):
        lines.append(
            "| " + " | ".join(key) + f" | {len(values)} | {math.fsum(values):.3f} |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path(CONFIG))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/runs/controlled-training-profile/profile.json"),
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
            (directory / "tables.md").write_text(tables(summary))
            (directory / "summary.json").write_text(
                json.dumps(summary, indent=2, sort_keys=True) + "\n"
            )
            for name, rows in (
                ("timings", saved["rows"]),
                ("forecast", summary["cells"]),
            ):
                with (directory / (name + ".csv")).open("w", newline="") as stream:
                    writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
                    writer.writeheader()
                    writer.writerows(rows)
        return 0
    result = run(root, root / args.config, root / args.output)
    print(f"{result['status']}: {len(result['rows'])}/420 timing rows; {args.output}")
    return 0 if result["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
