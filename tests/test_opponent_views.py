"""Own opponent-information views; independent tiny-game terminal arithmetic."""

import importlib.util
import itertools
from collections import defaultdict
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from poker_ai.abstraction.model import CardAbstraction
from poker_ai.evaluation.opponent_view_correctness import analytic_proof, signal_game
from poker_ai.finite import ArrayTree, FloatArray, IntArray
from poker_ai.postflop.controlled_training import ControlledTrainer
from poker_ai.postflop.game import load_spot
from poker_ai.postflop.matrix import MatrixTree
from poker_ai.postflop.opponent_views import (
    ARRAYS,
    bind_policy,
    build_view,
    compose,
    tree_digest,
)
from poker_ai.postflop.range_protocol import build_representation_control
from poker_ai.postflop.reply_trace import require_recall
from poker_ai.postflop.tree import SpotTree
from poker_ai.toy.analysis import best_response, evaluate
from poker_ai.training.holdem import exact_information

ROOT = Path(__file__).resolve().parents[1]


def fixture(risk_target: int = 0) -> tuple[ArrayTree, ArrayTree, IntArray]:
    # Two equally likely private signals. Safe pays0. Risk gives the opponent
    # A/B, paying target +1/-1 at signal0 and -1/+1 at signal1. Both exact
    # players legally observe their own correlated signal. Coarse views forget it.
    children = np.zeros((11, 2), dtype=np.int64)
    children[0], children[1], children[2] = (1, 2), (3, 5), (4, 6)
    children[5], children[6] = (7, 8), (9, 10)
    valid = np.zeros((11, 2), dtype=np.bool_)
    valid[[0, 1, 2, 5, 6]] = True
    player = np.array(
        [
            -1,
            risk_target,
            risk_target,
            -2,
            -2,
            1 - risk_target,
            1 - risk_target,
            -2,
            -2,
            -2,
            -2,
        ],
        dtype=np.int64,
    )
    chance = np.zeros((11, 2))
    chance[0] = [0.5, 0.5]
    sign = 1 if risk_target == 0 else -1
    fine = ArrayTree(
        children,
        valid,
        player,
        np.array([-1, 0, 1, -1, -1, 2, 3, -1, -1, -1, -1]),
        ("risk/signal0", "risk/signal1", "reply/signal0", "reply/signal1"),
        ((0, 1),) * 4,
        np.array([risk_target] * 2 + [1 - risk_target] * 2),
        np.ones((4, 2)),
        chance,
        np.array([1.0] + [0.5] * 10),
        sign * np.array([0.0, 0, 0, 0, 0, 0, 0, 1, -1, -1, 1]),
        (np.array([0]), np.array([1, 2]), np.array([5, 6])),
    )
    mapping = np.array([0, 0, 1, 1], dtype=np.int64)
    information = fine.information.copy()
    active = fine.player >= 0
    information[active] = mapping[information[active]]
    coarse = replace(
        fine,
        information=information,
        keys=("risk/shared", "reply/shared"),
        actions=((0, 1),) * 2,
        owners=np.array([risk_target, 1 - risk_target]),
        legal=np.ones((2, 2)),
    )
    return fine, coarse, mapping


def scalar_value(fine_policy: FloatArray, risk_target: int) -> float:
    # Independent four terminal branches; no ArrayTree traversal or BR helper.
    a, b, c, d = fine_policy
    target_value = 0.5 * a[1] * (c[0] - c[1]) + 0.5 * b[1] * (-d[0] + d[1])
    return float(target_value if risk_target == 0 else -target_value)


def pure_reply(
    tree: ArrayTree,
    policy: FloatArray,
    fine_to_tree: IntArray,
    target: int,
    risk_target: int,
) -> float:
    infos = np.flatnonzero(tree.owners == target)
    values = []
    for choices in itertools.product((0, 1), repeat=len(infos)):
        candidate = policy.copy()
        for info, column in zip(infos, choices, strict=True):
            candidate[info] = 0
            candidate[info, column] = 1
        value = scalar_value(candidate[fine_to_tree], risk_target)
        values.append(value if target == 0 else -value)
    return max(values)


@pytest.mark.parametrize("risk_target", [0, 1])
def test_coarse_equilibrium_can_be_unsafe_against_finer_legal_opponent(
    risk_target: int,
) -> None:
    fine, coarse, mapping = fixture(risk_target)
    unsafe = np.array([[0.0, 1.0], [0.5, 0.5]])
    assert evaluate(coarse, unsafe).exploitability == 0
    assert evaluate(fine, unsafe[mapping]).exploitability == 0.5
    for target in (0, 1):
        assert best_response(coarse, unsafe, target) == pure_reply(
            coarse, unsafe, mapping, target, risk_target
        )
        assert best_response(fine, unsafe[mapping], target) == pure_reply(
            fine, unsafe[mapping], np.arange(4), target, risk_target
        )
    mixed = build_view(fine, coarse, mapping, risk_target)
    policy = mixed.tree.normalize(mixed.tree.legal)
    policy[mixed.coarse_own_to_view[0]] = [0, 1]
    for target in (0, 1):
        assert best_response(mixed.tree, policy, target) == pure_reply(
            mixed.tree, policy, mixed.fine_to_view, target, risk_target
        )
    assert best_response(mixed.tree, policy, 1 - risk_target) == 1
    # The same coarse space contains Safe/uniform, a fine-game equilibrium.
    safe = np.array([[1.0, 0.0], [0.5, 0.5]])
    assert scalar_value(safe[mapping], risk_target) == 0
    assert evaluate(fine, safe[mapping]).exploitability == 0


@pytest.mark.parametrize("risk_target", [0, 1])
def test_compose_only_the_two_coarse_owned_roles_and_discard_opponent_rows(
    risk_target: int,
) -> None:
    fine, coarse, mapping = fixture(risk_target)
    desired = np.array([[1.0, 0.0], [0.5, 0.5]])
    bundles = []
    original = []
    for target in (0, 1):
        view = build_view(fine, coarse, mapping, target)
        policy = view.tree.normalize(view.tree.legal)
        policy[view.tree.owners != target] = [0, 1]
        owned = coarse.owners == target
        policy[view.coarse_own_to_view[owned]] = desired[owned]
        original.append(policy.copy())
        bundles.append((view, bind_policy(view, policy)))
    result = compose(coarse, bundles[0], bundles[1])
    np.testing.assert_array_equal(result, desired)
    assert evaluate(fine, result[mapping]).exploitability == 0
    for (_, bound), before in zip(bundles, original, strict=True):
        np.testing.assert_array_equal(bound.values, before)


@pytest.mark.parametrize("target", [0, 1])
def test_information_mapping_is_exactly_coarse_for_own_and_fine_for_other(
    target: int,
) -> None:
    fine, coarse, mapping = fixture()
    view = build_view(fine, coarse, mapping, target)
    for i, j in itertools.product(range(4), repeat=2):
        if fine.owners[i] != fine.owners[j]:
            assert view.fine_to_view[i] != view.fine_to_view[j]
        else:
            expected = mapping[i] == mapping[j] if fine.owners[i] == target else i == j
            assert (view.fine_to_view[i] == view.fine_to_view[j]) == expected
    require_recall(view.tree)
    # No actor's row is ever split on another hidden world or unrevealed future:
    # mapping factors only through its supplied legal fine/coarse information ID.
    decision = fine.player >= 0
    np.testing.assert_array_equal(
        view.tree.information[decision], view.fine_to_view[fine.information[decision]]
    )


def test_identity_limit_preserves_every_edge_value_and_reply() -> None:
    fine, _, _ = fixture()
    uniform = fine.normalize(fine.legal)
    for target in (0, 1):
        view = build_view(fine, fine, np.arange(4, dtype=np.int64), target)
        translated = uniform.copy()
        np.testing.assert_array_equal(view.fine_to_view, np.arange(4))
        np.testing.assert_array_equal(view.tree.edges(translated), fine.edges(uniform))
        np.testing.assert_array_equal(
            view.tree.values(view.tree.edges(translated)),
            fine.values(fine.edges(uniform)),
        )
        for responding in (0, 1):
            assert best_response(view.tree, translated, responding) == best_response(
                fine, uniform, responding
            )


def test_factory_and_bindings_own_immutable_copies_without_source_mutation() -> None:
    fine, coarse, mapping = fixture()
    before = (tree_digest(fine), tree_digest(coarse), mapping.copy())
    writable = {name: getattr(fine, name).flags.writeable for name in ARRAYS}
    view = build_view(fine, coarse, mapping, 0)
    assert (tree_digest(fine), tree_digest(coarse)) == before[:2]
    np.testing.assert_array_equal(mapping, before[2])
    for name in ARRAYS:
        assert getattr(fine, name).flags.writeable == writable[name]
        assert not getattr(view.tree, name).flags.writeable
        if name not in ("information", "owners", "legal"):
            np.testing.assert_array_equal(getattr(view.tree, name), getattr(fine, name))
            assert not np.shares_memory(getattr(view.tree, name), getattr(fine, name))
    for level in view.tree.levels:
        assert not level.flags.writeable
    assert not view.fine_to_view.flags.writeable
    assert not view.coarse_own_to_view.flags.writeable
    policy = fine.normalize(fine.legal)[[0, 2, 3]]
    bound = bind_policy(view, policy)
    policy[0] = [1, 0]
    assert not bound.values.flags.writeable
    np.testing.assert_array_equal(bound.values[0], [0.5, 0.5])


@pytest.mark.parametrize(
    "bad",
    [
        "seat_bool",
        "seat",
        "mapping_type",
        "mapping_range",
        "menu",
        "owner",
        "chance",
        "payoff",
        "nonfinite",
        "key",
        "legal",
    ],
)
def test_invalid_or_different_game_views_rejected(bad: str) -> None:
    fine, coarse, mapping = fixture()
    target: Any = 0
    if bad == "seat_bool":
        target = False
    elif bad == "seat":
        target = 2
    elif bad == "mapping_type":
        mapping = mapping.astype(float)
    elif bad == "mapping_range":
        mapping[0] = 3
    elif bad == "menu":
        coarse = replace(coarse, actions=((1, 0), (0, 1)))
    elif bad == "owner":
        coarse = replace(coarse, owners=1 - coarse.owners)
    elif bad == "chance":
        coarse = replace(coarse, chance_edges=coarse.chance_edges * 0.5)
    elif bad == "payoff":
        coarse = replace(coarse, terminal_values=coarse.terminal_values + 1)
    elif bad == "nonfinite":
        values = fine.terminal_values.copy()
        values[-1] = np.inf
        fine, coarse = (
            replace(fine, terminal_values=values),
            replace(coarse, terminal_values=values),
        )
    elif bad == "key":
        coarse = replace(coarse, keys=("same", "same"))
    else:
        coarse = replace(coarse, legal=coarse.legal * 0.5)
    with pytest.raises(ValueError):
        build_view(fine, coarse, mapping, target)


def test_policy_role_context_and_mutation_bindings_rejected() -> None:
    fine, coarse, mapping = fixture()
    a, b = (build_view(fine, coarse, mapping, seat) for seat in (0, 1))
    pa, pb = (bind_policy(v, v.tree.normalize(v.tree.legal)) for v in (a, b))
    with pytest.raises(ValueError):
        compose(coarse, (a, pb), (b, pa))
    with pytest.raises(ValueError):
        compose(coarse, (b, pb), (a, pa))
    altered = replace(coarse, terminal_values=coarse.terminal_values * 2)
    with pytest.raises(ValueError):
        compose(altered, (a, pa), (b, pb))
    changed = b.coarse_own_to_view.copy()
    changed[1] = 0
    with pytest.raises(ValueError):
        bind_policy(replace(b, coarse_own_to_view=changed), pb.values)
    pa.values.setflags(write=True)
    pa.values[0] = [1, 0]
    with pytest.raises(ValueError):
        compose(coarse, (a, pa), (b, pb))


def test_invalid_policy_not_silently_normalized() -> None:
    fine, coarse, mapping = fixture()
    view = build_view(fine, coarse, mapping, 0)
    policy = view.tree.normalize(view.tree.legal)
    policy[0] = [1, 1]
    with pytest.raises(ValueError):
        bind_policy(view, policy)
    policy[0] = [float("nan"), 0]
    with pytest.raises(ValueError):
        bind_policy(view, policy)


def test_view_build_does_not_change_charged_exact_initialization() -> None:
    fine, coarse, mapping = fixture()
    for target in (0, 1):
        view = build_view(fine, coarse, mapping, target)
        trainer = ControlledTrainer(view.tree, np.random.default_rng(7))
        trainer.initialize_exact()
        assert (
            trainer.initialization_visits
            == trainer.nodes_visited
            == 2 * len(fine.player)
        )
        assert trainer.iteration == 1
    # A future paired arm must charge two initializations, not one shared warmup.
    assert 2 * (2 * len(fine.player)) == 44


@pytest.mark.parametrize("kind", ["depth", "own_history"])
def test_equal_depth_and_own_recall_failures_are_rejected(kind: str) -> None:
    fine, _, _ = fixture()
    player = fine.player.copy()
    player[[5, 6]] = 0
    fine = replace(fine, player=player, owners=np.zeros(4, dtype=np.int64))
    require_recall(fine)
    # Identical menus and owner: both failures must reach the recall check.
    mapping = np.array(
        [0, 0, 0, 0] if kind == "depth" else [0, 1, 2, 2], dtype=np.int64
    )
    information = fine.information.copy()
    active = fine.player >= 0
    information[active] = mapping[information[active]]
    count = int(mapping.max()) + 1
    coarse = replace(
        fine,
        information=information,
        keys=tuple(f"merged/{i}" for i in range(count)),
        actions=((0, 1),) * count,
        owners=np.zeros(count, dtype=np.int64),
        legal=np.ones((count, 2)),
    )
    with pytest.raises(ValueError, match="equal-depth perfect recall"):
        build_view(fine, coarse, mapping, 0)


@pytest.mark.parametrize("name", ["dev_low_oop", "dev_medium_oop"])
def test_known_poker_views_preserve_game_and_every_hidden_future_information_row(
    name: str,
) -> None:
    model = CardAbstraction.load(ROOT / "results/card-models/potential-8.json")
    source = SpotTree.build(load_spot(ROOT / f"configs/learning-spots/{name}.json"))
    fine = MatrixTree.build(source)
    coarse = build_representation_control(source, "texture_range_q8_b8", model)
    mapping = coarse.exact_to_abstract
    originals = (tree_digest(fine), tree_digest(coarse))
    coarse_policy = coarse.normalize(coarse.legal)
    for target in (0, 1):
        view = build_view(fine, coarse, mapping, target)
        require_recall(view.tree)
        own = fine.owners == target
        assert len(np.unique(view.fine_to_view[own])) == int(
            np.count_nonzero(coarse.owners == target)
        )
        assert len(np.unique(view.fine_to_view[~own])) == int(np.count_nonzero(~own))
        policy = np.zeros_like(view.tree.legal)
        for info, group in enumerate(view.fine_to_view):
            policy[group] = coarse_policy[mapping[info]]
        np.testing.assert_array_equal(
            view.tree.edges(policy), coarse.edges(coarse_policy)
        )
        np.testing.assert_array_equal(
            view.tree.values(view.tree.edges(policy)),
            coarse.values(coarse.edges(coarse_policy)),
        )
        assert best_response(view.tree, policy, target) == best_response(
            coarse, coarse_policy, target
        )
        keys: dict[tuple[int, str], str] = {}
        hidden: dict[tuple[int, str], set[int | None]] = defaultdict(set)
        future: dict[tuple[int, str], set[tuple[int, ...]]] = defaultdict(set)
        for raw in np.flatnonzero(fine.player >= 0):
            node = int(raw)
            state = source.states[node]
            assert state.dealer is not None
            actor = state.actor
            obs = state.dealer.observe(actor)
            key = (actor, exact_information(obs))
            current = view.tree.keys[int(view.tree.information[node])]
            assert keys.setdefault(key, current) == current
            hidden[key].add(state.second if actor == 0 else state.first)
            if obs.street.name == "TURN":
                future[key].add(state.future)
        assert any(len(values) > 1 for values in hidden.values())
        assert any(len(values) > 1 for values in future.values())
    assert (tree_digest(fine), tree_digest(coarse)) == originals


def test_additive_module_does_not_break_the_published_cached_browser() -> None:
    # The old data/source receipt remains valid; it is NOT a new training admission.
    spec = importlib.util.spec_from_file_location(
        "cached_own_decisions", ROOT / "scripts/inspect_private_prefix_decisions.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    profiles = module.load(ROOT, ROOT / "results/private-prefix/decisions")
    assert len(profiles) == 9


def test_command_fixture_matches_independent_terminal_math_without_admission() -> None:
    for target in (0, 1):
        expected = fixture(target)
        actual = signal_game(target)
        assert tree_digest(actual[0]) == tree_digest(expected[0])
        assert tree_digest(actual[1]) == tree_digest(expected[1])
        np.testing.assert_array_equal(actual[2], expected[2])
    rows = analytic_proof()
    assert [r["risk_target"] for r in rows] == [0, 1]
    assert all(
        r["coarse_unsafe_exploitability"] == 0
        and r["fine_unsafe_exploitability"] == 0.5
        and r["fine_analytic_safe_exploitability"] == 0
        and r["long_run_admitted"] is False
        for r in rows
    )
