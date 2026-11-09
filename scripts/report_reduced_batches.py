"""Replay all own batch evidence and optional native receipt, then render."""

import argparse
import json
from pathlib import Path

from poker_ai.evaluation.frozen_batch_report import write_report
from poker_ai.evaluation.reduced_study_run import replay


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--own", type=Path, default=Path("results/reduced-batch-study/own.json")
    )
    parser.add_argument(
        "--native", type=Path, default=Path("results/reduced-batch-study/native.json")
    )
    parser.add_argument(
        "--output", type=Path, default=Path("results/runs/reduced-batch-study-report")
    )
    parser.add_argument("--no-plots", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    saved, _, proof = replay(root, root / args.own)
    print(json.dumps(proof, sort_keys=True))
    if (root / args.native).exists():
        from poker_ai.solver_validation.reduced_batches import read

        print(
            json.dumps(
                read(root, root / args.native, saved, root / args.own), sort_keys=True
            )
        )
    else:
        print(
            "Native receipt absent: own-only report, no independent-comparison claim."
        )
    result = write_report(root, saved, root / args.output, plots=not args.no_plots)
    print(f"{result['profiles']} profiles; report: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
