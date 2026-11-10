"""Complete paired tables and all-context heatmaps; no policy selection."""

import csv
import importlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from poker_ai.evaluation.private_prefix_design import OLD, READOUTS, TOY
from poker_ai.postflop.river_study import digest


def write(
    saved: dict[str, Any],
    folder: Path,
    pots: dict[str, float],
    *,
    no_plots: bool = False,
) -> dict[str, str]:
    if folder.exists() or folder.is_symlink():
        raise FileExistsError("retain private-prefix complete/partial report")
    if len(saved["self_pairs"]) != 864 or len(saved["fixed_pairs"]) != 2304:
        raise ArithmeticError("complete864/2304 contrasts required before report")
    if any(
        type(p) not in (int, float) or not math.isfinite(p) or p <= 0
        for p in pots.values()
    ):
        raise ValueError("report pot must be a finite positive chip quantity")
    profiles = {r["id"]: r for r in saved["rows"]}
    points = []
    for pair in saved["self_pairs"]:
        row = profiles[pair["candidate_id"]]
        pot = pots[row["case"]["spot_file"]]
        points.append(
            dict(
                baseline_kind=pair["baseline_kind"],
                batch_size=row["batch_size"],
                work_label=row["work_label"],
                readout=row["readout"],
                **{
                    k: row["case"][k]
                    for k in ("spot_file", "representation", "regret_rule", "seed")
                },
                candidate_id=row["id"],
                baseline_id=pair["baseline_id"],
                candidate_total_work=pair["candidate_total_work"],
                baseline_total_work=pair["baseline_total_work"],
                candidate_iteration=pair["candidate_iteration"],
                baseline_iteration=pair["baseline_iteration"],
                candidate_exact_exploitability_pct_pot=100
                * row["metrics"]["exact_exploitability_chips"]
                / pot,
                **{
                    "delta_" + k: v
                    for k, v in pair["baseline_minus_candidate_chips"].items()
                },
                **{
                    "delta_" + k.removesuffix("_chips") + "_pct_pot": 100 * v / pot
                    for k, v in pair["baseline_minus_candidate_chips"].items()
                },
            )
        )
    fields = (
        "spot_file",
        "representation",
        "regret_rule",
        "readout",
        "baseline_kind",
        "batch_size",
        "work_label",
    )
    grouped: dict[Any, list[dict[str, Any]]] = {}
    for point in points:
        grouped.setdefault(tuple(point[k] for k in fields), []).append(point)
    groups = []
    for key, rows in sorted(grouped.items()):
        if sorted(r["seed"] for r in rows) != [20261301, 20261302, 20261303]:
            raise ArithmeticError(
                "all three unique declared seeds per report group required"
            )
        metric = "delta_exact_exploitability_pct_pot"
        values = [r[metric] for r in rows]
        if any(not math.isfinite(x) for x in values):
            raise ArithmeticError("nonfinite normalized report difference")
        groups.append(
            dict(
                zip(fields, key, strict=True),
                seeds=3,
                mean_delta_pct_pot=math.fsum(values) / 3,
                min_delta_pct_pot=min(values),
                max_delta_pct_pot=max(values),
            )
        )
    if len(points) != 864 or len(groups) != 288:
        raise ArithmeticError("complete report seed groups required")
    fixed = []
    for pair in saved["fixed_pairs"]:
        row = profiles[pair["candidate_id"]]
        pot = pots[row["case"]["spot_file"]]
        fixed.append(
            dict(
                pair,
                **{
                    k: row["case"][k]
                    for k in ("spot_file", "representation", "regret_rule", "seed")
                },
                readout=row["readout"],
                batch_size=row["batch_size"],
                baseline_minus_candidate_ev_pct_pot=100
                * pair["baseline_minus_candidate_ev_chips"]
                / pot,
                baseline_minus_candidate_gain_pct_pot=100
                * pair["baseline_minus_candidate_gain_chips"]
                / pot,
            )
        )
    folder.mkdir(parents=True)
    for name, rows in (
        ("self-points", points),
        ("self-groups", groups),
        ("fixed-pairs", fixed),
    ):
        with (folder / (name + ".csv")).open("w", newline="") as stream:
            writer = csv.DictWriter(
                stream, fieldnames=sorted(rows[0]), lineterminator="\n"
            )
            writer.writeheader()
            writer.writerows(rows)
    scope = saved["scope"]
    summary = dict(
        scope=scope,
        status="own_only_native_pending",
        new_candidate_profiles=432,
        new_ledgers=288,
        new_fixed_targets=1152,
        self_contrasts=864,
        fixed_contrasts=2304,
        seed_groups=288,
        all_seeds_and_readouts_retained=True,
        baseline_rows=len(saved["baseline_rows"]),
        uncertainty=(
            "three fixed seeds, reused B1 baselines and dependent readouts; "
            "no population confidence interval"
        ),
        units=(
            "delta in percentage points of initial pot; baseline minus candidate; "
            "positive exploitability delta favors candidate"
        ),
        fixed_sign=(
            "positive EV delta favors baseline; positive gain delta favors "
            "candidate; fixed EV and security differ"
        ),
        new_agent_default=False,
        fresh_global_admission=False,
        scope_limit=(
            "explicit single nonuniform-Kuhn software fixture; "
            "logical spot/encoding labels are duplicates"
        )
        if scope == TOY
        else (
            "old own policies for cost calibration; "
            "no new trajectory or strength result"
        )
        if scope == OLD
        else (
            "two known tiny-range games; "
            "no general Holdem win-rate or convergence claim"
        ),
    )
    (folder / "summary.json").write_text(
        json.dumps(summary, sort_keys=True, indent=2) + "\n"
    )
    if not no_plots:
        plots(scope, groups, folder)
    return {p.name: digest(p) for p in sorted(folder.iterdir())}


def plots(scope: str, groups: list[dict[str, Any]], folder: Path) -> None:
    """Optional standard plotting boundary; no imports/stubs required in base."""
    matplotlib = importlib.import_module("matplotlib")
    matplotlib.use("Agg")
    plt = importlib.import_module("matplotlib.pyplot")
    colors = importlib.import_module("matplotlib.colors")
    context_fields = ("spot_file", "representation", "regret_rule")
    contexts = sorted({tuple(r[k] for k in context_fields) for r in groups})
    columns = sorted(
        {(r["baseline_kind"], r["batch_size"], r["work_label"]) for r in groups}
    )
    if len(contexts) != 8 or len(columns) != 12:
        raise ArithmeticError("complete plot context/column grid required")
    cmap = colors.LinearSegmentedColormap.from_list(
        "baseline_to_stratified", ["#2166ac", "#ffffff", "#d95f02"]
    )
    scope_title = (
        "EXPLICIT one-game toy software fixture; logical contexts are duplicates"
        if scope == TOY
        else "OLD own cost corpus; no new trajectories"
        if scope == OLD
        else "Two known tiny-range games; no default/global admission"
    )
    candidate = "old IID copy" if scope == OLD else "stratified"
    for readout in READOUTS:
        selected = [r for r in groups if r["readout"] == readout]
        lookup = {
            (
                tuple(r[k] for k in context_fields),
                (r["baseline_kind"], r["batch_size"], r["work_label"]),
            ): r
            for r in selected
        }
        array = np.array(
            [[lookup[c, k]["mean_delta_pct_pot"] for k in columns] for c in contexts]
        )
        extent = max(float(np.max(np.abs(array))), 1e-12)
        fig, axis = plt.subplots(figsize=(18, 10), layout="constrained")
        display = axis.imshow(
            array, cmap=cmap, vmin=-extent, vmax=extent, aspect="auto"
        )
        axis.set_yticks(
            range(8),
            [
                " / ".join(c)
                .replace("configs/learning-spots/", "")
                .replace(".json", "")
                .replace("texture_range_q8_b8", "q8")
                for c in contexts
            ],
        )
        axis.set_xticks(
            range(12),
            [
                f"{kind} / {candidate} B{batch}\nwork {label:,}"
                for kind, batch, label in columns
            ],
            rotation=45,
            ha="right",
        )
        axis.set_title(
            scope_title
            + "\n"
            + readout
            + (
                ": mean of all three fixed seeds; blue baseline lower, "
                f"orange {candidate} lower. Scales differ."
            )
        )
        for y, x in np.ndindex(array.shape):
            axis.text(x, y, f"{array[y, x]:.4g}", ha="center", va="center", fontsize=10)
        fig.colorbar(
            display,
            ax=axis,
            label=(
                f"Baseline minus {candidate} exact exploitability "
                "(percentage points of initial pot)"
            ),
        )
        fig.savefig(folder / (readout + ".png"), dpi=140)
        plt.close(fig)
