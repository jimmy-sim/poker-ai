"""Show saved counterstrategy examples offline; does not train or play poker."""

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--report", type=Path, default=Path("results/range-mass-replies/diagnosis.json")
    )
    parser.add_argument("--game", default="dev_medium_oop")
    parser.add_argument("--representation", default="texture_range_q8_b8")
    parser.add_argument("--seat", type=int, choices=(0, 1), default=0)
    parser.add_argument("--training", choices=("sampled", "full"), default="sampled")
    parser.add_argument("--seed", type=int, default=20261301)
    parser.add_argument("--rank", type=int, default=1)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    raw = json.loads((root / args.report).read_text())
    cases = [
        c
        for c in raw["cases"]
        if c["spot"] == args.game
        and c["representation"] == args.representation
        and c["training"] == args.training
        and c["seed"] == (args.seed if args.training == "sampled" else None)
    ]
    if len(cases) != 1:
        parser.error("choose a saved game and representation")
    case = cases[0]
    response = case["responses"][args.seat]
    if not 1 <= args.rank <= len(response["top_groups"]):
        parser.error("choose an available positive rank; near-zero cases may have none")
    group = response["top_groups"][args.rank - 1]
    print(
        f"{case['spot']}/{case['representation']}, responding seat {args.seat}, "
        f"row {group['abstract_info']}; {args.training}; seed {case['seed']}"
    )
    print(
        "Fixed saved opponent; own best-reply continuation. "
        "Values are not universal poker advice."
    )
    print(f"Total unilateral gain: {response['exact_gain_chips']:.6g} chips")
    print(
        f"Within-partition gain: {response['within_partition_gain_chips']:.6g}; "
        f"extra information: {response['extra_information_value_chips']:.6g}"
    )
    print(f"This row's additive loss: {group['loss_contribution_chips']:.6g} chips")
    for row in group["examples"]:
        print(
            f"\nOwn {' '.join(row['hole'])}; board {' '.join(row['board'])}; "
            f"{row['hand_category']}; {row['street']}"
        )
        print(
            f"Best reply: {row['reply_action']}; "
            f"saved reach: {row['saved_reach_mass']:.6g}"
        )
        for action, probability, value in zip(
            row["actions"],
            row["saved_probabilities"],
            row["reply_continuation_values_chips"],
            strict=True,
        ):
            print(
                f"  {action}: saved probability {probability:.6f}; "
                f"reply-suffix value {value:.6f} chips"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
