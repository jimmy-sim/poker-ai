"""Browse the cached fixed-profile and common-opponent diagnosis."""

from pathlib import Path

from poker_ai.evaluation.opponent_decision_view import main

if __name__ == "__main__":
    raise SystemExit(main(Path(__file__).resolve().parents[1]))
