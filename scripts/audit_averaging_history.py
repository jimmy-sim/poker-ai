"""Audit all OWN history profiles and fixed targets with native scalar checks."""

import argparse
from pathlib import Path

from poker_ai.solver_validation.averaging_history import run


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--own", type=Path, default=Path("results/averaging-history/own.json")
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/runs/averaging-history/native.json"),
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    print(run(root, root / args.own, root / args.output)["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
