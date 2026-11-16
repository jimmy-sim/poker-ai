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
s = importlib.import_module("suit_candidates_support")
SHA = "f422fabd71dd88fc9b169442354ac8a8d017be6debe69f170548f1064c8c3ec8"
GEOM = "f1cf3685244285e88220e82b5c274fd96b12f07acf4cd17a106bf079ce2cfc8d"


def test_all1248_entries_independent_rule_and_permutation_order() -> None:
    s.check_geometry(SHA, GEOM)
    assert len(s.TABLE) == 24 and s.lookup.PERMUTATIONS == tuple(
        itertools.permutations(range(4))
    )
    for index, permutation in enumerate(itertools.permutations(range(4))):
        for rank, suit in itertools.product(range(13), range(4)):
            assert s.TABLE[index][rank * 4 + suit] == rank * 4 + permutation[suit]


def test_all2652_ordered_preflop_pairs_match_original() -> None:
    assert sum(1 for _ in itertools.permutations(range(52), 2)) == 2652
    for hole in itertools.permutations(range(52), 2):
        assert s.reduced_cards(hole, ()) == s.BASE(hole, ())


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
    assert s.reduced_cards(hole, board) == s.BASE(hole, board)
    assert (hole, board) == before


@pytest.mark.parametrize("permutation", list(itertools.permutations(range(4))))
def test_suit_and_input_order_invariance(permutation: tuple[int, ...]) -> None:
    hole = (0, 19)
    board = (23, 28, 35, 42, 49)

    def move(cards: tuple[int, ...]) -> tuple[int, ...]:
        return tuple(4 * (c // 4) + permutation[c % 4] for c in cards)

    expected = s.BASE(hole, board)
    assert s.reduced_cards(move(hole[::-1]), move(board[::-1])) == expected


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
@pytest.mark.parametrize("mode", ["all", "reduced"])
def test_invalid_and_unsupported_preserve_original_value_or_error(
    case: Any, mode: str, tmp_path: Path
) -> None:
    expected = outcome(s.BASE, *case)
    with s.kernel_scope(mode, tmp_path / "kernel.json", 4, SHA, GEOM) as receipt:
        actual = outcome(s.potential.canonical_cards, *case)
    assert actual == expected and receipt["restored"]
    assert (
        receipt["requests"]
        == receipt["original_evaluations"]
        + receipt["all_evaluations"]
        + receipt["reduced_evaluations"]
        == 1
    )
    assert receipt["errors"] == (1 if expected["error"] else 0)
    assert receipt["status"] == ("failed_retained" if expected["error"] else "complete")


@pytest.mark.parametrize("mode", ["all", "reduced"])
def test_keyword_and_arity_fallback(mode: str, tmp_path: Path) -> None:
    with s.kernel_scope(mode, tmp_path / "kernel.json", 8, SHA, GEOM) as receipt:
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
        and receipt["reduced_evaluations"] == 0
    )
    assert receipt["restored"] and receipt["status"] == "failed_retained"


@pytest.mark.parametrize("mode", ["all", "reduced"])
def test_loaded_late_aliases_and_nested_refusal(
    mode: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    alias = ModuleType("compact_cached._suit_lookup_initial")
    vars(alias)["saved"] = s.BASE
    monkeypatch.setitem(sys.modules, alias.__name__, alias)
    late = ModuleType("poker_ai._suit_lookup_late")
    monkeypatch.setitem(sys.modules, late.__name__, late)
    with s.kernel_scope(mode, tmp_path / "kernel.json", 8, SHA, GEOM) as receipt:
        assert vars(alias)["saved"]((0, 1), ()) == s.BASE((0, 1), ())
        vars(late)["saved"] = s.potential.canonical_cards
        assert vars(late)["saved"]((2, 3), (4, 5, 6)) == s.BASE((2, 3), (4, 5, 6))
        with pytest.raises(ArithmeticError):
            with s.kernel_scope(mode, tmp_path / "nested.json", 8, SHA, GEOM):
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
            GEOM,
            receipt["pid"],
            receipt["thread"],
            require_reduced=mode == "reduced",
        )
        == receipt
    )


@pytest.mark.parametrize(
    "name", ["card_bit", "_require_int_in_range", "DECK_SIZE", "format_card"]
)
def test_card_dependency_change_uses_original(
    name: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    with s.kernel_scope("reduced", tmp_path / "kernel.json", 4, SHA, GEOM) as receipt:
        old = getattr(s.lookup.cards, name)

        def forward(*args: Any, **kwargs: Any) -> Any:
            return old(*args, **kwargs)

        replacement: Any = 53 if name == "DECK_SIZE" else forward

        monkeypatch.setattr(s.lookup.cards, name, replacement)
        assert s.potential.canonical_cards((0, 1), ()) == s.BASE((0, 1), ())
    assert (
        receipt["fallbacks"] == receipt["original_evaluations"] == 1
        and receipt["reduced_evaluations"] == 0
    )


@pytest.mark.parametrize("name", ["cards_to_mask", "SUIT_PERMUTATIONS"])
def test_potential_dependency_change_uses_original(
    name: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    with s.kernel_scope("reduced", tmp_path / "kernel.json", 4, SHA, GEOM) as receipt:
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
        and receipt["reduced_evaluations"] == 0
    )


def test_capacity_and_primary_failure_restore(tmp_path: Path) -> None:
    with pytest.raises(ArithmeticError, match="capacity"):
        with s.kernel_scope("reduced", tmp_path / "cap.json", 1, SHA, GEOM):
            s.potential.canonical_cards((0, 1), ())
            s.potential.canonical_cards((2, 3), ())
    cap = json.loads((tmp_path / "cap.json").read_text())
    assert cap["restored"] and cap["errors"] == 1 and cap["requests"] == 1
    error = KeyboardInterrupt("fictional stop")
    with pytest.raises(KeyboardInterrupt) as caught:
        with s.kernel_scope("reduced", tmp_path / "stop.json", 4, SHA, GEOM):
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

    with s.kernel_scope("reduced", tmp_path / "kernel.json", 4, SHA, GEOM) as receipt:
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
        "all_evaluations",
        "reduced_evaluations",
        "fallbacks",
        "errors",
        "aliases_remaining",
    ],
)
def test_boolean_counters_not_integer_proof(field: str, tmp_path: Path) -> None:
    with s.kernel_scope("reduced", tmp_path / "kernel.json", 4, SHA, GEOM) as receipt:
        s.potential.canonical_cards((0, 1), ())
    row = json.loads((tmp_path / "kernel.json").read_text())
    row[field] = bool(row[field])
    (tmp_path / "kernel.json").write_text(json.dumps(row))
    with pytest.raises(ArithmeticError):
        s.read_kernel(
            tmp_path / "kernel.json",
            "reduced",
            4,
            SHA,
            GEOM,
            receipt["pid"],
            receipt["thread"],
        )


@pytest.mark.parametrize(
    "change",
    ["table", "scope", "mode", "sum", "missing", "extra", "status", "restored"],
)
def test_corrupt_kernel_records_refused(change: str, tmp_path: Path) -> None:
    with s.kernel_scope("reduced", tmp_path / "kernel.json", 4, SHA, GEOM) as receipt:
        s.potential.canonical_cards((0, 1), ())
    row = json.loads((tmp_path / "kernel.json").read_text())
    if change == "missing":
        row.pop("requests")
    elif change == "extra":
        row["unexpected"] = True
    elif change == "table":
        row["table_sha256"] = "0" * 64
    elif change == "sum":
        row["reduced_evaluations"] = 0
    elif change == "restored":
        row["restored"] = False
    else:
        row[change] = "changed"
    (tmp_path / "kernel.json").write_text(json.dumps(row))
    with pytest.raises(ArithmeticError):
        s.read_kernel(
            tmp_path / "kernel.json",
            "reduced",
            4,
            SHA,
            GEOM,
            receipt["pid"],
            receipt["thread"],
            require_reduced=True,
        )


@pytest.mark.parametrize(
    "encoding", ["exact", "legacy_b8", "public_b8", "canonical_b8", "texture_b8"]
)
@pytest.mark.parametrize("mode", ["all", "reduced"])
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
    with s.kernel_scope(mode, tmp_path / "kernel.json", 100000, SHA, GEOM):
        with s.fields.constructor_scope("original", tmp_path / "constructors", 4):
            actual = MatrixTree.build(source, encoding, model)
    assert s.fields.matrix_witness(baseline, source) == s.fields.matrix_witness(
        actual, source
    )


@pytest.mark.parametrize("mode", ["all", "reduced"])
def test_no_result_memoization_or_rng_draws(mode: str, tmp_path: Path) -> None:
    import copy

    rng = np.random.default_rng(17)
    before = copy.deepcopy(rng.bit_generator.state)
    with s.kernel_scope(mode, tmp_path / "kernel.json", 4, SHA, GEOM) as receipt:
        for _ in range(3):
            assert s.potential.canonical_cards((0, 1), (4, 8, 12)) == s.BASE(
                (0, 1), (4, 8, 12)
            )
    assert receipt["requests"] == 3 and receipt["fallbacks"] == 0
    assert receipt["original_evaluations"] == 0
    assert receipt["all_evaluations"] == (3 if mode == "all" else 0)
    assert receipt["reduced_evaluations"] == (3 if mode == "reduced" else 0)
    assert rng.bit_generator.state == before


@pytest.mark.parametrize("reported_fallbacks", [0, 1])
def test_lookup_original_evaluations_are_exactly_fallbacks(
    tmp_path: Path, reported_fallbacks: int
) -> None:
    with s.kernel_scope("reduced", tmp_path / "kernel.json", 8, SHA, GEOM) as receipt:
        s.potential.canonical_cards((0, 1), ())
    path = tmp_path / "kernel.json"
    row = json.loads(path.read_text())
    row.update(requests=3, original_evaluations=2, fallbacks=reported_fallbacks)
    path.write_text(json.dumps(row))
    with pytest.raises(ArithmeticError):
        s.read_kernel(
            path,
            "reduced",
            8,
            SHA,
            GEOM,
            receipt["pid"],
            receipt["thread"],
            require_reduced=True,
        )


@pytest.mark.parametrize("mode", ["all", "reduced"])
def test_complete_supported_and_fallback_accounting(mode: str, tmp_path: Path) -> None:
    path = tmp_path / "kernel.json"
    with s.kernel_scope(mode, path, 8, SHA, GEOM) as receipt:
        s.potential.canonical_cards((0, 1), ())
        s.potential.canonical_cards(hole=(0, 1), board=())
    row = s.read_kernel(
        path,
        mode,
        8,
        SHA,
        GEOM,
        receipt["pid"],
        receipt["thread"],
        require_reduced=mode == "reduced",
    )
    assert row["requests"] == 2 and row["fallbacks"] == 1
    assert row["original_evaluations"] == 1
    assert row["all_evaluations"] == (1 if mode == "all" else 0)
    assert row["reduced_evaluations"] == (0 if mode == "all" else 1)


def test_all2704_geometry_slots_and_tie_classes() -> None:
    s.check_geometry(SHA, GEOM)
    assert s.geometry_sha() == GEOM
    counts = {2: 0, 4: 0, 6: 0}
    for a, row in enumerate(s.GEOMETRY):
        assert len(row) == 52
        for b, slot in enumerate(row):
            if a == b:
                assert slot is None
                continue
            assert slot is not None
            private, indices = slot
            assert private == s.BASE((a, b), ())[0]
            literal = []
            for i, permutation in enumerate(itertools.permutations(range(4))):
                transformed = tuple(
                    sorted(
                        (
                            4 * (a // 4) + permutation[a % 4],
                            4 * (b // 4) + permutation[b % 4],
                        )
                    )
                )
                if transformed == private:
                    literal.append(i)
            assert indices == tuple(literal)
            assert len(indices) == (
                6 if a % 4 == b % 4 else (4 if a // 4 == b // 4 else 2)
            )
            assert slot == s.GEOMETRY[b][a]
            counts[len(indices)] += 1
    assert counts == {2: 1872, 4: 156, 6: 624}


def test_private_prefix_cannot_be_sacrificed_for_smaller_board() -> None:
    hole, board = (0, 4), (11, 15, 19)
    assert s.reduced_cards(hole, board) == s.BASE(hole, board) == ((0, 4), (9, 13, 17))
    independent_board = min(
        tuple(sorted(4 * (c // 4) + p[c % 4] for c in board))
        for p in itertools.permutations(range(4))
    )
    assert independent_board == (8, 12, 16)
    assert s.reduced_cards(hole, board)[1] != independent_board


@pytest.mark.parametrize("mode", ["all", "reduced"])
def test_return_private_tuple_is_fresh(mode: str, tmp_path: Path) -> None:
    with s.kernel_scope(mode, tmp_path / "kernel.json", 4, SHA, GEOM):
        first = s.potential.canonical_cards((0, 4), ())
        second = s.potential.canonical_cards((0, 4), ())
    assert first == second == s.BASE((0, 4), ())
    assert first is not second and first[0] is not second[0]


@pytest.mark.parametrize("changed", ["geometry", "table", "all_function", "mask"])
def test_changed_static_dependencies_fall_back(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, changed: str
) -> None:
    with s.kernel_scope("reduced", tmp_path / "kernel.json", 4, SHA, GEOM) as receipt:
        if changed == "geometry":
            monkeypatch.setattr(s, "GEOMETRY", tuple(reversed(s.GEOMETRY)))
        elif changed == "table":
            monkeypatch.setattr(s.lookup, "TABLE", tuple(reversed(s.TABLE)))
        elif changed == "all_function":
            monkeypatch.setattr(
                s.lookup,
                "translated_cards",
                lambda *args: pytest.fail("changed private function called"),
            )
        else:
            monkeypatch.setattr(
                s.lookup,
                "BASE_MASK",
                lambda *args: pytest.fail("changed private mask called"),
            )
        assert s.potential.canonical_cards((0, 4), (11, 15, 19)) == s.BASE(
            (0, 4), (11, 15, 19)
        )
    assert receipt["original_evaluations"] == receipt["fallbacks"] == 1
    assert receipt["all_evaluations"] == receipt["reduced_evaluations"] == 0
    assert receipt["restored"] is True


def test_wrong_geometry_digest_refused_before_hook(tmp_path: Path) -> None:
    with pytest.raises(ArithmeticError):
        with s.kernel_scope("reduced", tmp_path / "kernel.json", 4, SHA, "0" * 64):
            pytest.fail("bad static geometry entered kernel")
    assert s.potential.canonical_cards is s.BASE
    assert not (tmp_path / "kernel.json").exists()


@pytest.mark.parametrize("mode", ["all", "reduced"])
@pytest.mark.parametrize("name", ["ALL", "BASE_MASK"])
def test_changed_local_alias_uses_captured_original(
    mode: str, name: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    with s.kernel_scope(mode, tmp_path / "kernel.json", 4, SHA, GEOM) as receipt:
        monkeypatch.setattr(
            s, name, lambda *args: pytest.fail("changed local dependency called")
        )
        assert s.potential.canonical_cards((0, 4), (11, 15, 19)) == s.BASE(
            (0, 4), (11, 15, 19)
        )
    assert receipt["original_evaluations"] == receipt["fallbacks"] == 1
    assert receipt["all_evaluations"] == receipt["reduced_evaluations"] == 0
    assert receipt["restored"] is True
