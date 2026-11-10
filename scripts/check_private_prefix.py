"""Check/replay the stratification kernel; never admits a real Hold'em study."""

import argparse
import json
from pathlib import Path

from poker_ai.evaluation.private_prefix_correctness import replay, run


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--output",
        type=Path,
        default=Path("results/runs/private-prefix/correctness.json"),
    )
    group.add_argument("--replay", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    saved = (
        replay(root, root / args.replay)
        if args.replay
        else run(root, root / args.output)
    )
    print(
        json.dumps(
            dict(
                status=saved["status"],
                raw_moment_cases=len(saved["math"]),
                trajectory_endpoints=len(saved["trajectories"]),
                B1_bit_checks=sum(
                    r["B1_original_bit_match"] for r in saved["trajectories"]
                ),
                maximum_array_error=max(
                    r["maximum_array_error"] for r in saved["trajectories"]
                ),
                real_poker_training=False,
                full_shape_proof_complete=False,
                long_run_admitted=False,
            ),
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
