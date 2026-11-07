"""Inspect a recorded conflicting row; no training or live-game integration."""

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--report", type=Path, default=Path("results/board-diagnosis/diagnosis.json")
    )
    parser.add_argument("--game", default="dev_medium_oop")
    parser.add_argument(
        "--panel", choices=("own_exact_full", "uniform"), default="own_exact_full"
    )
    parser.add_argument("--rank", type=int, default=1)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    raw = json.loads((root / args.report).read_text())
    cases = [
        c for c in raw["cases"] if c["spot"] == args.game and c["panel"] == args.panel
    ]
    if len(cases) != 1 or not 1 <= args.rank <= len(cases[0]["top_groups"]):
        parser.error("choose a recorded game/panel and an available 1-based rank")
    group = cases[0]["top_groups"][args.rank - 1]
    print(f"{args.game}, {args.panel}, texture row {group['abstract_info']}")
    print("Local frozen-own-continuation values; this score is not game EV loss.")
    print(
        f"Sharing score: {group['local_sharing_cost_chips_per_decision']:.6g} "
        "chips/weighted decision"
    )
    for example in group["examples"]:
        print(
            f"\nSeat {example['seat']}; own cards {' '.join(example['hole'])}; "
            f"board {' '.join(example['board'])}"
        )
        print(
            f"{example['hand_category']}; pot {example['pot']}; "
            f"preferred: {', '.join(example['preferred_actions'])}"
        )
        for action, value in zip(
            example["actions"], example["conditional_action_values_chips"], strict=True
        ):
            print(f"  {action}: {value:.6f} net chips")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
