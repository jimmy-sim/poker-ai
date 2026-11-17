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
runner = importlib.import_module("compare_context_reuse")


def test_frozen_contract_preserves_all447_scientific_files() -> None:
    c, source = runner.binding(ROOT, clean=False)
    _, old = runner.predecessor.binding(ROOT, clean=False)
    assert len(c["input_sha256"]) == 128
    assert len(source["sha256"]) == 450
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
    assert saved["state"]["restored"] is True and saved["state"]["root_active"] is False


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
    assert json.loads((tmp_path / "read-0.json").read_text())["status"] == "failed"


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
    assert json.loads((tmp_path / "read-0.json").read_text())["status"] == "failed"


@pytest.fixture(scope="module")
def actual_software_proof(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Actual archived software read; not a source-qualified formal measurement."""
    folder = tmp_path_factory.mktemp("phase-proof-unit")
    code = """import json,pathlib,sys
from poker_ai.evaluation.compact_opponent_guard import isolated
import compare_context_reuse as runner
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


@pytest.mark.parametrize("failure", ["source", "checks", "runtime", "math"])
def test_proof_prerequisite_failure_is_retained(tmp_path: Path, failure: str) -> None:
    code = """import pathlib,sys
from unittest.mock import patch
import compare_context_reuse as runner
root=pathlib.Path(sys.argv[1]);output=pathlib.Path(sys.argv[2]);failure=sys.argv[3]
primary=LookupError(failure)
def fail(*args,**kwargs):raise primary
with (
 patch.object(runner,'binding',
  fail if failure=='source' else lambda *a,**k:({},dict(sha256={}))),
 patch.object(runner,'checked',fail if failure=='checks' else lambda *a:None),
 patch.object(runner.previous,'runtime',
  fail if failure=='runtime' else lambda *a:None),
 patch.object(runner,'own_math',fail),
):
 try:runner.proof(root,output,0.0)
 except LookupError as caught:assert caught is primary
 else:raise AssertionError('prerequisite failure was swallowed')
assert 'pyspiel' not in sys.modules
"""
    subprocess.run(
        [sys.executable, "-c", code, str(ROOT), str(tmp_path), failure],
        cwd=ROOT,
        env=dict(
            os.environ,
            PYTHONPATH=str(ROOT / "src") + os.pathsep + str(ROOT / "scripts"),
        ),
        check=True,
        capture_output=True,
    )
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
    origin = proof["observed"]["reads"][0]["before"]["wall"] - 1.0
    seconds = proof["fixture_state"]["rows"][-1]["after"]["wall"] - origin + 1.0
    execution_output = str(ROOT / "results/runs/phase-publication-fixture")
    child = dict(
        status="complete_own_only_context_reuse_proof",
        config_sha256=runner.CONFIG_SHA,
        source=source,
        proof_sha256=runner.digest(folder / "proof.json"),
        reference_constructed=False,
        poker_training_performed=False,
        admission_evidence=False,
        pid=proof["observed"]["reads"][0]["before"]["pid"],
        thread=proof["observed"]["reads"][0]["before"]["thread"],
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
            cap_seconds=180,
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
    config = runner.contract(ROOT)
    monkeypatch.setattr(runner, "contract", lambda *a: config)
    return tmp_path, source


def test_complete_positive_own_publication(
    own_publication_fixture: tuple[Path, dict[str, Any]],
) -> None:
    root, source = own_publication_fixture
    assert (
        runner.own_published(root, source)["file"]
        == runner.FOLDER + "/software/child.json"
    )


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
            runner.child(ROOT, "ordinary", tmp_path, 0.0)
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
            "compare_context_reuse.py",
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


@pytest.mark.parametrize("failure", [None, "ordinary", "reuse", "supervisor"])
def test_pair_keeps_complete_or_partial_outcome_without_retry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str | None
) -> None:
    root = tmp_path / "repository"
    output = root / "results/runs/fixed-pair-fixture"
    c = dict(
        order=["ordinary", "reuse"], caps=dict(shared_seconds=1800, child_seconds=900)
    )
    monkeypatch.setattr(runner, "binding", lambda *a, **k: (c, {}))
    monkeypatch.setattr(runner, "checked", lambda *a: None)
    monkeypatch.setattr(runner, "own_published", lambda *a: {})
    attempts = []
    primary = LookupError("supervisor fixture failure")

    def supervise(command: Any, folder: Path, cap: float) -> dict[str, Any]:
        mode = command[3]
        attempts.append(mode)
        assert cap == 900 and command[1] == str(root / runner.ENTRY)
        folder.mkdir()
        if failure == "supervisor":
            raise primary
        runner.atomic(
            folder / "child.json",
            dict(
                mode=mode,
                status="complete_context_reuse_diagnostic",
                base_admission_rejected=True,
                admission_evidence=False,
                config_sha256=runner.CONFIG_SHA,
                pid=100 + len(attempts),
                source=dict(sha256={}),
                context_identity_sha256="a" * 64,
                identity=json.loads(
                    (
                        ROOT / "results/source-phase-cpu-v2/pair/plain/child.json"
                    ).read_text()
                )["identity"],
            ),
        )
        return dict(returncode=124 if failure == mode else 0, seconds=1.0)

    monkeypatch.setattr(runner.previous, "supervise", supervise)
    if failure is None:
        assert runner.pair(root, output) == 0
    else:
        with pytest.raises(
            LookupError if failure == "supervisor" else ArithmeticError
        ) as raised:
            runner.pair(root, output)
        if failure == "supervisor":
            assert raised.value is primary
    saved = json.loads((output / "pair.json").read_text())
    assert attempts == (
        ["ordinary"] if failure in ("ordinary", "supervisor") else ["ordinary", "reuse"]
    )
    assert saved["status"] == (
        "failed_retained"
        if failure
        else "exact_complete_scalar_and_computed_replay_identity"
    )
    assert saved["admission_evidence"] is False
    assert len(saved["measurements"]) == (
        0 if failure == "supervisor" else len(attempts)
    )


def test_exhausted_shared_clock_is_retained_before_child(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from types import SimpleNamespace

    root = tmp_path / "repository"
    output = root / "results/runs/shared-cap-fixture"
    ticks = iter([0.0, 1801.0, 1802.0])
    monkeypatch.setattr(
        runner, "time", SimpleNamespace(perf_counter=lambda: next(ticks))
    )
    monkeypatch.setattr(
        runner,
        "binding",
        lambda *a, **k: (
            dict(order=["ordinary", "reuse"], caps=dict(shared_seconds=1800)),
            {},
        ),
    )
    monkeypatch.setattr(runner, "checked", lambda *a: None)
    monkeypatch.setattr(runner, "own_published", lambda *a: {})
    with pytest.raises(TimeoutError):
        runner.pair(root, output)
    saved = json.loads((output / "pair.json").read_text())
    assert saved["status"] == "failed_retained" and saved["measurements"] == []


@pytest.mark.parametrize("write_failure", [False, True])
def test_failed_child_output_cannot_keep_base_admission(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, write_failure: bool
) -> None:
    from compact_suit import cli

    c = dict(base_own="fictional-fixture", scope="fixture-not-poker")
    raw = tmp_path / "native.json"

    def child(*args: Any, **kwargs: Any) -> int:
        runner.atomic(raw, dict(implementation_config=dict(fixture=True)))
        return 7

    monkeypatch.setattr(cli, "child_main", child)
    atomic = runner.atomic
    if write_failure:

        def fail_rewrite(path: Path, value: Any) -> None:
            if path == raw and "instrumentation_scope" in value:
                raise OSError("fixture cannot rewrite diagnostic header")
            atomic(path, value)

        monkeypatch.setattr(runner, "atomic", fail_rewrite)
    with pytest.raises(
        ArithmeticError, match="complete original cost-audit child failed"
    ):
        runner.execute_child(ROOT, tmp_path, c, enabled=True)
    if write_failure:
        assert json.loads((tmp_path / "invalidation-failure.json").read_text()) == dict(
            failure_kind="OSError"
        )
    else:
        saved = json.loads(raw.read_text())
        assert saved["implementation_config"]["admission_evidence"] is False
        assert saved["base_implementation_config"] == dict(fixture=True)
        assert saved["instrumentation_scope"] == "fixture-not-poker"
    assert (
        json.loads((tmp_path / "observer.json").read_text())["state"]["restored"]
        is True
    )


@pytest.mark.parametrize("cap", [180, 180.0, 179.9989877909975, 179.5, 100.0])
def test_startup_adjusted_inner_allowance_accepted(
    own_publication_fixture: tuple[Path, dict[str, Any]], cap: float
) -> None:
    root, source = own_publication_fixture
    path = root / runner.FOLDER / "software/measurement.json"
    measurement = json.loads(path.read_text())
    assert measurement["seconds"] < cap
    measurement["cap_seconds"] = cap
    runner.atomic(path, measurement)
    assert runner.own_published(root, source)["file"].endswith("software/child.json")


@pytest.mark.parametrize(
    "cap", [False, True, 0, -1, float("nan"), float("inf"), 180.001]
)
def test_invalid_remaining_allowances_rejected(
    own_publication_fixture: tuple[Path, dict[str, Any]], cap: float
) -> None:
    root, source = own_publication_fixture
    path = root / runner.FOLDER / "software/measurement.json"
    measurement = json.loads(path.read_text())
    measurement["cap_seconds"] = cap
    # NaN/inf are deliberately corrupt JSON, not valid producer output.
    path.write_text(json.dumps(measurement))
    with pytest.raises(ArithmeticError):
        runner.own_published(root, source)


def test_complete_child_must_fit_remaining_allowance(
    own_publication_fixture: tuple[Path, dict[str, Any]],
) -> None:
    root, source = own_publication_fixture
    path = root / runner.FOLDER / "software/measurement.json"
    measurement = json.loads(path.read_text())
    for cap in (measurement["seconds"], measurement["seconds"] / 2):
        measurement["cap_seconds"] = cap
        runner.atomic(path, measurement)
        with pytest.raises(ArithmeticError):
            runner.own_published(root, source)


def test_cli_remaining_allowance_round_trips_publication(
    own_publication_fixture: tuple[Path, dict[str, Any]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from types import SimpleNamespace

    root, source = own_publication_fixture
    ticks = iter((100.0, 100.0010122090025))
    monkeypatch.setattr(
        runner, "time", SimpleNamespace(perf_counter=lambda: next(ticks))
    )
    monkeypatch.setattr(
        sys, "argv", ["unit", "proof", "--output", "results/runs/unit-budget"]
    )
    captured = []

    def supervise(command: Any, output: Path, cap: float) -> dict[str, Any]:
        captured.append(cap)
        return dict(returncode=0)

    monkeypatch.setattr(runner.previous, "supervise", supervise)
    assert runner.main() == 0 and len(captured) == 1
    assert 179 < captured[0] < 180
    path = root / runner.FOLDER / "software/measurement.json"
    measurement = json.loads(path.read_text())
    measurement["cap_seconds"] = captured[0]
    runner.atomic(path, measurement)
    assert runner.own_published(root, source)["file"].endswith("software/child.json")


def test_startup_exhaustion_starts_no_proof_child(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from types import SimpleNamespace

    ticks = iter((100.0, 281.0))
    monkeypatch.setattr(
        runner, "time", SimpleNamespace(perf_counter=lambda: next(ticks))
    )
    monkeypatch.setattr(
        sys, "argv", ["unit", "proof", "--output", "results/runs/exhausted"]
    )

    def forbidden(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("exhausted proof started a child")

    monkeypatch.setattr(runner.previous, "supervise", forbidden)
    with pytest.raises(TimeoutError, match="startup exhausted"):
        runner.main()


def test_actual_proof_explicit_scope_and_independent_math(
    actual_software_proof: Path,
) -> None:
    saved = json.loads((actual_software_proof / "unit-proof.json").read_text())
    assert saved["plain_computed_replays"] == [
        x["computed"] for x in saved["observed"]["replays"]
    ]
    assert saved["observed"]["state"]["facts"]["roots"] == 0
    assert saved["fixture_state"]["facts"]["misses"] == 2
    assert saved["fixture_state"]["facts"]["hits"] == 4
    assert saved["nested_source"]["caller_mutation_isolated"] is True
    assert saved["tiny_math"]["maximum_error_chips"] <= 1e-12
    assert saved["tiny_math"]["independent_terminal_and_pure_response"] is True
    assert saved["real_cost_loader_coverage"] is False


@pytest.mark.parametrize(
    "damage",
    [
        "extra",
        "reference",
        "training",
        "cost_claim",
        "clones",
        "template",
        "nested",
        "math",
        "scalar",
        "events",
        "fixture_event",
        "command",
        "pid",
        "bool_cap",
        "excess_cap",
        "nan_cap",
        "zero_cap",
        "bool_seconds",
        "escape_clock",
    ],
)
def test_own_publication_rejects_coherently_rehashed_invalid_evidence(
    own_publication_fixture: tuple[Path, dict[str, Any]], damage: str
) -> None:
    root, source = own_publication_fixture
    folder = root / runner.FOLDER / "software"
    proof = json.loads((folder / "proof.json").read_text())
    child = json.loads((folder / "child.json").read_text())
    measurement = json.loads((folder / "measurement.json").read_text())
    if damage == "extra":
        (folder / "extra.raw").write_bytes(b"unexpected")
    elif damage == "reference":
        proof["reference_constructed"] = True
    elif damage == "training":
        proof["new_holdem_training_performed"] = True
    elif damage == "cost_claim":
        proof["real_cost_loader_coverage"] = True
    elif damage == "clones":
        proof["fixture_state"]["facts"]["return_clones"] -= 1
    elif damage == "template":
        proof["fixture_state"]["final_entries"] = 1
    elif damage == "nested":
        proof["nested_source"]["caller_mutation_isolated"] = False
    elif damage == "math":
        proof["tiny_math"]["helper"][0] += 0.1
    elif damage == "scalar":
        proof["plain_computed_replays"][0]["unique_profiles"] = 431
    elif damage == "events":
        (folder / "read-0-events.jsonl").write_bytes(b"{}\n")
    elif damage == "fixture_event":
        (folder / "fixture-events.jsonl").write_bytes(b"")
    elif damage == "command":
        measurement["command"][1] = "wrong.py"
    elif damage == "pid":
        measurement["child_pid"] += 1
    elif damage == "bool_cap":
        measurement["cap_seconds"] = True
    elif damage == "excess_cap":
        measurement["cap_seconds"] = 181
    elif damage == "nan_cap":
        measurement["cap_seconds"] = float("nan")
    elif damage == "zero_cap":
        measurement["cap_seconds"] = 0
    elif damage == "bool_seconds":
        measurement["seconds"] = True
    else:
        measurement["started_perf_counter"] += 1000
        child["started_perf_counter"] = measurement["started_perf_counter"]
    runner.atomic(folder / "proof.json", proof)
    child["proof_sha256"] = runner.digest(folder / "proof.json")
    runner.atomic(folder / "child.json", child)
    measurement["child_sha256"] = runner.digest(folder / "child.json")
    (folder / "measurement.json").write_text(json.dumps(measurement))
    with pytest.raises(ArithmeticError):
        runner.own_published(root, source)


def synthetic_reads(
    enabled: bool, pid: int, origin: float
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Invented schema clocks/counts, not measurement or a real context factory."""
    import context_reuse_support as support

    c = runner.contract(ROOT)

    def stamp(t: float) -> dict[str, Any]:
        return dict(wall=origin + t, cpu=t, pid=pid, thread=1234)

    state: dict[str, Any] = dict(
        enabled=enabled,
        facts=support.expected_facts(enabled),
        rows=[],
        events=[],
        final_entries=0,
        root_active=False,
        inflight=False,
        emitting=False,
        cleanup_failures=[],
        restored=True,
    )
    reads = []
    for index in range(3):
        indices = []
        events = []
        if index:
            root = index - 1
            base = 4 * root
            t = index * 0.1 + 0.001
            for offset, kind in enumerate(
                (
                    "archive_root",
                    "sampled_dictionary",
                    "full_dictionary",
                    "prior_iterator",
                )
            ):
                before = t if offset == 0 else t + 0.003 * offset
                after = t + 0.014 if offset == 0 else before + 0.001
                row = dict(
                    index=base + offset,
                    root=root,
                    kind=kind,
                    status="complete",
                    before=stamp(before),
                    after=stamp(after),
                )
                if offset == 0:
                    row.update(
                        software=False,
                        root_path=str(ROOT),
                        keys=c["expected_context_keys"],
                    )
                else:
                    row["collection_sha256"] = "a" * 64
                state["rows"].append(row)
                indices.append(base + offset)
            order = [(base, "start")]
            for child in range(base + 1, base + 4):
                order.extend(((child, "start"), (child, "end")))
            order.append((base, "end"))
            for ordinal, phase in order:
                row = state["rows"][ordinal]
                event = dict(
                    index=ordinal,
                    phase=phase,
                    clock=stamp(
                        row["before" if phase == "start" else "after"]["cpu"] + 0.0001
                    ),
                )
                if phase == "end":
                    event.update(
                        status="complete",
                        facts=support.progress_facts(
                            enabled, root + 1, ordinal % 4 or 3
                        ),
                    )
                events.append(event)
            state["events"].extend(events)
        reads.append(
            dict(
                index=index,
                status="complete",
                before=stamp(index * 0.1),
                after=stamp(index * 0.1 + 0.09),
                row_indices=indices,
                events=events,
            )
        )
    return state, reads


@pytest.fixture
def saved_fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Synthetic clocks and published scalar DATA, no solve or admission."""

    import profile_compact_replay as replay

    monkeypatch.setattr(replay, "authenticate_source", lambda *a: None)
    source = dict(
        sha256={},
        fingerprint="44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a",
    )
    base = json.loads(
        (ROOT / "results/source-phase-cpu-v2/pair/plain/native.json").read_text()
    )
    base["implementation_config"] = base.pop("base_implementation_config")
    replays = json.loads(
        (ROOT / "results/source-phase-cpu-v2/pair/plain/observer.json").read_text()
    )["replays"]
    children, measurements = [], []
    for index, mode in enumerate(("ordinary", "reuse")):
        pid, origin = 100 + index, 100.0 + 500 * index
        state, reads = synthetic_reads(index == 1, pid, origin)
        native = copy.deepcopy(base)
        native["normalization"].update(pid=pid, thread=1234)
        native.pop("complete_command", None)
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
                ROOT / "results/source-phase-cpu-v2/pair/plain/native-events.jsonl"
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
            status="complete_context_reuse_diagnostic",
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
            summaries=runner.validate_observed(
                dict(state=state, reads=reads, replays=replays),
                enabled=index == 1,
                pid=pid,
                thread=1234,
                config=runner.contract(ROOT),
            ),
            read_clocks=reads,
            context_identity_sha256=state["rows"][1]["collection_sha256"],
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
            order=["ordinary", "reuse"],
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
    assert len(saved["ledgers"][0]) == len(saved["ledgers"][1]) == 8


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
    folder = saved_fixture / "reuse"
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
            observed["state"]["rows"].reverse()
        runner.atomic(folder / "observer.json", observed)
    elif damage == "extra_raw":
        (folder / "extra.raw").write_bytes(b"extra")
    elif damage == "missing_event":
        (folder / "read-1-events.jsonl").write_bytes(b"")
    elif damage == "summary":
        child["summaries"][0]["cpu_seconds"] = 100.0
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


def test_previous_calculated_identity_drift_rejected(saved_fixture: Path) -> None:
    children = [
        json.loads((saved_fixture / mode / "child.json").read_text())
        for mode in ("ordinary", "reuse")
    ]
    for child in children:
        child["identity"]["computed_replays"][0]["computed"]["maximum_error"] += 1e-15
    with pytest.raises(ArithmeticError, match="previous complete numerical identity"):
        runner.pair_identity(children)


def test_published_rejected_pair_preserves_failure_and_all_other_result_fields() -> (
    None
):
    """Real retained DATA regression; never relax the original pair gate."""
    folder = ROOT / runner.FOLDER / "pair"
    if not folder.exists():
        pytest.skip("published rejected comparison not present at this checkpoint")
    manifest = json.loads(folder.with_name("pair-raw-manifest.json").read_text())
    assert manifest["status"] == "failed_retained" and len(manifest["files"]) == 27
    for row in manifest["files"]:
        path = ROOT / row["file"]
        assert path.stat().st_size == row["bytes"]
        assert runner.digest(path) == row["sha256"]
    pair = json.loads((folder / "pair.json").read_text())
    assert pair["status"] == "failed_retained"
    children = [
        json.loads((folder / mode / "child.json").read_text())
        for mode in ("ordinary", "reuse")
    ]
    assert all(c["status"] == "complete_context_reuse_diagnostic" for c in children)
    assert (
        children[0]["context_identity_sha256"] == children[1]["context_identity_sha256"]
    )
    with pytest.raises(ArithmeticError):
        runner.pair_identity(children)
    with pytest.raises(ArithmeticError):
        runner.saved_pair(ROOT, folder)
    projected = [copy.deepcopy(c["identity"]) for c in children]
    for category, key in (
        ("normalization", "requests"),
        ("normalization", "reduced_evaluations"),
        ("validation_cache", "requests"),
        ("validation_cache", "hits"),
    ):
        a, b = projected[0][category].pop(key), projected[1][category].pop(key)
        assert type(a) is int and type(b) is int and 0 <= b < a
    assert runner.canonical(projected[0]) == runner.canonical(projected[1])
    summary = json.loads(
        (ROOT / runner.FOLDER / "rejected-report/summary.json").read_text()
    )
    assert summary["original_gate_rejected"] is True and summary["valid_pair"] is False
    assert summary["forbidden_attempts"] == [] and summary["raw_unchanged"] is True
