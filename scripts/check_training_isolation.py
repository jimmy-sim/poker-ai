"""Check or replay exact software sentinels; does not train a postflop agent."""

import argparse
from pathlib import Path

from poker_ai.postflop.training_isolation import CONFIG, replay, run


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path(CONFIG))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/runs/training-isolation/correctness.json"),
    )
    parser.add_argument("--replay", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    result = (
        replay(root, root / args.replay)
        if args.replay
        else run(root, root / args.config, root / args.output)
    )
    print(
        f"{result['status']}: {len(result['sentinels'])} exact selector checks, "
        f"{len(result['historical_work'])} historical work rows; "
        "no new postflop training"
    )
    for row in result["historical_work"]:
        if row["representation"] == "texture_range_q8_b8":
            print(
                f"{Path(row['spot_file']).stem}/{row['seed']}: "
                f"full={row['full_node_work']:,}, "
                f"sampled={row['sampled_node_work']:,} node visits; "
                f"ratio={row['full_over_sampled_work']:.6f}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
