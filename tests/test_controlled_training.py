"""Controlled update math and old-trainer compatibility, not Hold'em strength."""

import copy
import itertools
import json
from pathlib import Path
from typing import Any, Literal

import numpy as np
import pytest
from numpy.random import PCG64, Generator

from poker_ai.postflop import training_isolation as audit
from poker_ai.postflop.controlled_training import (
    ArrayState,
    ControlledTrainer,
    Mass,
    Phase,
    Rules,
    Traversal,
    Weight,
    expected_pass,
)
from poker_ai.postflop.sampling import PostflopMCCFR, exact_initial_expectation
from poker_ai.toy.cfr import CFR
from poker_ai.training.mccfr import Updates
from poker_ai.validation.five_card import source_provenance

ROOT = Path(__file__).resolve().parents[1]
TRAVERSALS: tuple[Traversal, ...] = ("full", "external")
REGRET_RULES: tuple[Literal["signed", "clipped"], ...] = ("signed", "clipped")
WEIGHTS: tuple[Weight, ...] = ("uniform", "linear")


def test_real_range_mass_adapter_matches_old_sampled_updates() -> None:
    from poker_ai.abstraction.model import CardAbstraction
    from poker_ai.postflop.game import load_spot
    from poker_ai.postflop.learning import root_factory
    from poker_ai.postflop.range_protocol import build_representation_control
    from poker_ai.postflop.tree import SpotTree

    model = CardAbstraction.load(ROOT / "results/card-models/potential-8.json")
    for path in audit.SPOTS:
        source = SpotTree.build(load_spot(ROOT / path))
        tree = build_representation_control(source, "texture_range_q8_b8", model)
        old = PostflopMCCFR(root_factory(tree), Generator(PCG64(20261301)), "linear")
        new = ControlledTrainer(
            tree, Generator(PCG64(20261301)), rules=Rules("signed", "linear", "linear")
        )
        exact_initial_expectation(old, tree)
        new.initialize_exact()
        for _ in range(12):
            old.step()
            new.step()
        assert old.nodes_visited + old.warm_node_equivalent == new.nodes_visited
        assert old.rng.bit_generator.state == new.rng.bit_generator.state
        for key, row in old.rows.items():
            i = new.lookup[key]
            n = len(tree.actions[i])
            np.testing.assert_allclose(
                row.regrets, new.regrets[i, :n], atol=1e-12, rtol=0
            )
            np.testing.assert_allclose(
                row.strategy_sum, new.strategy_sum[i, :n], atol=1e-12, rtol=0
            )


def test_selector_expectations_include_all_random_subtrees_and_zero_support() -> None:
    config = json.loads((ROOT / audit.CONFIG).read_text())
    rows = audit.sentinel_checks(config)
    assert [(r["policy"], r["target"]) for r in rows] == list(
        itertools.product(["positive", "zero_support"], [0, 1])
    )
    assert [r["selector_paths"] for r in rows] == [24, 18, 6, 6]
    assert max(r["maximum_regret_error"] for r in rows) < 1e-14
    assert max(r["maximum_average_error"] for r in rows) < 1e-14
    assert max(r["maximum_expected_clip_vs_clip_expected"] for r in rows) > 0.05
    tree = audit.sentinel_tree()
    with pytest.raises(ValueError, match="cap"):
        audit.enumerate_pass(tree, tree.normalize(tree.legal), 0, maximum_paths=1)


def test_full_historical_cfr_plus_and_linear_scale_bridge() -> None:
    tree = audit.sentinel_tree()
    for variant in ("cfr_plus", "linear"):
        old = CFR(tree, variant)
        new = ControlledTrainer(
            tree,
            Generator(PCG64(4)),
            traversal="full",
            rules=Rules(
                "clipped" if variant == "cfr_plus" else "signed",
                "uniform" if variant == "cfr_plus" else "linear",
                "linear",
            ),
            average_phase="target_pass",
            average_mass="own_reach",
        )
        for _ in range(32):
            old.step()
            new.step()
            scale = old.iteration + 1 if variant == "linear" else 1
            np.testing.assert_allclose(
                new.regrets / scale, old.regrets, atol=1e-12, rtol=0
            )
            np.testing.assert_allclose(
                new.current_policy, old.current_policy, atol=1e-12, rtol=0
            )
            np.testing.assert_allclose(
                new.average_policy, old.average_policy, atol=1e-12, rtol=0
            )
        assert new.nodes_visited == 2 * len(tree.player) * 32


@pytest.mark.parametrize("weight", ["uniform", "linear"])
@pytest.mark.parametrize("warm", [False, True])
def test_external_historical_trajectory_and_simultaneous_initialization(
    weight: Any,
    warm: bool,
) -> None:
    tree = audit.sentinel_tree()
    old = PostflopMCCFR(lambda rng: ArrayState(tree), Generator(PCG64(81)), weight)
    new = ControlledTrainer(
        tree, Generator(PCG64(81)), rules=Rules("signed", weight, weight)
    )
    if warm:
        exact_initial_expectation(old, tree)
        new.initialize_exact()
    for _ in range(30):
        old.step()
        new.step()
        assert old.iteration == new.iteration
        assert old.nodes_visited + old.warm_node_equivalent == new.nodes_visited
        assert old.rng.bit_generator.state == new.rng.bit_generator.state
        for key in old.rows:
            i = new.lookup[key]
            n = len(tree.actions[i])
            np.testing.assert_allclose(
                old.rows[key].regrets, new.regrets[i, :n], atol=1e-12, rtol=0
            )
            np.testing.assert_allclose(
                old.rows[key].strategy_sum, new.strategy_sum[i, :n], atol=1e-12, rtol=0
            )
    assert old.sampled_keys == new.sampled_keys
    if warm:
        assert new.initialization_visits == 2 * len(tree.player)
        with pytest.raises(ValueError, match="unused"):
            new.initialize_exact()


def test_all_sixteen_rules_are_legal_reproducible_and_charge_work() -> None:
    tree = audit.sentinel_tree()
    for traversal, clip, rw, aw in itertools.product(
        TRAVERSALS,
        REGRET_RULES,
        WEIGHTS,
        WEIGHTS,
    ):
        a = ControlledTrainer(
            tree, Generator(PCG64(91)), traversal=traversal, rules=Rules(clip, rw, aw)
        )
        b = ControlledTrainer(
            tree, Generator(PCG64(91)), traversal=traversal, rules=Rules(clip, rw, aw)
        )
        for trainer in (a, b):
            trainer.initialize_exact()
            before, last = trainer.advance_work(2000)
            assert before < 2000 <= trainer.nodes_visited == before + last
            assert 0 <= trainer.nodes_visited - 2000 < last <= 2 * len(tree.player)
            tree.validate_policy(trainer.current_policy)
            tree.validate_policy(trainer.average_policy)
            assert np.all(np.isfinite(trainer.regrets))
            if clip == "clipped":
                assert np.min(trainer.regrets) >= 0
        np.testing.assert_array_equal(a.regrets, b.regrets)
        np.testing.assert_array_equal(a.strategy_sum, b.strategy_sum)
        assert a.nodes_visited == b.nodes_visited
        if traversal == "full":
            assert not a.sampled_keys
            assert a.nodes_visited == 2 * len(tree.player) * a.iteration
        else:
            assert a.sampled_keys
        for threshold in (True, 1.5, 0, a.nodes_visited):
            with pytest.raises(ValueError):
                a.advance_work(threshold)  # type: ignore[arg-type]


def test_regret_and_average_time_weights_are_independent() -> None:
    tree = audit.sentinel_tree()
    policy = audit.sentinel_policy(tree, "positive")
    update = expected_pass(tree, policy, 0)
    regret = audit.dense_updates(tree, update.regrets)
    average = audit.dense_updates(tree, update.averages)
    for rw, aw in itertools.product(WEIGHTS, repeat=2):
        solver = ControlledTrainer(
            tree, Generator(PCG64(2)), rules=Rules("signed", rw, aw)
        )
        solver._apply(update, 0, 3)
        np.testing.assert_array_equal(
            solver.regrets, regret * (3 if rw == "linear" else 1)
        )
        np.testing.assert_array_equal(
            solver.strategy_sum, average * (3 if aw == "linear" else 1)
        )


def test_aggregate_shared_history_regret_before_clipping() -> None:
    tree = audit.sentinel_tree()
    policy = audit.sentinel_policy(tree, "positive")
    edge = tree.edges(policy)
    values, reaches = tree.values(edge), tree.reaches(edge)
    per_history_clips = np.zeros_like(tree.legal)
    for node in np.flatnonzero(tree.player == 0):
        info = tree.information[node]
        for column in range(len(tree.actions[info])):
            delta = (
                tree.chance_reach[node]
                * reaches[node, 1]
                * (values[tree.children[node, column]] - values[node])
            )
            per_history_clips[info, column] += max(0.0, delta)
    update = expected_pass(tree, policy, 0)
    correct = np.maximum(audit.dense_updates(tree, update.regrets), 0)
    assert np.max(np.abs(per_history_clips - correct)) > 0.01
    solver = ControlledTrainer(tree, Generator(PCG64(2)), rules=Rules("clipped"))
    solver._apply(update, 0, 1)
    np.testing.assert_array_equal(solver.regrets, correct)


def test_averaging_phase_and_chance_mass_are_not_regret_changes() -> None:
    tree = audit.sentinel_tree()
    conventions: tuple[tuple[Phase, Mass], ...] = (
        ("target_pass", "own_reach"),
        ("target_pass", "chance_own_reach"),
        ("opponent_pass", "chance_own_reach"),
    )
    trainers = [
        ControlledTrainer(
            tree,
            Generator(PCG64(11)),
            traversal="full",
            rules=Rules("clipped", "uniform", "linear"),
            average_phase=phase,
            average_mass=mass,
        )
        for phase, mass in conventions
    ]
    for solver in trainers:
        for _ in range(32):
            solver.step()
    for solver in trainers[1:]:
        np.testing.assert_array_equal(trainers[0].regrets, solver.regrets)
    # Perfect recall makes own realization reach constant across histories in a
    # row. Static chance sums only rescale that row and cancel on normalization.
    np.testing.assert_allclose(
        trainers[0].average_policy, trainers[1].average_policy, atol=1e-12, rtol=0
    )
    assert (
        np.max(np.abs(trainers[1].average_policy - trainers[2].average_policy)) > 1e-4
    )


def test_invalid_conventions_and_target_ownership_rejected_before_mutation() -> None:
    tree = audit.sentinel_tree()
    for kwargs in (
        {"traversal": "unknown"},
        {"average_phase": "target_pass"},
        {"average_mass": "own_reach"},
    ):
        with pytest.raises(ValueError):
            ControlledTrainer(tree, Generator(PCG64(1)), **kwargs)  # type: ignore[arg-type]
    for rules in (("wrong", "uniform", "uniform"), ("signed", "bad", "linear")):
        with pytest.raises(ValueError):
            Rules(*rules)  # type: ignore[arg-type]
    for target in (True, -1, 2):
        with pytest.raises(ValueError):
            expected_pass(tree, tree.normalize(tree.legal), target)
    solver = ControlledTrainer(tree, Generator(PCG64(2)))
    key = next(k for k, i in solver.lookup.items() if tree.owners[i] == 1)
    with pytest.raises(ValueError):
        solver._apply(Updates({key: np.ones(2)}, {}), 0, 1)
    assert not np.any(solver.regrets) and not np.any(solver.strategy_sum)


def test_array_state_respects_decisions_and_legal_columns() -> None:
    state = ArrayState(audit.sentinel_tree())
    assert state.chance and state.chance_probabilities == (0.1, 0.3, 0.6)
    for name in ("actor", "information", "payoff"):
        with pytest.raises(ValueError):
            getattr(state, name)
    with pytest.raises(ValueError):
        state.child(True)


@pytest.fixture
def config() -> dict[str, Any]:
    return json.loads((ROOT / audit.CONFIG).read_text())  # type: ignore[no-any-return]


@pytest.mark.parametrize("mutation", ["seeds", "weight", "budget", "scope", "inputs"])
def test_config_rejects_changed_selection_and_claim(
    config: dict[str, Any], mutation: str
) -> None:
    if mutation == "seeds":
        config["future_comparison"]["seeds"] = [20261301]
    elif mutation == "weight":
        config["future_comparison"]["regret_weight"] = ["linear"]
    elif mutation == "budget":
        config["future_comparison"]["node_work_checkpoints"][0] = True
    elif mutation == "scope":
        config["status"] = "agent_improved"
    else:
        config["input_sha256"].pop(audit.FULL)
    with pytest.raises(ValueError):
        audit.validate_config(config)


def test_real_pinned_work_grid_and_changed_input(config: dict[str, Any]) -> None:
    result = audit.evidence(ROOT, config)
    assert len(result["historical_work"]) == 30
    medium = [r for r in result["historical_work"] if r["spot_file"] == audit.SPOTS[1]]
    assert all(17.45 < r["full_over_sampled_work"] < 17.46 for r in medium)
    assert result["new_postflop_training"] is False
    config["input_sha256"][audit.FULL] = "0" * 64
    with pytest.raises(ArithmeticError, match="prerequisite"):
        audit.evidence(ROOT, config)


def test_receipt_replay_rejects_changed_counts_source_and_learning_claim(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real = source_provenance

    def software_source(*args: Any, **kwargs: Any) -> dict[str, Any]:
        return {
            **real(*args, **kwargs),
            "dirty": False,
            "git_commit": "software-fixture-not-research",
        }

    monkeypatch.setattr(audit, "source_provenance", software_source)
    output = tmp_path / "receipt.json"
    saved = audit.run(ROOT, ROOT / audit.CONFIG, output)
    assert audit.replay(ROOT, output) == saved
    with pytest.raises(FileExistsError):
        audit.run(ROOT, ROOT / audit.CONFIG, output)
    for change in (
        "count",
        "value",
        "source",
        "claim",
        "seconds",
        "typed_id",
        "grid",
        "flag_type",
        "count_type",
        "config",
    ):
        modified = copy.deepcopy(saved)
        if change == "count":
            modified["historical_work"][0]["sampled_node_work"] += 1
        elif change == "value":
            modified["sentinels"][0]["maximum_regret_error"] = 0.1
        elif change == "source":
            modified["source"]["sha256"] = {}
        elif change == "claim":
            modified["causal_strength_result"] = True
        elif change == "seconds":
            modified["seconds"] = -1
        elif change == "typed_id":
            modified["sentinels"][0]["target"] = False
        elif change == "flag_type":
            modified["new_postflop_training"] = 0
        elif change == "count_type":
            modified["historical_work"][0]["seed"] = float(
                modified["historical_work"][0]["seed"]
            )
        elif change == "config":
            modified["config"]["scope"] = "causal training results"
        else:
            modified["sentinels"].pop()
        output.write_text(json.dumps(modified))
        with pytest.raises(ArithmeticError):
            audit.replay(ROOT, output)
