"""Source-bound own-opponent pipeline with complete command measurements."""

import math
import os
import sys
import time
from pathlib import Path

STARTED = time.perf_counter()
REGISTERED = os.environ.get("POKER_COMPACT_SUIT_COMMAND_STARTED")
if REGISTERED is not None:
    origin = float(REGISTERED)
    if not math.isfinite(origin) or not 0 < origin <= STARTED:
        raise ArithmeticError("finite complete-command origin before Python required")
    STARTED = origin
ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    if (
        len(sys.argv) > 1
        and sys.argv[1]
        in {
            "software-own",
            "software-audit",
            "cost-own",
            "cost-audit",
            "forecast",
            "admit",
            "study",
            "audit",
        }
        and REGISTERED is None
    ):
        raise ArithmeticError(
            "formal stages require the published pre-Python launch operator"
        )
    if "--_child" in sys.argv:
        from compact_suit.cli import child_main

        return child_main(ROOT, sys.argv[1:])

    from compact_suit.clock import execute

    return execute(ROOT, sys.argv[1:], STARTED)


if __name__ == "__main__":
    raise SystemExit(main())
