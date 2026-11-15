"""Software-only coarse timing and immutable original-audit acceptance fixtures."""

import copy
import importlib
import json
import os
import sys
import threading
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
tool = importlib.import_module("profile_coarse_reader")


def setup_fake_read(monkeypatch: pytest.MonkeyPatch) -> tuple[Any, list[Any]]:
    from compact_cached import cli

    calls: list[Any] = []

    def fake(*args: Any, **kwargs: Any) -> dict[str, Any]:
        calls.append((args, kwargs))
        kwargs["observed"].append(dict(fictional=True))
        return dict(scope="fictional")

    monkeypatch.setattr(cli, "read", fake)
    monkeypatch.setattr(tool.helpers, "observe", lambda r, c, o, call: call())
    return cli, calls


def test_original_shape_objects_forwarded_and_restored(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cli, calls = setup_fake_read(monkeypatch)
    previous = cli.read
    own, deadline = object(), object()
    actual: list[Any] = []
    with tool.reader_observer(ROOT, {"maximum_selected_calls": 4096}, tmp_path):
        result = cli.read(ROOT, own, deadline, observed=actual)
    assert cli.read is previous
    assert calls[0][0] == (ROOT, own, deadline)
    assert calls[0][1]["observed"] is actual
    row = json.loads((tmp_path / "inner-reads.json").read_text())["reads"][0]
    assert row["scope"] == result["scope"] == "fictional"
    assert row["computed"] == actual[0]
    tool.check_record(row["observation"])


@pytest.mark.parametrize(
    "kind", ["missing", "extra", "nonlist", "prefilled", "wrongargs"]
)
def test_read_shape_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    cli, calls = setup_fake_read(monkeypatch)
    args: tuple[Any, ...] = (ROOT, object(), object())
    kwargs: dict[str, Any] = dict(observed=[])
    if kind == "missing":
        kwargs = {}
    elif kind == "extra":
        kwargs["other"] = []
    elif kind == "nonlist":
        kwargs["observed"] = ()
    elif kind == "prefilled":
        kwargs["observed"] = [1]
    else:
        args = args[:2]
    with (
        tool.reader_observer(ROOT, {"maximum_selected_calls": 4096}, tmp_path),
        pytest.raises(ArithmeticError),
    ):
        cli.read(*args, **kwargs)
    assert not calls


def test_only_three_reads(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cli, calls = setup_fake_read(monkeypatch)
    with tool.reader_observer(ROOT, {"maximum_selected_calls": 4096}, tmp_path):
        for _ in range(3):
            cli.read(ROOT, object(), object(), observed=[])
        with pytest.raises(ArithmeticError):
            cli.read(ROOT, object(), object(), observed=[])
    assert len(calls) == 3


def test_primary_failure_retained_and_hooks_restored(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cli, _ = setup_fake_read(monkeypatch)
    error = RuntimeError("fictional failure")

    def failed(*args: Any, **kwargs: Any) -> Any:
        raise error

    monkeypatch.setattr(cli, "read", failed)
    with pytest.raises(RuntimeError) as caught:
        with tool.reader_observer(ROOT, {"maximum_selected_calls": 4096}, tmp_path):
            cli.read(ROOT, object(), object(), observed=[])
    assert caught.value is error and cli.read is failed
    row = json.loads((tmp_path / "inner-reads.json").read_text())["reads"][0]
    assert row["status"] == "failed_retained" and row["failure_kind"] == "RuntimeError"
    assert "observation" not in row


@pytest.mark.parametrize("count", [0, 2])
def test_actual_computed_witness_required(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, count: int
) -> None:
    cli, _ = setup_fake_read(monkeypatch)

    def fake(*args: Any, **kwargs: Any) -> dict[str, Any]:
        kwargs["observed"].extend({} for _ in range(count))
        return dict(scope="fictional")

    monkeypatch.setattr(cli, "read", fake)
    with (
        tool.reader_observer(ROOT, {"maximum_selected_calls": 4096}, tmp_path),
        pytest.raises(ArithmeticError),
    ):
        cli.read(ROOT, object(), object(), observed=[])


def original_fixture(tmp_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    c = tool.contract(ROOT)
    row = json.loads((ROOT / c["historical_original"]).read_text())
    (tmp_path / "old").mkdir()
    for p in (ROOT / "results/card-audit-clock-trace/pair/uncached").rglob("*"):
        if p.is_file():
            target = (
                tmp_path
                / "old"
                / p.relative_to(ROOT / "results/card-audit-clock-trace/pair/uncached")
            )
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(p.read_bytes())
    return c, row


def test_original_result_checks_existing_data(tmp_path: Path) -> None:
    c, row = original_fixture(tmp_path)
    assert tool.original_result(ROOT, tmp_path, c) == row


@pytest.mark.parametrize(
    "kind",
    [
        "mode",
        "status",
        "base_admission_rejected",
        "identity",
        "card_cache",
        "source",
        "raw",
        "worker",
    ],
)
def test_original_result_rejects_changes(tmp_path: Path, kind: str) -> None:
    c, row = original_fixture(tmp_path)
    if kind in ("mode", "status"):
        row[kind] = "changed"
    elif kind == "base_admission_rejected":
        row[kind] = False
    elif kind == "identity":
        row[kind]["profiles"].pop()
    elif kind == "card_cache":
        row[kind]["rank"]["hits"] += 1
    elif kind == "source":
        row[kind]["sha256"].popitem()
    elif kind == "raw":
        (tmp_path / "old/read-phases.json").write_text("{}")
    else:
        (tmp_path / "old/worker-telemetry/worker-0.json").write_text("{}")
    (tmp_path / "old/child.json").write_text(json.dumps(row))
    with pytest.raises((ArithmeticError, KeyError)):
        tool.original_result(ROOT, tmp_path, c)


def test_config_and_inputs_guarded(tmp_path: Path) -> None:
    (tmp_path / "configs").mkdir()
    (tmp_path / tool.CONFIG).write_text("{}")
    with pytest.raises(ArithmeticError, match="contract"):
        tool.contract(tmp_path)


@pytest.mark.parametrize("kind", ["missing_extras", "missing_checks", "wrong_mode"])
def test_child_preflight_stops_before_audit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    c = tool.contract(ROOT)
    calls = []
    monkeypatch.setattr(tool, "binding", lambda root, **k: (c, {}))

    def no_checks(*a: Any) -> None:
        raise ArithmeticError("fixture missing checks")

    def no_extras(*a: Any) -> None:
        raise ArithmeticError("fixture missing extras")

    monkeypatch.setattr(
        tool, "checked", no_checks if kind == "missing_checks" else lambda *a: None
    )
    monkeypatch.setattr(tool.helpers, "runtime_requirements", no_extras)
    monkeypatch.setattr(tool.original, "child", lambda *a: calls.append(a))
    assert (
        tool.child(
            ROOT,
            "wrong" if kind == "wrong_mode" else "control",
            tmp_path,
            tool.time.perf_counter(),
        )
        == 1
    )
    assert not calls
    assert (
        json.loads((tmp_path / "child.json").read_text())["status"] == "failed_retained"
    )


@pytest.mark.parametrize("code", [1, 124])
def test_pair_stops_and_retains_first_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, code: int
) -> None:
    root = tmp_path
    output = root / "results/runs/failure"
    c = tool.contract(ROOT)
    calls = []
    monkeypatch.setattr(tool, "contract", lambda r: c)
    monkeypatch.setattr(tool.original, "control", lambda c: {})

    def supervise(command: list[str], folder: Path, cap: float) -> dict[str, Any]:
        calls.append(cap)
        folder.mkdir()
        (folder / "command.log").write_text("fixture")
        return dict(
            returncode=code,
            interrupted="TimeoutExpired" if code == 124 else None,
            seconds=1,
        )

    monkeypatch.setattr(tool, "supervise", supervise)
    assert tool.pair(root, output) == 1
    saved = json.loads((output / "pair.json").read_text())
    assert len(calls) == 1 and calls[0] <= 900 and saved["status"] == "failed_retained"
    assert saved["measurements"][0]["returncode"] == code
    with pytest.raises(ValueError):
        tool.pair(root, output)


def test_existing_output_never_overwritten(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        tool.pair(tmp_path, tmp_path)


def test_control_keeps_original_child_and_observer_off(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from compact_cached import cli

    c = tool.contract(ROOT)
    import numpy

    import poker_ai.reproducibility as reproducibility

    monkeypatch.setattr(tool.sys, "version", "3.11.17 fictional fixture")
    monkeypatch.setattr(numpy, "__version__", "2.4.6")
    monkeypatch.setattr(reproducibility, "runtime_environment", lambda: c["runtime"])
    previous = cli.read
    calls = []
    monkeypatch.setattr(tool, "binding", lambda *a, **k: (c, dict(sha256={})))
    monkeypatch.setattr(tool, "checked", lambda *a: None)
    monkeypatch.setattr(tool.helpers, "runtime_requirements", lambda c: {})
    monkeypatch.setattr(tool.original, "control", lambda c: {})
    # Qualification hashing is stubbed, not a real source-admitted collection.
    monkeypatch.setattr(tool, "digest", lambda p: "fixture")

    def fake(root: Path, mode: str, out: Path, origin: float) -> int:
        assert cli.read is previous and mode == "uncached"
        calls.append(mode)
        (out / "child.json").write_text("retained original child")
        return 0

    monkeypatch.setattr(tool.original, "child", fake)
    monkeypatch.setattr(
        tool, "original_result", lambda *a: dict(identity={"fictional": True})
    )
    assert tool.child(ROOT, "control", tmp_path, tool.time.perf_counter()) == 0
    saved = json.loads((tmp_path / "child.json").read_text())
    assert calls == ["uncached"] and "old/child.json" in saved["raw_sha256"]
    assert not (tmp_path / "inner-reads.json").exists()


def sample() -> tuple[Any, dict[str, Any], list[dict[str, Any]]]:
    events: list[dict[str, Any]] = []
    ticks = iter([1, 2, 4, 8, 10, 12])

    def clock() -> dict[str, Any]:
        t = next(ticks)
        return dict(
            wall=float(t), cpu=float(t), pid=os.getpid(), thread=threading.get_ident()
        )

    r = tool.Regions(4096, events.append, clock)
    r.active = True
    r.read_index = 0
    child = r.wrap("spot_tree_build", lambda: object())
    parent = r.wrap("matrix_build", lambda: child())
    parent()
    r.wrap("checkpoint_replay", lambda: None)()
    saved = dict(
        status="complete", errors=r.errors, rows=r.rows, pid=r.pid, thread=r.thread
    )
    return r, saved, events


def test_nested_cpu_accounting_without_double_counting() -> None:
    r, saved, events = sample()
    result = tool.validate_regions(saved, events, r.pid, r.thread, 0)
    assert result["calls"] == 3 and result["selected_union_cpu"] == 9
    assert result["groups"]["matrix_build"]["inclusive_cpu"] == 7
    assert result["groups"]["matrix_build"]["exclusive_selected_cpu"] == 5
    assert result["groups"]["spot_tree_build"]["exclusive_selected_cpu"] == 2
    assert sum(x["exclusive_selected_cpu"] for x in result["groups"].values()) == 9


@pytest.mark.parametrize(
    "kind",
    [
        "missing",
        "pid",
        "thread",
        "category",
        "ordinal",
        "read",
        "cpu",
        "wall",
        "parent",
        "partial",
        "errors",
        "end_before",
        "duplicate",
    ],
)
def test_changed_region_events_rejected(kind: str) -> None:
    r, saved, events = sample()
    if kind == "missing":
        events.pop()
    elif kind == "partial":
        saved["status"] = "partial"
    elif kind == "errors":
        saved["errors"] = 1
    elif kind == "duplicate":
        events.insert(1, copy.deepcopy(events[0]))
    elif kind in ("pid", "thread"):
        events[1]["before"][kind] += 1
    elif kind == "cpu":
        events[1]["before"]["cpu"] = 0
    elif kind == "wall":
        events[1]["before"]["wall"] = 0
    elif kind == "end_before":
        events[-1]["after"]["cpu"] = 0
    else:
        events[1][kind] = "changed"
    with pytest.raises((ArithmeticError, TypeError)):
        tool.validate_regions(saved, events, r.pid, r.thread, 0)


def test_primary_exception_is_not_replaced_by_capture_failure() -> None:
    error = RuntimeError("primary fixture")

    def emit(row: dict[str, Any]) -> None:
        if row["status"] != "running":
            raise OSError("fixture observer failure")

    r = tool.Regions(2, emit)
    r.active = True

    def failed() -> None:
        raise error

    with pytest.raises(RuntimeError) as caught:
        r.wrap("matrix_build", failed)()
    assert caught.value is error and not r.stack and r.errors == 1
    assert r.rows[0]["status"] == "primary_with_observer_failure"


@pytest.mark.parametrize("kind", ["thread", "pid", "cap"])
def test_unsupported_coverage_fails_before_selected_call(
    kind: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    r = tool.Regions(1)
    r.active = True
    calls = []
    if kind == "thread":
        r.thread += 1
    elif kind == "pid":
        r.pid += 1
    else:
        r.total = 1
    with pytest.raises(ArithmeticError):
        r.wrap("matrix_build", lambda: calls.append(1))()
    assert not calls and r.errors == 1


@pytest.mark.parametrize("maximum", [0, -1, True, 1.5])
def test_invalid_capture_cap(maximum: Any) -> None:
    with pytest.raises(ValueError):
        tool.Regions(maximum)


def test_inactive_selected_call_is_unchanged() -> None:
    r = tool.Regions(1)
    token = object()
    actual = []

    def f(*args: Any, **kwargs: Any) -> Any:
        actual.append((args, kwargs))
        return token

    assert r.wrap("matrix_build", f)(token, a=token) is token
    assert actual[0][0][0] is token and actual[0][1]["a"] is token and not r.rows


def test_descriptor_subclass_alias_and_late_import_restoration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Original:
        @classmethod
        def build(cls, token: Any) -> Any:
            return cls, token

    class Subclass(Original):
        pass

    alias: Any = ModuleType("poker_ai._coarse_test_alias")
    late: Any = ModuleType("poker_ai._coarse_test_late")
    before = Original.build
    alias.bound = before
    alias.function = vars(Original)["build"].__func__
    monkeypatch.setitem(sys.modules, alias.__name__, alias)
    r = tool.Regions(10)
    r.active = True
    r.read_index = 0
    state: dict[str, Any] = {}
    token = object()
    descriptor = vars(Original)["build"]
    with tool.selected_hooks(r, state, (("matrix_build", Original, "build"),)):
        assert Original.build(token) == (Original, token)
        assert Subclass.build(token) == (Subclass, token)
        assert alias.bound(token) == (Original, token)
        assert alias.function(Original, token) == (Original, token)
        late.bound = Original.build
        monkeypatch.setitem(sys.modules, late.__name__, late)
    assert vars(Original)["build"] is descriptor and alias.bound is before
    assert alias.function is descriptor.__func__
    assert (
        late.bound.__func__ is descriptor.__func__ and late.bound.__self__ is Original
    )
    assert state["restored"] is True and state["aliases_remaining"] == 0
    assert len(r.rows) == 4


def test_hooks_restore_on_primary_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    module: Any = ModuleType("poker_ai._coarse_throw")
    error = ValueError("fixture")

    def failed() -> None:
        raise error

    module.f = failed
    monkeypatch.setitem(sys.modules, module.__name__, module)
    r = tool.Regions(10)
    r.active = True
    state: dict[str, Any] = {}
    with pytest.raises(ValueError) as caught:
        with tool.selected_hooks(r, state, (("checkpoint_replay", module, "f"),)):
            module.f()
    assert caught.value is error and module.f is failed and state["restored"] is True


def test_complete_empty_capture_is_zero_not_partial() -> None:
    r = tool.Regions(1)
    saved = dict(status="complete", errors=0, rows=[])
    assert (
        tool.validate_regions(saved, [], r.pid, r.thread, 0)["selected_union_cpu"] == 0
    )
    saved["status"] = "partial"
    with pytest.raises(ArithmeticError):
        tool.validate_regions(saved, [], r.pid, r.thread, 0)


def phase_fixture(
    tmp_path: Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    config = tool.contract(ROOT)
    template: dict[str, Any] = tool.snapshot()
    inner = []
    outer = []
    computed = []

    def snapshot(t: float) -> dict[str, Any]:
        value = copy.deepcopy(template)
        for key in (
            "perf_seconds",
            "utc_seconds",
            "process_cpu_seconds",
            "thread_cpu_seconds",
        ):
            value[key] = t
        return value

    for i, scope in enumerate(
        (
            "FICTIONAL_SIGNAL_GAMES_OWN_OPPONENT_SOFTWARE_NOT_HOLDEM",
            "OLD_OWN_OPPONENT_COST_STANDINS_NO_NEW_TRAINING",
            "OLD_OWN_OPPONENT_COST_STANDINS_NO_NEW_TRAINING",
        )
    ):
        regions, ledger, events = sample()
        for record in ledger["rows"] + events:
            record["read"] = i
            for name in ("before", "after"):
                if name in record:
                    for key in ("wall", "cpu"):
                        record[name][key] += 30 * i
        a, b = snapshot(30 * i + 1), snapshot(30 * i + 20)
        inner.append(
            dict(
                index=i,
                status="complete",
                scope=scope,
                before=a,
                computed=dict(fictional=i),
                observation=tool.record(a, b),
            )
        )
        outer.append(
            dict(
                scope=scope,
                observation=tool.record(snapshot(30 * i), snapshot(30 * i + 22)),
            )
        )
        computed.append(dict(scope=scope, computed=dict(fictional=i)))
        folder = tmp_path / "reads" / str(i)
        folder.mkdir(parents=True)
        tool.helpers.compressed(folder / "ledger.json.gz", ledger)
        with tool.gzip.open(folder / "events.jsonl.gz", "wt") as stream:
            for event in events:
                stream.write(json.dumps(event) + "\n")
    (tmp_path / "old").mkdir()
    (tmp_path / "old/parent-resource-reads.json").write_text(
        json.dumps(dict(reads=outer))
    )
    (tmp_path / "inner-reads.json").write_text(json.dumps(dict(reads=inner)))
    state = dict(
        categories=list(tool.CATEGORIES),
        restored=True,
        aliases_remaining=0,
        errors=0,
        total_selected_calls=9,
    )
    (tmp_path / "hook-state.json").write_text(json.dumps(state))
    return (
        config,
        dict(pid=regions.pid, thread=regions.thread),
        dict(identity=dict(computed_replays=computed)),
    )


def test_full_three_read_capture_schema(tmp_path: Path) -> None:
    c, child, old = phase_fixture(tmp_path)
    ledgers = tool.phase_ledgers(tmp_path, child, old, c)
    assert len(ledgers) == 3 and sum(x["summary"]["calls"] for x in ledgers) == 9


@pytest.mark.parametrize(
    "kind",
    [
        "restored",
        "remaining",
        "errors",
        "total",
        "cap",
        "missing_read",
        "thread",
        "pid",
        "scope",
        "index",
        "computed",
        "interval",
    ],
)
def test_phase_capture_changes_rejected(tmp_path: Path, kind: str) -> None:
    c, child, old = phase_fixture(tmp_path)
    state_path = tmp_path / "hook-state.json"
    state = json.loads(state_path.read_text())
    p = tmp_path / "inner-reads.json"
    rows = json.loads(p.read_text())
    if kind == "restored":
        state["restored"] = False
    elif kind == "remaining":
        state["aliases_remaining"] = 1
    elif kind == "errors":
        state["errors"] = 1
    elif kind == "total":
        state["total_selected_calls"] = 8
    elif kind == "cap":
        c["maximum_selected_calls"] = 8
    elif kind == "missing_read":
        rows["reads"].pop()
    elif kind in ("pid", "thread"):
        child[kind] += 1
    elif kind == "interval":
        rows["reads"][0]["observation"]["interval"]["clocks"]["process_cpu_seconds"] = 0
    else:
        rows["reads"][0][kind] = "changed"
    state_path.write_text(json.dumps(state))
    p.write_text(json.dumps(rows))
    with pytest.raises(ArithmeticError):
        tool.phase_ledgers(tmp_path, child, old, c)


def test_nested_hook_installation_rejected_and_restored() -> None:
    r = tool.Regions(10)
    state: dict[str, Any] = {}
    other: dict[str, Any] = {}
    with tool.selected_hooks(r, state):
        with pytest.raises(ArithmeticError):
            with tool.selected_hooks(r, other):
                pass
    assert state["restored"] is True


def test_regions_cannot_shift_cpu_outside_read(tmp_path: Path) -> None:
    c, child, old = phase_fixture(tmp_path)
    folder = tmp_path / "reads/0"
    ledger = tool.helpers.load_compressed(folder / "ledger.json.gz")
    with tool.gzip.open(folder / "events.jsonl.gz", "rt") as stream:
        events = [json.loads(x) for x in stream]
    for x in ledger["rows"] + events:
        for name in ("before", "after"):
            if name in x:
                x[name]["cpu"] += 100
    (folder / "ledger.json.gz").unlink()
    tool.helpers.compressed(folder / "ledger.json.gz", ledger)
    with tool.gzip.open(folder / "events.jsonl.gz", "wt") as stream:
        for event in events:
            stream.write(json.dumps(event) + "\n")
    with pytest.raises(ArithmeticError):
        tool.phase_ledgers(tmp_path, child, old, c)


def test_saved_report_never_runs_poker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    c, child, old = phase_fixture(tmp_path / "profiled")
    ledgers = tool.phase_ledgers(tmp_path / "profiled", child, old, c)
    folder = tmp_path / "control/old"
    folder.mkdir(parents=True)
    (folder / "parent-resource-reads.json").write_bytes(
        (tmp_path / "profiled/old/parent-resource-reads.json").read_bytes()
    )
    verified = dict(ledgers=ledgers, pair=dict(measurements=[]))
    monkeypatch.setattr(tool, "verify_pair", lambda *a: verified)

    def forbidden(*a: Any, **k: Any) -> None:
        raise AssertionError("pure report entered poker")

    monkeypatch.setattr(tool.original, "child", forbidden)
    monkeypatch.setattr(tool, "supervise", forbidden)
    saved = tool.report(ROOT, tmp_path)
    assert len(saved["rows"]) == 6 and saved["rows"][0]["selected"] is None
    assert saved["rows"][3]["selected"]["selected_union_cpu"] == 9
    assert saved["rows"][3]["outside_selected_cpu"] == 10
    assert saved["long_run_admitted"] is False


def test_reentrant_capture_callback_is_incomplete() -> None:
    r = tool.Regions(10)
    r.active = True
    nested = r.wrap("spot_tree_build", lambda: None)
    r.emit = lambda event: nested()
    with pytest.raises(ArithmeticError):
        r.wrap("matrix_build", lambda: None)()
    assert r.errors > 0 and not r.stack and not r.emitting
