"""Immutable cached ArrayState interface for fixed finite simulation trees."""

import struct
import time
from dataclasses import dataclass
from typing import Any, cast

from numpy.random import Generator

from poker_ai.finite import ArrayTree, FloatArray
from poker_ai.postflop.controlled_training import (
    ArrayState,
    Mass,
    Phase,
    Rules,
    Traversal,
)
from poker_ai.postflop.row_policy import RowPolicyTrainer
from poker_ai.training.mccfr import external_updates


@dataclass(frozen=True, slots=True, eq=False, repr=False)
class CachedNode:
    node: int
    terminal: bool
    chance: bool
    actions: tuple[int, ...]
    _actor: int
    _key: str | None
    _value: float
    _probabilities: tuple[float, ...]
    _children: tuple["CachedNode", ...]

    @property
    def actor(self) -> int:
        if self.terminal or self.chance:
            raise ValueError("actor requires a decision")
        return self._actor

    @property
    def information(self) -> str:
        if self._key is None:
            raise ValueError("information requires a decision")
        return self._key

    @property
    def payoff(self) -> float:
        if not self.terminal:
            raise ValueError("payoff requires a terminal")
        return self._value

    @property
    def chance_probabilities(self) -> tuple[float, ...]:
        if not self.chance:
            raise ValueError("probabilities require chance")
        return self._probabilities

    def child(self, action: int) -> "CachedNode":
        if type(action) is not int or action not in self.actions:
            raise ValueError("illegal controlled action")
        return self._children[self.actions.index(action)]


def cache_nodes(tree: ArrayTree) -> tuple[CachedNode, ...]:
    """Build leaves then reverse levels; no parent/context reference cycles.

    This copies immutable interface metadata, not strategy or reach information.
    It assumes the supplied game arrays remain static during training. Preparation
    touches every node once and is accounted separately from CFR traversal work.
    """
    ready: list[CachedNode | None] = [None] * len(tree.player)
    if not ready:
        raise ValueError("cached tree requires a root")

    def build(node: int) -> None:
        if ready[node] is not None:
            raise ValueError("duplicate cached node in tree levels")
        actor = int(tree.player[node])
        if actor not in (-2, -1, 0, 1):
            raise ValueError("invalid cached actor")
        terminal, chance = actor == -2, actor == -1
        info = int(tree.information[node])
        degree = int(tree.valid[node].sum())
        actions = (
            () if terminal else tuple(range(degree)) if chance else tree.actions[info]
        )
        if not terminal and len(actions) != degree:
            raise ValueError("cached menu/children mismatch")
        children = []
        for column in range(len(actions)):
            child = ready[int(tree.children[node, column])]
            if child is None:
                raise ValueError("cached child missing from deeper level")
            children.append(child)
        ready[node] = CachedNode(
            node,
            terminal,
            chance,
            actions,
            actor,
            tree.keys[info] if actor >= 0 else None,
            float(tree.terminal_values[node]) if terminal else 0.0,
            tuple(float(x) for x in tree.chance_edges[node, :degree]) if chance else (),
            tuple(children),
        )

    for node in range(len(tree.player)):
        if tree.player[node] == -2:
            build(node)
    for level in reversed(tree.levels):
        for node in level:
            build(int(node))
    if any(node is None for node in ready):
        raise ValueError("cached tree levels omit nodes")
    return cast(tuple[CachedNode, ...], tuple(ready))


def _same(a: Any, b: Any) -> bool:
    if type(a) is not type(b):
        return False
    if isinstance(a, float):
        return struct.pack("<d", a) == struct.pack("<d", b)
    if isinstance(a, tuple):
        return len(a) == len(b) and all(_same(x, y) for x, y in zip(a, b, strict=True))
    return bool(a == b)


def audit_interface(tree: ArrayTree, nodes: tuple[CachedNode, ...]) -> dict[str, int]:
    """Exhaust all node properties/errors and legal edge targets, not identities."""
    if len(nodes) != len(tree.player):
        raise ArithmeticError("cached node inventory changed")
    edges = errors = 0
    for i, cached in enumerate(nodes):
        original = ArrayState(tree, i)
        for name in (
            "node",
            "terminal",
            "chance",
            "actions",
            "actor",
            "information",
            "payoff",
            "chance_probabilities",
        ):
            try:
                value = getattr(original, name)
            except ValueError as expected:
                try:
                    getattr(cached, name)
                except ValueError as actual:
                    if actual.args != expected.args:
                        raise ArithmeticError(
                            f"cached {name} error changed at {i}"
                        ) from actual
                else:
                    raise ArithmeticError(
                        f"cached {name} did not reject node {i}"
                    ) from expected
                errors += 1
            else:
                if not _same(value, getattr(cached, name)):
                    raise ArithmeticError(f"cached {name} changed at {i}")
        for action in original.actions:
            expected_child = cast(ArrayState, original.child(action))
            actual_child = cached.child(action)
            if (
                actual_child.node != expected_child.node
                or actual_child is not nodes[expected_child.node]
            ):
                raise ArithmeticError(f"cached edge changed at {i}")
            edges += 1
        for invalid in (True, max(original.actions, default=-1) + 1):
            for state in (original, cached):
                try:
                    state.child(invalid)
                except ValueError as error:
                    if error.args != ("illegal controlled action",):
                        raise ArithmeticError(
                            "cached illegal-action error changed"
                        ) from error
                else:
                    raise ArithmeticError("cached illegal action accepted")
    return dict(
        nodes=len(nodes),
        edges=edges,
        invalid_property_errors=errors,
        decision_nodes=sum(not n.terminal and not n.chance for n in nodes),
        invalid_action_pairs=2 * len(nodes),
    )


class CachedNodeTrainer(RowPolicyTrainer):
    """Frozen row-policy pipeline with only the immutable root adapter changed."""

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
        if traversal != "external":
            raise ValueError("cached-node backend supports external sampling only")
        super().__init__(
            tree,
            rng,
            traversal=traversal,
            rules=rules,
            average_phase=average_phase,
            average_mass=average_mass,
        )
        started = time.perf_counter()
        self.cached_nodes = cache_nodes(tree)
        self.node_setup_seconds = time.perf_counter() - started
        self.node_records_prepared = len(self.cached_nodes)

    def step(self) -> None:
        # Preserve the frozen parent's pass/update ordering. The sole traversal
        # substitution is the cached immutable root; no module monkey-patching.
        if self.traversal != "external":
            raise ValueError("policy-row backend supports external sampling only")
        t = self.iteration + 1
        sizes = []
        for target in (0, 1):
            cache: dict[int, FloatArray] = {}

            def frozen(
                key: str, actions: tuple[int, ...], cache: dict[int, FloatArray] = cache
            ) -> FloatArray:
                info = self.lookup[key]
                if actions != self.tree.actions[info]:
                    raise ValueError("controlled action menu mismatch")
                self.sampled_keys.add(key)
                if info not in cache:
                    cache[info] = self._policy_row(info)
                    self.row_evaluations += 1
                return cache[info][: len(actions)].copy()

            def select(probabilities: FloatArray) -> int:
                return int(self.rng.choice(len(probabilities), p=probabilities))

            update = external_updates(self.cached_nodes[0], target, frozen, select)
            self._apply(update, target, t)
            self.nodes_visited += update.visited
            sizes.append(len(cache))
        self.last_pass_rows = sizes[0], sizes[1]
        self.iteration = t
