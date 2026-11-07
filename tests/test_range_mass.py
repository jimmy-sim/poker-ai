"""Static prior masses, privacy/context guards and structural encoder contract."""

import itertools
import json
import subprocess
import sys
from dataclasses import FrozenInstanceError, replace
from fractions import Fraction
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from poker_ai.abstraction.made_category import MadeCategoryAbstraction
from poker_ai.abstraction.model import CardAbstraction
from poker_ai.abstraction.range_mass import (
    RangeContext,
    RangeMassAbstraction,
    RangePrior,
    mass_bin,
    river_mass,
)
from poker_ai.cards import Deck, parse_card
from poker_ai.engine import Action, ActionKind, new_hand
from poker_ai.postflop.game import SpotState, load_spot
from poker_ai.postflop.matrix import MatrixTree, observation_key, recall_violations
from poker_ai.postflop.range_protocol import (
    CANDIDATE,
    build_representation_control,
    range_context,
)
from poker_ai.postflop.tree import SpotTree

ROOT = Path(__file__).resolve().parents[1]


def cards(text: str) -> tuple[int, ...]:
    return tuple(parse_card(c) for c in text.split())


def prior(*entries: tuple[str, int | float]) -> RangePrior:
    return RangePrior.create((cards(c), w) for c, w in entries)


def test_exact_blocker_mass_and_weighted_relative_outcomes() -> None:
    p = prior(("Kh Qh", 1), ("9c 9d", 1))
    a = river_mass(cards("Tc Td"), cards("Ts 9s 4d 2h 9h"), p)
    b = river_mass(cards("Tc Td"), cards("Ts 9s 4d 2h 9d"), p)
    assert a.masses == (Fraction(0), Fraction(1, 2), Fraction(0), Fraction(1, 2))
    assert b.masses == (Fraction(1, 2), Fraction(0), Fraction(0), Fraction(1, 2))
    assert a.bins == (0, 4, 0, 4) and b.bins == (4, 0, 0, 4)
    assert a.conditional_equity == Fraction(1, 2) and b.conditional_equity == 1
    weighted = river_mass(
        cards("Tc Td"), cards("Ts 9s 4d 2h 9h"), prior(("Kh Qh", 1), ("9c 9d", 2))
    )
    assert weighted.masses == (Fraction(0), Fraction(2, 3), Fraction(0), Fraction(1, 3))
    assert weighted.bins == (0, 5, 0, 2)
    assert sum(weighted.masses) == 1
    assert river_mass(cards("Tc Td"), cards("Ts 9s 4d 2h Kd"), p).bins == (0, 0, 0, 7)
    assert river_mass(cards("Tc Td"), cards("Ts 9s 4d 2h Jd"), p).bins == (0, 4, 0, 4)


def test_ties_and_decimal_weights_are_exact() -> None:
    p = prior(("5h 6h", 1), ("Ac 2d", 1))
    result = river_mass(cards("3d 4d"), cards("Ac Kc Qc Jc Tc"), p)
    assert result.masses == (Fraction(1, 2), Fraction(0), Fraction(1, 2), Fraction(0))
    assert result.conditional_equity == Fraction(1, 2)
    decimal = prior(("As Js", 0.1), ("Kh Qh", 0.2), ("9c 9d", 0.3))
    assert set(decimal.masses) == {Fraction(1, 6), Fraction(1, 3), Fraction(1, 2)}
    assert sum(decimal.masses) == 1


@pytest.mark.parametrize(
    "p,expected",
    [
        (Fraction(0), 0),
        (Fraction(1, 8) - Fraction(1, 10**100), 0),
        (Fraction(1, 8), 1),
        (Fraction(7, 8), 7),
        (Fraction(1), 7),
    ],
)
def test_exact_interval_edges(p: Fraction, expected: int) -> None:
    assert mass_bin(p) == expected


@pytest.mark.parametrize("weight", [0, -1, float("nan"), float("inf"), True])
def test_invalid_prior_weights(weight: Any) -> None:
    with pytest.raises((ValueError, TypeError)):
        prior(("As Js", weight))


def test_invalid_cards_duplicates_empty_ranges_and_all_blocked() -> None:
    bad_entries: list[Any] = [
        [],
        [(cards("As Js"), 1), (cards("Js As"), 2)],
        [((0, 0), 1)],
        [((0, True), 1)],
        [((0, 52), 1)],
        [((0, 1, 2), 1)],
    ]
    for entries in bad_entries:
        with pytest.raises((ValueError, TypeError)):
            RangePrior.create(entries)
    with pytest.raises(ValueError, match="compatible"):
        river_mass(cards("Tc Td"), cards("Ts 9s 4d 2h 9d"), prior(("9c 9d", 1)))
    with pytest.raises(ValueError):
        river_mass(cards("Tc Td"), cards("Ts 9s 4d 2h"), prior(("9c 9d", 1)))
    with pytest.raises(ValueError):
        mass_bin(Fraction(-1, 8))
    with pytest.raises(ValueError):
        mass_bin(Fraction(9, 8))


def test_prior_order_scaling_context_binding_and_immutability() -> None:
    a = prior(("Kh Qh", 1), ("9c 9d", 2))
    b = prior(("9d 9c", 20), ("Qh Kh", 10))
    assert a == b
    context = RangeContext((a, b))
    same = RangeContext((b, a))
    assert context.identifier == same.identifier
    changed = RangeContext((a, prior(("Kh Qh", 1), ("9c 9d", 1))))
    assert context.identifier != changed.identifier
    with pytest.raises(FrozenInstanceError):
        mutable: Any = context
        mutable.priors = (b, b)
    with pytest.raises(FrozenInstanceError):
        mutable = a
        mutable.masses = (Fraction(1),)


def test_whole_input_suit_symmetry_and_card_order() -> None:
    hole, board = cards("Tc Td"), cards("Ts 9s 4d 2h 9d")
    expected = river_mass(hole, board, prior(("Kh Qh", 1), ("9c 9d", 2)))
    for suits in itertools.permutations(range(4)):

        def rename(
            xs: tuple[int, ...], mapping: tuple[int, ...] = suits
        ) -> tuple[int, ...]:
            return tuple(4 * (c // 4) + mapping[c % 4] for c in xs)

        p = RangePrior.create(
            [(rename(cards("Kh Qh")), 1), (rename(cards("9c 9d")), 2)]
        )
        assert river_mass(rename(hole), rename(board), p) == expected
    assert (
        river_mass(
            hole[::-1],
            tuple(reversed(board[:3])) + board[3:],
            prior(("Kh Qh", 1), ("9c 9d", 2)),
        )
        == expected
    )


@pytest.fixture(scope="module")
def base_model() -> CardAbstraction:
    return CardAbstraction.load(ROOT / "results/card-models/potential-8.json")


@pytest.fixture(scope="module")
def medium(base_model: CardAbstraction) -> tuple[SpotTree, RangeMassAbstraction]:
    source = SpotTree.build(
        load_spot(ROOT / "configs/learning-spots/dev_medium_oop.json")
    )
    return source, RangeMassAbstraction(base_model, range_context(source.spot))


def retained_observations(
    source: SpotTree, seat: int, row: int, rivers: tuple[str, str]
) -> list[Any]:
    r = json.loads((ROOT / "results/river-distinctions/diagnosis.json").read_text())
    case = next(
        c
        for c in r["cases"]
        if c["spot"] == "dev_medium_oop" and c["representation"] == "texture_made_b8"
    )
    panel = next(
        p for p in case["responses"][seat]["panels"] if p["prefix"] == "exact_prefix"
    )
    group = next(g for g in panel["top_groups"] if g["abstract_info"] == row)
    result = []
    for river in rivers:
        example = next(e for e in group["examples"] if e["board"][-1] == river)
        state = source.states[source.representatives[example["exact_info"]]]
        assert state.dealer is not None
        result.append(state.dealer.observe(seat))
    return result


@pytest.mark.parametrize("row,rivers", [(1089, ("9h", "9d")), (1251, ("Kd", "Jd"))])
def test_splits_published_blocker_and_relative_strength_examples(
    medium: tuple[SpotTree, RangeMassAbstraction],
    base_model: CardAbstraction,
    row: int,
    rivers: tuple[str, str],
) -> None:
    source, encoder = medium
    obs = retained_observations(source, 0, row, rivers)
    old = MadeCategoryAbstraction(base_model.models, base_model.config)
    assert observation_key(obs[0], "texture_b8", old) == observation_key(
        obs[1], "texture_b8", old
    )
    assert observation_key(obs[0], "texture_b8", encoder) != observation_key(
        obs[1], "texture_b8", encoder
    )
    for o in obs:
        assert json.loads(encoder.information(o))[2] == old.information(o)


def test_known_static_prior_limitation_is_retained(
    medium: tuple[SpotTree, RangeMassAbstraction],
) -> None:
    source, encoder = medium
    a, b = retained_observations(source, 1, 954, ("Qd", "Qh"))
    # Same fixed prior masses do not capture different betting-conditioned weights.
    assert encoder.information(a) == encoder.information(b)
    assert observation_key(a, "texture_b8", encoder) == observation_key(
        b, "texture_b8", encoder
    )


def test_no_range_feature_before_river_and_actual_hidden_invariance(
    base_model: CardAbstraction, monkeypatch: pytest.MonkeyPatch
) -> None:
    import poker_ai.abstraction.range_mass as module

    spot = load_spot(ROOT / "configs/learning-spots/dev_medium_oop.json")
    encoder = RangeMassAbstraction(base_model, range_context(spot))
    first = SpotState(spot).child(0).child(0)
    second = SpotState(spot).child(0).child(1)
    worlds = (
        first.child(parse_card("9h")),
        first.child(parse_card("3c")),
        second.child(parse_card("9h")),
    )
    observations = []
    for state in worlds:
        assert state.dealer is not None
        observations.append(state.dealer.observe(0))
    assert len({encoder.information(o) for o in observations}) == 1
    river_views = []
    for state in (worlds[0], worlds[2]):
        state = state.child(1).child(1)
        assert state.dealer is not None
        river_views.append(state.dealer.observe(0))
    assert encoder.information(river_views[0]) == encoder.information(river_views[1])

    def forbidden(*a: Any, **k: Any) -> Any:
        raise AssertionError("range feature requested before river")

    monkeypatch.setattr(module, "river_mass", forbidden)
    prefix = cards("Qh As Kh Js 2c Ts 9s 4d 2d 2h 2s 9h")
    hand = new_hand(
        (200, 200), Deck(prefix + tuple(c for c in range(52) if c not in prefix))
    )
    early = [hand.observe(0)]
    hand = hand.apply(Action(ActionKind.CALL)).apply(Action(ActionKind.CHECK))
    early.append(hand.observe(1))
    hand = hand.apply(Action(ActionKind.CHECK)).apply(Action(ActionKind.CHECK))
    early.append(hand.observe(1))
    for o in early:
        assert json.loads(encoder.information(o))[3] == []


def test_context_separation_view_guards_and_serialization(
    medium: tuple[SpotTree, RangeMassAbstraction],
    base_model: CardAbstraction,
    tmp_path: Path,
) -> None:
    source, encoder = medium
    o = retained_observations(source, 0, 1089, ("9h", "9d"))[0]
    old = encoder.range_context
    p = old.priors[1]
    other = RangePrior.create([(p.combos[0], 1), (p.combos[1], 3)])
    changed = RangeMassAbstraction(base_model, RangeContext((old.priors[0], other)))
    assert encoder.information(o) != changed.information(o)
    own = old.priors[0]
    changed_own = RangePrior.create([(own.combos[0], 1), (own.combos[1], 3)])
    namespace_only = RangeMassAbstraction(
        base_model, RangeContext((changed_own, old.priors[1]))
    )
    before, after = (
        json.loads(encoder.information(o)),
        json.loads(namespace_only.information(o)),
    )
    assert before[1] != after[1] and before[2:] == after[2:]
    for invalid in (
        replace(o, terminal=True),
        replace(o, seat=1),
        replace(o, hole_cards=cards("2c 3c")),
    ):
        with pytest.raises(ValueError):
            encoder.information(invalid)
    with pytest.raises(ValueError, match="serialization"):
        encoder.save(tmp_path / "bad.json", provenance={})
    with pytest.raises(ValueError, match="explicitly"):
        RangeMassAbstraction.load(ROOT / "results/card-models/potential-8.json")
    assert not (tmp_path / "bad.json").exists()


@pytest.mark.parametrize("game", ["dev_low_oop", "dev_medium_oop"])
def test_refinement_menus_and_perfect_recall_only(
    base_model: CardAbstraction, game: str
) -> None:
    source = SpotTree.build(load_spot(ROOT / f"configs/learning-spots/{game}.json"))
    old = MatrixTree.build(
        source,
        "texture_b8",
        MadeCategoryAbstraction(base_model.models, base_model.config),
    )
    candidate = build_representation_control(source, CANDIDATE, base_model)
    assert recall_violations(candidate) == 0
    for i in range(len(candidate.keys)):
        members = np.flatnonzero(candidate.exact_to_abstract == i)
        assert len(set(old.exact_to_abstract[members])) == 1
        assert len({source.menus[int(m)] for m in members}) == 1
    # No compression ratio or learning result is measured/reported in this test.


def test_inspector_changes_feature_without_selecting_actions() -> None:
    command = [sys.executable, str(ROOT / "scripts/inspect_range_feature.py")]
    a = subprocess.run(command + ["9h"], capture_output=True, text=True)
    b = subprocess.run(command + ["9d"], capture_output=True, text=True)
    assert a.returncode == b.returncode == 0
    x, y = json.loads(a.stdout), json.loads(b.stdout)
    assert x["context_sha256"] == y["context_sha256"]
    assert x["feature_bins"] != y["feature_bins"]
    assert "action" not in x and "strategy" not in x
    bad = subprocess.run(command + ["Td"], capture_output=True)
    assert bad.returncode == 2
