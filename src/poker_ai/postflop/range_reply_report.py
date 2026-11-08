"""Replay all response cases; arithmetic means preserve additive identities."""

import importlib
import json
import math
import statistics
from pathlib import Path
from typing import Any

from poker_ai.postflop.public_report import write_csv
from poker_ai.postflop.range_reply import IDENTITY, check_source, replay
from poker_ai.postflop.river_study import digest


def summary_rows(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            **{k: c[k] for k in IDENTITY},
            "exact_percent_pot": 100 * c["exact_exploitability_chips"] / c["pot"],
            "within_percent_pot": 100 * c["restricted_exploitability_chips"] / c["pot"],
            "extra_percent_pot": 100 * c["extra_information_chips"] / c["pot"],
        }
        for c in cases
    ]


def aggregate(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    keys = list(
        dict.fromkeys(
            (r["spot_file"], r["representation"], r["training"]) for r in rows
        )
    )
    result = []
    for path, name, training in keys:
        selected = [
            r
            for r in rows
            if (r["spot_file"], r["representation"], r["training"])
            == (path, name, training)
        ]
        a = {
            "spot_file": path,
            "representation": name,
            "training": training,
            "profiles": len(selected),
            **{
                "mean_" + k: statistics.mean(r[k] for r in selected)
                for k in (
                    "exact_percent_pot",
                    "within_percent_pot",
                    "extra_percent_pot",
                )
            },
            "median_exact_percent_pot": statistics.median(
                r["exact_percent_pot"] for r in selected
            ),
        }
        if (
            abs(
                a["mean_exact_percent_pot"]
                - a["mean_within_percent_pot"]
                - a["mean_extra_percent_pot"]
            )
            > 1e-9
        ):
            raise ArithmeticError("mean response components do not add")
        result.append(a)
    return result


def checked_audit(path: Path, report: dict[str, Any], audit: dict[str, Any]) -> float:
    json.dumps(audit, allow_nan=False)
    expected = {
        tuple(c[k] for k in IDENTITY) + (target,)
        for c in report["cases"]
        for target in (0, 1)
    }
    ids = [tuple(r[k] for k in IDENTITY) + (r["target"],) for r in audit["rows"]]
    if (
        audit["status"] != "passed"
        or audit["input_sha256"] != digest(path)
        or len(ids) != len(set(ids))
        or set(ids) != expected
        or audit["reference"]
        != {"name": "OpenSpiel", "version": "2.0.2", "license": "Apache-2.0"}
    ):
        raise ArithmeticError("incomplete/mismatched native response audit")
    errors: list[float] = []
    cached: list[float] = []
    for row in audit["rows"]:
        if type(row["target"]) is not int or row["target"] not in (0, 1):
            raise ArithmeticError("changed native responding seat")
        case = next(c for c in report["cases"] if all(c[k] == row[k] for k in IDENTITY))
        if row["range_context_sha256"] != case["range_context_sha256"]:
            raise ArithmeticError("native response context changed")
        own = case["responses"][row["target"]]
        for label in ("exact", "restricted"):
            values = [
                row[label + "_root_error_chips"],
                row[label + "_achieved_error_chips"],
            ]
            cached.extend(values)
            errors.extend(values)
            errors.extend(
                (
                    abs(
                        row[label + "_native_value_chips"]
                        - own[label + "_reply_value_chips"]
                    ),
                    abs(
                        row[label + "_achieved_value_chips"]
                        - own[label + "_reply_value_chips"]
                    ),
                    abs(
                        row[label + "_native_value_chips"]
                        - row[label + "_achieved_value_chips"]
                    ),
                )
            )
    tolerance = report["config"]["tolerance_chips"]
    if any(not math.isfinite(v) or not 0 <= v <= tolerance for v in errors) or audit[
        "maximum_native_error_chips"
    ] != max(cached):
        raise ArithmeticError("native response value agreement failed")
    return max(errors)


def render(root: Path, path: Path, audit_path: Path, output: Path) -> dict[str, Any]:
    report, _, error = replay(root, path)
    audit = json.loads(audit_path.read_text())
    maximum = checked_audit(path, report, audit)
    check_source(root, audit["source"])
    rows = summary_rows(report["cases"])
    means = aggregate(rows)
    streets = [
        {
            **{k: c[k] for k in IDENTITY},
            "responding_seat": r["target"],
            "street": street,
            "unilateral_loss_chips": chips,
            "contribution_percent_pot": 50 * chips / c["pot"],
        }
        for c in report["cases"]
        for r in c["responses"]
        for street, chips in r["street_losses_chips"].items()
    ]
    summary = {
        "status": "verified_diagnosis",
        "input_sha256": digest(path),
        "audit_sha256": digest(audit_path),
        "cases": rows,
        "means": means,
        "native_roots_checked": 4 * len(rows),
        "own_reply_values_checked": 4 * len(rows),
        "maximum_native_error_chips": maximum,
        "maximum_own_replay_error_chips": error,
        "diagnosis_seconds": report["seconds"],
        "audit_seconds": audit["seconds"],
        "training_performed": False,
        "fresh_global_admission": False,
        "scope": (
            "fixed saved opponent diagnosis; no retraining gain or "
            "universal abstraction floor claim"
        ),
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    write_csv(output / "all-profiles.csv", rows)
    write_csv(output / "mean-components.csv", means)
    write_csv(output / "street-losses.csv", streets)
    lines = [
        "# Saved range-mass best-response diagnosis",
        "",
        "Every number is % of initial pot. Exact exploitability = "
        "within-partition + extra-information gain, half-summed over "
        "seats. All seeds are retained below.",
        "",
        "| Game | Representation | Training | Seed | Exact total | "
        "Within partition | Extra information |",
        "|---|---|---|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {Path(row['spot_file']).stem} | {row['representation']} | "
            f"{row['training']} | {row['seed']} | "
            f"{row['exact_percent_pot']:.7g} | "
            f"{row['within_percent_pot']:.7g} | "
            f"{row['extra_percent_pot']:.7g} |"
        )
    lines += [
        "",
        "Mean component tables use arithmetic means across all "
        "sampled seeds; medians of components are not added. Full "
        "controls are separate 4096-iteration CFR+ training "
        "conditions, not matched-work samples. Tiny signed values "
        "within the chip tolerance are numerical roundoff.",
        "",
        "These are fixed-opponent response opportunities, not "
        "measured retraining gains or a universal abstraction floor. "
        "Saved-prefix/reply-suffix street losses can include later "
        "opportunities. Counterstrategy examples are not "
        "deployed-agent frequencies or universal advice. Native "
        "checks share exported mechanics and partitions; no native "
        "actions are exported.",
        "",
        "![Candidate profiles](candidate-profiles.png)",
        "",
        "![All sampled controls, mean components](sampled-means.png)",
        "",
    ]
    (output / "tables.md").write_text("\n".join(lines))
    plots(rows, means, report["config"], output)
    return summary


def plots(
    rows: list[dict[str, Any]],
    means: list[dict[str, Any]],
    config: dict[str, Any],
    output: Path,
) -> None:
    plt = importlib.import_module("matplotlib.pyplot")
    paths = config["spot_files"]
    for filename, candidate in (
        ("candidate-profiles.png", True),
        ("sampled-means.png", False),
    ):
        fig, axes = plt.subplots(
            1, len(paths), figsize=(7 * len(paths), 4.8), squeeze=False
        )
        for ax, path in zip(axes[0], paths, strict=True):
            if candidate:
                selected = sorted(
                    (
                        r
                        for r in rows
                        if r["spot_file"] == path
                        and r["representation"] == "texture_range_q8_b8"
                    ),
                    key=lambda r: (r["training"] != "full", r["seed"] or 0),
                )
                labels = [
                    "full 4096" if r["training"] == "full" else str(r["seed"])
                    for r in selected
                ]
                within = [r["within_percent_pot"] for r in selected]
                extra = [r["extra_percent_pot"] for r in selected]
            else:
                selected = [
                    r
                    for r in means
                    if r["spot_file"] == path and r["training"] == "sampled"
                ]
                labels = [r["representation"] for r in selected]
                within = [r["mean_within_percent_pot"] for r in selected]
                extra = [r["mean_extra_percent_pot"] for r in selected]
            x = list(range(len(selected)))
            ax.bar(x, within, label="Gain within saved partition")
            ax.bar(x, extra, bottom=within, label="Extra exact-information value")
            ax.set_xticks(x, labels, rotation=20, ha="right", fontsize=8)
            ax.set(
                title=Path(path).stem,
                ylabel="Exploitability contribution (% initial pot)",
            )
            ax.grid(axis="y", alpha=0.2)
            ax.legend(fontsize=7)
        fig.suptitle(
            "Saved range-mass candidate: full control and every sampled seed"
            if candidate
            else "All sampled controls: mean components, not component medians",
            fontsize=11,
        )
        fig.tight_layout()
        fig.savefig(output / filename, dpi=160)
        plt.close(fig)
