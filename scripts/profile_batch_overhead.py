"""Record observed source checks or run the fixed complete batch cost profile."""

import argparse
import json
from pathlib import Path

from poker_ai.evaluation.batch_cost_inputs import CHECKED, record_checks
from poker_ai.evaluation.batch_cost_run import fresh, run
from poker_ai.postflop.learning_run import persist


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check-code", action="store_true")
    parser.add_argument("--ci-evidence", type=Path)
    parser.add_argument("--local-evidence", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if args.check_code:
        if args.ci_evidence is None or args.local_evidence is None:
            parser.error("actual observed --ci-evidence and --local-evidence required")
        output = root / (args.output or Path(CHECKED))
        fresh(output)
        saved = record_checks(
            root,
            json.loads(args.ci_evidence.read_text()),
            json.loads(args.local_evidence.read_text()),
        )
        persist(output, saved)
    else:
        saved = run(
            root,
            root / (args.output or Path("results/runs/batch-overhead/profile.json")),
        )
    print(saved["status"])
    if "seconds" in saved:
        print(f"elapsed: {saved['seconds']:.9f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
