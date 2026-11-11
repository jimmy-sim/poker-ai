"""The same own finite game with coarse, fine and two mixed legal views."""

from dataclasses import dataclass

import numpy as np

from poker_ai.evaluation.opponent_view_correctness import signal_game
from poker_ai.finite import ArrayTree, FloatArray, IntArray
from poker_ai.postflop.controlled_scoring import BoolArray, ScoringContext
from poker_ai.postflop.opponent_views import (
    OpponentView,
    bind_policy,
    build_view,
    compose,
)


@dataclass(frozen=True)
class Contexts:
    fine: ArrayTree
    coarse: ArrayTree
    mapping: IntArray
    views: tuple[OpponentView, OpponentView]
    scoring: dict[str, ScoringContext]

    @classmethod
    def build(
        cls,
        fine: ArrayTree,
        coarse: ArrayTree,
        mapping: IntArray,
        river: tuple[BoolArray, BoolArray],
    ) -> "Contexts":
        views = (
            build_view(fine, coarse, mapping, 0),
            build_view(fine, coarse, mapping, 1),
        )
        contexts = {
            "coarse": ScoringContext(fine, coarse, mapping, river),
            "fine": ScoringContext(fine, fine, np.arange(len(fine.keys)), river),
            **{
                f"mixed{i}": ScoringContext(fine, view.tree, view.fine_to_view, river)
                for i, view in enumerate(views)
            },
        }
        return cls(fine, coarse, mapping, views, contexts)

    def tree(self, kind: str) -> ArrayTree:
        if kind not in self.scoring:
            raise ValueError("unknown own training information view")
        return self.scoring[kind].partition

    def combine(self, arm: str, first: FloatArray, second: FloatArray) -> FloatArray:
        if arm == "mixed_pair":
            return compose(
                self.coarse,
                (self.views[0], bind_policy(self.views[0], first)),
                (self.views[1], bind_policy(self.views[1], second)),
            )
        if arm != "coarse_pair":
            raise ValueError("only paired arms combine two own strategies")
        self.coarse.validate_policy(first)
        self.coarse.validate_policy(second)
        result = np.zeros_like(self.coarse.legal)
        for target, policy in enumerate((first, second)):
            owned = self.coarse.owners == target
            result[owned] = policy[owned]
        self.coarse.validate_policy(result)
        return result


def software_context(game: int) -> Contexts:
    """Two explicit fictional sign mirrors; logical seed labels are not poker."""
    fine, coarse, mapping = signal_game(game)
    # These fictional decisions are marked river only to exercise the complete
    # reply/archive schema. They are not cards or actual poker betting streets.
    river = (fine.owners == 0, fine.owners == 1)
    return Contexts.build(fine, coarse, mapping, river)
