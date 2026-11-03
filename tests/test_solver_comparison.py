"""Exact common-opponent accounting and zero-gap integration controls."""

from pathlib import Path

import pytest

from poker_ai.abstraction.model import CardAbstraction
from poker_ai.agents.no_limit import OwnNoLimitAgent
from poker_ai.solver_validation.comparison import (
    AgentPolicy,
    compare,
    compile_agent,
    ev_attribution,
    information_reach,
    prepare_contexts,
    root_hand_values,
    weighted_gap,
)
from poker_ai.solver_validation.reference import Reference, SpotTree
from poker_ai.solver_validation.spots import load_spot

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def tree() -> SpotTree:
    return SpotTree.build(load_spot(ROOT / "configs/spots/dry_low_oop.json"))


def test_prepared_uniform_fallback_matches_exact_spot_menus(tree: SpotTree) -> None:
    model = CardAbstraction.load(ROOT / "results/card-models/potential-2.json")
    agent = OwnNoLimitAgent(model, tree.spot.rules, {})
    contexts = prepare_contexts(tree, agent, 28)
    compiled = compile_agent(tree, agent, contexts)
    assert compiled.policy == tree.uniform()
    assert set(compiled.statuses) == {"unseen"}
    assert compiled.shadow_changes == 0
    assert compiled.projection_mass == 0
    with pytest.raises(ValueError, match="observation"):
        compile_agent(tree, agent, tuple(reversed(contexts)))


def test_ev_attribution_telescopes_for_both_players(tree: SpotTree) -> None:
    uniform = tree.uniform()
    pure = tuple((1.0,) + (0.0,) * (len(m) - 1) for m in tree.menus)
    statuses = tuple("odd" if i % 2 else "even" for i in range(len(tree.keys)))
    for hero in (0, 1):
        policy = tree.cross(pure, uniform) if hero == 0 else tree.cross(uniform, pure)
        parts = ev_attribution(tree, policy, uniform, statuses, hero)
        expected = (1 if hero == 0 else -1) * (
            tree.values(policy)[0] - tree.values(uniform)[0]
        )
        assert sum(parts.values()) == pytest.approx(expected, abs=1e-10)
    with pytest.raises(ValueError, match="same opponent"):
        ev_attribution(tree, pure, uniform, statuses, 0)


def test_hand_conditional_values_average_back_to_root(tree: SpotTree) -> None:
    values = tree.values(tree.uniform())
    for hero in (0, 1):
        by_class = root_hand_values(tree, values, hero)
        # This fixture has equal marginal weights and distinct two hand classes.
        assert len(by_class) == 2
        assert sum(by_class.values()) / 2 == pytest.approx(
            (1 if hero == 0 else -1) * values[0], abs=1e-10
        )
    mass = information_reach(tree, tree.uniform())
    assert (
        weighted_gap(tree.uniform(), tree.uniform(), mass, list(range(len(mass)))) == 0
    )


def test_reference_compared_to_itself_has_zero_all_gaps(tree: SpotTree) -> None:
    pytest.importorskip("pyspiel")
    reference = Reference(tree)
    reference.train_to(64)
    policy = reference.policy()
    compiled = AgentPolicy(policy, ("matched",) * len(policy), 0.0, 0)
    result = compare(tree, reference, policy, compiled, tolerance=1e-9, detailed=True)
    assert result["action_gap"] == 0
    assert result["hero_ev_gap_vs_reference_opponent"] == 0
    assert result["hero_ev_gap_vs_own_opponent"] == 0
    assert all(v == 0 for v in result["ev_gap_attribution_vs_reference"].values())
    assert all(
        row["own_probabilities"] == row["reference_probabilities"]
        for row in result["decision_rows"]
    )
    for row in result["node_frequencies"]:
        assert row["own"] == row["reference"]
        if row["reference_reach"] > 0:
            assert sum(row["own"].values()) == pytest.approx(1)


def test_passive_worlds_match_independent_evaluator() -> None:
    pytest.importorskip("treys")
    from poker_ai.solver_validation.controls import verify_card_worlds

    for path in sorted((ROOT / "configs/spots").glob("*.json")):
        spot = load_spot(path)
        assert verify_card_worlds(spot)["worlds_checked"] == spot.worlds


def test_reference_code_cannot_enter_production_policy_path() -> None:
    import ast

    paths: list[Path] = []
    for package in ("agents", "training", "abstraction"):
        paths.extend((ROOT / "src/poker_ai" / package).glob("*.py"))
    for path in paths:
        for node in ast.walk(ast.parse(path.read_text())):
            names = (
                [node.module or ""]
                if isinstance(node, ast.ImportFrom)
                else [alias.name for alias in node.names]
                if isinstance(node, ast.Import)
                else []
            )
            assert not any(
                name.startswith(("poker_ai.solver_validation", "open_spiel", "pyspiel"))
                for name in names
            ), path
