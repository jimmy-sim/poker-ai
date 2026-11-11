"""Browse saved turn decisions under different fixed-opponent continuations."""

from pathlib import Path

from poker_ai.evaluation.turn_continuation_view import main

if __name__ == "__main__":
    raise SystemExit(main(Path(__file__).resolve().parents[1]))
