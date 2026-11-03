"""Generate diagnostic tables and honest claim drafts from saved solver runs."""

import argparse
import csv
import gzip
import hashlib
import json
import statistics
from pathlib import Path
from typing import Any

import numpy as np

from poker_ai.abstraction.model import CardAbstraction
from poker_ai.solver_validation.abstraction_check import check_model
from poker_ai.solver_validation.reference import SpotTree
from poker_ai.solver_validation.reporting import plot_strategy
from poker_ai.solver_validation.spots import load_spot
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
    training_path = output / "agent-training.json"
    training = json.loads(training_path.read_text())
    models = {}
    for relative, expected in training["model_sha256"].items():
        model_path = root / relative
        if hashlib.sha256(model_path.read_bytes()).hexdigest() != expected:
            raise ValueError("abstraction model changed since agent training")
        models[relative] = CardAbstraction.load(model_path)
    collision_rows = []
    for spot in report["spots"]:
        spot_path = root / "configs/spots" / (spot["name"] + ".json")
        if hashlib.sha256(spot_path.read_bytes()).hexdigest() != spot["config_sha256"]:
            raise ValueError("spot changed since the recorded comparison")
        tree = SpotTree.build(load_spot(spot_path))
        reference_path = output / spot["reference_file"]
        if (
            hashlib.sha256(reference_path.read_bytes()).hexdigest()
            != report["artifacts_sha256"][reference_path.name]
        ):
            raise ValueError("reference policy changed since comparison")
        reference = json.loads(gzip.decompress(reference_path.read_bytes()))
        if (
            reference["format"] != "poker-ai-reference-comparison-only-v1"
            or tuple(reference["information_keys"]) != tree.keys
        ):
            raise ValueError("reference/abstraction diagnostic alignment failed")
        policy = tuple(tuple(row) for row in reference["policy"])
        tree.validate_policy(policy)
        for relative, model in models.items():
            collision_rows.append(
                dict(
                    spot=spot["name"],
                    model=relative,
                    **check_model(tree, model, policy),
                )
            )
    collision_path = output / "abstraction-aliases.csv"
    with collision_path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(collision_rows[0]))
        writer.writeheader()
        writer.writerows(collision_rows)
    extra_plots = []
    hand_rows = []
    for spot in report["spots"]:
        primary = [
            r
            for r in spot["comparisons"]
            if r["buckets"] == report["config"]["primary_buckets"]
            and r["iteration"] == report["config"]["primary_iteration"]
        ]
        roots = []
        for run in primary:
            details_path = output / run["details_file"]
            if (
                hashlib.sha256(details_path.read_bytes()).hexdigest()
                != report["artifacts_sha256"][details_path.name]
            ):
                raise ValueError("node artifact changed since the recorded run")
            details = json.loads(gzip.decompress(details_path.read_bytes()))
            roots.append(
                [
                    r
                    for r in details["decision_rows"]
                    if r["owner"] == spot["config"]["hero"]
                    and len(r["public_state"]["history"])
                    == len(spot["config"]["prefix_actions"])
                ]
            )
        first = roots[0]
        if not first or any(
            [r["hand_class"] for r in x] != [r["hand_class"] for r in first]
            for x in roots
        ):
            raise ValueError("root heatmap alignment failed")
        matrix = {
            "spot": spot["name"],
            "classes": [r["hand_class"] for r in first],
            "actions": [
                kind if amount is None else f"raise-to {amount}"
                for kind, amount in first[0]["actions"]
            ],
            "reference": [r["reference_probabilities"] for r in first],
            "own": np.mean(
                [[r["own_probabilities"] for r in group] for group in roots], axis=0
            ).tolist(),
        }
        extra_plots.extend(plot_strategy(matrix, output, spot["name"] + "-strategy"))
        for label in sorted(primary[0]["hero_hand_class_ev_gaps"]):
            row = {
                "spot": spot["name"],
                "hero": spot["config"]["hero"],
                "hand_class": label,
            }
            for opponent in ("reference", "own"):
                values = [
                    r["hero_hand_class_ev_gaps"][label][
                        "versus_" + opponent + "_opponent"
                    ]
                    for r in primary
                ]
                row["ev_gap_vs_" + opponent + "_opponent_chips"] = statistics.mean(
                    values
                )
                row["ev_gap_vs_" + opponent + "_opponent_min"] = min(values)
                row["ev_gap_vs_" + opponent + "_opponent_max"] = max(values)
            hand_rows.append(row)
    hand_csv = output / "hand-class-ev.csv"
    with hand_csv.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(hand_rows[0]))
        writer.writeheader()
        writer.writerows(hand_rows)
    hand_lines = [
        "| Turn subgame | Hero hand class | EV gap vs ref. opponent (chips) | "
        "EV gap vs own opponent (chips) |",
        "| --- | --- | ---: | ---: |",
    ]
    for hand_row in hand_rows:
        hand_lines.append(
            f"| {hand_row['spot']} | {hand_row['hand_class']} | "
            f"{hand_row['ev_gap_vs_reference_opponent_chips']:+.4f} | "
            f"{hand_row['ev_gap_vs_own_opponent_chips']:+.4f} |"
        )
    hand_markdown = output / "hand-class-ev.md"
    hand_markdown.write_text("\n".join(hand_lines) + "\n")
    alias_lines = [
        "| Spot | Merged ref. reach: 2 / 4 / 8 buckets | Exact infos → 8-bucket keys |",
        "| --- | ---: | ---: |",
    ]
    for spot in report["spots"]:
        selected = [r for r in collision_rows if r["spot"] == spot["name"]]
        selected.sort(key=lambda r: int(Path(r["model"]).stem.rsplit("-", 1)[1]))
        percentages = " / ".join(
            f"{100 * r['reference_reach_in_merged_groups']:.3f}%" for r in selected
        )
        final = selected[-1]
        alias_lines.append(
            f"| {spot['name']} | {percentages} | "
            f"{final['exact_information_sets']:,} → "
            f"{final['abstract_information_sets']:,} |"
        )
    alias_lines += [
        "",
        "A merged group contains multiple exact information sets "
        "with the same own abstract key, including different revealed "
        "river boards. This measures representation collisions inside "
        "these spots, not EV loss or aliases with other global states.",
    ]
    alias_markdown = output / "abstraction-aliases.md"
    alias_markdown.write_text("\n".join(alias_lines) + "\n")
    manifest = {
        "status": "passed",
        "source": source_provenance(
            root,
            root / "configs/solver-validation-postflop.json",
            entrypoints=("scripts/render_solver_report.py",),
        ),
        "inputs_sha256": {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (report_path, tier_path, training_path)
        },
        "artifacts_sha256": {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (
                csv_path,
                diagnosis,
                claims,
                tier_table,
                collision_path,
                alias_markdown,
            )
        },
    }
    (output / "render-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    )
    print("passed: diagnostic tables and verified claim drafts", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
