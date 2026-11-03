"""Two-player Monte Carlo CFR with explicit random state and deferred updates.

External sampling estimates regrets by sampling chance/opponent and enumerating
own actions; simple two-player averaging updates the opponent's visited strategy.
Outcome sampling explores target actions with epsilon and follows one trajectory.
Its backward suffix value includes target/sampling tail likelihood ratios. The
regret prefix correction is opponent-including-chance reach / sampling reach;
averaging uses own realization reach / sampling reach. Own reach is never
included in counterfactual regret. Policies are frozen during each target pass.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal, Protocol

import numpy as np
from numpy.random import Generator

from poker_ai.toy.tree import FloatArray


class SampleState(Protocol):
    @property
    def terminal(self) -> bool: ...
    @property
    def chance(self) -> bool: ...
    @property
    def actor(self) -> int: ...
    @property
    def actions(self) -> tuple[int, ...]: ...
    @property
    def information(self) -> str: ...
    @property
    def payoff(self) -> float: ...
    @property
    def chance_probabilities(self) -> tuple[float, ...]: ...
    def child(self, action: int) -> "SampleState": ...


Selector = Callable[[FloatArray], int]
Policy = Callable[[str, tuple[int, ...]], FloatArray]
RootFactory = Callable[[Generator], SampleState]
Method = Literal["external", "outcome"]


@dataclass
class Row:
    actions: tuple[int, ...]
    regrets: FloatArray
    strategy_sum: FloatArray


@dataclass
class Updates:
    regrets: dict[str, FloatArray]
    averages: dict[str, FloatArray]
    visited: int = 0


def _add(table: dict[str, FloatArray], key: str, value: FloatArray) -> None:
    if key not in table:
        table[key] = value.copy()
    else:
        table[key] += value


def external_updates(
    root: SampleState, target: int, policy: Policy, select: Selector
) -> Updates:
    """One external-sampling target pass. Selector receives legal probabilities."""
    updates = Updates({}, {})

    def visit(state: SampleState) -> float:
        updates.visited += 1
        if state.terminal:
            return state.payoff * (1 if target == 0 else -1)
        actions = state.actions
        if state.chance:
            probabilities = np.asarray(state.chance_probabilities, dtype=np.float64)
            return visit(state.child(actions[select(probabilities)]))
        key = state.information
        sigma = policy(key, actions)
        if state.actor != target:
            _add(updates.averages, key, sigma)
            return visit(state.child(actions[select(sigma)]))
        values = np.array([visit(state.child(action)) for action in actions])
        value = float(sigma @ values)
        _add(updates.regrets, key, values - value)
        return value

    visit(root)
    return updates


@dataclass(frozen=True)
class Decision:
    key: str
    actor: int
    sigma: FloatArray
    chosen: int
    behavior_probability: float
    own_reach: float
    opponent_reach: float
    sample_reach: float


def outcome_updates(
    root: SampleState, target: int, policy: Policy, select: Selector, epsilon: float
) -> Updates:
    """One outcome sample, using zero-baseline importance-weighted suffix values.

    At h, only sampled action a has estimated action value suffix/q(a|h).
    The local value is sigma(a|h) times that estimate. Multiplication by
    pi_-i(h)/q(h) yields the counterfactual action/value estimates. Their difference
    estimates regret; pi_i(h)*sigma(.|h)/q(h) estimates averaging mass. Chance
    is sampled on-policy, so its suffix likelihood ratio is one.
    """
    if not 0 < epsilon <= 1:
        raise ValueError("outcome exploration must lie in (0,1]")
    updates = Updates({}, {})
    path: list[Decision] = []
    own_reach = opponent_reach = sample_reach = 1.0
    state = root
    while not state.terminal:
        updates.visited += 1
        actions = state.actions
        if state.chance:
            probabilities = np.asarray(state.chance_probabilities, dtype=np.float64)
            chosen = select(probabilities)
            opponent_reach *= float(probabilities[chosen])
            sample_reach *= float(probabilities[chosen])
        else:
            key = state.information
            sigma = policy(key, actions)
            behavior = (
                (1 - epsilon) * sigma + epsilon / len(actions)
                if state.actor == target
                else sigma
            )
            chosen = select(behavior)
            probability = float(behavior[chosen])
            if probability <= 0:
                raise ValueError("selector chose a zero-probability action")
            path.append(
                Decision(
                    key,
                    state.actor,
                    sigma,
                    chosen,
                    probability,
                    own_reach,
                    opponent_reach,
                    sample_reach,
                )
            )
            if state.actor == target:
                own_reach *= float(sigma[chosen])
            else:
                opponent_reach *= float(sigma[chosen])
            sample_reach *= probability
        state = state.child(actions[chosen])
    updates.visited += 1
    suffix = state.payoff * (1 if target == 0 else -1)
    for decision in reversed(path):
        action_values = np.zeros(len(decision.sigma))
        action_values[decision.chosen] = suffix / decision.behavior_probability
        value = float(decision.sigma @ action_values)
        if decision.actor == target:
            correction = decision.opponent_reach / decision.sample_reach
            _add(updates.regrets, decision.key, correction * (action_values - value))
            _add(
                updates.averages,
                decision.key,
                decision.own_reach / decision.sample_reach * decision.sigma,
            )
        suffix = value
    return updates


class MCCFR:
    def __init__(
        self,
        root_factory: RootFactory,
        rng: Generator,
        *,
        method: Method = "external",
        epsilon: float = 0.6,
    ) -> None:
        if method not in ("external", "outcome") or not 0 < epsilon <= 1:
            raise ValueError("invalid sampling method or exploration")
        self.root_factory = root_factory
        self.rng = rng
        self.method = method
        self.epsilon = epsilon
        self.iteration = 0
        self.nodes_visited = 0
        self.rows: dict[str, Row] = {}

    def _row(self, key: str, actions: tuple[int, ...]) -> Row:
        if key not in self.rows:
            self.rows[key] = Row(
                actions, np.zeros(len(actions)), np.zeros(len(actions))
            )
        row = self.rows[key]
        if row.actions != actions:
            raise ValueError("information set has inconsistent legal actions")
        return row

    def policy(
        self, key: str, actions: tuple[int, ...], *, average: bool = False
    ) -> FloatArray:
        row = self._row(key, actions)
        weights = row.strategy_sum if average else np.maximum(row.regrets, 0)
        total = float(weights.sum())
        return weights / total if total > 0 else np.full(len(actions), 1 / len(actions))

    def step(self) -> None:
        for target in (0, 1):

            def select(probabilities: FloatArray) -> int:
                return int(self.rng.choice(len(probabilities), p=probabilities))

            root = self.root_factory(self.rng)
            updates = (
                external_updates(root, target, self.policy, select)
                if self.method == "external"
                else outcome_updates(root, target, self.policy, select, self.epsilon)
            )
            for key, delta in updates.regrets.items():
                self.rows[key].regrets += delta
            for key, mass in updates.averages.items():
                self.rows[key].strategy_sum += mass
            self.nodes_visited += updates.visited
        self.iteration += 1

    def train(self, iterations: int) -> None:
        if type(iterations) is not int or iterations < 0:
            raise ValueError("iterations must be a nonnegative integer")
        for _ in range(iterations):
            self.step()
