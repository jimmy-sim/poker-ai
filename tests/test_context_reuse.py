"""Own exact graph/call correctness; no solver, training, or speed claims."""

import dataclasses
import json
import shutil
import struct
import threading
from pathlib import Path
from typing import Any
from unittest.mock import patch

import context_reuse_support as tool
import numpy as np
import pytest

from poker_ai.evaluation.compact_sampled_inputs import game_contexts
from poker_ai.postflop.compact_full_context import Context
from poker_ai.postflop.game import load_spot
from poker_ai.postflop.matrix import MatrixTree
from poker_ai.postflop.tree import SpotTree

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def contexts() -> dict[tuple[str, str], Context]:
    return game_contexts(ROOT, "software")


@pytest.mark.parametrize("dtype", [np.bool_, np.int64, np.float64])
@pytest.mark.parametrize("layout", ["C", "F", "view", "readonly", "empty", "scalar"])
def test_exact_array_bits_flags_and_storage(dtype: Any, layout: str) -> None:
    value = (
        np.arange(12)
        .astype(dtype)
        .reshape(3, 4)
        .copy(order="F" if layout == "F" else "C")
    )
    if layout == "view":
        value = value.view()
    if layout == "readonly":
        value.setflags(write=False)
    if layout == "empty":
        value = value[:0]
    if layout == "scalar":
        value = np.array(0, dtype=dtype)
    copied = tool.isolated_clone(value)
    assert tool.witness(value) == tool.witness(copied)
    assert not np.shares_memory(value, copied)
    assert tool.array_layout(value) == tool.array_layout(copied)
    if value.size and value.flags.writeable:
        copied.flat[0] = not bool(value.flat[0])
        assert copied.flat[0] != value.flat[0]


def test_float_bit_patterns_and_type_are_preserved() -> None:
    values = [0.0, -0.0, float("inf"), float("-inf")]
    values += [struct.unpack(">d", bytes.fromhex("7ff8000000000007"))[0]]
    for value in values:
        copied = tool.isolated_clone([value, np.float64(value)])
        assert tool.witness([value, np.float64(value)]) == tool.witness(copied)
    assert tool.witness(0.0) != tool.witness(-0.0)
    assert tool.witness(1) != tool.witness(True)
    assert tool.witness(1.0) != tool.witness(np.float64(1.0))


@pytest.mark.parametrize(
    "bad",
    [
        np.arange(10)[::2],
        np.array([object()]),
        np.zeros(2, dtype=np.int32),
        np.zeros(2, dtype=[("a", "i8")]),
        np.zeros(2).astype(">f8"),
        {1, 2},
        object(),
    ],
)
def test_unsupported_graphs_reject(bad: Any) -> None:
    with pytest.raises(ArithmeticError, match="unsupported"):
        tool.isolated_clone(bad)


def test_cycles_and_distinct_overlapping_views_reject() -> None:
    cyclic: list[Any] = []
    cyclic.append(cyclic)
    with pytest.raises(ArithmeticError, match="cyclic"):
        tool.isolated_clone(cyclic)
    array = np.arange(6, dtype=np.int64)
    with pytest.raises(ArithmeticError, match="overlapping"):
        tool.isolated_clone([array, array.view()])


def test_alias_topology_is_preserved_and_witnessed() -> None:
    array = np.ones(3)
    inner = {"a": array}
    original = [inner, inner, array, (array,)]
    copied = tool.isolated_clone(original)
    assert copied[0] is copied[1]
    assert copied[0]["a"] is copied[2] is copied[3][0]
    assert copied[0] is not inner
    assert tool.witness(original) != tool.witness([inner, dict(inner), array, (array,)])
    copied[0]["new"] = 7
    copied[2][0] = 19
    assert "new" not in inner and array[0] == 1


def test_complete_actual_factory_graph_is_isolated(contexts: Any) -> None:
    copied = tool.isolated_clone(contexts)
    assert tool.witness(contexts) == tool.witness(copied)
    a, b = list(contexts.values()), list(copied.values())
    assert a[0].scoring.exact is a[5].scoring.exact
    assert b[0].scoring.exact is b[5].scoring.exact
    assert a[0].scoring.exact is not b[0].scoring.exact
    b[0].diagnostics["new"] = 4
    b[0].scoring.exact.terminal_values[:] = 42
    assert "new" not in a[0].diagnostics
    assert not np.all(a[0].scoring.exact.terminal_values == 42)


@pytest.mark.parametrize("field", [f.name for f in dataclasses.fields(Context)])
def test_every_context_field_enters_witness(contexts: Any, field: str) -> None:
    original = next(iter(contexts.values()))
    copied = tool.isolated_clone(original)
    previous = tool.witness(copied)
    if field == "scoring":
        copied.scoring.exact_to_partition[0] += 1
    elif field == "diagnostics":
        copied.diagnostics["extra"] = 1
    else:
        object.__setattr__(copied, field, 7 if field == "pot" else "changed")
    assert tool.witness(copied) != previous


def test_nested_matrix_spot_engine_and_rules_all_enter_witness() -> None:
    matrix = MatrixTree.build(
        SpotTree.build(load_spot(ROOT / "configs/learning-spots/dev_low_oop.json"))
    )
    copied = tool.isolated_clone(matrix)
    assert tool.witness(matrix) == tool.witness(copied)
    assert copied.source is not matrix.source
    assert copied.source.spot is copied.source.states[0].spot
    for path in (
        "spot",
        "states",
        "children",
        "information",
        "representatives",
        "keys",
        "owners",
        "menus",
        "chance_probabilities",
        "payoffs",
    ):
        altered = tool.isolated_clone(copied)
        object.__setattr__(altered.source, path, None)
        assert tool.witness(altered) != tool.witness(copied)
    dealer = next(s.dealer for s in copied.source.states if s.dealer is not None)
    before = tool.witness(copied)
    object.__setattr__(dealer.deck, "cards", ())
    assert tool.witness(copied) != before
    assert next(
        s.dealer for s in matrix.source.states if s.dealer is not None
    ).deck.cards


def test_extra_instance_fields_and_unknown_subclasses_reject(contexts: Any) -> None:
    value = tool.isolated_clone(next(iter(contexts.values())))
    object.__setattr__(value, "unexpected", 1)
    with pytest.raises(ArithmeticError, match="attributes"):
        tool.witness(value)

    class Unknown(np.ndarray):
        pass

    with pytest.raises(ArithmeticError, match="unsupported"):
        tool.witness(np.ones(2).view(Unknown))


def requests(session: tool.Session) -> tuple[Any, Any, Any]:
    a = session.dictionary("sampled_dictionary", ROOT, "software")
    b = session.dictionary("full_dictionary", ROOT, "software")
    c = list(session.iterator(ROOT, software=True))
    return a, b, c


@pytest.mark.parametrize("enabled", [False, True])
def test_two_root_inventory_and_no_cross_root_reuse(enabled: bool) -> None:
    session = tool.Session(enabled=enabled)
    with session.hooks():
        for _ in range(2):
            with session.root(ROOT, True):
                a, b, c = requests(session)
                assert tool.witness(a) == tool.witness(b)
                assert tool.witness(list(a.values())) == tool.witness(c)
            assert session.template is None
    state = session.state()
    assert state["facts"] == dict(
        roots=2,
        requests=6,
        materializations=2 if enabled else 4,
        original_iterators=0 if enabled else 2,
        misses=2 if enabled else 0,
        hits=4 if enabled else 0,
        input_guards=6 if enabled else 0,
        template_clones=2 if enabled else 0,
        return_clones=4 if enabled else 0,
    )
    assert len(state["rows"]) == 8 and len(state["events"]) == 16
    assert all(r["status"] == "complete" for r in state["rows"])
    assert state["restored"] and state["final_entries"] == 0
    assert not state["cleanup_failures"]


def test_caller_mutations_do_not_contaminate_template_or_next_return() -> None:
    session = tool.Session(enabled=True)
    with session.root(ROOT, True):
        a = session.dictionary("sampled_dictionary", ROOT, "software")
        before = tool.witness(a)
        first = next(iter(a.values()))
        first.scoring.exact.terminal_values[:] = 99
        first.diagnostics.clear()
        a.clear()
        b = session.dictionary("full_dictionary", ROOT, "software")
        assert tool.witness(b) == before
        next(iter(b.values())).scoring.exact.legal[:] = 0
        c = list(session.iterator(ROOT, software=True))
        assert all(np.any(x.scoring.exact.legal) for x in c)


@pytest.mark.parametrize("where", ["before_reuse", "exit", "exceptional_exit"])
def test_template_mutation_rejects_and_clears(where: str) -> None:
    session = tool.Session(enabled=True)
    primary = RuntimeError("preserve me")
    with pytest.raises(
        RuntimeError if where == "exceptional_exit" else ArithmeticError
    ) as caught:
        with session.root(ROOT, True):
            session.dictionary("sampled_dictionary", ROOT, "software")
            assert session.template is not None
            next(iter(session.template.values())).diagnostics.clear()
            if where == "before_reuse":
                session.dictionary("full_dictionary", ROOT, "software")
            if where == "exceptional_exit":
                raise primary
    if where == "exceptional_exit":
        assert caught.value is primary
    assert session.template is None and session.cleanup_failures
    assert session.rows[0]["status"] == "primary_failed"


def test_failed_factory_has_no_entry_and_original_exception_identity() -> None:
    session = tool.Session(enabled=True)
    error = RuntimeError("factory sentinel")

    def fail(*args: Any, **kwargs: Any) -> Any:
        raise error

    session.factory = fail
    with pytest.raises(RuntimeError) as caught, session.root(ROOT, True):
        session.dictionary("sampled_dictionary", ROOT, "software")
    assert caught.value is error and session.template is None
    assert session.facts["misses"] == 0


@pytest.mark.parametrize("bad", ["root", "scope", "order", "kwargs", "fourth"])
def test_mismatched_requests_reject(bad: str) -> None:
    session = tool.Session(enabled=True)
    with session.root(ROOT, True):
        if bad == "fourth":
            requests(session)
        with pytest.raises(ArithmeticError):
            if bad == "kwargs":
                session.dictionary("sampled_dictionary", ROOT, scope="software")
            else:
                session.dictionary(
                    "full_dictionary" if bad == "order" else "sampled_dictionary",
                    ROOT.parent if bad == "root" else ROOT,
                    "real" if bad == "scope" else "software",
                )


@pytest.mark.parametrize("partial", ["unconsumed", "one", "closed"])
def test_lazy_partial_and_late_iterators_reject_without_false_completion(
    partial: str,
) -> None:
    session = tool.Session(enabled=True)
    iterator: Any = None
    if partial == "unconsumed":
        with session.root(ROOT, True):
            session.dictionary("sampled_dictionary", ROOT, "software")
            session.dictionary("full_dictionary", ROOT, "software")
            iterator = session.iterator(ROOT, software=True)
            assert session.facts["requests"] == 2
        with pytest.raises(ArithmeticError, match="outlived"):
            next(iterator)
    else:
        with pytest.raises(ArithmeticError), session.root(ROOT, True):
            session.dictionary("sampled_dictionary", ROOT, "software")
            session.dictionary("full_dictionary", ROOT, "software")
            iterator = session.iterator(ROOT, software=True)
            next(iterator)
            if partial == "closed":
                iterator.close()
        assert session.template is None
        iterator.close()
        assert session.cleanup_failures
        assert session.rows[0]["status"] == "primary_failed"


def test_outside_calls_preserve_lazy_forwarding_and_exception_identity() -> None:
    session = tool.Session(enabled=True)
    marker = object()

    def factory(*args: Any, **kwargs: Any) -> Any:
        assert args == (marker,) and kwargs == {"token": marker}
        return marker

    session.factory = factory
    assert session.dictionary("not_selected", marker, token=marker) is marker
    entered: list[bool] = []

    def lazy(*args: Any, **kwargs: Any) -> Any:
        entered.append(True)
        yield marker

    session.iterator_factory = lazy
    result = session.iterator(marker, token=marker)
    assert not entered and next(result) is marker
    assert not session.rows


def test_changed_real_pinned_input_is_rechecked_on_cache_hit(tmp_path: Path) -> None:
    relative = "configs/compact-public-range.json"
    config = json.loads((ROOT / relative).read_text())
    for name in [relative, *config["input_sha256"]]:
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    session = tool.Session(enabled=True)
    with session.root(tmp_path, True):
        session.dictionary("sampled_dictionary", tmp_path, "software")
        target = tmp_path / next(iter(config["input_sha256"]))
        target.write_bytes(target.read_bytes() + b" ")
        with pytest.raises(ArithmeticError, match="input hash changed"):
            session.dictionary("full_dictionary", tmp_path, "software")
        assert session.facts["hits"] == 0


def test_owner_nesting_and_cap_reject() -> None:
    session = tool.Session(enabled=True)
    with session.root(ROOT, True):
        with pytest.raises(ArithmeticError):
            with session.root(ROOT, True):
                pass
        errors = []

        def other() -> None:
            try:
                session.dictionary("sampled_dictionary", ROOT, "software")
            except ArithmeticError as error:
                errors.append(error)

        thread = threading.Thread(target=other)
        thread.start()
        thread.join()
        assert len(errors) == 1
        with (
            patch("os.getpid", return_value=-1),
            pytest.raises(ArithmeticError),
        ):
            session.dictionary("sampled_dictionary", ROOT, "software")
    with pytest.raises(ArithmeticError):
        tool.Session(enabled=True, maximum=33)
    bounded = tool.Session(enabled=False)
    for _ in range(32):
        with bounded.root(ROOT, True):
            pass
    with pytest.raises(ArithmeticError, match="cap"), bounded.root(ROOT, True):
        pass
    assert bounded.token is None


def test_caller_hooks_keep_defining_functions_and_restore_late_aliases() -> None:
    from poker_ai.evaluation import compact_opponent_sources as source
    from poker_ai.evaluation import compact_sampled_prior as prior
    from poker_ai.postflop import compact_full_context as defining

    original = defining.contexts
    session = tool.Session(enabled=True)
    with session.hooks():
        vars(tool)["late_module"] = vars(source)["sampled_parent"]
        vars(tool)["late_iterator"] = vars(prior)["contexts"]
        assert defining.contexts is original
    assert vars(tool)["late_module"] is not None
    assert vars(tool)["late_iterator"] is original
    assert session.restored
    delattr(tool, "late_module")
    delattr(tool, "late_iterator")
    with pytest.raises(ArithmeticError), session.hooks():
        pass


@pytest.mark.parametrize("phase", ["start", "end"])
def test_event_sink_failure_retains_partial_rows_and_clears(phase: str) -> None:
    error = OSError("sink sentinel")

    def sink(event: dict[str, Any]) -> None:
        if event["phase"] == phase:
            raise error

    session = tool.Session(enabled=True, sink=sink)
    with pytest.raises(OSError) as caught, session.hooks(), session.root(ROOT, True):
        session.dictionary("sampled_dictionary", ROOT, "software")
    assert caught.value is error
    assert session.template is None and session.token is None and session.restored
    assert session.rows


@pytest.fixture(scope="module")
def completed_state() -> dict[str, Any]:
    session = tool.Session(enabled=True)
    with session.hooks():
        for _ in range(2):
            with session.root(ROOT, True):
                requests(session)
    return session.state()


@pytest.mark.parametrize(
    "damage",
    [
        None,
        "count",
        "bool_count",
        "entries",
        "cleanup",
        "restoration",
        "partial",
        "producer",
        "clock",
        "overlap",
        "key",
        "scope",
        "hash",
        "event_missing",
        "event_clock",
        "event_count",
        "bool_index",
        "extra_field",
    ],
)
def test_saved_session_full_schema(
    completed_state: dict[str, Any], damage: str | None
) -> None:
    import copy

    state = copy.deepcopy(completed_state)
    if damage == "count":
        state["facts"]["hits"] -= 1
    elif damage == "bool_count":
        state["facts"]["roots"] = True
    elif damage == "entries":
        state["final_entries"] = 1
    elif damage == "cleanup":
        state["cleanup_failures"].append("fixture")
    elif damage == "restoration":
        state["restored"] = False
    elif damage == "partial":
        state["rows"][3]["status"] = "running"
    elif damage == "producer":
        state["rows"][1]["before"]["pid"] += 1
    elif damage == "clock":
        state["rows"][1]["before"]["cpu"] = -1
    elif damage == "overlap":
        state["rows"][2]["before"] = copy.deepcopy(state["rows"][1]["before"])
    elif damage == "key":
        state["rows"][0]["keys"].reverse()
    elif damage == "scope":
        state["rows"][0]["software"] = False
    elif damage == "hash":
        state["rows"][1]["collection_sha256"] = "b" * 64
    elif damage == "event_missing":
        state["events"].pop()
    elif damage == "event_clock":
        state["events"][2]["clock"]["wall"] += 100
    elif damage == "event_count":
        state["events"][2]["facts"]["hits"] += 1
    elif damage == "bool_index":
        state["rows"][1]["index"] = True
    elif damage == "extra_field":
        state["rows"][0]["extra"] = True
    first = completed_state["rows"][0]
    kwargs = dict(
        enabled=True,
        pid=first["before"]["pid"],
        thread=first["before"]["thread"],
        keys=first["keys"],
        software=True,
    )
    if damage is None:
        assert len(tool.validate_session(state, **kwargs)) == 8
    else:
        with pytest.raises(ArithmeticError):
            tool.validate_session(state, **kwargs)


def test_rebound_defining_factory_or_input_guard_rejects_and_clears() -> None:
    from poker_ai.postflop import compact_full_context

    session = tool.Session(enabled=True)
    with session.hooks():
        with session.root(ROOT, True):
            session.dictionary("sampled_dictionary", ROOT, "software")
            with (
                patch.object(compact_full_context, "contexts", lambda *a: None),
                pytest.raises(ArithmeticError, match="factory changed"),
            ):
                session.dictionary("full_dictionary", ROOT, "software")
            with (
                patch.object(session, "guard", lambda *a: None),
                pytest.raises(ArithmeticError, match="guard binding"),
            ):
                session.dictionary("full_dictionary", ROOT, "software")
    assert session.restored and session.template is None


@pytest.mark.parametrize("call", ["dictionary", "iterator", "root"])
def test_event_callback_reentrancy_rejects_before_factory(call: str) -> None:
    def sink(event: dict[str, Any]) -> None:
        if event["phase"] != "start":
            return
        if call == "dictionary":
            session.dictionary("sampled_dictionary", ROOT, "software")
        elif call == "iterator":
            session.iterator(ROOT, software=True)
        else:
            with session.root(ROOT, True):
                pass

    session = tool.Session(enabled=True, sink=sink)
    with (
        pytest.raises(ArithmeticError, match="reentrancy"),
        session.hooks(),
        session.root(ROOT, True),
    ):
        pass
    assert session.facts["materializations"] == 0
    assert session.template is None and not session.emitting and session.restored


def test_root_end_event_follows_template_clearance() -> None:
    observed: list[bool] = []

    def sink(event: dict[str, Any]) -> None:
        if (
            event["phase"] == "end"
            and session.rows[event["index"]]["kind"] == "archive_root"
        ):
            observed.append(session.template is None)

    session = tool.Session(enabled=True, sink=sink)
    with session.root(ROOT, True):
        requests(session)
    assert observed == [True]
