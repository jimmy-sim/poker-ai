"""All-cell fixed-work/iteration summaries and prespecified paired contrasts."""

import csv
import importlib
import itertools
import json
import math
from pathlib import Path
from typing import Any

from poker_ai.postflop.learning_analysis import FACTORS, LEVELS, contrasts
from poker_ai.postflop.river_study import digest

PRIMARY = (
    "exact_exploitability_chips",
    "within_partition_gain_chips",
    "extra_information_gap_chips",
    "river_only_gain_exact_prefix_chips",
)


def logical_rows(
    rows: list[dict[str, Any]], pots: dict[str, float]
) -> list[dict[str, Any]]:
    result = []
    for row in rows:
        for axis, target in row["labels"]:
            result.append(
                dict(
                    **row["case"],
                    id=row["id"],
                    axis=axis,
                    target=target,
                    iteration=row["iteration"],
                    total_work=row["total_work"],
                    previous_work=row["previous_work"],
                    overshoot=row["total_work"] - target if axis == "work" else None,
                    state_sha256=row["state_sha256"],
                    policy_sha256=row["receipt"]["policy_sha256"],
                    **row["metrics"],
                    **row["diagnostics"],
                    **{
                        k.removesuffix("_chips") + "_pct_initial_pot": 100
                        * row["metrics"][k]
                        / pots[row["case"]["spot_file"]]
                        for k in PRIMARY
                    },
                )
            )
    return result


def analyze(
    rows: list[dict[str, Any]], seeds: list[int]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Return all factor means, 32+15 differences, and the four bridge points."""
    means, effects, bridges = [], [], []
    groups = sorted(
        {(r["spot_file"], r["representation"], r["axis"], r["target"]) for r in rows}
    )
    for game, representation, axis, target in groups:
        subset = [
            r
            for r in rows
            if (r["spot_file"], r["representation"], r["axis"], r["target"])
            == (game, representation, axis, target)
        ]
        common = [r for r in subset if r["bridge"] == "common"]
        base = dict(
            spot_file=game, representation=representation, axis=axis, target=target
        )
        for metric in PRIMARY:
            grids: dict[int, dict[tuple[str, ...], float]] = {
                seed: {} for seed in seeds
            }
            values = {}
            for levels in LEVELS:
                chosen = [r for r in common if tuple(r[f] for f in FACTORS) == levels]
                expected = seeds if levels[0] == "external" else [None]
                if (
                    sorted([r["seed"] for r in chosen], key=lambda v: v or 0)
                    != expected
                ):
                    raise ArithmeticError("factor seed grid incomplete/duplicate")
                by_seed = {r["seed"]: r[metric] for r in chosen}
                values[levels] = math.fsum(by_seed.values()) / len(by_seed)
                for seed in seeds:
                    grids[seed][levels] = by_seed[
                        seed if levels[0] == "external" else None
                    ]
                means.append(
                    dict(
                        **base,
                        metric=metric,
                        **dict(zip(FACTORS, levels, strict=True)),
                        mean_chips=values[levels],
                        values_by_seed=by_seed,
                        deterministic_full_reused=levels[0] == "full",
                    )
                )
            average_effects = contrasts(values)
            paired = {seed: contrasts(grid) for seed, grid in grids.items()}
            for kind, contrasts_rows in average_effects.items():
                for index, effect in enumerate(contrasts_rows):
                    differences = {
                        seed: paired[seed][kind][index]["difference"] for seed in seeds
                    }
                    if (
                        abs(
                            math.fsum(differences.values()) / len(seeds)
                            - effect["difference"]
                        )
                        > 1e-9
                    ):
                        raise ArithmeticError("paired-factor mean identity failed")
                    effects.append(
                        dict(
                            **base,
                            metric=metric,
                            kind=kind,
                            **effect,
                            paired_seed_differences=differences,
                            full_controls_reused_not_independent=True,
                        )
                    )
        for bridge in (
            "cold_target_history_mass",
            "warm_target_history_mass",
            "warm_target_chance_mass",
            "warm_opponent_chance_mass",
        ):
            peers = [
                r
                for r in subset
                if r["traversal"] == "full"
                and r["regret_rule"] == "clipped"
                and r["regret_weight"] == "uniform"
                and r["average_weight"] == "linear"
                and r["bridge"]
                == ("common" if bridge == "warm_opponent_chance_mass" else bridge)
            ]
            if len(peers) != 1:
                raise ArithmeticError("four-point bridge incomplete")
            row = peers[0]
            bridges.append(
                dict(
                    **base,
                    bridge=bridge,
                    source_id=row["id"],
                    aliases_common=bridge == "warm_opponent_chance_mass",
                    iteration=row["iteration"],
                    total_work=row["total_work"],
                    **{k: row[k] for k in PRIMARY},
                )
            )
    return means, effects, bridges


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = sorted({k for r in rows for k in r})
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    k: json.dumps(v, sort_keys=True)
                    if isinstance(v, (dict, list))
                    else v
                    for k, v in row.items()
                }
            )


def render(
    rows: list[dict[str, Any]],
    output: Path,
    *,
    scope: str = "Known-game controlled learning",
) -> list[str]:
    matplotlib = importlib.import_module("matplotlib")
    matplotlib.use("Agg")
    plt = importlib.import_module("matplotlib.pyplot")
    groups = sorted({(r["spot_file"], r["representation"]) for r in rows})
    figures = []
    for metric, axis in itertools.product(PRIMARY, ("work", "iteration")):
        fig, axes = plt.subplots(2, 2, figsize=(14, 10), squeeze=False)
        for plot, group in zip(axes.flat, groups, strict=True):
            chosen = [
                r
                for r in rows
                if r["axis"] == axis
                and r["bridge"] == "common"
                and (r["spot_file"], r["representation"]) == group
            ]
            for color, rules in enumerate(
                itertools.product(*list(FACTORS.values())[1:])
            ):
                for traversal in FACTORS["traversal"]:
                    series = [
                        r
                        for r in chosen
                        if r["traversal"] == traversal
                        and tuple(r[f] for f in list(FACTORS)[1:]) == rules
                    ]
                    targets = sorted({r["target"] for r in series})
                    key = metric.removesuffix("_chips") + "_pct_initial_pot"
                    values = [
                        math.fsum(r[key] for r in series if r["target"] == t)
                        / sum(r["target"] == t for r in series)
                        for t in targets
                    ]
                    label = "/".join((traversal, *rules))
                    plot.plot(
                        targets,
                        values,
                        color=f"C{color}",
                        linestyle="-" if traversal == "full" else "--",
                        marker=".",
                        label=label,
                    )
                    if traversal == "external":
                        for seed in sorted({r["seed"] for r in series}):
                            line = sorted(
                                [r for r in series if r["seed"] == seed],
                                key=lambda r: r["target"],
                            )
                            plot.plot(
                                [r["target"] for r in line],
                                [r[key] for r in line],
                                color=f"C{color}",
                                linestyle=":",
                                linewidth=0.6,
                                alpha=0.35,
                            )
            if axis == "work":
                plot.set_xscale("log")
            plot.set_title(f"{Path(group[0]).stem} / {group[1]}", fontsize=9)
            plot.set_xlabel(axis + " checkpoint label (complete crossings for work)")
            plot.set_ylabel("% initial pot")
            plot.grid(alpha=0.2)
        handles, labels = axes[0, 0].get_legend_handles_labels()
        fig.legend(handles, labels, loc="lower center", ncol=4, fontsize=7)
        fig.suptitle(
            scope + ": " + metric + "\nSolid: full; dashed: 3 fixed-seed mean; "
            "faint dotted: individual seeds; no confidence intervals",
            fontsize=10,
        )
        fig.tight_layout(rect=(0, 0.10, 1, 0.94))
        name = metric + "-" + axis + ".png"
        fig.savefig(output / name, dpi=140)
        plt.close(fig)
        figures.append(name)
    return figures


def write_report(
    saved: dict[str, Any],
    comparison: dict[str, Any],
    pots: dict[str, float],
    output: Path,
    *,
    plots: bool = True,
) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    rows = logical_rows(saved["rows"], pots)
    means, effects, bridges = analyze(rows, comparison["seeds"])
    files = {
        "checkpoints.csv": rows,
        "factor-means.csv": means,
        "contrasts.csv": effects,
        "bridges.csv": bridges,
    }
    for name, data in files.items():
        write_csv(output / name, data)
    figures = (
        render(rows, output)
        if plots
        else [
            m + "-" + a + ".png"
            for m in PRIMARY
            for a in ("work", "iteration")
            if (output / (m + "-" + a + ".png")).exists()
        ]
    )
    summary = dict(
        status="complete_own_diagnostic_native_audit_separate",
        cells=140,
        physical_snapshots=len(saved["rows"]),
        logical_checkpoints=len(rows),
        factor_means=len(means),
        contrasts=len(effects),
        bridge_rows=len(bridges),
        training_batch_seconds=saved["batch"]["seconds"],
        native_required=True,
        scope=(
            "known games only; no default/best-arm/fresh/global admission; "
            "no seed confidence intervals"
        ),
        files={name: digest(output / name) for name in files},
        figures=figures,
    )
    lines = [
        "# Fixed controlled-learning endpoints",
        "",
        "All known-game arms. Chips; external arithmetic mean of three fixed seeds.",
        "Work and iteration are separate. No winner/default/global admission.",
        "",
        "| Game / encoding | Axis | Traversal / regret / regret weight "
        "/ average weight "
        "| Exact | Within | Extra | River |",
        "|---|---|---|---:|---:|---:|---:|",
    ]
    common = [
        r
        for r in rows
        if r["bridge"] == "common"
        and r["target"] == (10000000 if r["axis"] == "work" else 128)
    ]
    groups = sorted(
        {
            (r["spot_file"], r["representation"], r["axis"], *(r[f] for f in FACTORS))
            for r in common
        }
    )
    for group in groups:
        selected = [
            r
            for r in common
            if (
                r["spot_file"],
                r["representation"],
                r["axis"],
                *(r[f] for f in FACTORS),
            )
            == group
        ]
        numbers = [math.fsum(r[k] for r in selected) / len(selected) for k in PRIMARY]
        lines.append(
            f"| {Path(group[0]).stem} / {group[1]} | {group[2]} | "
            f"{' / '.join(group[3:])} | "
            + " | ".join(f"{v:.9g}" for v in numbers)
            + " |"
        )
    (output / "tables.md").write_text("\n".join(lines) + "\n")
    summary["files"]["tables.md"] = digest(output / "tables.md")
    (output / "summary.json").write_text(
        json.dumps(summary, sort_keys=True, indent=2) + "\n"
    )
    return summary
