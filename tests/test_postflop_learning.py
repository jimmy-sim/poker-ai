"""Own finite postflop backend: chance, observation boundaries, solver alignment."""

import ast
import json
from pathlib import Path

import numpy as np
import pytest
from numpy.random import PCG64, Generator

from poker_ai.abstraction.model import CardAbstraction
from poker_ai.postflop.game import SpotState, load_spot
from poker_ai.postflop.matrix import IndexedState, MatrixTree, observation_key
from poker_ai.postflop.tree import SpotTree
from poker_ai.solver_validation.reference import Reference
from poker_ai.toy.analysis import evaluate
from poker_ai.toy.cfr import CFR
from poker_ai.training.mccfr import MCCFR

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def low_tree() -> SpotTree:
    return SpotTree.build(load_spot(ROOT / "configs/learning-spots/dev_low_oop.json"))


def test_own_game_compatibility_exports() -> None:
    from poker_ai.solver_validation.reference import SpotTree as LegacyTree
    from poker_ai.solver_validation.spots import SpotState as LegacyState

    assert LegacyState is SpotState and LegacyTree is SpotTree


def test_exact_matrix_chance_values_and_serialized_policy(low_tree: SpotTree) -> None:
    tree = MatrixTree.build(low_tree)
    policy = tree.normalize(tree.legal)
    exact = tree.exact_policy(policy)
    np.testing.assert_array_equal(tree.dense_exact(exact), policy)
    assert tree.keys == low_tree.keys
    assert float(tree.values(tree.edges(policy))[0]) == pytest.approx(
        low_tree.values(exact)[0]
    )
    reaches = tree.reaches(tree.edges(policy))
    terminals = tree.player == -2
    assert (
        tree.chance_reach[terminals] * reaches[terminals].prod(axis=1)
    ).sum() == pytest.approx(1)
    assert sum(
        low_tree.reaches(exact)[i] for i in np.flatnonzero(terminals)
    ) == pytest.approx(1)
    root = IndexedState(tree)
    assert root.chance and not root.terminal
    with pytest.raises(ValueError):
        _ = root.information
    for action in root.actions:
        assert root.child(action).chance


def test_nonuniform_range_chance_is_preserved(tmp_path: Path) -> None:
    raw = json.loads((ROOT / "configs/learning-spots/dev_low_oop.json").read_text())
    raw["ranges"][0][0]["weight"] = 3.0
    path = tmp_path / "spot.json"
    path.write_text(json.dumps(raw))
    tree = MatrixTree.build(SpotTree.build(load_spot(path)))
    assert IndexedState(tree).chance_probabilities == pytest.approx((0.75, 0.25))
    np.testing.assert_allclose(tree.chance_edges[0, :2], [0.75, 0.25])


def test_matrix_cfr_matches_independent_solver(low_tree: SpotTree) -> None:
    pytest.importorskip("pyspiel")
    tree = MatrixTree.build(low_tree)
    own = CFR(tree, "cfr_plus")
    reference = Reference(low_tree)
    for iteration in (1, 2, 16):
        own.train(iteration - own.iteration)
        reference.train_to(iteration)
        policy = tree.exact_policy(own.average_policy)
        np.testing.assert_allclose(
            np.concatenate(policy),
            np.concatenate(reference.policy()),
            atol=1e-10,
            rtol=0,
        )
        assert evaluate(tree, own.average_policy).exploitability == pytest.approx(
            reference.exploitability(policy), abs=1e-9
        )


def test_observation_keys_hide_opponent_and_future_cards() -> None:
    spot = load_spot(ROOT / "configs/learning-spots/dev_low_oop.json")
    base = SpotState(spot).child(0).child(0)
    first = base.child(base.actions[0])
    different_river = base.child(base.actions[1])
    other = SpotState(spot).child(0).child(1)
    different_opponent = other.child(other.actions[0])
    model = CardAbstraction.load(ROOT / "results/card-models/potential-8.json")
    for encoding in ("exact", "legacy_b8", "public_b8"):
        assert first.dealer is not None and different_river.dealer is not None
        assert different_opponent.dealer is not None
        keys = []
        for state in (first, different_river, different_opponent):
            assert state.dealer is not None
            keys.append(
                observation_key(state.dealer.observe(state.actor), encoding, model)
            )
        assert len(set(keys)) == 1


def test_sampled_matrix_adapter_replays_rng(low_tree: SpotTree) -> None:
    tree = MatrixTree.build(low_tree)

    def solver() -> MCCFR:
        return MCCFR(
            lambda rng: IndexedState(tree), Generator(PCG64(43)), method="external"
        )

    a, b = solver(), solver()
    a.train(20)
    b.train(20)
    assert a.nodes_visited == b.nodes_visited
    assert a.rows.keys() == b.rows.keys()
    for key in a.rows:
        np.testing.assert_array_equal(a.rows[key].regrets, b.rows[key].regrets)
        np.testing.assert_array_equal(
            a.rows[key].strategy_sum, b.rows[key].strategy_sum
        )


def test_postflop_training_has_no_reference_imports() -> None:
    for path in (ROOT / "src/poker_ai/postflop").glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            names = (
                [node.module or ""]
                if isinstance(node, ast.ImportFrom)
                else [a.name for a in node.names]
                if isinstance(node, ast.Import)
                else []
            )
            assert not any(
                n.startswith(("poker_ai.solver_validation", "open_spiel", "pyspiel"))
                for n in names
            ), path


def test_representations_preserve_own_abstract_recall(low_tree: SpotTree) -> None:
    from poker_ai.postflop.matrix import recall_violations

    model = CardAbstraction.load(ROOT / "results/card-models/potential-8.json")
    for encoding in ("exact", "legacy_b8", "public_b8"):
        assert recall_violations(MatrixTree.build(low_tree, encoding, model)) == 0


def test_profiled_menu_cache_preserves_all_sampled_updates(low_tree: SpotTree) -> None:
    tree = MatrixTree.build(low_tree)
    cached = MCCFR(lambda rng: IndexedState(tree), Generator(PCG64(17)))
    dynamic = MCCFR(
        lambda rng: IndexedState(tree, cached_actions=False), Generator(PCG64(17))
    )
    cached.train(200)
    dynamic.train(200)
    assert cached.nodes_visited == dynamic.nodes_visited
    assert cached.rows.keys() == dynamic.rows.keys()
    for key in cached.rows:
        np.testing.assert_array_equal(
            cached.rows[key].regrets, dynamic.rows[key].regrets
        )
        np.testing.assert_array_equal(
            cached.rows[key].strategy_sum, dynamic.rows[key].strategy_sum
        )
