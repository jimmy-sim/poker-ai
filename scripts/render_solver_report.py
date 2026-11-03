"""Generate diagnostic tables and honest claim drafts from saved solver runs."""

import argparse
import csv
import hashlib
import json
import statistics
from pathlib import Path
from typing import Any

from poker_ai.validation.five_card import source_provenance


def diagnostic_rows(report: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    config = report["config"]
    for spot in report["spots"]:
        primary = [
            r
            for r in spot["comparisons"]
            if r["buckets"] == config["primary_buckets"]
            and r["iteration"] == config["primary_iteration"]
        ]
        total_ev = statistics.mean(
            r["hero_ev_gap_vs_reference_opponent"] for r in primary
        )
        fallback_ev = statistics.mean(
            sum(
                v
                for key, v in r["ev_gap_attribution_vs_reference"].items()
                if key != "matched"
            )
            for r in primary
        )
        row = {
            "spot": spot["name"],
            "reference_policy_change_pp": 100 * spot["reference_stability_action_gap"],
            "reference_exploitability_over_pot": spot["reference_exploitability"]
            / spot["pot"],
            "fallback_ev_contribution_chips": fallback_ev,
            "total_ev_gap_chips": total_ev,
            "fallback_ev_deficit_accounting_share": None
            if total_ev == 0
            else fallback_ev / total_ev,
            "max_native_value_error": max(
                r["max_native_value_error"] for r in spot["comparisons"]
            ),
            "worlds_checked": spot["controls"]["worlds_checked"],
            "projection_mass": max(r["projection_mass"] for r in spot["comparisons"]),
            "shadow_changes": sum(r["shadow_changes"] for r in spot["comparisons"]),
        }
        for dimension, fixed, fixed_value in (
            ("buckets", "iteration", config["primary_iteration"]),
            ("iteration", "buckets", config["primary_buckets"]),
        ):
            for value in sorted({r[dimension] for r in spot["comparisons"]}):
                selected = [
                    r
                    for r in spot["comparisons"]
                    if r[dimension] == value and r[fixed] == fixed_value
                ]
                row[f"{dimension}_{value}_action_gap"] = statistics.mean(
                    r["action_gap"] for r in selected
                )
                row[f"{dimension}_{value}_exploitability_over_pot"] = statistics.mean(
                    r["exploitability"] / spot["pot"] for r in selected
                )
        rows.append(row)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    output = args.output_dir
    report_path, tier_path = output / "postflop.json", output / "tier-a.json"
    report, tier = (
        json.loads(report_path.read_text()),
        json.loads(tier_path.read_text()),
    )
    if report["status"] != "passed" or tier["status"] != "passed":
        raise ValueError("cannot draft verified claims from failed reports")
    rows = diagnostic_rows(report)
    csv_path = output / "diagnosis.csv"
    with csv_path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    lines = [
        "| Turn subgame | Ref. policy change (pp) | "
        "EV deficit accounted for at fallback nodes | "
        "Action gap: 100 → 1,000 iters (pp) |",
        "| --- | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| {row['spot']} | {row['reference_policy_change_pp']:.3f} | "
            f"{100 * row['fallback_ev_deficit_accounting_share']:.1f}% | "
            f"{100 * row['iteration_100_action_gap']:.2f} → "
            f"{100 * row['iteration_1000_action_gap']:.2f} |"
        )
    lines += [
        "",
        "Fallback shares use the exact performance-difference identity, "
        "averaged across the three primary seeds. They are an EV accounting "
        "decomposition, not a causal estimate for extra training. Reference "
        "policy changes use the final reference reach weights.",
    ]
    diagnosis = output / "diagnosis.md"
    diagnosis.write_text("\n".join(lines) + "\n")
    max_gap = max(r["exploitability_gap"] for r in tier["rows"])
    mean_gap = statistics.mean(r["action_gap"] for r in report["primary_summary"])
    worlds = sum(row["worlds_checked"] for row in rows)
    nodes = sum(s["nodes"] for s in report["spots"])
    worse = sum(
        r["own_exploitability_pot_fraction"]
        > r["reference_exploitability_pot_fraction"]
        for r in report["primary_summary"]
    )
    losses = sum(r["ev_gap_vs_reference_chips"] < 0 for r in report["primary_summary"])
    claims = output / "verified-claims.md"
    claims.write_text(
        "# Verified claim drafts\n\n"
        f"- Implemented four exact CFR variants for Kuhn and Leduc; matched "
        f"OpenSpiel 2.0.2 exploitability within {max_gap:.3g} ante chips/hand "
        "at the tested equal iteration budgets. This is implementation agreement, "
        "not zero remaining exploitability.\n"
        f"- Built a reproducible external-solver comparison across {len(rows)} "
        f"restricted turn subgames; measured {100 * mean_gap:.2f} percentage points "
        "mean action-frequency gap versus OpenSpiel CFR+ (equal spot weighting, "
        "three fixed agent seeds, reference-reach-weighted node MAE). The agent "
        f"had higher restricted exploitability in {worse}/{len(rows)} spots and "
        f"lower hero EV versus the reference opponent in {losses}/{len(rows)}; "
        "this is not a full-game "
        "win-rate claim.\n"
        f"- Verified every exported node in {nodes:,} restricted-game tree nodes "
        f"against OpenSpiel's parser and {worlds:,} passive private-card/river "
        "worlds against independent Treys showdown ranks and expected payouts. "
        "The exported mechanics are project code, so parser/solver agreement "
        "alone is not an independent full-engine validation.\n"
    )
    table = [
        "| Game | Variant | Iterations | Own exploitability | "
        "Ref. exploitability | Mean strategy L1 | Kuhn value error |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for game in ("kuhn", "leduc"):
        for variant in tier["config"]["variants"]:
            row = max(
                (
                    r
                    for r in tier["rows"]
                    if r["game"] == game and r["variant"] == variant
                ),
                key=lambda r: r["iteration"],
            )
            error = (
                "—"
                if row["kuhn_value_error"] is None
                else f"{row['kuhn_value_error']:.8g}"
            )
            table.append(
                f"| {game} | {variant} | {row['iteration']:,} | "
                f"{row['exploitability']:.8g} | "
                f"{row['reference_exploitability']:.8g} | "
                f"{row['strategy_mean_l1']:.8g} | {error} |"
            )
    tier_table = output / "tier-a-summary.md"
    tier_table.write_text("\n".join(table) + "\n")
    root = Path(__file__).resolve().parents[1]
    manifest = {
        "status": "passed",
        "source": source_provenance(
            root,
            root / "configs/solver-validation-postflop.json",
            entrypoints=("scripts/render_solver_report.py",),
        ),
        "inputs_sha256": {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (report_path, tier_path)
        },
        "artifacts_sha256": {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (csv_path, diagnosis, claims, tier_table)
        },
    }
    (output / "render-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    )
    print("passed: diagnostic tables and verified claim drafts", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
