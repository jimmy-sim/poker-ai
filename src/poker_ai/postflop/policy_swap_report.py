"""Offline fixed-policy intervention report; no retraining-cause claim."""

import importlib
import json
import math
import statistics
from pathlib import Path
from typing import Any

from poker_ai.postflop.policy_swaps import CELL, CROSS, HYBRID, effects, labels, replay
from poker_ai.postflop.public_report import write_csv
from poker_ai.postflop.range_reply import check_source
from poker_ai.postflop.river_study import digest


def checked_audit(path: Path, report: dict[str, Any], audit: dict[str, Any]) -> float:
    json.dumps(audit, allow_nan=False)
    if (
        audit["status"] != "passed"
        or audit["input_sha256"] != digest(path)
        or audit["reference"]
        != {"name": "OpenSpiel", "version": "2.0.2", "license": "Apache-2.0"}
    ):
        raise ArithmeticError("changed native swap audit header")
    own_cross = {tuple(r[k] for k in CROSS): r for r in report["crossplay"]}
    native_cross = {tuple(r[k] for k in CROSS): r for r in audit["crossplay"]}
    own_reply = {
        tuple(c[k] for k in HYBRID) + (r["target"],): (c, r)
        for c in report["hybrids"]
        for r in c["responses"]
    }
    native_reply = {
        tuple(r[k] for k in HYBRID) + (r["target"],): r for r in audit["responses"]
    }
    if (
        own_cross.keys() != native_cross.keys()
        or len(native_cross) != len(audit["crossplay"])
        or own_reply.keys() != native_reply.keys()
        or len(native_reply) != len(audit["responses"])
    ):
        raise ArithmeticError("incomplete/duplicate native swap grid")
    errors: list[float] = []
    cached: list[float] = []
    for key, row in native_cross.items():
        own = own_cross[key]
        if row["range_context_sha256"] != own["range_context_sha256"]:
            raise ArithmeticError("cross context changed")
        cached.append(row["value_error_chips"])
        errors.extend(
            (
                row["value_error_chips"],
                abs(
                    row["native_value_player_zero_chips"]
                    - own["value_player_zero_chips"]
                ),
            )
        )
        reverse = native_cross[(*key[:2], key[3], key[2])]
        errors.append(
            abs(
                (
                    row["native_value_player_zero_chips"]
                    - reverse["native_value_player_zero_chips"]
                )
                / 2
                - own["seat_balanced_first_chips"]
            )
        )
    for key, row in native_reply.items():
        c, own = own_reply[key]
        if (
            type(row["target"]) is not int
            or type(row["seed"]) is not int
            or row["range_context_sha256"] != c["range_context_sha256"]
        ):
            raise ArithmeticError("native response identity/context changed")
        cached.append(row["baseline_error_chips"])
        errors.extend(
            (
                row["baseline_error_chips"],
                abs(row["native_baseline_value_chips"] - own["baseline_value_chips"]),
            )
        )
        for label in ("exact", "restricted"):
            for suffix in ("_root_error_chips", "_achieved_error_chips"):
                cached.append(row[label + suffix])
                errors.append(row[label + suffix])
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
                )
            )
        errors.append(
            abs(
                row["exact_native_value_chips"]
                - row["restricted_native_value_chips"]
                - own["extra_information_chips"]
            )
        )
    for row in report["effects"]:
        base = tuple(row[k] for k in (*CELL, "seed"))
        g = {
            c: native_reply[(*base, c, row["target"])]["exact_native_value_chips"]
            - native_reply[(*base, c, row["target"])]["restricted_native_value_chips"]
            for c in report["config"]["street_combinations"]
        }
        errors.extend(abs(v - row[k]) for k, v in effects(g).items())
    if any(
        not math.isfinite(v) or not 0 <= v <= report["config"]["tolerance_chips"]
        for v in errors
    ) or audit["maximum_native_error_chips"] != max(cached):
        raise ArithmeticError("native swap/attribution values disagree")
    return max(errors)


def tables(
    report: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    hybrid = []
    for row in report["hybrids"]:
        hybrid.append(
            {
                **{k: row[k] for k in HYBRID},
                "extra_percent_pot": 50
                * sum(r["extra_information_chips"] for r in row["responses"])
                / row["pot"],
            }
        )
    effects_rows = []
    for p, e in dict.fromkeys(
        (r["spot_file"], r["representation"]) for r in report["effects"]
    ):
        for seed in report["config"]["seeds"]:
            selected = [
                r
                for r in report["effects"]
                if (r["spot_file"], r["representation"], r["seed"]) == (p, e, seed)
            ]
            effects_rows.append(
                {
                    "spot_file": p,
                    "representation": e,
                    "seed": seed,
                    **{
                        k.replace("_chips", "_percent_pot"): sum(
                            50 * r[k] / r["pot"] for r in selected
                        )
                        for k in (
                            "gap_change_chips",
                            "turn_effect_chips",
                            "river_effect_chips",
                            "interaction_chips",
                        )
                    },
                }
            )
    means = []
    for p, e in dict.fromkeys(
        (r["spot_file"], r["representation"]) for r in effects_rows
    ):
        selected = [
            r for r in effects_rows if (r["spot_file"], r["representation"]) == (p, e)
        ]
        means.append(
            {
                "spot_file": p,
                "representation": e,
                **{
                    k: statistics.mean(r[k] for r in selected)
                    for k in (
                        "gap_change_percent_pot",
                        "turn_effect_percent_pot",
                        "river_effect_percent_pot",
                        "interaction_percent_pot",
                    )
                },
            }
        )
    return hybrid, effects_rows, means


def render(root: Path, path: Path, audit_path: Path, output: Path) -> dict[str, Any]:
    report, _, error = replay(root, path)
    audit = json.loads(audit_path.read_text())
    maximum = checked_audit(path, report, audit)
    check_source(root, audit["source"])
    hybrid, attribution, means = tables(report)
    summary = {
        "status": "verified_fixed_policy_interventions",
        "input_sha256": digest(path),
        "audit_sha256": digest(audit_path),
        "crossed_profiles_checked": len(report["crossplay"]),
        "hybrid_profiles_checked": len(report["hybrids"]),
        "native_roots_checked": 4 * len(report["hybrids"]),
        "own_achieved_values_checked": 4 * len(report["hybrids"]),
        "maximum_native_error_chips": maximum,
        "maximum_own_replay_error_chips": error,
        "study_seconds": report["seconds"],
        "audit_seconds": audit["seconds"],
        "mean_attribution": means,
        "training_performed": False,
        "fresh_global_admission": False,
        "scope": (
            "saved-policy substitutions; not training-algorithm causality or "
            "a deployed hybrid"
        ),
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    for filename, rows in (
        ("crossplay.csv", report["crossplay"]),
        ("cross-targets.csv", report["cross_targets"]),
        ("hybrid-gaps.csv", hybrid),
        ("all-attributions.csv", attribution),
        ("mean-attributions.csv", means),
    ):
        write_csv(output / filename, rows)
    lines = [
        "# Frozen-policy seat and street interventions",
        "",
        "All effects below are percentage points of the initial "
        "pot, half-summed over responding seats and averaged across "
        "every sampled seed. Signed turn + river = change in the "
        "extra-information gap. Interaction is separate and is "
        "already shared between the two order-averaged effects.",
        "",
        "| Game | Representation | Extra-gap change | Turn "
        "contribution | River contribution | Interaction |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for r in means:
        lines.append(
            f"| {Path(r['spot_file']).stem} | {r['representation']} | "
            f"{r['gap_change_percent_pot']:.7g} | "
            f"{r['turn_effect_percent_pot']:.7g} | "
            f"{r['river_effect_percent_pot']:.7g} | "
            f"{r['interaction_percent_pot']:.7g} |"
        )
    lines += [
        "",
        "All seeds and target seats remain in raw receipts. "
        "Repeated FF controls are not independent observations. "
        "Extra-information roots depend on the fixed opponent and "
        "partition, not the responder's saved baseline. Crossed EVs "
        "hold opponents fixed; seat-balanced EV is antisymmetric "
        "and diagonal zero, not universal playing strength.",
        "",
        "These are frozen-policy interventions on known tiny games. "
        "Training update rules, work and traversal differ; the "
        "study does not identify a training-algorithm cause, "
        "guarantee retraining gains or deploy a hybrid. Exact "
        "responses respect hidden opponent cards. Native checks "
        "share exported mechanics and partitions.",
        "",
        "![Seat-balanced crossed payoff](crossed-payoffs.png)",
        "",
        "![Candidate opponent street gaps](street-gaps.png)",
        "",
    ]
    (output / "tables.md").write_text("\n".join(lines))
    plots(report, hybrid, output)
    return summary


def plots(report: dict[str, Any], hybrid: list[dict[str, Any]], output: Path) -> None:
    plt = importlib.import_module("matplotlib.pyplot")
    np = importlib.import_module("numpy")
    config = report["config"]
    paths = config["spot_files"]
    names = labels(config)
    fig, axes = plt.subplots(1, len(paths), figsize=(7 * len(paths), 5), squeeze=False)
    selected = [
        r for r in report["crossplay"] if r["representation"] == "texture_range_q8_b8"
    ]
    cap = (
        max(abs(100 * r["seat_balanced_first_chips"] / r["pot"]) for r in selected)
        or 1e-12
    )
    for ax, path in zip(axes[0], paths, strict=True):
        a = np.array(
            [
                [
                    next(
                        100 * r["seat_balanced_first_chips"] / r["pot"]
                        for r in selected
                        if (r["spot_file"], r["first"], r["second"]) == (path, i, j)
                    )
                    for j in names
                ]
                for i in names
            ]
        )
        im = ax.imshow(a, cmap="RdBu", vmin=-cap, vmax=cap)
        for (i, j), v in np.ndenumerate(a):
            ax.text(
                j,
                i,
                f"{v:.3g}",
                ha="center",
                va="center",
                color="black" if abs(v) < 0.65 * cap else "white",
                fontsize=8,
            )
        ax.set_xticks(range(len(names)), names, rotation=20, ha="right")
        ax.set_yticks(range(len(names)), names)
        ax.set(
            title=Path(path).stem, xlabel="Column opponent policy", ylabel="Row policy"
        )
        fig.colorbar(im, ax=ax, label="Seat-balanced row EV (% initial pot)")
    fig.suptitle(
        "Range-mass candidate: frozen crossed policies; positive favors row",
        fontsize=11,
    )
    fig.tight_layout()
    fig.savefig(output / "crossed-payoffs.png", dpi=160)
    plt.close(fig)
    fig, axes = plt.subplots(
        1, len(paths), figsize=(7 * len(paths), 4.7), squeeze=False
    )
    for ax, path in zip(axes[0], paths, strict=True):
        means = [
            statistics.mean(
                r["extra_percent_pot"]
                for r in hybrid
                if r["spot_file"] == path
                and r["representation"] == "texture_range_q8_b8"
                and r["combination"] == c
            )
            for c in config["street_combinations"]
        ]
        ax.bar(["Full/full", "Sampled turn", "Sampled river", "Sampled both"], means)
        ax.set(
            title=Path(path).stem, ylabel="Extra exact-information gap (% initial pot)"
        )
        ax.tick_params(axis="x", rotation=15, labelsize=8)
        ax.grid(axis="y", alpha=0.2)
    fig.suptitle(
        "Candidate opponent street substitutions: mean over all seeds; no training",
        fontsize=11,
    )
    fig.tight_layout()
    fig.savefig(output / "street-gaps.png", dpi=160)
    plt.close(fig)
