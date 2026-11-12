"""Inspect cached public blockers and all grouping controls, never live play."""

import argparse
from pathlib import Path
from typing import Any

from poker_ai.evaluation.range_blocker_io import FOLDER, Cache, load
from poker_ai.evaluation.range_blocker_probe import CONTROLS, SUFFIXES


def show(
    cache: Cache, profile: dict[str, Any], target: int, suffix: int, rank: int
) -> None:
    summary = profile["responses"][target]["suffixes"][suffix]
    detail, old = cache.detail(profile)
    groups = summary["top_source_groups"]
    if not 1 <= rank <= max(1, len(groups)):
        raise ValueError("choose an available positive source-group rank")
    print(
        f"\n{profile['game']} / {profile['seed']} / {profile['arm']} / "
        f"seat {target} / {summary['suffix']}"
    )
    print("Cached public-range grouping diagnostic; fixed source Q and weights.")
    print("Local costs: chips per weighted decision, not root EV or trained gains.")
    print("control | actual cost / prior cost | actual conflicts / prior conflicts")
    for control in CONTROLS:
        a, p = (w["group_controls"][control] for w in summary["panels"])
        print(
            f"  {control}: "
            f"{a['local_sharing_cost_chips_per_weighted_decision']:.9g} / "
            f"{p['local_sharing_cost_chips_per_weighted_decision']:.9g}; "
            f"{a['strict_conflicting_groups']} / {p['strict_conflicting_groups']} "
            f"of {a['total_groups']} groups; source conflicts resolved "
            f"{a['source_conflicting_groups_resolved']} / "
            f"{p['source_conflicting_groups_resolved']}"
        )
    print("Both-public and joint controls are redundant with fixed declared ranges.")
    if not groups:
        print("No source-supported groups; unsupported rows remain saved and unranked.")
        return
    group_id = groups[rank - 1]
    new = detail["responses"][target]
    source = old["responses"][target]["suffixes"][suffix]
    lookup = {r["exact_info"]: r for r in source["rows"]}
    baseline = next(
        g for g in new["partitions"][0]["groups"] if g["source_group_id"] == group_id
    )
    bindings = {r["exact_info"]: r["feature"] for r in new["row_features"]}
    print(f"\nSource static group {rank}/{len(groups)}: {group_id}")
    print(
        "Declared range order by seat:", cache.book.record()["ranges"][profile["game"]]
    )
    candidates = [lookup[i] for i in baseline["supported_infos"]]
    chosen, seen = [], set()
    for row in candidates:
        f = cache.book.features[bindings[row["exact_info"]]]
        q = row["actual_action_values_chips"]
        key = f.available, max(range(len(q)), key=lambda i: q[i])
        if key not in seen:
            chosen.append(row)
            seen.add(key)
    chosen.extend(r for r in candidates if r not in chosen)
    print(
        "Up to four deterministic examples; distinct masks/actions first. "
        "All rows retained."
    )
    for row in chosen[:4]:
        f = cache.book.features[bindings[row["exact_info"]]]
        print(
            f"\nOwn {' '.join(row['hole'])}; board {' '.join(row['board'])}; "
            f"pot {row['pot']}"
        )
        print("Public availability seat0 / seat1:", f.available)
        print(
            "Joint matrix: rows seat0 alternatives, columns seat1 alternatives:",
            f.joint,
        )
        print(
            f"Source CF support {row['counterfactual_support']:.9g}; "
            f"fixed exposure {row['uniform_decision_weight']:.9g}"
        )
        for i, action in enumerate(row["actions"]):
            print(
                f"  {action}: actual Q {row['actual_action_values_chips'][i]:.6f}; "
                f"prior Q {row['prior_action_values_chips'][i]:.6f}"
            )
    print(
        "No actual opponent hand is revealed; own alternatives use public cards only."
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
    print(
        "Checking complete cached blocker report and parent-source hashes...",
        flush=True,
    )
    cache = load(root, root / args.report)
    current = dict(game=args.game, seed=args.seed, arm=args.arm)
    rank, suffix = args.rank, SUFFIXES.index(args.suffix)
    choices: dict[str, tuple[Any, ...]] = dict(
        game=("dev_low_oop", "dev_medium_oop"),
        seed=(20261301, 20261302, 20261303),
        arm=("coarse_self", "coarse_pair", "mixed_pair", "fine_self"),
    )
    while True:
        profile = next(
            p for p in cache.profiles if all(p[k] == v for k, v in current.items())
        )
        show(cache, profile, args.seat, suffix, rank)
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
            print("\nLeaving cached blocker report.")
            return 0
        if key == "q":
            return 0
        if key in ("s", "o", "g"):
            field = {"s": "seed", "o": "arm", "g": "game"}[key]
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
                1,
                len(
                    profile["responses"][args.seat]["suffixes"][suffix][
                        "top_source_groups"
                    ]
                ),
            )
            rank = 1 + (rank - 1 + (1 if key == "n" else -1)) % count
        else:
            print("Choose n, p, s, o, g, t, r or q.")
