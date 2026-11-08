"""Fixed independent-cell process calibration; no learning-strength comparison."""

import argparse
import csv
import json
import math
import statistics
import time
from pathlib import Path
from typing import Any, cast

from poker_ai.abstraction.model import CardAbstraction
from poker_ai.postflop import controlled_profile as original
from poker_ai.postflop import node_profile as previous
from poker_ai.postflop.cell_process import THREAD_ENV, Send, run_batch
from poker_ai.postflop.game import load_spot
from poker_ai.postflop.range_protocol import build_representation_control
from poker_ai.postflop.river_study import Deadline, digest
from poker_ai.postflop.tree import SpotTree
from poker_ai.reproducibility import runtime_environment
from poker_ai.validation.five_card import source_provenance

CONFIG = "configs/parallel-cell-profile.json"
ENTRY = "scripts/profile_parallel_cells.py"
FORMAT = "poker-ai-independent-cell-profile-v1"
COUNTS = [1, 2, 3]
ORDERS = [[1, 2, 3], [2, 3, 1], [3, 1, 2]]


def same(a: Any, b: Any) -> bool:
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    if isinstance(a, (list, tuple)):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b, strict=True))
    return bool(a == b)


def finite(value: Any, *, positive: bool = False) -> bool:
    return (
        type(value) in (int, float)
        and math.isfinite(value)
        and (value > 0 if positive else value >= 0)
    )


def inputs(
    root: Path, config: dict[str, Any]
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    fixed = dict(
        schema_version=1,
        status="profile_only_no_learning_admission",
        node_profile="results/cached-node-profile/profile.json",
        worker_counts=COUNTS,
        repetitions=3,
        round_orders=ORDERS,
        assignment="fixed original 140-cell order; cell index modulo worker count",
        start_method="spawn",
        child_thread_environment=THREAD_ENV,
        external_iterations_after_initialization=1000,
        full_iterations_after_initialization=16,
        maximum_seconds=1200,
        forecast_target_node_work=10000000,
        forecast_guard_multiplier=2.0,
        own_stage_cap_seconds=7200,
    )
    pins = {
        previous.CONFIG,
        fixed["node_profile"],
        "results/cached-node-profile/report/summary.json",
        "configs/training-isolation.json",
    }
    if (
        any(not same(config[k], v) for k, v in fixed.items())
        or set(config["input_sha256"]) != pins
        or any(digest(root / p) != sha for p, sha in config["input_sha256"].items())
        or not same(json.loads((root / CONFIG).read_text()), config)
    ):
        raise ValueError("invalid fixed process calibration config/inputs")
    prior, _ = previous.report(root, root / config["node_profile"])
    protocol = json.loads((root / "configs/training-isolation.json").read_text())
    return prior, original.cells(protocol["future_comparison"]), protocol


def real_partition(
    slot: int, indices: list[int], payload: dict[str, Any], send: Send
) -> dict[str, Any]:
    """Fresh worker-local matrices/trainers/RNG; shared payload is read-only."""
    del slot
    root = Path(payload["root"])
    config, comparison = payload["config"], payload["comparison"]
    deadline = Deadline(payload["remaining_seconds"])
    started = time.perf_counter()
    model = CardAbstraction.load(root / "results/card-models/potential-8.json")
    trees = {}
    for game in comparison["spot_files"]:
        raw = SpotTree.build(load_spot(root / game))
        for name in comparison["representations"]:
            deadline.check()
            trees[game, name] = build_representation_control(raw, name, model)
    send(
        dict(
            kind="prepared",
            seconds=time.perf_counter() - started,
            tree_nodes={json.dumps(k): len(v.player) for k, v in trees.items()},
        )
    )
    for index in indices:
        cell = payload["cells"][index]
        started, cpu = time.perf_counter(), time.process_time()
        row, diagnostics = previous.measure(
            trees[cell["spot_file"], cell["representation"]],
            cell,
            "nodes" if cell["traversal"] == "external" else "parent",
            config[f"{cell['traversal']}_iterations_after_initialization"],
            deadline,
        )
        send(
            dict(
                kind="cell",
                index=index,
                row=row,
                diagnostics=diagnostics,
                seconds=time.perf_counter() - started,
                cpu_seconds=time.process_time() - cpu,
            )
        )
    return dict(cells=len(indices))


def endpoint_reference(prior: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = [r for r in prior["timings"]["parent"] if r["traversal"] == "full"]
    rows += prior["timings"]["nodes"]
    return {original.identity(r): r for r in rows if r["repeat"] == 0}


def validate(
    saved: dict[str, Any], prior: dict[str, Any], cells: list[dict[str, Any]]
) -> None:
    """Require complete ordered batches, exact endpoint fields and cost coverage."""
    batches = saved["batches"]
    wanted = [(r, p) for r, order in enumerate(ORDERS) for p in order]
    if not same([(b["repeat"], b["worker_count"]) for b in batches], wanted):
        raise ArithmeticError("process-count/repeat order changed")
    reference = endpoint_reference(prior)
    diagnostics = {
        original.identity(d): d for d in prior["cache_diagnostics"] if d["repeat"] == 0
    }
    tree_nodes = {
        json.dumps((r["spot_file"], r["representation"])): r["tree_nodes"]
        for r in reference.values()
    }
    count = 0
    for batch in batches:
        p = batch["worker_count"]
        assignments = [list(range(s, len(cells), p)) for s in range(p)]
        if (
            batch["status"] != "completed"
            or batch["failure"] is not None
            or not same(batch["assignments"], assignments)
            or len(batch["workers"]) != p
            or not finite(batch["seconds"], positive=True)
            or not finite(batch["parent_cpu_seconds"])
            or not finite(batch["reaped_children_cpu_seconds"])
        ):
            raise ArithmeticError("partial/changed process batch")
        pids = []
        for slot, worker in enumerate(batch["workers"]):
            indices = assignments[slot]
            events = worker["messages"]
            if (
                not same(worker["slot"], slot)
                or type(worker["pid"]) is not int
                or worker["pid"] <= 0
                or not same(worker["exitcode"], 0)
                or [e["kind"] for e in events]
                != ["started", "prepared"] + ["cell"] * len(indices) + ["done"]
                or not same(events[0]["pid"], worker["pid"])
                or not same(events[0]["thread_environment"], THREAD_ENV)
                or not same(events[1]["tree_nodes"], tree_nodes)
                or not finite(events[1]["seconds"])
                or not same(events[-1]["summary"], dict(cells=len(indices)))
                or not finite(events[-1]["seconds"], positive=True)
                or not finite(events[-1]["cpu_seconds"])
                or events[-1]["seconds"] > batch["seconds"] + 1e-6
            ):
                raise ArithmeticError("changed worker identity/events/setup")
            pids.append(worker["pid"])
            measured = events[1]["seconds"]
            for index, event in zip(indices, events[2:-1], strict=True):
                row = event["row"]
                expected = reference[original.identity(cells[index])]
                if (
                    not same(event["index"], index)
                    or set(row)
                    != set(original.KEY)
                    | set(original.STABLE)
                    | {"initialization_seconds", "incremental_seconds"}
                    or any(
                        not same(row[k], expected[k])
                        for k in (*original.KEY, *original.STABLE)
                    )
                    or not finite(row["initialization_seconds"], positive=True)
                    or not finite(row["incremental_seconds"], positive=True)
                    or not finite(event["seconds"], positive=True)
                    or not finite(event["cpu_seconds"])
                    or row["initialization_seconds"] + row["incremental_seconds"]
                    > event["seconds"] + 1e-6
                ):
                    raise ArithmeticError(
                        "cell endpoint/work/timing differs from serial"
                    )
                diag = event["diagnostics"]
                if row["traversal"] == "full":
                    if diag != {}:
                        raise ArithmeticError("full cell unexpectedly cached")
                else:
                    peer = diagnostics[original.identity(row)]
                    if (
                        set(diag)
                        != {
                            "row_evaluations",
                            "last_pass_rows",
                            "node_records_prepared",
                            "node_setup_seconds",
                        }
                        or any(
                            not same(diag[k], peer[k])
                            for k in (
                                "row_evaluations",
                                "last_pass_rows",
                                "node_records_prepared",
                            )
                        )
                        or not finite(diag["node_setup_seconds"])
                        or diag["node_setup_seconds"] > row["initialization_seconds"]
                    ):
                        raise ArithmeticError("cached-node accounting changed")
                measured += event["seconds"]
                count += 1
            if measured > events[-1]["seconds"] + 1e-6:
                raise ArithmeticError("worker timers omit measured work")
        if len(set(pids)) != p:
            raise ArithmeticError("workers did not have distinct processes")
    if count != 1260:
        raise ArithmeticError("incomplete endpoint grid")
    if (
        not finite(saved["seconds"], positive=True)
        or math.fsum(b["seconds"] for b in batches) > saved["seconds"] + 1e-6
        or saved["seconds"] > saved["config"]["maximum_seconds"]
    ):
        raise ArithmeticError("invalid total calibration time")


def forecast(
    batches: list[dict[str, Any]], cells: list[dict[str, Any]], config: dict[str, Any]
) -> dict[str, Any]:
    """Conservative fixed-partition makespan; never serial-time/core-count."""
    p = batches[0]["worker_count"]
    rows = [
        event["row"]
        for b in batches
        for w in b["workers"]
        for event in w["messages"]
        if event["kind"] == "cell"
    ]
    estimates = original.forecast(
        rows,
        config["forecast_target_node_work"],
        config["forecast_guard_multiplier"],
        config["own_stage_cap_seconds"],
    )
    by_cell = {original.identity(r): r["training_seconds"] for r in estimates["cells"]}
    sums = [
        math.fsum(by_cell[original.identity(cells[i])] for i in range(s, len(cells), p))
        for s in range(p)
    ]
    # These residuals retain preparation, exports/fingerprints, IPC/collection and
    # launch/import/join. Each max is conservative over observed short workloads;
    # additional future scoring/checkpoint costs are still unmeasured.
    worker_extra = max(
        w["messages"][-1]["seconds"]
        - math.fsum(
            e["row"]["initialization_seconds"] + e["row"]["incremental_seconds"]
            for e in w["messages"]
            if e["kind"] == "cell"
        )
        for b in batches
        for w in b["workers"]
    )
    launch_extra = max(
        b["seconds"] - max(w["messages"][-1]["seconds"] for w in b["workers"])
        for b in batches
    )
    known = max(sums) + worker_extra + launch_extra
    guarded = config["forecast_guard_multiplier"] * known
    return dict(
        worker_training_seconds=sums,
        maximum_worker_nontraining_seconds=worker_extra,
        maximum_launch_collection_seconds=launch_extra,
        known_training_launch_forecast_seconds=known,
        guarded_known_seconds=guarded,
        cap_seconds=config["own_stage_cap_seconds"],
        decision="known_cost_exceeds_cap"
        if guarded > config["own_stage_cap_seconds"]
        else "unresolved_unmeasured_pipeline_cost",
        strength_comparison_performed=False,
    )


def run(root: Path, output: Path) -> dict[str, Any]:
    if output.exists():
        raise FileExistsError("retain process-calibration evidence")
    started = time.perf_counter()
    config = json.loads((root / CONFIG).read_text())
    prior, cells, protocol = inputs(root, config)
    source = source_provenance(root, root / CONFIG, entrypoints=(ENTRY,))
    if source["dirty"] is not False:
        raise ValueError("publish checked process-calibration code first")
    deadline = Deadline(config["maximum_seconds"])
    deadline.started = started
    saved: dict[str, Any] = dict(
        format=FORMAT,
        status="running",
        failure=None,
        config=config,
        source=source,
        environment=runtime_environment(),
        batches=[],
        seconds=0.0,
        strength_comparison_performed=False,
    )
    output.parent.mkdir(parents=True, exist_ok=True)

    def persist() -> None:
        saved["seconds"] = time.perf_counter() - started
        tmp = output.with_suffix(".tmp")
        tmp.write_text(
            json.dumps(saved, sort_keys=True, indent=2, allow_nan=False) + "\n"
        )
        tmp.replace(output)

    try:
        for repeat, order in enumerate(ORDERS):
            for p in order:
                batch: dict[str, Any] = {}
                saved["batches"].append(batch)
                payload = dict(
                    root=str(root),
                    config=config,
                    cells=cells,
                    comparison=protocol["future_comparison"],
                    remaining_seconds=config["maximum_seconds"]
                    - (time.perf_counter() - started),
                )
                try:
                    run_batch(len(cells), p, real_partition, payload, deadline, batch)
                finally:
                    batch["repeat"] = repeat
                persist()
                print(
                    f"process calibration repeat {repeat + 1}/3: {p} workers",
                    flush=True,
                )
        validate(saved, prior, cells)
        inputs(root, config)
        if any(
            digest(root / path) != sha
            for path, sha in cast(dict[str, str], source["sha256"]).items()
        ):
            raise ArithmeticError("calibration source changed")
        deadline.check()
        saved["status"] = "completed"
    except (Exception, KeyboardInterrupt) as error:
        saved["status"] = "incomplete"
        saved["failure"] = dict(type=type(error).__name__, reason=str(error))
    finally:
        persist()
    return saved


def report(root: Path, path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    saved: dict[str, Any] = json.loads(path.read_text())
    json.dumps(saved, allow_nan=False)
    prior, cells, _ = inputs(root, saved["config"])
    if (
        saved["format"] != FORMAT
        or saved["status"] != "completed"
        or saved["failure"] is not None
        or saved["strength_comparison_performed"] is not False
        or saved["source"]["dirty"] is not False
        or not {
            ENTRY,
            CONFIG,
            "src/poker_ai/postflop/cell_process.py",
            "src/poker_ai/postflop/parallel_profile.py",
        }.issubset(saved["source"]["sha256"])
        or any(digest(root / p) != sha for p, sha in saved["source"]["sha256"].items())
    ):
        raise ArithmeticError("partial/changed process-calibration evidence")
    validate(saved, prior, cells)
    baseline = {b["repeat"]: b for b in saved["batches"] if b["worker_count"] == 1}
    batches = [
        dict(
            repeat=b["repeat"],
            worker_count=b["worker_count"],
            seconds=b["seconds"],
            serial_over_batch=baseline[b["repeat"]]["seconds"] / b["seconds"],
            parent_cpu_seconds=b["parent_cpu_seconds"],
            reaped_children_cpu_seconds=b["reaped_children_cpu_seconds"],
            aggregate_cpu_seconds=b["parent_cpu_seconds"]
            + b["reaped_children_cpu_seconds"],
        )
        for b in saved["batches"]
    ]
    summary = dict(
        input_sha256=digest(path),
        endpoint_rows=1260,
        seconds=saved["seconds"],
        batches=batches,
        forecasts={
            str(p): forecast(
                [b for b in saved["batches"] if b["worker_count"] == p],
                cells,
                saved["config"],
            )
            for p in COUNTS
        },
        strength_comparison_performed=False,
    )
    return saved, summary


def tables(summary: dict[str, Any]) -> str:
    lines = [
        "# Independent-cell process calibration",
        "",
        "All 1260 short-workload endpoints exactly match the pinned serial profile.",
        "CPU seconds include parent plus reaped children; elapsed seconds differ.",
        "",
        "| Workers | Median batch wall (s) | Median serial / batch | Median CPU (s) | "
        "2x known-cost forecast (s) | Decision |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for p in COUNTS:
        rows = [b for b in summary["batches"] if b["worker_count"] == p]
        f = summary["forecasts"][str(p)]
        wall, ratio, cpu = (
            statistics.median(r[k] for r in rows)
            for k in ("seconds", "serial_over_batch", "aggregate_cpu_seconds")
        )
        lines.append(
            f"| {p} | {wall:.3f} | {ratio:.3f} | {cpu:.3f} | "
            f"{f['guarded_known_seconds']:.3f} | {f['decision']} |"
        )
    lines += [
        "",
        "Fixed partitions and max-of-three cell forecasts include measured "
        "launch/tree/export/collection overhead, then the unchanged 2x margin.",
        "Future scoring/checkpoint/audit costs remain unmeasured. "
        "No automatic learning admission, default or playing-strength claim.",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/runs/parallel-cell-profile/profile.json"),
    )
    parser.add_argument("--report", type=Path)
    parser.add_argument("--tables", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    if args.report:
        _, summary = report(root, root / args.report)
        print(tables(summary))
        if args.tables:
            directory = root / args.tables
            directory.mkdir(parents=True, exist_ok=False)
            (directory / "summary.json").write_text(
                json.dumps(summary, sort_keys=True, indent=2) + "\n"
            )
            (directory / "tables.md").write_text(tables(summary))
            with (directory / "batches.csv").open("w", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=list(summary["batches"][0]))
                writer.writeheader()
                writer.writerows(summary["batches"])
        return 0
    saved = run(root, root / args.output)
    print(f"{saved['status']}: {len(saved['batches'])} process batches")
    return 0 if saved["status"] == "completed" else 1
