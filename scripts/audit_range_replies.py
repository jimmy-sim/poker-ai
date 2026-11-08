"""Independently check own response roots; reference outputs are comparison-only."""

import argparse
from pathlib import Path

from poker_ai.solver_validation.range_reply import audit


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=Path("configs/range-mass-reply-diagnosis.json")
    )
    parser.add_argument(
        "--report", type=Path, default=Path("results/range-mass-replies/diagnosis.json")
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/range-mass-replies/independent.json"),
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    result = audit(root, root / args.config, root / args.report, root / args.output)
    print(f"native reply audit: {result['status']}")
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
