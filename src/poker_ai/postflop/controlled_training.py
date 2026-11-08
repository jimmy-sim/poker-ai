"""Own full/external CFR controls with separately specified training conventions.

This is an experimental harness, not a replacement for either historical trainer.
Simple external averaging is estimated on the opponent's target pass and includes
chance in expectation. Full traversal can use that same expectation, or explicit
historical own-pass/history-mass conventions for a deterministic bridge.
"""

from dataclasses import dataclass
from typing import Literal

import numpy as np
from numpy.random import Generator

from poker_ai.finite import ArrayTree, FloatArray
from poker_ai.training.mccfr import SampleState, Updates, external_updates

Traversal = Literal["full", "external"]
Weight = Literal["uniform", "linear"]
Phase = Literal["target_pass", "opponent_pass"]
Mass = Literal["own_reach", "chance_own_reach"]


@dataclass(frozen=True)
class Rules:
    regret_rule: Literal["signed", "clipped"] = "signed"
    regret_weight: Weight = "uniform"
    average_weight: Weight = "uniform"

    def __post_init__(self) -> None:
        if (
            self.regret_rule not in ("signed", "clipped")
            or self.regret_weight not in ("uniform", "linear")
            or self.average_weight not in ("uniform", "linear")
        ):
            raise ValueError("unknown controlled training rule")


@dataclass(frozen=True)
class ArrayState:
    """SampleState adapter; only the supplied information groups enter policy."""

    tree: ArrayTree
    node: int = 0

    @property
    def terminal(self) -> bool:
        return bool(self.tree.player[self.node] == -2)

    @property
    def chance(self) -> bool:
        return bool(self.tree.player[self.node] == -1)

    @property
    def actor(self) -> int:
        if self.terminal or self.chance:
            raise ValueError("actor requires a decision")
        return int(self.tree.player[self.node])

    @property
    def actions(self) -> tuple[int, ...]:
        if self.terminal:
            return ()
        if self.chance:
            return tuple(range(int(self.tree.valid[self.node].sum())))
        return self.tree.actions[int(self.tree.information[self.node])]

    @property
    def information(self) -> str:
        if self.terminal or self.chance:
            raise ValueError("information requires a decision")
        return self.tree.keys[int(self.tree.information[self.node])]

    @property
    def payoff(self) -> float:
        if not self.terminal:
            raise ValueError("payoff requires a terminal")
        return float(self.tree.terminal_values[self.node])

    @property
    def chance_probabilities(self) -> tuple[float, ...]:
        if not self.chance:
            raise ValueError("probabilities require chance")
        return tuple(
            float(x) for x in self.tree.chance_edges[self.node, : len(self.actions)]
        )

    def child(self, action: int) -> SampleState:
        if type(action) is not int or action not in self.actions:
            raise ValueError("illegal controlled action")
        return ArrayState(
            self.tree, int(self.tree.children[self.node, self.actions.index(action)])
        )


def expected_pass(
    tree: ArrayTree,
    policy: FloatArray,
    target: int,
    *,
    average_phase: Phase = "opponent_pass",
    average_mass: Mass = "chance_own_reach",
) -> Updates:
    """Full frozen-pass expectation, including simple external averaging.

    Regrets exclude own reach. In matched mode, averaging for j != target has
    mass chance(h)*own_reach_j(h)*sigma_j(h). All histories of a shared row are
    summed before the caller clips accumulated regret. No joint policy mutation
    occurs in this function. N visited nodes include terminals and zero reach.
    """
    if type(target) is not int or target not in (0, 1):
        raise ValueError("target must be zero or one")
    if average_phase not in ("target_pass", "opponent_pass") or average_mass not in (
        "own_reach",
        "chance_own_reach",
    ):
        raise ValueError("unknown averaging convention")
    edges = tree.edges(policy)
    reach, values = tree.reaches(edges), tree.values(edges)
    regrets, averages = np.zeros_like(tree.legal), np.zeros_like(tree.legal)
    nodes = np.flatnonzero(tree.player == target)
    infos = tree.information[nodes]
    advantage = (values[tree.children[nodes]] - values[nodes, None]) * tree.valid[nodes]
    advantage *= 1 if target == 0 else -1
    cf = tree.chance_reach[nodes] * reach[nodes, 1 - target]
    np.add.at(regrets, infos, cf[:, None] * advantage)
    actor = target if average_phase == "target_pass" else 1 - target
    nodes = np.flatnonzero(tree.player == actor)
    infos = tree.information[nodes]
    mass = reach[nodes, actor].copy()
    if average_mass == "chance_own_reach":
        mass *= tree.chance_reach[nodes]
    np.add.at(averages, infos, mass[:, None] * policy[infos])
    return Updates(
        {
            tree.keys[i]: regrets[i, : len(tree.actions[i])].copy()
            for i in range(len(tree.keys))
            if tree.owners[i] == target
        },
        {
            tree.keys[i]: averages[i, : len(tree.actions[i])].copy()
            for i in range(len(tree.keys))
            if tree.owners[i] == actor
        },
        len(tree.player),
    )


class ControlledTrainer:
    """Common alternating updater; raw time weights are 1 or iteration t.

    A complete iteration is target 0 then target 1. Each target's policy is frozen
    before traversal; increments aggregate before clipping. The common warm start
    uses TWO simultaneous uniform expectations and costs 2N visits. No arithmetic
    equivalence to fused historical runs or convergence is assumed.
    """

    def __init__(
        self,
        tree: ArrayTree,
        rng: Generator,
        *,
        traversal: Traversal = "external",
        rules: Rules | None = None,
        average_phase: Phase = "opponent_pass",
        average_mass: Mass = "chance_own_reach",
    ) -> None:
        if traversal not in ("full", "external"):
            raise ValueError("unknown traversal")
        if average_phase not in (
            "target_pass",
            "opponent_pass",
        ) or average_mass not in ("own_reach", "chance_own_reach"):
            raise ValueError("unknown averaging convention")
        if traversal == "external" and (
            average_phase != "opponent_pass" or average_mass != "chance_own_reach"
        ):
            raise ValueError("external updates require matched simple averaging")
        self.tree, self.rng, self.rules = tree, rng, rules or Rules()
        self.traversal = traversal
        self.average_phase, self.average_mass = average_phase, average_mass
        self.regrets = np.zeros_like(tree.legal)
        self.strategy_sum = np.zeros_like(tree.legal)
        self.iteration = self.nodes_visited = self.initialization_visits = 0
        self.sampled_keys: set[str] = set()
        self.lookup = {key: i for i, key in enumerate(tree.keys)}

    @property
    def current_policy(self) -> FloatArray:
        return self.tree.normalize(np.maximum(self.regrets, 0))

    @property
    def average_policy(self) -> FloatArray:
        return self.tree.normalize(self.strategy_sum)

    def _apply(self, updates: Updates, target: int, iteration: int) -> None:
        # Validate the whole update before mutation, including target ownership.
        avg_owner = target if self.average_phase == "target_pass" else 1 - target
        for table, owner in ((updates.regrets, target), (updates.averages, avg_owner)):
            for key, value in table.items():
                if key not in self.lookup:
                    raise ValueError("unknown update row")
                i = self.lookup[key]
                if (
                    self.tree.owners[i] != owner
                    or value.shape != (len(self.tree.actions[i]),)
                    or not np.all(np.isfinite(value))
                    or (table is updates.averages and np.any(value < 0))
                ):
                    raise ValueError("invalid controlled update")
        rw = float(iteration) if self.rules.regret_weight == "linear" else 1.0
        aw = float(iteration) if self.rules.average_weight == "linear" else 1.0
        for key, value in updates.regrets.items():
            i = self.lookup[key]
            n = len(value)
            self.regrets[i, :n] += rw * value
            if self.rules.regret_rule == "clipped":
                self.regrets[i, :n] = np.maximum(0, self.regrets[i, :n])
        for key, value in updates.averages.items():
            self.strategy_sum[self.lookup[key], : len(value)] += aw * value

    def initialize_exact(self) -> None:
        """Simultaneous uniform iteration; independent of the later bridge mode."""
        if (
            self.iteration
            or self.nodes_visited
            or np.any(self.regrets)
            or np.any(self.strategy_sum)
        ):
            raise ValueError("exact initialization requires an unused trainer")
        policy = self.current_policy
        updates = [expected_pass(self.tree, policy, i) for i in (0, 1)]
        # Initialization's expected simple averages always belong to the other
        # player, even if later full bridge iterations use own-pass averaging.
        phase = self.average_phase
        self.average_phase = "opponent_pass"
        try:
            for i, update in enumerate(updates):
                self._apply(update, i, 1)
        finally:
            self.average_phase = phase
        self.iteration = 1
        self.initialization_visits = 2 * len(self.tree.player)
        self.nodes_visited = self.initialization_visits

    def step(self) -> None:
        t = self.iteration + 1
        for target in (0, 1):
            policy = self.current_policy

            def frozen(
                key: str, actions: tuple[int, ...], policy: FloatArray = policy
            ) -> FloatArray:
                i = self.lookup[key]
                if actions != self.tree.actions[i]:
                    raise ValueError("controlled action menu mismatch")
                if self.traversal == "external":
                    self.sampled_keys.add(key)
                return policy[i, : len(actions)].copy()

            def select(probabilities: FloatArray) -> int:
                return int(self.rng.choice(len(probabilities), p=probabilities))

            update = (
                expected_pass(
                    self.tree,
                    policy,
                    target,
                    average_phase=self.average_phase,
                    average_mass=self.average_mass,
                )
                if self.traversal == "full"
                else external_updates(ArrayState(self.tree), target, frozen, select)
            )
            self._apply(update, target, t)
            self.nodes_visited += update.visited
        self.iteration = t

    def advance_work(self, threshold: int) -> tuple[int, int]:
        """First complete iteration crossing W; return prior work and last cost."""
        if type(threshold) is not int or threshold <= self.nodes_visited:
            raise ValueError("work threshold must exceed existing work")
        previous = last = 0
        while self.nodes_visited < threshold:
            previous = self.nodes_visited
            self.step()
            last = self.nodes_visited - previous
        return previous, last
