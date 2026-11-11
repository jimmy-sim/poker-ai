"""Fast hash-checked cached browser; full mathematical replay is separate."""

import argparse
import itertools
import json
from pathlib import Path
from typing import Any

from poker_ai.evaluation.opponent_decision_inputs import CONFIG_SHA, FOLDER, contract
from poker_ai.evaluation.opponent_decision_math import validate_cross
from poker_ai.evaluation.opponent_learning_sources import input_pins
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.pipeline_report import check_source
from poker_ai.postflop.river_study import digest


def load(root: Path, folder: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    config = contract(root)
    if (folder / "failure.json").exists() or any(folder.rglob("*.tmp")):
        raise ArithmeticError("refuse failed or interrupted diagnostic cache")
    manifest = json.loads((folder / "manifest.json").read_text())
    if (
        manifest["status"] != "complete_own_opponent_decisions"
        or manifest["config_sha256"] != CONFIG_SHA
        or manifest["profiles"] != 24
        or manifest["responses"] != 48
        or manifest["cross_conditions"] != 192
        or manifest["constructors_blocked"] is not True
        or manifest["source_sha256"] != sha(manifest["source"]["sha256"])
        or any(
            manifest[k] is not False
            for k in (
                "training_performed",
                "reference_constructed",
                "independent_new_cross_audit",
                "new_agent_default",
                "fresh_global_admission",
            )
        )
    ):
        raise ArithmeticError("complete read-only24/48/192 diagnostic receipt required")
    check_source(root, manifest["source"])
    input_pins(root)
    expected_outputs = {
        f"details/{coordinate:02d}-{arm}.json.gz"
        for coordinate in range(6)
        for arm in config["arms"]
    } | {
        "summary.json",
        "cross.json",
        "cross.csv",
        "partial.json",
        "partial-cross.json",
    }
    if set(manifest["outputs"]) != expected_outputs:
        raise ArithmeticError("complete cached diagnostic file inventory required")
    for name in ("own", "native"):
        if (
            digest(root / config[name]) != config[name + "_sha256"]
            or manifest[name + "_sha256"] != config[name + "_sha256"]
        ):
            raise ArithmeticError("cached diagnostic source input changed")
    for name, expected in manifest["outputs"].items():
        path = folder / name
        if (
            not path.resolve().is_relative_to(folder.resolve())
            or digest(path) != expected
        ):
            raise ArithmeticError("cached diagnostic output bytes changed")
    summaries: list[dict[str, Any]] = json.loads((folder / "summary.json").read_text())[
        "profiles"
    ]
    crosses: list[dict[str, Any]] = json.loads((folder / "cross.json").read_text())[
        "conditions"
    ]
    expected_panel = set(
        itertools.product(config["games"], config["seeds"], config["arms"])
    )
    if (
        len(summaries) != 24
        or {(p["game"], p["seed"], p["arm"]) for p in summaries} != expected_panel
        or any([r["target"] for r in p["responses"]] != [0, 1] for p in summaries)
        or len(crosses) != 192
    ):
        raise ArithmeticError("complete cached panel required")
    for game, seed in itertools.product(config["games"], config["seeds"]):
        rows = [r for r in crosses if r["game"] == game and r["seed"] == seed]
        validate_cross(rows, tuple(config["arms"]), config["absolute_tolerance_chips"])
    return summaries, crosses


def show(
    profile: dict[str, Any], crosses: list[dict[str, Any]], seat: int, rank: int
) -> None:
    response = profile["responses"][seat]
    groups = response["top_groups"]
    if not 1 <= rank <= max(1, len(groups)):
        raise ValueError("choose an available positive group rank")
    print(
        f"\n{profile['game']} / {profile['seed']} / {profile['arm']} / "
        f"responding seat {seat}"
    )
    print("Cached hash-checked own report; full mathematical replay is separate.")
    print("Fixed saved other seat, legal own best reply; simulation diagnostic only.")
    print(
        f"Self exploitability: {profile['exact_exploitability_chips']:.6g} chips; "
        f"this seat's unilateral gain: {response['exact_gain_chips']:.6g} chips"
    )
    print("\nSame candidate versus each SAME saved opponent (target net chips):")
    for row in crosses:
        if (
            row["game"] == profile["game"]
            and row["seed"] == profile["seed"]
            and row["candidate"] == profile["arm"]
            and row["target"] == seat
        ):
            print(
                f"  {row['opponent']}: EV {row['target_ev_chips']:.6f}; "
                f"own reply gap {row['unilateral_gain_chips']:.6f}"
            )
    print("Off-diagonal values are own calculations, not new native-audited results.")
    if not groups:
        print("No displayed positive-loss groups above the report tolerance.")
        return
    group = groups[rank - 1]
    print(
        f"\nGroup {rank}/{len(groups)}, row {group['abstract_info']}: "
        f"{group['loss_contribution_chips']:.6g} chips of TOTAL unilateral gain."
    )
    print(
        "Row loss is not extra-information-only, "
        "retraining EV or universal poker advice."
    )
    if not group["examples"]:
        print(
            "No positive saved-reach example in this group; "
            "full row details remain saved."
        )
    for row in group["examples"]:
        print(
            f"\nOwn {' '.join(row['hole'])}; board {' '.join(row['board'])}; "
            f"{row['street']}; {row['hand_category']}"
        )
        print(
            f"Own best reply: {row['reply_action']}; "
            f"saved reach {row['saved_reach_mass']:.6g}"
        )
        for action, probability, value in zip(
            row["actions"],
            row["saved_probabilities"],
            row["reply_continuation_values_chips"],
            strict=True,
        ):
            print(
                f"  {action}: saved probability {probability:.6f}; "
                f"own-reply-suffix net chips {value:.6f}"
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
    parser.add_argument("--seat", type=int, choices=(0, 1), default=0)
    parser.add_argument("--rank", type=int, default=1)
    parser.add_argument("--interactive", action="store_true")
    args = parser.parse_args()
    print("Checking cached report and source hashes...", flush=True)
    profiles, crosses = load(root, root / args.report)
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
        show(profile, crosses, args.seat, rank)
        if not args.interactive:
            return 0
        try:
            key = (
                input("\nn/p group / s seed / o method / g game / t seat / q quit: ")
                .strip()
                .lower()
            )
        except (EOFError, KeyboardInterrupt):
            print("\nLeaving saved report.")
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
            count = max(1, len(profile["responses"][args.seat]["top_groups"]))
            rank = 1 + (rank - 1 + (1 if key == "n" else -1)) % count
        else:
            print("Choose n, p, s, o, g, t or q.")
