"""Phase collection lifecycle; mocked boundaries are software fixtures only."""

import copy
import importlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
runner = importlib.import_module("profile_reader_phases")


def test_frozen_contract_preserves_all436_scientific_files() -> None:
    c, source = runner.binding(ROOT, clean=False)
    _, old = runner.previous.binding(ROOT, clean=False)
    assert len(c["input_sha256"]) == 128
    assert len(source["sha256"]) == 439
    assert {p: source["sha256"][p] for p in old["sha256"]} == old["sha256"]
    assert set(source["sha256"]) - set(old["sha256"]) == {
        runner.CONFIG,
        runner.ENTRY,
        runner.SUPPORT,
    }


@pytest.fixture
def fake_reader(monkeypatch: pytest.MonkeyPatch) -> Any:
    from compact_suit import cli

    calls = []
    sentinel = dict(scope="fixture-not-poker")

    def read(*args: Any, **kwargs: Any) -> Any:
        calls.append((args, kwargs))
        kwargs["observed"].append(dict(fixture=True))
        return sentinel

    monkeypatch.setattr(cli, "read", read)
    return cli, calls, sentinel, read


@pytest.mark.parametrize("enabled", [False, True])
def test_reader_forwarding_and_restoration(
    tmp_path: Path, fake_reader: Any, enabled: bool
) -> None:
    cli, calls, sentinel, original = fake_reader
    args = (object(), object(), object())
    with runner.observe_reader(tmp_path, enabled=enabled) as (_, receipt):
        for _ in range(3):
            assert cli.read(*args) is sentinel
    assert cli.read is original
    assert all(c[0] == args and len(c[1]["observed"]) == 1 for c in calls)
    assert len(receipt["replays"]) == 3
    saved = json.loads((tmp_path / "observer.json").read_text())
    assert saved["state"]["restored"] is True and saved["state"]["active"] is False


@pytest.mark.parametrize("damage", ["arguments", "keywords", "four_reads"])
def test_reader_call_shape_failure_retained(
    tmp_path: Path, fake_reader: Any, damage: str
) -> None:
    cli, _, _, original = fake_reader
    with runner.observe_reader(tmp_path, enabled=True), pytest.raises(ArithmeticError):
        if damage == "arguments":
            cli.read(object(), object())
        elif damage == "keywords":
            cli.read(object(), object(), object(), observed=[])
        else:
            for _ in range(4):
                cli.read(object(), object(), object())
    assert cli.read is original
    assert (
        json.loads((tmp_path / "observer.json").read_text())["state"]["restored"]
        is True
    )


@pytest.mark.parametrize("count", [0, 2])
def test_complete_computed_replay_witness_required(
    tmp_path: Path, fake_reader: Any, monkeypatch: pytest.MonkeyPatch, count: int
) -> None:
    cli = fake_reader[0]

    def bad(*args: Any, **kwargs: Any) -> Any:
        kwargs["observed"].extend({} for _ in range(count))
        return dict(scope="fixture")

    monkeypatch.setattr(cli, "read", bad)
    with runner.observe_reader(tmp_path, enabled=True), pytest.raises(ArithmeticError):
        cli.read(object(), object(), object())
    assert cli.read is bad
    assert json.loads((tmp_path / "read-0.json").read_text())["status"] == "partial"


def test_original_reader_error_survives_final_write_failure(
    tmp_path: Path, fake_reader: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    cli = fake_reader[0]
    primary = LookupError("original reader failure")
    atomic = runner.atomic

    def read(*args: Any, **kwargs: Any) -> Any:
        raise primary

    def write(path: Path, value: Any) -> None:
        if path.name == "observer.json":
            raise OSError("final write failed")
        atomic(path, value)

    monkeypatch.setattr(cli, "read", read)
    monkeypatch.setattr(runner, "atomic", write)
    with pytest.raises(LookupError) as caught:
        with runner.observe_reader(tmp_path, enabled=True):
            cli.read(object(), object(), object())
    assert caught.value is primary and cli.read is read
    assert json.loads((tmp_path / "read-0.json").read_text())["status"] == "partial"


@pytest.fixture(scope="module")
def actual_software_proof(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Actual archived software read; not a source-qualified formal measurement."""
    folder = tmp_path_factory.mktemp("phase-proof-unit")
    code = """import json,pathlib,sys
from poker_ai.evaluation.compact_opponent_guard import isolated
import profile_reader_phases as runner
with isolated(worker=False):
 proof=runner.own_math(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
assert 'pyspiel' not in sys.modules
runner.atomic(pathlib.Path(sys.argv[2])/'unit-proof.json',proof)
"""
    subprocess.run(
        [sys.executable, "-c", code, str(ROOT), str(folder)],
        env=dict(
            os.environ,
            PYTHONPATH=str(ROOT / "src") + os.pathsep + str(ROOT / "scripts"),
        ),
        check=True,
        capture_output=True,
    )
    return folder


def test_actual_proof_keeps_fixture_scope_explicit(actual_software_proof: Path) -> None:
    saved = json.loads((actual_software_proof / "unit-proof.json").read_text())
    assert saved["plain_computed_replays"] == saved["observed_computed_replays"]
    assert saved["actual_read_indices"] == [0] and saved["synthetic_read_indices"] == [
        1,
        2,
    ]
    assert len(saved["fixtures"]) == 6
    assert (
        saved["real_cost_loader_coverage"]
        is saved["independent_new_poker_math"]
        is False
    )
    assert saved["observer_state"]["selected_calls"] == 7
    assert saved["observer_state"]["restored"] is True
    assert saved["reference_constructed"] is saved["poker_training_performed"] is False


@pytest.mark.parametrize("failure", ["source", "checks", "runtime", "math"])
def test_proof_prerequisite_failure_is_retained(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    primary = LookupError(failure)

    def fail(*args: Any, **kwargs: Any) -> Any:
        raise primary

    monkeypatch.setattr(
        runner,
        "binding",
        fail if failure == "source" else lambda *a, **k: ({}, dict(sha256={})),
    )
    monkeypatch.setattr(
        runner, "checked", fail if failure == "checks" else lambda *a: None
    )
    monkeypatch.setattr(
        runner.previous, "runtime", fail if failure == "runtime" else lambda *a: None
    )
    monkeypatch.setattr(runner, "own_math", fail)
    with pytest.raises(LookupError) as caught:
        runner.proof(ROOT, tmp_path, 0.0)
    assert caught.value is primary
    saved = json.loads((tmp_path / "child.json").read_text())
    assert saved["status"] == "failed_retained"
    assert saved["reference_constructed"] is saved["poker_training_performed"] is False


@pytest.fixture
def own_publication_fixture(
    tmp_path: Path, actual_software_proof: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, dict[str, Any]]:
    """Real software proof bytes with explicitly mocked publication/source gates."""
    import profile_compact_replay as replay
    from compact_suit import admission

    folder = tmp_path / runner.FOLDER / "software"
    shutil.copytree(actual_software_proof, folder)
    (folder / "unit-proof.json").rename(folder / "proof.json")
    proof = json.loads((folder / "proof.json").read_text())
    path = tmp_path / proof["input"]["file"]
    path.parent.mkdir(parents=True)
    path.write_bytes((ROOT / proof["input"]["file"]).read_bytes())
    source: dict[str, Any] = dict(sha256={})
    origin = proof["reads"][0]["before"]["wall"] - 1.0
    seconds = proof["reads"][-1]["after"]["wall"] - origin + 1.0
    execution_output = str(ROOT / "results/runs/phase-publication-fixture")
    child = dict(
        status="complete_own_only_phase_proof",
        config_sha256=runner.CONFIG_SHA,
        source=source,
        proof_sha256=runner.digest(folder / "proof.json"),
        reference_constructed=False,
        poker_training_performed=False,
        admission_evidence=False,
        pid=proof["observer_state"]["pid"],
        thread=proof["observer_state"]["thread"],
        executable=sys.executable,
        execution_root=str(ROOT),
        execution_output=execution_output,
        started_perf_counter=origin,
        seconds=seconds - 0.1,
    )
    runner.atomic(folder / "child.json", child)
    runner.atomic(
        folder / "measurement.json",
        dict(
            returncode=0,
            interrupted=None,
            seconds=seconds,
            started_perf_counter=origin,
            command=[
                sys.executable,
                str(ROOT / runner.ENTRY),
                "--child",
                "proof",
                "--output",
                execution_output,
            ],
            child_pid=child["pid"],
            child_sha256=runner.digest(folder / "child.json"),
        ),
    )
    (folder / "command.log").write_bytes(
        b"publication fixture, not formal qualification\n"
    )
    monkeypatch.setattr(admission, "published", lambda *a: None)
    monkeypatch.setattr(replay, "authenticate_source", lambda *a: None)
    return tmp_path, source


def test_complete_positive_own_publication(
    own_publication_fixture: tuple[Path, dict[str, Any]],
) -> None:
    root, source = own_publication_fixture
    assert (
        runner.own_published(root, source)["file"]
        == runner.FOLDER + "/software/child.json"
    )


@pytest.mark.parametrize(
    "damage",
    [
        "extra",
        "reference",
        "cost_claim",
        "fixture_claim",
        "scalars",
        "events",
        "source",
        "clock",
        "pid",
        "missing",
        "input",
        "matched_wrong_inventory",
        "matched_excess_error",
        "wrong_proof_command",
        "escaping_proof_clock",
    ],
)
def test_own_publication_rejects_false_or_damaged_evidence(
    own_publication_fixture: tuple[Path, dict[str, Any]], damage: str
) -> None:
    root, source = own_publication_fixture
    folder = root / runner.FOLDER / "software"
    child = json.loads((folder / "child.json").read_text())
    proof = json.loads((folder / "proof.json").read_text())
    measurement = json.loads((folder / "measurement.json").read_text())
    if damage == "extra":
        (folder / "unlisted").write_bytes(b"extra")
    elif damage == "reference":
        child["reference_constructed"] = True
    elif damage == "cost_claim":
        proof["real_cost_loader_coverage"] = True
    elif damage == "fixture_claim":
        proof["synthetic_read_indices"] = []
    elif damage == "scalars":
        proof["plain_computed_replays"][0]["unique_profiles"] = 431
    elif damage == "events":
        (folder / "read-0-events.jsonl").write_bytes(b"")
    elif damage == "source":
        child["source"] = dict(sha256=dict(changed="x"))
    elif damage == "clock":
        measurement["seconds"] = True
    elif damage == "pid":
        measurement["child_pid"] += 1
    elif damage == "missing":
        (folder / "read-2.json").unlink()
    elif damage in ("matched_wrong_inventory", "matched_excess_error"):
        key = (
            "unique_profiles"
            if damage == "matched_wrong_inventory"
            else "maximum_error"
        )
        for name in ("plain_computed_replays", "observed_computed_replays"):
            proof[name][0][key] = 431 if key == "unique_profiles" else 100.0
        observed = json.loads((folder / "observer.json").read_text())
        observed["replays"][0]["computed"] = proof["plain_computed_replays"][0]
        runner.atomic(folder / "observer.json", observed)
    elif damage == "wrong_proof_command":
        measurement["command"][1] = "wrong-proof-entry.py"
    elif damage == "escaping_proof_clock":
        child["started_perf_counter"] = proof["reads"][0]["before"]["wall"] + 1
        measurement["started_perf_counter"] = child["started_perf_counter"]
    else:
        (root / proof["input"]["file"]).write_bytes(b"changed")
    runner.atomic(folder / "proof.json", proof)
    child["proof_sha256"] = runner.digest(folder / "proof.json")
    runner.atomic(folder / "child.json", child)
    measurement["child_sha256"] = runner.digest(folder / "child.json")
    runner.atomic(folder / "measurement.json", measurement)
    with pytest.raises(ArithmeticError):
        runner.own_published(root, source)


def synthetic_reads(
    enabled: bool, pid: int, origin: float
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Invented disjoint clocks for schema tests; never measured evidence."""
    import reader_phase_support as support

    def stamp(cpu: float) -> dict[str, Any]:
        return dict(wall=origin + cpu, cpu=cpu, pid=pid, thread=1234)

    reads = []
    for index, categories in enumerate(support.INVENTORIES):
        rows, events = [], []
        if enabled:
            for ordinal, category in enumerate(categories):
                row = dict(
                    index=ordinal,
                    read=index,
                    parent=None,
                    category=category,
                    status="complete",
                    before=stamp(index * 0.1 + ordinal * 0.01 + 0.001),
                    after=stamp(index * 0.1 + ordinal * 0.01 + 0.002),
                )
                start = copy.deepcopy(row)
                del start["after"]
                start["status"] = "running"
                rows.append(row)
                events.extend([start, copy.deepcopy(row)])
        reads.append(
            dict(
                index=index,
                status="complete",
                before=stamp(index * 0.1),
                after=stamp(index * 0.1 + 0.09),
                ledger=dict(
                    status="complete", errors=0, rows=rows, pid=pid, thread=1234
                ),
                events=events,
            )
        )
    state = dict(
        enabled=enabled,
        pid=pid,
        thread=1234,
        active=False,
        restored=True,
        aliases_remaining=0,
        original_functions_unchanged=True,
        errors=0,
        cleanup_failures=[],
        selected_calls=7 if enabled else 0,
        maximum=16,
        read_count=3,
        categories=list(support.CATEGORIES),
    )
    return state, reads


@pytest.fixture
def saved_fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Synthetic clocks and published scalar DATA, no solve or admission."""
    import profile_compact_replay as replay
    import reader_phase_support as support

    monkeypatch.setattr(replay, "authenticate_source", lambda *a: None)
    source = dict(
        sha256={},
        fingerprint="44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a",
    )
    base = json.loads(
        (ROOT / "results/compact-suit-learning/cost/0/native.json").read_text()
    )
    c = runner.contract(ROOT)
    replays = [
        dict(
            scope=scope,
            computed=json.loads(
                (
                    ROOT
                    / (
                        "results/compact-suit-learning/software/own.json"
                        if index == 0
                        else c["base_own"]
                    )
                ).read_text()
            )["own_replay"],
        )
        for index, scope in enumerate(c["expected"]["read_scopes"])
    ]
    children, measurements = [], []
    for index, mode in enumerate(("plain", "profiled")):
        pid, origin = 100 + index, 100.0 + 500 * index
        state, reads = synthetic_reads(index == 1, pid, origin)
        native = copy.deepcopy(base)
        native["normalization"].update(pid=pid, thread=1234)
        native.pop("complete_command")
        identity = runner.previous.numerical_identity(native, replays)
        native["base_implementation_config"] = native["implementation_config"]
        native["implementation_config"] = dict(
            instrumentation_config=runner.CONFIG,
            instrumentation_sha256=runner.CONFIG_SHA,
            admission_evidence=False,
        )
        native["instrumentation_scope"] = "synthetic-schema-fixture-not-measurement"
        folder = tmp_path / mode
        folder.mkdir()
        runner.atomic(
            folder / "observer.json", dict(state=state, reads=reads, replays=replays)
        )
        for ordinal, row in enumerate(reads):
            runner.atomic(folder / f"read-{ordinal}.json", row)
            (folder / f"read-{ordinal}-events.jsonl").write_bytes(
                b"".join(runner.canonical(e) + b"\n" for e in row["events"])
            )
        runner.atomic(folder / "native.json", native)
        (folder / "native-events.jsonl").write_bytes(
            (
                ROOT / "results/compact-suit-learning/cost/0/native-events.jsonl"
            ).read_bytes()
        )
        execution_output = str(ROOT / "results/runs/synthetic-phase-fixture" / mode)
        clocks = [
            dict(
                slot=w["slot"], wall_seconds=m["seconds"], cpu_seconds=m["cpu_seconds"]
            )
            for w in native["native_batch"]["workers"]
            for m in w["messages"]
            if m.get("kind") == "done"
        ]
        child = dict(
            status="complete_reader_phase_diagnostic",
            mode=mode,
            pid=pid,
            thread=1234,
            base_admission_rejected=True,
            config_sha256=runner.CONFIG_SHA,
            source=source,
            identity=identity,
            worker_body_clocks=clocks,
            body_before=dict(wall=origin, cpu=0.0, pid=pid, thread=1234),
            body_after=dict(wall=origin + 150, cpu=0.4, pid=pid, thread=1234),
            complete_body_parent_cpu_seconds=0.4,
            executable=sys.executable,
            execution_root=str(ROOT),
            execution_output=execution_output,
            summaries=support.validate_state(
                state, reads, enabled=index == 1, pid=pid, thread=1234
            ),
            raw_sha256={
                str(p.relative_to(folder)): runner.digest(p) for p in folder.iterdir()
            },
            admission_evidence=False,
            reference_constructed=True,
            poker_training_performed=False,
            reference_output_used_in_training=False,
        )
        runner.atomic(folder / "child.json", child)
        (folder / "command.log").write_bytes(b"synthetic fixture, no new execution\n")
        measurement = dict(
            command=[
                sys.executable,
                str(ROOT / runner.ENTRY),
                "--child",
                mode,
                "--output",
                execution_output,
            ],
            child_pid=pid,
            started_perf_counter=origin,
            cap_seconds=900,
            returncode=0,
            interrupted=None,
            seconds=200.0,
            child_sha256=runner.digest(folder / "child.json"),
        )
        runner.atomic(folder / "measurement.json", measurement)
        children.append(child)
        measurements.append(measurement)
    runner.atomic(
        tmp_path / "pair.json",
        dict(
            **runner.pair_identity(children),
            order=["plain", "profiled"],
            measurements=measurements,
            seconds=700.0,
            admission_evidence=False,
        ),
    )
    return tmp_path


def test_saved_pair_is_data_only(
    saved_fixture: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from compact_suit import cli

    from poker_ai.postflop.controlled_scoring import ScoringContext

    def forbidden(*a: Any, **k: Any) -> Any:
        raise AssertionError("numerical execution in saved parser")

    monkeypatch.setattr(cli, "read", forbidden)
    monkeypatch.setattr(cli, "child_main", forbidden)
    monkeypatch.setattr(ScoringContext, "score", forbidden)
    saved = runner.saved_pair(ROOT, saved_fixture)
    assert (
        saved["pair"]["status"] == "exact_complete_scalar_and_computed_replay_identity"
    )
    reads, commands = runner.exports(saved)
    assert len(reads) == 6 and len(commands) == 2
    assert sum(r["selected_calls"] for r in reads) == 7


@pytest.mark.parametrize(
    "damage",
    [
        "bool_cap",
        "bool_seconds",
        "wrong_pid",
        "wrong_command",
        "admission",
        "training",
        "reference",
        "worker_clock",
        "escaping_read",
        "phase_order",
        "extra_raw",
        "missing_event",
        "summary",
        "identity",
        "shared_clock",
        "overlap",
    ],
)
def test_saved_pair_rejects_coherently_rehashed_invalid_evidence(
    saved_fixture: Path, damage: str
) -> None:
    folder = saved_fixture / "profiled"
    child = json.loads((folder / "child.json").read_text())
    measurement = json.loads((folder / "measurement.json").read_text())
    pair = json.loads((saved_fixture / "pair.json").read_text())
    if damage == "bool_cap":
        measurement["cap_seconds"] = True
    elif damage == "bool_seconds":
        measurement["seconds"] = True
    elif damage == "wrong_pid":
        measurement["child_pid"] += 1
    elif damage == "wrong_command":
        measurement["command"][1] = "wrong-entry.py"
    elif damage == "admission":
        child["admission_evidence"] = True
    elif damage == "training":
        child["poker_training_performed"] = True
    elif damage == "reference":
        child["reference_constructed"] = False
    elif damage == "worker_clock":
        child["body_after"]["wall"] = child["body_before"]["wall"] + 0.5
    elif damage in ("escaping_read", "phase_order"):
        observed = json.loads((folder / "observer.json").read_text())
        if damage == "escaping_read":
            observed["reads"][-1]["after"]["cpu"] = 10.0
        else:
            observed["reads"][1]["ledger"]["rows"].reverse()
        runner.atomic(folder / "observer.json", observed)
    elif damage == "extra_raw":
        (folder / "extra.raw").write_bytes(b"extra")
    elif damage == "missing_event":
        (folder / "read-0-events.jsonl").write_bytes(b"")
    elif damage == "summary":
        child["summaries"][0]["read_cpu_seconds"] = 100.0
    elif damage == "identity":
        child["identity"]["computed_replays"][0]["computed"]["unique_profiles"] = 431
    elif damage == "shared_clock":
        pair["seconds"] = 500.0
    else:
        measurement["started_perf_counter"] = 100.1
    # Refresh all hashes that cover the altered bytes. A rejection must come
    # from complete inventory/math/clock consistency, not merely a stale digest.
    child["raw_sha256"] = {
        name: runner.digest(folder / name) for name in child["raw_sha256"]
    }
    runner.atomic(folder / "child.json", child)
    measurement["child_sha256"] = runner.digest(folder / "child.json")
    runner.atomic(folder / "measurement.json", measurement)
    pair["measurements"][1] = measurement
    runner.atomic(saved_fixture / "pair.json", pair)
    with pytest.raises(ArithmeticError):
        runner.saved_pair(ROOT, saved_fixture)


@pytest.mark.parametrize("operation", ["proof", "child", "pair"])
def test_primary_failure_survives_failed_failure_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, operation: str
) -> None:
    primary = LookupError("original preflight failure")
    atomic = runner.atomic

    def binding(*args: Any, **kwargs: Any) -> Any:
        raise primary

    def write(path: Path, data: Any) -> None:
        if data.get("status") == "failed_retained":
            raise OSError("cannot save failure receipt")
        atomic(path, data)

    monkeypatch.setattr(runner, "binding", binding)
    monkeypatch.setattr(runner, "atomic", write)
    with pytest.raises(LookupError) as caught:
        if operation == "proof":
            runner.proof(ROOT, tmp_path, 0.0)
        elif operation == "child":
            runner.child(ROOT, "plain", tmp_path, 0.0)
        else:
            # The protocol requires a fresh ignored destination. Only this unit
            # fixture substitutes its root; no collection command is launched.
            root = tmp_path / "fixture-root"
            (root / "results/runs").mkdir(parents=True)
            runner.pair(root, root / "results/runs/new")
    assert caught.value is primary


def test_cli_report_routes_without_starting_collection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = []
    monkeypatch.setattr(runner, "report", lambda *a: calls.append(a))
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "profile_reader_phases.py",
            "report",
            "--output",
            "results/reader-phase-cpu/pair",
            "--report-output",
            str(tmp_path / "new-report"),
        ],
    )
    assert runner.main() == 0
    assert calls == [
        (ROOT, ROOT / "results/reader-phase-cpu/pair", tmp_path / "new-report")
    ]


def test_report_recreates_numeric_exports_without_mutating_raw(
    saved_fixture: Path,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    pytest.importorskip("matplotlib")
    from compact_suit import admission, cli

    def forbidden(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("saved report started numerical work")

    monkeypatch.setattr(admission, "published", lambda *a: None)
    monkeypatch.setattr(cli, "child_main", forbidden)
    monkeypatch.setattr(cli, "read", forbidden)
    before = {
        str(p.relative_to(saved_fixture)): runner.digest(p)
        for p in saved_fixture.rglob("*")
        if p.is_file()
    }
    destination = tmp_path_factory.mktemp("phase-reports")
    first, second = destination / "first-report", destination / "second-report"
    with pytest.raises(ValueError, match="outside saved raw"):
        runner.report(ROOT, saved_fixture, saved_fixture / "bad-report")
    runner.report(ROOT, saved_fixture, first)
    runner.report(ROOT, saved_fixture, second)
    for name in ("reads.csv", "commands.csv", "summary.json"):
        assert (first / name).read_bytes() == (second / name).read_bytes()
    assert before == {
        str(p.relative_to(saved_fixture)): runner.digest(p)
        for p in saved_fixture.rglob("*")
        if p.is_file()
    }
    with pytest.raises(FileExistsError):
        runner.report(ROOT, saved_fixture, first)
