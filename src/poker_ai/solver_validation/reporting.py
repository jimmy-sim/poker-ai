"""Reproduce compact tables and figures from recorded comparison metrics."""

import importlib
import os
from pathlib import Path
from typing import Any

import numpy as np


def primary_summary(report: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    config = report["config"]
    for spot in report["spots"]:
        runs = [
            r
            for r in spot["comparisons"]
            if r["buckets"] == config["primary_buckets"]
            and r["iteration"] == config["primary_iteration"]
        ]
        row: dict[str, Any] = {
            "spot": spot["name"],
            "reference_iterations": spot["reference_iterations"],
            "reference_exploitability_pot_fraction": spot["reference_exploitability"]
            / spot["pot"],
        }
        fields = {
            "action_gap": "action_gap",
            "hero_ev_gap_vs_reference_opponent": "ev_gap_vs_reference_chips",
            "hero_ev_gap_vs_own_opponent": "ev_gap_vs_own_chips",
            "exploitability": "own_exploitability_chips",
        }
        for source, destination in fields.items():
            values = [r[source] for r in runs]
            row[destination] = float(np.mean(values))
            row[destination + "_min"] = min(values)
            row[destination + "_max"] = max(values)
        for street in ("2", "3"):
            row["action_gap_" + ("turn" if street == "2" else "river")] = float(
                np.mean([r["action_gap_per_street"][street] for r in runs])
            )
        row["trained_policy_reach_fraction"] = float(
            np.mean(
                [
                    r["status_diagnosis"].get("matched", {}).get("reach_fraction", 0)
                    for r in runs
                ]
            )
        )
        row["own_exploitability_pot_fraction"] = (
            row["own_exploitability_chips"] / spot["pot"]
        )
        row["ev_gap_vs_reference_pot_fraction"] = (
            row["ev_gap_vs_reference_chips"] / spot["pot"]
        )
        rows.append(row)
    return rows


def markdown_table(rows: list[dict[str, Any]]) -> str:
    lines = [
        "| Turn subgame | Action gap (pp) | Turn / river (pp) | "
        "Own exploit. / pot | Hero EV gap vs ref. / pot | Trained-policy reach |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for r in rows:
        lines.append(
            f"| {r['spot']} | {100 * r['action_gap']:.2f} | "
            f"{100 * r['action_gap_turn']:.2f} / {100 * r['action_gap_river']:.2f} | "
            f"{r['own_exploitability_pot_fraction']:.4f} | "
            f"{r['ev_gap_vs_reference_pot_fraction']:+.4f} | "
            f"{100 * r['trained_policy_reach_fraction']:.1f}% |"
        )
    return "\n".join(lines) + "\n"


def plot_strategy(
    heatmap: dict[str, Any], output: Path, basename: str = "strategy-heatmap"
) -> list[Path]:
    os.environ.setdefault("MPLCONFIGDIR", str(output / "runs/mpl-cache"))
    mpl = importlib.import_module("matplotlib")
    mpl.use("Agg")
    mpl.rcParams["svg.hashsalt"] = "poker-ai-solver-validation"
    plt = importlib.import_module("matplotlib.pyplot")
    paths = []
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8), layout="constrained")
    image = None
    for axis, name in zip(axes, ("reference", "own"), strict=True):
        matrix = np.array(heatmap[name])
        image = axis.imshow(matrix, vmin=0, vmax=1, cmap="Blues", aspect="auto")
        axis.set_xticks(range(len(heatmap["actions"])), heatmap["actions"], rotation=20)
        axis.set_yticks(range(len(heatmap["classes"])), heatmap["classes"])
        axis.set_title(
            "OpenSpiel CFR+" if name == "reference" else "Own agent: mean of 3 seeds"
        )
        for i in range(matrix.shape[0]):
            for j in range(matrix.shape[1]):
                axis.text(
                    j,
                    i,
                    f"{100 * matrix[i, j]:.1f}%",
                    ha="center",
                    va="center",
                    color="white" if matrix[i, j] > 0.5 else "black",
                )
    assert image is not None
    fig.colorbar(image, ax=axes, label="Action probability", shrink=0.8)
    fig.suptitle(f"{heatmap['spot']}: root hero decision, two configured hand classes")
    for suffix in ("png", "svg"):
        path = output / f"{basename}.{suffix}"
        fig.savefig(path, dpi=160, metadata={"Date": None} if suffix == "svg" else None)
        paths.append(path)
    plt.close(fig)

    return paths


def plot(report: dict[str, Any], output: Path) -> list[Path]:
    paths = plot_strategy(report["heatmap"], output)
    plt = importlib.import_module("matplotlib.pyplot")
    config = report["config"]
    all_runs = [
        dict(r, pot=s["pot"], spot=s["name"])
        for s in report["spots"]
        for r in s["comparisons"]
    ]
    fig, axes = plt.subplots(2, 2, figsize=(11, 7), layout="constrained")
    for column, dimension in enumerate(("buckets", "iteration")):
        for row, metric in enumerate(("action_gap", "exploitability")):
            axis = axes[row, column]
            for name in [s["name"] for s in report["spots"]]:
                selected = [
                    r
                    for r in all_runs
                    if r["spot"] == name
                    and (
                        r["iteration"] == config["primary_iteration"]
                        if dimension == "buckets"
                        else r["buckets"] == config["primary_buckets"]
                    )
                ]
                x = sorted({r[dimension] for r in selected})
                means, low, high = [], [], []
                for value in x:
                    numbers = [
                        r[metric] * (100 if metric == "action_gap" else 1 / r["pot"])
                        for r in selected
                        if r[dimension] == value
                    ]
                    means.append(float(np.mean(numbers)))
                    low.append(min(numbers))
                    high.append(max(numbers))
                axis.plot(x, means, marker="o", label=name)
                axis.fill_between(x, low, high, alpha=0.12)
            axis.set_xlabel(
                "Buckets" if dimension == "buckets" else "Training iterations"
            )
            axis.set_ylabel(
                "Action gap (pp)"
                if metric == "action_gap"
                else "Restricted exploitability / root pot"
            )
            if dimension == "iteration":
                axis.set_xscale("log")
            axis.set_xticks(x, [str(value) for value in x])
            if row == 1:
                axis.set_yscale("log")
            axis.grid(alpha=0.2)
    axes[0, 0].legend(fontsize=7)
    fig.suptitle("Global self-play ablations: mean and min–max of 3 fixed seeds")
    for suffix in ("png", "svg"):
        path = output / f"ablation-gaps.{suffix}"
        fig.savefig(path, dpi=160, metadata={"Date": None} if suffix == "svg" else None)
        paths.append(path)
    plt.close(fig)
    return paths
