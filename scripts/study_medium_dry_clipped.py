"""Run guarded stages of the prospectively fixed clipped-regret study."""

import argparse
from pathlib import Path

from medium_dry_clipped.native import audit
from medium_dry_clipped.report import report
from medium_dry_clipped.study import main

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "stage", choices=("proof", "profile", "admit", "study", "native", "report")
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.stage == "native":
        audit(Path(__file__).resolve().parents[1], args.output.resolve())
    elif args.stage == "report":
        report(Path(__file__).resolve().parents[1], args.output.resolve())
    else:
        main(args.stage, args.output)
