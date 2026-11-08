"""Exhaustive static-interface checks, exact trajectories and paired node timings."""

import argparse
import cProfile
import csv
import json
import math
import statistics
import time
from pathlib import Path
from typing import Any, cast

from numpy.random import PCG64, Generator

from poker_ai.abstraction.model import CardAbstraction
from poker_ai.finite import ArrayTree
from poker_ai.postflop import controlled_profile as original
from poker_ai.postflop import row_profile as parent
from poker_ai.postflop.cached_nodes import (
    CachedNodeTrainer,
    audit_interface,
    cache_nodes,
)
from poker_ai.postflop.controlled_training import ControlledTrainer, Rules
from poker_ai.postflop.game import load_spot
from poker_ai.postflop.range_protocol import build_representation_control
from poker_ai.postflop.river_study import Deadline, digest
from poker_ai.postflop.tree import SpotTree
from poker_ai.reproducibility import runtime_environment
from poker_ai.validation.five_card import source_provenance

CONFIG = "configs/cached-node-profile.json"
ENTRY = "scripts/profile_cached_nodes.py"
FORMAT = "poker-ai-cached-node-profile-v1"


def inputs(root: Path, config: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    if (
        type(config["schema_version"]) is not int
        or config["schema_version"] != 1
        or config["status"] != "opt_in_immutable_adapter_only"
        or config["parent_config"] != parent.CONFIG
        or config["parent_profile"] != "results/row-policy-profile/profile.json"
        or set(config["input_sha256"])
        != {
            parent.CONFIG,
            config["parent_profile"],
            "results/row-policy-profile/report/summary.json",
        }
        or config["parity_iterations"] != parent.PARITY
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
        raise ValueError("invalid cached-node profile config")
    if any(digest(root / p) != sha for p, sha in config["input_sha256"].items()):
        raise ArithmeticError("cached-node prerequisites changed")
    previous = json.loads((root / parent.CONFIG).read_text())
    base, protocol = parent.inputs(root, previous)
    parent.report(root, root / config["parent_profile"])
    return base, protocol


def trainer(tree: ArrayTree, cell: dict[str, Any], engine: str) -> ControlledTrainer:
    if engine == "parent":
        return parent.trainer(
            tree, cell, "rows" if cell["traversal"] == "external" else "dense"
        )
    if (
        engine != "nodes"
        or cell["traversal"] != "external"
        or cell["bridge"] != "common"
    ):
        raise ValueError("invalid cached-node backend/cell")
    return CachedNodeTrainer(
        tree,
        Generator(PCG64(cell["seed"])),
        rules=Rules(cell["regret_rule"], cell["regret_weight"], cell["average_weight"]),
    )


def parity(
    tree: ArrayTree, cell: dict[str, Any], checkpoints: list[int], deadline: Deadline
) -> list[dict[str, Any]]:
    a, b = trainer(tree, cell, "parent"), trainer(tree, cell, "nodes")
    a.initialize_exact()
    b.initialize_exact()
    rows = []
    for checkpoint in checkpoints:
        while a.iteration < checkpoint:
            deadline.check()
            a.step()
            b.step()
        try:
            signature = parent.assert_equal(a, b)
            if (cast(Any, a).row_evaluations, cast(Any, a).last_pass_rows) != (
                cast(Any, b).row_evaluations,
                cast(Any, b).last_pass_rows,
            ):
                raise ArithmeticError("row-policy access counts changed")
        except ArithmeticError as error:
            raise ArithmeticError(
                f"{original.identity(cell)} at checkpoint {checkpoint}: {error}"
            ) from error
        rows.append(
            {
                **cell,
                "iteration": checkpoint,
                "state_sha256": signature,
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
    if engine == "parent":
        return parent.measure(
            tree,
            cell,
            "rows" if cell["traversal"] == "external" else "dense",
            steps,
            deadline,
            instrument,
        )
    started = time.perf_counter()
    solver = cast(CachedNodeTrainer, trainer(tree, cell, engine))
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
        "state_sha256": parent.fingerprint(solver),
        "tree_nodes": len(tree.player),
        "information_sets": len(tree.keys),
        "width": tree.legal.shape[1],
    }
    diagnostics = dict(
        row_evaluations=solver.row_evaluations,
        last_pass_rows=list(solver.last_pass_rows),
        node_records_prepared=solver.node_records_prepared,
        node_setup_seconds=solver.node_setup_seconds,
    )
    return row, diagnostics


def canonical_roles(saved: dict[str, Any]) -> dict[str, Any]:
    """Reuse the frozen generic paired validator: names only, no value changes.

    Its legacy dense/rows columns mean reference/candidate here. Public evidence
    names the actual parent/nodes implementations, including unchanged full cells.
    """
    roles = {"parent": "dense", "nodes": "rows"}
    return {
        **saved,
        "timings": {roles[k]: v for k, v in saved["timings"].items()},
        "pair_orders": [
            {**o, "order": [roles[e] for e in o["order"]]} for o in saved["pair_orders"]
        ],
        "profiles": [{**p, "engine": roles[p["engine"]]} for p in saved["profiles"]],
    }


def validate(saved: dict[str, Any], protocol: dict[str, Any]) -> None:
    parent.validate(canonical_roles(saved), protocol)
    all_cells = original.cells(protocol["future_comparison"])
    expected = {(c["spot_file"], c["representation"]) for c in all_cells}
    checks = saved["adapter_checks"]
    ids = [(c["spot_file"], c["representation"]) for c in checks]
    if len(ids) != len(set(ids)) or set(ids) != expected:
        raise ArithmeticError("adapter-interface grid incomplete")
    reference = saved["timings"]["parent"]
    for c in checks:
        peer = next(
            r
            for r in reference
            if r["spot_file"] == c["spot_file"]
            and r["representation"] == c["representation"]
        )
        if (
            any(
                type(c[k]) is not int or c[k] < 0
                for k in (
                    "nodes",
                    "edges",
                    "decision_nodes",
                    "invalid_property_errors",
                    "invalid_action_pairs",
                )
            )
            or c["nodes"] != peer["tree_nodes"]
            or c["edges"] != c["nodes"] - 1
            or not 0 < c["decision_nodes"] < c["nodes"]
            or c["invalid_property_errors"] != 3 * c["nodes"] - c["decision_nodes"]
            or c["invalid_action_pairs"] != 2 * c["nodes"]
        ):
            raise ArithmeticError("adapter-interface coverage changed")
    candidates = {
        (original.identity(r), r["repeat"]): r for r in saved["timings"]["nodes"]
    }
    for d in saved["cache_diagnostics"]:
        row = candidates[original.identity(d), d["repeat"]]
        if (
            type(d["node_records_prepared"]) is not int
            or d["node_records_prepared"] != row["tree_nodes"]
            or type(d["node_setup_seconds"]) not in (int, float)
            or not math.isfinite(d["node_setup_seconds"])
            or d["node_setup_seconds"] < 0
            or d["node_setup_seconds"] > row["initialization_seconds"]
        ):
            raise ArithmeticError("cached preparation accounting changed")


def run(root: Path, config_path: Path, output: Path) -> dict[str, Any]:
    if output.exists():
        raise FileExistsError("retain cached-node evidence")
    started = time.perf_counter()
    config: dict[str, Any] = json.loads(config_path.read_text())
    base, protocol = inputs(root, config)
    source = source_provenance(root, config_path, entrypoints=(ENTRY,))
    if source["dirty"] is not False:
        raise ValueError("publish checked node-cache code first")
    deadline = Deadline(config["maximum_seconds"])
    deadline.started = started
    result: dict[str, Any] = dict(
        format=FORMAT,
        status="running",
        failure=None,
        config=config,
        source=source,
        environment=runtime_environment(),
        adapter_checks=[],
        parity=[],
        timings={"parent": [], "nodes": []},
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
        model = CardAbstraction.load(root / "results/card-models/potential-8.json")
        workload = original.cells(protocol["future_comparison"])
        external = [c for c in workload if c["traversal"] == "external"]
        trees = {}
        for game in protocol["future_comparison"]["spot_files"]:
            raw = SpotTree.build(load_spot(root / game))
            for name in protocol["future_comparison"]["representations"]:
                tree = build_representation_control(raw, name, model)
                trees[game, name] = tree
                result["adapter_checks"].append(
                    dict(
                        spot_file=game,
                        representation=name,
                        **audit_interface(tree, cache_nodes(tree)),
                    )
                )
        persist()
        for i, cell in enumerate(external):
            result["parity"].extend(
                parity(
                    trees[cell["spot_file"], cell["representation"]],
                    cell,
                    parent.PARITY,
                    deadline,
                )
            )
            print(f"node parity {i + 1}/96", flush=True)
            persist()
        for cell in workload:
            tree = trees[cell["spot_file"], cell["representation"]]
            steps = config[f"{cell['traversal']}_iterations_after_initialization"]
            for repeat in range(config["repetitions"]):
                if cell["traversal"] == "external":
                    i = external.index(cell)
                    order = (
                        ["parent", "nodes"]
                        if (i + repeat) % 2 == 0
                        else ["nodes", "parent"]
                    )
                    result["pair_orders"].append(
                        {**cell, "repeat": repeat, "order": order}
                    )
                else:
                    order = ["parent"]
                for engine in order:
                    row, diag = measure(tree, cell, engine, steps, deadline)
                    result["timings"][engine].append({**row, "repeat": repeat})
                    if engine == "nodes":
                        result["cache_diagnostics"].append(
                            {**cell, "repeat": repeat, **diag}
                        )
            count = sum(len(r) for r in result["timings"].values())
            print(f"node timed {count}/708", flush=True)
            persist()
        for cell in base["profiler_cases"]:
            tree = trees[cell["spot_file"], cell["representation"]]
            for engine in (
                ["parent", "nodes"] if cell["traversal"] == "external" else ["parent"]
            ):
                instrument = cProfile.Profile()
                row, _ = measure(
                    tree,
                    cell,
                    engine,
                    config[f"{cell['traversal']}_iterations_after_initialization"],
                    deadline,
                    instrument,
                )
                result["profiles"].append(
                    {
                        **row,
                        "engine": engine,
                        "hotspots": original.hotspots(instrument, root, 25),
                    }
                )
        validate(result, protocol)
        inputs(root, config)
        if any(
            digest(root / p) != sha
            for p, sha in cast(dict[str, str], source["sha256"]).items()
        ):
            raise ArithmeticError("cached-node source changed")
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
    base, protocol = inputs(root, saved["config"])
    if (
        saved["format"] != FORMAT
        or saved["status"] != "completed"
        or saved["failure"] is not None
        or saved["strength_comparison_performed"] is not False
        or saved["source"]["dirty"] is not False
        or not {
            ENTRY,
            CONFIG,
            "src/poker_ai/postflop/cached_nodes.py",
            "src/poker_ai/postflop/node_profile.py",
        }.issubset(saved["source"]["sha256"])
        or any(digest(root / p) != sha for p, sha in saved["source"]["sha256"].items())
        or json.loads((root / CONFIG).read_text()) != saved["config"]
    ):
        raise ArithmeticError("partial/changed cached-node evidence")
    validate(saved, protocol)
    measured = math.fsum(
        r["initialization_seconds"] + r["incremental_seconds"]
        for r in saved["timings"]["parent"]
        + saved["timings"]["nodes"]
        + saved["profiles"]
    )
    if (
        type(saved["seconds"]) not in (int, float)
        or not math.isfinite(saved["seconds"])
        or measured > saved["seconds"] + 1e-6
    ):
        raise ArithmeticError("invalid cached-node elapsed time")
    reference = saved["timings"]["parent"]
    mixed = [r for r in reference if r["traversal"] == "full"] + saved["timings"][
        "nodes"
    ]
    forecasts = {
        engine: original.forecast(
            rows,
            base["forecast_target_node_work"],
            base["forecast_guard_multiplier"],
            protocol["future_comparison"]["maximum_own_seconds"],
        )
        for engine, rows in (("parent", reference), ("nodes", mixed))
    }
    index = {(original.identity(r), r["repeat"]): r for r in reference}
    ratios = [
        {
            **{k: r[k] for k in original.KEY},
            "repeat": r["repeat"],
            "parent_over_nodes": index[original.identity(r), r["repeat"]][
                "incremental_seconds"
            ]
            / r["incremental_seconds"],
        }
        for r in saved["timings"]["nodes"]
    ]
    summary = dict(
        input_sha256=digest(path),
        forecasts=forecasts,
        paired_ratios=ratios,
        median_paired_ratio=statistics.median(r["parent_over_nodes"] for r in ratios),
        adapter_nodes=sum(c["nodes"] for c in saved["adapter_checks"]),
        adapter_edges=sum(c["edges"] for c in saved["adapter_checks"]),
        parity_cells=len(saved["parity"]) // len(parent.PARITY),
        parity_checkpoints=len(saved["parity"]),
        timing_rows=sum(len(r) for r in saved["timings"].values()),
        seconds=saved["seconds"],
        strength_comparison_performed=False,
    )
    return saved, summary


def tables(summary: dict[str, Any]) -> str:
    lines = [
        "# Immutable-node paired profile",
        "",
        "Exact interface/trajectory checks; timing estimates only.",
        "",
        f"Interface: {summary['adapter_nodes']} nodes / "
        f"{summary['adapter_edges']} edges.",
        f"Parity: {summary['parity_cells']} cells / "
        f"{summary['parity_checkpoints']} checkpoints.",
        f"Timing rows: {summary['timing_rows']}; median paired parent / nodes: "
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
        "Fresh graph construction is charged to initialization; static-node records "
        "are separate from unchanged CFR visits.",
        "Full cells are shared. Other pipeline costs remain unestimated; "
        "no strength/default/admission claim.",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path(CONFIG))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/runs/cached-node-profile/profile.json"),
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
                ("parent", saved["timings"]["parent"]),
                ("nodes", saved["timings"]["nodes"]),
                ("ratios", summary["paired_ratios"]),
            ):
                with (directory / (name + ".csv")).open("w", newline="") as stream:
                    writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
                    writer.writeheader()
                    writer.writerows(rows)
        return 0
    result = run(root, root / args.config, root / args.output)
    print(
        f"{result['status']}: {len(result['adapter_checks'])} interface grids, "
        f"{len(result['parity'])} checkpoints, "
        f"{sum(len(r) for r in result['timings'].values())} timings"
    )
    return 0 if result["status"] == "completed" else 1
