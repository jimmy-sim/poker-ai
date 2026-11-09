"""Record/replay toy correctness or observed checked-source/compute admission."""

import argparse
import json
from pathlib import Path

from poker_ai.evaluation import reduced_study_protocol as protocol
from poker_ai.evaluation.reduced_study_inputs import config_inputs
from poker_ai.postflop.learning_run import persist


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--replay", type=Path)
    parser.add_argument("--code-checks", action="store_true")
    parser.add_argument("--admit", action="store_true")
    parser.add_argument("--ci-evidence", type=Path)
    parser.add_argument("--local-evidence", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if sum((args.replay is not None, args.code_checks, args.admit)) > 1:
        parser.error("select only one receipt operation")
    if args.replay:
        saved = json.loads((root / args.replay).read_text())
        protocol.validate_correctness(root, saved, config_inputs(root))
        print("passed: complete explicit-backend tiny-game IO; no postflop training")
        return 0
    if args.code_checks:
        if args.ci_evidence is None or args.local_evidence is None:
            parser.error(
                "code checks need actual observed --ci-evidence and --local-evidence"
            )
        output = root / (args.output or Path(protocol.CHECKS))
        protocol.fresh_output(output)
        saved = protocol.record_code_checks(
            root,
            json.loads(args.ci_evidence.read_text()),
            json.loads(args.local_evidence.read_text()),
        )
        persist(output, saved)
    elif args.admit:
        output = root / (args.output or Path(protocol.ADMITTED))
        protocol.fresh_output(output)
        saved = protocol.record_admission(root)
        persist(output, saved)
    else:
        output = root / (
            args.output or Path("results/runs/reduced-batch-study/correctness.json")
        )
        saved = protocol.run_correctness(root, output)
    print(saved["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
