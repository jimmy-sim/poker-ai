"""Own tree arithmetic and optional native-reference export alignment."""

from pathlib import Path

import pytest

from poker_ai.solver_validation.reference import Reference, SpotTree
from poker_ai.solver_validation.spots import load_spot

ROOT = Path(__file__).resolve().parents[1]


def test_spot_tree_has_finite_information_sets_and_uniform_root_reach() -> None:
    tree = SpotTree.build(load_spot(ROOT / "configs/spots/dry_low_oop.json"))
    policy = tree.uniform()
    assert 0 < len(tree.keys) < len(tree.states) < tree.spot.max_tree_nodes
    reach = tree.reaches(policy)
    assert reach[0] == 1
    assert sum(
        reach[i] for i, s in enumerate(tree.states) if s.terminal
    ) == pytest.approx(1)
    assert sum(1 for s in tree.states if s.terminal) > tree.spot.worlds
    assert abs(tree.values(policy)[0]) <= 200
    assert tree.efg().count("\n") == len(tree.states) + 1


def test_native_parser_value_br_and_cfr_alignment() -> None:
    pytest.importorskip("pyspiel")
    tree = SpotTree.build(load_spot(ROOT / "configs/spots/dry_low_oop.json"))
    reference = Reference(tree)
    uniform = tree.uniform()
    assert reference.value(uniform) == pytest.approx(tree.values(uniform)[0], abs=1e-10)
    initial = reference.exploitability(uniform)
    reference.train_to(64)
    policy = reference.policy()
    assert reference.value(policy) == pytest.approx(tree.values(policy)[0], abs=1e-10)
    assert reference.exploitability(policy) < initial
