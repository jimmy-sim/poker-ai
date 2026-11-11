"""Reproduce the frozen own-opponent saved-decision diagnosis."""

import time
from pathlib import Path

STARTED = time.perf_counter()

if __name__ == "__main__":
    from poker_ai.evaluation.opponent_decision_run import main

    raise SystemExit(main(Path(__file__).resolve().parents[1], STARTED))
