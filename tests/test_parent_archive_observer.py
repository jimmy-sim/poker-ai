"""Exact nested archive inventory and fail-closed clocks; no new training."""

import copy
import os
import subprocess
import sys
import threading
from collections import Counter
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import parent_archive_support as tool

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def calls(monkeypatch: pytest.MonkeyPatch) -> Any:
    from poker_ai.evaluation import compact_fixed_inputs as full
    from poker_ai.evaluation import compact_opponent_sources as source
    from poker_ai.evaluation import compact_sampled_inputs as inputs
    from poker_ai.evaluation import compact_sampled_own as own
    from poker_ai.evaluation import compact_sampled_prior as prior
    from poker_ai.postflop import compact_full_artifacts as files
    from poker_ai.postflop import compact_sampled_state as state

    invoked: list[Any] = []
    definitions: list[Any] = []

    def callback(category: str) -> Any:
        def function(*args: Any, **kwargs: Any) -> Any:
            invoked.append((category, args, dict(kwargs)))
            if kwargs.get("failure_at") == category:
                raise kwargs["failure"]
            return kwargs["result"]

        return function

    for category, defining, name, holder, alias in (
        ("sampled_contexts", inputs, "game_contexts", None, None),
        ("sampled_decode", state, "decode", own, "decode"),
        ("sampled_scores", state, "scores", own, "scores"),
        ("full_decode", files, "decode", None, None),
    ):
        function = callback(category)
        monkeypatch.setattr(defining, name, function)
        if holder is not None:
            assert alias is not None
            monkeypatch.setattr(holder, alias, function)
        definitions.append((defining, name, function))
    # Two context callsites share one defining function; both module aliases
    # must remain independently wrapped while the defining module is untouched.
    own_api: Any = own
    full_api: Any = full
    prior_api: Any = prior
    source_api: Any = source

    def gather(*args: Any, **kwargs: Any) -> Any:
        invoked.append(("sampled_gather", args, dict(kwargs)))
        assert own_api.inputs.game_contexts(*args, **kwargs) is kwargs["result"]
        for _ in range(36):
            assert own_api.decode(*args, **kwargs) is kwargs["result"]
            for _ in range(3):
                assert own_api.decode(*args, **kwargs) is kwargs["result"]
                assert own_api.scores(*args, **kwargs) is kwargs["result"]
        return kwargs["result"]

    def verify(*args: Any, **kwargs: Any) -> Any:
        invoked.append(("prior_full", args, dict(kwargs)))
        for _ in range(72):
            assert prior_api.old.decode(*args, **kwargs) is kwargs["result"]
        return kwargs["result"]

    def replay(*args: Any, **kwargs: Any) -> Any:
        invoked.append((tool.ROOT, args, dict(kwargs)))
        if kwargs.get("recursive"):
            return source_api.sampled_parent.replay_sources(*args, **kwargs)
        assert full_api.old_own.gather(*args, **kwargs) is kwargs["result"]
        assert full_api.old_inputs.game_contexts(*args, **kwargs) is kwargs["result"]
        for _ in range(72):
            assert full_api.files.decode(*args, **kwargs) is kwargs["result"]
        assert full_api.prior_full(*args, **kwargs) is kwargs["result"]
        return kwargs["result"]

    for defining, name, function in (
        (own, "gather", gather),
        (prior, "verify", verify),
        (full, "replay_sources", replay),
    ):
        monkeypatch.setattr(defining, name, function)
        definitions.append((defining, name, function))
    monkeypatch.setattr(full, "prior_full", verify)
    return source, full, invoked, definitions


def observed(calls: Any, *, enabled: bool = True) -> tool.Observer:
    source, _, _, _ = calls
    ticks = iter(range(10000))

    def clock() -> dict[str, Any]:
        t = float(next(ticks))
        return dict(cpu=t, wall=2 * t, pid=os.getpid(), thread=threading.get_ident())

    observer = tool.Observer(enabled=enabled, read_clock=clock)
    with observer.hooks():
        for i in range(3):
            with observer.read(i):
                if i:
                    token = object()
                    assert (
                        source.sampled_parent.replay_sources(token, result=token)
                        is token
                    )
    return observer


def test_predeclared_inventory() -> None:
    rows = tool.inventory()
    assert len(rows) == 401
    assert rows[255] == ("full_contexts", 0)
    assert rows[328] == ("prior_full", 0)
    assert rows[-1] == ("prior_decode", 328)
    assert Counter(x[0] for x in rows) == {
        tool.ROOT: 1,
        "sampled_gather": 1,
        "sampled_contexts": 1,
        "sampled_decode": 144,
        "sampled_scores": 108,
        "full_contexts": 1,
        "full_decode": 72,
        "prior_full": 1,
        "prior_decode": 72,
    }


@pytest.mark.parametrize("enabled", [False, True])
def test_forwarding_exact_hierarchy_arithmetic_and_identity(
    calls: Any, enabled: bool
) -> None:
    _, _, invoked, definitions = calls
    observer = observed(calls, enabled=enabled)
    results = tool.validate_state(
        observer.state(),
        observer.reads,
        enabled=enabled,
        pid=os.getpid(),
        thread=threading.get_ident(),
    )
    assert len(invoked) == 802
    assert observer.state()["selected_calls"] == (802 if enabled else 0)
    for _, args, kw in invoked:
        assert len(args) == 1 and args[0] is kw["result"]
    for defining, name, function in definitions:
        assert getattr(defining, name) is function
    assert not tool.BUSY
    assert results[0]["selected_calls"] == 0
    for result in results[1:]:
        if enabled:
            assert result["archive_cpu_seconds"] == 801
            assert result["read_cpu_seconds"] == 803
            assert result["outside_archive_cpu_seconds"] == 2
            assert result["inclusive_cpu_seconds"]["sampled_gather"] == 507
            assert result["inclusive_cpu_seconds"]["prior_full"] == 145
            assert result["residual_cpu_seconds"]["sampled_gather"] == 254
            assert result["residual_cpu_seconds"]["prior_full"] == 73
            assert sum(result["residual_cpu_seconds"].values()) == 801
        else:
            assert result["archive_cpu_seconds"] == 0


@pytest.mark.parametrize(
    "damage",
    [
        "extra",
        "missing",
        "parent",
        "order",
        "index_bool",
        "parent_bool",
        "read_bool",
        "clock_extra",
        "bool_clock",
        "nan",
        "inf",
        "negative",
        "pid",
        "thread",
        "overlap",
        "escape",
        "reversed",
        "root_escape",
        "event_missing",
        "event_order",
        "event_bool",
        "event_after",
        "partial",
        "errors",
        "ledger_pid_bool",
        "read_index_bool",
        "extra_row_field",
    ],
)
def test_corrupt_saved_tree_rejected(calls: Any, damage: str) -> None:
    row = copy.deepcopy(observed(calls).reads[1])
    rows = row["ledger"]["rows"]
    item = rows[4]
    if damage == "extra":
        rows.append(copy.deepcopy(item))
    elif damage == "missing":
        rows.pop()
    elif damage == "parent":
        item["parent"] = 0
    elif damage == "order":
        item["category"] = "sampled_scores"
    elif damage == "index_bool":
        item["index"] = True
    elif damage == "parent_bool":
        item["parent"] = True
    elif damage == "read_bool":
        item["read"] = True
    elif damage == "clock_extra":
        item["before"]["extra"] = 0
    elif damage == "bool_clock":
        item["before"]["cpu"] = True
    elif damage in ("nan", "inf"):
        item["before"]["cpu"] = float(damage)
    elif damage == "negative":
        item["before"]["cpu"] = -1
    elif damage in ("pid", "thread"):
        item["before"][damage] += 1
    elif damage == "overlap":
        item["before"]["cpu"] = rows[3]["before"]["cpu"]
    elif damage == "escape":
        item["after"]["wall"] = rows[1]["after"]["wall"] + 1
    elif damage == "reversed":
        item["after"]["cpu"] = item["before"]["cpu"] - 1
    elif damage == "root_escape":
        rows[0]["before"]["cpu"] = row["before"]["cpu"] - 1
    elif damage == "event_missing":
        row["events"].pop()
    elif damage == "event_order":
        row["events"][3:5] = reversed(row["events"][3:5])
    elif damage == "event_bool":
        row["events"][0]["read"] = True
    elif damage == "event_after":
        row["events"][-1]["after"]["cpu"] += 1
    elif damage == "partial":
        item["status"] = "primary_failed"
    elif damage == "errors":
        row["ledger"]["errors"] = True
    elif damage == "ledger_pid_bool":
        row["ledger"]["pid"] = True
    elif damage == "read_index_bool":
        row["index"] = True
    else:
        item["extra"] = 0
    with pytest.raises(ArithmeticError):
        tool.validate_read(row, 1, enabled=True)


@pytest.mark.parametrize(
    "field",
    [
        "selected_calls",
        "maximum",
        "restored",
        "enabled",
        "active",
        "pid",
        "module_aliases_restored",
        "original_functions_unchanged",
        "read_count",
    ],
)
def test_strict_state_types(calls: Any, field: str) -> None:
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
def test_typed_positive_cap(maximum: Any) -> None:
    with pytest.raises((ValueError, TypeError)):
        tool.Observer(enabled=True, maximum=maximum)


@pytest.mark.parametrize("mode", ["cap", "recursive", "failure", "bad_parent"])
def test_partial_failure_kept_and_aliases_restored(calls: Any, mode: str) -> None:
    source, full, _, definitions = calls
    observer = tool.Observer(enabled=True, maximum=3 if mode == "cap" else 1024)
    primary = LookupError("same primary instance")
    with pytest.raises(LookupError if mode == "failure" else ArithmeticError) as raised:
        with observer.hooks(), observer.read(0):
            token = object()
            kw: dict[str, Any] = dict(result=token)
            if mode == "recursive":
                kw["recursive"] = True
            if mode == "failure":
                kw.update(failure_at="sampled_decode", failure=primary)
            if mode == "bad_parent":
                observer.regions.wrap(
                    tool.ROOT,
                    lambda: full.old_own.decode(token, result=token),
                )()
            else:
                source.sampled_parent.replay_sources(token, **kw)
    if mode == "failure":
        assert raised.value is primary
    assert observer.reads[0]["status"] == "partial"
    assert observer.state()["restored"] is True
    assert all(getattr(m, n) is f for m, n, f in definitions)
    assert not tool.BUSY


def test_outside_root_passthrough_and_proxy_forwarding(calls: Any) -> None:
    _, full, invoked, _ = calls
    observer = tool.Observer(enabled=True)
    with observer.hooks(), observer.read(0):
        marker = object()
        assert full.old_inputs.game_contexts(marker, result=marker) is marker
        assert full.old_inputs.protocol is full.old_own.inputs.protocol
    assert observer.regions.total == 0
    assert len(invoked) == 1
    tool.validate_read(observer.reads[0], 0, enabled=True)


def test_late_function_and_module_aliases_restored(
    calls: Any, monkeypatch: Any
) -> None:
    from poker_ai.evaluation import compact_sampled_own as own
    from poker_ai.evaluation import compact_sampled_prior as prior

    own_api: Any = own
    prior_api: Any = prior
    original = own_api.decode
    module = prior_api.old
    observer = tool.Observer(enabled=True)
    with observer.hooks():
        monkeypatch.setattr(
            prior, "late_function_fixture", own_api.decode, raising=False
        )
        monkeypatch.setattr(own, "late_module_fixture", prior_api.old, raising=False)
    assert prior_api.late_function_fixture is original
    assert own_api.late_module_fixture is module
    assert observer.state()["aliases_remaining"] == 0


@pytest.mark.parametrize("enabled", [False, True])
def test_changed_import_alias_refused(
    calls: Any, monkeypatch: Any, enabled: bool
) -> None:
    _, full, _, _ = calls
    monkeypatch.setattr(full, "prior_full", object())
    observer = tool.Observer(enabled=enabled)
    with pytest.raises(ArithmeticError):
        with observer.hooks():
            pass
    assert not tool.BUSY


def test_defining_module_change_detected(calls: Any) -> None:
    _, _, _, definitions = calls
    module, name, original = definitions[0]
    observer = tool.Observer(enabled=True)
    try:
        with pytest.raises(ArithmeticError, match="restoration"):
            with observer.hooks():
                setattr(module, name, object())
        assert observer.state()["original_functions_unchanged"] is False
    finally:
        setattr(module, name, original)
    assert not tool.BUSY


def test_cross_thread_refused(calls: Any) -> None:
    observer = tool.Observer(enabled=True)
    failures = []

    def enter() -> None:
        try:
            with observer.hooks():
                pass
        except BaseException as error:
            failures.append(error)

    thread = threading.Thread(target=enter)
    thread.start()
    thread.join()
    assert len(failures) == 1 and isinstance(failures[0], ArithmeticError)
    assert not tool.BUSY


def test_cross_process_refused(calls: Any, monkeypatch: Any) -> None:
    observer = tool.Observer(enabled=True)
    pid = os.getpid()
    monkeypatch.setattr(os, "getpid", lambda: pid + 1)
    with pytest.raises(ArithmeticError):
        with observer.hooks():
            pass
    assert not tool.BUSY


def test_actual_software_replay_unchanged_zero_roots() -> None:
    program = """import sys
from pathlib import Path
r=Path.cwd();sys.path[:0]=[str(r/'src'),str(r/'scripts')]
from poker_ai.evaluation.compact_opponent_guard import isolated
with isolated(worker=False):
 import parent_archive_support as tool
 from compact_suit.cli import read
 from poker_ai.postflop.river_study import Deadline
 path=r/'results/compact-suit-learning/software/own.json'
 before=[];after=[]
 a=read(r,path,Deadline(180),before)
 observer=tool.Observer(enabled=True)
 with observer.hooks(),observer.read(0): b=read(r,path,Deadline(180),after)
 assert a==b and before==after and before[0]==a['own_replay']
 assert tool.validate_read(observer.reads[0],0,enabled=True)['selected_calls']==0
 assert observer.state()['restored'] is True and 'pyspiel' not in sys.modules
 print('actual saved software replay identical; zero roots; not cost coverage')
"""
    result = subprocess.run(
        [sys.executable, "-c", program], cwd=ROOT, capture_output=True, text=True
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("with_primary", [False, True])
def test_cleanup_continues_and_preserves_primary(
    calls: Any, with_primary: bool
) -> None:
    from types import ModuleType

    _, full, _, _ = calls
    original = full.prior_full
    original_type = type(full)

    class RefuseOneRestoration(ModuleType):
        def __setattr__(self, name: str, value: Any) -> None:
            if name == "prior_full" and value is original:
                raise RuntimeError("fixture cannot restore this alias")
            super().__setattr__(name, value)

    observer = tool.Observer(enabled=True)
    primary = LookupError("same primary error")
    full.__class__ = RefuseOneRestoration
    try:
        with pytest.raises(LookupError if with_primary else ArithmeticError) as caught:
            with observer.hooks():
                if with_primary:
                    raise primary
        if with_primary:
            assert caught.value is primary
        assert observer.cleanup_failures
        assert observer.state()["restored"] is False
        assert not isinstance(full.old_own, tool.ModuleAlias)
        assert not isinstance(full.old_inputs, tool.ModuleAlias)
        assert not isinstance(full.files, tool.ModuleAlias)
    finally:
        full.__class__ = original_type
        full.prior_full = original
    assert not tool.BUSY


@pytest.mark.parametrize("at", ["start", "end"])
def test_event_retention_failure_is_partial_and_restores(calls: Any, at: str) -> None:
    source, _, _, _ = calls
    primary = OSError("fixture cannot retain event")

    def sink(index: int, row: dict[str, Any]) -> None:
        if row["category"] == "sampled_decode" and row["status"] == (
            "running" if at == "start" else "complete"
        ):
            raise primary

    observer = tool.Observer(enabled=True, event_sink=sink)
    token = object()
    with pytest.raises(OSError) as caught:
        with observer.hooks(), observer.read(0):
            source.sampled_parent.replay_sources(token, result=token)
    assert caught.value is primary
    assert observer.reads[0]["status"] == "partial"
    assert observer.state()["restored"] is True
    assert observer.state()["errors"] > 0
    assert not tool.BUSY


def test_scope_cannot_be_reused_or_nested(calls: Any) -> None:
    observer = tool.Observer(enabled=True)
    with observer.hooks():
        with pytest.raises(ArithmeticError):
            with tool.Observer(enabled=False).hooks():
                pass
    with pytest.raises(ArithmeticError):
        with observer.hooks():
            pass
    assert not tool.BUSY
