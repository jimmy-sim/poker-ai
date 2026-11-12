"""Run the prospectively fixed cached two-sided blocker diagnosis."""

import time
from pathlib import Path

STARTED = time.perf_counter()

if __name__ == "__main__":
    from poker_ai.evaluation.range_blocker_run import main

    raise SystemExit(main(Path(__file__).resolve().parents[1], STARTED))
