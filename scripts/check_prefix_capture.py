"""Run/replay explicit tiny-game own capture proof; never train or score Hold'em."""

import argparse
import json
from pathlib import Path

from poker_ai.evaluation.prefix_capture_software import read, run


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/runs/matched-prefix-proof/own.json"),
    )
    parser.add_argument("--replay", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if args.replay is not None:
        proof = read(root, root / args.replay)
    else:
        saved = run(root, root / args.output)
        proof = saved["replay"]
        print(f"{saved['status']}: {saved['seconds']:.9f}s")
    print(json.dumps(proof, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
