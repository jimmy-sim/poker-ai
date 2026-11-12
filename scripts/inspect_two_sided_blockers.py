"""Browse the complete cached two-sided public-blocker diagnosis."""

from pathlib import Path

from poker_ai.evaluation.range_blocker_view import main

if __name__ == "__main__":
    raise SystemExit(main(Path(__file__).resolve().parents[1]))
