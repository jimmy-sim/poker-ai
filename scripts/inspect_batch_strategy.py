"""Compare verified saved own action probabilities; optionally browse n/p/q."""

import argparse
from pathlib import Path

from poker_ai.evaluation.batch_strategy_viewer import (
    READOUTS,
    Selection,
    browse,
    display,
    load,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--game", choices=("dev_low_oop", "dev_medium_oop"), default="dev_medium_oop"
    )
    parser.add_argument(
        "--representation",
        choices=("exact", "texture_range_q8_b8"),
        default="texture_range_q8_b8",
    )
    parser.add_argument("--rule", choices=("signed", "clipped"), default="signed")
    parser.add_argument(
        "--seed", type=int, choices=(20261301, 20261302, 20261303), default=20261301
    )
    parser.add_argument(
        "--work", type=int, choices=(100_000, 1_000_000, 10_000_000), default=10_000_000
    )
    parser.add_argument("--left", choices=READOUTS, default="current")
    parser.add_argument("--right", choices=READOUTS, default="linear_average")
    parser.add_argument("--left-batch", type=int, choices=(1, 4, 16), default=4)
    parser.add_argument("--right-batch", type=int, choices=(1, 4, 16), default=4)
    parser.add_argument("--seat", type=int, choices=(0, 1), default=0)
    parser.add_argument("--rank", type=int, default=1)
    parser.add_argument("--interactive", action="store_true")
    args = parser.parse_args()
    common = dict(
        game=args.game,
        representation=args.representation,
        rule=args.rule,
        seed=args.seed,
        work=args.work,
    )
    if args.rank < 1:
        parser.error("choose a positive rank")
    print(
        "Checking published own archives and audit receipts; "
        "loading once for browsing...",
        flush=True,
    )
    try:
        comparison = load(
            Path(__file__).resolve().parents[1],
            Selection(**common, batch=args.left_batch, readout=args.left),
            Selection(**common, batch=args.right_batch, readout=args.right),
        )
        if args.interactive:
            browse(comparison, args.seat, args.rank)
        else:
            print(display(comparison, args.seat, args.rank))
    except (ValueError, ArithmeticError) as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
