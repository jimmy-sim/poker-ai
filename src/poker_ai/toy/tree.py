"""Materialize small exact game trees; chance probabilities remain explicit."""

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from poker_ai.finite import ArrayTree
from poker_ai.toy.games import GameName, ToyState

FloatArray = NDArray[np.float64]
IntArray = NDArray[np.int64]


@dataclass(frozen=True)
class Tree(ArrayTree):
    states: tuple[ToyState, ...]

    @classmethod
    def build(cls, game: GameName) -> "Tree":
        states: list[ToyState] = []
        children: list[list[int]] = []
        depths: list[int] = []
        infos: list[int] = []
        keys: list[str] = []
        actions: list[tuple[int, ...]] = []
        owners: list[int] = []
        lookup: dict[str, int] = {}
        info_depths: dict[str, int] = {}

        def visit(state: ToyState, depth: int) -> int:
            index = len(states)
            states.append(state)
            depths.append(depth)
            children.append([])
            info = -1
            if not state.chance and not state.terminal:
                key = state.information
                if key not in lookup:
                    lookup[key] = len(keys)
                    keys.append(key)
                    actions.append(state.actions)
                    owners.append(state.actor)
                info = lookup[key]
                assert actions[info] == state.actions and owners[info] == state.actor
                assert info_depths.setdefault(key, depth) == depth
            infos.append(info)
            children[index] = [visit(state.child(a), depth + 1) for a in state.actions]
            return index

        visit(ToyState(game), 0)
        size = len(states)
        width = max(map(len, children))
        child_array = np.zeros((size, width), dtype=np.int64)
        valid = np.zeros((size, width), dtype=np.bool_)
        chance_edges = np.zeros((size, width))
        players = np.array(
            [-2 if s.terminal else -1 if s.chance else s.actor for s in states],
            dtype=np.int64,
        )
        chance_reach = np.ones(size)
        for index, group in enumerate(children):
            child_array[index, : len(group)] = group
            valid[index, : len(group)] = True
            if states[index].chance:
                chance_edges[index, : len(group)] = 1 / len(group)
            for child in group:
                chance_reach[child] = chance_reach[index] * (
                    1 / len(group) if states[index].chance else 1
                )
        legal = np.zeros((len(keys), width))
        for info, moves in enumerate(actions):
            legal[info, : len(moves)] = 1
        depth_array = np.array(depths)
        levels = tuple(
            np.flatnonzero((depth_array == d) & (players != -2))
            for d in range(max(depths) + 1)
        )
        return cls(
            states=tuple(states),
            children=child_array,
            valid=valid,
            player=players,
            information=np.array(infos, dtype=np.int64),
            keys=tuple(keys),
            actions=tuple(actions),
            owners=np.array(owners, dtype=np.int64),
            legal=legal,
            chance_edges=chance_edges,
            chance_reach=chance_reach,
            terminal_values=np.array([s.payoff if s.terminal else 0 for s in states]),
            levels=levels,
        )
