"""Offline checkpoint replay, native audit binding and matched-work reporting."""

import importlib
import json
import math
import statistics
from pathlib import Path
from typing import Any

from poker_ai.postflop.public_report import write_csv
from poker_ai.postflop.range_protocol import assess_sampled_metrics
from poker_ai.postflop.range_sampled import FULL_STUDY, IDENTITY, replay
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
        raise ArithmeticError("missing/duplicate/changed sampled native audit")
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
        raise ArithmeticError("sampled native value agreement failed")
    return max(errors)


def learning_summary(report: dict[str, Any]) -> list[dict[str, Any]]:
    config = report["config"]
    later = config["later_sampled"]
    rows = []
    for filename in config["spot_files"]:
        for name in config["representations"]:
            for checkpoint in later["node_work_checkpoints"]:
                selected = [
                    r
                    for r in report["rows"]
                    if (r["spot_file"], r["representation"], r["node_work_checkpoint"])
                    == (filename, name, checkpoint)
                ]
                if sorted(r["seed"] for r in selected) != later["seeds"]:
                    raise ArithmeticError("missing/duplicate sampled summary seeds")
                values = [100 * r["exploitability_pot_fraction"] for r in selected]
                rows.append(
                    {
                        "spot_file": filename,
                        "representation": name,
                        "requested_node_work": checkpoint,
                        "median_exploitability_percent_pot": statistics.median(values),
                        "minimum_exploitability_percent_pot": min(values),
                        "worst_exploitability_percent_pot": max(values),
                        "minimum_average_coverage": min(
                            r["uniform_reach_average_row_coverage"] for r in selected
                        ),
                        "minimum_subsequently_sampled_coverage": min(
                            r["uniform_reach_subsequently_sampled_coverage"]
                            for r in selected
                        ),
                        "maximum_initial_only_rows": max(
                            r["initial_only_information_sets"] for r in selected
                        ),
                        "minimum_actual_node_work": min(
                            r["total_node_work"] for r in selected
                        ),
                        "maximum_actual_node_work": max(
                            r["total_node_work"] for r in selected
                        ),
                    }
                )
    return rows


def render(root: Path, path: Path, audit_path: Path, output: Path) -> dict[str, Any]:
    report, policies, own_error = replay(root, path)
    audit = json.loads(audit_path.read_text())
    error = checked_audit(path, report, audit)
    if audit["reference"] != {
        "name": "OpenSpiel",
        "version": "2.0.2",
        "license": "Apache-2.0",
    }:
        raise ArithmeticError("native reference version/license changed")
    for name, sha in audit["source"]["sha256"].items():
        if digest(root / name) != sha:
            raise ArithmeticError("sampled audit source changed")
    assessment = assess_sampled_metrics(
        report["rows"],
        audit["comparisons"],
        report["full_prerequisite"]["assessment"],
        report["config"],
        report["range_contexts"],
        elapsed_seconds=report["seconds"],
    )
    summary = {
        "input_sha256": digest(path),
        "audit_sha256": digest(audit_path),
        "assessment": assessment,
        "candidate_development_gate_passed": assessment["development_metrics_passed"],
        "native_policies_checked": len(policies),
        "checkpoint_visit_pairs_replayed": len(policies),
        "maximum_own_replay_error_chips": own_error,
        "maximum_native_error_chips": error,
        "study_seconds": report["seconds"],
        "audit_seconds": audit["seconds"],
        "fresh_global_admission": False,
        "scope": "known separately trained games; no fresh/global/default admission",
    }
    learning = learning_summary(report)
    full = json.loads((root / FULL_STUDY).read_text())
    baseline = [
        r
        for r in full["rows"]
        if r["spot_file"] in report["config"]["spot_files"]
        and r["iteration"] == full["config"]["full_tree_checkpoints"][-1]
    ]
    output.mkdir(parents=True, exist_ok=True)
    (output / "summary.json").write_text(
        json.dumps(summary, sort_keys=True, indent=2, allow_nan=False) + "\n"
    )
    write_csv(output / "all-checkpoints.csv", report["rows"])
    write_csv(output / "learning.csv", learning)
    write_csv(output / "full-control-reference.csv", baseline)
    diagnostics = [
        {k: v for k, v in d.items() if k != "profiles"} for d in report["diagnostics"]
    ]
    write_csv(output / "diagnostics.csv", diagnostics)
    profiles = [
        {"spot_file": d["spot_file"], "representation": d["representation"], **p}
        for d in report["diagnostics"]
        for p in d["profiles"]
    ]
    write_csv(output / "profiles.csv", profiles)
    lines = [
        "# Range-mass fixed-work sampled comparison",
        "",
        f"Development gate: "
        f"**{summary['candidate_development_gate_passed']}**; native audit "
        f"**passed** ({len(policies)} own policies).",
        "",
        "All policies and checkpoint/visit pairs replayed. No "
        "fresh/global/default admission follows.",
        "",
        "| Game | Representation | Median final exploitability (% pot) | "
        "Worst seed (% pot) | Average coverage (min) | Subsequently "
        "sampled coverage (min) |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in learning:
        if (
            row["requested_node_work"]
            == report["config"]["later_sampled"]["node_work_checkpoints"][-1]
        ):
            lines.append(
                f"| {Path(row['spot_file']).stem} | {row['representation']} | "
                f"{row['median_exploitability_percent_pot']:.6g} | "
                f"{row['worst_exploitability_percent_pot']:.6g} | "
                f"{100 * row['minimum_average_coverage']:.6g}% | "
                f"{100 * row['minimum_subsequently_sampled_coverage']:.6g}% |"
            )
    lines += [
        "",
        "Exact and candidate require median <=1% pot and worst <=2.5% on "
        "each game at final work. All final controls require average "
        "coverage >=95% and zero recall violations. Every seed remains in "
        "the CSV. Three seeds are not a confidence interval.",
        "",
        "Work includes exact initialization and actual recursive visits; "
        "a whole iteration crosses each requested budget. Profiles are "
        "separate solvers; setup/profiling/receipt persistence are "
        "included in study wall time. Uniform-reach initialized-average "
        "coverage is distinct from subsequent sampled coverage. Key/table "
        "bytes are components, not total memory; RSS is a "
        "process-lifetime high-water mark.",
        "",
        "Exploitability is exact-game NashConv/2 divided by initial pot, "
        "not a match win rate. Native evaluation shares own exported "
        "mechanics and never trains the learner. Known tiny ranges and "
        "separate per-game training do not establish global Hold'em "
        "strength.",
        "",
        "![Matched-work learning](learning-work.png)",
        "",
        "![Final seeds](final-seeds.png)",
        "",
    ]
    (output / "tables.md").write_text("\n".join(lines))
    plots(report, learning, output)
    return summary


def plots(report: dict[str, Any], learning: list[dict[str, Any]], output: Path) -> None:
    plt = importlib.import_module("matplotlib.pyplot")
    config = report["config"]
    paths = config["spot_files"]
    fig, axes = plt.subplots(
        1, len(paths), figsize=(7 * len(paths), 4.8), squeeze=False
    )
    for ax, path in zip(axes[0], paths, strict=True):
        for index, name in enumerate(config["representations"]):
            color = f"C{index}"
            for seed in config["later_sampled"]["seeds"]:
                selected = [
                    r
                    for r in report["rows"]
                    if (r["spot_file"], r["representation"], r["seed"])
                    == (path, name, seed)
                ]
                ax.plot(
                    [r["node_work_checkpoint"] for r in selected],
                    [
                        max(1e-10, 100 * r["exploitability_pot_fraction"])
                        for r in selected
                    ],
                    color=color,
                    alpha=0.25,
                    linewidth=1,
                )
            selected = [
                r
                for r in learning
                if (r["spot_file"], r["representation"]) == (path, name)
            ]
            ax.plot(
                [r["requested_node_work"] for r in selected],
                [max(1e-10, r["median_exploitability_percent_pot"]) for r in selected],
                color=color,
                label=name,
                marker="o",
                linewidth=2,
            )
        ax.axhline(1, color="black", linestyle=":", label="Final median limit")
        ax.set(
            xscale="log",
            yscale="log",
            title=Path(path).stem,
            xlabel="Requested node work (initialization included)",
            ylabel="Exact-game exploitability (% initial pot)",
        )
        ax.grid(alpha=0.2)
        ax.legend(fontsize=7)
    fig.suptitle(
        "Fixed development games: faint individual seeds, bold medians; "
        "plot floor 1e-10%",
        fontsize=10,
    )
    fig.tight_layout()
    fig.savefig(output / "learning-work.png", dpi=160)
    plt.close(fig)
    fig, axes = plt.subplots(
        1, len(paths), figsize=(7 * len(paths), 4.8), squeeze=False
    )
    for ax, path in zip(axes[0], paths, strict=True):
        for index, name in enumerate(config["representations"]):
            selected = [
                r
                for r in report["rows"]
                if (r["spot_file"], r["representation"], r["node_work_checkpoint"])
                == (path, name, config["later_sampled"]["node_work_checkpoints"][-1])
            ]
            ax.scatter(
                [index] * len(selected),
                [100 * r["exploitability_pot_fraction"] for r in selected],
                color=f"C{index}",
            )
        ax.axhline(
            1, color="black", linestyle=":", label="Exact/candidate median limit"
        )
        ax.axhline(
            2.5, color="black", linestyle="--", label="Exact/candidate worst limit"
        )
        ax.set_xticks(
            range(len(config["representations"])),
            config["representations"],
            rotation=20,
            fontsize=8,
        )
        ax.set(
            title=Path(path).stem,
            ylabel="Final exact-game exploitability (% initial pot)",
        )
        ax.grid(alpha=0.2)
        ax.legend(fontsize=7)
    fig.suptitle(
        "All final seeds retained; limits apply to exact and the candidate", fontsize=10
    )
    fig.tight_layout()
    fig.savefig(output / "final-seeds.png", dpi=160)
    plt.close(fig)
