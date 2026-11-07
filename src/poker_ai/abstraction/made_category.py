"""Experimental own-card made-category history layered over unchanged buckets."""

import json

from poker_ai.abstraction.model import CardAbstraction
from poker_ai.cards import cards_to_mask
from poker_ai.engine import Observation
from poker_ai.evaluator import evaluate_best


def made_category_history(
    hole: tuple[int, ...], board: tuple[int, ...]
) -> tuple[int, ...]:
    """Standard 0..8 hand categories at each visible street; no tiebreakers.

    Each prefix uses only the acting player's own cards and that public prefix.
    Preflop has no made five-card hand and adds an empty sequence. Rank/suit names
    and hidden cards are not feature parameters. Earlier categories stay in keys.
    """
    if len(hole) != 2 or len(board) not in (0, 3, 4, 5):
        raise ValueError("need two own cards and an observed Hold'em board")
    cards_to_mask(hole + board)
    return tuple(
        int(evaluate_best(hole + board[:n]).category)
        for n in (3, 4, 5)
        if n <= len(board)
    )


class MadeCategoryAbstraction(CardAbstraction):
    """Opt-in research encoder, not a new serialized global quantizer format.

    Construct with the pinned base model's quantizers/config. The finite matrix
    adds the unchanged public texture around this richer own information key.
    Admission artifacts bind this encoder version/source separately; inherited
    quantizer serialization alone is not a global strategy/encoder checkpoint.
    """

    def information(self, observation: Observation) -> str:
        if observation.terminal or observation.seat != observation.actor:
            raise ValueError("made-category key requires the acting player's view")
        return json.dumps(
            [
                "made-category-history-v1",
                super().information(observation),
                made_category_history(observation.hole_cards, observation.board),
            ],
            separators=(",", ":"),
        )
