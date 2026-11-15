"""Independent grouped-depth predicates and original constructor-bit witnesses."""

import importlib
import inspect
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

from poker_ai.abstraction.model import CardAbstraction
from poker_ai.postflop.game import load_spot
from poker_ai.postflop.matrix import MatrixTree
from poker_ai.postflop.tree import SpotTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
g = importlib.import_module("grouped_depth_support")
reader = importlib.import_module("profile_reader_loads")


@pytest.fixture(scope="module")
def source() -> SpotTree:
    return SpotTree.build(load_spot(ROOT / "configs/learning-spots/dev_low_oop.json"))


def outcome(information: list[int], depths: list[int], groups: int) -> bool:
    expected = all(
        len(
            {
                depth
                for info, depth in zip(information, depths, strict=True)
                if info == group
            }
        )
        == 1
        for group in range(groups)
    )
    a, b = np.array(information, dtype=np.int64), np.array(depths, dtype=np.int64)
    before = a.tobytes(), b.tobytes()
    a.flags.writeable = b.flags.writeable = False
    try:
        g.grouped_depths(a, b, groups)
    except ValueError as error:
        assert str(error) == g.MESSAGE
        actual = False
    else:
        actual = True
    assert actual is expected
    assert (a.tobytes(), b.tobytes()) == before
    return actual


@settings(max_examples=128, derandomize=True, deadline=None)
@given(
    st.lists(
        st.tuples(st.integers(-3, 12), st.integers(-(2**63), 2**63 - 1)), max_size=64
    ),
    st.integers(0, 8),
)
def test_grouped_matches_independent_direct_sets(
    rows: list[tuple[int, int]], groups: int
) -> None:
    outcome([x[0] for x in rows], [x[1] for x in rows], groups)


@pytest.mark.parametrize(
    ("information", "depths", "groups", "expected"),
    [
        ([], [], 0, True),
        ([], [], 1, False),
        ([0, 0, 1], [2, 2, 3], 2, True),
        ([0, 0, 1], [2, 4, 3], 2, False),
        ([0, 2], [2, 2], 3, False),
        ([-1, 0, 9], [9, 3, 8], 1, True),
        ([-(2**63), 2**63 - 1], [2, 3], 0, True),
        ([0, 0, 1], [-(2**63), -(2**63), 2**63 - 1], 2, True),
        ([0, 0], [-(2**63), 2**63 - 1], 1, False),
        ([0, 0], [2**63 - 1, 2**63 - 1], 1, True),
        ([0, 0], [-(2**63), -(2**63)], 1, True),
    ],
)
def test_depth_edge_cases(
    information: list[int], depths: list[int], groups: int, expected: bool
) -> None:
    assert outcome(information, depths, groups) is expected


@pytest.mark.parametrize(
    "kind",
    [
        "float",
        "bool",
        "uint",
        "rank",
        "shape",
        "negative",
        "count_bool",
        "count_float",
        "list",
    ],
)
def test_reject_malformed_predicate_inputs(kind: str) -> None:
    a: Any = np.array([0, 0], dtype=np.int64)
    b: Any = np.array([2, 2], dtype=np.int64)
    count: Any = 1
    if kind in ("float", "bool", "uint"):
        a = a.astype({"float": np.float64, "bool": np.bool_, "uint": np.uint64}[kind])
    elif kind == "rank":
        a = a.reshape(1, 2)
    elif kind == "shape":
        b = b[:1]
    elif kind == "negative":
        count = -1
    elif kind == "count_bool":
        count = True
    elif kind == "count_float":
        count = 1.0
    else:
        a = a.tolist()
    with pytest.raises(ValueError, match="canonical"):
        g.grouped_depths(a, b, count)


def test_noncontiguous_readonly_inputs() -> None:
    a = np.array([0, 99, 1, 99], dtype=np.int64)[::2]
    b = np.array([2, 99, 3, 99], dtype=np.int64)[::2]
    a.flags.writeable = b.flags.writeable = False
    g.grouped_depths(a, b, 2)
    assert a.tolist() == [0, 1] and b.tolist() == [2, 3]


@pytest.mark.parametrize(
    "encoding", ["exact", "legacy_b8", "public_b8", "canonical_b8", "texture_b8"]
)
def test_complete_constructor_fields_match(source: SpotTree, encoding: Any) -> None:
    model = CardAbstraction.load(ROOT / "results/card-models/potential-8.json")
    old = g.BASE_FUNCTION(MatrixTree, source, encoding, model)
    new = g.build(MatrixTree, source, encoding, model)
    assert g.matrix_witness(old, source) == g.matrix_witness(new, source)
    assert old.source is new.source is source


def test_literal_ast_body_guard() -> None:
    g.ast_equivalence()


@pytest.mark.parametrize("change", ["body", "depth", "annotation", "decorator"])
def test_ast_guard_rejects_unregistered_changes(
    monkeypatch: pytest.MonkeyPatch, change: str
) -> None:
    getsource = inspect.getsource

    def modified(function: Any) -> str:
        s = getsource(function)
        if function is g.build:
            if change == "body":
                return s.replace("width = max", "width = min")
            if change == "depth":
                return s.replace(
                    "grouped_depths(information, depths, len(keys))",
                    "grouped_depths(depths, information, len(keys))",
                )
            if change == "annotation":
                return s.replace("cls: type[MatrixTree]", "cls")
        if function is g.BASE_FUNCTION and change == "decorator":
            return s.replace("@classmethod", "@staticmethod")
        return s

    monkeypatch.setattr(g.inspect, "getsource", modified)
    with pytest.raises(ArithmeticError):
        g.ast_equivalence()


def test_changed_global_dependency_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(g, "observation_key", lambda *args: "changed")
    with pytest.raises(ArithmeticError, match="global dependency"):
        g.ast_equivalence()


@pytest.mark.parametrize("mode", ["original", "grouped"])
def test_subclass_and_existing_late_owned_aliases(
    source: SpotTree, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str
) -> None:
    class Child(MatrixTree):
        pass

    alias = ModuleType("compact_cached._depth_initial")
    vars(alias)["saved"] = Child.build
    initial = vars(alias)["saved"]
    monkeypatch.setitem(sys.modules, alias.__name__, alias)
    late = ModuleType("poker_ai._depth_late")
    monkeypatch.setitem(sys.modules, late.__name__, late)
    with g.constructor_scope(mode, tmp_path / "record", 4) as receipt:
        first = vars(alias)["saved"](source)
        vars(late)["saved"] = MatrixTree.build
        second = vars(late)["saved"](source=source)
        assert type(first) is Child and type(second) is MatrixTree
        with pytest.raises(ArithmeticError, match="changed baseline"):
            with g.constructor_scope(mode, tmp_path / "nested", 4):
                pass
    assert vars(MatrixTree)["build"] is g.BASE_DESCRIPTOR
    assert vars(alias)["saved"] is initial
    assert vars(late)["saved"].__func__ is g.BASE_FUNCTION
    assert receipt["restored"] is True and receipt["calls"] == receipt["completed"] == 2
    assert receipt["status"] == "complete" and receipt["aliases_remaining"] == 0
    rows = [
        json.loads(x)
        for x in (tmp_path / "record/constructor-events.jsonl").read_text().splitlines()
    ]
    assert [x["status"] for x in rows] == ["running", "complete", "running", "complete"]


@pytest.mark.parametrize("mode", ["original", "grouped"])
def test_primary_constructor_exception_is_preserved(
    source: SpotTree, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str
) -> None:
    module = importlib.import_module("poker_ai.postflop.matrix")
    error = RuntimeError("fictional constructor exception")

    def failed(*args: Any, **kwargs: Any) -> Any:
        raise error

    monkeypatch.setattr(module, "observation_key", failed)
    monkeypatch.setattr(g, "observation_key", failed)
    with pytest.raises(RuntimeError) as caught:
        with g.constructor_scope(mode, tmp_path / "record", 4):
            MatrixTree.build(source)
    assert caught.value is error and vars(MatrixTree)["build"] is g.BASE_DESCRIPTOR
    x = json.loads((tmp_path / "record/constructor.json").read_text())
    assert (
        x["status"] == "failed_retained"
        and x["primary_failures"] == 1
        and x["restored"]
    )


def test_capacity_failure_retained(source: SpotTree, tmp_path: Path) -> None:
    with pytest.raises(ArithmeticError, match="capacity"):
        with g.constructor_scope("grouped", tmp_path / "record", 1):
            MatrixTree.build(source)
            MatrixTree.build(source)
    x = json.loads((tmp_path / "record/constructor.json").read_text())
    assert x["calls"] == x["completed"] == 1 and x["errors"] == 1 and x["restored"]
    assert x["status"] == "failed_retained"


def test_foreign_thread_rejected(source: SpotTree, tmp_path: Path) -> None:
    errors: list[BaseException] = []

    def foreign() -> None:
        try:
            MatrixTree.build(source)
        except BaseException as error:
            errors.append(error)

    with g.constructor_scope("grouped", tmp_path / "record", 4) as receipt:
        thread = threading.Thread(target=foreign)
        thread.start()
        thread.join()
    assert len(errors) == 1 and isinstance(errors[0], ArithmeticError)
    assert receipt["status"] == "failed_retained" and receipt["errors"] == 1
    assert receipt["calls"] == 0 and receipt["restored"]


def test_scope_body_exception_restores(source: SpotTree, tmp_path: Path) -> None:
    error = KeyboardInterrupt("fictional stop")
    with pytest.raises(KeyboardInterrupt) as caught:
        with g.constructor_scope("grouped", tmp_path / "record", 4):
            MatrixTree.build(source)
            raise error
    assert caught.value is error and vars(MatrixTree)["build"] is g.BASE_DESCRIPTOR
    assert (
        json.loads((tmp_path / "record/constructor.json").read_text())["status"]
        == "failed_retained"
    )


def test_same_sparse_collector_can_wrap_both_builder_modes(
    source: SpotTree, tmp_path: Path
) -> None:
    for mode in ("original", "grouped"):
        regions = reader.coarse.Regions(16)
        regions.active = True
        regions.read_index = 0
        selected: dict[str, Any] = {}
        with g.constructor_scope(mode, tmp_path / mode, 4) as receipt:
            with reader.extension(), reader.coarse.selected_hooks(regions, selected):
                MatrixTree.build(source)
        assert regions.total == 1 and len(regions.rows) == 1
        assert regions.rows[0]["status"] == "complete"
        assert (
            selected["restored"] and receipt["restored"] and receipt["completed"] == 1
        )
        assert vars(MatrixTree)["build"] is g.BASE_DESCRIPTOR


@pytest.mark.parametrize("change", ["bits", "shape", "strides", "readonly", "dtype"])
def test_field_witness_detects_representation_changes(change: str) -> None:
    a = np.array([1.0, -0.0, 3.0, 4.0], dtype=np.float64)
    before = g.field_value(a)
    if change == "bits":
        a[1] = 0.0
    elif change == "shape":
        a = a.reshape(2, 2)
    elif change == "strides":
        a = np.repeat(a, 2)[::2]
    elif change == "readonly":
        a.flags.writeable = False
    else:
        a = a.view(np.int64)
    assert g.field_value(a) != before


def test_object_array_not_a_bit_witness() -> None:
    with pytest.raises(ArithmeticError, match="object array"):
        g.field_value(np.array([object()], dtype=object))


def test_source_identity_cannot_be_replaced(source: SpotTree) -> None:
    import copy

    matrix = g.build(MatrixTree, source)
    with pytest.raises(ArithmeticError, match="source object"):
        g.matrix_witness(matrix, copy.copy(source))


@pytest.mark.parametrize("mode", ["original", "grouped"])
def test_original_early_constructor_failures_match(source: SpotTree, mode: str) -> None:
    call = g.BASE_FUNCTION if mode == "original" else g.build
    with pytest.raises(ValueError, match="unknown/missing representation model"):
        call(MatrixTree, source, "unknown", None)


def test_failed_field_observation_retains_missing_completion(
    source: SpotTree, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    error = RuntimeError("fictional witness failure")

    def failed(*args: Any, **kwargs: Any) -> Any:
        raise error

    monkeypatch.setattr(g, "matrix_witness", failed)
    with pytest.raises(RuntimeError) as caught:
        with g.constructor_scope("grouped", tmp_path / "record", 4):
            MatrixTree.build(source)
    assert caught.value is error
    x = json.loads((tmp_path / "record/constructor.json").read_text())
    assert x["calls"] == 1 and x["completed"] == 0 and x["errors"] == 1
    assert x["restored"] and x["status"] == "failed_retained"
    events = (tmp_path / "record/constructor-events.jsonl").read_text().splitlines()
    assert len(events) == 1 and json.loads(events[0])["status"] == "running"


def test_primary_survives_failed_failure_record(
    source: SpotTree, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    error = RuntimeError("fictional primary")
    module = importlib.import_module("poker_ai.postflop.matrix")
    encode = g.canonical

    def failed(*args: Any, **kwargs: Any) -> Any:
        raise error

    def encode_except_failure(row: Any) -> bytes:
        if isinstance(row, dict) and row.get("status") == "primary_failed":
            raise OSError("fictional event write failure")
        return bytes(encode(row))

    monkeypatch.setattr(module, "observation_key", failed)
    monkeypatch.setattr(g, "observation_key", failed)
    monkeypatch.setattr(g, "canonical", encode_except_failure)
    with pytest.raises(RuntimeError) as caught:
        with g.constructor_scope("original", tmp_path / "record", 4):
            MatrixTree.build(source)
    assert caught.value is error and vars(MatrixTree)["build"] is g.BASE_DESCRIPTOR
    x = json.loads((tmp_path / "record/constructor.json").read_text())
    assert x["status"] == "failed_retained" and x["errors"] == 1 and x["restored"]


def test_changed_descriptor_rejected_before_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(MatrixTree, "build", classmethod(lambda *args: None))
    with pytest.raises(ArithmeticError, match="changed baseline"):
        with g.constructor_scope("original", tmp_path / "record", 4):
            pass
    assert not (tmp_path / "record").exists()


def test_compact_tuple_witness_hashes_every_value_and_type() -> None:
    value = tuple((i, i + 1) for i in range(1000))
    old = g.field_value(value)
    assert old["length"] == 1000 and len(g.canonical(old)) < 200
    changed = list(value)
    changed[997] = (997, 999)
    assert g.field_value(tuple(changed)) != old
    assert g.field_value((1,)) != g.field_value((1.0,))
    assert g.field_value(((1,),)) != g.field_value((1,))
    with pytest.raises(ArithmeticError, match="unsupported"):
        g.field_value(([1],))


def test_read_complete_constructor_records_without_building(
    source: SpotTree, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    with g.constructor_scope("grouped", tmp_path / "record", 4) as receipt:
        MatrixTree.build(source)
    monkeypatch.setattr(
        MatrixTree,
        "build",
        classmethod(lambda *args: pytest.fail("data parser constructed matrix")),
    )
    result = g.read_constructors(
        tmp_path / "record", "grouped", 4, receipt["pid"], receipt["thread"]
    )
    assert len(result) == 1 and len(result[0]) == 64


@pytest.mark.parametrize(
    "key",
    [
        "maximum",
        "calls",
        "completed",
        "errors",
        "primary_failures",
        "aliases_remaining",
    ],
)
def test_boolean_counters_are_not_integer_proof(
    source: SpotTree, tmp_path: Path, key: str
) -> None:
    with g.constructor_scope("grouped", tmp_path / "record", 1) as receipt:
        MatrixTree.build(source)
    p = tmp_path / "record/constructor.json"
    raw = json.loads(p.read_text())
    raw[key] = bool(raw[key])
    p.write_text(json.dumps(raw))
    with pytest.raises(ArithmeticError):
        g.read_constructors(
            tmp_path / "record", "grouped", 1, receipt["pid"], receipt["thread"]
        )


@pytest.mark.parametrize(
    "change",
    ["order", "missing", "failed", "field", "fingerprint", "class", "source_identity"],
)
def test_changed_constructor_records_fail_even_after_event_rehash(
    source: SpotTree, tmp_path: Path, change: str
) -> None:
    import hashlib

    with g.constructor_scope("original", tmp_path / "record", 4) as receipt:
        MatrixTree.build(source)
    path = tmp_path / "record/constructor-events.jsonl"
    rows = [json.loads(x) for x in path.read_text().splitlines()]
    if change == "order":
        rows.reverse()
    elif change == "missing":
        rows.pop()
    elif change == "failed":
        rows[1]["status"] = "primary_failed"
    else:
        witness = rows[1]["witness"]
        if change == "field":
            witness["fields"].pop("children")
        elif change == "fingerprint":
            witness["fingerprint"] = "0" * 64
        elif change == "class":
            witness["matrix_class"] = "other.MatrixTree"
        else:
            witness["source_is_exact_input"] = False
        if change != "fingerprint":
            witness["fingerprint"] = hashlib.sha256(
                g.canonical({k: v for k, v in witness.items() if k != "fingerprint"})
            ).hexdigest()
    data = b"\n".join(g.canonical(x) for x in rows) + b"\n"
    path.write_bytes(data)
    p = tmp_path / "record/constructor.json"
    raw = json.loads(p.read_text())
    raw["events_sha256"] = hashlib.sha256(data).hexdigest()
    p.write_text(json.dumps(raw))
    with pytest.raises(ArithmeticError):
        g.read_constructors(
            tmp_path / "record", "original", 4, receipt["pid"], receipt["thread"]
        )


@pytest.mark.parametrize(
    "change", ["flag", "shape", "dtype", "digest", "extra", "missing"]
)
def test_reject_malformed_array_field_metadata(change: str) -> None:
    value = g.field_value(np.array([1, 2], dtype=np.int64))
    if change == "flag":
        value["flags"]["WRITEABLE"] = 1
    elif change == "shape":
        value["shape"] = [True]
    elif change == "dtype":
        value["dtype"] = "O"
    elif change == "digest":
        value["sha256"] = "Z" * 64
    elif change == "extra":
        value["extra"] = None
    else:
        value.pop("strides")
    with pytest.raises(ArithmeticError):
        g.validate_field(value)
