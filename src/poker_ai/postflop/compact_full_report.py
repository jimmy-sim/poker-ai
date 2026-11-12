"""Authenticate the complete full-control result; never admit sampled learning."""

import importlib
import json
from pathlib import Path
from typing import Any

from poker_ai.postflop import compact_full_artifacts as artifacts
from poker_ai.postflop.compact_full_clock import measurement
from poker_ai.postflop.compact_full_gate import checked_path, require_admission
from poker_ai.postflop.compact_full_run import replay
from poker_ai.postflop.public_range_acceptance import assess_full
from poker_ai.postflop.public_range_definition import contract
from poker_ai.postflop.public_report import write_csv
from poker_ai.postflop.river_study import digest
from poker_ai.solver_validation.compact_full import validate


def render(
    root: Path, own_path: Path, native_path: Path, output: Path
) -> dict[str, Any]:
    replay(root, own_path)
    own = json.loads(own_path.read_text())
    audit = json.loads(native_path.read_text())
    if own["software_only"] is not False:
        raise ValueError("software fixture never supplies scientific full admission")
    require_admission(root, checked_path(root, own["admission"]))
    validate(own, audit, digest(own_path))
    artifacts.check_source(root, audit["source"])
    own_clock = measurement(own_path, "own")
    audit_clock = measurement(native_path, "native")
    rows = [
        dict(
            **{
                k: r[k]
                for k in (*artifacts.IDENTITY, "context_sha256", "total_node_work")
            },
            **r["metrics"],
        )
        for r in own["rows"]
    ]
    config = contract(root)
    assessment = assess_full(
        rows,
        own["partitions"],
        audit["comparisons"],
        config,
        elapsed_seconds=own_clock["seconds"],
        audit_seconds=audit_clock["seconds"],
    )
    directory = output.parent / "report"
    if directory.exists():
        raise FileExistsError("retain prior compact full report")
    directory.mkdir()
    write_csv(directory / "all-checkpoints.csv", rows)
    write_csv(directory / "layouts.csv", own["partitions"])
    candidate = config["candidate"]
    differences = []
    lines = [
        "# Compact full-control results",
        "",
        "Known games only. Lower exploitability is better. "
        "No sampled study or default change.",
        "",
        "| Game | Representation | Final exploitability (% pot) | "
        "Rows | Key bytes | Table bytes |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for spot in config["spot_files"]:
        for name in config["representations"]:
            selected = [
                r
                for r in rows
                if r["spot_file"] == spot and r["representation"] == name
            ]
            final = selected[-1]
            layout = next(
                d
                for d in own["partitions"]
                if d["spot_file"] == spot and d["representation"] == name
            )
            lines.append(
                f"| {Path(spot).stem} | {name} | "
                f"{100 * final['exploitability_pot']:.8g} | "
                f"{layout['information_sets']} | {layout['key_utf8_bytes']} | "
                f"{layout['dense_regret_average_bytes']} |"
            )
            if name == candidate:
                continue
            for baseline in selected:
                candidate_row = next(
                    r
                    for r in rows
                    if r["spot_file"] == spot
                    and r["representation"] == candidate
                    and r["iteration"] == baseline["iteration"]
                )
                differences.append(
                    dict(
                        spot_file=spot,
                        baseline=name,
                        iteration=baseline["iteration"],
                        baseline_minus_candidate_exploitability_pot=(
                            baseline["exploitability_pot"]
                            - candidate_row["exploitability_pot"]
                        ),
                    )
                )
    (directory / "tables.md").write_text("\n".join(lines) + "\n")
    write_csv(directory / "signed-differences.csv", differences)
    plt = importlib.import_module("matplotlib.pyplot")
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))
    for ax, spot in zip(axes, config["spot_files"], strict=True):
        for name in config["representations"]:
            selected = [
                r
                for r in rows
                if r["spot_file"] == spot and r["representation"] == name
            ]
            ax.plot(
                [r["iteration"] for r in selected],
                [max(1e-12, r["exploitability_pot"]) for r in selected],
                marker="o",
                label=name,
            )
        ax.set(
            xscale="log",
            yscale="log",
            title=Path(spot).stem,
            xlabel="Full CFR+ iterations",
            ylabel="Exact exploitability / initial pot",
        )
        ax.legend(fontsize=6)
        ax.grid(alpha=0.2)
    fig.suptitle("Known games only; full controls; plotting floor 1e-12")
    fig.tight_layout()
    fig.savefig(directory / "full-controls.png", dpi=160)
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))
    for ax, spot in zip(axes, config["spot_files"], strict=True):
        layouts = [d for d in own["partitions"] if d["spot_file"] == spot]
        ax.bar(
            [d["representation"] for d in layouts],
            [d["information_sets"] for d in layouts],
        )
        public = next(
            d["information_sets"] for d in layouts if d["representation"] == "public_b8"
        )
        ax.axhline(
            0.75 * public, linestyle=":", color="black", label="Candidate row limit"
        )
        ax.set(title=Path(spot).stem, ylabel="Strategy rows")
        ax.tick_params(axis="x", labelrotation=25, labelsize=6)
        ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(directory / "row-counts.png", dpi=160)
    plt.close(fig)
    return dict(
        format="compact-full-result-v1",
        status="completed",
        failure=None,
        source=artifacts.source(root, clean=True),
        own_sha256=digest(own_path),
        native_sha256=digest(native_path),
        assessment=assessment,
        full_control_admission_passed=assessment["thresholds_passed"],
        actual_admission=assessment["thresholds_passed"],
        fresh_global_admission=False,
        sampled_learning="not_run",
        new_agent_default=False,
        scope=(
            "authenticated known-game full-control result only; "
            "separate sampled proposal still required"
        ),
    )
