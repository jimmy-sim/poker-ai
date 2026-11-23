"""Run guarded stages of the prospectively fixed full-pass river study."""

import argparse
from pathlib import Path

from medium_dry_full.native import audit
from medium_dry_full.report import report
from medium_dry_full.study import main

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
