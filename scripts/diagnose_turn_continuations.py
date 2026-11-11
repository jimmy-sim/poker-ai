"""Reproduce the frozen fixed-turn continuation diagnostic without learning."""

import time
from pathlib import Path

STARTED = time.perf_counter()

if __name__ == "__main__":
    from poker_ai.evaluation.turn_continuation_run import main

    raise SystemExit(main(Path(__file__).resolve().parents[1], STARTED))
