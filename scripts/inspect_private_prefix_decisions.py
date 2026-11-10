"""Browse the cached saved-decision diagnosis after checking its bound hashes."""

import argparse
import json
from pathlib import Path
from typing import Any

from poker_ai.postflop.pipeline_report import check_source
from poker_ai.postflop.river_study import digest

FOLDER = "results/private-prefix/decisions"
CONFIG = "configs/private-prefix-decisions.json"


def load(root: Path, folder: Path) -> list[dict[str, Any]]:
    manifest = json.loads((folder / "manifest.json").read_text())
    if (
        manifest["status"] != "complete_saved_decision_diagnosis"
        or manifest["config_sha256"] != digest(root / CONFIG)
        or manifest["profiles"] != 9
        or manifest["responses"] != 18
        or manifest["constructors_blocked"] is not True
        or any(
            manifest[k] is not False
            for k in (
                "training_performed",
                "reference_constructed",
                "new_agent_default",
                "fresh_global_admission",
            )
        )
    ):
        raise ArithmeticError("complete saved decision receipt required")
    config = json.loads((root / CONFIG).read_text())
    check_source(root, manifest["source"])
    if any(digest(folder / p) != h for p, h in manifest["outputs"].items()):
        raise ArithmeticError("cached decision report bytes changed")
    if any(
        digest(root / config[k]) != manifest[k + "_sha256"] for k in ("own", "native")
    ):
        raise ArithmeticError("bound decision input bytes changed")
    profiles: list[dict[str, Any]] = json.loads((folder / "summary.json").read_text())[
        "profiles"
    ]
    expected = {(s, r) for s in config["seeds"] for r in config["roles"]}
    if (
        len(profiles) != 9
        or {(p["seed"], p["role"]) for p in profiles} != expected
        or any([r["target"] for r in p["responses"]] != [0, 1] for p in profiles)
    ):
        raise ArithmeticError("complete cached decision panel required")
    return profiles


def show(profile: dict[str, Any], seat: int, rank: int) -> None:
    response = profile["responses"][seat]
    groups = response["top_groups"]
    if not 1 <= rank <= max(1, len(groups)):
        raise ValueError("choose an available positive group rank")
    print(f"\n{profile['seed']} / {profile['role']} / responding seat {seat}")
    print("Cached hash-checked report; full poker replay is a separate command.")
    print("Own best reply against the fixed saved other seat; no new training.")
    print(
        f"Total exploitability: {profile['exact_exploitability_chips']:.6g} chips; "
        f"this seat's unilateral gain: {response['exact_gain_chips']:.6g} chips"
    )
    if not groups:
        print("No positive-loss groups above the report's numerical tolerance.")
        return
    group = groups[rank - 1]
    print(
        f"Group {rank}/{len(groups)} (row {group['abstract_info']}): "
        f"{group['loss_contribution_chips']:.6g} chips of TOTAL unilateral gain."
    )
    print("This row loss is not an extra-information-only or retraining benefit.")
    for row in group["examples"]:
        print(
            f"\nResponding cards {' '.join(row['hole'])}; "
            f"board {' '.join(row['board'])}; {row['street']}; "
            f"{row['hand_category']}"
        )
        print(f"Counterstrategy chooses {row['reply_action']}.")
        for action, probability, value in zip(
            row["actions"],
            row["saved_probabilities"],
            row["reply_continuation_values_chips"],
            strict=True,
        ):
            print(
                f"  {action}: saved probability {probability:.6f}; "
                f"best-reply-suffix value {value:.6f} chips"
            )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=Path(FOLDER))
    parser.add_argument(
        "--seed", type=int, choices=(20261301, 20261302, 20261303), default=20261302
    )
    parser.add_argument(
        "--role", choices=("B1", "IID", "stratified"), default="stratified"
    )
    parser.add_argument("--seat", type=int, choices=(0, 1), default=0)
    parser.add_argument("--rank", type=int, default=1)
    parser.add_argument("--interactive", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    profiles = load(root, root / args.report)
    profile = next(
        p for p in profiles if p["seed"] == args.seed and p["role"] == args.role
    )
    rank = args.rank
    while True:
        show(profile, args.seat, rank)
        if not args.interactive:
            break
        try:
            command = (
                input("\nn next / p previous / s seed / o method / t seat / q quit: ")
                .strip()
                .lower()
            )
        except (EOFError, KeyboardInterrupt):
            print("\nLeaving saved report.")
            break
        if command == "q":
            break
        if command in ("s", "o"):
            choices = (
                (20261301, 20261302, 20261303)
                if command == "s"
                else (
                    "B1",
                    "IID",
                    "stratified",
                )
            )
            field = "seed" if command == "s" else "role"
            value = choices[(choices.index(profile[field]) + 1) % 3]
            profile = next(
                p
                for p in profiles
                if p[field] == value
                and (
                    p["role"] == profile["role"]
                    if field == "seed"
                    else p["seed"] == profile["seed"]
                )
            )
            rank = 1
        elif command == "t":
            args.seat = 1 - args.seat
            rank = 1
        elif command in ("n", "p"):
            count = max(1, len(profile["responses"][args.seat]["top_groups"]))
            rank = 1 + (rank - 1 + (1 if command == "n" else -1)) % count
        else:
            print("Choose n, p, s, o, t or q.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
