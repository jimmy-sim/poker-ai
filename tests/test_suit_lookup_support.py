"""Independent finite-card checks and scoped fallback/restoration accounting."""

import importlib
import itertools
import json
import sys
import threading
from pathlib import Path
from types import ModuleType
from typing import Any

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
s = importlib.import_module("suit_lookup_support")
SHA = "f422fabd71dd88fc9b169442354ac8a8d017be6debe69f170548f1064c8c3ec8"


def test_all1248_entries_independent_rule_and_permutation_order() -> None:
    s.check_table(SHA)
    assert len(s.TABLE) == 24 and s.PERMUTATIONS == tuple(
        itertools.permutations(range(4))
    )
    for index, permutation in enumerate(itertools.permutations(range(4))):
        for rank, suit in itertools.product(range(13), range(4)):
            assert s.TABLE[index][rank * 4 + suit] == rank * 4 + permutation[suit]


def test_all1326_preflop_pairs_match_original() -> None:
    assert sum(1 for _ in itertools.combinations(range(52), 2)) == 1326
    for hole in itertools.combinations(range(52), 2):
        assert s.translated_cards(hole, ()) == s.BASE(hole, ())


@settings(max_examples=128, derandomize=True, deadline=None)
@given(
    st.lists(st.integers(0, 51), min_size=7, max_size=7, unique=True),
    st.sampled_from([0, 3, 4, 5]),
)
def test_valid_cards_match_original_without_input_change(
    cards: list[int], length: int
) -> None:
    hole, board = tuple(cards[:2]), tuple(cards[2 : 2 + length])
    before = (hole, board)
    assert s.translated_cards(hole, board) == s.BASE(hole, board)
    assert (hole, board) == before


@pytest.mark.parametrize("permutation", list(itertools.permutations(range(4))))
def test_suit_and_input_order_invariance(permutation: tuple[int, ...]) -> None:
    hole = (0, 19)
    board = (23, 28, 35, 42, 49)

    def move(cards: tuple[int, ...]) -> tuple[int, ...]:
        return tuple(4 * (c // 4) + permutation[c % 4] for c in cards)

    expected = s.BASE(hole, board)
    assert s.translated_cards(move(hole[::-1]), move(board[::-1])) == expected


def outcome(call: Any, *args: Any, **kwargs: Any) -> dict[str, Any]:
    try:
        return dict(value=call(*args, **kwargs), error=None)
    except Exception as error:
        return dict(value=None, error=(type(error).__name__, str(error)))


@pytest.mark.parametrize(
    "case",
    [
        ((), ()),
        ((0,), ()),
        ((0, 1, 2), ()),
        ((0, 1), (2,)),
        ((0, 1), (2, 3)),
        ((0, 1), (2, 3, 4, 5, 6, 7)),
        ((0, 0), ()),
        ((0, 1), (2, 2, 3)),
        ((0, 1), (0, 2, 3)),
        ((-1, 1), ()),
        ((0, 52), ()),
        ((False, 1), ()),
        ((0, 1), (2.0, 3, 4)),
        ([0, 1], [2, 3, 4]),
        ((0, 1), [2, 3, 4]),
        ((np.int64(0), 1), ()),
        (None, ()),
    ],
)
@pytest.mark.parametrize("mode", ["original", "lookup"])
def test_invalid_and_unsupported_preserve_original_value_or_error(
    case: Any, mode: str, tmp_path: Path
) -> None:
    expected = outcome(s.BASE, *case)
    with s.kernel_scope(mode, tmp_path / "kernel.json", 4, SHA) as receipt:
        actual = outcome(s.potential.canonical_cards, *case)
    assert actual == expected and receipt["restored"]
    assert (
        receipt["requests"]
        == receipt["original_evaluations"] + receipt["lookup_evaluations"]
        == 1
    )
    assert receipt["errors"] == (1 if expected["error"] else 0)
    assert receipt["status"] == ("failed_retained" if expected["error"] else "complete")


@pytest.mark.parametrize("mode", ["original", "lookup"])
def test_keyword_and_arity_fallback(mode: str, tmp_path: Path) -> None:
    with s.kernel_scope(mode, tmp_path / "kernel.json", 8, SHA) as receipt:
        calls: list[tuple[list[Any], dict[str, Any]]] = [
            ([], dict(hole=(0, 1), board=())),
            ([(0, 1)], {}),
            ([], dict(hole=(0, 1), board=(), extra=True)),
        ]
        for args, kwargs in calls:
            assert outcome(s.potential.canonical_cards, *args, **kwargs) == outcome(
                s.BASE, *args, **kwargs
            )
    assert (
        receipt["fallbacks"] == 3
        and receipt["original_evaluations"] == 3
        and receipt["lookup_evaluations"] == 0
    )
    assert receipt["restored"] and receipt["status"] == "failed_retained"


@pytest.mark.parametrize("mode", ["original", "lookup"])
def test_loaded_late_aliases_and_nested_refusal(
    mode: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    alias = ModuleType("compact_cached._suit_lookup_initial")
    vars(alias)["saved"] = s.BASE
    monkeypatch.setitem(sys.modules, alias.__name__, alias)
    late = ModuleType("poker_ai._suit_lookup_late")
    monkeypatch.setitem(sys.modules, late.__name__, late)
    with s.kernel_scope(mode, tmp_path / "kernel.json", 8, SHA) as receipt:
        assert vars(alias)["saved"]((0, 1), ()) == s.BASE((0, 1), ())
        vars(late)["saved"] = s.potential.canonical_cards
        assert vars(late)["saved"]((2, 3), (4, 5, 6)) == s.BASE((2, 3), (4, 5, 6))
        with pytest.raises(ArithmeticError):
            with s.kernel_scope(mode, tmp_path / "nested.json", 8, SHA):
                pass
    assert vars(alias)["saved"] is s.BASE and vars(late)["saved"] is s.BASE
    assert (
        receipt["restored"]
        and receipt["status"] == "complete"
        and receipt["requests"] == 2
    )
    assert (
        s.read_kernel(
            tmp_path / "kernel.json",
            mode,
            8,
            SHA,
            receipt["pid"],
            receipt["thread"],
            require_lookup=mode == "lookup",
        )
        == receipt
    )


@pytest.mark.parametrize(
    "name", ["card_bit", "_require_int_in_range", "DECK_SIZE", "format_card"]
)
def test_card_dependency_change_uses_original(
    name: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    with s.kernel_scope("lookup", tmp_path / "kernel.json", 4, SHA) as receipt:
        old = getattr(s.cards, name)

        def forward(*args: Any, **kwargs: Any) -> Any:
            return old(*args, **kwargs)

        replacement: Any = 53 if name == "DECK_SIZE" else forward

        monkeypatch.setattr(s.cards, name, replacement)
        assert s.potential.canonical_cards((0, 1), ()) == s.BASE((0, 1), ())
    assert (
        receipt["fallbacks"] == receipt["original_evaluations"] == 1
        and receipt["lookup_evaluations"] == 0
    )


@pytest.mark.parametrize("name", ["cards_to_mask", "SUIT_PERMUTATIONS"])
def test_potential_dependency_change_uses_original(
    name: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    with s.kernel_scope("lookup", tmp_path / "kernel.json", 4, SHA) as receipt:
        old = getattr(s.potential, name)

        def forward(*args: Any, **kwargs: Any) -> Any:
            return old(*args, **kwargs)

        replacement: Any = (
            tuple(reversed(old)) if name == "SUIT_PERMUTATIONS" else forward
        )

        monkeypatch.setattr(s.potential, name, replacement)
        assert s.potential.canonical_cards((0, 1), ()) == s.BASE((0, 1), ())
    assert (
        receipt["fallbacks"] == receipt["original_evaluations"] == 1
        and receipt["lookup_evaluations"] == 0
    )


def test_capacity_and_primary_failure_restore(tmp_path: Path) -> None:
    with pytest.raises(ArithmeticError, match="capacity"):
        with s.kernel_scope("lookup", tmp_path / "cap.json", 1, SHA):
            s.potential.canonical_cards((0, 1), ())
            s.potential.canonical_cards((2, 3), ())
    cap = json.loads((tmp_path / "cap.json").read_text())
    assert cap["restored"] and cap["errors"] == 1 and cap["requests"] == 1
    error = KeyboardInterrupt("fictional stop")
    with pytest.raises(KeyboardInterrupt) as caught:
        with s.kernel_scope("lookup", tmp_path / "stop.json", 4, SHA):
            raise error
    assert caught.value is error and s.potential.canonical_cards is s.BASE
    assert (
        json.loads((tmp_path / "stop.json").read_text())["status"] == "failed_retained"
    )


def test_foreign_thread_refused(tmp_path: Path) -> None:
    errors = []

    def foreign() -> None:
        try:
            s.potential.canonical_cards((0, 1), ())
        except BaseException as error:
            errors.append(error)

    with s.kernel_scope("lookup", tmp_path / "kernel.json", 4, SHA) as receipt:
        thread = threading.Thread(target=foreign)
        thread.start()
        thread.join()
    assert len(errors) == 1 and isinstance(errors[0], ArithmeticError)
    assert receipt["restored"] and receipt["errors"] == 1 and receipt["requests"] == 0


@pytest.mark.parametrize(
    "field",
    [
        "maximum",
        "pid",
        "thread",
        "requests",
        "original_evaluations",
        "lookup_evaluations",
        "fallbacks",
        "errors",
        "aliases_remaining",
    ],
)
def test_boolean_counters_not_integer_proof(field: str, tmp_path: Path) -> None:
    with s.kernel_scope("lookup", tmp_path / "kernel.json", 4, SHA) as receipt:
        s.potential.canonical_cards((0, 1), ())
    row = json.loads((tmp_path / "kernel.json").read_text())
    row[field] = bool(row[field])
    (tmp_path / "kernel.json").write_text(json.dumps(row))
    with pytest.raises(ArithmeticError):
        s.read_kernel(
            tmp_path / "kernel.json",
            "lookup",
            4,
            SHA,
            receipt["pid"],
            receipt["thread"],
        )


@pytest.mark.parametrize(
    "change",
    ["table", "scope", "mode", "sum", "missing", "extra", "status", "restored"],
)
def test_corrupt_kernel_records_refused(change: str, tmp_path: Path) -> None:
    with s.kernel_scope("lookup", tmp_path / "kernel.json", 4, SHA) as receipt:
        s.potential.canonical_cards((0, 1), ())
    row = json.loads((tmp_path / "kernel.json").read_text())
    if change == "missing":
        row.pop("requests")
    elif change == "extra":
        row["unexpected"] = True
    elif change == "table":
        row["table_sha256"] = "0" * 64
    elif change == "sum":
        row["lookup_evaluations"] = 0
    elif change == "restored":
        row["restored"] = False
    else:
        row[change] = "changed"
    (tmp_path / "kernel.json").write_text(json.dumps(row))
    with pytest.raises(ArithmeticError):
        s.read_kernel(
            tmp_path / "kernel.json",
            "lookup",
            4,
            SHA,
            receipt["pid"],
            receipt["thread"],
            require_lookup=True,
        )


@pytest.mark.parametrize(
    "encoding", ["exact", "legacy_b8", "public_b8", "canonical_b8", "texture_b8"]
)
@pytest.mark.parametrize("mode", ["original", "lookup"])
def test_all_original_constructor_fields_preserved(
    encoding: Any, mode: str, tmp_path: Path
) -> None:
    from poker_ai.abstraction.model import CardAbstraction
    from poker_ai.postflop.game import load_spot
    from poker_ai.postflop.matrix import MatrixTree
    from poker_ai.postflop.tree import SpotTree

    source = SpotTree.build(load_spot(ROOT / "configs/learning-spots/dev_low_oop.json"))
    model = CardAbstraction.load(ROOT / "results/card-models/potential-8.json")
    baseline = s.fields.BASE_FUNCTION(MatrixTree, source, encoding, model)
    with s.kernel_scope(mode, tmp_path / "kernel.json", 100000, SHA):
        with s.fields.constructor_scope("original", tmp_path / "constructors", 4):
            actual = MatrixTree.build(source, encoding, model)
    assert s.fields.matrix_witness(baseline, source) == s.fields.matrix_witness(
        actual, source
    )


@pytest.mark.parametrize("mode", ["original", "lookup"])
def test_no_result_memoization_or_rng_draws(mode: str, tmp_path: Path) -> None:
    import copy

    rng = np.random.default_rng(17)
    before = copy.deepcopy(rng.bit_generator.state)
    with s.kernel_scope(mode, tmp_path / "kernel.json", 4, SHA) as receipt:
        for _ in range(3):
            assert s.potential.canonical_cards((0, 1), (4, 8, 12)) == s.BASE(
                (0, 1), (4, 8, 12)
            )
    assert receipt["requests"] == 3 and receipt["fallbacks"] == 0
    assert receipt["original_evaluations"] == (3 if mode == "original" else 0)
    assert receipt["lookup_evaluations"] == (3 if mode == "lookup" else 0)
    assert rng.bit_generator.state == before
