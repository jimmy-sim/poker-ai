"""Whole-reader observer plumbing, proof fixtures and saved-data-only parsing."""

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
runner = importlib.import_module("profile_checkpoint_cpu")


def test_contract_and_source_inventory_preserve_all433() -> None:
    c, source = runner.binding(ROOT, clean=False)
    assert len(c["input_sha256"]) == 128
    assert len(source["sha256"]) == 436
    historical = json.loads((ROOT / c["base_own"]).read_text())["source"]["sha256"]
    assert {p: source["sha256"][p] for p in historical} == historical
    assert set(source["sha256"]) - set(historical) == {
        runner.CONFIG,
        runner.ENTRY,
        runner.SUPPORT,
    }


@pytest.mark.parametrize("damage", ["config", "input", "symlink"])
def test_frozen_contract_rejects_damage(tmp_path: Path, damage: str) -> None:
    (tmp_path / "configs").mkdir()
    original = ROOT / runner.CONFIG
    (tmp_path / runner.CONFIG).write_bytes(
        original.read_bytes() if damage != "config" else b"{}"
    )
    if damage != "config":
        c = json.loads(original.read_text())
        first = next(iter(c["input_sha256"]))
        path = tmp_path / first
        path.parent.mkdir(parents=True, exist_ok=True)
        if damage == "input":
            path.write_bytes(b"changed")
        else:
            path.symlink_to(ROOT / first)
    with pytest.raises((ArithmeticError, FileNotFoundError)):
        runner.contract(tmp_path)


def test_fresh_own_math_is_reference_free_and_positive(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import subprocess

    command = (
        "import json,pathlib,sys; "
        "from poker_ai.evaluation.compact_opponent_guard import isolated; "
        "import profile_checkpoint_cpu as runner; "
        "folder=pathlib.Path(sys.argv[1]); "
        "scope=isolated(worker=False); scope.__enter__(); "
        "saved=runner.own_math(folder); scope.__exit__(None,None,None); "
        "assert 'pyspiel' not in sys.modules; "
        "(folder/'unit-proof.json').write_text(json.dumps(saved))"
    )
    environment = dict(
        os.environ, PYTHONPATH=str(ROOT / "src") + os.pathsep + str(ROOT / "scripts")
    )
    subprocess.run(
        [sys.executable, "-c", command, str(tmp_path)],
        env=environment,
        check=True,
        capture_output=True,
    )
    saved = json.loads((tmp_path / "unit-proof.json").read_text())
    assert saved["cases"] == 8 and saved["maximum_independent_error"] <= 1e-14
    assert saved["instrumented_results"] == [saved["original_results"]] * 3
    assert saved["observer_state"]["selected_calls"] == 72
    assert saved["observer_state"]["restored"] is True
    assert saved["reference_constructed"] is saved["poker_training_performed"] is False
    assert len(list((tmp_path / "snapshots").glob("*.json.gz"))) == 8


@pytest.fixture
def fake_reader(monkeypatch: pytest.MonkeyPatch) -> Any:
    from compact_suit import cli

    calls = []
    sentinel = dict(scope="fictional-no-native")

    def read(*args: Any, **kwargs: Any) -> Any:
        calls.append((args, kwargs))
        kwargs["observed"].append(dict(fixture=True))
        return sentinel

    monkeypatch.setattr(cli, "read", read)
    return cli, calls, sentinel, read


@pytest.mark.parametrize("enabled", [False, True])
def test_complete_reader_preserves_arguments_result_and_restores(
    tmp_path: Path, fake_reader: Any, enabled: bool
) -> None:
    cli, calls, sentinel, original = fake_reader
    arguments = (object(), object(), object())
    with runner.observe_reader(tmp_path, enabled=enabled) as receipt:
        for _ in range(3):
            assert cli.read(*arguments) is sentinel
    assert cli.read is original
    assert all(call[0] == arguments and len(call[1]["observed"]) == 1 for call in calls)
    assert len(receipt["replays"]) == 3
    saved = json.loads((tmp_path / "observer.json").read_text())
    assert saved["state"]["restored"] is True and saved["state"]["read_count"] == 3
    assert saved["state"]["active"] is False


@pytest.mark.parametrize("damage", ["few_args", "kwargs", "prepopulated", "four_reads"])
def test_complete_reader_rejects_changed_call_shape(
    tmp_path: Path, fake_reader: Any, damage: str
) -> None:
    cli = fake_reader[0]
    with runner.observe_reader(tmp_path, enabled=True), pytest.raises(ArithmeticError):
        if damage == "few_args":
            cli.read(object(), object())
        elif damage in ("kwargs", "prepopulated"):
            cli.read(
                object(),
                object(),
                object(),
                observed=[] if damage == "kwargs" else [{}],
            )
        else:
            for _ in range(4):
                cli.read(object(), object(), object())
    assert cli.read is fake_reader[3]


@pytest.mark.parametrize("witnesses", [0, 2])
def test_one_actual_computed_replay_required(
    tmp_path: Path, fake_reader: Any, monkeypatch: pytest.MonkeyPatch, witnesses: int
) -> None:
    cli = fake_reader[0]

    def read(*args: Any, **kwargs: Any) -> dict[str, Any]:
        kwargs["observed"].extend({} for _ in range(witnesses))
        return dict(scope="fictional")

    monkeypatch.setattr(cli, "read", read)
    with runner.observe_reader(tmp_path, enabled=True), pytest.raises(ArithmeticError):
        cli.read(object(), object(), object())
    assert json.loads((tmp_path / "read-0.json").read_text())["status"] == "partial"


def test_reader_original_exception_survives_final_receipt_failure(
    tmp_path: Path, fake_reader: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    cli = fake_reader[0]
    primary = ValueError("original read")

    def fail(*args: Any, **kwargs: Any) -> Any:
        raise primary

    monkeypatch.setattr(cli, "read", fail)
    original_atomic = runner.atomic

    def atomic(path: Path, data: Any) -> None:
        if path.name == "observer.json":
            raise OSError("receipt write")
        original_atomic(path, data)

    monkeypatch.setattr(runner, "atomic", atomic)
    with pytest.raises(ValueError) as caught:
        with runner.observe_reader(tmp_path, enabled=True):
            cli.read(object(), object(), object())
    assert caught.value is primary and cli.read is fail
    assert (
        json.loads((tmp_path / "read-0.json").read_text())["failure_kind"]
        == "ValueError"
    )


@pytest.mark.parametrize("status", ["failed_retained", "completed_scalar_comparison"])
def test_even_failed_native_is_marked_diagnostic(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, status: str
) -> None:
    from compact_suit import cli

    primary = RuntimeError("original child failed")

    def child(*args: Any, **kwargs: Any) -> Any:
        runner.atomic(
            tmp_path / "native.json",
            dict(status=status, implementation_config=dict(original=True)),
        )
        raise primary

    monkeypatch.setattr(cli, "child_main", child)
    with pytest.raises(RuntimeError) as caught:
        runner.execute_child(
            ROOT, tmp_path, dict(base_own="fixture", scope="fixture"), enabled=True
        )
    assert caught.value is primary
    saved = json.loads((tmp_path / "native.json").read_text())
    assert saved["implementation_config"]["admission_evidence"] is False
    assert saved["base_implementation_config"] == dict(original=True)


@pytest.mark.parametrize("cap", [0, -1, True, float("nan"), float("inf")])
def test_supervisor_rejects_bad_caps(tmp_path: Path, cap: Any) -> None:
    with pytest.raises(ValueError):
        runner.supervise(
            [sys.executable, "-c", "raise AssertionError('must not run')"],
            tmp_path / "child",
            cap,
        )


@pytest.mark.parametrize("code", [0, 7])
def test_supervisor_records_real_pid_and_exact_child_bytes(
    tmp_path: Path, code: int
) -> None:
    folder = tmp_path / "child"
    command = [
        sys.executable,
        "-c",
        (
            "import json,os,pathlib,sys; p=pathlib.Path(sys.argv[1]); "
            "p.write_text(json.dumps(dict(pid=os.getpid()))); "
            "sys.exit(int(sys.argv[2]))"
        ),
        str(folder / "child.json"),
        str(code),
    ]
    result = runner.supervise(command, folder, 10)
    assert result["returncode"] == code and result["interrupted"] is None
    assert result["child_pid"] == json.loads((folder / "child.json").read_text())["pid"]
    assert result["child_sha256"] == runner.digest(folder / "child.json")
    with pytest.raises(FileExistsError):
        runner.supervise(command, folder, 10)


def test_supervisor_timeout_retains_partial_child(tmp_path: Path) -> None:
    folder = tmp_path / "child"
    command = [
        sys.executable,
        "-c",
        (
            "import pathlib,sys,time; "
            "pathlib.Path(sys.argv[1]).write_bytes(b'partial'); time.sleep(5)"
        ),
        str(folder / "raw.partial"),
    ]
    result = runner.supervise(command, folder, 0.2)
    assert result["returncode"] == 124 and result["interrupted"] == "TimeoutExpired"
    assert (folder / "raw.partial").read_bytes() == b"partial"
    assert result["child_sha256"] is None


def historical_identity() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    saved = json.loads(
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
    return saved, replays


def test_complete_historical_identity_and_only_os_normalization_identity_excluded() -> (
    None
):
    saved, replays = historical_identity()
    expected = runner.numerical_identity(saved, replays)
    changed = copy.deepcopy(saved)
    changed["normalization"]["pid"] += 1
    changed["normalization"]["thread"] += 1
    assert runner.numerical_identity(changed, replays) == expected
    changed["normalization"]["reduced_evaluations"] += 1
    assert runner.numerical_identity(changed, replays) != expected


@pytest.mark.parametrize(
    "damage",
    [
        "profile_missing",
        "condition_missing",
        "scope",
        "training",
        "worker",
        "worker_config",
        "computed",
        "read_order",
        "bool_repetition",
    ],
)
def test_numerical_identity_rejects_incomplete_work(damage: str) -> None:
    saved, replays = historical_identity()
    if damage == "profile_missing":
        saved["profiles"].pop()
    elif damage == "condition_missing":
        saved["fixed_conditions"].pop()
    elif damage == "scope":
        saved["scope"] = "new"
    elif damage == "training":
        saved["poker_training_performed"] = True
    elif damage == "worker":
        saved["native_batch"]["workers"].pop()
    elif damage == "worker_config":
        saved["native_batch"]["workers"][0]["messages"][-1]["summary"][
            "implementation_sha256"
        ] = "other"
    elif damage == "computed":
        replays[1]["computed"]["policy_and_ledger_bits_exact"] = False
    elif damage == "read_order":
        replays.reverse()
    else:
        saved["repetition"] = False
    with pytest.raises(ArithmeticError):
        runner.numerical_identity(saved, replays)


def synthetic_reads(
    *, enabled: bool, pid: int, origin: float
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Invented clock records for schema tests, never measurement evidence."""
    import checkpoint_cpu_support as support

    thread = 1234

    def stamp(amount: float) -> dict[str, Any]:
        return dict(wall=origin + amount, cpu=amount, pid=pid, thread=thread)

    reads = []
    for read in range(3):
        rows: list[dict[str, Any]] = []
        events: list[dict[str, Any]] = []
        if enabled:
            for checkpoint in range(432):
                base = read * 0.01 + checkpoint * 0.00001
                group = []
                for offset, category in enumerate(support.CATEGORIES):
                    index = len(rows)
                    start, end = ((1, 6), (2, 3), (4, 5))[offset]
                    row = dict(
                        index=index,
                        read=read,
                        parent=None if offset == 0 else index - offset,
                        category=category,
                        status="complete",
                        before=stamp(base + start * 0.000001),
                        after=stamp(base + end * 0.000001),
                    )
                    rows.append(row)
                    group.append(row)
                starts = []
                for row in group:
                    start_row = copy.deepcopy(row)
                    del start_row["after"]
                    start_row["status"] = "running"
                    starts.append(start_row)
                events.extend(
                    [
                        starts[0],
                        starts[1],
                        copy.deepcopy(group[1]),
                        starts[2],
                        copy.deepcopy(group[2]),
                        copy.deepcopy(group[0]),
                    ]
                )
        reads.append(
            dict(
                index=read,
                status="complete",
                before=stamp(read * 0.01),
                after=stamp(read * 0.01 + 0.009),
                ledger=dict(
                    status="complete", errors=0, rows=rows, pid=pid, thread=thread
                ),
                events=events,
            )
        )
    state = dict(
        enabled=enabled,
        pid=pid,
        thread=thread,
        active=False,
        restored=True,
        aliases_remaining=0,
        original_root_unchanged=True,
        errors=0,
        cleanup_failures=[],
        selected_calls=3888 if enabled else 0,
        maximum=4096,
        read_count=3,
        categories=list(support.CATEGORIES),
    )
    return state, reads


@pytest.fixture
def saved_fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Synthetic clocks plus already-published scalar DATA, with no new solve."""
    import checkpoint_cpu_support as support
    import profile_compact_replay as replay

    monkeypatch.setattr(replay, "authenticate_source", lambda *args: None)
    source = dict(
        sha256={},
        fingerprint="44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a",
    )
    native_base, replays = historical_identity()
    children, measurements = [], []
    for index, mode in enumerate(("plain", "profiled")):
        pid, origin = 100 + index, 100.0 + index
        state, reads = synthetic_reads(enabled=index == 1, pid=pid, origin=origin)
        native = copy.deepcopy(native_base)
        native["normalization"].update(pid=pid, thread=1234)
        native.pop("complete_command")
        identity = runner.numerical_identity(native, replays)
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
                b"".join(runner.canonical(event) + b"\n" for event in row["events"])
            )
        runner.atomic(folder / "native.json", native)
        (folder / "native-events.jsonl").write_bytes(
            (
                ROOT / "results/compact-suit-learning/cost/0/native-events.jsonl"
            ).read_bytes()
        )
        execution_output = str(ROOT / "results/runs/synthetic-schema-fixture" / mode)
        clocks = [
            dict(
                slot=w["slot"], wall_seconds=m["seconds"], cpu_seconds=m["cpu_seconds"]
            )
            for w in native["native_batch"]["workers"]
            for m in w["messages"]
            if m.get("kind") == "done"
        ]
        child = dict(
            status="complete_checkpoint_cpu_diagnostic",
            mode=mode,
            pid=pid,
            thread=1234,
            base_admission_rejected=True,
            config_sha256=runner.CONFIG_SHA,
            source=source,
            identity=identity,
            worker_body_clocks=clocks,
            body_before=dict(wall=origin, cpu=0.0, pid=pid, thread=1234),
            body_after=dict(wall=origin + 0.1, cpu=0.1, pid=pid, thread=1234),
            complete_body_parent_cpu_seconds=0.1,
            executable=sys.executable,
            execution_root=str(ROOT),
            execution_output=execution_output,
            summaries=support.validate_state(
                state, reads, enabled=index == 1, pid=pid, thread=1234, expected=432
            ),
            raw_sha256={
                str(p.relative_to(folder)): runner.digest(p) for p in folder.iterdir()
            },
        )
        runner.atomic(folder / "child.json", child)
        (folder / "command.log").write_bytes(
            b"synthetic schema fixture; no execution\n"
        )
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
            seconds=0.2,
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
            seconds=1.2,
        ),
    )
    return tmp_path


def test_complete_saved_parser_is_data_only(
    saved_fixture: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from compact_suit import cli

    from poker_ai.evaluation import opponent_learning_own as own
    from poker_ai.postflop.controlled_scoring import ScoringContext

    def forbidden(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("saved parser executed numerical work")

    monkeypatch.setattr(cli, "child_main", forbidden)
    monkeypatch.setattr(cli, "read", forbidden)
    monkeypatch.setattr(own, "replay_snapshot", forbidden)
    monkeypatch.setattr(ScoringContext, "score", forbidden)
    result = runner.saved_pair(ROOT, saved_fixture)
    reads, commands = runner.exports(result)
    assert len(reads) == 6 and len(commands) == 2
    assert sum(row["selected_calls"] for row in reads) == 3888
    assert all(row["outside_checkpoint_cpu_seconds"] >= -1e-9 for row in reads)
    assert commands[0]["complete_wall_seconds"] == 0.2


@pytest.mark.parametrize(
    "damage",
    [
        "missing",
        "extra",
        "event",
        "raw",
        "pid",
        "read_body",
        "command",
        "identity",
        "worker_clock",
        "base_admission",
        "read_clock",
        "source",
        "cap",
        "overlap",
    ],
)
def test_saved_pair_damage_fails_closed(saved_fixture: Path, damage: str) -> None:
    pair_path = saved_fixture / "pair.json"
    child_path = saved_fixture / "profiled/child.json"
    pair = json.loads(pair_path.read_text())
    child = json.loads(child_path.read_text())
    if damage == "missing":
        del child["raw_sha256"]["read-0.json"]
    elif damage == "extra":
        (saved_fixture / "profiled/unaccounted.txt").write_text("unexpected")
    elif damage in ("event", "raw"):
        path = (
            saved_fixture
            / "profiled"
            / ("read-0-events.jsonl" if damage == "event" else "native.json")
        )
        path.write_bytes(b"changed")
    elif damage == "pid":
        pair["measurements"][1]["child_pid"] = True
    elif damage == "read_body":
        child["body_before"]["wall"] += 0.05
    elif damage == "command":
        pair["measurements"][1]["command"][-1] = "elsewhere"
    elif damage == "identity":
        child["identity"]["profiles"][0]["native_metrics"][
            "value_player_zero_chips"
        ] += 1
    elif damage == "worker_clock":
        child["worker_body_clocks"][0]["cpu_seconds"] += 1
    elif damage == "base_admission":
        child["base_admission_rejected"] = False
    elif damage == "read_clock":
        child["complete_body_parent_cpu_seconds"] = -1
    elif damage == "source":
        child["source"]["fingerprint"] = "changed"
    elif damage == "cap":
        pair["measurements"][1]["seconds"] = 900
    else:
        pair["measurements"][1]["started_perf_counter"] = 100.1
    runner.atomic(child_path, child)
    pair["measurements"][1]["child_sha256"] = runner.digest(child_path)
    runner.atomic(saved_fixture / "profiled/measurement.json", pair["measurements"][1])
    runner.atomic(pair_path, pair)
    with pytest.raises((ArithmeticError, KeyError)):
        runner.saved_pair(ROOT, saved_fixture)


def test_native_invalidation_write_failures_preserve_primary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from compact_suit import cli

    primary = ValueError("primary child failure")

    def child(*args: Any, **kwargs: Any) -> Any:
        (tmp_path / "native.json").write_text(
            json.dumps(dict(implementation_config={}))
        )
        raise primary

    original_atomic = runner.atomic

    def atomic(path: Path, saved: Any) -> None:
        if path.name in ("native.json", "invalidation-failure.json"):
            raise OSError("disk refused invalidation record")
        original_atomic(path, saved)

    monkeypatch.setattr(cli, "child_main", child)
    monkeypatch.setattr(runner, "atomic", atomic)
    with pytest.raises(ValueError) as caught:
        runner.execute_child(
            ROOT, tmp_path, dict(base_own="fixture", scope="fixture"), enabled=True
        )
    assert caught.value is primary


@pytest.fixture
def own_publication_fixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, dict[str, Any]]:
    import profile_compact_replay as prior
    from compact_suit import admission

    folder = tmp_path / runner.FOLDER / "software"
    folder.mkdir(parents=True)
    proof = runner.own_math(folder)
    source: dict[str, Any] = dict(sha256={})
    saved = dict(
        status="complete_own_only_observer_proof",
        config_sha256=runner.CONFIG_SHA,
        source=source,
        proof=proof,
        pid=proof["observer_state"]["pid"],
        thread=proof["observer_state"]["thread"],
        reference_constructed=False,
        poker_training_performed=False,
        raw_sha256={
            str(p.relative_to(folder)): runner.digest(p)
            for p in (folder / "snapshots").iterdir()
        },
    )
    runner.atomic(folder / "child.json", saved)
    runner.atomic(
        folder / "measurement.json",
        dict(
            returncode=0,
            interrupted=None,
            seconds=1.0,
            child_sha256=runner.digest(folder / "child.json"),
            child_pid=saved["pid"],
        ),
    )
    (folder / "command.log").write_bytes(b"unit fixture only; publication is mocked\n")
    monkeypatch.setattr(admission, "published", lambda *args: None)
    monkeypatch.setattr(prior, "authenticate_source", lambda *args: None)
    return tmp_path, source


def test_own_publication_checks_complete_positive_coverage(
    own_publication_fixture: tuple[Path, dict[str, Any]],
) -> None:
    root, source = own_publication_fixture
    result = runner.own_published(root, source)
    assert result["file"] == runner.FOLDER + "/software/child.json"


@pytest.mark.parametrize(
    "damage",
    [
        "nan",
        "bool_cases",
        "results",
        "inner_reference",
        "snapshots",
        "extra",
        "pid",
        "summary",
    ],
)
def test_own_publication_rejects_bad_proof(
    own_publication_fixture: tuple[Path, dict[str, Any]], damage: str
) -> None:
    root, source = own_publication_fixture
    folder = root / runner.FOLDER / "software"
    saved = json.loads((folder / "child.json").read_text())
    measurement = json.loads((folder / "measurement.json").read_text())
    if damage == "nan":
        # Write intentionally invalid JSON extension directly, bypassing writer.
        saved["proof"]["maximum_independent_error"] = float("nan")
    elif damage == "bool_cases":
        saved["proof"]["cases"] = True
    elif damage == "results":
        saved["proof"]["original_results"] = [None] * 8
        saved["proof"]["instrumented_results"] = [[None] * 8] * 3
    elif damage == "inner_reference":
        saved["proof"]["reference_constructed"] = True
    elif damage == "snapshots":
        saved["raw_sha256"].popitem()
    elif damage == "extra":
        (folder / "unlisted").write_bytes(b"extra")
    elif damage == "pid":
        measurement["child_pid"] += 1
    else:
        saved["proof"]["summaries"][0]["calls"] = 0
    (folder / "child.json").write_text(json.dumps(saved))
    measurement["child_sha256"] = runner.digest(folder / "child.json")
    runner.atomic(folder / "measurement.json", measurement)
    with pytest.raises(ArithmeticError):
        runner.own_published(root, source)
