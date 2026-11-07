"""Array backend and observation-only representation controls for own spot learning."""

import json
from dataclasses import dataclass
from typing import Literal

import numpy as np

from poker_ai.abstraction.model import CardAbstraction
from poker_ai.abstraction.public_board import (
    board_texture_history,
    canonical_public_board,
)
from poker_ai.engine import Observation
from poker_ai.finite import ArrayTree, FloatArray, IntArray
from poker_ai.postflop.tree import Policy, SpotTree
from poker_ai.training.holdem import exact_information
from poker_ai.training.mccfr import SampleState

Encoding = Literal["exact", "legacy_b8", "public_b8", "canonical_b8", "texture_b8"]


def observation_key(
    observation: Observation, encoding: Encoding, model: CardAbstraction | None
) -> str:
    if encoding == "exact":
        return exact_information(observation)
    if (
        encoding
        not in (
            "legacy_b8",
            "public_b8",
            "canonical_b8",
            "texture_b8",
        )
        or model is None
    ):
        raise ValueError("unknown/missing representation model")
    if encoding in ("canonical_b8", "texture_b8"):
        if observation.terminal or observation.actor != observation.seat:
            raise ValueError(
                "public-board key requires the acting player's observation"
            )
        public = (
            canonical_public_board(observation.board)
            if encoding == "canonical_b8"
            else board_texture_history(observation.board)
        )
        return json.dumps(
            ["public-board-v1", encoding, model.information(observation), public],
            separators=(",", ":"),
        )
    key = model.information(observation)
    if encoding == "public_b8":
        # Preserve ordered public reveals independently of private-card buckets.
        # Raw observed suits are intentional for this local exact-board control.
        return json.dumps([key, observation.board], separators=(",", ":"))
    return key


@dataclass(frozen=True)
class MatrixTree(ArrayTree):
    source: SpotTree
    exact_to_abstract: IntArray
    encoding: Encoding
    node_actions: tuple[tuple[int, ...], ...]

    @classmethod
    def build(
        cls,
        source: SpotTree,
        encoding: Encoding = "exact",
        model: CardAbstraction | None = None,
    ) -> "MatrixTree":
        keys: list[str] = []
        menus: list[tuple[int, ...]] = []
        owners: list[int] = []
        lookup: dict[str, int] = {}
        mapping = np.zeros(len(source.keys), dtype=np.int64)
        for exact, node in enumerate(source.representatives):
            state = source.states[node]
            assert state.dealer is not None
            key = observation_key(state.dealer.observe(state.actor), encoding, model)
            if key not in lookup:
                lookup[key] = len(keys)
                keys.append(key)
                menus.append(source.menus[exact])
                owners.append(state.actor)
            info = lookup[key]
            if menus[info] != source.menus[exact] or owners[info] != state.actor:
                raise ValueError("representation merges incompatible owners/actions")
            mapping[exact] = info
        n = len(source.states)
        width = max(map(len, source.children))
        children = np.zeros((n, width), dtype=np.int64)
        valid = np.zeros((n, width), dtype=np.bool_)
        chance_edges = np.zeros((n, width))
        chance_reach = np.ones(n)
        depths = np.zeros(n, dtype=np.int64)
        information = np.full(n, -1, dtype=np.int64)
        players = np.full(n, -2, dtype=np.int64)
        for node, state in enumerate(source.states):
            group = source.children[node]
            children[node, : len(group)] = group
            valid[node, : len(group)] = True
            if state.chance:
                players[node] = -1
                chance_edges[node, : len(group)] = source.chance_probabilities[node]
            elif not state.terminal:
                players[node] = state.actor
                information[node] = mapping[source.information[node]]
            for column, child in enumerate(group):
                depths[child] = depths[node] + 1
                chance_reach[child] = chance_reach[node] * (
                    chance_edges[node, column] if state.chance else 1.0
                )
        legal = np.zeros((len(keys), width))
        for info, menu in enumerate(menus):
            legal[info, : len(menu)] = 1
        levels = tuple(
            np.flatnonzero((depths == d) & (players != -2))
            for d in range(int(depths.max()) + 1)
        )
        for info in range(len(keys)):
            if len(set(depths[information == info].tolist())) != 1:
                raise ValueError("information set merges different depths")
        return cls(
            children=children,
            valid=valid,
            player=players,
            information=information,
            keys=tuple(keys),
            actions=tuple(menus),
            owners=np.array(owners, dtype=np.int64),
            legal=legal,
            chance_edges=chance_edges,
            chance_reach=chance_reach,
            terminal_values=np.array(source.payoffs),
            levels=levels,
            source=source,
            exact_to_abstract=mapping,
            encoding=encoding,
            node_actions=tuple(state.actions for state in source.states),
        )

    def exact_policy(self, policy: FloatArray) -> Policy:
        self.validate_policy(policy)
        return tuple(
            tuple(float(v) for v in policy[self.exact_to_abstract[info], : len(menu)])
            for info, menu in enumerate(self.source.menus)
        )

    def dense_exact(self, policy: Policy) -> FloatArray:
        """For an EXACT matrix only, align an exact policy to its padded rows."""
        if self.encoding != "exact":
            raise ValueError("exact policy evaluation requires the exact matrix")
        self.source.validate_policy(policy)
        result = np.zeros_like(self.legal)
        for info, row in enumerate(policy):
            result[info, : len(row)] = row
        return result


@dataclass(frozen=True)
class IndexedState:
    """Sample the already-materialized own mechanics tree; no hidden data in keys."""

    tree: MatrixTree
    node: int = 0
    cached_actions: bool = True

    @property
    def terminal(self) -> bool:
        return bool(self.tree.player[self.node] == -2)

    @property
    def chance(self) -> bool:
        return bool(self.tree.player[self.node] == -1)

    @property
    def actor(self) -> int:
        return max(0, int(self.tree.player[self.node]))

    @property
    def actions(self) -> tuple[int, ...]:
        return (
            self.tree.node_actions[self.node]
            if self.cached_actions
            else self.tree.source.states[self.node].actions
        )

    @property
    def chance_probabilities(self) -> tuple[float, ...]:
        if not self.chance:
            raise ValueError("not a chance node")
        return self.tree.source.chance_probabilities[self.node]

    @property
    def information(self) -> str:
        if self.chance or self.terminal:
            raise ValueError("information requires an acting player")
        return self.tree.keys[int(self.tree.information[self.node])]

    @property
    def payoff(self) -> float:
        if not self.terminal:
            raise ValueError("payoff requires terminal node")
        return float(self.tree.terminal_values[self.node])

    def child(self, action: int) -> SampleState:
        if type(action) is not int or action not in self.actions:
            raise ValueError("illegal indexed action")
        column = self.actions.index(action)
        return IndexedState(
            self.tree, int(self.tree.children[self.node, column]), self.cached_actions
        )


def recall_violations(tree: MatrixTree) -> int:
    """Count infos merging different past own info/action sequences, structurally."""
    signatures: dict[int, tuple[tuple[int, int], ...]] = {}
    violated: set[int] = set()
    paths: list[tuple[tuple[tuple[int, int], ...], tuple[tuple[int, int], ...]]] = [
        ((), ()) for _ in tree.player
    ]
    for node in range(len(tree.player)):
        actor, info = int(tree.player[node]), int(tree.information[node])
        if actor >= 0:
            past = paths[node][actor]
            if signatures.setdefault(info, past) != past:
                violated.add(info)
        for column, action in enumerate(tree.node_actions[node]):
            child = int(tree.children[node, column])
            first, second = paths[node]
            if actor == 0:
                first += ((info, action),)
            elif actor == 1:
                second += ((info, action),)
            paths[child] = first, second
    return len(violated)
