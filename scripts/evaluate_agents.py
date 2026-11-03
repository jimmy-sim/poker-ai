"""Run preregistered frozen-agent duplicate matches and retain every hand result."""

import argparse
import csv
import hashlib
import importlib
import importlib.metadata
import json
import multiprocessing
import os
import platform
import shutil
import subprocess
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

from poker_ai.evaluation.experiment import betting_rules, load_config, own_rows, worker
from poker_ai.evaluation.reference_validation import validate_native_traces
from poker_ai.validation.five_card import source_provenance


def figures(results: list[dict[str, Any]], output: Path) -> list[Path]:
    os.environ.setdefault("MPLCONFIGDIR", str(output / "runs/mpl-cache"))
    mpl = importlib.import_module("matplotlib")
    mpl.use("Agg")
    mpl.rcParams["svg.hashsalt"] = "poker-ai-evaluation"
    plt = importlib.import_module("matplotlib.pyplot")
    fig, axis = plt.subplots(figsize=(11, 5), layout="constrained")
    for index, result in enumerate(results):
        data = result["primary_inference"]
        mean = data["mbb_per_hand"]
        for field, color, offset, label in (
            (
                "hoeffding_interval_mbb_per_hand",
                "#b5bcc6",
                -0.06,
                "95% Hoeffding interval",
            ),
            (
                "clt_interval_mbb_per_hand",
                "#176b9b",
                0.06,
                "95% CLT interval (approx.)",
            ),
        ):
            low, high = data[field]
            axis.errorbar(
                mean,
                index + offset,
                xerr=[[mean - low], [high - mean]],
                fmt="o",
                color=color,
                capsize=4,
                label=label if index == 0 else None,
            )
    axis.set_yticks(range(len(results)), [r["opponent"] for r in results])
    axis.axvline(0, color="black", linewidth=0.8)
    axis.set(
        xlabel="Own net milli-big-blinds per hand (three fixed agents, paired deals)",
        title="Frozen-policy evaluation: uncertainty uses independent decks",
    )
    axis.grid(axis="x", alpha=0.2)
    axis.legend(fontsize=8)
    files = []
    for suffix in ("png", "svg"):
        path = output / f"winrate-intervals.{suffix}"
        fig.savefig(path, dpi=160, metadata={"Date": None} if suffix == "svg" else None)
        files.append(path)
    plt.close(fig)
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--mode", choices=("pilot", "main"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    config = load_config(args.config)
    source = source_provenance(
        root, args.config, entrypoints=("scripts/evaluate_agents.py",)
    )
    frozen = own_rows(root, config)
    rules = betting_rules(config)
    os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    started = time.perf_counter()
    controls = validate_native_traces(
        rules,
        seed=config["native_validation"]["seed"],
        hands=config["native_validation"]["hands"],
    )
    print(
        f"native mechanics gate: {controls['hands']} hands / "
        f"{controls['actions']} actions; "
        f"payout error={controls['max_payout_error']}",
        flush=True,
    )
    build = args.output.parent / "runs" / args.output.stem
    build.mkdir(parents=True, exist_ok=True)
    tasks = [
        {
            "root": str(root),
            "config": config,
            "own_rows": frozen,
            "opponent": opponent,
            "opponent_index": index,
            "mode": args.mode,
            "raw_dir": str((build / "raw").resolve()),
        }
        for index, opponent in enumerate(config["opponents"])
    ]
    results = []
    failures = []
    with ProcessPoolExecutor(
        max_workers=config["workers"],
        mp_context=multiprocessing.get_context("spawn"),
        max_tasks_per_child=1,
    ) as pool:
        futures = [pool.submit(worker, task) for task in tasks]
        for task, future in zip(tasks, futures, strict=True):
            try:
                result = future.result()
            except Exception as error:
                failures.append(
                    {
                        "opponent": task["opponent"]["name"],
                        "error": type(error).__name__,
                        "reason": str(error),
                    }
                )
                print(f"failed {task['opponent']['name']}: {error}", flush=True)
                continue
            results.append(result)
            if result["status"] != "completed":
                failures.append(
                    {"opponent": result["opponent"], "reason": result["failure"]}
                )
            print(
                f"{args.mode}/{result['opponent']}: {result['status']}, "
                f"{result['completed_deals']} decks / {result['hands']} hands "
                f"in {result['seconds']:.2f}s",
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
    report: dict[str, Any] = {
        "schema_version": 1,
        "status": "failed" if failures else "completed",
        "mode": args.mode,
        "source": source,
        "config": config,
        "native_controls": controls,
        "failures": failures,
        "frozen_agents": [
            {
                key: row[key]
                for key in ("model", "method", "seed", "iteration", "checkpoint_sha256")
            }
            for row in frozen
        ],
        "training_report_sha256": hashlib.sha256(
            (root / config["training_report"]).read_bytes()
        ).hexdigest(),
        "results": results,
        "seconds": time.perf_counter() - started,
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "cpu_model": cpu,
            "logical_cpus": os.cpu_count(),
            **{
                p: importlib.metadata.version(p)
                for p in ("numpy", "open_spiel", "matplotlib")
            },
        },
    }
    if args.mode == "pilot" and not failures:
        projected = (
            sum(r["seconds"] for r in results)
            * config["main_deals"]
            / config["pilot_deals"]
        )
        report["main_projected_serial_worker_seconds"] = projected
        report["projection_caveat"] = (
            "linear extrapolation includes startup/cache effects; "
            "parallel wall time differs"
        )
    if failures:
        failed = build / "failed-report.json"
        failed.write_text(
            json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
        )
        print(f"failed; no reviewed results replaced: {failed}", flush=True)
        return 1
    destination = args.output.parent
    destination.mkdir(parents=True, exist_ok=True)
    artifacts = []
    summary = []
    for result in results:
        raw_path = Path(result["raw_file"])
        if hashlib.sha256(raw_path.read_bytes()).hexdigest() != result["raw_sha256"]:
            raise ArithmeticError("raw match artifact changed")
        published = destination / raw_path.name
        shutil.copyfile(raw_path, published)
        result["raw_file"] = published.name
        artifacts.append(published)
        stats = result["primary_inference"]
        summary.append(
            {
                "opponent": result["opponent"],
                "deals": stats["independent_deals"],
                "hands": result["hands"],
                "mbb_per_hand": stats["mbb_per_hand"],
                "clt_low": stats["clt_interval_mbb_per_hand"][0],
                "clt_high": stats["clt_interval_mbb_per_hand"][1],
                "hoeffding_low": stats["hoeffding_interval_mbb_per_hand"][0],
                "hoeffding_high": stats["hoeffding_interval_mbb_per_hand"][1],
                "family_adjusted_p_bound": stats["family_adjusted_two_sided_p_bound"],
                "positive_significant": stats["positive_mean_significant"],
                "paired_variance_ratio": stats["paired_to_unpaired_variance_ratio"],
            }
        )
    table = destination / "match-summary.csv"
    with table.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(summary[0]))
        writer.writeheader()
        writer.writerows(summary)
    artifacts.append(table)
    lines = [
        "| Opponent | mbb/hand | Approx. 95% CLT CI | "
        "Conservative 95% Hoeffding CI | Adjusted p bound | Paired variance ratio |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in summary:
        ratio = (
            "undefined"
            if row["paired_variance_ratio"] is None
            else f"{row['paired_variance_ratio']:.3f}"
        )
        lines.append(
            f"| {row['opponent']} | {row['mbb_per_hand']:+.1f} | "
            f"[{row['clt_low']:+.1f}, {row['clt_high']:+.1f}] | "
            f"[{row['hoeffding_low']:+.1f}, {row['hoeffding_high']:+.1f}] | "
            f"{row['family_adjusted_p_bound']:.3g} | {ratio} |"
        )
    markdown = destination / "match-summary.md"
    markdown.write_text("\n".join(lines) + "\n")
    artifacts.append(markdown)
    artifacts.extend(figures(results, destination))
    report["artifacts_sha256"] = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in artifacts
    }
    report["seconds"] = time.perf_counter() - started
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    print(f"completed {args.mode}: {args.output}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
