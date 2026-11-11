"""Complete own comparison tables/figures; all seeds/readouts and scope retained."""

import csv
import importlib
import json
import math
import statistics
from pathlib import Path
from typing import Any

import numpy as np

from poker_ai.evaluation.opponent_learning_design import (
    ARMS,
    COST,
    READOUTS,
    REAL,
    SEEDS,
    Design,
)
from poker_ai.postflop.river_study import digest


def points(
    saved: dict[str, Any], design: Design, pots: tuple[float, float]
) -> list[dict[str, Any]]:
    design.require_rows("arms", saved["arms"])
    design.require_rows("profiles", saved["rows"])
    rows = {r["id"]: r for r in saved["rows"]}
    if any(type(p) not in (int, float) or not math.isfinite(p) or p <= 0 for p in pots):
        raise ValueError("report scales must be finite positive quantities")
    result = []
    for arm in saved["arms"]:
        row = rows[arm["id"]]
        game = arm["coordinate"] // 3
        scale = 100 / pots[game] if design.scope in (REAL, COST) else 1.0
        coverage = row["coverage"]
        record = dict(
            coordinate=arm["coordinate"],
            game=game,
            seed=arm["seed"],
            arm=arm["arm"],
            work_label=arm["work_label"],
            readout=arm["readout"],
            id=arm["id"],
            scope=design.scope,
            total_charged_work=arm["charged_work"]["total_work"],
            initialization_visits=arm["charged_work"]["initialization_visits"],
            component_iterations=arm["charged_work"]["component_iterations"],
            component_work=arm["charged_work"]["component_total_work"],
            units="percent initial pot"
            if design.scope in (REAL, COST)
            else "fictional payoff units",
            initial_pot_chips=pots[game] if design.scope in (REAL, COST) else None,
            policy_sha256=row["receipt"]["policy_sha256"],
            **{k.removesuffix("_chips"): v * scale for k, v in row["metrics"].items()},
        )
        for phase in ("whole", "post_warm"):
            for street in ("all", "river"):
                for measure in ("row_fraction", "uniform_reach_fraction"):
                    record[f"{phase}_{street}_{measure}"] = (
                        coverage[phase][street][measure]
                        if coverage is not None
                        else None
                    )
        result.append(record)
    if len(result) != 216:
        raise ArithmeticError("all216 logical own comparison points required")
    return result


def assessment(rows: list[dict[str, Any]], design: Design) -> dict[str, Any]:
    groups = []
    for game in (0, 1):
        primary = {
            arm: sorted(
                [
                    r
                    for r in rows
                    if r["game"] == game
                    and r["arm"] == arm
                    and r["readout"] == "linear_average"
                    and r["work_label"] == design.labels[-1]
                ],
                key=lambda r: r["seed"],
            )
            for arm in ARMS
        }
        if any(
            [r["seed"] for r in selected] != list(SEEDS)
            for selected in primary.values()
        ):
            raise ArithmeticError("all three fixed primary seeds required in each game")
        mixed = primary["mixed_pair"]
        values = [r["exact_exploitability"] for r in mixed]
        delta = [
            a["exact_exploitability"] - b["exact_exploitability"]
            for a, b in zip(primary["coarse_pair"], mixed, strict=True)
        ]
        practical = [
            a["exact_exploitability"] - b["exact_exploitability"]
            for a, b in zip(primary["coarse_self"], mixed, strict=True)
        ]
        coverage = [r["whole_all_uniform_reach_fraction"] for r in mixed]
        known = design.scope == REAL
        groups.append(
            dict(
                game=game,
                seeds=list(SEEDS),
                mixed_exact_exploitability=values,
                median=statistics.median(values),
                worst=max(values),
                paired_coarse_minus_mixed=delta,
                median_paired_improvement=statistics.median(delta),
                ordinary_coarse_minus_mixed=practical,
                whole_average_uniform_reach_coverage=coverage,
                post_warm_uniform_reach_coverage=[
                    r["post_warm_all_uniform_reach_fraction"] for r in mixed
                ],
                accuracy_limits_pass=(
                    statistics.median(values) <= 1.0 and max(values) <= 2.5
                )
                if known
                else None,
                paired_improvement_pass=statistics.median(delta) > 0 if known else None,
                historical_whole_average_coverage_pass=all(
                    v is not None and v >= 0.95 for v in coverage
                )
                if known
                else None,
            )
        )
    return dict(
        groups=groups,
        known_game_accuracy_and_improvement_only=design.scope == REAL,
        median_limit_pct_initial_pot=1.0,
        worst_limit_pct_initial_pot=2.5,
        minimum_whole_average_uniform_reach_coverage=0.95,
        independent_audit=(
            "reported separately; this own report cannot accept its numerical gate"
        ),
        recall_and_source_gates=(
            "required separately; not inferred from a strength curve"
        ),
        no_secondary_readout_rescue=True,
        new_agent_default=False,
        fresh_global_admission=False,
    )


def _csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="") as out:
        writer = csv.DictWriter(out, sorted(rows[0]), lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    k: json.dumps(v, sort_keys=True, allow_nan=False)
                    if isinstance(v, (list, dict))
                    else v
                    for k, v in row.items()
                }
            )


def write(
    folder: Path,
    saved: dict[str, Any],
    design: Design,
    pots: tuple[float, float],
    *,
    no_plots: bool = False,
) -> dict[str, str]:
    if folder.exists() or folder.is_symlink():
        raise FileExistsError("retain own comparison report")
    rows = points(saved, design, pots)
    fixed = []
    for row in saved["fixed_conditions"]:
        game = row["coordinate"] // 3
        scale = 100 / pots[game] if design.scope in (REAL, COST) else 1.0
        fixed.append(
            dict(
                condition_id=row["condition_id"],
                id=row["id"],
                game=game,
                seed=row["seed"],
                arm=row["arm"],
                readout=row["readout"],
                target=row["target"],
                opponent_id=row["opponent_id"],
                scope=design.scope,
                units=rows[0]["units"],
                target_ev=row["target_ev_chips"] * scale,
                fine_reply_value=row["fine_reply_value_chips"] * scale,
                fine_reply_gain=row["fine_reply_gain_chips"] * scale,
                candidate_policy_sha256=row["candidate_policy_sha256"],
                opponent_policy_sha256=row["opponent_policy_sha256"],
                own_reply_sha256=row["own_reply_sha256"],
            )
        )
    if len(fixed) != 1152 or len({r["condition_id"] for r in fixed}) != 1152:
        raise ArithmeticError("report requires every1152 fixed own target condition")
    folder.mkdir(parents=True)
    _csv(folder / "arm-points.csv", rows)
    _csv(folder / "fixed-conditions.csv", fixed)
    summary = dict(
        scope=design.scope,
        units=rows[0]["units"],
        primary=assessment(rows, design),
        arm_points=216,
        fixed_conditions=1152,
        unique_scored_profiles=432,
        all_seeds_and_readouts_retained=True,
        dependence=(
            "Three fixed seeds; reused prefixes and related readouts; "
            "no population confidence interval."
        ),
        reuse=(
            "Logical comparisons charge each component fully; "
            "actual prefix execution is counted once."
        )
        if design.scope != COST
        else (
            "Old OWN endpoints reused at nominal cost coordinates. "
            "Zero new training; mixed tables were never learned together."
        ),
        fixed_metric=(
            "Fine best-response gain against each frozen OWN opponent; "
            "not self exploitability or an external strategy comparison."
        ),
        poker_results=design.scope == REAL,
        new_agent_default=False,
        fresh_global_admission=False,
    )
    (folder / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    if not no_plots:
        plots(folder, rows, fixed, design)
    return {p.name: digest(p) for p in sorted(folder.iterdir())}


def plots(
    folder: Path,
    rows: list[dict[str, Any]],
    fixed: list[dict[str, Any]],
    design: Design,
) -> None:
    plt = importlib.import_module("matplotlib.pyplot")
    unit = rows[0]["units"]
    title = (
        "Known own games; no global admission"
        if design.scope == REAL
        else "Old OWN cost stand-ins; zero new learning; no strength admission"
        if design.scope == COST
        else "Fictional software fixtures; repeated labels; no poker results"
    )
    names = dict(
        coarse_self="ordinary coarse",
        coarse_pair="paired coarse",
        mixed_pair="fine opponent treatment",
        fine_self="ordinary fine",
    )
    colors = dict(
        zip(ARMS, ("tab:blue", "tab:orange", "tab:green", "tab:purple"), strict=True)
    )
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), squeeze=False)
    for game, ax in enumerate(axes[0]):
        for arm in ARMS:
            means = []
            for label in design.labels:
                selected = [
                    r
                    for r in rows
                    if r["game"] == game
                    and r["arm"] == arm
                    and r["readout"] == "linear_average"
                    and r["work_label"] == label
                ]
                ys = [r["exact_exploitability"] for r in selected]
                if sorted(r["seed"] for r in selected) != list(SEEDS):
                    raise ArithmeticError("plot omits a declared seed")
                means.append(math.fsum(ys) / 3)
                ax.scatter([label] * 3, ys, color=colors[arm], alpha=0.45, s=18)
            ax.plot(
                design.labels, means, color=colors[arm], marker="o", label=names[arm]
            )
        ax.set(
            title=f"Game {game}; linear average",
            xlabel="Logical node-work label",
            ylabel=f"Exact exploitability ({unit})",
            xscale="log",
        )
        ax.grid(alpha=0.2)
        ax.set_xticks(design.labels, [f"{v:,}" for v in design.labels])
        ax.minorticks_off()
        ax.legend(fontsize=8)
    fig.suptitle(title + "\nLines: means over3 fixed seeds; dots: individual seeds")
    fig.tight_layout()
    fig.savefig(folder / "learning.png", dpi=150)
    plt.close(fig)

    fig, axes = plt.subplots(2, 3, figsize=(15, 8), squeeze=False)
    for game in (0, 1):
        for column, readout in enumerate(READOUTS):
            ax = axes[game, column]
            for seed in SEEDS:
                delta = []
                for label in design.labels:
                    by_arm = {
                        r["arm"]: r
                        for r in rows
                        if r["game"] == game
                        and r["seed"] == seed
                        and r["readout"] == readout
                        and r["work_label"] == label
                    }
                    delta.append(
                        by_arm["coarse_pair"]["exact_exploitability"]
                        - by_arm["mixed_pair"]["exact_exploitability"]
                    )
                ax.plot(design.labels, delta, marker="o", label=str(seed))
            ax.axhline(0, color="black", lw=0.8)
            ax.set(
                title=f"Game {game}; {readout}",
                xscale="log",
                xlabel="Logical node-work label",
                ylabel=f"Paired coarse minus treatment\n({unit})",
            )
            ax.set_xticks(design.labels, [f"{v:,}" for v in design.labels])
            ax.minorticks_off()
            ax.grid(alpha=0.2)
            ax.legend(fontsize=7)
    fig.suptitle(title + "\nPositive gaps favor treatment; all fixed seeds/readouts")
    fig.tight_layout()
    fig.savefig(folder / "paired-gaps.png", dpi=150)
    plt.close(fig)

    panels = []
    for game in (0, 1):
        opponents = sorted({r["opponent_id"] for r in fixed if r["game"] == game})
        if len(opponents) != 8:
            raise ArithmeticError("fixed heatmap requires all eight own opponents")
        for readout in READOUTS:
            values = np.zeros((8, 4))
            for i, opponent in enumerate(opponents):
                for j, arm in enumerate(ARMS):
                    chosen = [
                        r
                        for r in fixed
                        if r["game"] == game
                        and r["opponent_id"] == opponent
                        and r["readout"] == readout
                        and r["arm"] == arm
                    ]
                    if {(r["seed"], r["target"]) for r in chosen} != {
                        (s, t) for s in SEEDS for t in (0, 1)
                    } or len(chosen) != 6:
                        raise ArithmeticError(
                            "fixed heatmap omits a seed or target seat"
                        )
                    values[i, j] = math.fsum(r["fine_reply_gain"] for r in chosen) / 6
            panels.append((game, readout, opponents, values))
    lo = min(float(p[3].min()) for p in panels)
    hi = max(float(p[3].max()) for p in panels)
    fig, axes = plt.subplots(2, 3, figsize=(16, 10), squeeze=False)
    for game, readout, opponents, values in panels:
        ax = axes[game, READOUTS.index(readout)]
        im = ax.imshow(values, aspect="auto", vmin=lo, vmax=hi, cmap="viridis")
        labels = []
        for opponent in opponents:
            if opponent.startswith("FICTIONAL_"):
                labels.append("scripted " + opponent.rsplit("_", 1)[-1])
            else:
                case = json.loads(opponent)
                labels.append(
                    ("fine" if case["representation"] == "exact" else "coarse")
                    + " "
                    + case["regret_rule"]
                    + " "
                    + case["average_weight"]
                )
        ax.set(
            title=f"Game {game}; {readout}",
            yticks=range(8),
            yticklabels=labels,
            xticks=range(4),
            xticklabels=[names[a] for a in ARMS],
        )
        ax.tick_params(axis="x", labelrotation=25, labelsize=8)
        ax.tick_params(axis="y", labelsize=8)
        for i in range(8):
            for j in range(4):
                ax.text(
                    j,
                    i,
                    f"{values[i, j]:.3g}",
                    ha="center",
                    va="center",
                    fontsize=7,
                    color="white" if values[i, j] < (lo + hi) / 2 else "black",
                )
    fig.suptitle(
        title + "\nFixed own opponents; means over 3 seeds and 2 target seats; "
        "individual conditions in CSV"
        "\nFine replies can use extra information; this gap is not self exploitability."
    )
    fig.subplots_adjust(
        left=0.16, right=0.84, bottom=0.13, top=0.87, wspace=0.55, hspace=0.55
    )
    color_axis = fig.add_axes([0.9, 0.23, 0.015, 0.54])
    fig.colorbar(im, cax=color_axis, label=f"Gap to own fine best response ({unit})")
    fig.savefig(folder / "fixed-gain.png", dpi=150)
    plt.close(fig)
