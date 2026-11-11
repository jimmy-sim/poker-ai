"""Source-bound own-opponent pipeline with complete command measurements."""

import sys
import time
from pathlib import Path

STARTED = time.perf_counter()
ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    if "--_child" in sys.argv:
        from poker_ai.evaluation.opponent_learning_cli import child_main

        return child_main(ROOT, sys.argv[1:])

    from poker_ai.evaluation.opponent_learning_clock import execute

    return execute(ROOT, sys.argv[1:], STARTED)


if __name__ == "__main__":
    raise SystemExit(main())
