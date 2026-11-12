"""Independent category oracle, information boundaries and structural checks only."""

import inspect
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

from poker_ai.abstraction.model import CardAbstraction
from poker_ai.abstraction.public_range import (
    ORDER,
    VERSION,
    PublicOwnMass,
    PublicOwnRangeAbstraction,
    pack,
    public_own_mass,
    unpack,
)
from poker_ai.abstraction.range_mass import (
    RangeContext,
    RangeMassAbstraction,
    RangePrior,
)
from poker_ai.cards import Deck, parse_card
from poker_ai.engine import Action, ActionKind, new_hand
from poker_ai.evaluator import evaluate_five
from poker_ai.postflop.game import SpotState, load_spot
from poker_ai.postflop.matrix import recall_violations
from poker_ai.postflop.public_range_definition import (
    CANDIDATE,
    build_control,
    check_inputs,
    contract,
)
from poker_ai.postflop.range_protocol import range_context
from poker_ai.postflop.tree import SpotTree

ROOT = Path(__file__).resolve().parents[1]


def cards(text: str) -> tuple[int, ...]:
    return tuple(parse_card(c) for c in text.split())


def prior(*hands: tuple[str, int | float]) -> RangePrior:
    return RangePrior.create((cards(h), w) for h, w in hands)


def test_known_public_removal_exact_weights_and_packed_words() -> None:
    p = prior(("Qh Kh", 1), ("9c 9d", 1))
    h = public_own_mass(cards("Ts 9s 4d 2h 9h"), p)
    d = public_own_mass(cards("Ts 9s 4d 2h 9d"), p)
    assert h.masses[2] == h.masses[8] == Fraction(1, 2) and sum(h.masses) == 1
    assert d.masses[0] == d.masses[2] == Fraction(1, 2) and d.masses[8] == 0
    assert h.word == 67109120 and d.word == 260
    assert unpack(h.word) == h.bins and unpack(d.word) == d.bins
    weighted = public_own_mass(
        cards("Ts 9s 4d 2h 9h"), prior(("Qh Kh", 0.1), ("9c 9d", 0.2))
    )
    assert weighted.masses[2] == Fraction(1, 3) and weighted.masses[8] == Fraction(2, 3)
    assert weighted.bins[2] == 2 and weighted.bins[8] == 5


@pytest.mark.parametrize(
    "hand,category",
    [
        ("Ah Kd 2c 4s 6h 8d Tc", 0),
        ("Ah Ad 2c 4s 6h 8d Tc", 1),
        ("Ah Ad Kc Ks 6h 8d Tc", 2),
        ("Ah Ad Ac 4s 6h 8d Tc", 3),
        ("Ah Kd Qc Js Th 2d 3c", 4),
        ("Ah Kh 2h 4h 6h 8d Tc", 5),
        ("Ah Ad Ac Ks Kh 2d 3c", 6),
        ("Ah Ad Ac As Kh 2d 3c", 7),
        ("Ah Kh Qh Jh Th 2d 3c", 8),
    ],
)
def test_all_categories_against_exhaustive_five_card_oracle(
    hand: str, category: int
) -> None:
    h = cards(hand)
    p = RangePrior.create([(h[:2], 1)])
    expected = max(evaluate_five(c) for c in itertools.combinations(h, 5)).category
    assert int(expected) == category
    m = public_own_mass(h[2:], p)
    assert m.masses[1 + category] == 1 and m.bins[1 + category] == 7


def test_set_blockers_and_exhaustive_category_oracle_fixed_random_inputs() -> None:
    rng = np.random.default_rng(54)
    for _ in range(40):
        board = tuple(int(x) for x in rng.choice(52, 5, replace=False))
        hands = [
            tuple(int(x) for x in rng.choice(52, 2, replace=False)) for _ in range(5)
        ]
        if len({frozenset(h) for h in hands}) != len(hands):
            continue
        p = RangePrior.create((h, i + 1) for i, h in enumerate(hands))
        expected = [Fraction(0)] * 10
        for h, w in zip(p.combos, p.masses, strict=True):
            i = (
                0
                if set(board) & set(h)
                else 1
                + int(
                    max(
                        evaluate_five(c) for c in itertools.combinations(h + board, 5)
                    ).category
                )
            )
            expected[i] += w
        assert public_own_mass(board, p).masses == tuple(expected)


@pytest.mark.parametrize("edge", range(1, 8))
def test_all_rational_boundaries_and_pack_round_trip(edge: int) -> None:
    q = Fraction(edge, 8)
    tiny = Fraction(1, 10**100)
    for value, expected in ((q - tiny, edge - 1), (q, edge), (q + tiny, edge)):
        masses = (value, 1 - value) + tuple(Fraction(0) for _ in range(8))
        m = PublicOwnMass(masses)
        assert m.bins[0] == expected and unpack(m.word) == m.bins
    assert unpack((1 << 30) - 1) == (7,) * 10


@pytest.mark.parametrize("word", [True, -1, 1 << 30, 1.2, float("nan")])
def test_invalid_word(word: Any) -> None:
    with pytest.raises(ValueError):
        unpack(word)


@pytest.mark.parametrize(
    "bins", [(0,) * 9, (0,) * 9 + (8,), (0,) * 9 + (-1,), (0,) * 9 + (True,)]
)
def test_invalid_bins(bins: tuple[int, ...]) -> None:
    with pytest.raises(ValueError):
        pack(bins)


def test_immutability_all_blocked_invalid_mass_and_public_inputs() -> None:
    p = prior(("As Kd", 1), ("As Qd", 1))
    m = public_own_mass(cards("2c 3d 4h 5s 9c"), p)
    assert m.masses[0] == 0  # Actual AsKd must NOT remove alternative AsQd.
    assert set(inspect.signature(public_own_mass).parameters) == {"board", "prior"}
    blocked = public_own_mass(cards("As 3d 4h 5s 9c"), p)
    assert blocked.masses[0] == 1 and blocked.word == 7
    with pytest.raises(FrozenInstanceError):
        mutable: Any = m
        mutable.masses = ()
    for bad in (
        (Fraction(1),),
        (1,) + (Fraction(0),) * 9,
        (Fraction(-1), Fraction(2)) + (Fraction(0),) * 8,
    ):
        with pytest.raises(ValueError):
            invalid: Any = bad
            PublicOwnMass(invalid)
    for board in ((0, 1), (0, 1, 2, 3, 3), (0, 1, 2, 3, 52), (0, 1, 2, 3, True)):
        with pytest.raises((ValueError, TypeError)):
            public_own_mass(board, p)


def test_symmetries_prior_scaling_large_integers_and_pooled_collision() -> None:
    board = cards("Ts 9s 4d 2h 9d")
    p = prior(("Qh Kh", 2**110 + 1), ("9c 9d", 2))
    assert p == prior(("9d 9c", 14), ("Kh Qh", 7 * (2**110 + 1)))
    expected = public_own_mass(board, p)
    for suits in itertools.permutations(range(4)):

        def rename(
            xs: tuple[int, ...], mapping: tuple[int, ...] = suits
        ) -> tuple[int, ...]:
            return tuple(4 * (c // 4) + mapping[c % 4] for c in xs)

        transformed = RangePrior.create(
            [
                (rename(h), 2**110 + 1 if h == tuple(sorted(cards("Qh Kh"))) else 2)
                for h in p.combos
            ]
        )
        assert public_own_mass(rename(board), transformed) == expected
    assert public_own_mass(tuple(reversed(board)), p) == expected
    assert (
        public_own_mass(cards("Ts 9s 4d 2h 5c"), p).word
        == public_own_mass(cards("Ts 9s 4d 2h 5h"), p).word
    )
    many = RangePrior.create(((a, b), 1) for a in range(15) for b in range(a + 1, 16))
    for r in (p, many):
        m = public_own_mass(board, r)
        assert len(m.bins) == len(ORDER) == 10 and 0 <= m.word < 2**30


@pytest.fixture(scope="module")
def model() -> CardAbstraction:
    return CardAbstraction.load(ROOT / "results/card-models/potential-8.json")


def test_recorded_public_counterexample_splits_without_loading_saved_values(
    model: CardAbstraction,
) -> None:
    # These two observation IDs are pinned by the previous published example.
    # No saved Q/strategy file is loaded; the bound game must reproduce the cards.
    source = SpotTree.build(
        load_spot(ROOT / "configs/learning-spots/dev_medium_oop.json")
    )
    context = range_context(source.spot)
    parent = RangeMassAbstraction(model, context)
    candidate = PublicOwnRangeAbstraction(model, context)
    views = []
    for info, river in ((1013, "9d"), (1049, "9h")):
        state = source.states[source.representatives[info]]
        assert state.dealer is not None
        view = state.dealer.observe(1)
        assert tuple(sorted(view.hole_cards)) == tuple(sorted(cards("Qh Kh")))
        assert view.board == cards("Ts 9s 4d 2h " + river)
        views.append(view)
    assert len(views) == 2
    assert parent.information(views[0]) == parent.information(views[1])
    assert candidate.information(views[0]) != candidate.information(views[1])
    assert [json.loads(candidate.information(v))[2] for v in views] == [260, 67109120]


def test_earlier_streets_hidden_future_invariance_and_view_guards(
    model: CardAbstraction, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    import poker_ai.abstraction.public_range as module

    spot = load_spot(ROOT / "configs/learning-spots/dev_medium_oop.json")
    context = range_context(spot)
    encoder = PublicOwnRangeAbstraction(model, context)
    first = SpotState(spot).child(0).child(0)
    second = SpotState(spot).child(0).child(1)
    worlds = [
        first.child(parse_card("9h")),
        first.child(parse_card("3c")),
        second.child(parse_card("9h")),
    ]
    early = []
    for state in worlds:
        assert state.dealer is not None
        early.append(state.dealer.observe(0))
    assert len({encoder.information(o) for o in early}) == 1
    rivers = []
    for state in (worlds[0], worlds[2]):
        state = state.child(1).child(1)
        assert state.dealer is not None
        rivers.append(state.dealer.observe(0))
    assert encoder.information(rivers[0]) == encoder.information(rivers[1])

    def forbidden(*a: Any, **k: Any) -> Any:
        raise AssertionError("public feature before river")

    monkeypatch.setattr(module, "public_own_mass", forbidden)
    prefix = cards("Qh As Kh Js 2c Ts 9s 4d 2d 2h 2s 9h")
    hand = new_hand(
        (200, 200), Deck(prefix + tuple(c for c in range(52) if c not in prefix))
    )
    views = [hand.observe(0)]
    hand = hand.apply(Action(ActionKind.CALL)).apply(Action(ActionKind.CHECK))
    views.append(hand.observe(1))
    hand = hand.apply(Action(ActionKind.CHECK)).apply(Action(ActionKind.CHECK))
    views.append(hand.observe(1))
    parent = RangeMassAbstraction(model, context)
    for o in views + early:
        version, base, word = json.loads(encoder.information(o))
        assert version == VERSION and base == parent.information(o) and word is None
    for bad in (
        replace(early[0], terminal=True),
        replace(early[0], seat=1),
        replace(early[0], hole_cards=cards("2c 3c")),
        replace(early[0], seat=True),
    ):
        with pytest.raises(ValueError):
            encoder.information(bad)
    with pytest.raises(ValueError):
        encoder.save(tmp_path / "bad.json", provenance={})
    with pytest.raises(ValueError):
        PublicOwnRangeAbstraction.load(tmp_path / "bad.json")
    assert not (tmp_path / "bad.json").exists()
    p = context.priors[0]
    other = RangePrior.create([(p.combos[0], 1), (p.combos[1], 3)])
    changed = PublicOwnRangeAbstraction(model, RangeContext((other, context.priors[1])))
    assert encoder.information(early[0]) != changed.information(early[0])


@pytest.mark.parametrize("game", ["dev_low_oop", "dev_medium_oop"])
def test_only_structural_refinement_concrete_menus_owners_and_recall(
    model: CardAbstraction, game: str
) -> None:
    check_inputs(ROOT, contract(ROOT))
    source = SpotTree.build(load_spot(ROOT / f"configs/learning-spots/{game}.json"))
    old = build_control(source, "texture_range_q8_b8", model)
    candidate = build_control(source, CANDIDATE, model)
    assert recall_violations(candidate) == 0
    for i in range(len(candidate.keys)):
        members = np.flatnonzero(candidate.exact_to_abstract == i)
        assert len(set(old.exact_to_abstract[members])) == 1
        assert len({source.menus[int(m)] for m in members}) == 1
    # No row-count/compression/learning measurements published by this test.


def test_cli_only_fixed_public_encoding_no_actual_hand_or_actions() -> None:
    cmd = [sys.executable, str(ROOT / "scripts/inspect_public_range_feature.py")]
    results = [
        subprocess.run(cmd + [river], capture_output=True, text=True, check=True)
        for river in ("9h", "9d")
    ]
    a, b = (json.loads(r.stdout) for r in results)
    assert a["word"] == 67109120 and b["word"] == 260
    assert a["context_sha256"] == b["context_sha256"]
    assert not {"strategy", "action", "own_cards", "opponent_cards"} & set(a)
    assert subprocess.run(cmd + ["9s"], capture_output=True).returncode == 2
