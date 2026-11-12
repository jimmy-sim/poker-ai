"""Structural training factory, isolated from saved strategies and native code."""

from pathlib import Path

import numpy as np

from poker_ai.abstraction.model import CardAbstraction
from poker_ai.evaluation.compact_opponent_contract import contract
from poker_ai.evaluation.opponent_learning_contexts import Contexts
from poker_ai.evaluation.opponent_learning_design import GAMES
from poker_ai.finite import IntArray
from poker_ai.postflop.game import load_spot
from poker_ai.postflop.matrix import MatrixTree
from poker_ai.postflop.opponent_views import tree_digest
from poker_ai.postflop.public_range_definition import CANDIDATE, build_control
from poker_ai.postflop.river_distinctions import river_mask
from poker_ai.postflop.river_study import digest
from poker_ai.postflop.tree import SpotTree


def build_game(root: Path, game: int) -> Contexts:
    if type(game) is not int or game not in (0, 1):
        raise ValueError("choose one of the two registered compact games")
    config = contract(root)
    if config["coarse_representation"] != CANDIDATE:
        raise ArithmeticError("learner information groups changed")
    for filename in (GAMES[game], config["model"]):
        if digest(root / filename) != config["input_sha256"][filename]:
            raise ArithmeticError("training structural input changed")
    source = SpotTree.build(load_spot(root / GAMES[game]))
    fine = MatrixTree.build(source)
    coarse = build_control(
        source, CANDIDATE, CardAbstraction.load(root / config["model"])
    )
    return Contexts.build(
        fine,
        coarse,
        coarse.exact_to_abstract,
        (river_mask(fine, 0), river_mask(fine, 1)),
    )


def refinement(old: Contexts, new: Contexts) -> IntArray:
    """Map each NEW compact row to one original coarse row, or reject it.

    A larger row count is insufficient: every fine history in a new group must
    agree on the original group, owner and action menu. No private-card history
    or changed payoff/chance tree can enter through a cost projection.
    """
    if tree_digest(old.fine) != tree_digest(new.fine):
        raise ArithmeticError("cost refinement changes the underlying fine game")
    result = np.full(len(new.coarse.keys), -1, dtype=np.int64)
    for fine, group in enumerate(new.mapping):
        parent = int(old.mapping[fine])
        if result[group] not in (-1, parent):
            raise ArithmeticError("new compact row crosses original coarse groups")
        result[group] = parent
    if (
        np.any(result < 0)
        or set(result.tolist()) != set(range(len(old.coarse.keys)))
        or any(
            new.coarse.owners[i] != old.coarse.owners[parent]
            or new.coarse.actions[i] != old.coarse.actions[parent]
            for i, parent in enumerate(result)
        )
    ):
        raise ArithmeticError("cost refinement loses rows or changes owners/menus")
    result.flags.writeable = False
    return result
