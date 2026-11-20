"""Opt-in exact river refinement of the unchanged q8 range representation.

Build the historical q8 tree with its original source, then split only acting
river information rows using existing exact legal observations. The base game,
chance, menu, owner and pre-river q8 key bytes remain unchanged.
"""

from dataclasses import replace

import numpy as np

from poker_ai.abstraction.model import CardAbstraction
from poker_ai.abstraction.range_mass import RangeMassAbstraction
from poker_ai.engine import Observation
from poker_ai.postflop.matrix import MatrixTree, observation_key, recall_violations
from poker_ai.postflop.range_protocol import (
    CANDIDATE,
    build_representation_control,
    range_context,
)
from poker_ai.postflop.tree import SpotTree
from poker_ai.training.holdem import exact_information

RIVER_CANDIDATE = "q8_turn_exact_river"


def river_information(observation: Observation, model: RangeMassAbstraction) -> str:
    """Use the original q8 key through turn; exact acting observation on river."""
    if observation.terminal or observation.actor != observation.seat:
        raise ValueError("river key requires the acting player's observation")
    if len(observation.board) == 5:
        return exact_information(observation)
    return observation_key(observation, "texture_b8", model)


def build_river_candidate(source: SpotTree, model: CardAbstraction) -> MatrixTree:
    """Split only q8 river groups, leaving pinned historical modules untouched."""
    base = build_representation_control(source, CANDIDATE, model)
    encoder = RangeMassAbstraction(model, range_context(source.spot))
    keys: list[str] = []
    actions: list[tuple[int, ...]] = []
    owners: list[int] = []
    lookup: dict[str, int] = {}
    mapping = np.empty(len(source.keys), dtype=np.int64)
    for exact, node in enumerate(source.representatives):
        state = source.states[node]
        if state.dealer is None:
            raise ArithmeticError("decision representative lacks a dealer")
        observed = state.dealer.observe(state.actor)
        key = river_information(observed, encoder)
        if (
            len(observed.board) != 5
            and key != base.keys[int(base.exact_to_abstract[exact])]
        ):
            raise ArithmeticError("pre-river q8 key changed")
        if key not in lookup:
            lookup[key] = len(keys)
            keys.append(key)
            actions.append(source.menus[exact])
            owners.append(state.actor)
        info = lookup[key]
        if actions[info] != source.menus[exact] or owners[info] != state.actor:
            raise ValueError("river refinement merges incompatible owners/actions")
        mapping[exact] = info
    if len(keys) < len(base.keys) or len(keys) > len(source.keys):
        raise ArithmeticError("river refinement row count invalid")
    information = base.information.copy()
    decisions = np.flatnonzero(base.player >= 0)
    information[decisions] = mapping[
        np.asarray(source.information, dtype=np.int64)[decisions]
    ]
    legal = np.zeros((len(keys), base.legal.shape[1]), dtype=base.legal.dtype)
    for info, menu in enumerate(actions):
        legal[info, : len(menu)] = 1
    result = replace(
        base,
        keys=tuple(keys),
        actions=tuple(actions),
        owners=np.asarray(owners, dtype=np.int64),
        legal=legal,
        information=information,
        exact_to_abstract=mapping,
    )
    if recall_violations(result):
        raise ArithmeticError("river candidate violates abstract recall")
    return result
