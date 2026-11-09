"""Record toy correctness/historical cost, or observed source-bound CI admission."""

import argparse
import json
from pathlib import Path

from poker_ai.evaluation.averaging_history_correctness import run
from poker_ai.evaluation.averaging_history_protocol import record_admission
from poker_ai.postflop.learning_run import persist


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--admit", action="store_true")
    parser.add_argument("--ci-evidence", type=Path)
    parser.add_argument("--local-evidence", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = root / (
        args.output
        or Path(
            "results/runs/averaging-history/"
            + ("admission.json" if args.admit else "correctness.json")
        )
    )
    if args.admit:
        if args.ci_evidence is None or args.local_evidence is None:
            parser.error(
                "admission requires actual observed --ci-evidence and --local-evidence"
            )
        if output.exists() or output.with_suffix(".tmp").exists():
            raise FileExistsError("retain recorded averaging admission")
        saved = record_admission(
            root,
            json.loads(args.ci_evidence.read_text()),
            json.loads(args.local_evidence.read_text()),
        )
        persist(output, saved)
        print(saved["status"])
        return 0
    saved = run(root, output)
    print(saved["status"])
    print(json.dumps(saved["forecast"], sort_keys=True))
    return (
        0 if saved["forecast"]["decision"] == "fits_requires_checked_admission" else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
