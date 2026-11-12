"""Audited known-game results; seed ranges are descriptive, not confidence bands."""

import csv
import importlib
import json
import statistics
import time
from pathlib import Path
from typing import Any

from poker_ai.evaluation import compact_sampled_inputs as inputs
from poker_ai.evaluation import compact_sampled_own as own
from poker_ai.evaluation.compact_sampled_clock import measurement
from poker_ai.evaluation.compact_sampled_gate import (
    bound,
    checked_native,
    require_admission,
)
from poker_ai.evaluation.compact_sampled_prior import verify
from poker_ai.postflop import compact_full_artifacts as files
from poker_ai.postflop.compact_full_run import runtime
from poker_ai.postflop.public_range_acceptance import assess_sampled
from poker_ai.postflop.public_range_definition import CANDIDATE, contract


def summaries(rows: list[dict[str, Any]], config: dict[str, Any]) -> dict[str, Any]:
    """All paired signs retained; smaller exploitability is better."""
    sampled = config["sampled"]
    ids = [inputs.identity(r, inputs.IDENTITY) for r in rows]
    expected = {
        (s, r, seed, w, readout)
        for s in config["spot_files"]
        for r in config["representations"]
        for seed in sampled["seeds"]
        for w in sampled["node_work_checkpoints"]
        for readout in inputs.READOUTS
    }
    if len(ids) != 324 or len(set(ids)) != 324 or set(ids) != expected:
        raise ArithmeticError("all324 unique rows required for result summaries")
    lookup = dict(zip(ids, rows, strict=True))
    curves = []
    for spot in config["spot_files"]:
        for rep in config["representations"]:
            for readout in inputs.READOUTS:
                for work in sampled["node_work_checkpoints"]:
                    values = [
                        lookup[spot, rep, seed, work, readout]["exploitability_pot"]
                        for seed in sampled["seeds"]
                    ]
                    curves.append(
                        dict(
                            spot_file=spot,
                            representation=rep,
                            readout=readout,
                            work_checkpoint=work,
                            seeds=sampled["seeds"],
                            values=values,
                            median=statistics.median(values),
                            minimum=min(values),
                            maximum=max(values),
                        )
                    )
    paired = []
    superiority = []
    for baseline in config["representations"]:
        if baseline == CANDIDATE:
            continue
        both = []
        for spot in config["spot_files"]:
            differences = []
            for seed in sampled["seeds"]:
                key = (
                    spot,
                    CANDIDATE,
                    seed,
                    sampled["node_work_checkpoints"][-1],
                    "linear",
                )
                other = (spot, baseline, *key[2:])
                difference = (
                    lookup[key]["exploitability_pot"]
                    - lookup[other]["exploitability_pot"]
                )
                differences.append(difference)
                paired.append(
                    dict(
                        spot_file=spot,
                        baseline=baseline,
                        candidate=CANDIDATE,
                        seed=seed,
                        candidate_minus_baseline_pot=difference,
                        interpretation=(
                            "negative favors candidate; positive favors baseline"
                        ),
                    )
                )
            median = statistics.median(differences)
            both.append(median < 0)
            superiority.append(
                dict(
                    spot_file=spot,
                    baseline=baseline,
                    median_candidate_minus_baseline_pot=median,
                    candidate_paired_median_better=median < 0,
                )
            )
        superiority.append(
            dict(baseline=baseline, both_games_paired_median_better=all(both))
        )
    return dict(
        curves=curves,
        final_linear_paired=paired,
        baseline_specific_superiority=superiority,
        interval_scope=(
            "Median/minimum/maximum of three fixed seeds; not confidence intervals"
        ),
    )


def plot(rows: list[dict[str, Any]], output: Path, config: dict[str, Any]) -> None:
    matplotlib = importlib.import_module("matplotlib")
    matplotlib.use("Agg")
    plt = importlib.import_module("matplotlib.pyplot")

    fig, axes = plt.subplots(1, 2, figsize=(13, 5), sharey=False)
    for axis, spot in zip(axes, config["spot_files"], strict=True):
        for rep in config["representations"]:
            selected = [
                r
                for r in rows
                if r["spot_file"] == spot
                and r["representation"] == rep
                and r["readout"] == "linear"
            ]
            x = [r["work_checkpoint"] for r in selected]
            axis.plot(x, [100 * r["median"] for r in selected], marker="o", label=rep)
            axis.fill_between(
                x,
                [100 * r["minimum"] for r in selected],
                [100 * r["maximum"] for r in selected],
                alpha=0.12,
            )
        axis.set_xscale("log")
        axis.set_yscale("symlog", linthresh=1e-6)
        axis.set_title(Path(spot).stem)
        axis.set_xlabel("Total node visits, including exact warm initialization")
        axis.set_ylabel("Exact exploitability (% initial pot)")
        axis.axhline(1, color="black", linestyle=":", label="median limit (1%)")
        axis.grid(alpha=0.2)
    axes[1].legend(fontsize=7)
    fig.suptitle(
        "Fixed-work B4; linear-average median and three-seed range; known games"
    )
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)


def tables(
    folder: Path,
    rows: list[dict[str, Any]],
    summary: dict[str, Any],
    config: dict[str, Any],
) -> list[Path]:
    """Full numeric readouts plus a short primary-final table; preserve every seed."""
    fields = (
        *inputs.IDENTITY,
        "total_node_work",
        "iteration",
        "exploitability_pot",
        "value_player_zero_chips",
        "best_response_zero_chips",
        "best_response_one_chips",
        "coverage",
    )
    numeric = folder / "all-readouts.csv"
    paired = folder / "paired-final-linear.csv"
    markdown = folder / "tables.md"
    for path in (numeric, paired, markdown):
        if path.exists() or path.is_symlink():
            raise FileExistsError("retain previous report tables")
    with numeric.open("x", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows({k: row[k] for k in fields} for row in rows)
    differences = summary["final_linear_paired"]
    with paired.open("x", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(differences[0]))
        writer.writeheader()
        writer.writerows(differences)
    lines = [
        "# Fixed-work compact sampled comparison",
        "",
        "Known restricted games; final LINEAR averages. "
        "Lower exploitability is better.",
        "Three fixed seeds; ranges are descriptive, not confidence intervals.",
        "",
        "| Game | Representation | Median % pot | Worst % pot | "
        "All three seeds % pot |",
        "|---|---|---:|---:|---|",
    ]
    final = config["sampled"]["node_work_checkpoints"][-1]
    for row in summary["curves"]:
        if row["readout"] == "linear" and row["work_checkpoint"] == final:
            seeds = ", ".join(f"{100 * v:.9g}" for v in row["values"])
            lines.append(
                f"| {Path(row['spot_file']).stem} | {row['representation']} | "
                f"{100 * row['median']:.9g} | {100 * row['maximum']:.9g} | {seeds} |"
            )
    lines.extend(
        [
            "",
            "Exact AND candidate must meet median <=1% and worst <=2.5% in BOTH games.",
            "Other readouts cannot replace this declared primary.",
            "All324 readouts and30 signed paired baseline effects "
            "are in the CSV files.",
            "Negative candidate-minus-baseline favors candidate; "
            "every seed is retained.",
            "Whole average coverage includes exact warm mass; "
            "see result.json support rows",
            "for post-warm/all/river support. No default/fresh/global strength claim.",
            "",
        ]
    )
    markdown.write_text("\n".join(lines))
    return [numeric, paired, markdown]


def run(
    root: Path, own_path: Path, native_path: Path, output: Path, started: float
) -> dict[str, Any]:
    if output.exists():
        raise FileExistsError("retain previous result")
    saved: dict[str, Any] = dict(
        format="compact-sampled-result-v1",
        status="running",
        failure=None,
        source=inputs.source(root),
        runtime=runtime(),
        actual_admission=False,
        fresh_global_admission=False,
        new_agent_default=False,
    )
    try:
        own.replay(root, own_path)
        original = json.loads(own_path.read_text())
        if original["scope"] != "real":
            raise ValueError(
                "tiny/cost evidence cannot establish sampled poker accuracy"
            )
        require_admission(root, root / inputs.FOLDER / "admission.json")
        files.published(root, own_path)
        files.published(root, native_path)
        audit = checked_native(root, native_path, own_path, original, "audit")
        config = contract(root)
        previous = verify(root)
        assessment = assess_sampled(
            original["rows"],
            audit["comparisons"],
            previous["assessment"],
            config,
            elapsed_seconds=measurement(own_path, "study")["seconds"],
            audit_seconds=measurement(native_path, "audit")["seconds"],
        )
        summary = summaries(original["rows"], config)
        figure = output.with_name("learning.png")
        if figure.exists():
            raise FileExistsError("retain existing result plot")
        plot(summary["curves"], figure, config)
        outputs = tables(output.parent, original["rows"], summary, config)
        superiority = {
            r["baseline"]: assessment["thresholds_passed"]
            and r["both_games_paired_median_better"]
            for r in summary["baseline_specific_superiority"]
            if "both_games_paired_median_better" in r
        }
        saved.update(
            inputs=[bound(root, own_path), bound(root, native_path)],
            assessment=assessment,
            summary=summary,
            sampled_known_game_gates_passed=assessment["thresholds_passed"],
            actual_admission=assessment["thresholds_passed"],
            plot=bound(root, figure),
            tables=[bound(root, path) for path in outputs],
            baseline_specific_superiority_admitted=superiority,
            dominates_all_five_baselines=len(superiority) == 5
            and all(superiority.values()),
            storage=dict(
                partitions=original["partitions"],
                parent_lifetime_peak_rss_bytes=original["peak_process_rss_bytes"],
                workers=original["worker_receipts"],
                limitation=(
                    "Row counts/key bytes/lifetime RSS are distinct measurements"
                ),
            ),
            support_rows=[
                {
                    k: v
                    for k, v in r.items()
                    if "coverage" in k
                    or "rows" in k
                    or k in (*inputs.IDENTITY, "support_basis", "support")
                }
                for r in original["rows"]
            ],
            limitations=[
                "Two development range-restricted games; "
                "not fresh/global Hold'em strength.",
                "Three dependent fixed-seed summaries are not confidence intervals.",
                "Native scalar audit shares exported own engine mechanics.",
                "Whole average coverage includes exact warm mass; "
                "post-warm support is separate.",
                "State replay checks algebra/receipts, "
                "not every historical random draw.",
                "Fewer information rows do not establish lower whole-process memory.",
            ],
        )
        inputs.check_source(root, saved["source"])
        if time.perf_counter() - started >= 900:
            raise TimeoutError("complete sampled report cap")
        saved["status"] = "completed"
    except (Exception, KeyboardInterrupt) as error:
        saved.update(
            status="incomplete",
            actual_admission=False,
            failure=dict(type=type(error).__name__, reason=str(error)),
        )
    finally:
        saved["seconds"] = time.perf_counter() - started
        files.atomic(output, saved)
    return saved
