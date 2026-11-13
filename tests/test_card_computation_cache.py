"""Pure-card equality, invalid-input preservation, finite reuse and hook scope."""

import copy
import importlib
import json
import sys
import time
from pathlib import Path
from types import ModuleType
from typing import Any

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from numpy.random import default_rng

from poker_ai import evaluator
from poker_ai.abstraction import potential
from poker_ai.cards import Deck, parse_card
from poker_ai.engine import Action, ActionKind, new_hand

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
support = importlib.import_module("card_cache_support")
tool = importlib.import_module("check_card_cache")
CONFIG = tool.contract(ROOT)


def cards(text: str) -> tuple[int, ...]:
    return tuple(map(parse_card, text.split()))


@pytest.mark.parametrize(
    "text",
    [
        "As Kd 9c 7h 3s",
        "As Ad 9c 7h 3s",
        "As Ad 9c 9h 3s",
        "As Ad Ac 7h 3s",
        "As 2d 3c 4h 5s",
        "As Js 9s 7s 3s",
        "As Ad Ac 7h 7s",
        "As Ad Ac Ah 3s",
        "As Ks Qs Js Ts",
    ],
)
def test_every_category_and_immutable_result(text: str) -> None:
    hand = cards(text)
    expected = evaluator.evaluate_best_reference(hand)
    with support.hooks(CONFIG, enabled=True) as cache:
        actual = evaluator.evaluate_best(hand)
        assert actual == expected
        assert evaluator.evaluate_best(hand) is actual
        with pytest.raises(AttributeError):
            actual.tiebreakers = ()  # type: ignore[misc]
    assert cache["rank"].summary()["hits"] == 1


@given(st.lists(st.integers(0, 51), min_size=5, max_size=7, unique=True))
@settings(max_examples=75, deadline=None)
def test_rank_all_lengths_order_and_suit_permutations(values: list[int]) -> None:
    original = evaluator.evaluate_best
    hand = tuple(values)
    changed = tuple(4 * (x // 4) + (x % 4 + 1) % 4 for x in reversed(hand))
    expected = original(hand)
    assert expected == evaluator.evaluate_best_reference(hand)
    with support.hooks(CONFIG, enabled=True) as cache:
        assert evaluator.evaluate_best(hand) == expected
        assert evaluator.evaluate_best(changed) == expected
        assert evaluator.evaluate_best(hand) == expected
    support.check_summary({k: v.summary() for k, v in cache.items()}, CONFIG, True)


@given(
    st.lists(st.integers(0, 51), min_size=7, max_size=7, unique=True),
    st.sampled_from((0, 3, 4, 5)),
)
@settings(max_examples=50, deadline=None)
def test_canonical_original_suit_and_order(values: list[int], length: int) -> None:
    hole, board = tuple(values[:2]), tuple(values[2 : 2 + length])
    original = potential.canonical_cards
    expected = original(hole, board)
    with support.hooks(CONFIG, enabled=True) as cache:
        assert potential.canonical_cards(hole, board) == expected
        assert potential.canonical_cards(hole, board) == expected

        def changed(xs: tuple[int, ...]) -> tuple[int, ...]:
            return tuple(4 * (x // 4) + (x % 4 + 1) % 4 for x in reversed(xs))

        assert potential.canonical_cards(changed(hole), changed(board)) == expected
    assert cache["canonical"].summary()["hits"] >= 1


@pytest.mark.parametrize(
    "value",
    [
        (0, 1, 2, 3),
        (0, 1, 2, 3, 3),
        (0, 1, 2, 3, 52),
        (-1, 1, 2, 3, 4),
        (False, 1, 2, 3, 4),
        (np.int64(0), 1, 2, 3, 4),
        ("0", 1, 2, 3, 4),
    ],
)
def test_repeat_invalid_ranks_preserve_original_error(value: Any) -> None:
    original = evaluator.evaluate_best
    with pytest.raises((ValueError, TypeError)) as expected:
        original(value)
    with support.hooks(CONFIG, enabled=True) as cache:
        for _ in range(2):
            with pytest.raises(
                type(expected.value),
                match="^"
                + str(expected.value).replace("[", r"\[").replace("]", r"\]")
                + "$",
            ):
                evaluator.evaluate_best(value)
    row = cache["rank"].summary()
    assert row["hits"] == row["insertions"] == 0 and row["errors"] == 2


@pytest.mark.parametrize(
    "hole,board",
    [
        ((), ()),
        ((0, 1), (2,)),
        ((0, 1), (0, 2, 3)),
        ((False, 1), ()),
        ((np.int64(0), 1), ()),
        ((0, 52), ()),
    ],
)
def test_repeat_invalid_canonical_error(hole: Any, board: Any) -> None:
    original = potential.canonical_cards
    with pytest.raises((ValueError, TypeError)) as expected:
        original(hole, board)
    with support.hooks(CONFIG, enabled=True) as cache:
        for _ in range(2):
            with pytest.raises(type(expected.value)) as actual:
                potential.canonical_cards(hole, board)
            assert str(actual.value) == str(expected.value)
    assert cache["canonical"].summary()["errors"] == 2


def test_lists_iterators_keywords_and_tuple_subclass_fall_back() -> None:
    hand = cards("As Ad Ac 7h 7s")
    expected = evaluator.evaluate_best(hand)

    class Tuple(tuple[int, ...]):
        pass

    with support.hooks(CONFIG, enabled=True) as cache:
        for value in (list(hand), iter(hand), Tuple(hand)):
            assert evaluator.evaluate_best(value) == expected
        assert evaluator.evaluate_best(cards=hand) == expected
        assert potential.canonical_cards(
            hole=hand[:2], board=hand[2:]
        ) == potential.canonical_cards(hand[:2], hand[2:])
    assert cache["rank"].summary()["fallbacks"] == 4
    assert cache["canonical"].summary()["fallbacks"] == 1


@pytest.mark.parametrize("enabled", [False, True])
def test_bounded_lru_eviction_and_accounting(enabled: bool) -> None:
    c = dict(CONFIG, canonical_maxsize=2, rank_maxsize=2)
    with support.hooks(c, enabled=enabled) as stores:
        for index in (0, 1, 0, 2, 1, 3):
            evaluator.evaluate_best((index, 8, 12, 16, 20))
            potential.canonical_cards((index, 8), ())
    saved = {k: v.summary() for k, v in stores.items()}
    support.check_summary(saved, c, enabled)
    for row in saved.values():
        assert row["requests"] == 6
        assert row["hits"] == (1 if enabled else 0)
        assert row["evictions"] == (3 if enabled else 0)
        assert row["size"] == (2 if enabled else 0)


@pytest.mark.parametrize("which", ["canonical", "rank"])
def test_changed_dependency_cannot_hit_old_result(
    which: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = potential if which == "canonical" else evaluator
    with support.hooks(CONFIG, enabled=True) as stores:

        def call() -> Any:
            return (
                potential.canonical_cards((0, 1), ())
                if which == "canonical"
                else evaluator.evaluate_best((0, 4, 8, 12, 16, 20))
            )

        call()

        def reject(*args: Any, **kwargs: Any) -> Any:
            raise ValueError("changed dependency")

        with monkeypatch.context() as local:
            local.setattr(module, "cards_to_mask", reject)
            with pytest.raises(ValueError, match="changed dependency"):
                call()
        call()
    assert stores[which].summary()["fallbacks"] == 1
    assert stores[which].summary()["hits"] == 1


def test_changed_suit_constant_falls_back(monkeypatch: pytest.MonkeyPatch) -> None:
    original = potential.canonical_cards
    with support.hooks(CONFIG, enabled=True) as cache:
        expected = potential.canonical_cards((5, 8), (12, 16, 20))
        with monkeypatch.context() as local:
            local.setattr(potential, "SUIT_PERMUTATIONS", ((0, 1, 2, 3),))
            assert potential.canonical_cards((5, 8), (12, 16, 20)) == original(
                (5, 8), (12, 16, 20)
            )
        assert potential.canonical_cards((5, 8), (12, 16, 20)) == expected
    assert cache["canonical"].summary()["fallbacks"] == 1


def test_aliases_late_import_nested_scope_and_failure_restoration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from poker_ai import engine, equity

    original = evaluator.evaluate_best
    canonical = potential.canonical_cards
    late = ModuleType("poker_ai._card_cache_fixture")
    monkeypatch.setitem(sys.modules, late.__name__, late)
    with pytest.raises(ValueError, match="fixture"):
        with support.hooks(CONFIG, enabled=True):
            assert (
                vars(engine)["evaluate_best"]
                is vars(equity)["evaluate_best"]
                is evaluator.evaluate_best
            )
            vars(late)["rank"] = evaluator.evaluate_best
            vars(late)["canonical"] = potential.canonical_cards
            with pytest.raises(RuntimeError, match="nested"):
                with support.hooks(CONFIG, enabled=True):
                    pass
            raise ValueError("fixture")
    assert (
        vars(engine)["evaluate_best"]
        is vars(equity)["evaluate_best"]
        is evaluator.evaluate_best
        is vars(late)["rank"]
        is original
    )
    assert vars(late)["canonical"] is potential.canonical_cards is canonical


def test_potential_rng_and_complete_engine_hand_unchanged() -> None:
    def execute(enabled: bool) -> tuple[Any, ...]:
        rng = default_rng(20261113)
        with support.hooks(CONFIG, enabled=enabled):
            feature = potential.estimate_potential(
                (0, 4),
                (8, 12, 17),
                config=potential.FeatureConfig(
                    runouts=2, opponent_samples=2, current_samples=4
                ),
                rng=rng,
            )
            state = new_hand((20, 20), Deck.shuffled(rng))
            sequence = []
            while not state.terminal:
                action = Action(
                    ActionKind.CHECK
                    if state.legal_actions.can_check
                    else ActionKind.CALL
                )
                state = state.apply(action)
                sequence.append((state.street, state.board, state.pot, state.stacks))
            return (
                feature,
                sequence,
                state.net_payoffs,
                copy.deepcopy(rng.bit_generator.state),
            )

    a, b = execute(False), execute(True)
    assert a[0].equity == b[0].equity and np.array_equal(
        a[0].histograms, b[0].histograms
    )
    assert a[1:] == b[1:]


@pytest.mark.parametrize(
    "field,value",
    [
        ("requests", 99),
        ("hits", True),
        ("size", 999999),
        ("evictions", 1),
        ("enabled", False),
        ("fallbacks", 2),
        ("errors", 2),
        ("maximum", 1),
    ],
)
def test_malformed_summary_rejected(field: str, value: Any) -> None:
    with support.hooks(CONFIG, enabled=True) as cache:
        evaluator.evaluate_best((0, 4, 8, 12, 16))
    saved = {k: v.summary() for k, v in cache.items()}
    saved["rank"][field] = value
    with pytest.raises(ArithmeticError, match="accounting"):
        support.check_summary(saved, CONFIG, True)


def fixtures() -> tuple[dict[str, Any], dict[str, Any]]:
    saved = json.loads(
        (ROOT / "results/compact-cached-learning/cost/0/native.json").read_text()
    )
    reads = []
    for name in (
        "results/compact-cached-learning/software/own.json",
        *["results/compact-cached-learning/cost/0/own.json"] * 2,
    ):
        own = json.loads((ROOT / name).read_text())
        reads.append(dict(scope=own["scope"], computed=own["own_replay"]))
    identity = tool.base.identity(saved, reads)
    result = []
    for mode in CONFIG["order"]:
        with support.hooks(CONFIG, enabled=mode == "cached") as cache:
            for _ in range(2):
                evaluator.evaluate_best((0, 4, 8, 12, 16))
                potential.canonical_cards((0, 4), ())
        result.append(
            dict(
                status="complete_card_cache_audit",
                mode=mode,
                base_admission_rejected=True,
                source=dict(sha256={"fixture": "source"}),
                config_sha256=tool.CONFIG_SHA,
                identity=copy.deepcopy(identity),
                card_cache={k: v.summary() for k, v in cache.items()},
            )
        )
    return result[0], result[1]


def test_pair_complete_exact_identity() -> None:
    a, b = fixtures()
    assert (
        tool.pair_identity(a, b, CONFIG)["status"]
        == "same_complete_audit_with_parent_card_reuse"
    )


@pytest.mark.parametrize(
    "damage",
    [
        "score",
        "read",
        "worker",
        "source",
        "config",
        "mode",
        "admission",
        "counters",
        "no_hits",
    ],
)
def test_pair_cannot_hide_changes(damage: str) -> None:
    a, b = fixtures()
    if damage == "score":
        b["identity"]["profiles"].pop()
    elif damage == "read":
        b["identity"]["computed_replays"].pop()
    elif damage == "worker":
        b["identity"]["worker_summaries"].pop()
    elif damage == "source":
        b["source"]["sha256"] = {}
    elif damage == "config":
        b["config_sha256"] = "changed"
    elif damage == "mode":
        b["mode"] = "uncached"
    elif damage == "admission":
        b["base_admission_rejected"] = False
    elif damage == "counters":
        b["card_cache"]["rank"]["requests"] += 1
    else:
        b["card_cache"] = a["card_cache"]
    with pytest.raises(ArithmeticError):
        tool.pair_identity(a, b, CONFIG)


def test_contract_source_checks_and_partial_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / tool.CONFIG
    path.parent.mkdir()
    path.write_text("{}")
    with pytest.raises(ArithmeticError, match="contract"):
        tool.contract(tmp_path)
    path = tmp_path / tool.FOLDER / "checks.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(dict(checks=[], source_fingerprint="fixture")))
    with pytest.raises(ArithmeticError, match="six exact-source"):
        tool.checked(tmp_path, dict(fingerprint="fixture"))
    monkeypatch.setattr(
        tool,
        "preflight",
        lambda *a, **k: (_ for _ in ()).throw(ArithmeticError("fixture failure")),
    )
    with pytest.raises(ArithmeticError, match="fixture failure"):
        tool.child(ROOT, "cached", tmp_path, time.perf_counter())
    saved = json.loads((tmp_path / "child.json").read_text())
    assert saved["status"] == "failed_retained" and saved["admission_evidence"] is False


@pytest.mark.parametrize(
    "log",
    [
        "requested3.12.15; Installed Python3.12.15",
        "Using CPython 3.12.3\nACTUAL_PYTHON=3.12.15\nACTUAL_NUMPY=2.5.4",
        "Using CPython 3.12.15\nACTUAL_PYTHON=3.12.3\nACTUAL_NUMPY=2.5.4",
        "Using CPython 3.12.15\nACTUAL_PYTHON=3.12.15\nACTUAL_NUMPY=2.4.6",
        "Using CPython 3.12.15\nUsing CPython 3.12.3\n"
        "ACTUAL_PYTHON=3.12.15\nACTUAL_NUMPY=2.5.4",
    ],
)
def test_host_labels_cannot_replace_actual_runtime(log: str) -> None:
    with pytest.raises(ArithmeticError, match="actual hosted runtime"):
        tool.actual_host_runtime(log, "3.12.15", "2.5.4")


def test_actual_host_guard_and_uv_agree() -> None:
    tool.actual_host_runtime(
        "\ufeffUsing CPython 3.12.15\nACTUAL_PYTHON=3.12.15\nACTUAL_NUMPY=2.5.4",
        "3.12.15",
        "2.5.4",
    )


def test_historical_source_mismatch_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        tool.base, "preflight", lambda *a, **k: (CONFIG, dict(fingerprint="changed"))
    )
    with pytest.raises(ArithmeticError, match="historical source"):
        tool.preflight(ROOT)


def test_changed_transitive_card_validation_falls_back(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import poker_ai.cards as card_module

    with support.hooks(CONFIG, enabled=True) as cache:
        evaluator.evaluate_best((0, 4, 8, 12, 16))

        def reject(*args: Any, **kwargs: Any) -> Any:
            raise ValueError("changed card validation")

        with monkeypatch.context() as local:
            local.setattr(card_module, "card_bit", reject)
            with pytest.raises(ValueError, match="changed card validation"):
                evaluator.evaluate_best((0, 4, 8, 12, 16))
    assert cache["rank"].summary()["fallbacks"] == 1
