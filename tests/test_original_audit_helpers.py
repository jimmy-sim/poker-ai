"""Original-context software fixtures; never collect a real audit in tests."""

import copy
import importlib
import json
import os
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
tool = importlib.import_module("measure_original_audit")


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
    with tool.reader_observer(ROOT, {}, tmp_path):
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
    with tool.reader_observer(ROOT, {}, tmp_path), pytest.raises(ArithmeticError):
        cli.read(*args, **kwargs)
    assert not calls


def test_only_three_reads(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cli, calls = setup_fake_read(monkeypatch)
    with tool.reader_observer(ROOT, {}, tmp_path):
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
        with tool.reader_observer(ROOT, {}, tmp_path):
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
    with tool.reader_observer(ROOT, {}, tmp_path), pytest.raises(ArithmeticError):
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


def test_ledger_nested_intervals_and_coverage(tmp_path: Path) -> None:
    # Reuse three actual standalone helper ledgers only as data fixtures.
    folder = ROOT / "results/complete-reader-helper-trace/pair/observed"
    child = json.loads((folder / "child.json").read_text())
    ledger = tool.helpers.load_compressed(folder / "ledger.json.gz")
    tool.helpers.validate_ledger(
        ledger,
        [json.loads(line) for line in tool.gzip.open(folder / "events.jsonl.gz", "rt")],
        child["pid"],
        tool.contract(ROOT)["commands"],
    )
    bad = copy.deepcopy(ledger)
    bad["census"]["unassigned"] = 1
    with pytest.raises(ArithmeticError):
        tool.helpers.validate_ledger(
            bad, [], child["pid"], tool.contract(ROOT)["commands"]
        )


def ledger_fixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    import subprocess

    accounting = importlib.import_module("helper_call_accounting")
    c = tool.contract(ROOT)
    template: dict[str, Any] = tool.snapshot()

    def snap(t: float) -> dict[str, Any]:
        s = copy.deepcopy(template)
        for k in (
            "perf_seconds",
            "utc_seconds",
            "process_cpu_seconds",
            "thread_cpu_seconds",
        ):
            s[k] = t
        for kind in ("self_usage", "reaped_child_usage"):
            for k in ("ru_utime", "ru_stime"):
                s[kind][k] = t
        return s

    outer, inner, computed = [], [], []
    scopes = [
        "FICTIONAL_SIGNAL_GAMES_OWN_OPPONENT_SOFTWARE_NOT_HOLDEM",
        "OLD_OWN_OPPONENT_COST_STANDINS_NO_NEW_TRAINING",
        "OLD_OWN_OPPONENT_COST_STANDINS_NO_NEW_TRAINING",
    ]
    for i, scope in enumerate(scopes):
        a, b = snap(10 * i + 1), snap(10 * i + 9)
        x, y = snap(10 * i + 2), snap(10 * i + 8)
        h, j = snap(10 * i + 3), snap(10 * i + 7)
        outer.append(dict(scope=scope, observation=tool.record(a, b)))
        computed.append(dict(scope=scope, computed=dict(fictional=i)))
        inner.append(
            dict(
                index=i,
                status="complete",
                scope=scope,
                before=x,
                computed=dict(fictional=i),
                observation=tool.record(x, y),
            )
        )
        events: list[dict[str, Any]] = []
        snapshots = iter([h, j])
        with monkeypatch.context() as m:
            m.setattr(
                accounting, "snapshot", lambda snapshots=snapshots: next(snapshots)
            )
            recorder = tool.helpers.Recorder(
                ROOT,
                tuple(c["commands"]),
                emit=events.append,
                original=lambda *a, **k: subprocess.CompletedProcess([], 0, b"", None),
            )
            recorder(["git", "-C", str(ROOT), "status"])
        ledger = dict(
            rows=recorder.rows,
            summary=recorder.summary(),
            census=dict(
                registered=True,
                active=False,
                events_by_ordinal={"0": 1},
                unassigned=0,
                audit_arguments_retained=False,
            ),
        )
        folder = tmp_path / "reads" / str(i)
        folder.mkdir(parents=True)
        tool.helpers.compressed(folder / "ledger.json.gz", ledger)
        with tool.gzip.open(folder / "events.jsonl.gz", "wt") as stream:
            for e in events:
                stream.write(json.dumps(e) + "\n")
    (tmp_path / "old").mkdir()
    (tmp_path / "old/parent-resource-reads.json").write_text(
        json.dumps(dict(reads=outer))
    )
    (tmp_path / "inner-reads.json").write_text(json.dumps(dict(reads=inner)))
    return c, dict(pid=os.getpid()), dict(identity=dict(computed_replays=computed))


def test_complete_three_nested_ledgers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    c, child, old = ledger_fixture(tmp_path, monkeypatch)
    assert len(tool.ledgers(tmp_path, child, old, c)) == 3


@pytest.mark.parametrize(
    "kind", ["missing", "pid", "scope", "index", "computed", "interval", "outside"]
)
def test_inner_ledger_schema_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    c, child, old = ledger_fixture(tmp_path, monkeypatch)
    p = tmp_path / "inner-reads.json"
    data = json.loads(p.read_text())
    row = data["reads"][1]
    if kind == "missing":
        data["reads"].pop()
    elif kind == "pid":
        child["pid"] += 1
    elif kind in ("scope", "index", "computed"):
        row[kind] = "changed"
    elif kind == "interval":
        row["observation"]["interval"]["clocks"]["perf_seconds"] += 1
    else:
        row["before"]["perf_seconds"] = 0
        row["observation"]["before"] = copy.deepcopy(row["before"])
        row["observation"] = tool.record(row["before"], row["observation"]["after"])
    p.write_text(json.dumps(data))
    with pytest.raises(ArithmeticError):
        tool.ledgers(tmp_path, child, old, c)


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


def test_data_only_report_uses_saved_rows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    c, child, old = ledger_fixture(tmp_path / "observed", monkeypatch)
    control = tmp_path / "control"
    (control / "old").mkdir(parents=True)
    (control / "old/parent-resource-reads.json").write_bytes(
        (tmp_path / "observed/old/parent-resource-reads.json").read_bytes()
    )
    ledgers = tool.ledgers(tmp_path / "observed", child, old, c)
    verified = dict(
        originals=[dict(body_observation={"interval": {}}, resource_validation={})] * 2,
        ledgers=ledgers,
        pair=dict(measurements=[]),
    )
    monkeypatch.setattr(tool, "verify_pair", lambda *a: verified)

    def forbidden(*a: Any, **k: Any) -> None:
        raise AssertionError("data-only report cannot execute audit")

    monkeypatch.setattr(tool.original, "child", forbidden)
    monkeypatch.setattr(tool, "supervise", forbidden)
    saved = tool.report(ROOT, tmp_path)
    assert len(saved["rows"]) == 6 and saved["rows"][0]["helper_count"] is None
    assert saved["rows"][3]["helper_count"] == 1
    assert saved["rows"][3]["helper_totals"] == dict(ru_utime=4, ru_stime=4)
    assert saved["long_run_admitted"] is False
