"""Scientific figures from complete own fallback tables, never new measurements."""

import importlib
import itertools
from pathlib import Path
from typing import Any

import numpy as np

from poker_ai.evaluation.controlled_reply_inputs import modes
from poker_ai.evaluation.window_fallback_inputs import FallbackInputs
from poker_ai.evaluation.window_fallback_math import LABELS

METRICS = ("exact_exploitability", "within_partition_gain", "extra_information_gap")
NAMES = ("Exact total", "Within groups", "Extra exact info")
COLORS = ("tab:blue", "tab:orange", "tab:green")
WINDOWS = {"suffix_5m_10m": "5–10m", "suffix_9m_10m": "9–10m"}
FILLS = {"fill_0": "seat0", "fill_1": "seat1", "fill_both": "both"}


def mode_label(mode: tuple[str, str]) -> str:
    return mode[0] + ("/u" if mode[1] == "uniform" else "/l")


def groups(data: FallbackInputs) -> list[tuple[str, str]]:
    return list(
        itertools.product(data.config["spot_files"], data.config["representations"])
    )


def self_changes(
    plt: Any,
    data: FallbackInputs,
    raw: list[dict[str, Any]],
    means: list[dict[str, Any]],
    output: Path,
    scope: str,
    traversal: str,
) -> None:
    conditions = list(
        itertools.product(
            modes(data.config), data.config["suffix_variants"], LABELS[1:]
        )
    )
    fig, axes = plt.subplots(2, 2, figsize=(18, 20), squeeze=False)
    for ax, (game, name) in zip(axes.flat, groups(data), strict=True):
        chosen = {
            (
                r["regret_rule"],
                r["average_weight"],
                r["window_variant"],
                r["fill_label"],
            ): r
            for r in means
            if (r["spot_file"], r["representation"], r["traversal"])
            == (game, name, traversal)
        }
        for m, (metric, title, color) in enumerate(
            zip(METRICS, NAMES, COLORS, strict=True)
        ):
            key = metric + "_difference_pct_initial_pot"
            y = np.arange(len(conditions)) + (m - 1) * 0.18
            values = [
                chosen[*mode, window, fill][key] for mode, window, fill in conditions
            ]
            ax.scatter(values, y, color=color, marker="D", s=24, label=title, zorder=4)
            if traversal == "external":
                for i, (mode, window, fill) in enumerate(conditions):
                    points = [
                        r[key]
                        for r in raw
                        if (
                            r["spot_file"],
                            r["representation"],
                            r["traversal"],
                            r["regret_rule"],
                            r["average_weight"],
                            r["window_variant"],
                            r["fill_label"],
                        )
                        == (game, name, traversal, *mode, window, fill)
                    ]
                    ax.scatter(
                        points,
                        [y[i]] * len(points),
                        color=color,
                        s=10,
                        alpha=0.3,
                        zorder=3,
                    )
        ax.axvline(0, color="gray", linestyle=":", linewidth=1)
        ax.set_yticks(
            range(len(conditions)),
            [
                mode_label(mode) + " " + WINDOWS[window] + " " + FILLS[fill]
                for mode, window, fill in conditions
            ],
            fontsize=8,
        )
        ax.invert_yaxis()
        ax.set_title(Path(game).stem + " / " + name, fontsize=10)
        ax.set_xlabel("Fill minus raw same window (percentage points of initial pot)")
        ax.grid(axis="x", alpha=0.2)
    axes[0, 0].legend(fontsize=9, loc="best")
    fig.suptitle(scope + " — self changes, " + traversal, fontsize=13)
    fig.text(
        0.5,
        0.01,
        "All three seat-fill masks and both windows. "
        + (
            "Diamonds: three-seed means; small points: raw seeds; "
            "no confidence intervals."
            if traversal == "external"
            else "Full controls run once."
        )
        + " No-op duplicates retained.",
        ha="center",
        fontsize=10,
    )
    fig.tight_layout(rect=(0, 0.035, 1, 0.96))
    fig.savefig(output / ("self-changes-" + traversal + ".png"), dpi=140)
    plt.close(fig)


def fixed_changes(
    plt: Any,
    data: FallbackInputs,
    means: list[dict[str, Any]],
    output: Path,
    scope: str,
    traversal: str,
) -> None:
    order = modes(data.config)
    conditions = list(itertools.product(order, data.config["suffix_variants"]))
    values = [
        abs(r["gain_difference_pct_initial_pot"])
        for r in means
        if r["traversal"] == traversal and r["fill_label"] == "fill_both"
    ]
    # Display floor only: numerical control noise stays neutral. Never alter data.
    maximum = max(1e-6, max(values, default=0))
    fig, axes = plt.subplots(2, 4, figsize=(22, 13), squeeze=False)
    color = None
    for target in (0, 1):
        for column, (game, name) in enumerate(groups(data)):
            ax = axes[target, column]
            chosen = {
                (
                    r["regret_rule"],
                    r["average_weight"],
                    r["window_variant"],
                    r["opponent_regret_rule"],
                    r["opponent_average_weight"],
                ): r
                for r in means
                if (
                    r["spot_file"],
                    r["representation"],
                    r["traversal"],
                    r["target"],
                    r["fill_label"],
                )
                == (game, name, traversal, target, "fill_both")
            }
            matrix = np.array(
                [
                    [
                        chosen[*own, window, *opponent][
                            "gain_difference_pct_initial_pot"
                        ]
                        for opponent in order
                    ]
                    for own, window in conditions
                ]
            )
            color = ax.imshow(
                matrix, aspect="auto", cmap="coolwarm", vmin=-maximum, vmax=maximum
            )
            ax.set_yticks(
                range(8),
                [
                    mode_label(mode) + " " + WINDOWS[window]
                    for mode, window in conditions
                ],
                fontsize=8,
            )
            ax.set_xticks(
                range(4),
                [mode_label(mode) for mode in order],
                rotation=45,
                ha="right",
                fontsize=8,
            )
            ax.set_title(
                f"{Path(game).stem} / {name}\nresponding seat {target}", fontsize=9
            )
            ax.set_xlabel("Fixed saved whole-average opponent", fontsize=8)
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
        + " — fixed-opponent changes, "
        + traversal
        + "\nBoth-fill minus raw window; negative gain change means better own EV",
        fontsize=12,
    )
    fig.text(
        0.5,
        0.01,
        "All opponents and both seats. "
        + (
            "Three-seed means; no confidence intervals."
            if traversal == "external"
            else "Full controls once."
        )
        + " Symmetric color range has a display-only minimum ±1e-6 percentage points.",
        ha="center",
        fontsize=9,
    )
    fig.tight_layout(rect=(0, 0.04, 0.94, 0.94))
    bar = fig.add_axes((0.955, 0.2, 0.012, 0.6))
    fig.colorbar(
        color, cax=bar, label="Change in unilateral gain (percentage points of pot)"
    )
    fig.savefig(output / ("fixed-opponent-changes-" + traversal + ".png"), dpi=140)
    plt.close(fig)


def render(
    data: FallbackInputs,
    raw: list[dict[str, Any]],
    means: list[dict[str, Any]],
    fixed_means: list[dict[str, Any]],
    output: Path,
    scope: str,
) -> None:
    mpl = importlib.import_module("matplotlib")
    mpl.use("Agg")
    plt = importlib.import_module("matplotlib.pyplot")
    for traversal in data.config["traversals"]:
        self_changes(plt, data, raw, means, output, scope, traversal)
        fixed_changes(plt, data, fixed_means, output, scope, traversal)
