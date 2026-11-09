"""Offline source/state/call audit and report; no training or native solver."""

import argparse
from pathlib import Path

from poker_ai.evaluation.batch_cost_report import write_report
from poker_ai.evaluation.batch_cost_run import replay


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--report", type=Path, default=Path("results/batch-overhead/profile.json")
    )
    parser.add_argument(
        "--output", type=Path, default=Path("results/runs/batch-overhead-report")
    )
    parser.add_argument("--no-plots", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    saved = replay(root, root / args.report)
    result = write_report(saved, root / args.output, plots=not args.no_plots)
    print(
        f"passed: {result['paths']} paths, {result['endpoints']} exact endpoints, "
        f"{result['instrumented_profiles']} complete function profiles"
    )
    print("Cost only; no new strength, optimizer, forecast or long-learning admission.")
    print(f"report: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
