"""Frozen-policy diagnostic; complete clock starts before numerical imports."""

import time

STARTED = time.perf_counter()
import sys  # noqa:E402
from pathlib import Path  # noqa:E402

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    if "--_child" in sys.argv:
        from poker_ai.evaluation.compact_fixed_cli import child

        return child(ROOT, sys.argv[1:])
    from poker_ai.evaluation.compact_fixed_clock import execute

    return execute(ROOT, sys.argv[1:], STARTED)


if __name__ == "__main__":
    raise SystemExit(main())
