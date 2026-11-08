"""Replay range-mass admission and report full controls, never sampled strength."""

import importlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from poker_ai.postflop.public_report import write_csv
from poker_ai.postflop.range_admission import IDENTITY, replay
from poker_ai.postflop.range_protocol import assess_full_metrics
from poker_ai.postflop.river_study import digest


def checked_audit(path: Path, report: dict[str, Any], audit: dict[str, Any]) -> float:
    own = {tuple(r[k] for k in IDENTITY): r for r in report["rows"]}
    native = {tuple(r[k] for k in IDENTITY): r for r in audit["comparisons"]}
    tolerance = report["config"]["full_limits"]["independent_tolerance_chips"]
    if (
        audit["status"] != "passed"
        or audit["input_sha256"] != digest(path)
        or native.keys() != own.keys()
        or len(native) != len(audit["comparisons"])
        or audit["tolerance_chips"] != tolerance
    ):
        raise ArithmeticError("missing/duplicate/mismatched admission native audit")
    errors: list[float] = []
    for key, row in native.items():
        if row.get("range_context_sha256") != own[key].get("range_context_sha256"):
            raise ArithmeticError("native range context changed")
        errors.extend(
            (
                row["value_error_chips"],
                row["exploitability_error_chips"],
                abs(row["native_value_chips"] - own[key]["value_player_zero_chips"]),
                abs(
                    row["native_exploitability_chips"]
                    - own[key]["exploitability_chips"]
                ),
            )
        )
    if any(not math.isfinite(v) or not 0 <= v <= tolerance for v in errors):
        raise ArithmeticError("admission native metric agreement fails")
    return max(errors)


def render(root: Path, path: Path, audit_path: Path, output: Path) -> dict[str, Any]:
    report, policies, own_error = replay(root, path)
    audit = json.loads(audit_path.read_text())
    native_error = checked_audit(path, report, audit)
    if audit["reference"] != {
        "name": "OpenSpiel",
        "version": "2.0.2",
        "license": "Apache-2.0",
    }:
        raise ArithmeticError("reference version/license changed")
    for name, sha in audit["source"]["sha256"].items():
        if digest(root / name) != sha:
            raise ArithmeticError("native audit source changed")
    assessment = assess_full_metrics(
        report["rows"],
        report["diagnostics"],
        audit["comparisons"],
        report["config"],
        report["range_contexts"],
        elapsed_seconds=report["seconds"],
    )
    summary = {
        "input_sha256": digest(path),
        "audit_sha256": digest(audit_path),
        "full_control_admission_passed": assessment["eligible_for_sampled_comparison"],
        "acceptance": assessment,
        "native_policies_checked": len(policies),
        "maximum_own_replay_error_chips": own_error,
        "maximum_native_error_chips": native_error,
        "study_seconds": report["seconds"],
        "audit_seconds": audit["seconds"],
        "sampled_learning": "not_run",
        "fresh_global_admission": False,
        "scope": (
            "known-game full-control admission only; "
            "sampled learning/fresh/global strength not established"
        ),
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    write_csv(output / "all-checkpoints.csv", report["rows"])
    write_csv(output / "diagnostics.csv", report["diagnostics"])
    lines = [
        "# Range-mass full-control admission",
        "",
        f"Full-control admission: **{summary['full_control_admission_passed']}**; "
        f"native audit **passed** ({len(policies)} policies).",
        "",
        "Sampled learning has not run. No fresh/global admission "
        "or default-agent change follows this result.",
        "",
        "| Game | Representation | Final full exploitability (% pot) | "
        "Rows | Key bytes | Regret/average bytes |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for filename in report["config"]["spot_files"]:
        for name in report["config"]["representations"]:
            row = next(
                r
                for r in report["rows"]
                if r["spot_file"] == filename
                and r["representation"] == name
                and r["iteration"] == report["config"]["full_tree_checkpoints"][-1]
            )
            diag = next(
                d
                for d in report["diagnostics"]
                if d["spot_file"] == filename and d["representation"] == name
            )
            lines.append(
                f"| {Path(filename).stem} | {name} | "
                f"{100 * row['exploitability_pot_fraction']:.6g} | "
                f"{diag['information_sets']} | {diag['key_utf8_bytes']} | "
                f"{diag['unpadded_regret_average_bytes']} |"
            )
    lines += [
        "",
        "All snapshots are own full-tree CFR+ average strategies, "
        "trained separately per known game. Rows/storage are components, "
        "not total process memory. Zero abstract-recall violations and "
        "complete-grid/coverage/work checks are required. Native evaluation "
        "shares own exported mechanics; it is not an independent full-engine proof.",
        "",
        "![Full controls](full-controls.png)",
        "",
        "![Row counts](row-counts.png)",
        "",
    ]
    (output / "tables.md").write_text("\n".join(lines))
    plots(report, output)
    return summary


def plots(report: dict[str, Any], output: Path) -> None:
    plt = importlib.import_module("matplotlib.pyplot")
    paths = report["config"]["spot_files"]
    fig, axes = plt.subplots(
        1, len(paths), figsize=(6 * len(paths), 4.5), squeeze=False
    )
    for ax, path in zip(axes[0], paths, strict=True):
        for name in report["config"]["representations"]:
            rows = [
                r
                for r in report["rows"]
                if r["spot_file"] == path and r["representation"] == name
            ]
            x = [r["iteration"] for r in rows]
            ax.plot(
                x,
                np.maximum(1e-12, [r["exploitability_pot_fraction"] for r in rows]),
                marker="o",
                label=name,
            )
        ax.set(
            xscale="log",
            yscale="log",
            title=Path(path).stem,
            xlabel="Full-tree CFR+ iterations",
            ylabel="Exact-game exploitability / initial pot",
        )
        ax.set_xticks(x, [f"{v:g}" for v in x], fontsize=8)
        ax.minorticks_off()
        ax.grid(alpha=0.2)
        ax.legend(fontsize=7)
    fig.suptitle(
        "Known games: full controls only; sampled learning not run; plot floor 1e-12",
        fontsize=10,
    )
    fig.tight_layout()
    fig.savefig(output / "full-controls.png", dpi=160)
    plt.close(fig)
    fig, axes = plt.subplots(1, len(paths), figsize=(6 * len(paths), 4), squeeze=False)
    for ax, path in zip(axes[0], paths, strict=True):
        rows = [r for r in report["diagnostics"] if r["spot_file"] == path]
        ax.bar(
            [r["representation"] for r in rows], [r["information_sets"] for r in rows]
        )
        raw = next(
            r["information_sets"] for r in rows if r["representation"] == "public_b8"
        )
        ax.axhline(
            report["config"]["full_limits"][
                "candidate_information_sets_relative_to_public_b8"
            ]
            * raw,
            color="black",
            linestyle=":",
            label="Candidate row limit",
        )
        ax.tick_params(axis="x", labelrotation=20, labelsize=8)
        ax.set(title=Path(path).stem, ylabel="Strategy rows")
        ax.legend(fontsize=7)
    fig.suptitle("Representation size on the same materialized game trees", fontsize=10)
    fig.tight_layout()
    fig.savefig(output / "row-counts.png", dpi=160)
    plt.close(fig)
