"""Complete-command entry point; clock begins before numerical imports."""

import time

STARTED = time.perf_counter()

import sys  # noqa: E402
from pathlib import Path  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    if "--_child" in sys.argv:
        from poker_ai.postflop.compact_full_cli import child_main

        return child_main(ROOT, sys.argv[1:])
    from poker_ai.postflop.compact_full_clock import execute

    return execute(ROOT, sys.argv[1:], STARTED)


if __name__ == "__main__":
    raise SystemExit(main())
