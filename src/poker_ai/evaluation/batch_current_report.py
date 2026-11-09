"""Every current/average point and fixed opponent; shared trajectories stay explicit."""

import importlib
import itertools
import json
import math
from pathlib import Path
from typing import Any

from poker_ai.evaluation import batch_current_inputs as inputs
from poker_ai.evaluation.batch_current_math import paired_fixed
from poker_ai.postflop.learning_report import write_csv
from poker_ai.postflop.river_study import digest

METRICS = (
    "value_player_zero",
    "exact_exploitability",
    "within_partition_gain",
    "extra_information_gap",
    "river_only_gain_exact_prefix",
)
GROUP = (
    "spot_file",
    "representation",
    "regret_rule",
    "batch_size",
    "readout",
    "work_label",
)
FIGURES = (
    "current-self-exact.png",
    "current-self-texture_range_q8_b8.png",
    "fixed-current-average.png",
)


def tables(
    saved: dict[str, Any], sources: inputs.Sources, pot: dict[str, float]
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    profiles = []
    self_pairs = []
    fixed = []
    fixed_pairs = []
    old = {
        (r["path_index"], r["case"]["average_weight"], r["work_label"]): r
        for r in sources.own["rows"]
        if r["path_index"] < 72
    }
    for row in [
        *saved["rows"],
        *(r for r in sources.own["rows"] if r["path_index"] < 72),
    ]:
        readout = (
            "current"
            if row.get("variant") == "current"
            else row["case"]["average_weight"] + "_average"
        )
        point = dict(
            id=row["id"],
            path_index=row["path_index"],
            **row["case"],
            batch_size=row["batch_size"],
            readout=readout,
            work_label=row["work_label"],
        )
        for m in METRICS:
            point[m + "_chips"] = row["metrics"][m + "_chips"]
            point[m + "_pct_initial_pot"] = (
                100 * point[m + "_chips"] / pot[row["case"]["spot_file"]]
            )
        profiles.append(point)
    for current in saved["rows"]:
        for weight in ("uniform", "linear"):
            average = old[current["path_index"], weight, current["work_label"]]
            point = dict(
                current_id=current["id"],
                average_id=average["id"],
                path_index=current["path_index"],
                **current["case"],
                batch_size=current["batch_size"],
                readout=weight + "_average",
                work_label=current["work_label"],
            )
            for m in METRICS:
                gap = (
                    current["metrics"][m + "_chips"] - average["metrics"][m + "_chips"]
                )
                point["current_minus_average_" + m + "_chips"] = gap
                point["current_minus_average_" + m + "_pct_initial_pot"] = (
                    100 * gap / pot[current["case"]["spot_file"]]
                )
            self_pairs.append(point)
    by = {
        (r["own_snapshot_id"], r["opponent_profile_id"], r["target"]): r
        for r in saved["fixed_matches"]
    }
    for row in saved["fixed_matches"]:
        opponent = json.loads(row["opponent_profile_id"])
        point = dict(
            **row["case"],
            path_index=row["path_index"],
            own_snapshot_id=row["own_snapshot_id"],
            readout=row["own_variant"],
            batch_size=row["batch_size"],
            work_label=row["work_label"],
            target=row["target"],
            opponent_profile_id=row["opponent_profile_id"],
            opponent_regret_rule=opponent["regret_rule"],
            opponent_average_weight=opponent["average_weight"],
        )
        for m in ("baseline_value", "restricted_reply_value", "gain"):
            point[m + "_chips"] = row[m + "_chips"]
            point[m + "_pct_initial_pot"] = (
                100 * row[m + "_chips"] / pot[row["case"]["spot_file"]]
            )
        fixed.append(point)
        if row["own_variant"] != "current":
            continue
        for weight in ("uniform", "linear"):
            average = old[row["path_index"], weight, row["work_label"]]
            peer = by[average["id"], row["opponent_profile_id"], row["target"]]
            gap = paired_fixed(row, peer)
            record = dict(
                point, readout=weight + "_average", average_id=average["id"], **gap
            )
            for k, v in gap.items():
                record[k.removesuffix("_chips") + "_pct_initial_pot"] = (
                    100 * v / pot[row["case"]["spot_file"]]
                )
            fixed_pairs.append(record)
    if tuple(map(len, (profiles, self_pairs, fixed, fixed_pairs))) != (
        648,
        432,
        1728,
        1152,
    ):
        raise ArithmeticError("saved-current report grid incomplete")
    return profiles, self_pairs, fixed, fixed_pairs


def means(
    rows: list[dict[str, Any]], fields: tuple[str, ...], metrics: list[str]
) -> list[dict[str, Any]]:
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for row in rows:
        groups.setdefault(tuple(row[k] for k in fields), []).append(row)
    return [
        dict(
            zip(fields, key, strict=True),
            observations=len(cell),
            **{m: math.fsum(r[m] for r in cell) / len(cell) for m in metrics},
        )
        for key, cell in sorted(groups.items())
    ]


def figures(
    output: Path,
    profiles: list[dict[str, Any]],
    fixed: list[dict[str, Any]],
    software: bool,
) -> None:
    plt = importlib.import_module("matplotlib.pyplot")
    colors = {1: "tab:blue", 4: "tab:orange", 16: "tab:green"}
    styles = {"current": "-", "uniform_average": ":", "linear_average": "--"}
    games = sorted({r["spot_file"] for r in profiles})
    prefix = "SOFTWARE FIXTURE, NOT POKER RESULTS; " if software else ""
    for rep in ("exact", "texture_range_q8_b8"):
        fig, axes = plt.subplots(2, 2, figsize=(16, 10), squeeze=False)
        for col, game in enumerate(games):
            for ri, clip in enumerate(("signed", "clipped")):
                ax = axes[ri, col]
                for batch, readout in itertools.product((1, 4, 16), styles):
                    rows = [
                        r
                        for r in profiles
                        if r["spot_file"] == game
                        and r["representation"] == rep
                        and r["regret_rule"] == clip
                        and r["batch_size"] == batch
                        and r["readout"] == readout
                    ]
                    group = means(
                        rows, ("work_label",), ["exact_exploitability_pct_initial_pot"]
                    )
                    ax.plot(
                        [r["work_label"] for r in group],
                        [r["exact_exploitability_pct_initial_pot"] for r in group],
                        marker="o",
                        color=colors[batch],
                        linestyle=styles[readout],
                        label=f"B{batch} {readout}",
                    )
                ax.set_xscale("log")
                ax.set_title(Path(game).stem + "; " + clip)
                ax.set_xlabel("Charged node-work checkpoint")
                ax.set_ylabel("Exact exploitability (% initial pot)")
                ax.grid(alpha=0.2)
        handles, labels = axes[0, 0].get_legend_handles_labels()
        fig.legend(handles, labels, loc="lower center", ncol=3, fontsize=8)
        fig.suptitle(
            prefix + rep + ": all seeds; current and averages share each learning path"
        )
        fig.tight_layout(rect=(0, 0.09, 1, 0.95))
        fig.savefig(output / ("current-self-" + rep + ".png"), dpi=160)
        plt.close(fig)
    fig, axes = plt.subplots(2, 2, figsize=(16, 10), squeeze=False)
    for col, game in enumerate(games):
        for ri, rep in enumerate(("exact", "texture_range_q8_b8")):
            ax = axes[ri, col]
            for clip, marker in (("signed", "o"), ("clipped", "s")):
                for readout, style in styles.items():
                    rows = [
                        r
                        for r in fixed
                        if r["spot_file"] == game
                        and r["representation"] == rep
                        and r["regret_rule"] == clip
                        and r["readout"] == readout
                    ]
                    group = means(rows, ("batch_size",), ["gain_pct_initial_pot"])
                    ax.plot(
                        [r["batch_size"] for r in group],
                        [r["gain_pct_initial_pot"] for r in group],
                        marker=marker,
                        linestyle=style,
                        label=clip + " " + readout,
                    )
            ax.set_title(Path(game).stem + "; " + rep)
            ax.set_xlabel("Frozen-pass batch size")
            ax.set_ylabel("Unilateral within-game gain (% initial pot)")
            ax.grid(alpha=0.2)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=3, fontsize=8)
    fig.suptitle(
        prefix + "Final policies vs all four original full opponents; "
        "means over 2 seats x 3 seeds x 4 controls"
    )
    fig.tight_layout(rect=(0, 0.09, 1, 0.95))
    fig.savefig(output / "fixed-current-average.png", dpi=160)
    plt.close(fig)


def write_report(
    root: Path,
    saved: dict[str, Any],
    sources: inputs.Sources,
    output: Path,
    *,
    plots: bool = True,
) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    games = sources.own["config"]["spot_files"]
    pot = {g: float(json.loads((root / g).read_text())["pot"]) for g in games}
    profiles, self_pairs, fixed, fixed_pairs = tables(saved, sources, pot)
    average = means(profiles, GROUP, [m + "_pct_initial_pot" for m in METRICS])
    names = (
        "profiles.csv",
        "self-pairs.csv",
        "fixed-targets.csv",
        "fixed-pairs.csv",
        "means.csv",
    )
    for n, rows in zip(
        names, (profiles, self_pairs, fixed, fixed_pairs, average), strict=True
    ):
        write_csv(output / n, rows)
    software = str(saved["config"]["status"]).startswith("EXPLICIT")
    lines = [
        "# Saved batch current-policy diagnosis",
        "",
        "SOFTWARE FIXTURE, NOT POKER RESULTS"
        if software
        else "Known saved games only; no new training or policy changes.",
        "All 216 current scores; 432 average scores reused; "
        "1,728 fixed targets; 1,152 paired fixed contrasts.",
        "Current minus average self gaps change both players; "
        "fixed targets keep opponents unchanged.",
        "Fixed gains are unilateral; "
        "do not equate them to half-summed self exploitability.",
        "All modes/seeds/opponents retained; "
        "shared trajectories are not independent samples.",
        "No pure-variance causal or selected/default/fresh/global claim.",
        "",
        "| Game | Encoding | Rule | Batch | Readout | "
        "Final exact (%pot) | Within | Extra |",
        "|---|---|---|---:|---|---:|---:|---:|",
    ]
    for r in average:
        if r["work_label"] != sources.own["config"]["work_labels"][-1]:
            continue
        lines.append(
            "| "
            + " | ".join(
                [
                    Path(r["spot_file"]).stem,
                    r["representation"],
                    r["regret_rule"],
                    str(r["batch_size"]),
                    r["readout"],
                    *(
                        f"{r[m + '_pct_initial_pot']:.9f}"
                        for m in (
                            "exact_exploitability",
                            "within_partition_gain",
                            "extra_information_gap",
                        )
                    ),
                ]
            )
            + " |"
        )
    (output / "tables.md").write_text("\n".join(lines) + "\n")
    if plots:
        figures(output, profiles, fixed, software)
    result = dict(
        current_profiles=216,
        reused_average_profiles=432,
        fixed_targets=1728,
        self_pairs=432,
        paired_fixed_targets=1152,
        numerical_sha256={n: digest(output / n) for n in (*names, "tables.md")},
        figures=list(FIGURES) if plots else [],
        scope="saved-data diagnosis only; no training/default/fresh/global admission",
    )
    (output / "summary.json").write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n"
    )
    return result
