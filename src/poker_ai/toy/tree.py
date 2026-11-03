"""Materialize small exact game trees; chance probabilities remain explicit."""

from dataclasses import dataclass
from typing import cast

import numpy as np
from numpy.typing import NDArray

from poker_ai.toy.games import GameName, ToyState

FloatArray = NDArray[np.float64]
IntArray = NDArray[np.int64]


@dataclass(frozen=True)
class Tree:
    states: tuple[ToyState, ...]
    children: IntArray
    valid: NDArray[np.bool_]
    player: IntArray  # -2 terminal, -1 chance, otherwise 0/1.
    information: IntArray
    keys: tuple[str, ...]
    actions: tuple[tuple[int, ...], ...]
    owners: IntArray
    legal: FloatArray
    chance_edges: FloatArray
    chance_reach: FloatArray
    terminal_values: FloatArray
    levels: tuple[IntArray, ...]

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
            tuple(states),
            child_array,
            valid,
            players,
            np.array(infos, dtype=np.int64),
            tuple(keys),
            tuple(actions),
            np.array(owners, dtype=np.int64),
            legal,
            chance_edges,
            chance_reach,
            np.array([s.payoff if s.terminal else 0 for s in states]),
            levels,
        )

    def normalize(self, weights: FloatArray) -> FloatArray:
        """Normalize nonnegative legal action weights, falling back to uniform."""
        if weights.shape != self.legal.shape or not np.all(np.isfinite(weights)):
            raise ValueError("invalid strategy weights")
        if np.any(weights < 0) or np.any(weights * (1 - self.legal)):
            raise ValueError("negative or illegal action weight")
        total = weights.sum(axis=1, keepdims=True)
        return cast(
            FloatArray,
            np.divide(
                weights,
                total,
                out=self.legal / self.legal.sum(axis=1, keepdims=True),
                where=total > 0,
            ),
        )

    def validate_policy(self, policy: FloatArray) -> None:
        if (
            policy.shape != self.legal.shape
            or not np.all(np.isfinite(policy))
            or np.any(policy < 0)
            or np.any(policy * (1 - self.legal))
            or not np.allclose(policy.sum(axis=1), 1, atol=1e-12, rtol=0)
        ):
            raise ValueError("policy must assign normalized legal probabilities")

    def edges(self, policy: FloatArray) -> FloatArray:
        self.validate_policy(policy)
        probabilities = self.chance_edges.copy()
        decision = np.flatnonzero(self.player >= 0)
        probabilities[decision] = policy[self.information[decision]]
        return probabilities

    def values(self, probabilities: FloatArray) -> FloatArray:
        values = self.terminal_values.copy()
        for nodes in reversed(self.levels):
            values[nodes] = (values[self.children[nodes]] * probabilities[nodes]).sum(
                axis=1
            )
        return values

    def reaches(self, probabilities: FloatArray) -> FloatArray:
        """Each player's own realization reach; deliberately excludes chance."""
        reach = np.ones((len(self.states), 2))
        for nodes in self.levels:
            for player in (0, 1):
                factors = np.where(
                    self.player[nodes, None] == player, probabilities[nodes], 1.0
                )
                contributions = reach[nodes, player, None] * factors
                active = self.valid[nodes]
                reach[self.children[nodes][active], player] = contributions[active]
        return reach
