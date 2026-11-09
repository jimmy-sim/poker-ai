"""Complete known-game current/whole/window tables, with optional static figures."""

import importlib
import itertools
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from poker_ai.evaluation.averaging_history_inputs import HistoryInputs
from poker_ai.evaluation.controlled_reply_inputs import modes
from poker_ai.postflop.game import load_spot
from poker_ai.postflop.learning_report import write_csv
from poker_ai.postflop.river_study import digest

FIGURES = tuple(
    name + "-" + traversal + ".png"
    for name in ("current-curves", "final-averages", "fixed-opponent-differences")
    for traversal in ("full", "external")
)
CASE = ("spot_file", "representation", "traversal", "regret_rule", "average_weight")
SCORES = (
    "exact_exploitability",
    "within_partition_gain",
    "extra_information_gap",
    "river_only_gain_exact_prefix",
    "value_player_zero",
)


def final_variant(row: dict[str, Any], config: dict[str, Any]) -> str:
    if row["kind"] == "current" and row["work_label"] == config["source_target"]:
        return "current_final"
    variant = row["variant"]
    if not isinstance(variant, str):
        raise ValueError("history variant must be a string")
    return variant


def profile_rows(
    data: HistoryInputs, saved: dict[str, Any], pot: dict[str, float]
) -> list[dict[str, Any]]:
    result = []
    for row in saved["rows"]:
        record = dict(
            **row["case"],
            profile_id=row["id"],
            source_profile_id=row["source_profile_id"],
            kind=row["kind"],
            variant=final_variant(row, data.config),
            work_label=row["work_label"],
            actual_work=row["total_work"],
            iteration=row["iteration"],
            window_left=row["window"]["left_label"] if row["window"] else None,
            window_left_work=row["window"]["left_work"] if row["window"] else None,
            window_left_iteration=row["window"]["left_iteration"]
            if row["window"]
            else None,
            policy_sha256=row["receipt"]["policy_sha256"],
        )
        for metric in SCORES:
            value = row["metrics"][metric + "_chips"]
            record[metric + "_chips"] = value
            record[metric + "_pct_initial_pot"] = (
                100 * value / pot[row["case"]["spot_file"]]
            )
        for region in ("all", "river"):
            for label in ("row_fraction", "uniform_reach_fraction"):
                record["coverage_" + region + "_" + label] = (
                    row["coverage"][region][label] if row["coverage"] else None
                )
        for label in ("mean_row_l1", "maximum_row_l1", "uniform_reach_weighted_l1"):
            record[label] = (
                row["current_movement"][label] if row["current_movement"] else None
            )
        result.append(record)
    return result


def fixed_rows(saved: dict[str, Any], pot: dict[str, float]) -> list[dict[str, Any]]:
    whole = {
        (r["own_source_profile_id"], r["opponent_profile_id"], r["target"]): r
        for r in saved["fixed_matches"]
        if r["own_variant"] == "whole_average"
    }
    result = []
    for row in saved["fixed_matches"]:
        baseline = whole[
            row["own_source_profile_id"], row["opponent_profile_id"], row["target"]
        ]
        scale = 100 / pot[row["case"]["spot_file"]]
        record = dict(
            **row["case"],
            own_variant=row["own_variant"],
            target=row["target"],
            own_snapshot_id=row["own_snapshot_id"],
            own_source_profile_id=row["own_source_profile_id"],
            opponent_profile_id=row["opponent_profile_id"],
            opponent_regret_rule=row["opponent_case"]["regret_rule"],
            opponent_average_weight=row["opponent_case"]["average_weight"],
            reply_sha256=row["reply_sha256"],
            gain_difference_chips=row["gain_chips"] - baseline["gain_chips"],
            ev_difference_chips=row["baseline_value_chips"]
            - baseline["baseline_value_chips"],
        )
        for key in (
            "baseline_value_chips",
            "restricted_reply_value_chips",
            "achieved_reply_value_chips",
            "gain_chips",
        ):
            record[key] = row[key]
        record["gain_pct_initial_pot"] = row["gain_chips"] * scale
        record["gain_difference_pct_initial_pot"] = (
            record["gain_difference_chips"] * scale
        )
        record["ev_difference_pct_initial_pot"] = record["ev_difference_chips"] * scale
        result.append(record)
    return result


def grouped_means(
    rows: list[dict[str, Any]],
    fields: tuple[str, ...],
    numeric: tuple[str, ...],
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        key = json.dumps({k: row[k] for k in fields}, sort_keys=True)
        groups.setdefault(key, []).append(row)
    result = []
    for key in sorted(groups):
        selected = sorted(groups[key], key=lambda r: r["seed"] or 0)
        identity = json.loads(key)
        expected = config["seeds"] if identity["traversal"] == "external" else [None]
        if [r["seed"] for r in selected] != expected:
            raise ArithmeticError(
                "cannot average a partial/duplicated history seed group"
            )
        record = dict(
            **identity, count=len(selected), seeds=[r["seed"] for r in selected]
        )
        for label in numeric:
            values = [r[label] for r in selected]
            if all(v is None for v in values):
                record[label] = None
            elif any(v is None for v in values):
                raise ArithmeticError(
                    "inconsistent support/movement in history seed group"
                )
            else:
                record[label] = math.fsum(values) / len(values)
        result.append(record)
    return result


VARIANT_LABEL = dict(
    whole_average="whole",
    current_final="current",
    suffix_5m_10m="5–10m",
    suffix_9m_10m="9–10m",
)


def _mode_label(mode: tuple[str, str]) -> str:
    return mode[0] + "/" + ("u" if mode[1] == "uniform" else "l")


def _plot_current(
    plt: Any,
    data: HistoryInputs,
    profiles: list[dict[str, Any]],
    means: list[dict[str, Any]],
    output: Path,
    scope: str,
    traversal: str,
) -> None:
    groups = list(
        itertools.product(data.config["spot_files"], data.config["representations"])
    )
    fig, axes = plt.subplots(2, 2, figsize=(14, 10), squeeze=False)
    for ax, (game, name) in zip(axes.flat, groups, strict=True):
        for color, clip in enumerate(data.config["regret_rules"]):
            selected = sorted(
                [
                    r
                    for r in means
                    if r["spot_file"] == game
                    and r["representation"] == name
                    and r["traversal"] == traversal
                    and r["kind"] == "current"
                    and r["regret_rule"] == clip
                    and r["average_weight"] == data.config["average_weights"][0]
                ],
                key=lambda r: r["work_label"],
            )
            ax.plot(
                [r["work_label"] for r in selected],
                [r["exact_exploitability_pct_initial_pot"] for r in selected],
                marker="o",
                label=clip,
                color=f"C{color}",
            )
            if traversal == "external":
                raw = [
                    r
                    for r in profiles
                    if r["spot_file"] == game
                    and r["representation"] == name
                    and r["traversal"] == traversal
                    and r["kind"] == "current"
                    and r["regret_rule"] == clip
                    and r["average_weight"] == data.config["average_weights"][0]
                ]
                ax.scatter(
                    [r["work_label"] for r in raw],
                    [r["exact_exploitability_pct_initial_pot"] for r in raw],
                    s=12,
                    color=f"C{color}",
                    alpha=0.6,
                )
        ax.set_xscale("log")
        ax.set_xlabel("First complete work crossing (node visits)")
        ax.set_ylabel("Current exact exploitability (% initial pot)")
        ax.set_title(Path(game).stem + " / " + name, fontsize=9)
        ax.grid(alpha=0.2)
    axes[0, 0].legend()
    fig.suptitle(scope + " — current policies, " + traversal, fontsize=11)
    fig.text(
        0.5,
        0.01,
        "Both average-weight paths match bit-for-bit; "
        "canonical first-label copy drawn once. "
        + (
            "Three-seed means and raw points; no confidence intervals."
            if traversal == "external"
            else "Deterministic controls, once."
        ),
        ha="center",
        fontsize=8,
    )
    fig.tight_layout(rect=(0, 0.04, 1, 0.94))
    fig.savefig(output / ("current-curves-" + traversal + ".png"), dpi=140)
    plt.close(fig)


def _plot_final(
    plt: Any,
    data: HistoryInputs,
    profiles: list[dict[str, Any]],
    means: list[dict[str, Any]],
    output: Path,
    scope: str,
    traversal: str,
) -> None:
    groups = list(
        itertools.product(data.config["spot_files"], data.config["representations"])
    )
    mode_order = modes(data.config)
    variant_order = data.config["fixed_opponent_own_variants"]
    variant_label = VARIANT_LABEL
    label = _mode_label
    fig, axes = plt.subplots(2, 2, figsize=(19, 12), squeeze=False)
    for ax, (game, name) in zip(axes.flat, groups, strict=True):
        chosen = {
            (r["regret_rule"], r["average_weight"], r["variant"]): r
            for r in means
            if (r["spot_file"], r["representation"], r["traversal"])
            == (game, name, traversal)
        }
        combinations = list(itertools.product(mode_order, variant_order))
        values = [chosen[*mode, variant] for mode, variant in combinations]
        x = np.arange(len(values))
        within = [r["within_partition_gain_pct_initial_pot"] for r in values]
        extra = [r["extra_information_gap_pct_initial_pot"] for r in values]
        ax.bar(x, within, label="Within information groups")
        ax.bar(x, extra, bottom=within, label="Extra exact-information value")
        if traversal == "external":
            for i, (mode, variant) in enumerate(combinations):
                raw = [
                    r
                    for r in profiles
                    if (
                        r["spot_file"],
                        r["representation"],
                        r["traversal"],
                        r["regret_rule"],
                        r["average_weight"],
                        r["variant"],
                    )
                    == (game, name, traversal, *mode, variant)
                ]
                ax.scatter(
                    [i] * len(raw),
                    [r["exact_exploitability_pct_initial_pot"] for r in raw],
                    color="black",
                    s=10,
                    zorder=5,
                )
        ax.set_xticks(
            x,
            [
                label(mode) + "\n" + variant_label[variant]
                for mode, variant in combinations
            ],
            rotation=50,
            ha="right",
            fontsize=7,
        )
        ax.set_title(Path(game).stem + " / " + name, fontsize=10)
        ax.set_ylabel("Self exact exploitability (% initial pot)")
        ax.grid(axis="y", alpha=0.2)
    axes[0, 0].legend(fontsize=8)
    fig.suptitle(
        scope + " — final current / whole / windows, " + traversal, fontsize=12
    )
    fig.text(
        0.5,
        0.01,
        "Linear regret weights; u/l = uniform/linear average. "
        "Current duplicates retained. "
        + (
            "Means and individual seed totals; no confidence intervals."
            if traversal == "external"
            else "Full controls, once."
        ),
        ha="center",
        fontsize=9,
    )
    fig.tight_layout(rect=(0, 0.04, 1, 0.94))
    fig.savefig(output / ("final-averages-" + traversal + ".png"), dpi=140)
    plt.close(fig)


def _plot_fixed(
    plt: Any,
    data: HistoryInputs,
    fixed: list[dict[str, Any]],
    output: Path,
    scope: str,
    traversal: str,
) -> None:
    groups = list(
        itertools.product(data.config["spot_files"], data.config["representations"])
    )
    mode_order = modes(data.config)
    variant_order = data.config["fixed_opponent_own_variants"]
    variant_label = VARIANT_LABEL
    label = _mode_label
    selected = [
        r
        for r in fixed
        if r["traversal"] == traversal and r["own_variant"] != "whole_average"
    ]
    maximum = (
        max((abs(r["gain_difference_pct_initial_pot"]) for r in selected), default=0.0)
        or 1e-12
    )
    fig, axes = plt.subplots(2, 4, figsize=(22, 17), squeeze=False)
    own_order = list(itertools.product(mode_order, variant_order[1:]))
    for column, (game, name) in enumerate(groups):
        for target in (0, 1):
            ax = axes[target, column]
            matrix = np.zeros((12, 4))
            for i, (mode, variant) in enumerate(own_order):
                for j, opponent in enumerate(mode_order):
                    values = [
                        r["gain_difference_pct_initial_pot"]
                        for r in selected
                        if (
                            r["spot_file"],
                            r["representation"],
                            r["target"],
                            r["regret_rule"],
                            r["average_weight"],
                            r["own_variant"],
                            r["opponent_regret_rule"],
                            r["opponent_average_weight"],
                        )
                        == (game, name, target, *mode, variant, *opponent)
                    ]
                    if len(values) != 1:
                        raise ArithmeticError("fixed-opponent mean heatmap incomplete")
                    matrix[i, j] = values[0]
            color = ax.imshow(
                matrix, vmin=-maximum, vmax=maximum, cmap="coolwarm", aspect="auto"
            )
            ax.set_xticks(
                range(4),
                [label(m) for m in mode_order],
                rotation=45,
                ha="right",
                fontsize=8,
            )
            ax.set_yticks(
                range(12),
                [label(m) + " " + variant_label[v] for m, v in own_order],
                fontsize=8,
            )
            ax.set_xlabel("Fixed saved opponent", fontsize=9)
            ax.set_title(
                f"{Path(game).stem} / {name}\nresponding seat {target}", fontsize=9
            )
            for i, j in np.ndindex(matrix.shape):
                ax.text(
                    j,
                    i,
                    f"{matrix[i, j]:.3g}",
                    ha="center",
                    va="center",
                    fontsize=8,
                    color="white" if abs(matrix[i, j]) > maximum * 0.65 else "black",
                )
    fig.suptitle(
        scope
        + " — fixed-opponent gain change, "
        + traversal
        + "\nVariant minus matching whole average; "
        "negative is better own EV; positive is worse",
        fontsize=12,
    )
    fig.text(
        0.5,
        0.01,
        "Unilateral % initial pot; all four fixed opponents and both seats. "
        + (
            "Three-seed arithmetic means, no confidence intervals."
            if traversal == "external"
            else "Deterministic full controls."
        ),
        ha="center",
        fontsize=9,
    )
    fig.tight_layout(rect=(0, 0.04, 0.94, 0.94))
    bar = fig.add_axes((0.955, 0.2, 0.012, 0.6))
    fig.colorbar(color, cax=bar, label="Change in within gain (% initial pot)")
    fig.savefig(output / ("fixed-opponent-differences-" + traversal + ".png"), dpi=140)
    plt.close(fig)


def render(
    data: HistoryInputs,
    profiles: list[dict[str, Any]],
    means: list[dict[str, Any]],
    fixed: list[dict[str, Any]],
    output: Path,
    scope: str,
) -> None:
    mpl = importlib.import_module("matplotlib")
    mpl.use("Agg")
    plt = importlib.import_module("matplotlib.pyplot")
    for traversal in data.config["traversals"]:
        _plot_current(plt, data, profiles, means, output, scope, traversal)
        _plot_final(plt, data, profiles, means, output, scope, traversal)
        _plot_fixed(plt, data, fixed, output, scope, traversal)


def write_report(
    root: Path,
    data: HistoryInputs,
    saved: dict[str, Any],
    output: Path,
    *,
    plots: bool = True,
    pot: dict[str, float] | None = None,
    scope: str = "Known tiny-range trajectory diagnosis",
) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    pot = (
        {game: float(load_spot(root / game).pot) for game in data.config["spot_files"]}
        if pot is None
        else pot
    )
    profiles = profile_rows(data, saved, pot)
    fixed = fixed_rows(saved, pot)
    masses = [
        dict(
            **r["case"],
            boundary_id=r["id"],
            source_profile_id=r["source_profile_id"],
            work_label=r["work_label"],
            actual_work=r["total_work"],
            iteration=r["iteration"],
            state_sha256=r["state_sha256"],
            learning_path_sha256=r["learning_path_sha256"],
            cumulative_mass_sha256=r["receipt"]["mass_sha256"],
        )
        for r in saved["masses"]
    ]
    numeric = tuple(
        k
        for k in profiles[0]
        if k.endswith(("_chips", "_pct_initial_pot", "_fraction", "_l1"))
    )
    # Both current L1 fields and weighted L1 are included, not inferred from means.
    means = grouped_means(
        profiles, (*CASE, "kind", "variant", "work_label"), numeric, data.config
    )
    fixed_numeric = tuple(
        k for k in fixed[0] if k.endswith(("_chips", "_pct_initial_pot"))
    )
    fixed_means = grouped_means(
        fixed,
        (
            *CASE,
            "own_variant",
            "opponent_regret_rule",
            "opponent_average_weight",
            "target",
        ),
        fixed_numeric,
        data.config,
    )
    if (len(profiles), len(masses), len(fixed), len(means), len(fixed_means)) != (
        512,
        192,
        2048,
        256,
        1024,
    ):
        raise ArithmeticError("history reporting grid incomplete")
    tables = dict(
        profiles=profiles,
        cumulative_boundaries=masses,
        fixed_targets=fixed,
        profile_means=means,
        fixed_means=fixed_means,
    )
    for name, rows in tables.items():
        write_csv(output / (name.replace("_", "-") + ".csv"), rows)
    if plots:
        render(data, profiles, means, fixed_means, output, scope)
    lines = [
        "# Current policies and averaging history",
        "",
        scope + ".",
        "All modes, known games, original work limit. Full controls once; sampled "
        "arithmetic means of three fixed seeds, not a mixture of their strategies.",
        "Current paths duplicate across average-weight modes; all raw rows remain. "
        "Suffixes retain original time weights and the uniform zero-mass fallback.",
        "",
        "| Game / information | Traversal | Regret / average | Final variant | "
        "Exact total | Within | Extra | Window reach coverage |",
        "|---|---|---|---|---:|---:|---:|---:|",
    ]
    for row in means:
        if row["variant"] not in data.config["fixed_opponent_own_variants"]:
            continue
        support = row["coverage_all_uniform_reach_fraction"]
        support_label = "—" if support is None else f"{support:.6g}"
        lines.append(
            f"| {Path(row['spot_file']).stem} / {row['representation']} | "
            f"{row['traversal']} | "
            f"{row['regret_rule']} / {row['average_weight']} | {row['variant']} | "
            f"{row['exact_exploitability_pct_initial_pot']:.9g} | "
            f"{row['within_partition_gain_pct_initial_pot']:.9g} | "
            f"{row['extra_information_gap_pct_initial_pot']:.9g} | {support_label} |"
        )
    lines += [
        "",
        "Scores above: percent initial pot, half-summed over seats. Coverage "
        "is a unitless uniform-decision-reach fraction; current policies have no "
        "window support claim. Whole coverage includes warm initialization.",
        "Fixed-opponent tables use unilateral gains; their differences are variant "
        "minus matching whole average. Negative gain differences mean better own "
        "EV against that same saved opponent. Every opponent, target and seed remains.",
        "No confidence interval, convergence claim, selected snapshot/window, "
        "stronger default, fresh-game or global admission follows.",
    ]
    (output / "tables.md").write_text("\n".join(lines) + "\n")
    files = [name.replace("_", "-") + ".csv" for name in tables] + ["tables.md"]
    summary = dict(
        scope=scope,
        source_cases=64,
        profiles=len(profiles),
        cumulative_boundaries=len(masses),
        fixed_opponent_target_conditions=len(fixed),
        profile_mean_groups=len(means),
        fixed_mean_groups=len(fixed_means),
        figures=[name for name in FIGURES if (output / name).exists()],
        files={name: digest(output / name) for name in files},
        interpretation=(
            "known trajectories only; no selected remedy or default/global admission"
        ),
    )
    (output / "summary.json").write_text(
        json.dumps(summary, sort_keys=True, indent=2) + "\n"
    )
    return summary
