"""Record observed saved-current code checks or conditional source admission."""

import argparse
import json
from pathlib import Path

from poker_ai.evaluation import batch_current_inputs as inputs
from poker_ai.evaluation import batch_current_protocol as protocol
from poker_ai.evaluation.batch_current_run import fresh
from poker_ai.postflop.learning_run import persist


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--code-checks", action="store_true")
    modes.add_argument("--admit", action="store_true")
    parser.add_argument("--ci-evidence", type=Path)
    parser.add_argument("--local-evidence", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = root / (
        args.output or Path(inputs.CHECKS if args.code_checks else inputs.ADMITTED)
    )
    fresh(output)
    if args.code_checks:
        if args.ci_evidence is None or args.local_evidence is None:
            parser.error("actual observed code/local evidence required")
        saved = protocol.record_checks(
            root,
            json.loads(args.ci_evidence.read_text()),
            json.loads(args.local_evidence.read_text()),
        )
    else:
        saved = protocol.record_admission(root)
    persist(output, saved)
    print(saved["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
