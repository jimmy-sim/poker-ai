"""Validate prospective saved-metadata grid; never run Hold'em learning/scoring."""

import argparse
import json
from pathlib import Path

from poker_ai.evaluation.matched_update_grid import manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = manifest(Path(__file__).resolve().parents[1])
    if args.output is not None:
        if args.output.exists():
            parser.error("retain the existing manifest; choose a new output path")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(
        f"{result['status']}: {result['contexts']} contexts, "
        f"{len(result['iteration_targets'])} targets, "
        f"{len(result['self_pairs'])} pairs; "
        "no new training/strength scores or long admission"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
