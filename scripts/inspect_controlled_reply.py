"""Inspect one frozen within-partition row; no live play or training."""

import argparse
from pathlib import Path

from poker_ai.evaluation.controlled_reply_inspect import display, inspect


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--report", type=Path, default=Path("results/controlled-replies/own.json")
    )
    parser.add_argument("--native", type=Path)
    parser.add_argument("--game", default="dev_medium_oop")
    parser.add_argument(
        "--representation",
        choices=("exact", "texture_range_q8_b8"),
        default="texture_range_q8_b8",
    )
    parser.add_argument("--training", choices=("sampled", "full"), default="sampled")
    parser.add_argument("--seed", type=int, default=20261301)
    parser.add_argument(
        "--regret-rule", choices=("signed", "clipped"), default="clipped"
    )
    parser.add_argument(
        "--average-weight", choices=("uniform", "linear"), default="linear"
    )
    parser.add_argument("--seat", type=int, choices=(0, 1), default=0)
    parser.add_argument("--rank", type=int, default=1)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    try:
        row = inspect(
            root,
            root / args.report,
            game=args.game,
            representation=args.representation,
            traversal="external" if args.training == "sampled" else "full",
            seed=args.seed if args.training == "sampled" else None,
            clip=args.regret_rule,
            average=args.average_weight,
            target=args.seat,
            rank=args.rank,
            native_path=(root / args.native) if args.native else None,
        )
    except ValueError as error:
        parser.error(str(error))
    print(display(row))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
