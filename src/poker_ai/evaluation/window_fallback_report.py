"""All raw fallback conditions and fixed seed means, with optional figures."""

import json
from pathlib import Path
from typing import Any

from poker_ai.evaluation.averaging_history_report import grouped_means
from poker_ai.evaluation.window_fallback_inputs import FallbackInputs
from poker_ai.evaluation.window_fallback_validation import grid
from poker_ai.postflop.game import load_spot
from poker_ai.postflop.learning_report import write_csv
from poker_ai.postflop.river_study import digest

CASE = ("spot_file", "representation", "traversal", "regret_rule", "average_weight")
SCORES = (
    "exact_exploitability",
    "within_partition_gain",
    "extra_information_gap",
    "river_only_gain_exact_prefix",
    "value_player_zero",
)
FIGURES = tuple(
    prefix + "-" + traversal + ".png"
    for prefix in ("self-changes", "fixed-opponent-changes")
    for traversal in ("full", "external")
)


def records(
    saved: dict[str, Any], pot: dict[str, float]
) -> tuple[list[dict[str, Any]], ...]:
    raw = {r["index"]: r for r in saved["rows"] if r["fill_label"] == "raw"}
    profiles = []
    support = []
    panels = []
    fixed = []
    for row in saved["rows"]:
        record = dict(
            **row["case"],
            profile_id=row["id"],
            source_window_id=row["source_window_id"],
            window_variant=row["window_variant"],
            fill_label=row["fill_label"],
            policy_sha256=row["receipt"]["policy_sha256"],
            window_index=row["index"],
            maximum_realization_change=row["maximum_realization_change"],
        )
        scale = 100 / pot[row["case"]["spot_file"]]
        for name in SCORES:
            value = row["metrics"][name + "_chips"]
            delta = value - raw[row["index"]]["metrics"][name + "_chips"]
            record[name + "_chips"] = value
            record[name + "_pct_initial_pot"] = value * scale
            record[name + "_difference_chips"] = delta
            record[name + "_difference_pct_initial_pot"] = delta * scale
        profiles.append(record)
        for target in row["support"]:
            support.append(
                dict(
                    **row["case"],
                    profile_id=row["id"],
                    source_window_id=row["source_window_id"],
                    window_variant=row["window_variant"],
                    fill_label=row["fill_label"],
                    maximum_realization_change=row["maximum_realization_change"],
                    **target,
                )
            )
    for row in saved["panels"]:
        panel = {**row["case"], **{k: v for k, v in row.items() if k != "case"}}
        panel["baseline_ev_interaction_pct_initial_pot"] = (
            100 * panel["baseline_ev_interaction_chips"] / pot[row["case"]["spot_file"]]
        )
        panels.append(panel)
    for row in saved["fixed_matches"]:
        record = dict(
            **row["case"],
            profile_id=row["own_snapshot_id"],
            source_window_id=row["source_window_id"],
            window_variant=row["window_variant"],
            fill_label=row["fill_label"],
            target=row["target"],
            opponent_profile_id=row["opponent_profile_id"],
            opponent_regret_rule=row["opponent_case"]["regret_rule"],
            opponent_average_weight=row["opponent_case"]["average_weight"],
        )
        for key in (
            "baseline_value_chips",
            "restricted_reply_value_chips",
            "achieved_reply_value_chips",
            "gain_chips",
            "gain_difference_chips",
            "ev_difference_chips",
        ):
            record[key] = row[key]
            record[key.removesuffix("_chips") + "_pct_initial_pot"] = (
                100 * row[key] / pot[row["case"]["spot_file"]]
            )
        fixed.append(record)
    return profiles, support, panels, fixed


def write_report(
    root: Path,
    data: FallbackInputs,
    saved: dict[str, Any],
    output: Path,
    *,
    plots: bool = True,
    pot: dict[str, float] | None = None,
    scope: str = "Known saved windows; exact-zero fallback intervention",
) -> dict[str, Any]:
    grid(saved, data)
    pot = (
        pot
        if pot is not None
        else {
            game: float(load_spot(root / game).pot)
            for game in data.config["spot_files"]
        }
    )
    profiles, support, panels, fixed = records(saved, pot)
    numeric = tuple(
        k for k in profiles[0] if k.endswith(("_chips", "_pct_initial_pot"))
    )
    means = grouped_means(
        profiles, (*CASE, "window_variant", "fill_label"), numeric, data.config
    )
    fixed_numeric = tuple(
        k for k in fixed[0] if k.endswith(("_chips", "_pct_initial_pot"))
    )
    fixed_means = grouped_means(
        fixed,
        (
            *CASE,
            "window_variant",
            "fill_label",
            "target",
            "opponent_regret_rule",
            "opponent_average_weight",
        ),
        fixed_numeric,
        data.config,
    )
    if (
        len(profiles),
        len(support),
        len(panels),
        len(fixed),
        len(means),
        len(fixed_means),
    ) != (512, 1024, 128, 2048, 256, 1024):
        raise ArithmeticError("fallback numerical report inventory incomplete")
    output.mkdir(parents=True, exist_ok=True)
    tables = dict(
        profiles=profiles,
        support=support,
        panels=panels,
        fixed_targets=fixed,
        profile_means=means,
        fixed_means=fixed_means,
    )
    for name, rows in tables.items():
        write_csv(output / (name.replace("_", "-") + ".csv"), rows)
    if plots:
        from poker_ai.evaluation.window_fallback_figures import render

        render(data, profiles, means, fixed_means, output, scope)
    lines = [
        "# Saved-window fallback intervention",
        "",
        scope + ".",
        "All raw windows and three target-fill masks retained. "
        "Changes are relative to the raw same window.",
        "Full controls once; sampled arithmetic means of three fixed seeds, "
        "not mixed strategies.",
        "Positive-mass rows stay bit-exact; duplicate/no-op fills "
        "are not independent observations.",
        "",
        "| Game / information | Traversal | Regret / average | Window | Fill | "
        "Total | Within | Extra | Total change |",
        "|---|---|---|---|---|---:|---:|---:|---:|",
    ]
    for row in means:
        lines.append(
            f"| {Path(row['spot_file']).stem} / {row['representation']} | "
            f"{row['traversal']} | {row['regret_rule']} / {row['average_weight']} | "
            f"{row['window_variant']} | {row['fill_label']} | "
            f"{row['exact_exploitability_pct_initial_pot']:.9g} | "
            f"{row['within_partition_gain_pct_initial_pot']:.9g} | "
            f"{row['extra_information_gap_pct_initial_pot']:.9g} | "
            f"{row['exact_exploitability_difference_pct_initial_pot']:.9g} |"
        )
    lines += [
        "",
        "Self scores: percent initial pot, half-summed over seats. "
        "Changes: percentage points of initial pot.",
        "Fixed targets use unilateral target chips; negative gain change "
        "means better EV against that same opponent.",
        "Support fractions are unitless. Own realization reach excludes "
        "chance/opponent; it differs from uniform-game exposure.",
        "All raw seeds, full invariants, seat-fill accounting and baseline "
        "EV interactions remain in CSVs.",
        "No confidence intervals, new training, selected window/fallback "
        "deployment or default/fresh/global admission.",
    ]
    (output / "tables.md").write_text("\n".join(lines) + "\n")
    files = [name.replace("_", "-") + ".csv" for name in tables] + ["tables.md"]
    summary = dict(
        scope=scope,
        source_cases=64,
        source_windows=128,
        self_profiles=512,
        support_rows=1024,
        additivity_panels=128,
        fixed_target_conditions=2048,
        profile_mean_groups=256,
        fixed_mean_groups=1024,
        figures=list(FIGURES) if plots else [],
        files={name: digest(output / name) for name in files},
        interpretation=(
            "saved-policy diagnostic only; no new training or admitted replacement"
        ),
    )
    (output / "summary.json").write_text(
        json.dumps(summary, sort_keys=True, indent=2) + "\n"
    )
    return summary
