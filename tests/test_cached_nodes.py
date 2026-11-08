"""Exhaustive cached interfaces and exact sampled states, not strength tests."""

from dataclasses import FrozenInstanceError, replace
from pathlib import Path
from typing import Literal

import numpy as np
import pytest
from numpy.random import PCG64, Generator

from poker_ai.abstraction.model import CardAbstraction
from poker_ai.postflop.cached_nodes import (
    CachedNodeTrainer,
    audit_interface,
    cache_nodes,
)
from poker_ai.postflop.controlled_training import ArrayState, Rules, Weight
from poker_ai.postflop.game import load_spot
from poker_ai.postflop.node_profile import parity
from poker_ai.postflop.range_protocol import build_representation_control
from poker_ai.postflop.river_study import Deadline
from poker_ai.postflop.row_policy import RowPolicyTrainer
from poker_ai.postflop.row_profile import assert_equal
from poker_ai.postflop.training_isolation import SPOTS, sentinel_tree
from poker_ai.postflop.tree import SpotTree

ROOT = Path(__file__).resolve().parents[1]
CLIPS: tuple[Literal["signed", "clipped"], ...] = ("signed", "clipped")
WEIGHTS: tuple[Weight, ...] = ("uniform", "linear")
RULES = [Rules(c, r, a) for c in CLIPS for r in WEIGHTS for a in WEIGHTS]


def test_exhaustive_toy_properties_errors_children_and_immutability() -> None:
    tree = sentinel_tree()
    nodes = cache_nodes(tree)
    result = audit_interface(tree, nodes)
    assert result["nodes"] == len(tree.player)
    assert result["edges"] == len(tree.player) - 1
    assert (
        result["invalid_property_errors"] == 3 * len(nodes) - result["decision_nodes"]
    )
    action = nodes[0].actions[0]
    assert nodes[0].child(action) is nodes[0].child(action)
    assert ArrayState(tree).child(action) is not ArrayState(tree).child(action)
    with pytest.raises(FrozenInstanceError):
        nodes[0].actions = (999,)  # type: ignore[misc]  # Deliberate frozen mutation.
    changed = list(nodes)
    changed[0] = replace(nodes[0], actions=(999,))
    with pytest.raises(ArithmeticError):
        audit_interface(tree, tuple(changed))


def test_reverse_levels_support_nonpreorder_node_ids() -> None:
    tree = sentinel_tree()
    order = np.concatenate(
        ([0], Generator(PCG64(8)).permutation(np.arange(1, len(tree.player))))
    )
    children = np.zeros_like(tree.children)
    children[order] = order[tree.children]
    fields = {}
    for name in (
        "valid",
        "player",
        "information",
        "chance_edges",
        "chance_reach",
        "terminal_values",
    ):
        values = getattr(tree, name)
        result = np.empty_like(values)
        result[order] = values
        fields[name] = result
    permuted = replace(
        tree,
        children=children,
        levels=tuple(order[level] for level in tree.levels),
        **fields,
    )
    assert audit_interface(permuted, cache_nodes(permuted))["nodes"] == len(tree.player)
    with pytest.raises(ValueError):
        cache_nodes(replace(tree, levels=tree.levels[:1]))


@pytest.mark.parametrize("rules", RULES)
@pytest.mark.parametrize("warm", [False, True])
def test_each_iteration_preserves_math_rng_visits_and_policy_queries(
    rules: Rules, warm: bool
) -> None:
    tree = sentinel_tree()
    parent = RowPolicyTrainer(tree, Generator(PCG64(71)), rules=rules)
    child = CachedNodeTrainer(tree, Generator(PCG64(71)), rules=rules)
    assert child.nodes_visited == child.initialization_visits == 0
    assert child.node_records_prepared == len(tree.player)
    assert child.node_setup_seconds >= 0
    assert parent.rng.bit_generator.state == child.rng.bit_generator.state
    if warm:
        parent.initialize_exact()
        child.initialize_exact()
    for _ in range(32):
        parent.step()
        child.step()
        assert_equal(parent, child)
        assert parent.row_evaluations == child.row_evaluations
        assert parent.last_pass_rows == child.last_pass_rows


def test_step_never_constructs_array_wrappers(monkeypatch: pytest.MonkeyPatch) -> None:
    import poker_ai.postflop.row_policy as frozen

    solver = CachedNodeTrainer(sentinel_tree(), Generator(PCG64(3)))
    solver.initialize_exact()

    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("ArrayState construction inside cached step")

    monkeypatch.setattr(frozen, "ArrayState", forbidden)
    solver.step()
    with pytest.raises(ValueError, match="external"):
        CachedNodeTrainer(sentinel_tree(), Generator(PCG64(3)), traversal="full")


def test_all_four_real_interfaces_and_all_rule_prefixes() -> None:
    model = CardAbstraction.load(ROOT / "results/card-models/potential-8.json")
    counts = []
    for path in SPOTS:
        raw = SpotTree.build(load_spot(ROOT / path))
        for name in ("exact", "texture_range_q8_b8"):
            tree = build_representation_control(raw, name, model)
            counts.append(audit_interface(tree, cache_nodes(tree)))
            for rules in RULES:
                cell = dict(
                    spot_file=path,
                    representation=name,
                    traversal="external",
                    regret_rule=rules.regret_rule,
                    regret_weight=rules.regret_weight,
                    average_weight=rules.average_weight,
                    seed=20261301,
                    bridge="common",
                )
                assert [
                    r["iteration"] for r in parity(tree, cell, [1, 2, 4], Deadline(30))
                ] == [1, 2, 4]
    assert sum(c["nodes"] for c in counts) == 48604
    assert sum(c["edges"] for c in counts) == 48600
