"""Source-root observation, alias proxies and exact saved nesting; no new training."""

import copy
import dataclasses
import os
import subprocess
import sys
import threading
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import source_phase_support as tool

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def calls(monkeypatch: pytest.MonkeyPatch) -> Any:
    from compact_suit import cli

    from poker_ai.evaluation import compact_fixed_inputs as sampled
    from poker_ai.evaluation import compact_opponent_boundaries as boundaries
    from poker_ai.evaluation import compact_opponent_contexts as contexts
    from poker_ai.evaluation import compact_opponent_sources as source
    from poker_ai.evaluation import opponent_learning_sources as previous

    source_api: Any = source
    cli_api: Any = cli
    invoked = []
    originals = []
    for category, defining, name, alias in (
        ("previous_sources", previous, "load", None),
        ("compact_game", contexts, "build_game", "build_game"),
        ("parent_replay", sampled, "replay_sources", None),
        ("original_contexts", boundaries, "load_contexts", "load_contexts"),
        ("original_boundaries", boundaries, "boundaries", "boundaries"),
    ):

        def original(*args: Any, _name: str = category, **kwargs: Any) -> Any:
            invoked.append((_name, args, kwargs))
            if "failure" in kwargs:
                raise kwargs["failure"]
            return kwargs["result"]

        monkeypatch.setattr(defining, name, original)
        if alias:
            monkeypatch.setattr(source, alias, original)
        originals.append((defining, name, original))

    def root(*args: Any, **kwargs: Any) -> Any:
        if kwargs.get("recursive"):
            return cli_api.load(*args, **kwargs)
        for category, function in (
            ("previous_sources", source_api.old_sources.load),
            ("compact_game", source_api.build_game),
            ("compact_game", source_api.build_game),
            ("parent_replay", source_api.sampled_parent.replay_sources),
            ("original_contexts", source_api.load_contexts),
            ("original_boundaries", source_api.boundaries),
        ):
            forwarded = dict(result=kwargs["result"])
            if kwargs.get("failure_at") == category:
                forwarded["failure"] = kwargs["failure"]
            assert function(*args, **forwarded) is kwargs["result"]
        return kwargs["result"]

    monkeypatch.setattr(source, "load", root)
    monkeypatch.setattr(cli, "load", root)
    return cli, source, invoked, originals


def observed(calls: Any, *, enabled: bool = True) -> tool.Observer:
    cli, _, _, _ = calls
    ticks = iter(range(1000))

    def clock() -> dict[str, Any]:
        t = float(next(ticks))
        return dict(cpu=t, wall=2 * t, pid=os.getpid(), thread=threading.get_ident())

    observer = tool.Observer(enabled=enabled, read_clock=clock)
    with observer.hooks():
        for i in range(3):
            with observer.read(i):
                if i:
                    token = object()
                    assert cli.load(token, result=token) is token
    return observer


@pytest.mark.parametrize("enabled", [False, True])
def test_forwarding_nested_arithmetic_and_identity(calls: Any, enabled: bool) -> None:
    cli, source, invoked, originals = calls
    observer = observed(calls, enabled=enabled)
    rows = tool.validate_state(
        observer.state(),
        observer.reads,
        enabled=enabled,
        pid=os.getpid(),
        thread=threading.get_ident(),
    )
    assert len(invoked) == 12
    assert all(
        getattr(module, name) is function for module, name, function in originals
    )
    assert cli.load is source.load
    assert sum(r["selected_calls"] for r in rows) == (14 if enabled else 0)
    assert [r["read_cpu_seconds"] for r in rows] == (
        [1, 15, 15] if enabled else [1, 1, 1]
    )
    if enabled:
        assert rows[1]["source_cpu_seconds"] == 13
        assert rows[1]["remaining_source_cpu_seconds"] == 7
        assert rows[1]["outside_source_cpu_seconds"] == 2
        assert rows[1]["child_cpu_seconds"] == dict(
            previous_sources=1,
            compact_game=2,
            parent_replay=1,
            original_contexts=1,
            original_boundaries=1,
        )
    with pytest.raises(ArithmeticError):
        with observer.hooks():
            pass


def test_proxy_keeps_defining_module_and_unselected_members(
    calls: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    cli, source, _, originals = calls
    module = source.old_sources
    contract = module.contract
    unselected = {name: object() for name in ("selected", "selected_name", "delegate")}
    for name, token in unselected.items():
        monkeypatch.setattr(module, name, token, raising=False)
    observer = tool.Observer(enabled=True)
    with observer.hooks():
        assert source.old_sources is not module
        assert source.old_sources.contract is contract
        assert source.old_sources.__name__ == module.__name__
        assert all(
            getattr(source.old_sources, name) is token
            for name, token in unselected.items()
        )
        assert module.load is originals[0][2]
        with pytest.raises(dataclasses.FrozenInstanceError):
            source.old_sources.selected_name = "contract"
        # Unrelated calls within a read but outside its source root pass through.
        with observer.read(0):
            token = object()
            assert source.old_sources.load(token, result=token) is token
            assert source.build_game(token, result=token) is token
        assert observer.regions.total == 0
        assert cli.load is not source.load
    assert source.old_sources is module
    assert cli.load is source.load
    assert observer.state()["restored"] is True


@pytest.mark.parametrize("failure_at", sorted(set(tool.CHILDREN)))
def test_original_error_and_partial_events_survive_retention_failure(
    calls: Any, failure_at: str
) -> None:
    cli, source, _, _ = calls
    primary = LookupError("original source failure")

    def sink(row: dict[str, Any]) -> None:
        if row["status"] == "partial":
            raise OSError("secondary write failure")

    observer = tool.Observer(enabled=True, read_sink=sink)
    with pytest.raises(LookupError) as raised:
        with observer.hooks(), observer.read(0):
            cli.load(object(), result=object(), failure_at=failure_at, failure=primary)
    assert raised.value is primary
    assert observer.reads[0]["status"] == "partial"
    assert observer.reads[0]["events"]
    assert observer.state()["restored"] is True
    assert cli.load is source.load
    assert tool.BUSY is False


@pytest.mark.parametrize(
    "case", ["root_recursion", "nested_scope", "cap", "reentrant_sink"]
)
def test_unsupported_scopes_fail_and_restore(calls: Any, case: str) -> None:
    cli, source, _, _ = calls
    observer = tool.Observer(enabled=True, maximum=1 if case == "cap" else 32)
    if case == "reentrant_sink":
        observer.event_sink = lambda index, row: cli.load(result=object())
    with pytest.raises(ArithmeticError):
        with observer.hooks(), observer.read(0):
            if case == "nested_scope":
                with tool.Observer(enabled=False).hooks():
                    pass
            else:
                cli.load(result=object(), recursive=case == "root_recursion")
    assert observer.state()["restored"] is True
    assert cli.load is source.load
    assert not tool.BUSY


def test_late_aliases_restore_function_and_module(
    calls: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, source, _, _ = calls
    late = ModuleType("poker_ai.source_phase_late")
    monkeypatch.setitem(sys.modules, late.__name__, late)
    original_module, original_function = source.old_sources, source.build_game
    late_api: Any = late
    observer = tool.Observer(enabled=True)
    with observer.hooks():
        late_api.module = source.old_sources
        late_api.function = source.build_game
    assert late_api.module is original_module
    assert late_api.function is original_function
    assert observer.state()["aliases_remaining"] == 0


@pytest.mark.parametrize(
    "damage",
    [
        "row_extra",
        "row_missing",
        "clock_extra",
        "bool_clock",
        "nan",
        "negative",
        "pid",
        "order",
        "parent_bool",
        "index_bool",
        "read_bool",
        "event_bool",
        "event_missing",
        "event_order",
        "root_overlap",
        "child_overlap",
        "child_outside",
        "root_outside",
        "errors",
        "incomplete",
    ],
)
def test_corrupt_nested_records_rejected(calls: Any, damage: str) -> None:
    row = copy.deepcopy(observed(calls).reads[1])
    items = row["ledger"]["rows"]
    if damage == "row_extra":
        items.append(copy.deepcopy(items[-1]))
    elif damage == "row_missing":
        items.pop()
    elif damage == "clock_extra":
        items[1]["before"]["extra"] = 0
    elif damage == "bool_clock":
        items[1]["before"]["cpu"] = True
    elif damage == "nan":
        items[1]["before"]["cpu"] = float("nan")
    elif damage == "negative":
        items[1]["before"]["cpu"] = -1
    elif damage == "pid":
        items[1]["before"]["pid"] += 1
    elif damage == "order":
        items[1]["category"] = "compact_game"
    elif damage == "parent_bool":
        items[1]["parent"] = False
    elif damage == "index_bool":
        items[1]["index"] = True
    elif damage == "read_bool":
        row["index"] = True
    elif damage == "event_bool":
        row["events"][1]["index"] = True
    elif damage == "event_missing":
        row["events"].pop()
    elif damage == "event_order":
        row["events"][1:3] = reversed(row["events"][1:3])
    elif damage == "root_overlap":
        items[0]["after"]["cpu"] = items[0]["before"]["cpu"] - 1
    elif damage == "child_overlap":
        items[2]["before"]["cpu"] = items[1]["before"]["cpu"]
    elif damage == "child_outside":
        items[-1]["after"]["wall"] = row["after"]["wall"] + 1
    elif damage == "root_outside":
        items[0]["before"]["cpu"] = row["before"]["cpu"] - 1
    elif damage == "errors":
        row["ledger"]["errors"] = True
    else:
        items[0]["status"] = "running"
        items[0].pop("after")
    with pytest.raises(ArithmeticError):
        tool.validate_read(row, 1, enabled=True)


@pytest.mark.parametrize(
    "field",
    [
        "selected_calls",
        "read_count",
        "maximum",
        "restored",
        "enabled",
        "module_aliases_restored",
        "original_functions_unchanged",
        "pid",
        "active",
    ],
)
def test_state_types_are_strict(calls: Any, field: str) -> None:
    observer = observed(calls)
    state = observer.state()
    state[field] = int(state[field]) if type(state[field]) is bool else True
    with pytest.raises(ArithmeticError):
        tool.validate_state(
            state,
            observer.reads,
            enabled=True,
            pid=os.getpid(),
            thread=threading.get_ident(),
        )


@pytest.mark.parametrize("maximum", [True, 0, -1, 1.5])
def test_positive_typed_cap(maximum: Any) -> None:
    with pytest.raises((ValueError, TypeError)):
        tool.Observer(enabled=True, maximum=maximum)


def test_actual_archived_software_read_has_no_source_root() -> None:
    program = """import sys
from pathlib import Path
r=Path.cwd();sys.path[:0]=[str(r/'src'),str(r/'scripts')]
from poker_ai.evaluation.compact_opponent_guard import isolated
with isolated(worker=False):
 import source_phase_support as tool
 from compact_suit.cli import read
 from poker_ai.postflop.river_study import Deadline
 path=r/'results/compact-suit-learning/software/own.json'
 before=[];after=[]
 a=read(r,path,Deadline(180),before)
 observer=tool.Observer(enabled=True)
 with observer.hooks(),observer.read(0): b=read(r,path,Deadline(180),after)
 assert a==b and before==after and before[0]==a['own_replay']
 result=tool.validate_read(observer.reads[0],0,enabled=True)
 assert result['selected_calls']==0 and observer.state()['restored'] is True
 assert 'pyspiel' not in sys.modules
 print('actual archived software replay identical; zero source roots; '
       'not real cost-loader coverage')
"""
    result = subprocess.run(
        [sys.executable, "-c", program], cwd=ROOT, capture_output=True, text=True
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_wrong_process_cannot_enter_scope(
    calls: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    observer = tool.Observer(enabled=True)
    pid = os.getpid()
    monkeypatch.setattr(os, "getpid", lambda: pid + 1)
    with pytest.raises(ArithmeticError):
        with observer.hooks():
            pass
    assert not tool.BUSY


def test_other_thread_cannot_enter_scope(calls: Any) -> None:
    observer = tool.Observer(enabled=True)
    failures = []

    def enter() -> None:
        try:
            with observer.hooks():
                pass
        except BaseException as error:
            failures.append(error)

    worker = threading.Thread(target=enter)
    worker.start()
    worker.join()
    assert len(failures) == 1 and isinstance(failures[0], ArithmeticError)
    assert not tool.BUSY


@pytest.mark.parametrize("enabled", [False, True])
def test_changed_module_alias_refused_before_scope(
    calls: Any, monkeypatch: pytest.MonkeyPatch, enabled: bool
) -> None:
    _, source, _, _ = calls
    monkeypatch.setattr(source, "old_sources", object())
    observer = tool.Observer(enabled=enabled)
    with pytest.raises(ArithmeticError):
        with observer.hooks():
            pass
    assert not tool.BUSY


def test_defining_module_mutation_detected(calls: Any) -> None:
    _, source, _, originals = calls
    module, member, original = originals[0]
    observer = tool.Observer(enabled=True)
    try:
        with pytest.raises(ArithmeticError, match="restoration"):
            with observer.hooks():
                setattr(module, member, object())
        assert observer.state()["original_functions_unchanged"] is False
        assert source.old_sources is module
    finally:
        setattr(module, member, original)
    assert not tool.BUSY


@pytest.mark.parametrize("with_primary", [False, True])
def test_cleanup_attempts_others_and_preserves_original_error(
    calls: Any, with_primary: bool
) -> None:
    cli, source, _, _ = calls
    original = source.build_game
    original_type = type(source)

    class RefuseOneRestoration(ModuleType):
        def __setattr__(self, name: str, value: Any) -> None:
            if name == "build_game" and value is original:
                raise RuntimeError("fixture cannot restore this alias")
            super().__setattr__(name, value)

    primary = LookupError("original body error")
    observer = tool.Observer(enabled=True)
    source.__class__ = RefuseOneRestoration
    try:
        with pytest.raises(LookupError if with_primary else ArithmeticError) as raised:
            with observer.hooks():
                if with_primary:
                    raise primary
        if with_primary:
            assert raised.value is primary
        assert observer.cleanup_failures
        assert observer.state()["restored"] is False
        assert cli.load is source.load
        assert not isinstance(source.old_sources, tool.ModuleAlias)
        assert not isinstance(source.sampled_parent, tool.ModuleAlias)
    finally:
        source.__class__ = original_type
        source.build_game = original
    assert not tool.BUSY
