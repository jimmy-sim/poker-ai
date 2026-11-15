"""Literal-constructor parity, phase accounting and retained negative software cases."""

import importlib
import inspect
import json
import sys
import threading
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from poker_ai.abstraction.model import CardAbstraction
from poker_ai.postflop.game import load_spot
from poker_ai.postflop.matrix import MatrixTree
from poker_ai.postflop.tree import SpotTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
p = importlib.import_module("matrix_phase_support")
g = importlib.import_module("grouped_depth_support")
reader = importlib.import_module("profile_reader_loads")


@pytest.fixture(scope="module")
def source() -> SpotTree:
    return SpotTree.build(load_spot(ROOT / "configs/learning-spots/dev_low_oop.json"))


@pytest.mark.parametrize(
    "encoding", ["exact", "legacy_b8", "public_b8", "canonical_b8", "texture_b8"]
)
def test_full_fields_and_five_disjoint_phases(
    source: SpotTree, tmp_path: Path, encoding: Any
) -> None:
    model = CardAbstraction.load(ROOT / "results/card-models/potential-8.json")
    original = g.BASE_FUNCTION(MatrixTree, source, encoding, model)
    with p.constructor_scope("phased", tmp_path / "capture", 2) as receipt:
        actual = MatrixTree.build(source, encoding, model)
    assert g.matrix_witness(original, source) == g.matrix_witness(actual, source)
    assert (
        len(
            g.read_constructors(
                tmp_path / "capture", "phased", 2, receipt["pid"], receipt["thread"]
            )
        )
        == 1
    )
    rows = p.read_phases(tmp_path / "capture", 1, 2, receipt["pid"], receipt["thread"])
    assert set(rows[0]["phases"]) == set(p.PHASES)
    assert all(x >= -1e-9 for x in rows[0]["remainder"].values())
    assert p.CURRENT.get() is None and vars(MatrixTree)["build"] is p.BASE_DESCRIPTOR


def test_literal_constructor_guard() -> None:
    p.ast_equivalence()


@pytest.mark.parametrize(
    "change", ["body", "boundary", "annotation", "decorator", "globals"]
)
def test_guard_detects_undeclared_changes(
    monkeypatch: pytest.MonkeyPatch, change: str
) -> None:
    old = inspect.getsource

    def changed(function: Any) -> str:
        s = old(function)
        if function is p.build:
            if change == "body":
                return s.replace("width = max", "width = min")
            if change == "boundary":
                return s.replace('phase("array_setup")', 'phase("depth_validation")')
            if change == "annotation":
                return s.replace("cls: type[MatrixTree]", "cls")
        if function is p.BASE_FUNCTION and change == "decorator":
            return s.replace("@classmethod", "@staticmethod")
        return s

    if change == "globals":
        monkeypatch.setattr(p, "observation_key", lambda *args: "changed")
    else:
        monkeypatch.setattr(p.inspect, "getsource", changed)
    with pytest.raises(ArithmeticError):
        p.ast_equivalence()


@pytest.mark.parametrize("mode", ["original", "phased"])
def test_real_depth_rejection_and_retention(
    source: SpotTree, tmp_path: Path, mode: str
) -> None:
    synthetic = p.depth_error_fixture(source)
    with pytest.raises(ValueError, match="information set merges different depths"):
        with p.constructor_scope(mode, tmp_path / "negative", 2):
            MatrixTree.build(synthetic)
    r = json.loads((tmp_path / "negative/constructor.json").read_text())
    assert (
        r["restored"]
        and r["status"] == "failed_retained"
        and r["primary_failures"] == 1
    )
    if mode == "phased":
        events = [
            json.loads(x)
            for x in (tmp_path / "negative/phase-events.jsonl").read_text().splitlines()
        ]
        assert events[-1]["event"] == "constructor_failed"
        assert (
            events[-2]["event"] == "phase_failed"
            and events[-2]["phase"] == "depth_validation"
        )
        with pytest.raises(ArithmeticError):
            p.read_phases(tmp_path / "negative", 1, 2, r["pid"], r["thread"])


@pytest.mark.parametrize("mode", ["original", "phased"])
def test_subclass_owned_aliases_and_nested_scope(
    source: SpotTree, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str
) -> None:
    class Child(MatrixTree):
        pass

    alias = ModuleType("compact_cached._matrix_phases_initial")
    vars(alias)["saved"] = Child.build
    saved = vars(alias)["saved"]
    monkeypatch.setitem(sys.modules, alias.__name__, alias)
    late = ModuleType("poker_ai._matrix_phases_late")
    monkeypatch.setitem(sys.modules, late.__name__, late)
    with p.constructor_scope(mode, tmp_path / "capture", 4) as receipt:
        assert type(vars(alias)["saved"](source)) is Child
        vars(late)["saved"] = MatrixTree.build
        assert type(vars(late)["saved"](source=source)) is MatrixTree
        with pytest.raises(ArithmeticError):
            with p.constructor_scope(mode, tmp_path / "nested", 4):
                pass
    assert receipt["restored"] and receipt["completed"] == 2
    assert (
        vars(alias)["saved"] is saved
        and vars(late)["saved"].__func__ is p.BASE_FUNCTION
    )


def test_sparse_outer_boundary_contains_phases(
    source: SpotTree, tmp_path: Path
) -> None:
    regions = reader.coarse.Regions(16)
    regions.active = True
    regions.read_index = 0
    selected: dict[str, Any] = {}
    with p.constructor_scope("phased", tmp_path / "capture", 2) as receipt:
        with reader.extension(), reader.coarse.selected_hooks(regions, selected):
            MatrixTree.build(source)
    phases = p.read_phases(
        tmp_path / "capture", 1, 2, receipt["pid"], receipt["thread"]
    )
    assert regions.total == 1 and len(regions.rows) == 1
    assert phases[0]["total"]["cpu"] > 0 and selected["restored"]


def test_foreign_thread_and_capacity_fail_closed(
    source: SpotTree, tmp_path: Path
) -> None:
    errors = []

    def foreign() -> None:
        try:
            MatrixTree.build(source)
        except BaseException as error:
            errors.append(error)

    with p.constructor_scope("phased", tmp_path / "foreign", 1) as receipt:
        thread = threading.Thread(target=foreign)
        thread.start()
        thread.join()
    assert len(errors) == 1 and isinstance(errors[0], ArithmeticError)
    assert receipt["status"] == "failed_retained" and receipt["restored"]
    with pytest.raises(ArithmeticError, match="capacity"):
        with p.constructor_scope("phased", tmp_path / "capacity", 1):
            MatrixTree.build(source)
            MatrixTree.build(source)
    assert p.CURRENT.get() is None and vars(MatrixTree)["build"] is p.BASE_DESCRIPTOR


def test_primary_exception_survives_failed_phase_event(
    source: SpotTree, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    error = RuntimeError("fictional primary")
    mod = importlib.import_module("poker_ai.postflop.matrix")

    def failed(*args: Any, **kwargs: Any) -> Any:
        raise error

    monkeypatch.setattr(mod, "observation_key", failed)
    monkeypatch.setattr(p, "observation_key", failed)
    old = p.PhaseRecorder.emit

    def emit(self: Any, event: str, **payload: Any) -> None:
        if event == "phase_failed":
            raise OSError("fictional retention failure")
        old(self, event, **payload)

    monkeypatch.setattr(p.PhaseRecorder, "emit", emit)
    with pytest.raises(RuntimeError) as caught:
        with p.constructor_scope("phased", tmp_path / "capture", 2):
            MatrixTree.build(source)
    assert caught.value is error and p.CURRENT.get() is None
    assert vars(MatrixTree)["build"] is p.BASE_DESCRIPTOR
    assert (
        json.loads((tmp_path / "capture/phases.json").read_text())["status"]
        == "failed_retained"
    )


@pytest.mark.parametrize(
    "change",
    [
        "missing",
        "order",
        "bool",
        "pid",
        "thread",
        "negative",
        "backward",
        "nan",
        "extra",
        "nested",
        "failure",
    ],
)
def test_saved_phase_tampering_rejected_after_rehash(
    source: SpotTree, tmp_path: Path, change: str
) -> None:
    import hashlib

    out = tmp_path / "capture"
    with p.constructor_scope("phased", out, 1) as r:
        MatrixTree.build(source)
    path = out / "phase-events.jsonl"
    rows = [json.loads(x) for x in path.read_text().splitlines()]
    if change == "missing":
        rows.pop()
    elif change == "order":
        rows[1], rows[2] = rows[2], rows[1]
    elif change == "bool":
        rows[1]["sequence"] = True
    elif change in ("pid", "thread"):
        rows[1][change] += 1
    elif change == "negative":
        rows[1]["clocks"]["cpu"] = -1
    elif change == "backward":
        rows[2]["clocks"]["cpu"] = rows[1]["clocks"]["cpu"] - 0.01
    elif change == "nan":
        rows[1]["clocks"]["wall"] = float("nan")
    elif change == "extra":
        rows[1]["unexpected"] = True
    elif change == "nested":
        rows[2]["event"] = "phase_begin"
    else:
        rows[2]["failure_kind"] = "ValueError"
    data = ("\n".join(json.dumps(x) for x in rows) + "\n").encode()
    path.write_bytes(data)
    receipt = json.loads((out / "phases.json").read_text())
    receipt["events_sha256"] = hashlib.sha256(data).hexdigest()
    (out / "phases.json").write_text(json.dumps(receipt))
    with pytest.raises(ArithmeticError):
        p.read_phases(out, 1, 1, r["pid"], r["thread"])


def test_guard_rejects_moved_statement_even_when_whole_body_unchanged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    old = inspect.getsource

    def moved(function: Any) -> str:
        s = old(function)
        if function is p.build:
            s = s.replace(
                '    with phase("array_setup"):\n        n = len(source.states)',
                '        n = len(source.states)\n    with phase("array_setup"):',
            )
        return s

    monkeypatch.setattr(p.inspect, "getsource", moved)
    with pytest.raises(ArithmeticError, match="boundaries"):
        p.ast_equivalence()


@pytest.mark.parametrize(
    "failure",
    [
        "backward",
        "nonfinite",
        "pid",
        "nesting",
        "phase_order",
        "field_witness",
        "keyboard",
    ],
)
def test_phase_failures_restore_and_retain_primary(
    source: SpotTree, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    if failure in ("backward", "nonfinite"):
        original = p.clock
        calls = []

        def bad_clock() -> dict[str, float]:
            calls.append(True)
            value: dict[str, float] = original()
            if len(calls) == 3:
                value["cpu"] = float("nan") if failure == "nonfinite" else 0.0
            return value

        monkeypatch.setattr(p, "clock", bad_clock)
    elif failure == "pid":
        original = p.PhaseRecorder.guard
        calls = []

        def bad_guard(self: Any) -> None:
            calls.append(True)
            if len(calls) == 3:
                raise ArithmeticError("fictional pid changed")
            original(self)

        monkeypatch.setattr(p.PhaseRecorder, "guard", bad_guard)
    elif failure in ("nesting", "phase_order"):
        original = p.phase

        def bad_phase(name: str) -> Any:
            if name == "array_setup":
                recorder = p.CURRENT.get()
                assert recorder is not None
                if failure == "nesting":
                    recorder.in_phase = True
                return original("information_keys")
            return original(name)

        monkeypatch.setattr(p, "phase", bad_phase)
    elif failure == "field_witness":

        def bad_witness(*args: Any) -> Any:
            raise RuntimeError("fictional witness failed")

        monkeypatch.setattr(g, "matrix_witness", bad_witness)
    with pytest.raises((ArithmeticError, RuntimeError, KeyboardInterrupt)):
        with p.constructor_scope("phased", tmp_path / "capture", 2):
            MatrixTree.build(source)
            if failure == "keyboard":
                raise KeyboardInterrupt("fictional stop")
    assert p.CURRENT.get() is None and vars(MatrixTree)["build"] is p.BASE_DESCRIPTOR
    assert (
        json.loads((tmp_path / "capture/constructor.json").read_text())["status"]
        == "failed_retained"
    )


@pytest.mark.parametrize("change", [None, "fields", "outside"])
def test_original_baseline_and_real_outer_containment(
    source: SpotTree, tmp_path: Path, change: str | None
) -> None:
    import gzip
    import os

    t = importlib.import_module("profile_matrix_phases")
    with p.constructor_scope("original", tmp_path / "baseline", 2):
        MatrixTree.build(source)
    regions = reader.coarse.Regions(16)
    regions.active = True
    regions.read_index = 1
    selected: dict[str, Any] = {}
    out = tmp_path / "current"
    with p.constructor_scope("phased", out / "constructors", 2) as receipt:
        with reader.extension(), reader.coarse.selected_hooks(regions, selected):
            MatrixTree.build(source)
    fp = g.read_constructors(
        out / "constructors", "phased", 2, receipt["pid"], receipt["thread"]
    )
    if change == "fields":
        fp = ["0" * 64]
    if change == "outside":
        regions.rows[0]["before"]["cpu"] = regions.rows[0]["after"]["cpu"]
    for i in range(3):
        path = out / "reads" / str(i) / "ledger.json.gz"
        path.parent.mkdir(parents=True)
        with gzip.open(path, "wt") as stream:
            json.dump(dict(rows=regions.rows if i == 1 else []), stream)
    c = dict(
        constructor_baseline="baseline",
        maximum_builder_calls_per_child=2,
        expected_constructors=1,
    )
    child = dict(pid=os.getpid(), thread=threading.get_ident())
    if change is None:
        rows = t.constructor_phases(tmp_path, out, c, child, fp)
        assert len(rows) == 1 and rows[0]["read"] == 1
    else:
        with pytest.raises(ArithmeticError):
            t.constructor_phases(tmp_path, out, c, child, fp)
