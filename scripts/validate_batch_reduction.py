"""Checked reduction code, exact original prefixes, fixed forecast or offline replay."""

import argparse
import json
from pathlib import Path

from poker_ai.evaluation import batch_reduction_inputs as inputs
from poker_ai.evaluation.batch_reduction_report import write_report
from poker_ai.evaluation.batch_reduction_run import fresh, replay, run
from poker_ai.postflop.learning_run import persist


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--check-code", action="store_true")
    modes.add_argument("--correctness", action="store_true")
    modes.add_argument("--profile", action="store_true")
    modes.add_argument("--replay", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--report-output", type=Path)
    parser.add_argument("--ci-evidence", type=Path)
    parser.add_argument("--local-evidence", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if args.replay:
        saved = replay(root, root / args.replay)
    elif args.check_code:
        if args.ci_evidence is None or args.local_evidence is None:
            parser.error("observed --ci-evidence and --local-evidence required")
        output = root / (args.output or Path(inputs.CHECKS))
        fresh(output)
        saved = inputs.record_checks(
            root,
            json.loads(args.ci_evidence.read_text()),
            json.loads(args.local_evidence.read_text()),
        )
        persist(output, saved)
    else:
        kind = "correctness" if args.correctness else "profile"
        output = root / (
            args.output
            or Path(inputs.CORRECTNESS if args.correctness else inputs.PROFILE)
        )
        saved = run(root, output, kind)
    if args.report_output is not None:
        if args.check_code:
            parser.error("code gate has no prefix report")
        print(write_report(saved, root / args.report_output))
    print(saved["status"])
    if "forecast" in saved and saved["forecast"] is not None:
        print(json.dumps(saved["forecast"], indent=2))
    print("Execution only; no long-learning/default/fresh/global admission.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
