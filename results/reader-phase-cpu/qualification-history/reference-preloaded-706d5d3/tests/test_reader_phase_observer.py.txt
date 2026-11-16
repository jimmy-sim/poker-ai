"""Reader phase safety and actual archived software coverage; no new training."""

import copy
import os
import sys
import threading
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import reader_phase_support as tool

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def phases(monkeypatch: pytest.MonkeyPatch) -> Any:
    from compact_suit import cli

    from poker_ai.evaluation import compact_opponent_sources as sources
    from poker_ai.evaluation import opponent_learning_own as own

    calls = []
    originals = []
    for module, name, alias in (
        (sources, "load", "load"),
        (sources, "standins", "load_standins"),
        (own, "replay", "replay"),
    ):

        def original(*args: Any, _name: str = alias, **kwargs: Any) -> Any:
            calls.append((_name, args, kwargs))
            if "failure" in kwargs:
                raise kwargs["failure"]
            return kwargs["result"]

        monkeypatch.setattr(module, name, original)
        monkeypatch.setattr(cli, alias, original)
        originals.append(original)
    return cli, calls, originals


def observed(phases: Any, *, enabled: bool = True) -> tool.Observer:
    cli, _, _ = phases
    ticks = iter(range(100))

    def clock() -> dict[str, Any]:
        value = float(next(ticks))
        return dict(
            cpu=value, wall=2 * value, pid=os.getpid(), thread=threading.get_ident()
        )

    observer = tool.Observer(enabled=enabled, read_clock=clock)
    with observer.hooks():
        for index, names in enumerate(
            (
                ("replay",),
                ("load", "load_standins", "replay"),
                ("load", "load_standins", "replay"),
            )
        ):
            with observer.read(index):
                for name in names:
                    token = object()
                    assert getattr(cli, name)(token, result=token) is token
    return observer


@pytest.mark.parametrize("enabled", [False, True])
def test_exact_forwarding_disjoint_arithmetic_and_restoration(
    phases: Any, enabled: bool
) -> None:
    cli, calls, originals = phases
    observer = observed(phases, enabled=enabled)
    rows = tool.validate_state(
        observer.state(),
        observer.reads,
        enabled=enabled,
        pid=os.getpid(),
        thread=threading.get_ident(),
    )
    assert len(calls) == 7
    assert [
        getattr(cli, name) for name in ("load", "load_standins", "replay")
    ] == originals
    assert sum(r["selected_calls"] for r in rows) == (7 if enabled else 0)
    if enabled:
        assert [r["read_cpu_seconds"] for r in rows] == [3, 7, 7]
        assert [r["remaining_read_cpu_seconds"] for r in rows] == [2, 4, 4]
        assert rows[0]["phase_cpu_seconds"] == dict(
            source_load=0, standin_load=0, own_replay=1
        )
    with pytest.raises(ArithmeticError):
        with observer.hooks():
            pass


@pytest.mark.parametrize(
    "damage",
    [
        "extra",
        "missing",
        "order",
        "event_bool",
        "ledger_bool",
        "nan",
        "pid",
        "overlap",
        "outside",
        "parent",
        "error",
        "extra_clock",
    ],
)
def test_corrupt_saved_phase_data_rejected(phases: Any, damage: str) -> None:
    row = copy.deepcopy(observed(phases).reads[1])
    ledger = row["ledger"]
    if damage == "extra":
        row["events"].append(copy.deepcopy(row["events"][-1]))
    elif damage == "missing":
        ledger["rows"].pop()
    elif damage == "order":
        ledger["rows"].reverse()
    elif damage == "event_bool":
        row["events"][0]["index"] = False
    elif damage == "ledger_bool":
        ledger["errors"] = False
    elif damage == "nan":
        row["before"]["cpu"] = float("nan")
    elif damage == "pid":
        ledger["pid"] += 1
    elif damage == "overlap":
        ledger["rows"][1]["before"]["cpu"] = ledger["rows"][0]["before"]["cpu"]
    elif damage == "outside":
        ledger["rows"][-1]["after"]["cpu"] = row["after"]["cpu"] + 1
    elif damage == "parent":
        ledger["rows"][1]["parent"] = 0
    elif damage == "error":
        ledger["errors"] = 1
    else:
        row["before"]["extra"] = 0
    with pytest.raises(ArithmeticError):
        tool.validate_read(row, 1, enabled=True)


@pytest.mark.parametrize("enabled", [False, True])
def test_nested_plain_or_observed_scopes_rejected(phases: Any, enabled: bool) -> None:
    observer = tool.Observer(enabled=enabled)
    with observer.hooks():
        with observer.read(0), pytest.raises(ArithmeticError):
            with observer.read(1):
                pass
        with pytest.raises(ArithmeticError):
            with tool.Observer(enabled=False).hooks():
                pass


@pytest.mark.parametrize("secondary", ["none", "clock", "sink"])
def test_primary_exception_identity_partial_records_and_cleanup(
    phases: Any, secondary: str
) -> None:
    cli, _, originals = phases
    primary = LookupError("original phase failure")
    count = 0

    def clock() -> dict[str, Any]:
        nonlocal count
        count += 1
        if secondary == "clock" and count >= 3:
            raise OSError("clock failed")
        return dict(
            cpu=float(count),
            wall=float(count),
            pid=os.getpid(),
            thread=threading.get_ident(),
        )

    def sink(index: int, event: dict[str, Any]) -> None:
        if secondary == "sink" and event["status"] != "running":
            raise OSError("retention failed")

    observer = tool.Observer(enabled=True, read_clock=clock, event_sink=sink)
    with pytest.raises(LookupError) as caught:
        with observer.hooks(), observer.read(0):
            cli.replay(failure=primary)
    assert caught.value is primary
    assert observer.restored and not tool.BUSY
    assert observer.reads[0]["status"] != "complete"
    assert [
        getattr(cli, name) for name in ("load", "load_standins", "replay")
    ] == originals


def test_only_named_aliases_observed_and_late_alias_restored(
    phases: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    from poker_ai.evaluation import compact_opponent_sources as sources

    cli, _, originals = phases
    observer = tool.Observer(enabled=True)
    with observer.hooks(), observer.read(0):
        assert sources.load is originals[0]
        sources.load(result=None)
        monkeypatch.setattr(cli, "temporary_phase_alias", cli.replay, raising=False)
        cli.replay(result=None)
    assert observer.regions.total == 1
    assert cli.temporary_phase_alias is originals[2]


def test_actual_archived_software_read_preserves_computed_math() -> None:
    from compact_suit import cli

    from poker_ai.postflop.river_study import Deadline

    path = ROOT / "results/compact-suit-learning/software/own.json"
    before = path.read_bytes()
    plain: list[dict[str, Any]] = []
    expected = cli.read(ROOT, path, Deadline(180), observed=plain)
    actual: list[dict[str, Any]] = []
    observer = tool.Observer(enabled=True)
    with observer.hooks(), observer.read(0):
        saved = cli.read(ROOT, path, Deadline(180), observed=actual)
    assert saved == expected and actual == plain
    assert len(actual) == 1 and actual[0]["unique_profiles"] == 432
    assert observer.restored and observer.state()["selected_calls"] == 1
    assert tool.validate_read(observer.reads[0], 0, enabled=True)["selected_calls"] == 1
    assert path.read_bytes() == before


@pytest.mark.parametrize("maximum", [True, False, 0, -1, 1.5])
def test_typed_positive_cap(maximum: Any) -> None:
    with pytest.raises(ValueError):
        tool.Observer(enabled=True, maximum=maximum)


def test_call_cap_partial_retention(phases: Any) -> None:
    cli, _, _ = phases
    observer = tool.Observer(enabled=True, maximum=1)
    with pytest.raises(ArithmeticError, match="cap"):
        with observer.hooks(), observer.read(0):
            cli.replay(result=None)
            cli.replay(result=None)
    assert observer.restored and observer.regions.total == 1
    assert observer.reads[0]["status"] == "partial"


def test_event_sink_reentrancy_rejected(phases: Any) -> None:
    cli, _, _ = phases

    def emit(index: int, event: dict[str, Any]) -> None:
        cli.replay(result=None)

    observer = tool.Observer(enabled=True, event_sink=emit)
    with pytest.raises(ArithmeticError, match="disjoint"):
        with observer.hooks(), observer.read(0):
            cli.replay(result=None)
    assert observer.restored and observer.regions.errors > 0


def test_other_thread_cannot_create_active_scope(phases: Any) -> None:
    outcomes = []

    def thread() -> None:
        observer = tool.Observer(enabled=True)
        try:
            with observer.hooks():
                pass
        except ArithmeticError:
            outcomes.append("rejected")

    worker = threading.Thread(target=thread)
    worker.start()
    worker.join()
    assert outcomes == ["rejected"] and not tool.BUSY


def test_wrong_process_rejected_and_bindings_restored(
    phases: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    cli, _, _ = phases
    observer = tool.Observer(enabled=True)
    pid = os.getpid()
    with pytest.raises(ArithmeticError, match="serial parent"):
        with observer.hooks(), observer.read(0), monkeypatch.context() as patch:
            patch.setattr(os, "getpid", lambda: pid + 1)
            cli.replay(result=None)
    assert observer.restored


@pytest.mark.parametrize(
    "field", ["pid", "selected_calls", "restored", "maximum", "categories"]
)
def test_strict_saved_state(phases: Any, field: str) -> None:
    observer = observed(phases)
    state = observer.state()
    state[field] = False
    with pytest.raises(ArithmeticError):
        tool.validate_state(
            state,
            observer.reads,
            enabled=True,
            pid=os.getpid(),
            thread=threading.get_ident(),
        )
