"""Replay and report the entire fresh cohort; failed performance gates stay failed."""

import csv
import importlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from poker_ai.postflop.fresh_cohort import verify_freeze
from poker_ai.postflop.fresh_learning import IDENTITY, checked_artifacts, filenames
from poker_ai.postflop.game import load_spot
from poker_ai.postflop.matrix import MatrixTree
from poker_ai.postflop.river_report import checked_audit, learning_summary
from poker_ai.postflop.river_study import digest
from poker_ai.postflop.tree import SpotTree
from poker_ai.toy.analysis import evaluate
from poker_ai.validation.five_card import source_provenance


def render(
    root: Path, config_path: Path, path: Path, audit_path: Path, output: Path
) -> dict[str, Any]:
    config, freeze = verify_freeze(root, config_path)
    report, snapshots = checked_artifacts(path)
    audit = checked_audit(path, audit_path, report)
    if (
        report["config"] != config
        or report["spot_sha256"] != freeze["spot_sha256"]
        or report["freeze_sha256"] != digest(root / config["freeze_file"])
        or audit["freeze_sha256"] != report["freeze_sha256"]
    ):
        raise ArithmeticError("frozen source/config/input identity changed")
    maximum = 0.0
    for filename in filenames(config):
        tree = MatrixTree.build(SpotTree.build(load_spot(root / filename)))
        for snapshot in snapshots:
            if snapshot["spot_file"] != filename:
                continue
            row = next(
                r for r in report["rows"] if all(r[k] == snapshot[k] for k in IDENTITY)
            )
            metrics = evaluate(
                tree, tree.dense_exact(tuple(tuple(p) for p in snapshot["policy"]))
            )
            maximum = max(
                maximum,
                abs(metrics.exploitability - row["exploitability_chips"]),
                abs(metrics.value_player_zero - row["value_player_zero_chips"]),
            )
    if maximum > config["independent_tolerance_chips"]:
        raise ArithmeticError("fresh frozen-policy own replay failed")
    # Reuse the tested summary arithmetic with a one-method view, without
    # changing the original frozen config or any experimental result.
    learning = learning_summary(
        {
            **report,
            "config": {
                **config,
                "variants": ["external"],
                "spot_files": filenames(config),
            },
        }
    )
    summary = {
        "audit_status": "passed",
        "fresh_gate_passed": report["acceptance"]["passed"],
        "acceptance": report["acceptance"],
        "learning": learning,
        "input_sha256": digest(path),
        "audit_sha256": digest(audit_path),
        "freeze_sha256": report["freeze_sha256"],
        "maximum_own_replay_error_chips": maximum,
        "maximum_native_error_chips": max(
            max(r["value_error_chips"], r["exploitability_error_chips"])
            for r in audit["comparisons"]
        ),
        "study_seconds": report["seconds"],
        "native_audit_seconds": audit["seconds"],
        "scope": (
            "fresh procedure validation with per-spot retraining; "
            "four structural strata, no global/zero-shot strength claim"
        ),
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    with (output / "learning.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(learning[0]))
        writer.writeheader()
        writer.writerows(learning)
    lines = [
        "# Fresh procedure validation",
        "",
        "Each case receives its own training. Lower epsilon/pot is better.",
        "",
        "| Case | Node threshold | Median epsilon/pot | Min–max | Iterations | "
        "Median seconds | Initial-only rows (max) | Subsequent coverage (min) |",
        "| --- | ---: | ---: | --- | --- | ---: | ---: | ---: |",
    ]
    for r in learning:
        lines.append(
            f"| {r['spot']} | {r['node_threshold']:,} | "
            f"{r['median_epsilon_pot']:.6g} | "
            f"{r['min_epsilon_pot']:.6g}–{r['max_epsilon_pot']:.6g} | "
            f"{r['min_iterations']:,}–{r['max_iterations']:,} | "
            f"{r['median_seconds']:.3f} | {r['maximum_initial_only_rows']} | "
            f"{r['minimum_subsequent_coverage']:.2%} |"
        )
    lines += [
        "",
        "## Final limits",
        "",
        "| Case | Full epsilon/pot | Sampled median | Sampled worst | "
        "Average coverage | Passed |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for r in report["acceptance"]["checks"]:
        lines.append(
            f"| {Path(r['spot_file']).stem} | {r['full_epsilon_pot']:.6g} | "
            f"{r['median_epsilon_pot']:.6g} | {r['max_epsilon_pot']:.6g} | "
            f"{r['minimum_average_coverage']:.2%} | {r['passed']} |"
        )
    lines += [
        "",
        f"Fresh procedure gate: **{report['acceptance']['passed']}**. "
        "No thresholds or cases were replaced.",
        "Average coverage includes initialization; see initial-only rows "
        "and subsequent coverage separately.",
        "Bands/ranges span three fixed seeds and are not confidence intervals. "
        "No global or zero-shot claim.",
    ]
    (output / "tables.md").write_text("\n".join(lines) + "\n")
    _plots(learning, config, output)
    files = (
        "summary.json",
        "learning.csv",
        "tables.md",
        "learning-work.png",
        "learning-time.png",
    )
    manifest = {
        "artifacts_sha256": {p: digest(output / p) for p in files},
        "input_sha256": digest(path),
        "audit_sha256": digest(audit_path),
        "freeze_sha256": report["freeze_sha256"],
        "source": source_provenance(
            root, config_path, entrypoints=("scripts/report_fresh_games.py",)
        ),
    }
    (output / "render-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    )
    return summary


def _plots(rows: list[dict[str, Any]], config: dict[str, Any], output: Path) -> None:
    matplotlib = importlib.import_module("matplotlib")
    matplotlib.use("Agg")
    plt = importlib.import_module("matplotlib.pyplot")
    names = list(dict.fromkeys(r["spot"] for r in rows))
    for xkey, file, label in (
        (
            "node_threshold",
            "learning-work.png",
            "Total-node threshold (warm + recursive work; overshoot retained)",
        ),
        (
            "median_seconds",
            "learning-time.png",
            "Observed cumulative run seconds including earlier checkpoint overhead",
        ),
    ):
        fig, axes = plt.subplots(2, 2, figsize=(13, 8))
        for ax, name in zip(axes.flat, names, strict=True):
            selected = [r for r in rows if r["spot"] == name]
            x = [r[xkey] for r in selected]
            ax.plot(
                x,
                np.maximum([r["median_epsilon_pot"] for r in selected], 1e-15),
                "o-",
                label="frozen ordinary procedure",
            )
            ax.fill_between(
                x,
                np.maximum([r["min_epsilon_pot"] for r in selected], 1e-15),
                np.maximum([r["max_epsilon_pot"] for r in selected], 1e-15),
                alpha=0.15,
            )
            ax.axhline(
                config["sampled_median_exploitability_pot_limit"],
                ls=":",
                color="black",
                label="declared median limit",
            )
            ax.set(
                xscale="log",
                yscale="log",
                title=name,
                xlabel=label,
                ylabel="Restricted exploitability / initial pot",
            )
            ax.grid(alpha=0.2)
            ax.legend(fontsize=8)
        fig.suptitle(
            "Fresh cases, separate per-case training; median and min–max over 3 seeds\n"
            "Independent vertical scales; log display floor 1e-15; "
            "ranges are not confidence intervals"
        )
        fig.tight_layout()
        fig.savefig(output / file, dpi=150)
        plt.close(fig)
