"""Software fixtures only: no real reader collection before qualification."""

import copy
import gzip
import importlib
import json
import os
import subprocess
import sys
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
tool = importlib.import_module("collect_reader_helpers")


def software_ledger(tmp_path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    events: list[dict[str, Any]] = []
    result = subprocess.CompletedProcess([], 0, b"unchanged", None)
    recorder = tool.Recorder(
        tmp_path, ("status",), original=lambda *a, **k: result, emit=events.append
    )
    assert recorder(["git", "-C", str(tmp_path), "status"]) is result
    census = dict(
        registered=True,
        active=False,
        events_by_ordinal={"0": 1},
        unassigned=0,
        audit_arguments_retained=False,
    )
    return dict(rows=recorder.rows, summary=recorder.summary(), census=census), events


def test_raw_ledger_and_stream_identity(tmp_path: Path) -> None:
    ledger, events = software_ledger(tmp_path)
    tool.validate_ledger(ledger, events, os.getpid(), ["status"])
    assert "unchanged" not in json.dumps(ledger)


@pytest.mark.parametrize(
    "kind",
    [
        "clock",
        "pid",
        "ordinal",
        "status",
        "category",
        "hash",
        "summary",
        "census",
        "events",
    ],
)
def test_ledger_tampering_rejected(tmp_path: Path, kind: str) -> None:
    ledger, events = copy.deepcopy(software_ledger(tmp_path))
    row = ledger["rows"][0]
    if kind == "clock":
        row["observation"]["interval"]["clocks"]["perf_seconds"] += 1
    elif kind == "pid":
        row["before"]["pid"] += 1
    elif kind == "ordinal":
        row["ordinal"] = True
    elif kind == "status":
        row["returncode"] = 7
    elif kind == "category":
        row["category"] = "git push"
    elif kind == "hash":
        row["stdout"]["sha256"] = "raw SECRET"
    elif kind == "summary":
        ledger["summary"]["unsupported"] = 1
    elif kind == "census":
        ledger["census"]["events_by_ordinal"]["0"] = 2
    else:
        events.pop()
    with pytest.raises(ArithmeticError):
        tool.validate_ledger(ledger, events, os.getpid(), ["status"])


# The real audit-hook fixtures use separate interpreters: hooks cannot be removed
# and must not perturb later project tests. Their roots are tiny temporary repos.
PROGRAM = """
import json,os,pathlib,subprocess,sys
from subprocess import run as old_run, Popen as old_popen, check_output as old_output
import collect_reader_helpers as t
root=pathlib.Path(sys.argv[1]);output=root/'out';output.mkdir()
pattern=sys.argv[2];cmd=['git','-C',str(root),'status','--porcelain']
sentinel={'accepted':True}
def call():
 if pattern=='initial_failure':
  import helper_call_accounting as h
  def fail():raise OSError('fixture')
  h.snapshot=fail
 subprocess.run(cmd,check=True,capture_output=True,env=dict(os.environ,PRIVATE_VALUE='SECRET'))
 if pattern=='run_alias':old_run(cmd,check=True,capture_output=True)
 elif pattern=='popen_alias':
  p=old_popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  p.communicate();assert p.returncode==0
 elif pattern=='output_alias':assert old_output(cmd)==b''
 elif pattern=='unsupported':
  subprocess.run(['git','--version'],capture_output=True,check=True)
 return sentinel
try:
 result=t.observe(root,{'commands':['status']},output,call)
 assert result is sentinel
 status='complete'
except (ArithmeticError,OSError):status='incomplete'
ledger=t.load_compressed(output/'ledger.json.gz')
assert 'SECRET' not in json.dumps(ledger)
assert str(root) not in json.dumps(ledger)
print(json.dumps({'status':status,'ledger':ledger}))
"""


@pytest.mark.parametrize(
    "pattern",
    [
        "normal",
        "output_alias",
        "run_alias",
        "popen_alias",
        "initial_failure",
        "unsupported",
    ],
)
def test_independent_process_census_catches_aliases(
    tmp_path: Path, pattern: str
) -> None:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / ".git/info/exclude").write_text("out/\n")
    result = subprocess.run(
        [sys.executable, "-c", PROGRAM, str(tmp_path), pattern],
        capture_output=True,
        text=True,
        check=True,
        env={"PATH": os.environ.get("PATH", ""), "PYTHONPATH": str(ROOT / "scripts")},
    )
    saved = json.loads(result.stdout)
    complete = pattern in ("normal", "output_alias")
    assert saved["status"] == ("complete" if complete else "incomplete")
    bypass = pattern in ("run_alias", "popen_alias")
    assert saved["ledger"]["census"]["unassigned"] == (1 if bypass else 0)
    if pattern == "initial_failure":
        assert saved["ledger"]["summary"]["observer_errors"] == 1
        assert (
            saved["ledger"]["rows"][0]["status"] == "observer_failed_before_execution"
        )
    assert saved["ledger"]["census"]["active"] is False


def test_suppressed_audit_hook_blocks_target(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    recorder = tool.Recorder(tmp_path, ("status",))
    census = tool.Census(recorder)
    monkeypatch.setattr(sys, "addaudithook", lambda *a: None)
    with pytest.raises(ArithmeticError, match="suppressed"):
        with census.counting():
            pytest.fail("target must not start")
    assert not census.active


def fixture_contract() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    import numpy

    source = dict(git_commit="a" * 40, fingerprint="fixture-only", sha256={})
    c = dict(
        commands=["status"],
        own="fixture-own.json",
        historical_anchor="fixture-anchor.json",
        original_source_fingerprint="fixture-only",
        input_sha256={"fixture-own.json": "b" * 64, "fixture-anchor.json": "c" * 64},
        runtime=dict(python=sys.version.split()[0], numpy=numpy.__version__),
        order=["control", "observed"],
        maximum_child_seconds=900,
        maximum_pair_seconds=1800,
    )
    c.update(
        original_own_canonical_sha256="c" * 64,
        expected_source_sha256="fixture-only",
        reader_scope="fictional_reader_scope",
        expected_replay=dict(unique_profiles=432, fixed_conditions=1152),
        idle_control=dict(
            path="/fixture/idle-control", arguments=["-i"], sha256="d" * 64
        ),
    )
    witness = dict(
        own_sha256="b" * 64,
        complete_own_sha256="c" * 64,
        source_sha256="fixture-only",
        reader_scope=c["reader_scope"],
        computed_replay=copy.deepcopy(c["expected_replay"]),
        validation_cache=dict(
            requests=2,
            original_traversals=1,
            hits=1,
            rejections=0,
            fallbacks=0,
            successful_proofs=1,
            enabled=True,
        ),
    )
    return c, source, witness


def test_missing_qualification_retains_failure_before_target(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    c, source, _ = fixture_contract()
    monkeypatch.setattr(tool, "binding", lambda *a, **k: (c, source))
    monkeypatch.setattr(
        tool,
        "control",
        lambda *a: dict(
            c["idle_control"],
            requested=True,
            assertion_state_independently_audited=False,
        ),
    )

    def fail(*args: Any) -> None:
        raise ArithmeticError("SECRET missing checks")

    monkeypatch.setattr(tool, "checked", fail)
    monkeypatch.setattr(
        tool, "target", lambda *a: pytest.fail("unqualified target executed")
    )
    assert tool.child(tmp_path, "observed", tmp_path, time.perf_counter()) == 1
    row = json.loads((tmp_path / "child.json").read_text())
    assert (
        row["status"] == "failed_retained" and row["failure_kind"] == "ArithmeticError"
    )
    assert "SECRET" not in json.dumps(row)
    assert not (tmp_path / "events.jsonl.gz").exists()


def test_control_calls_unchanged_target_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import numpy

    c, source, witness = fixture_contract()
    c["runtime"] = dict(python=sys.version.split()[0], numpy=numpy.__version__)
    checks = tmp_path / tool.FOLDER / "checks.json"
    checks.parent.mkdir(parents=True)
    checks.write_text("fixture only")
    monkeypatch.setattr(tool, "binding", lambda *a, **k: (c, source))
    monkeypatch.setattr(
        tool,
        "control",
        lambda *a: dict(
            c["idle_control"],
            requested=True,
            assertion_state_independently_audited=False,
        ),
    )
    monkeypatch.setattr(tool, "checked", lambda *a: None)
    calls = []

    def target(*args: Any) -> dict[str, Any]:
        calls.append(True)
        return witness

    monkeypatch.setattr(tool, "target", target)
    assert tool.child(tmp_path, "control", tmp_path, time.perf_counter()) == 0
    row = json.loads((tmp_path / "child.json").read_text())
    assert calls == [True] and row["witness"] == witness and row["status"] == "complete"
    assert (
        row["poker_training_performed"] is False
        and row["reference_constructed"] is False
    )


def test_pair_retains_partial_failure_without_retry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    c, _, _ = fixture_contract()
    monkeypatch.setattr(tool, "contract", lambda *a: c)
    monkeypatch.setattr(
        tool,
        "control",
        lambda *a: dict(
            c["idle_control"],
            requested=True,
            assertion_state_independently_audited=False,
        ),
    )
    calls = []

    def supervise(*args: Any) -> dict[str, Any]:
        calls.append(args)
        return dict(returncode=124, interrupted="TimeoutExpired", seconds=900)

    monkeypatch.setattr(tool, "supervise", supervise)
    output = tmp_path / "results/runs/fixture"
    assert tool.pair(tmp_path, output) == 1
    saved = json.loads((output / "pair.json").read_text())
    assert saved["status"] == "failed_retained" and len(saved["measurements"]) == 1
    assert len(calls) == 1
    with pytest.raises(ValueError, match="fresh"):
        tool.pair(tmp_path, output)


def test_symbolic_ref_catalog_extension(tmp_path: Path) -> None:
    result = subprocess.CompletedProcess([], 0, b"fixture-branch", b"")
    recorder = tool.Recorder(
        tmp_path, ("symbolic-ref",), original=lambda *a, **k: result
    )
    assert (
        recorder(["git", "-C", str(tmp_path), "symbolic-ref", "--short", "HEAD"])
        is result
    )
    recorder.require_complete_coverage()
    assert recorder.rows[0]["category"] == "git symbolic-ref"


def test_contract_and_frozen_inventory_are_prospective_only() -> None:
    # Read configuration bytes only; no real publication target or source path.
    c = json.loads((ROOT / tool.CONFIG).read_text())
    assert tool.digest(ROOT / tool.CONFIG) == tool.CONFIG_SHA
    assert len(c["input_sha256"]) == 16 and c["order"] == ["control", "observed"]
    assert c["maximum_child_seconds"] == 900 and c["maximum_pair_seconds"] == 1800
    assert (
        c["poker_training_performed"]
        is c["reference_constructed"]
        is c["admission_evidence"]
        is False
    )


def saved_software_pair(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Fictional raw data for parser/report tests; never a collector result."""
    from poker_ai.postflop import compact_full_artifacts

    c, source, witness = fixture_contract()
    monkeypatch.setattr(tool, "contract", lambda *a: c)
    monkeypatch.setattr(
        tool,
        "control",
        lambda *a: dict(
            c["idle_control"],
            requested=True,
            assertion_state_independently_audited=False,
        ),
    )
    monkeypatch.setattr(tool, "binding", lambda *a, **k: (c, source))
    monkeypatch.setattr(
        tool,
        "control",
        lambda *a: dict(
            c["idle_control"],
            requested=True,
            assertion_state_independently_audited=False,
        ),
    )
    monkeypatch.setattr(tool, "checked", lambda *a: None)
    monkeypatch.setattr(compact_full_artifacts, "commit_sources", lambda *a: None)
    qual = tmp_path / tool.FOLDER / "checks.json"
    qual.parent.mkdir(parents=True)
    qual.write_text("FICTIONAL SOFTWARE FIXTURE NOT QUALIFICATION")
    output = tmp_path / "results/runs/fixture"
    ledger, _ = software_ledger(tmp_path)
    row = ledger["rows"][0]
    before = copy.deepcopy(row["before"])
    after = copy.deepcopy(before)
    after["perf_seconds"] += 0.25
    after["process_cpu_seconds"] += 0.01
    after["reaped_child_usage"]["ru_utime"] += 0.02
    after["reaped_child_usage"]["ru_stime"] += 0.003
    row["before"] = before
    row["observation"] = tool.record(before, after)
    start = copy.deepcopy(row)
    for field in ("observation", "stdout", "stderr", "returncode"):
        del start[field]
    start["status"] = "running"
    events = [start, row]
    measurements = []
    for i, mode in enumerate(c["order"]):
        folder = output / mode
        folder.mkdir(parents=True)
        a = copy.deepcopy(before)
        b = copy.deepcopy(after)
        a["pid"] = b["pid"] = os.getpid() + (1 if i == 0 else 0)
        child = dict(
            status="complete",
            mode=mode,
            pid=a["pid"],
            source=source,
            environment=dict(
                **c["runtime"],
                platform="software-fixture",
                cpu="software-fixture",
                cpu_query_status="fixture",
                logical_cpus=1,
            ),
            idle_control=dict(
                c["idle_control"],
                requested=True,
                assertion_state_independently_audited=False,
            ),
            config_sha256=tool.CONFIG_SHA,
            qualification_sha256=tool.digest(qual),
            witness=witness,
            poker_training_performed=False,
            reference_constructed=False,
            admission_evidence=False,
            target_before=a,
            target_observation=tool.record(a, b),
            execution_root=str(tmp_path),
            execution_output=str(folder),
            executable=sys.executable,
        )
        if mode == "observed":
            tool.compressed(folder / "ledger.json.gz", ledger)
            with gzip.GzipFile(
                filename=str(folder / "events.jsonl.gz"), mode="wb", mtime=0
            ) as stream:
                stream.write("".join(json.dumps(e) + "\n" for e in events).encode())
            child.update(
                ledger_sha256=tool.digest(folder / "ledger.json.gz"),
                events_sha256=tool.digest(folder / "events.jsonl.gz"),
            )
        tool.atomic(folder / "child.json", child)
        (folder / "command.log").write_text("")
        measurement = dict(
            returncode=0,
            interrupted=None,
            seconds=1,
            child_sha256=tool.digest(folder / "child.json"),
            command=[
                c["idle_control"]["path"],
                *c["idle_control"]["arguments"],
                sys.executable,
                str(tmp_path / tool.ENTRY),
                "--child",
                mode,
                "--output",
                str(folder),
            ],
        )
        tool.atomic(folder / "measurement.json", measurement)
        measurements.append(measurement)
    tool.atomic(
        output / "pair.json",
        dict(
            status="complete",
            seconds=3,
            measurements=measurements,
            admission_evidence=False,
            command_log_sha256={
                mode: tool.digest(output / mode / "command.log") for mode in c["order"]
            },
        ),
    )
    return output


def test_saved_report_uses_checked_raw_deltas(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = saved_software_pair(tmp_path, monkeypatch)
    summary = tool.report(tmp_path, output, tmp_path / "report")
    row = summary["groups"][0]
    assert summary["helpers"] == 1 and summary["original_witness_exact"] is True
    assert row["interval_wall_seconds"] == pytest.approx(0.25)
    assert row["reaped_child_user_seconds"] == pytest.approx(0.02)
    assert row["reaped_child_system_seconds"] == pytest.approx(0.003)
    assert len(summary["input_sha256"]) == 9
    with pytest.raises(FileExistsError):
        tool.report(tmp_path, output, tmp_path / "report")
    with pytest.raises(ValueError, match="outside"):
        tool.report(tmp_path, output, output / "report")


@pytest.mark.parametrize(
    "kind",
    [
        "witness",
        "source",
        "qualification",
        "pid",
        "command",
        "cap",
        "ledger",
        "missing",
        "environment",
        "log",
        "idle",
        "pair_admission",
        "pair_length",
        "bool_seconds",
        "cache",
    ],
)
def test_saved_pair_cannot_accept_changed_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    output = saved_software_pair(tmp_path, monkeypatch)
    folder = output / "observed"
    child = json.loads((folder / "child.json").read_text())
    pair = json.loads((output / "pair.json").read_text())
    m = pair["measurements"][1]
    if kind == "log":
        (folder / "command.log").write_text("tampered")
    elif kind == "idle":
        child["idle_control"]["requested"] = False
    elif kind == "pair_admission":
        pair["admission_evidence"] = True
    elif kind == "pair_length":
        pair["measurements"] = pair["measurements"][:1]
    elif kind == "bool_seconds":
        m["seconds"] = True
    elif kind == "cache":
        child["witness"]["validation_cache"].update(requests=3, hits=2)
    elif kind == "witness":
        child["witness"]["computed_replay"]["unique_profiles"] = 431
    elif kind == "source":
        child["source"]["fingerprint"] = "different"
    elif kind == "qualification":
        child["qualification_sha256"] = "0" * 64
    elif kind == "pid":
        child["pid"] += 7
    elif kind == "command":
        m["command"][5] = "control"
    elif kind == "cap":
        m["seconds"] = 901
    elif kind == "environment":
        child["environment"]["python"] = "3.12.3"
    elif kind == "ledger":
        (folder / "ledger.json.gz").write_text("tampered")
    else:
        (folder / "command.log").unlink()
    # Keep outer hashes consistent, so semantic checks still have to reject it.
    tool.atomic(folder / "child.json", child)
    m["child_sha256"] = tool.digest(folder / "child.json")
    tool.atomic(folder / "measurement.json", m)
    tool.atomic(output / "pair.json", pair)
    with pytest.raises(ArithmeticError):
        tool.verify_pair(tmp_path, output)


@pytest.mark.parametrize("bad", [None, "base312", "optional311", "hosted312"])
def test_actual_runtime_markers_required_for_each_role(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, bad: str | None
) -> None:
    from compact_cached import admission

    from poker_ai.evaluation import diagnostic_receipts

    monkeypatch.setattr(admission, "published", lambda *a: None)
    monkeypatch.setattr(diagnostic_receipts, "checks", lambda *a: None)
    folder = tmp_path / tool.FOLDER
    folder.mkdir(parents=True)
    rows = []
    for role in ("base", "optional", "hosted"):
        for minor, python, numpy in (
            ("311", "3.11.17", "2.4.6"),
            ("312", "3.12.15", "2.5.4"),
        ):
            name = role + minor
            log = (
                f"Using CPython {python}\nACTUAL_PYTHON={python}\n"
                f"ACTUAL_NUMPY={numpy}\n"
            )
            if name == bad:
                log = log.replace("ACTUAL_PYTHON=", "MATRIX_LABEL=")
            path = folder / (name + ".log")
            path.write_text(log)
            rows.append(
                dict(
                    role=role,
                    minor=minor,
                    python=python,
                    numpy=numpy,
                    log=dict(file=str(path.relative_to(tmp_path))),
                )
            )
    (folder / "checks.json").write_text(json.dumps(dict(checks=rows)))
    if bad is None:
        tool.checked(tmp_path, {})
    else:
        with pytest.raises(ArithmeticError):
            tool.checked(tmp_path, {})


@pytest.mark.parametrize("kind", ["bytes", "symlink"])
def test_changed_reader_input_rejected_before_collection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    member = tmp_path / "own.json"
    member.write_text("original fixture")
    c = dict(input_sha256={"own.json": tool.digest(member)})
    cfg = tmp_path / tool.CONFIG
    cfg.parent.mkdir()
    cfg.write_text(json.dumps(c))
    monkeypatch.setattr(tool, "CONFIG_SHA", tool.digest(cfg))
    if kind == "bytes":
        member.write_text("changed fixture")
    else:
        member.unlink()
        target = tmp_path / "other.json"
        target.write_text("original fixture")
        member.symlink_to(target)
    with pytest.raises(ArithmeticError, match="input changed"):
        tool.contract(tmp_path)


def test_relative_output_is_bound_to_absolute_child_command(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    c, _, _ = fixture_contract()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(tool, "contract", lambda *a: c)
    monkeypatch.setattr(
        tool,
        "control",
        lambda *a: dict(
            c["idle_control"],
            requested=True,
            assertion_state_independently_audited=False,
        ),
    )
    commands = []

    def supervisor(command: list[str], output: Path, cap: float) -> dict[str, Any]:
        commands.append(command)
        assert Path(command[-1]) == output.resolve() and output.is_absolute()
        return dict(returncode=0, interrupted=None, seconds=0.01)

    monkeypatch.setattr(tool, "supervise", supervisor)
    monkeypatch.setattr(tool, "verify_pair", lambda *a: None)
    assert tool.pair(tmp_path, Path("results/runs/relative")) == 0
    assert [c[-1] for c in commands] == [
        str(tmp_path / "results/runs/relative" / m) for m in c["order"]
    ]


@pytest.mark.parametrize("count", [0, 1, 2])
def test_target_calls_unchanged_reader_once_with_actual_summary_and_fresh_cache(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, count: int
) -> None:
    from compact_cached import cache as cache_module
    from compact_cached import cli

    c, _, witness = fixture_contract()
    own = {"source_sha256": "fixture-only", "scope": c["reader_scope"]}
    (tmp_path / c["own"]).write_text(json.dumps(own))
    calls = []
    state = {"inside": False, "entered": 0}

    class Cache:
        def summary(self) -> dict[str, Any]:
            assert not state["inside"]
            return dict(witness["validation_cache"])

    @contextmanager
    def cached(root: Path) -> Iterator[Cache]:
        assert root == tmp_path and not state["inside"]
        state["inside"] = True
        state["entered"] += 1
        try:
            yield Cache()
        finally:
            state["inside"] = False

    origin = time.perf_counter()

    def read(
        root: Path, path: Path, deadline: Any, observed: list[dict[str, Any]]
    ) -> dict[str, Any]:
        assert state["inside"] and root == tmp_path and path == tmp_path / c["own"]
        assert deadline.started == origin and deadline.seconds == 900
        calls.append(True)
        observed.extend([c["expected_replay"]] * count)
        return own

    monkeypatch.setattr(cache_module, "cached", cached)
    monkeypatch.setattr(cli, "read", read)
    if count == 1:
        value = tool.target(tmp_path, c, origin)
        assert value["computed_replay"] == c["expected_replay"]
        assert value["validation_cache"] == witness["validation_cache"]
        import hashlib

        assert (
            value["complete_own_sha256"]
            == hashlib.sha256(tool.canonical(own)).hexdigest()
        )
    else:
        with pytest.raises(ArithmeticError, match="one actual"):
            tool.target(tmp_path, c, origin)
    assert calls == [True] and state == {"inside": False, "entered": 1}


@pytest.mark.parametrize(
    "field",
    [
        "complete_own_sha256",
        "source_sha256",
        "reader_scope",
        "computed_replay",
        "validation_cache",
    ],
)
def test_reader_identity_cannot_hide_changed_computed_math(
    tmp_path: Path, field: str
) -> None:
    c, source, witness = fixture_contract()
    if field == "computed_replay":
        witness[field]["unique_profiles"] = 431
    elif field == "validation_cache":
        witness[field]["enabled"] = False
    else:
        witness[field] = "changed"
    with pytest.raises(ArithmeticError):
        tool.validate_witness(witness, c, source)


def test_gzip_retains_partial_events_and_original_target_error(tmp_path: Path) -> None:
    script = """
import sys,pathlib,subprocess
import collect_reader_helpers as t
r=pathlib.Path(sys.argv[1]);error=ValueError('private not retained')
def target():
 subprocess.run(['git','-C',str(r),'status','--porcelain'],capture_output=True,check=True)
 raise error
try:t.observe(r,{'commands':['status']},r/'out',target)
except ValueError as actual:assert actual is error
else:raise AssertionError('original exception lost')
x=t.load_compressed(r/'out/ledger.json.gz');assert len(x['rows'])==1
assert x['census']['active']is False
"""
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / "out").mkdir()
    (tmp_path / ".git/info/exclude").write_text("out/\n")
    subprocess.run(
        [sys.executable, "-c", script, str(tmp_path)],
        check=True,
        env={"PATH": os.environ.get("PATH", ""), "PYTHONPATH": str(ROOT / "scripts")},
    )


def test_compressed_records_are_lossless_and_deterministic(tmp_path: Path) -> None:
    data = {
        "units": "fixture",
        "rows": [{"counter": 0.125, "status": "failed_retained"}],
    }
    a, b = tmp_path / "a.gz", tmp_path / "b.gz"
    tool.compressed(a, data)
    tool.compressed(b, data)
    assert a.read_bytes() == b.read_bytes() and tool.load_compressed(a) == data
    a.write_bytes(a.read_bytes()[:-5])
    with pytest.raises(EOFError):
        tool.load_compressed(a)
