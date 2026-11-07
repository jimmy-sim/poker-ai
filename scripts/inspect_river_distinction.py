"""Inspect saved river conflicts offline; no training or online poker advice."""

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--report", type=Path, default=Path("results/river-distinctions/diagnosis.json")
    )
    parser.add_argument("--game", default="dev_medium_oop")
    parser.add_argument("--representation", default="texture_made_b8")
    parser.add_argument("--seat", type=int, choices=(0, 1), default=0)
    parser.add_argument(
        "--prefix",
        choices=("restricted_prefix", "exact_prefix"),
        default="exact_prefix",
    )
    parser.add_argument("--rank", type=int, default=1)
    args = parser.parse_args()
    if args.rank < 1:
        parser.error("choose a positive rank")
    root = Path(__file__).resolve().parents[1]
    report = json.loads((root / args.report).read_text())
    cases = [
        c
        for c in report["cases"]
        if c["spot"] == args.game and c["representation"] == args.representation
    ]
    if len(cases) != 1:
        parser.error("choose a saved game/representation")
    response = cases[0]["responses"][args.seat]
    panel = next(p for p in response["panels"] if p["prefix"] == args.prefix)
    print(
        f"{args.game}/{args.representation}; responding seat {args.seat}; {args.prefix}"
    )
    print(
        f"River-only gain: {panel['river_gain_chips']:.6g} target chips; "
        f"strict conflicting rows: {panel['conflicting_rows']}"
    )
    if not panel["top_groups"]:
        print("No strict reachable merged-row conflicts in this panel.")
        return 0
    if not 1 <= args.rank <= len(panel["top_groups"]):
        parser.error("choose an available positive rank")
    group = panel["top_groups"][args.rank - 1]
    print(
        f"Shared row {group['abstract_info']}; "
        f"panel loss {group['loss_chips']:.6g} chips; diagnostic probes only"
    )
    print(
        "Declared opponent range order:",
        group["examples"][0]["declared_opponent_range"],
    )
    print("Relations: -1 own loss, 0 tie, +1 own win, None blocked.")
    for row in group["examples"]:
        print(
            f"\nOwn {' '.join(row['hole'])}; board {' '.join(row['board'])}; "
            f"own rank {row['features']['own_rank']}"
        )
        best = ", ".join(row["actions"][i] for i in row["near_optimal_columns"])
        print(
            f"Near-best actions: {best}; "
            f"reach {row['panels'][args.prefix]['reach']:.6g}"
        )
        print(
            f"Range compatibility: {row['features']['range_compatibility']}; "
            f"relations: {row['features']['range_relations']}"
        )
        print(
            f"Conditional opponent range weights: {row['conditional_opponent_range']}"
        )
        for action, p, q in zip(
            row["actions"],
            row["restricted_probabilities"],
            row["conditional_values_chips"],
            strict=True,
        ):
            print(
                f"  {action}: restricted probability {p:.6f}; "
                f"exact-river-suffix value {q:.6f} chips"
            )
    print(
        "\nFixed saved opponent and own reply suffix; no feature trained or deployed."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
