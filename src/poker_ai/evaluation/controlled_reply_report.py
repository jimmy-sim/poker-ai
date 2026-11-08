"""All-source street accounting and ordered fixed-opponent gain reports."""

import importlib
import json
import math
from pathlib import Path
from typing import Any

from poker_ai.evaluation.controlled_reply_inputs import Inputs, modes
from poker_ai.postflop.learning_report import write_csv
from poker_ai.postflop.matrix import MatrixTree
from poker_ai.postflop.river_study import digest

FIGURES = (
    "within-streets-full.png",
    "within-streets-external.png",
    "fixed-opponent-full.png",
    "fixed-opponent-external.png",
)


def pots(data: Inputs) -> dict[str, float]:
    result = {}
    for (game, _), context in data.contexts.items():
        if not isinstance(context.exact, MatrixTree):
            raise ValueError("poker report requires its source pot")
        result[game] = float(context.exact.source.spot.pot)
    return result


def rows(
    saved: dict[str, Any], pot: dict[str, float]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    self_rows, cross_rows = [], []
    for item in saved["self_profiles"]:
        for response in item["responses"]:
            self_rows.append(
                dict(
                    **item["case"],
                    profile_id=item["id"],
                    target=response["target"],
                    gain_chips=response["gain_chips"],
                    turn_loss_chips=response["street_losses_chips"]["TURN"],
                    river_loss_chips=response["street_losses_chips"]["RIVER"],
                    gain_pct_initial_pot=100
                    * response["gain_chips"]
                    / pot[item["case"]["spot_file"]],
                    root_chips=response["restricted_reply_value_chips"],
                    baseline_chips=response["baseline_value_chips"],
                    rows=response["owned_rows"],
                    reply_sha256=response["reply_sha256"],
                )
            )
    for item in saved["crosses"]:
        for target, response in enumerate(item["responses"]):
            own, opponent = (
                (item["first_mode"], item["second_mode"])
                if target == 0
                else (item["second_mode"], item["first_mode"])
            )
            cross_rows.append(
                dict(
                    **item["group"],
                    **response,
                    own_regret_rule=own[0],
                    own_average_weight=own[1],
                    opponent_regret_rule=opponent[0],
                    opponent_average_weight=opponent[1],
                    gain_pct_initial_pot=100
                    * response["gain_chips"]
                    / pot[item["group"]["spot_file"]],
                )
            )
    return self_rows, cross_rows


def means(
    data: Inputs, saved: dict[str, Any], pot: dict[str, float]
) -> list[dict[str, Any]]:
    result = []
    for game in data.config["spot_files"]:
        for name in data.config["representations"]:
            for traversal in data.config["traversals"]:
                for clip, average in modes(data.config):
                    chosen = [
                        r
                        for r in saved["self_profiles"]
                        if r["case"]["spot_file"] == game
                        and r["case"]["representation"] == name
                        and r["case"]["traversal"] == traversal
                        and (r["case"]["regret_rule"], r["case"]["average_weight"])
                        == (clip, average)
                    ]
                    expected = (
                        data.config["seeds"] if traversal == "external" else [None]
                    )
                    if (
                        sorted(
                            (r["case"]["seed"] for r in chosen), key=lambda s: s or 0
                        )
                        != expected
                    ):
                        raise ArithmeticError(
                            "report cannot average an incomplete source group"
                        )
                    result.append(
                        dict(
                            spot_file=game,
                            representation=name,
                            traversal=traversal,
                            regret_rule=clip,
                            average_weight=average,
                            within_pct_initial_pot=100
                            * math.fsum(
                                r["within_partition_gain_chips"] for r in chosen
                            )
                            / len(chosen)
                            / pot[game],
                            turn_pct_initial_pot=100
                            * math.fsum(
                                r["street_losses_chips"]["TURN"] for r in chosen
                            )
                            / len(chosen)
                            / pot[game],
                            river_pct_initial_pot=100
                            * math.fsum(
                                r["street_losses_chips"]["RIVER"] for r in chosen
                            )
                            / len(chosen)
                            / pot[game],
                            source_ids=[r["id"] for r in chosen],
                            count=len(chosen),
                        )
                    )
    return result


def render(
    data: Inputs,
    saved: dict[str, Any],
    output: Path,
    pot: dict[str, float],
    *,
    scope: str = "Frozen controlled policies",
) -> None:
    mpl = importlib.import_module("matplotlib")
    mpl.use("Agg")
    plt = importlib.import_module("matplotlib.pyplot")
    import numpy as np

    grouped = [
        (g, n)
        for g in data.config["spot_files"]
        for n in data.config["representations"]
    ]
    order = modes(data.config)
    labels = [clip + "/" + average for clip, average in order]
    average_rows = means(data, saved, pot)
    _, crossed = rows(saved, pot)
    for traversal in data.config["traversals"]:
        fig, axes = plt.subplots(2, 2, figsize=(13, 9), squeeze=False)
        for ax, (game, name) in zip(axes.flat, grouped, strict=True):
            selected = [
                r
                for r in average_rows
                if (r["spot_file"], r["representation"], r["traversal"])
                == (game, name, traversal)
            ]
            by_mode = {(r["regret_rule"], r["average_weight"]): r for r in selected}
            turns = [by_mode[m]["turn_pct_initial_pot"] for m in order]
            rivers = [by_mode[m]["river_pct_initial_pot"] for m in order]
            x = np.arange(4)
            ax.bar(x, turns, label="Turn loss")
            ax.bar(x, rivers, bottom=turns, label="River loss")
            if traversal == "external":
                for i, mode in enumerate(order):
                    profiles = sorted(
                        [
                            p
                            for p in saved["self_profiles"]
                            if p["case"]["spot_file"] == game
                            and p["case"]["representation"] == name
                            and p["case"]["traversal"] == traversal
                            and (p["case"]["regret_rule"], p["case"]["average_weight"])
                            == mode
                        ],
                        key=lambda p: p["case"]["seed"],
                    )
                    ax.scatter(
                        [i + (j - 1) * 0.06 for j in range(3)],
                        [
                            100 * p["within_partition_gain_chips"] / pot[game]
                            for p in profiles
                        ],
                        color="black",
                        s=14,
                        zorder=4,
                    )
            ax.set_xticks(x, labels, rotation=20, ha="right")
            ax.set_title(Path(game).stem + " / " + name, fontsize=9)
            ax.set_ylabel("Within-partition gain (% initial pot)")
            ax.grid(axis="y", alpha=0.2)
        axes[0, 0].legend()
        fig.suptitle(
            scope + " — " + traversal + "\nSaved prefix / optimal own reply suffix; "
            "street accounting is not a training-cause attribution",
            fontsize=10,
        )
        fig.text(
            0.5,
            0.01,
            "Linear regret weights; mode = regret rule / average weight. "
            + (
                "Means of 3 fixed seeds; black dots are individual totals, "
                "not confidence intervals."
                if traversal == "external"
                else "Deterministic full controls, run once."
            ),
            ha="center",
            fontsize=8,
        )
        fig.tight_layout(rect=(0, 0.04, 1, 0.93))
        fig.savefig(output / ("within-streets-" + traversal + ".png"), dpi=140)
        plt.close(fig)
        selected_cross = [r for r in crossed if r["traversal"] == traversal]
        maximum = max((r["gain_pct_initial_pot"] for r in selected_cross), default=1.0)
        maximum = max(maximum, 1e-12)
        fig, axes = plt.subplots(2, 4, figsize=(21, 10), squeeze=False)
        for column, (game, name) in enumerate(grouped):
            for target in (0, 1):
                ax = axes[target, column]
                matrix = np.zeros((4, 4))
                for i, own in enumerate(order):
                    for j, opponent in enumerate(order):
                        values = [
                            r["gain_pct_initial_pot"]
                            for r in selected_cross
                            if (r["spot_file"], r["representation"], r["target"])
                            == (game, name, target)
                            and (r["own_regret_rule"], r["own_average_weight"]) == own
                            and (
                                r["opponent_regret_rule"],
                                r["opponent_average_weight"],
                            )
                            == opponent
                        ]
                        if len(values) != (3 if traversal == "external" else 1):
                            raise ArithmeticError(
                                "heatmap crossed seed inventory incomplete"
                            )
                        matrix[i, j] = math.fsum(values) / len(values)
                color = ax.imshow(matrix, vmin=0, vmax=maximum, cmap="viridis")
                ax.set_xticks(range(4), labels, rotation=45, ha="right", fontsize=7)
                ax.set_yticks(range(4), labels, fontsize=7)
                ax.set_xlabel("Fixed opponent mode", fontsize=8)
                ax.set_ylabel("Own mode", fontsize=8)
                ax.set_title(
                    f"{Path(game).stem} / {name}\nresponding seat {target}", fontsize=8
                )
                for i, j in np.ndindex(matrix.shape):
                    ax.text(
                        j,
                        i,
                        f"{matrix[i, j]:.3g}",
                        ha="center",
                        va="center",
                        fontsize=8,
                        color="white" if matrix[i, j] < maximum * 0.5 else "black",
                    )
        fig.suptitle(
            scope
            + " — fixed-opponent within gain, "
            + traversal
            + "\nLower is better; % initial pot; "
            + (
                "means of 3 fixed seeds, no confidence intervals"
                if traversal == "external"
                else "deterministic controls"
            ),
            fontsize=11,
        )
        fig.tight_layout(rect=(0, 0, 0.94, 0.93))
        bar = fig.add_axes((0.955, 0.2, 0.012, 0.6))
        fig.colorbar(color, cax=bar, label="Within gain (% initial pot)")
        fig.savefig(output / ("fixed-opponent-" + traversal + ".png"), dpi=140)
        plt.close(fig)


def write_report(
    data: Inputs,
    saved: dict[str, Any],
    output: Path,
    *,
    plots: bool = True,
    pot: dict[str, float] | None = None,
    scope: str = "Frozen controlled policies",
) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    pot = pots(data) if pot is None else pot
    self_rows, cross_rows = rows(saved, pot)
    average_rows = means(data, saved, pot)
    write_csv(output / "self-targets.csv", self_rows)
    write_csv(output / "crossed-targets.csv", cross_rows)
    write_csv(output / "street-means.csv", average_rows)
    if plots:
        render(data, saved, output, pot, scope=scope)
    lines = [
        "# Frozen controlled-policy within gains",
        "",
        scope + ". All modes; linear regret weights.",
        "Full controls once; sampled arithmetic means of three fixed seeds. "
        "Units: percent initial pot.",
        "",
        "| Game / encoding | Traversal | Regret / average "
        "| Within | Turn loss | River loss |",
        "|---|---|---|---:|---:|---:|",
    ]
    for row in average_rows:
        lines.append(
            f"| {Path(row['spot_file']).stem} / {row['representation']} | "
            f"{row['traversal']} | " + f"{row['regret_rule']} / "
            f"{row['average_weight']} | "
            f"{row['within_pct_initial_pot']:.9g} | "
            + f"{row['turn_pct_initial_pot']:.9g} | "
            f"{row['river_pct_initial_pot']:.9g} |"
        )
    lines += [
        "",
        "Street losses use saved-prefix reach and an optimal own reply suffix; "
        "they are not a causal feature attribution.",
        "Fixed-opponent crossed EV/gain identities and every seed/target appear "
        "in crossed-targets.csv. No default or global admission.",
    ]
    (output / "tables.md").write_text("\n".join(lines) + "\n")
    files = ["self-targets.csv", "crossed-targets.csv", "street-means.csv", "tables.md"]
    summary = dict(
        scope=scope,
        source_profiles=64,
        target_traces=len(self_rows),
        crossed_target_conditions=len(cross_rows),
        figures=[name for name in FIGURES if (output / name).exists()],
        files={name: digest(output / name) for name in files},
        no_training_performed=True,
        interpretation=(
            "fixed saved policies only; no causal street/default/global claim"
        ),
    )
    (output / "summary.json").write_text(
        json.dumps(summary, sort_keys=True, indent=2) + "\n"
    )
    return summary
