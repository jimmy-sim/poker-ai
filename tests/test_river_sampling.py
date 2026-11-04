"""Exact finite expectations, physical card removal, privacy and resume semantics."""

from collections.abc import Callable, Iterator
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np
import pytest
from numpy.random import PCG64, Generator

from poker_ai.finite import FloatArray
from poker_ai.postflop.game import load_spot
from poker_ai.postflop.matrix import IndexedState, MatrixTree
from poker_ai.postflop.river_sampling import (
    RiverIntegratedMCCFR,
    integrated_external_updates,
    is_hidden_river,
)
from poker_ai.postflop.sampling import (
    PostflopMCCFR,
    Weighting,
    exact_initial_expectation,
    load_learning_checkpoint,
    save_learning_checkpoint,
)
from poker_ai.postflop.tree import SpotTree
from poker_ai.toy.games import ToyState
from poker_ai.training.mccfr import SampleState, Selector, Updates, external_updates

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class HiddenGame:
    """Two unobserved chance variables; optionally put river AFTER own decision.

    P(private=0)=1/4, P(river=1|private=0)=4/5, P(river=1|private=1)=2/5.
    Thus E[private+1]=7/4 and E[2*river-1]=0. The chance order cannot change
    the exact expected updates because neither player observes these variables.
    """

    private: int | None = None
    river: int | None = None
    first: int | None = None
    second: int | None = None
    late_river: bool = False

    @property
    def terminal(self) -> bool:
        return self.second is not None

    @property
    def chance(self) -> bool:
        return self.private is None or (
            self.river is None and (not self.late_river or self.first is not None)
        )

    @property
    def actor(self) -> int:
        return 0 if self.first is None else 1

    @property
    def actions(self) -> tuple[int, ...]:
        return () if self.terminal else (0, 1)

    @property
    def information(self) -> str:
        assert not self.chance and not self.terminal
        return "turn" if self.actor == 0 else f"reply/{self.first}"

    @property
    def chance_probabilities(self) -> tuple[float, ...]:
        assert self.chance
        if self.private is None:
            return (0.25, 0.75)
        return (0.2, 0.8) if self.private == 0 else (0.6, 0.4)

    @property
    def payoff(self) -> float:
        assert self.terminal and self.private is not None and self.river is not None
        return float(
            (self.private + 1) * (1 if self.first == self.second else -1)
            + (2 * self.river - 1) * (3 if self.first == 0 else -2)
        )

    def child(self, action: int) -> "HiddenGame":
        assert action in self.actions
        if self.private is None:
            return replace(self, private=action)
        if self.chance:
            return replace(self, river=action)
        if self.first is None:
            return replace(self, first=action)
        return replace(self, second=action)


def frozen_policy(key: str, actions: tuple[int, ...]) -> FloatArray:
    assert actions == (0, 1)
    return np.array([0.4, 0.6] if key == "turn" else [0.3, 0.7])


class NeedChoice(Exception):
    def __init__(self, probabilities: FloatArray) -> None:
        self.probabilities = probabilities.copy()


def enumerate_selector_expectation(run: Callable[[Selector], Updates]) -> Updates:
    """Enumerate every finite random choice tape, using its actual probability.

    This covers stochastic opponent choices, including distinct draws in hidden
    worlds sharing the same info set. It is exact enumeration, not a Monte Carlo
    tolerance test. Expected values below are independently derived closed forms.
    """
    pending: list[tuple[tuple[int, ...], float]] = [((), 1.0)]
    total = Updates({}, {})
    probability = 0.0
    while pending:
        tape, weight = pending.pop()
        position = 0

        def select(p: FloatArray, tape: tuple[int, ...] = tape) -> int:
            nonlocal position
            if position == len(tape):
                raise NeedChoice(p)
            choice = tape[position]
            position += 1
            return choice

        try:
            result = run(select)
        except NeedChoice as request:
            for i, p in enumerate(request.probabilities):
                if p > 0:
                    pending.append((tape + (i,), weight * float(p)))
            continue
        probability += weight
        for dest, source in (
            (total.regrets, result.regrets),
            (total.averages, result.averages),
        ):
            for key, value in source.items():
                dest.setdefault(key, np.zeros_like(value))[:] += weight * value
    assert probability == pytest.approx(1, abs=1e-13)
    return total


@pytest.mark.parametrize("late", [False, True])
@pytest.mark.parametrize("target", [0, 1])
@pytest.mark.parametrize("domain", ["none", "river", "all"])
def test_exact_expected_updates_equal_independent_closed_form(
    late: bool, target: int, domain: str
) -> None:
    root = HiddenGame(late_river=late)

    def integrate(s: SampleState) -> bool:
        assert isinstance(s, HiddenGame)
        return domain == "all" or (domain == "river" and s.private is not None)

    actual = enumerate_selector_expectation(
        lambda select: integrated_external_updates(
            root, target, frozen_policy, select, integrate
        )
    )
    # E[v0(a)]=[-.7,.7], E[v0]=.14 => target-0 regret [-.84,.56].
    # For player 1: advantages [-1.4*k,.6*k] at a=0, reversed at a=1,
    # with E[k]=7/4 and opponent reaches .4 and .6, respectively.
    regrets = (
        {"turn": [-0.84, 0.56]}
        if target == 0
        else {"reply/0": [-0.98, 0.42], "reply/1": [1.47, -0.63]}
    )
    averages = (
        {"reply/0": [0.3, 0.7], "reply/1": [0.3, 0.7]}
        if target == 0
        else {"turn": [0.4, 0.6]}
    )
    assert actual.regrets.keys() == regrets.keys()
    assert actual.averages.keys() == averages.keys()
    for key, expected in regrets.items():
        np.testing.assert_allclose(actual.regrets[key], expected, atol=1e-13, rtol=0)
    for key, expected in averages.items():
        np.testing.assert_allclose(actual.averages[key], expected, atol=1e-13, rtol=0)


@pytest.mark.parametrize(
    "target,ordinary_nodes,integrated_nodes", [(0, 7, 12), (1, 6, 10)]
)
def test_enumeration_charges_every_recursive_and_terminal_visit(
    target: int, ordinary_nodes: int, integrated_nodes: int
) -> None:
    def select(p: FloatArray) -> int:
        return int(p.argmax())

    ordinary = external_updates(HiddenGame(), target, frozen_policy, select)
    integrated = integrated_external_updates(
        HiddenGame(),
        target,
        frozen_policy,
        select,
        lambda s: isinstance(s, HiddenGame) and s.private is not None,
    )
    assert ordinary.visited == ordinary_nodes
    assert integrated.visited == integrated_nodes


@pytest.fixture(scope="module")
def low_tree() -> MatrixTree:
    return MatrixTree.build(
        SpotTree.build(load_spot(ROOT / "configs/learning-spots/dev_low_oop.json"))
    )


@pytest.mark.parametrize("target", [0, 1])
def test_physical_card_removal_and_nonuniform_joint_expectation(
    tmp_path: Path, target: int
) -> None:
    import json

    raw = json.loads((ROOT / "configs/learning-spots/dev_low_oop.json").read_text())
    raw["ranges"][0][0]["weight"] = 3
    raw["ranges"][1][0]["weight"] = 2
    raw["ranges"][1][1] = {"cards": ["Ah", "9d"], "weight": 5}
    path = tmp_path / "nonuniform.json"
    path.write_text(json.dumps(raw))
    source = SpotTree.build(load_spot(path))
    tree = MatrixTree.build(source)
    assert source.spot.joint == ((0, 0, 6 / 23), (0, 1, 15 / 23), (1, 0, 2 / 23))
    policy = np.zeros_like(tree.legal)
    policy[:, 0] = 1
    edges = tree.edges(policy)
    reach = tree.reaches(edges)
    values = tree.values(edges)
    expected_r, expected_a = np.zeros_like(policy), np.zeros_like(policy)
    own_nodes = np.flatnonzero(tree.player == target)
    opposite = np.flatnonzero(tree.player == 1 - target)
    cf = tree.chance_reach[own_nodes] * reach[own_nodes, 1 - target]
    delta = (values[tree.children[own_nodes]] - values[own_nodes, None]) * tree.valid[
        own_nodes
    ]
    np.add.at(
        expected_r,
        tree.information[own_nodes],
        cf[:, None] * delta * (1 if target == 0 else -1),
    )
    mass = tree.chance_reach[opposite] * reach[opposite, 1 - target]
    np.add.at(
        expected_a,
        tree.information[opposite],
        mass[:, None] * policy[tree.information[opposite]],
    )
    actual_r, actual_a = np.zeros_like(policy), np.zeros_like(policy)
    lookup = {key: i for i, key in enumerate(tree.keys)}
    root = IndexedState(tree)
    for first, second, probability in source.spot.joint:
        first_index = root.actions.index(first)
        second_index = root.child(first).actions.index(second)
        tape = iter([first_index, second_index])

        def select(p: FloatArray, tape: Iterator[int] = tape) -> int:
            return next(tape, int(p.argmax()))

        def pure(key: str, actions: tuple[int, ...]) -> FloatArray:
            return policy[lookup[key], : len(actions)]

        update = integrated_external_updates(
            root, target, pure, select, is_hidden_river
        )
        for dest, updates in ((actual_r, update.regrets), (actual_a, update.averages)):
            for key, value in updates.items():
                dest[lookup[key], : len(value)] += probability * value
    np.testing.assert_allclose(actual_r, expected_r, atol=1e-10, rtol=0)
    np.testing.assert_allclose(actual_a, expected_a, atol=1e-12, rtol=0)


def test_hidden_rivers_and_opponent_cards_never_change_root_policy_key(
    low_tree: MatrixTree,
) -> None:
    keys = []
    for second_choice in (0, 1):
        private_tape = iter([0, second_choice])
        root = IndexedState(low_tree)
        second = root.child(root.actions[0])
        river = second.child(second.actions[second_choice])
        assert isinstance(river, IndexedState) and len(river.actions) == 44
        root_keys = {river.child(a).information for a in river.actions}
        assert len(root_keys) == 1
        expected_key = root_keys.pop()
        count = 0

        def policy(
            key: str, actions: tuple[int, ...], root_key: str = expected_key
        ) -> FloatArray:
            nonlocal count
            info = low_tree.keys.index(key)
            assert low_tree.actions[info] == actions
            count += int(key == root_key)
            return np.full(len(actions), 1 / len(actions))

        def select(p: FloatArray, private_tape: Iterator[int] = private_tape) -> int:
            return next(private_tape, int(p.argmax()))

        integrated_external_updates(root, 0, policy, select, is_hidden_river)
        assert count == 44
        keys.append(expected_key)
    assert keys[0] == keys[1]


@pytest.mark.parametrize("weighting", ["uniform", "linear"])
@pytest.mark.parametrize("warm", [False, True])
def test_integrated_resume_is_byte_identical_and_bound_to_sampler(
    low_tree: MatrixTree, tmp_path: Path, weighting: Weighting, warm: bool
) -> None:
    def factory(rng: Generator) -> IndexedState:
        return IndexedState(low_tree)

    solver = RiverIntegratedMCCFR(factory, Generator(PCG64(31)), weighting)
    if warm:
        exact_initial_expectation(solver, low_tree)
    solver.epsilon = 0.25
    solver.train(8)
    path = tmp_path / "checkpoint.json"
    config = {
        "learning": {"sampling_weighting": weighting, "sampler": "river_integrated"}
    }
    save_learning_checkpoint(solver, path, config=config, provenance={"test": True})
    with pytest.raises(ValueError, match="sampler"):
        load_learning_checkpoint(path, factory, expected_config=config)
    resumed = load_learning_checkpoint(
        path, factory, expected_config=config, solver_class=RiverIntegratedMCCFR
    )
    solver.train(4)
    resumed.train(4)
    a, b = tmp_path / "a.json", tmp_path / "b.json"
    for item, output in ((solver, a), (resumed, b)):
        save_learning_checkpoint(item, output, config=config, provenance={"test": True})
    assert a.read_bytes() == b.read_bytes()
    assert (
        a.with_suffix(".visits.json").read_bytes()
        == b.with_suffix(".visits.json").read_bytes()
    )
    assert solver.sampled_keys == resumed.sampled_keys
    assert solver.warm_node_equivalent == resumed.warm_node_equivalent
    assert resumed.sampler == "river_integrated" and resumed.epsilon == 0.25


def test_integrated_solver_rejects_wrong_domain_before_updating(
    low_tree: MatrixTree,
) -> None:
    toy = RiverIntegratedMCCFR(lambda rng: ToyState("kuhn"), Generator(PCG64(1)))
    fake_flop = replace(
        low_tree,
        source=replace(
            low_tree.source,
            spot=replace(low_tree.source.spot, board=low_tree.source.spot.board[:3]),
        ),
    )
    flop = RiverIntegratedMCCFR(
        lambda rng: IndexedState(fake_flop), Generator(PCG64(1))
    )
    for solver in (toy, flop):
        with pytest.raises(ValueError, match="turn-only"):
            solver.step()
        assert not solver.rows and solver.iteration == solver.nodes_visited == 0


def test_sampler_config_required_on_save(low_tree: MatrixTree, tmp_path: Path) -> None:
    solver = RiverIntegratedMCCFR(
        lambda rng: IndexedState(low_tree), Generator(PCG64(1))
    )
    path = tmp_path / "missing-mode.json"
    with pytest.raises(ValueError, match="sampler"):
        save_learning_checkpoint(solver, path, config={"learning": {}}, provenance={})
    assert not path.exists()


@pytest.mark.parametrize("late", [False, True])
@pytest.mark.parametrize("target", [0, 1])
def test_no_integrated_edges_preserves_ordinary_update_and_rng(
    late: bool, target: int
) -> None:
    a, b = Generator(PCG64(93)), Generator(PCG64(93))
    root = HiddenGame(late_river=late)
    ordinary = external_updates(
        root, target, frozen_policy, lambda p: int(a.choice(len(p), p=p))
    )
    control = integrated_external_updates(
        root,
        target,
        frozen_policy,
        lambda p: int(b.choice(len(p), p=p)),
        lambda state: False,
    )
    assert ordinary.visited == control.visited
    assert a.bit_generator.state == b.bit_generator.state
    for x, y in (
        (ordinary.regrets, control.regrets),
        (ordinary.averages, control.averages),
    ):
        assert x.keys() == y.keys()
        for key in x:
            np.testing.assert_array_equal(x[key], y[key])


@pytest.mark.parametrize(
    "probabilities", [(float("nan"), 0.5), (-0.1, 1.1), (0.2, 0.2), (1.0,)]
)
def test_invalid_chance_distribution_rejected(probabilities: tuple[float, ...]) -> None:
    class InvalidChance(HiddenGame):
        @property
        def chance_probabilities(self) -> tuple[float, ...]:
            return probabilities

    def no_selection(p: FloatArray) -> int:
        raise AssertionError("invalid chance should fail before selection")

    with pytest.raises(ValueError, match="chance distribution"):
        integrated_external_updates(
            InvalidChance(), 0, frozen_policy, no_selection, lambda s: True
        )


def test_zero_probability_integrated_world_not_traversed() -> None:
    class ZeroWorld(HiddenGame):
        @property
        def chance_probabilities(self) -> tuple[float, ...]:
            return (1.0, 0.0) if self.private is None else super().chance_probabilities

        def child(self, action: int) -> HiddenGame:
            assert not (self.private is None and action == 1)
            return super().child(action)

    result = integrated_external_updates(
        ZeroWorld(), 0, frozen_policy, lambda p: int(p.argmax()), lambda s: True
    )
    assert result.visited == 12


@pytest.mark.parametrize("damage", ["sampler", "missing", "extra", "core_method"])
def test_integrated_checkpoint_metadata_fails_closed(
    low_tree: MatrixTree, tmp_path: Path, damage: str
) -> None:
    import hashlib
    import json

    def factory(rng: Generator) -> IndexedState:
        return IndexedState(low_tree)

    solver = RiverIntegratedMCCFR(factory, Generator(PCG64(5)))
    solver.train(2)
    config = {"learning": {"sampler": "river_integrated"}}
    path = tmp_path / "own.json"
    save_learning_checkpoint(solver, path, config=config, provenance={})
    metadata_path = path.with_suffix(".visits.json")
    metadata = json.loads(metadata_path.read_text())
    if damage == "sampler":
        metadata["sampler"] = "external"
    elif damage == "missing":
        del metadata["sampler"]
    elif damage == "extra":
        metadata["unknown"] = 1
    else:
        core = json.loads(path.read_text())
        core["method"] = "outcome"
        path.write_text(json.dumps(core))
        metadata["core_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    metadata_path.write_text(json.dumps(metadata))
    with pytest.raises(ValueError):
        load_learning_checkpoint(
            path, factory, expected_config=config, solver_class=RiverIntegratedMCCFR
        )


def test_legacy_checkpoint_keeps_v1_and_rejects_integrated_loader(
    low_tree: MatrixTree, tmp_path: Path
) -> None:
    import json

    def factory(rng: Generator) -> IndexedState:
        return IndexedState(low_tree)

    solver = PostflopMCCFR(factory, Generator(PCG64(11)))
    solver.train(4)
    path = tmp_path / "legacy.json"
    config: dict[str, dict[str, str]] = {"learning": {}}
    save_learning_checkpoint(solver, path, config=config, provenance={})
    metadata = json.loads(path.with_suffix(".visits.json").read_text())
    assert metadata["format"] == "poker-ai-own-postflop-visits-v1"
    assert "sampler" not in metadata
    restored = load_learning_checkpoint(path, factory, expected_config=config)
    assert type(restored) is PostflopMCCFR
    with pytest.raises(ValueError, match="sampler"):
        load_learning_checkpoint(
            path, factory, expected_config=config, solver_class=RiverIntegratedMCCFR
        )
