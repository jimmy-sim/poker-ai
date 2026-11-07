"""Offline report of the complete board-representation comparison; no training."""

import csv
import importlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from poker_ai.postflop.public_evidence import replay
from poker_ai.postflop.public_metrics import IDENTITY
from poker_ai.postflop.river_study import digest


def checked_native(
    path: Path,
    report: dict[str, Any],
    crossplay: list[dict[str, Any]],
    audit: dict[str, Any],
) -> float:
    """Bind every native result to own rows; reject duplicates and nonfinite data."""
    tolerance = report["config"]["limits"]["independent_value_br_tolerance_chips"]
    if (
        audit["status"] != "passed"
        or audit["input_sha256"] != digest(path)
        or audit["tolerance_chips"] != tolerance
        or audit["checkpoint_receipts_checked"]
        != sum(r["method"] == "external" for r in report["rows"])
    ):
        raise ArithmeticError("missing/mismatched native audit or checkpoint receipts")
    own = {tuple(r[k] for k in IDENTITY): r for r in report["rows"]}
    native = {tuple(r[k] for k in IDENTITY): r for r in audit["comparisons"]}
    fields = ("spot_file", "first", "second")
    own_cross = {tuple(r[k] for k in fields): r for r in crossplay}
    native_cross = {tuple(r[k] for k in fields): r for r in audit["crossplay"]}
    if (
        own.keys() != native.keys()
        or len(native) != len(audit["comparisons"])
        or own_cross.keys() != native_cross.keys()
        or len(native_cross) != len(audit["crossplay"])
    ):
        raise ArithmeticError("incomplete/duplicate native policy or cross-play grid")
    errors: list[float] = []
    for key, row in native.items():
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
    for key, row in native_cross.items():
        errors.extend(
            (
                row["value_error_chips"],
                row["balanced_error_chips"],
                abs(
                    row["native_value_player_zero_chips"]
                    - own_cross[key]["value_player_zero_chips"]
                ),
                abs(
                    row["native_seat_balanced_first_chips"]
                    - own_cross[key]["seat_balanced_first_chips"]
                ),
            )
        )
    if any(not math.isfinite(v) or not 0 <= v <= tolerance for v in errors):
        raise ArithmeticError("native metric agreement outside declared tolerance")
    return float(max(errors))


def learning_summary(report: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    config = report["config"]
    for filename in config["development_spots"]:
        for encoding in config["encodings"]:
            for threshold in config["sampled_node_checkpoints"]:
                selected = [
                    r
                    for r in report["rows"]
                    if r["spot_file"] == filename
                    and r["encoding"] == encoding
                    and r["method"] == "external"
                    and r["node_threshold"] == threshold
                ]
                if sorted(r["seed"] for r in selected) != sorted(config["seeds"]):
                    raise ArithmeticError("missing/duplicate learning-summary seeds")
                eps = [r["exploitability_pot_fraction"] for r in selected]
                rows.append(
                    {
                        "spot_file": filename,
                        "spot": selected[0]["spot"],
                        "encoding": encoding,
                        "node_threshold": threshold,
                        "median_epsilon_pot": float(np.median(eps)),
                        "min_epsilon_pot": min(eps),
                        "max_epsilon_pot": max(eps),
                        "minimum_average_coverage": min(
                            r["uniform_reach_average_row_coverage"] for r in selected
                        ),
                        "minimum_subsequent_coverage": min(
                            r["uniform_reach_subsequently_sampled_coverage"]
                            for r in selected
                        ),
                        "maximum_initial_only_rows": max(
                            r["initial_only_information_sets"] for r in selected
                        ),
                        "median_actual_work": float(
                            np.median([r["total_node_work"] for r in selected])
                        ),
                    }
                )
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted({k for r in rows for k in r}))
        writer.writeheader()
        writer.writerows(rows)


def render(root: Path, path: Path, audit_path: Path, output: Path) -> dict[str, Any]:
    report, snapshots, own = replay(root, path)
    audit = json.loads(audit_path.read_text())
    maximum_native = checked_native(path, report, own["crossplay"], audit)
    learning = learning_summary(report)
    summary = {
        "input_sha256": digest(path),
        "audit_sha256": digest(audit_path),
        "study_source_commit": report["source"]["git_commit"],
        "acceptance": report["acceptance"],
        "audit_status": "passed",
        "candidate_development_gate_passed": report["acceptance"][
            "candidate_learning_gate_passed"
        ],
        "own_policies_replayed": len(snapshots),
        "native_policies_checked": len(audit["comparisons"]),
        "native_crossplay_profiles_checked": len(audit["crossplay"]),
        "checkpoint_receipts_checked_at_native_audit": audit[
            "checkpoint_receipts_checked"
        ],
        "maximum_own_replay_error_chips": own["maximum_own_replay_error_chips"],
        "maximum_native_error_chips": maximum_native,
        "learning": learning,
        "study_seconds": report["seconds"],
        "audit_seconds": audit["seconds"],
        "peak_process_rss_bytes": report["peak_process_rss_bytes"],
        "scope": (
            "known tiny per-game learners; not zero-shot/global strength; "
            "no fresh/global admission in this block"
        ),
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    write_csv(output / "learning.csv", learning)
    write_csv(output / "all-checkpoints.csv", report["rows"])
    write_csv(output / "crossplay.csv", own["crossplay"])
    write_csv(
        output / "diagnostics.csv",
        [
            {k: v for k, v in r.items() if k != "profiles"}
            for r in report["diagnostics"]
        ],
    )
    write_csv(
        output / "profiles.csv",
        [
            {"spot_file": r["spot_file"], "encoding": r["encoding"], **p}
            for r in report["diagnostics"]
            for p in r["profiles"]
        ],
    )
    lines = [
        "# Public-board comparison: known development games",
        "",
        "Candidate development gate: "
        f"**{summary['candidate_development_gate_passed']}**. "
        f"Native audit: **passed**, {len(snapshots)} policies and "
        f"{len(audit['crossplay'])} ordered final profiles.",
        "",
        "All exploitability percentages are fractions of initial pot "
        "multiplied by 100. "
        "Rows are distinct strategy entries; smaller is not automatically stronger.",
        "",
        "| Game | Encoding | Full epsilon % | Sample median % | Worst % | "
        "Rows | Rows/raw-public | Failed criteria |",
        "|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for check in report["acceptance"]["checks"]:
        diagnostic = next(
            r
            for r in report["diagnostics"]
            if r["spot_file"] == check["spot_file"]
            and r["encoding"] == check["encoding"]
        )
        failures = ", ".join(k for k, v in check["criteria"].items() if not v) or "none"
        lines.append(
            f"| {diagnostic['spot']} | {check['encoding']} | "
            f"{100 * check['full_epsilon_pot']:.6g} | "
            f"{100 * check['median_epsilon_pot']:.6g} | "
            f"{100 * check['worst_epsilon_pot']:.6g} | "
            f"{diagnostic['information_sets']} | "
            f"{check['information_sets_relative_to_public_b8']:.4f} | {failures} |"
        )
    lines += [
        "",
        "Only exact and the preselected texture candidate control admission. "
        "Criteria for other encodings are diagnostic.",
        "",
        "The CSVs retain all seeds/checkpoints, collisions and their "
        "uniform-decision-reach mass, initial-only rows, initialized/subsequent "
        "coverage, work overshoot and memory counters. Key bytes and float-array "
        "bytes exclude Python containers and shared tree storage. RSS is a "
        "cumulative process high-water mark, not a per-representation memory saving.",
        "",
        "Cross-play covers every ordered pair of final full/sample policies, "
        "including self. "
        "Seat-balanced advantage is (V(A0,B1)-V(B0,A1))/2; self is zero by definition. "
        "These own-policy matchups do not replace exact best responses "
        "or establish a global win rate.",
        "",
        "Profiles use separate fresh solvers at the first study seed, repeated "
        "at the fixed iteration count; profile work is not added to learning "
        "checkpoints. Study wall time includes profiling/setup/serialization.",
        "",
        "![Sampled learning](learning-work.png)",
        "",
        "![Full controls](full-tree.png)",
        "",
        "![Representation storage](representation-size.png)",
        "",
        "![Own-policy cross-play](crossplay.png)",
        "",
    ]
    (output / "tables.md").write_text("\n".join(lines))
    plots(report, learning, own["crossplay"], output)
    return summary


def plots(
    report: dict[str, Any],
    learning: list[dict[str, Any]],
    crossplay: list[dict[str, Any]],
    output: Path,
) -> None:
    plt = importlib.import_module("matplotlib.pyplot")
    config = report["config"]
    paths = config["development_spots"]
    for sampled, name in ((True, "learning-work"), (False, "full-tree")):
        fig, axes = plt.subplots(
            1, len(paths), figsize=(6 * len(paths), 4.5), squeeze=False
        )
        for ax, path in zip(axes[0], paths, strict=True):
            for encoding in config["encodings"]:
                if sampled:
                    selected = [
                        r
                        for r in learning
                        if r["spot_file"] == path and r["encoding"] == encoding
                    ]
                    x = [r["node_threshold"] for r in selected]
                    y = [r["median_epsilon_pot"] for r in selected]
                    ax.fill_between(
                        x,
                        np.maximum(1e-12, [r["min_epsilon_pot"] for r in selected]),
                        np.maximum(1e-12, [r["max_epsilon_pot"] for r in selected]),
                        alpha=0.12,
                    )
                else:
                    selected = [
                        r
                        for r in report["rows"]
                        if r["spot_file"] == path
                        and r["encoding"] == encoding
                        and r["method"] == "full_cfr_plus"
                    ]
                    x = [r["iteration"] for r in selected]
                    y = [r["exploitability_pot_fraction"] for r in selected]
                ax.plot(x, np.maximum(1e-12, y), marker="o", label=encoding)
            ax.set(
                xscale="log",
                yscale="log",
                title=Path(path).stem,
                xlabel="Charged node work" if sampled else "Full-tree CFR+ iterations",
                ylabel="Exact-game exploitability / initial pot",
            )
            ax.set_xticks(x, [f"{value:g}" for value in x], fontsize=8)
            ax.minorticks_off()
            ax.axhline(
                config["limits"]["candidate_sampled_median_exploitability_pot"]
                if sampled
                else config["limits"]["exact_full_exploitability_pot"],
                color="black",
                linestyle=":",
                linewidth=1,
                label="Sampled median limit" if sampled else "Exact full control limit",
            )
            ax.grid(alpha=0.2)
            ax.legend(fontsize=7)
        fig.suptitle(
            "Known games: fixed-seed median and min–max; shaded range is not a CI"
            if sampled
            else "Full-tree controls; plot floor 1e-12, raw metrics unchanged",
            fontsize=10,
        )
        fig.tight_layout()
        fig.savefig(output / f"{name}.png", dpi=160)
        plt.close(fig)
    fig, axes = plt.subplots(
        1, len(paths), figsize=(6 * len(paths), 4.5), squeeze=False
    )
    for ax, path in zip(axes[0], paths, strict=True):
        selected = [r for r in report["diagnostics"] if r["spot_file"] == path]
        positions = np.arange(len(selected))
        ax.bar(
            positions - 0.18,
            [r["key_utf8_bytes"] / 1024 for r in selected],
            0.36,
            label="UTF-8 keys",
        )
        ax.bar(
            positions + 0.18,
            [r["unpadded_regret_average_bytes"] / 1024 for r in selected],
            0.36,
            label="Regret + average floats",
        )
        ax.set_xticks(
            positions,
            [r["encoding"] for r in selected],
            rotation=25,
            ha="right",
            fontsize=8,
        )
        ax.set(
            title=Path(path).stem,
            ylabel="KiB; excludes containers and shared game tree",
        )
        ax.legend(fontsize=8)
    fig.suptitle(
        "Measured representation storage components; not total process memory",
        fontsize=10,
    )
    fig.tight_layout()
    fig.savefig(output / "representation-size.png", dpi=160)
    plt.close(fig)
    fig, axes = plt.subplots(1, len(paths), figsize=(8 * len(paths), 7), squeeze=False)
    limit = max(abs(r["seat_balanced_first_pot"]) * 100 for r in crossplay) or 1e-12
    for ax, path in zip(axes[0], paths, strict=True):
        selected = [r for r in crossplay if r["spot_file"] == path]
        labels = list(dict.fromkeys(r["first"] for r in selected))
        lookup = {
            (r["first"], r["second"]): r["seat_balanced_first_pot"] * 100
            for r in selected
        }
        values = [[lookup[a, b] for b in labels] for a in labels]
        im = ax.imshow(values, cmap="RdBu", vmin=-limit, vmax=limit)
        ax.set_xticks(range(len(labels)), labels, rotation=90, fontsize=5)
        ax.set_yticks(range(len(labels)), labels, fontsize=5)
        ax.set(title=Path(path).stem, xlabel="Second policy", ylabel="First policy")
        fig.colorbar(
            im,
            ax=ax,
            fraction=0.04,
            pad=0.04,
            label="First policy seat-balanced EV (% pot)",
        )
    fig.suptitle(
        "Final own policies: all ordered matchups; self = 0 by definition", fontsize=10
    )
    fig.tight_layout()
    fig.savefig(output / "crossplay.png", dpi=180)
    plt.close(fig)
