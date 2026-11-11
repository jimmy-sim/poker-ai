"""Cached terminal inspection of fixed-turn continuation values."""

import argparse
from pathlib import Path
from typing import Any

from poker_ai.evaluation.turn_continuation_io import FOLDER, load
from poker_ai.evaluation.turn_continuation_math import PANELS


def show(profile: dict[str, Any], seat: int, rank: int) -> None:
    response = profile["responses"][seat]
    groups = response["top_turn_groups"]
    if not 1 <= rank <= max(1, len(groups)):
        raise ValueError("choose an available positive turn-group rank")
    print(
        f"\n{profile['game']} / {profile['seed']} / {profile['arm']} / "
        f"responding seat {seat}"
    )
    print(
        "Cached hash-checked own calculation; fixed saved opponent; "
        "no new native audit."
    )
    print(
        "First three panels freeze every own turn and opponent row; "
        "full reply may change turns."
    )
    print("Responding-seat root net chips:")
    for name in PANELS:
        print(f"  {name}: {response['root_values_chips'][name]:.9f}")
    print(
        "Root increments (restricted river / finer river / full-reply turns): "
        + " / ".join(f"{v:.9f}" for v in response["root_increments_chips"])
    )
    print(
        "Root increments are distinct from the earlier turn/river row-loss attribution."
    )
    if not groups:
        print("No supported own turn groups; full unsupported rows remain saved.")
        return
    group = groups[rank - 1]
    print(
        f"\nTurn group {rank}/{len(groups)}, row {group['abstract_info']}; "
        f"prior full-reply loss {group['prior_loss_chips']:.9f} chips."
    )
    print(
        "Ranked by prior trace loss; these conditional action values "
        "are not additive losses."
    )
    lookup = {r["exact_info"]: r for r in response["turn_rows"]}
    for info in group["infos"]:
        row = lookup[info]
        print(
            f"\nOwn {' '.join(row['hole'])}; board {' '.join(row['board'])}; "
            f"{row['hand_category']}; pot {row['pot']}"
        )
        print(
            f"Chance-opponent support {row['support']:.9g}; "
            f"saved full reach {row['saved_reach_mass']:.9g}"
        )
        for history in row["history"]:
            print(
                f"  history: seat {history['seat']} {history['street']} "
                f"{history['kind']} {history['amount']}; "
                f"paid {history['chips_paid']}"
            )
        q = row["conditional_action_values_chips"]
        print(
            "  action | saved probability | "
            "saved / restricted-river / fine-river / full-reply net chips"
        )
        for column, action in enumerate(row["actions"]):
            values = " / ".join(f"{q[name][column]:.6f}" for name in PANELS)
            print(f"  {action}: {row['saved_probabilities'][column]:.6f} | {values}")
        for name in PANELS:
            best = max(range(len(row["actions"])), key=lambda c: q[name][c])
            print(f"  preferred with {name}: {row['actions'][best]}")
    print(
        "Continuation-specific local deviations inside this saved simulation, "
        "not universal poker advice."
    )


def main(root: Path) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=Path(FOLDER))
    parser.add_argument(
        "--game", choices=("dev_low_oop", "dev_medium_oop"), default="dev_medium_oop"
    )
    parser.add_argument(
        "--seed", type=int, choices=(20261301, 20261302, 20261303), default=20261302
    )
    parser.add_argument(
        "--arm",
        choices=("coarse_self", "coarse_pair", "mixed_pair", "fine_self"),
        default="mixed_pair",
    )
    parser.add_argument("--seat", type=int, choices=(0, 1), default=1)
    parser.add_argument("--rank", type=int, default=1)
    parser.add_argument("--interactive", action="store_true")
    args = parser.parse_args()
    print("Checking cached continuation and original-source hashes...", flush=True)
    profiles = load(root, root / args.report)
    current = dict(game=args.game, seed=args.seed, arm=args.arm)
    rank = args.rank
    choices: dict[str, tuple[Any, ...]] = dict(
        game=("dev_low_oop", "dev_medium_oop"),
        seed=(20261301, 20261302, 20261303),
        arm=("coarse_self", "coarse_pair", "mixed_pair", "fine_self"),
    )
    while True:
        profile = next(
            p for p in profiles if all(p[k] == v for k, v in current.items())
        )
        show(profile, args.seat, rank)
        if not args.interactive:
            return 0
        try:
            key = (
                input("\nn/p group / s seed / o method / g game / t seat / q quit: ")
                .strip()
                .lower()
            )
        except (EOFError, KeyboardInterrupt):
            print("\nLeaving saved continuations.")
            return 0
        if key == "q":
            return 0
        if key in ("g", "s", "o"):
            field = {"g": "game", "s": "seed", "o": "arm"}[key]
            values = choices[field]
            current[field] = values[(values.index(current[field]) + 1) % len(values)]
            rank = 1
        elif key == "t":
            args.seat = 1 - args.seat
            rank = 1
        elif key in ("n", "p"):
            count = max(1, len(profile["responses"][args.seat]["top_turn_groups"]))
            rank = 1 + (rank - 1 + (1 if key == "n" else -1)) % count
        else:
            print("Choose n, p, s, o, g, t or q.")
