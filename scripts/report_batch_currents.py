"""Offline saved-current/source/fixed-target audit and complete numerical reports."""

import argparse
import json
from pathlib import Path

from poker_ai.evaluation.batch_current_report import write_report
from poker_ai.evaluation.batch_current_run import replay
from poker_ai.solver_validation.batch_currents import read


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--own", type=Path, default=Path("results/batch-current-diagnosis/own.json")
    )
    parser.add_argument(
        "--native",
        type=Path,
        default=Path("results/batch-current-diagnosis/native.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/runs/batch-current-diagnosis-report"),
    )
    parser.add_argument("--no-plots", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    saved, sources, proof = replay(root, root / args.own)
    print(json.dumps(proof, sort_keys=True))
    if (root / args.native).exists():
        print(
            json.dumps(
                read(root, root / args.native, saved, root / args.own), sort_keys=True
            )
        )
    else:
        print("Own-only diagnosis: independent current/fixed-target audit pending.")
    result = write_report(
        root, saved, sources, root / args.output, plots=not args.no_plots
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
