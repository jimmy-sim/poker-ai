"""Browse cached local river range weights and frozen continuation values."""

from pathlib import Path

from poker_ai.evaluation.river_range_view import main

if __name__ == "__main__":
    raise SystemExit(main(Path(__file__).resolve().parents[1]))
