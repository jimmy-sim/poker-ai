"""No-training information-loss trace, timed before numerical imports."""

import time

STARTED = time.perf_counter()
import sys  # noqa:E402
from pathlib import Path  # noqa:E402

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    if "--_child" in sys.argv:
        from poker_ai.evaluation.compact_information_run import child

        return child(ROOT, sys.argv[1:])
    from poker_ai.evaluation.diagnostic_clock import execute

    return execute(ROOT, sys.argv[1:], STARTED, "scripts/trace_compact_information.py")


if __name__ == "__main__":
    raise SystemExit(main())
