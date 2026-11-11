"""Cached local river range controls; no live play, learning or root-EV claim."""

import argparse
from pathlib import Path
from typing import Any

from poker_ai.evaluation.river_range_io import (
    FOLDER,
    GROUPS,
    SUFFIXES,
    load,
    load_detail,
)


def show(
    profile: dict[str, Any], detail: dict[str, Any], seat: int, suffix: int, rank: int
) -> None:
    response = profile["responses"][seat]
    summary = response["suffixes"][suffix]
    full = detail["responses"][seat]
    data = full["suffixes"][suffix]
    groups = summary["top_groups"]
    if not 1 <= rank <= max(1, len(groups)):
        raise ValueError("choose an available positive river-group rank")
    print(
        f"\n{profile['game']} / {profile['seed']} / {profile['arm']} / "
        f"responding seat {seat} / {summary['suffix']}"
    )
    print("Cached own local diagnostic; same saved opponent and own river suffix.")
    print(
        "Prior replacement is a LOCAL weight control, not a global strategy or root EV."
    )
    print(
        "Local sharing cost: chips per decision under fixed uniform exposure weights."
    )
    for control in GROUPS:
        print(f"\n{control}:")
        for panel in summary["panels"]:
            m = panel["group_controls"][control]
            cost = m["local_sharing_cost_chips_per_weighted_decision"]
            print(
                f"  {panel['range_weights']}: cost {cost:.9g}; "
                f"conflicts {m['strict_conflicting_groups']}/{m['total_groups']}; "
                f"common supported weight {m['supported_uniform_decision_weight']:.6f}"
            )
    print(
        "Declared hypothetical opponent range order:", full["declared_opponent_range"]
    )
    if not groups:
        print(
            "No supported river groups; unsupported rows remain retained and unranked."
        )
        return
    group = groups[rank - 1]
    print(
        f"\nGroup {rank}/{len(groups)}, row {group['abstract_info']}; "
        f"actual-weight local cost {group['local_cost']:.9g}."
    )
    print(
        "Display order uses actual-posterior local cost; all rows/groups remain saved."
    )
    lookup = {r["exact_info"]: r for r in data["rows"]}
    candidates = [lookup[i] for i in group["supported_infos"]]
    chosen = []
    seen = set()
    for row in candidates:
        q = row["actual_action_values_chips"]
        preferred = max(range(len(q)), key=lambda i: q[i])
        if preferred not in seen:
            chosen.append(row)
            seen.add(preferred)
    chosen.extend(r for r in candidates if r not in chosen)
    print(
        "Showing up to four deterministic examples; distinct preferred actions first."
    )
    for row in chosen[:4]:
        print(
            f"\nOwn {' '.join(row['hole'])}; board {' '.join(row['board'])}; "
            f"pot {row['pot']}"
        )
        print(
            f"Actual CF support {row['counterfactual_support']:.9g}; "
            f"saved own/full reach {row['saved_reach_mass']:.9g}; "
            f"uniform exposure weight {row['uniform_decision_weight']:.9g}"
        )
        print("Static diagnostic signatures:", row["static_features"])
        for i, combo in enumerate(full["declared_opponent_range"]):
            print(
                f"  hypothetical {' '.join(combo)}: compatible {row['compatible'][i]}; "
                f"posterior {row['actual_posterior'][i]:.6f}; "
                f"prior {row['compatible_prior'][i]:.6f}"
            )
        for a, action in enumerate(row["actions"]):
            conditional = " / ".join(
                f"{q[a]:.6f}" for q in row["combo_action_values_chips"]
            )
            print(
                f"  {action}: actual Q {row['actual_action_values_chips'][a]:.6f}; "
                f"prior Q {row['prior_action_values_chips'][a]:.6f}; "
                f"frozen combo-Q [{conditional}]"
            )
    print(
        "Range entries are hypothetical inputs. These local values use "
        "this saved simulation and fixed continuation."
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
    parser.add_argument("--suffix", choices=SUFFIXES, default=SUFFIXES[0])
    parser.add_argument("--rank", type=int, default=1)
    parser.add_argument("--interactive", action="store_true")
    args = parser.parse_args()
    folder = root / args.report
    print("Checking cached range report and bound source hashes...", flush=True)
    profiles = load(root, folder)
    cache: dict[str, dict[str, Any]] = {}
    current = dict(game=args.game, seed=args.seed, arm=args.arm)
    rank = args.rank
    suffix = SUFFIXES.index(args.suffix)
    choices: dict[str, tuple[Any, ...]] = dict(
        game=("dev_low_oop", "dev_medium_oop"),
        seed=(20261301, 20261302, 20261303),
        arm=("coarse_self", "coarse_pair", "mixed_pair", "fine_self"),
    )
    while True:
        p = next(p for p in profiles if all(p[k] == v for k, v in current.items()))
        if p["source_id"] not in cache:
            cache[p["source_id"]] = load_detail(folder, p)
        show(p, cache[p["source_id"]], args.seat, suffix, rank)
        if not args.interactive:
            return 0
        try:
            key = (
                input(
                    "\nn/p group / s seed / o method / g game / "
                    "t seat / r suffix / q quit: "
                )
                .strip()
                .lower()
            )
        except (EOFError, KeyboardInterrupt):
            print("\nLeaving saved local range report.")
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
        elif key == "r":
            suffix = 1 - suffix
            rank = 1
        elif key in ("n", "p"):
            count = max(
                1, len(p["responses"][args.seat]["suffixes"][suffix]["top_groups"])
            )
            rank = 1 + (rank - 1 + (1 if key == "n" else -1)) % count
        else:
            print("Choose n, p, s, o, g, t, r or q.")
