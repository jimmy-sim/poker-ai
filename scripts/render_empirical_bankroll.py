"""Render measured-return risk with explicit fitted-law limitations."""

import argparse
import csv
import hashlib
import importlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from poker_ai.risk.bankroll import ReturnLaw
from poker_ai.risk.empirical import confidence_sizing, read_own_blocks
from poker_ai.validation.five_card import source_provenance


def render(directory: Path, root: Path) -> None:
    path = directory / "empirical-bankroll.json"
    report = json.loads(path.read_text())
    if report["status"] != "completed":
        raise ValueError("requires complete measured-return simulation")
    config = report["config"]
    match_path = root / config["match_report"]
    if (
        report["input_match_report_sha256"]
        != hashlib.sha256(match_path.read_bytes()).hexdigest()
    ):
        raise ArithmeticError("measured match-report bytes changed")
    match_config, blocks = read_own_blocks(match_path, config["opponents"])
    bb = match_config["rules"]["big_blind"]
    expected_keys = {
        (name, fee, sizing)
        for name in config["opponents"]
        for fee in config["flat_fee_bb_per_100_hands"]
        for sizing in config["sizing"]
    }
    keys = [
        (r["opponent"], r["fee_bb_per_100_hands"], r["sizing"]) for r in report["rows"]
    ]
    if len(keys) != len(expected_keys) or set(keys) != expected_keys:
        raise ArithmeticError("duplicate/missing measured risk cell")
    flat = []
    for r in report["rows"]:
        block = blocks[r["opponent"]]
        values = block["values"]
        fee = r["fee_bb_per_100_hands"] * bb / 100
        unit = block["loss_bound_chips_per_hand"] + fee
        law = ReturnLaw((values - fee) / unit, np.full(len(values), 1 / len(values)))
        lower, robust = confidence_sizing(
            float(values.mean()),
            block["loss_bound_chips_per_hand"],
            fee,
            len(values),
            len(blocks),
            config["family_alpha"],
            config["kelly_cap"],
        )
        plugin = law.kelly(config["kelly_cap"])
        fraction = {
            "half_plugin": plugin / 2,
            "full_plugin": plugin,
            "confidence_robust": robust,
        }[r["sizing"]]
        for actual, expected in (
            (r["fraction"], fraction),
            (r["plugin_optimal_fraction"], plugin),
            (r["confidence_robust_fraction"], robust),
            (r["familywise_lower_net_mbb_per_hand"], lower / bb * 1000),
            (r["measured_net_mbb_per_hand"], law.mean * unit / bb * 1000),
            (r["expected_log_growth_per_block"], law.log_growth(fraction)),
        ):
            if not math.isclose(actual, expected, abs_tol=1e-12, rel_tol=0):
                raise ArithmeticError("measured risk analytic metric changed")
        sim = r["simulation"]
        half = (
            config["horizon_blocks"]
            * float(np.ptp(np.log1p(fraction * law.outcomes)))
            * math.sqrt(math.log(2 * len(keys) / 0.001) / (2 * config["paths"]))
        )
        if (
            abs(
                sim["mean_terminal_log_wealth"]
                - config["horizon_blocks"] * law.log_growth(fraction)
            )
            > half + 1e-10
        ):
            raise ArithmeticError("measured risk simulated mean-growth check failed")
        row: dict[str, Any] = {
            key: value for key, value in r.items() if key != "simulation"
        }
        for event in ("threshold_crossing", "drawdown_exceedance", "terminal_loss"):
            data = sim[event]
            if (
                data["paths"] != config["paths"]
                or not 0 <= data["count"] <= data["paths"]
                or data["probability"] != data["count"] / data["paths"]
            ):
                raise ArithmeticError("measured event count inconsistency")
            row.update(
                {
                    f"{event}_{key}": data[key]
                    for key in ("count", "paths", "probability")
                }
            )
        flat.append(row)
    csv_path = directory / "empirical-bankroll-cells.csv"
    with csv_path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(flat[0]))
        writer.writeheader()
        writer.writerows(flat)
    matplotlib = importlib.import_module("matplotlib")
    matplotlib.use("Agg")
    plt = importlib.import_module("matplotlib.pyplot")
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), constrained_layout=True)
    for name in config["opponents"]:
        selected = [
            r
            for r in report["rows"]
            if r["opponent"] == name and r["sizing"] == "full_plugin"
        ]
        line = axes[0].plot(
            [r["fee_bb_per_100_hands"] for r in selected],
            [r["measured_net_mbb_per_hand"] for r in selected],
            marker="o",
            label=name,
        )[0]
        axes[0].plot(
            [r["fee_bb_per_100_hands"] for r in selected],
            [r["familywise_lower_net_mbb_per_hand"] for r in selected],
            color=line.get_color(),
            linestyle="--",
        )
    axes[0].axhline(0, color="black", linewidth=0.7)
    axes[0].set_xlabel("Illustrative fixed fee (bb per 100 hands)")
    axes[0].set_ylabel("mbb per hand")
    axes[0].set_title("Measured point means; dashed: familywise lower bounds")
    axes[0].legend(fontsize=8)
    selected = [
        next(
            r
            for r in report["rows"]
            if r["opponent"] == name
            and r["fee_bb_per_100_hands"] == 0
            and r["sizing"] == "full_plugin"
        )
        for name in config["opponents"]
    ]
    x = np.arange(len(selected))
    axes[1].bar(
        x - 0.15,
        [r["plugin_optimal_fraction"] for r in selected],
        0.3,
        label="Fitted-law optimum",
    )
    axes[1].bar(
        x + 0.15,
        [r["confidence_robust_fraction"] for r in selected],
        0.3,
        label="Confidence-robust",
    )
    axes[1].set_xticks(x, [r["opponent"].replace("_", "\n") for r in selected])
    axes[1].set_ylabel("Fraction in the conditional block-scaling model")
    axes[1].set_title("Fitted favorable mean does not establish an edge")
    axes[1].legend(fontsize=8)
    for axis in axes:
        axis.grid(axis="y", alpha=0.2)
    fig.suptitle(
        "Measured own baselines: 1,000 original deck clusters; "
        "resampling is not independent validation"
    )
    figures = []
    for suffix in ("png", "svg"):
        figure = directory / f"empirical-bankroll.{suffix}"
        fig.savefig(figure, dpi=160, metadata={"Date": None} if suffix == "svg" else {})
        figures.append(figure)
    plt.close(fig)
    no_fee = [
        r
        for r in report["rows"]
        if r["fee_bb_per_100_hands"] == 0 and r["sizing"] == "full_plugin"
    ]
    zero_robust = sum(r["confidence_robust_fraction"] == 0 for r in no_fee)
    table = (
        "| Own opponent | Gross mbb/hand | Five-opponent lower bound | "
        "Fitted fraction | Robust fraction |\n"
        "| --- | ---: | ---: | ---: | ---: |\n"
    )
    for r in no_fee:
        table += (
            f"| {r['opponent']} | {r['measured_net_mbb_per_hand']:+,.1f} | "
            f"{r['familywise_lower_net_mbb_per_hand']:+,.1f} | "
            f"{r['plugin_optimal_fraction']:.4f} | "
            f"{r['confidence_robust_fraction']:.4f} |\n"
        )
    body = (
        "### Measured-return risk and fee sensitivity\n\n"
        "All five own scripted opponents are included; OpenSpiel and Slumbot outcomes "
        "are excluded. Each fitted law contains 1,000 original deck clusters, "
        "each retaining three frozen own policies × two seats. A simulated step is "
        "one **six-hand block**, not one independent hand.\n\n" + table + "\n"
        f"**{zero_robust}/{len(no_fee)} confidence-robust fractions "
        "are zero before fees.** "
        "The positive fitted fractions in some matchups depend on the empirical "
        "return law being correct; resampling does not independently establish its "
        "mean. The study includes half/full fitted sizing and confidence-robust "
        f"sizing across {len(report['rows'])} cells, each with {config['paths']:,} "
        f"paths of {config['horizon_blocks']:,} blocks. Five-opponent one-sided "
        "Bonferroni–Hoeffding bounds cover the same fixed target as the original "
        "duplicate study, not a population of training seeds.\n\n"
        "The 0/5/10 bb/100 fixed costs are illustrative, not a real site's "
        "pot-rake schedule. No positive edge was established by the primary match "
        "test even before fees; positive fee-adjusted point estimates cannot prove "
        "an edge survives realistic rake.\n\n"
        "![Measured-return risk sensitivity]"
        "(results/extensions/empirical-bankroll.png)\n"
    )
    (directory / "empirical-summary.md").write_text(body)
    summary = directory / "summary-body.md"
    text = (
        summary.read_text()
        .split("### Measured-return risk and fee sensitivity", 1)[0]
        .rstrip()
    )
    summary.write_text(text + "\n\n" + body)
    audit = {
        "status": "passed",
        "cells": len(keys),
        "zero_robust_before_fee": zero_robust,
        "source": source_provenance(
            root,
            root / "configs/empirical-bankroll.json",
            entrypoints=("scripts/render_empirical_bankroll.py",),
        ),
        "input_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "artifacts_sha256": {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [csv_path, *figures, directory / "empirical-summary.md"]
        },
    }
    (directory / "empirical-audit.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n"
    )
    manifest_path = directory / "render-manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["inputs_sha256"][path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest["artifacts_sha256"].update(
        {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [
                summary,
                csv_path,
                *figures,
                directory / "empirical-summary.md",
                directory / "empirical-audit.json",
            ]
        }
    )
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(
        f"passed: {len(keys)} measured-return cells "
        "and original block/uncertainty checks"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=Path("results/extensions"))
    args = parser.parse_args()
    render(args.directory, Path(__file__).resolve().parents[1])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
