"""Browse the retained restricted-reply-prefix decision trace."""

from pathlib import Path

from poker_ai.evaluation.compact_information_view import main

if __name__ == "__main__":
    main(Path(__file__).resolve().parents[1])
