"""Replay every own checkpoint and regenerate separate-axis tables/figures."""

import argparse
import json
from pathlib import Path

from poker_ai.postflop.learning_protocol import pots, read_own
from poker_ai.postflop.learning_replay import replay
from poker_ai.postflop.learning_report import write_report
from poker_ai.postflop.pipeline_report import check_source


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--own", type=Path, default=Path("results/controlled-learning/own.json")
    )
    parser.add_argument(
        "--native", type=Path, default=Path("results/controlled-learning/native.json")
    )
    parser.add_argument(
        "--output", type=Path, default=Path("results/runs/controlled-learning-report")
    )
    parser.add_argument("--no-plots", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    saved, comparison = read_own(root, root / args.own)
    print(json.dumps(replay(root, root / args.own), sort_keys=True))
    if (root / args.native).exists():
        from poker_ai.solver_validation.controlled_learning import validate

        native = json.loads((root / args.native).read_text())
        check_source(root, native["source"])
        print(json.dumps(validate(native, saved, root / args.own), sort_keys=True))
    else:
        print(
            "Native audit absent; own-only report, "
            "no completed external validation claim."
        )
    summary = write_report(
        saved,
        comparison,
        pots(root, comparison),
        root / args.output,
        plots=not args.no_plots,
    )
    print(
        f"{summary['logical_checkpoints']} logical checkpoints; report: {args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
