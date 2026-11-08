"""Inspect fixed opponent street swaps; no training or poker advice."""

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--report", type=Path, default=Path("results/policy-swaps/study.json")
    )
    parser.add_argument("--game", default="dev_medium_oop")
    parser.add_argument("--representation", default="texture_range_q8_b8")
    parser.add_argument("--seed", type=int, default=20261301)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    report = json.loads((root / args.report).read_text())
    selected = [
        r
        for r in report["hybrids"]
        if Path(r["spot_file"]).stem == args.game
        and r["representation"] == args.representation
        and r["seed"] == args.seed
    ]
    if len(selected) != 4:
        parser.error("choose a saved game, representation and seed")
    print(f"{args.game}/{args.representation}; sampled seed {args.seed}")
    print(
        "Fixed opponent policies; exact replies still respect "
        "hidden cards. No retraining."
    )
    for row in selected:
        gap = sum(r["extra_information_chips"] for r in row["responses"]) / 2
        print(
            f"{row['combination']}: extra gap {gap:.6g} chips = "
            f"{100 * gap / row['pot']:.6g}% "
            f"initial pot"
        )
    rows = [
        r
        for r in report["effects"]
        if Path(r["spot_file"]).stem == args.game
        and r["representation"] == args.representation
        and r["seed"] == args.seed
    ]
    for name in ("turn_effect_chips", "river_effect_chips", "interaction_chips"):
        print(f"{name}: {sum(r[name] for r in rows) / 2:.6g} half-summed chips")
    print(
        "F = saved full, S = sampled; first letter turn, second "
        "river. Signed effects are policy substitutions, not "
        "learning causes."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
