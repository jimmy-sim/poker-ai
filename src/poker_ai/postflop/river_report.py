"""Replay own policies, check the recorded audit, and render all river-study cells."""

import csv
import json
import math
import time
from pathlib import Path
from typing import Any

import numpy as np

from poker_ai.postflop.game import load_spot
from poker_ai.postflop.matrix import MatrixTree
from poker_ai.postflop.river_artifacts import IDENTITY, checked_artifacts
from poker_ai.postflop.river_study import digest
from poker_ai.postflop.tree import SpotTree
from poker_ai.toy.analysis import evaluate
from poker_ai.validation.five_card import source_provenance


def checked_audit(
    path: Path, audit_path: Path, report: dict[str, Any]
) -> dict[str, Any]:
    audit: dict[str, Any] = json.loads(audit_path.read_text())
    own = {tuple(r[k] for k in IDENTITY): r for r in report["rows"]}
    native = {tuple(r[k] for k in IDENTITY): r for r in audit["comparisons"]}
    tolerance = report["config"]["independent_tolerance_chips"]
    if (
        audit["status"] != "passed"
        or audit["input_sha256"] != digest(path)
        or own.keys() != native.keys()
        or len(native) != len(audit["comparisons"])
        or audit["tolerance_chips"] != tolerance
    ):
        raise ArithmeticError("missing/duplicate/mismatched native audit")
    for key, row in native.items():
        errors = [
            row["value_error_chips"],
            row["exploitability_error_chips"],
            abs(own[key]["value_player_zero_chips"] - row["native_value_chips"]),
            abs(own[key]["exploitability_chips"] - row["native_exploitability_chips"]),
        ]
        if any(not math.isfinite(v) or not 0 <= v <= tolerance for v in errors):
            raise ArithmeticError("native comparison does not satisfy tolerance")
    return audit


def learning_summary(report: dict[str, Any]) -> list[dict[str, Any]]:
    rows, config = report["rows"], report["config"]
    result = []
    for filename in config["spot_files"]:
        for threshold in config["total_node_thresholds"]:
            for method in config["variants"]:
                selected = [
                    r
                    for r in rows
                    if r["spot_file"] == filename
                    and r["method"] == method
                    and r["node_threshold"] == threshold
                ]
                if sorted(r["seed"] for r in selected) != sorted(
                    config["training_seeds"]
                ):
                    raise ArithmeticError("missing or duplicate comparison seeds")
                epsilon = [r["exploitability_pot_fraction"] for r in selected]
                result.append(
                    {
                        "spot": selected[0]["spot"],
                        "variant": method,
                        "node_threshold": threshold,
                        "median_epsilon_pot": float(np.median(epsilon)),
                        "min_epsilon_pot": min(epsilon),
                        "max_epsilon_pot": max(epsilon),
                        "median_seconds": float(
                            np.median([r["seconds"] for r in selected])
                        ),
                        "min_iterations": min(r["iteration"] for r in selected),
                        "max_iterations": max(r["iteration"] for r in selected),
                        "maximum_overshoot": max(r["overshoot"] for r in selected),
                        "minimum_average_coverage": min(
                            r["uniform_reach_average_row_coverage"] for r in selected
                        ),
                        "minimum_subsequent_coverage": min(
                            r["uniform_reach_subsequently_sampled_coverage"]
                            for r in selected
                        ),
                        "maximum_initial_only_rows": max(
                            r["initial_only_information_sets"] for r in selected
                        ),
                    }
                )
    return result


def panel_summary(report: dict[str, Any]) -> list[dict[str, Any]]:
    result = []
    panel = report["frozen_panel"]
    groups = sorted({(r["spot"], r["policy"], r["target"]) for r in panel})
    metrics = (
        "regret_mse_all",
        "regret_mse_turn",
        "average_mse_all",
        "mean_node_visits",
    )
    for spot, policy, target in groups:
        means = {}
        for method in report["config"]["variants"]:
            selected = [
                r
                for r in panel
                if (r["spot"], r["policy"], r["target"], r["variant"])
                == (spot, policy, target, method)
            ]
            means[method] = {
                m: float(np.mean([r[m] for r in selected])) for m in metrics
            }
        baseline, candidate = means["external"], means["river_integrated"]

        def ratio(
            metric: str,
            candidate: dict[str, float] = candidate,
            baseline: dict[str, float] = baseline,
        ) -> float | None:
            return (
                candidate[metric] / baseline[metric] if baseline[metric] > 0 else None
            )

        cost = ratio("mean_node_visits")
        row: dict[str, Any] = {
            "spot": spot,
            "policy": policy,
            "target": target,
            "external": baseline,
            "river_integrated": candidate,
            "visit_ratio": cost,
        }
        for m in metrics[:3]:
            error = ratio(m)
            row[m + "_ratio"] = error
            row[m + "_cost_ratio"] = (
                error * cost if error is not None and cost is not None else None
            )
        result.append(row)
    return result


def render(root: Path, path: Path, audit_path: Path, output: Path) -> dict[str, Any]:
    started = time.perf_counter()
    report, policies = checked_artifacts(path)
    audit = checked_audit(path, audit_path, report)
    if report["config"] != json.loads(
        (root / "configs/river-integration-study.json").read_text()
    ):
        raise ArithmeticError("committed prospective config differs from experiment")
    maximum = 0.0
    for filename, expected in report["spot_sha256"].items():
        if digest(root / filename) != expected:
            raise ArithmeticError("spot changed before replay")
        tree = MatrixTree.build(SpotTree.build(load_spot(root / filename)))
        for snapshot in policies:
            if snapshot["spot_file"] != filename:
                continue
            row = next(
                r for r in report["rows"] if all(r[k] == snapshot[k] for k in IDENTITY)
            )
            policy = tree.dense_exact(tuple(tuple(p) for p in snapshot["policy"]))
            metrics = evaluate(tree, policy)
            maximum = max(
                maximum,
                abs(metrics.exploitability - row["exploitability_chips"]),
                abs(metrics.value_player_zero - row["value_player_zero_chips"]),
            )
    if maximum > report["config"]["independent_tolerance_chips"]:
        raise ArithmeticError("frozen policy own-metric replay failed")
    learning, panels = learning_summary(report), panel_summary(report)
    output.mkdir(parents=True, exist_ok=True)
    summary = {
        "status": "passed",
        "candidate_passed": report["acceptance"]["candidate_passed"],
        "learning": learning,
        "frozen_panel": panels,
        "acceptance": report["acceptance"],
        "study_seconds": report["seconds"],
        "native_audit_seconds": audit["seconds"],
        "native_policies": len(audit["comparisons"]),
        "maximum_own_replay_error_chips": maximum,
        "maximum_native_error_chips": max(
            max(r["value_error_chips"], r["exploitability_error_chips"])
            for r in audit["comparisons"]
        ),
        "input_sha256": digest(path),
        "audit_sha256": digest(audit_path),
        "limitations": "known development games, three seeds; min-max "
        "bands are not confidence intervals; no global strength/fresh hold-out claim",
    }
    (output / "summary.json").write_text(
        json.dumps(summary, sort_keys=True, indent=2, allow_nan=False) + "\n"
    )
    with (output / "learning.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(learning[0]))
        writer.writeheader()
        writer.writerows(learning)
    lines = [
        "# Fixed-work river results",
        "",
        "Known development games. Lower exploitability is better. Ranges "
        "span three seeds, not confidence intervals.",
        "",
        "| Spot | Work threshold | Variant | Median epsilon/pot | Min–max "
        "| Iterations | Median seconds | Initial-only rows (max) |",
        "| --- | ---: | --- | ---: | --- | --- | ---: | ---: |",
    ]
    for r in learning:
        lines.append(
            f"| {r['spot']} | {r['node_threshold']:,} | {r['variant']} | "
            f"{r['median_epsilon_pot']:.6g} | "
            f"{r['min_epsilon_pot']:.6g}–{r['max_epsilon_pot']:.6g} | "
            f"{r['min_iterations']:,}–{r['max_iterations']:,} | "
            f"{r['median_seconds']:.3f} | "
            f"{r['maximum_initial_only_rows']} |"
        )
    lines += [
        "",
        "## Frozen-policy ratios",
        "",
        "Integrated / ordinary: below 1 favors integration. Means pool "
        "the equal-sized seed batches before division. "
        "Zero denominators remain unavailable.",
        "",
        "| Spot | Policy | Target | Regret MSE | Visits | Regret MSE × "
        "visits | Turn regret MSE × visits | Average MSE × visits |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for r in panels:

        def fmt(v: Any) -> str:
            return "n/a" if v is None else f"{v:.4g}"

        lines.append(
            f"| {r['spot']} | {r['policy']} | {r['target']} | "
            + " | ".join(
                fmt(r[k])
                for k in (
                    "regret_mse_all_ratio",
                    "visit_ratio",
                    "regret_mse_all_cost_ratio",
                    "regret_mse_turn_cost_ratio",
                    "average_mse_all_cost_ratio",
                )
            )
            + " |"
        )
    lines += [
        "",
        f"Candidate development gate: **{report['acceptance']['candidate_passed']}**.",
        f"Study {report['seconds']:.3f}s; native audit {audit['seconds']:.3f}s; "
        f"{len(audit['comparisons'])} frozen policies checked.",
        "",
        "All per-seed, per-budget rows, coverage, overshoot and costs "
        "remain in study.json and learning.csv.",
    ]
    (output / "tables.md").write_text("\n".join(lines) + "\n")
    _plots(learning, panels, report, output)
    files = (
        "summary.json",
        "learning.csv",
        "tables.md",
        "learning-work.png",
        "learning-time.png",
        "frozen-cost.png",
    )
    manifest = {
        "artifacts_sha256": {p: digest(output / p) for p in files},
        "source": source_provenance(
            root,
            root / "configs/river-integration-study.json",
            entrypoints=("scripts/report_river_study.py",),
        ),
        "seconds": time.perf_counter() - started,
        "input_sha256": digest(path),
        "audit_sha256": digest(audit_path),
    }
    (output / "render-manifest.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2) + "\n"
    )
    return summary


def _plots(
    learning: list[dict[str, Any]],
    panels: list[dict[str, Any]],
    report: dict[str, Any],
    output: Path,
) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"svg.hashsalt": "river-study-v1"})
    spots = list(dict.fromkeys(r["spot"] for r in learning))
    for xkey, filename, xlabel in (
        (
            "node_threshold",
            "learning-work.png",
            "Total node-work threshold (warm + recursive; overshoot in raw rows)",
        ),
        (
            "median_seconds",
            "learning-time.png",
            "Observed cumulative run seconds (includes earlier checkpoint/report work)",
        ),
    ):
        fig, axes = plt.subplots(2, 2, figsize=(13, 8), squeeze=False)
        for ax, spot in zip(axes.flat, spots, strict=True):
            for variant in report["config"]["variants"]:
                selected = [
                    r for r in learning if r["spot"] == spot and r["variant"] == variant
                ]
                x = [r[xkey] for r in selected]
                ax.plot(
                    x, [r["median_epsilon_pot"] for r in selected], "o-", label=variant
                )
                ax.fill_between(
                    x,
                    [r["min_epsilon_pot"] for r in selected],
                    [r["max_epsilon_pot"] for r in selected],
                    alpha=0.15,
                )
            ax.axhline(
                report["config"]["sampled_median_exploitability_pot_limit"],
                ls=":",
                color="black",
                label="declared median limit",
            )
            ax.set(
                xscale="log",
                yscale="log",
                title=spot,
                xlabel=xlabel,
                ylabel="Restricted exploitability / initial pot",
            )
            ax.grid(alpha=0.2)
            ax.legend(fontsize=8)
        fig.suptitle(
            "Known development games; median and min–max over 3 seeds (not "
            "confidence intervals)"
        )
        fig.tight_layout()
        fig.savefig(output / filename, dpi=150)
        plt.close(fig)
    fig, ax = plt.subplots(figsize=(13, 8))
    positions = np.arange(len(panels))
    for offset, metric, label in (
        (-0.18, "regret_mse_all_cost_ratio", "all-info regret"),
        (0.18, "regret_mse_turn_cost_ratio", "turn-only regret"),
    ):
        values = [r[metric] if r[metric] is not None else float("nan") for r in panels]
        ax.barh(positions + offset, values, height=0.35, label=label)
    labels = [
        f"{r['spot']} / "
        f"{'uniform' if r['policy'] == 'uniform' else 'own CFR+256'} / "
        f"target {r['target']}"
        for r in panels
    ]
    ax.set_yticks(positions, labels, fontsize=9)
    ax.axvline(1, color="black", ls=":")
    ax.set(
        xscale="log",
        xlabel=(
            "Integrated / ordinary MSE × mean node visits (below 1 favors integration)"
        ),
        title="Frozen policy, unweighted target passes; pooled equal seed batches",
    )
    ax.legend()
    ax.grid(axis="x", alpha=0.2)
    fig.tight_layout()
    fig.savefig(output / "frozen-cost.png", dpi=150)
    plt.close(fig)
