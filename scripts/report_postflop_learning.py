"""Replay frozen own policies and render strength diagnostics without training."""

import argparse
import importlib
import json
from pathlib import Path
from typing import Any

from poker_ai.postflop.report import summarize
from poker_ai.reproducibility import runtime_environment
from poker_ai.validation.five_card import source_provenance


def render(
    root: Path, manifest: dict[str, Any], output: Path, manifest_path: Path
) -> dict[str, Any]:
    result = summarize(root, manifest)
    result["analysis_source"] = source_provenance(
        root, manifest_path, entrypoints=("scripts/report_postflop_learning.py",)
    )
    result["analysis_environment"] = runtime_environment()
    output.mkdir(parents=True, exist_ok=True)
    (output / "summary.json").write_text(
        json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n"
    )
    lines = [
        "# Own postflop learning diagnostic",
        "",
        "Audit: **passed**. Held-out learning gate: **"
        + ("passed" if result["learning_gate_passed"] else "FAILED")
        + "**.",
        "",
        "Exploitability is exact restricted-game NashConv/2, divided by the "
        "initial pot.",
        "Each range has only two physical combos per seat. "
        "Each game receives its own training.",
        "",
        "| Experiment | Spot | Encoding | Median ε/pot | Worst seed | "
        "Min average coverage | Initial-only rows (max) |",
        "|---|---|---|---:|---:|---:|---:|",
    ]
    for row in result["summaries"]:
        lines.append(
            f"| {row['experiment']} | {row['spot']} | {row['encoding']} | "
            f"{row['median_epsilon_pot']:.9g} | {row['max_epsilon_pot']:.9g} | "
            f"{row['minimum_uniform_average_coverage']:.2%} | "
            f"{row['maximum_initial_only_rows']} |"
        )
    lines.extend(
        [
            "",
            "The preset median target is ≤0.01 pots; worst seed ≤0.025; coverage ≥95%.",
            "Initialization calculates every row once; 100% average-row coverage "
            "does not mean every row was subsequently sampled.",
            "",
            "## Cross-play against own full-tree CFR+ control",
            "",
            "Positive EV favors the tested strategy; averaged over its two seats. "
            "This is not a best-response metric.",
            "The row L1 gap uses uniform-policy decision reach; range 0–2. "
            "Different equilibria can have different actions.",
            "",
            "| Experiment | Spot | Encoding | Seed | EV/pot | Weighted row L1 |",
            "|---|---|---|---:|---:|---:|",
        ]
    )
    for row in result["crossplay"]:
        lines.append(
            f"| {row['experiment']} | {row['spot']} | {row['encoding']} | "
            f"{row['seed']} | {row['ev_vs_own_full_control_pot']:.9g} | "
            f"{row['uniform_reach_weighted_row_l1_vs_own_full']:.6g} |"
        )
    lines.extend(
        [
            "",
            f"Replayed {result['independently_checked_policies']} independently "
            "checked frozen policies; maximum own replay error "
            f"{result['maximum_own_replay_error_chips']:.3g} chips.",
            "Reference comparison hashes are linked in summary.json; "
            "reference strategies never enter training.",
            "Public-board collision counts, actual sampled node counts and "
            "initialization work are in summary.json.",
            "",
            "A failed learning gate blocks the preregistered global comparison. "
            "These numbers do not establish full-game strength or profitability.",
            "",
        ]
    )
    (output / "tables.md").write_text("\n".join(lines))

    # Plotting is optional; baseline setup/type checks need no research extra.
    matplotlib = importlib.import_module("matplotlib")
    matplotlib.use("Agg")
    plt = importlib.import_module("matplotlib.pyplot")

    entries = {
        e["name"]: json.loads((root / e["report"]).read_text())
        for e in manifest["experiments"]
    }
    reports = [entries["linear-warm"], entries["representations"], entries["heldout"]]
    spots = sorted({r["spot"] for report in reports for r in report["rows"]})
    colors = {"exact": "tab:blue", "legacy_b8": "tab:orange", "public_b8": "tab:green"}
    labels = {
        "exact": "exact cards",
        "legacy_b8": "existing potential-8",
        "public_b8": "potential-8 + public board",
    }
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), constrained_layout=True)
    for spot, ax in zip(spots, axes.flat, strict=True):
        rows = [r for report in reports for r in report["rows"] if r["spot"] == spot]
        for encoding, color in colors.items():
            for seed in reports[0]["config"]["seeds"]:
                selected = [
                    r
                    for r in rows
                    if r["encoding"] == encoding
                    and r["method"] == "external"
                    and r["seed"] == seed
                ]
                selected.sort(key=lambda r: r["iteration"])
                if selected:
                    ax.plot(
                        [r["iteration"] for r in selected],
                        [
                            max(r["exploitability_pot_fraction"], 1e-12)
                            for r in selected
                        ],
                        color=color,
                        alpha=0.55,
                        marker=".",
                        label=labels[encoding]
                        if seed == reports[0]["config"]["seeds"][0]
                        else None,
                    )
        ax.axhline(0.01, color="black", linestyle="--", label="median target (3 seeds)")
        ax.set(
            xscale="log",
            yscale="log",
            title=spot,
            xlabel="Own sampled iterations (unequal cost to full-tree CFR+)",
            ylabel="Exact restricted exploitability / initial pot",
        )
        ax.grid(alpha=0.2)
        ax.legend(fontsize=8)
    gate_label = "passed" if result["learning_gate_passed"] else "FAILED"
    fig.suptitle(
        "Fixed linear weighting + one exact initial expectation; all 3 seeds\n"
        f"Own training per game; tiny ranges; held-out median gate {gate_label}"
    )
    fig.savefig(output / "learning-curves.png", dpi=170)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6), constrained_layout=True)
    for ax, spot in zip(axes, ("dev_low_oop", "dev_medium_oop"), strict=True):
        for name, marker, color in zip(
            ("uniform", "warm", "linear", "linear-warm"),
            ("o", "s", "^", "D"),
            ("tab:blue", "tab:orange", "tab:green", "tab:red"),
            strict=True,
        ):
            rows = [
                r
                for r in entries[name]["rows"]
                if r["spot"] == spot and r["method"] == "external"
            ]
            for seed in entries[name]["config"]["seeds"]:
                selected = [r for r in rows if r["seed"] == seed]
                ax.plot(
                    [
                        r["nodes_visited_or_full_node_equivalent"]
                        + r["warm_node_equivalent"]
                        for r in selected
                    ],
                    [max(r["exploitability_pot_fraction"], 1e-12) for r in selected],
                    alpha=0.5,
                    marker=marker,
                    color=color,
                    label=name if seed == entries[name]["config"]["seeds"][0] else None,
                )
        ax.axhline(0.01, color="black", linestyle="--")
        ax.set(
            xscale="log",
            yscale="log",
            title=spot,
            xlabel="Sampled node visits + initialization node equivalent",
            ylabel="Exact restricted exploitability / initial pot",
        )
        ax.grid(alpha=0.2)
        ax.legend(fontsize=8)
    fig.suptitle(
        "All four preregistered controls; fixed 300k iterations, all 3 seeds\n"
        "Work counts include initialization; "
        "curves do not imply equal-cost full-tree iterations"
    )
    fig.savefig(output / "factorial-work.png", dpi=170)
    plt.close(fig)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest", type=Path, default=Path("configs/holdem-learning-evidence.json")
    )
    parser.add_argument(
        "--output", type=Path, default=Path("results/holdem-learning/report")
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    result = render(
        root, json.loads(args.manifest.read_text()), args.output, args.manifest
    )
    print(
        "audit passed; held-out learning gate "
        f"passed={result['learning_gate_passed']}; tables/plots: {args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
