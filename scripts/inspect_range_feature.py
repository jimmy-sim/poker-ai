"Inspect the prospective static-prior river feature; no action selection/training."

import argparse
import json
from pathlib import Path

from poker_ai.abstraction.range_mass import MASS_ORDER, river_mass
from poker_ai.cards import format_card, parse_card
from poker_ai.postflop.game import load_spot
from poker_ai.postflop.range_protocol import check_inputs, range_context


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("river", nargs="?", default="9h")
    parser.add_argument(
        "--protocol", type=Path, default=Path("configs/range-mass-protocol.json")
    )
    parser.add_argument("--spot", default="configs/learning-spots/dev_medium_oop.json")
    parser.add_argument("--seat", type=int, choices=(0, 1), default=0)
    parser.add_argument("--hole", nargs=2, default=["Tc", "Td"])
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    try:
        config = json.loads((root / args.protocol).read_text())
        check_inputs(root, config)
        if args.spot not in config["spot_files"]:
            raise ValueError("choose a pinned protocol spot")
        spot = load_spot(root / args.spot)
        if len(spot.board) != 4:
            raise ValueError("this inspector expects a turn-start spot")
        context = range_context(spot)
        hole = tuple(parse_card(c) for c in args.hole)
        if tuple(sorted(hole)) not in context.priors[args.seat].combos:
            raise ValueError("choose an own hand from the declared context")
        board = spot.board + (parse_card(args.river),)
        prior = context.priors[1 - args.seat]
        mass = river_mass(hole, board, prior)
    except (ValueError, TypeError, ArithmeticError) as error:
        parser.error(str(error))
    print(
        json.dumps(
            {
                "candidate": config["candidate"],
                "context_sha256": context.identifier,
                "own_cards": args.hole,
                "board": [format_card(c) for c in board],
                "opponent_static_prior": [
                    {"cards": [format_card(c) for c in h], "mass": str(m)}
                    for h, m in zip(prior.combos, prior.masses, strict=True)
                ],
                "prior_mass": {
                    k: str(v) for k, v in zip(MASS_ORDER, mass.masses, strict=True)
                },
                "feature_bins": dict(zip(MASS_ORDER, mass.bins, strict=True)),
                "conditional_static_showdown_equity": str(mass.conditional_equity),
                "scope": (
                    "encoding only; fixed prior, no betting posterior or "
                    "strategy/action output"
                ),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
