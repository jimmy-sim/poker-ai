"""Every fixed batch profile/seed and paired contrast, never a selected agent."""

import importlib
import itertools
import json
import math
from pathlib import Path
from typing import Any

from poker_ai.postflop.learning_report import write_csv
from poker_ai.postflop.river_study import digest

METRICS = (
    "exact_exploitability",
    "within_partition_gain",
    "extra_information_gap",
    "river_only_gain_exact_prefix",
    "value_player_zero",
)
GROUP = (
    "spot_file",
    "representation",
    "regret_rule",
    "average_weight",
    "batch_size",
    "work_label",
)
FIGURES = tuple(
    kind + "-" + rep + ".png"
    for kind in ("curves", "final-components")
    for rep in ("exact", "texture_range_q8_b8")
)


def numeric_rows(saved: dict[str, Any], pot: dict[str, float]) -> list[dict[str, Any]]:
    rows = []
    for row in saved["rows"]:
        record = dict(
            **row["case"],
            profile_id=row["id"],
            origin=row["origin"],
            batch_size=row["batch_size"],
            work_label=row["work_label"],
            actual_work=row["total_work"],
            overshoot=row["overshoot"],
            iteration=row["iteration"],
            initialization_visits=row["initialization_visits"],
            sampled_traversals=row["sampled_traversals"],
            policy_sha256=row["receipt"]["policy_sha256"],
        )
        for metric in METRICS:
            value = row["metrics"][metric + "_chips"]
            record[metric + "_chips"] = value
            record[metric + "_pct_initial_pot"] = (
                100 * value / pot[row["case"]["spot_file"]]
            )
        for stage, region, measure in itertools.product(
            ("whole", "post_warm"),
            ("all", "river"),
            ("rows", "positive_rows", "row_fraction", "uniform_reach_fraction"),
        ):
            record[f"{stage}_{region}_{measure}"] = (
                row["coverage"][stage][region][measure] if row["coverage"] else None
            )
        for key in ("mean_row_l1", "maximum_row_l1", "uniform_reach_weighted_l1"):
            record["current_" + key] = (
                row["current_movement"][key] if row["current_movement"] else None
            )
        rows.append(record)
    return rows


def means(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        key = json.dumps({k: row[k] for k in GROUP}, sort_keys=True)
        buckets.setdefault(key, []).append(row)
    result = []
    for key, cell in sorted(buckets.items()):
        base = json.loads(key)
        expected = 1 if base["batch_size"] is None else 3
        if len(cell) != expected:
            raise ArithmeticError(
                "batch means require all declared seeds/one full control"
            )
        record = dict(
            **base,
            replicates=len(cell),
            dependence="single reused full control"
            if expected == 1
            else "three fixed seeds; average books share learning paths",
        )
        for metric in METRICS:
            for unit in ("chips", "pct_initial_pot"):
                name = metric + "_" + unit
                record[name] = math.fsum(r[name] for r in cell) / len(cell)
        for name in (
            "actual_work",
            "iteration",
            "sampled_traversals",
            "post_warm_river_uniform_reach_fraction",
            "post_warm_river_row_fraction",
        ):
            values = [r[name] for r in cell]
            record[name] = (
                None
                if any(v is None for v in values)
                else math.fsum(values) / len(cell)
            )
        result.append(record)
    return result


def contrasts(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    fields = (
        "spot_file",
        "representation",
        "regret_rule",
        "average_weight",
        "seed",
        "work_label",
    )
    base = {tuple(r[k] for k in fields): r for r in rows if r["batch_size"] == 1}
    result = []
    for row in rows:
        if row["batch_size"] not in (4, 16):
            continue
        peer = base[tuple(row[k] for k in fields)]
        result.append(
            dict(
                **{k: row[k] for k in fields},
                batch_size=row["batch_size"],
                iteration_ratio_vs_B1=row["iteration"] / peer["iteration"],
                actual_work_difference_vs_B1=row["actual_work"] - peer["actual_work"],
                **{
                    metric + "_delta_pct_initial_pot": row[metric + "_pct_initial_pot"]
                    - peer[metric + "_pct_initial_pot"]
                    for metric in METRICS
                },
            )
        )
    return result


def figures(
    output: Path,
    rows: list[dict[str, Any]],
    averaged: list[dict[str, Any]],
    config: dict[str, Any],
) -> None:
    plt = importlib.import_module("matplotlib.pyplot")
    scope = (
        "SOFTWARE FIXTURE, NOT POKER RESULTS; "
        if config["status"].startswith("EXPLICIT")
        else ""
    )
    modes = list(itertools.product(config["regret_rules"], config["average_weights"]))
    for rep in config["representations"]:
        fig, axes = plt.subplots(
            2, 4, figsize=(18, 8), squeeze=False, layout="constrained"
        )
        for gi, game in enumerate(config["spot_files"]):
            for mi, (clip, weight) in enumerate(modes):
                ax = axes[gi, mi]
                chosen = [
                    r
                    for r in averaged
                    if r["spot_file"] == game
                    and r["representation"] == rep
                    and r["regret_rule"] == clip
                    and r["average_weight"] == weight
                ]
                for batch, color in ((None, "0.4"), (1, "C0"), (4, "C1"), (16, "C2")):
                    cell = sorted(
                        [r for r in chosen if r["batch_size"] == batch],
                        key=lambda r: r["work_label"],
                    )
                    ax.plot(
                        [r["work_label"] for r in cell],
                        [r["exact_exploitability_pct_initial_pot"] for r in cell],
                        marker="o",
                        color=color,
                        label="full (reused)" if batch is None else f"B{batch} mean",
                    )
                    for raw in rows:
                        if (
                            all(
                                raw[k] == cell[0][k]
                                for k in (
                                    "spot_file",
                                    "representation",
                                    "regret_rule",
                                    "average_weight",
                                    "batch_size",
                                )
                            )
                            and batch is not None
                        ):
                            ax.scatter(
                                raw["work_label"],
                                raw["exact_exploitability_pct_initial_pot"],
                                s=12,
                                color=color,
                                alpha=0.4,
                            )
                ax.set_xscale("log")
                ax.grid(alpha=0.25)
                ax.set_title(f"{Path(game).stem}\n{clip}/{weight}")
                ax.set_xlabel("Charged node-work label")
                if mi == 0:
                    ax.set_ylabel("Exact exploitability (% initial pot)")
                if gi == 0 and mi == 0:
                    ax.legend(fontsize=8)
        fig.suptitle(
            f"{scope}{rep}: fixed known games; all seed points and means; "
            "no global strength claim"
        )
        fig.savefig(output / f"curves-{rep}.png", dpi=140)
        plt.close(fig)
        fig, axes = plt.subplots(
            2, 4, figsize=(18, 8), squeeze=False, layout="constrained"
        )
        for gi, game in enumerate(config["spot_files"]):
            for mi, (clip, weight) in enumerate(modes):
                ax = axes[gi, mi]
                cell = [
                    next(
                        r
                        for r in averaged
                        if r["spot_file"] == game
                        and r["representation"] == rep
                        and r["regret_rule"] == clip
                        and r["average_weight"] == weight
                        and r["batch_size"] == b
                        and r["work_label"] == config["work_labels"][-1]
                    )
                    for b in (None, 1, 4, 16)
                ]
                within = [r["within_partition_gain_pct_initial_pot"] for r in cell]
                extra = [r["extra_information_gap_pct_initial_pot"] for r in cell]
                ax.bar(range(4), within, label="within partition")
                ax.bar(range(4), extra, bottom=within, label="extra exact information")
                ax.set_xticks(range(4), ["full", "B1", "B4", "B16"])
                ax.set_title(f"{Path(game).stem}\n{clip}/{weight}")
                ax.grid(axis="y", alpha=0.25)
                if mi == 0:
                    ax.set_ylabel("Exploitability (% initial pot)")
                if gi == 0 and mi == 0:
                    ax.legend(fontsize=8)
        fig.suptitle(
            f"{scope}{rep}: final {config['work_labels'][-1]} work; "
            "bars sum to exact exploitability; fixed-seed means"
        )
        fig.savefig(output / f"final-components-{rep}.png", dpi=140)
        plt.close(fig)


def write_report(
    root: Path, saved: dict[str, Any], output: Path, *, plots: bool = True
) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    pot = {
        p: float(json.loads((root / p).read_text())["pot"])
        for p in saved["config"]["spot_files"]
    }
    rows = numeric_rows(saved, pot)
    averaged = means(rows)
    paired = contrasts(rows)
    if (len(rows), len(averaged), len(paired)) != (480, 192, 288):
        raise ArithmeticError("batch report grid incomplete")
    for name, values in (
        ("profiles.csv", rows),
        ("means.csv", averaged),
        ("paired-seeds.csv", paired),
    ):
        write_csv(output / name, values)
    lines = [
        "# Fixed-work frozen-pass batches",
        "",
        saved["config"]["status"],
        "",
        "Known games only. All seeds retained; average books share paths. "
        "Full controls are reused once.",
        "Differences combine conditional-variance, update-count "
        "and iteration-weight effects.",
        "No selected/default/fresh/global admission. Values are % initial pot; "
        "zero is not a universal guarantee.",
        "",
        "| Game | Encoding | Regret/average | Method | Total | Within | "
        "Extra | River |",
        "|---|---|---|---|---:|---:|---:|---:|",
    ]
    for r in averaged:
        if r["work_label"] != saved["config"]["work_labels"][-1]:
            continue
        method = "full (reused)" if r["batch_size"] is None else f"B{r['batch_size']}"
        lines.append(
            f"| {Path(r['spot_file']).stem} | {r['representation']} | "
            f"{r['regret_rule']}/{r['average_weight']} | {method} | "
            + " | ".join(f"{r[m + '_pct_initial_pot']:.9f}" for m in METRICS[:4])
            + " |"
        )
    (output / "tables.md").write_text("\n".join(lines) + "\n")
    if plots:
        figures(output, rows, averaged, saved["config"])
    names = ("profiles.csv", "means.csv", "paired-seeds.csv", "tables.md")
    result = dict(
        profiles=480,
        unique_external_learning_paths=72,
        dependent_average_streams=144,
        reused_full_profiles=48,
        mean_rows=192,
        paired_seed_rows=288,
        numerical_sha256={n: digest(output / n) for n in names},
        figures=list(FIGURES) if plots else [],
        scope="known-game diagnosis, no selected/default/fresh/global admission",
    )
    (output / "summary.json").write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n"
    )
    return result
