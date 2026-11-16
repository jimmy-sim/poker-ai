"""Own-family protocol, clocks, failures and complete-run orchestration fixtures."""

import copy
import importlib
import json
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
t = importlib.import_module("profile_matrix_phases")


def test_sealed_contract_and_all53_pins() -> None:
    c = t.contract(ROOT)
    assert len(c["input_sha256"]) == 53
    assert c["maximum_child_seconds"] == 900 and c["maximum_pair_seconds"] == 1800
    assert c["maximum_software_proof_seconds"] == 180
    assert c["order"] == ["original_profiled"]
    assert c["maximum_selected_calls_pair"] == 4096


@pytest.mark.parametrize("change", ["config", "input", "symlink"])
def test_contract_rejects_changed_inputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: str
) -> None:
    c = t.contract(ROOT)
    cfg = tmp_path / t.CONFIG
    cfg.parent.mkdir(parents=True)
    cfg.write_bytes((ROOT / t.CONFIG).read_bytes())
    if change == "config":
        cfg.write_text("{}")
    else:
        original_digest = t.digest
        first = next(iter(c["input_sha256"]))
        monkeypatch.setattr(
            t,
            "digest",
            lambda p: (
                original_digest(cfg)
                if p == cfg
                else (
                    "changed"
                    if change == "input"
                    else c["input_sha256"].get(str(p.relative_to(tmp_path)), "missing")
                )
            ),
        )
        if change == "symlink":
            path = tmp_path / first
            path.parent.mkdir(parents=True, exist_ok=True)
            path.symlink_to(ROOT / first)
    with pytest.raises((ArithmeticError, FileNotFoundError)):
        t.contract(tmp_path)


@pytest.mark.parametrize("value", [None, "nan", "inf", "-1", "0", "1e100"])
def test_bad_or_missing_registered_origin_rejected(
    monkeypatch: pytest.MonkeyPatch, value: str | None
) -> None:
    if value is None:
        monkeypatch.delenv("POKER_MATRIX_PHASES_COMMAND_STARTED", raising=False)
    else:
        monkeypatch.setenv("POKER_MATRIX_PHASES_COMMAND_STARTED", value)
    with pytest.raises(ArithmeticError):
        t.registered_origin()


def test_registered_origin_includes_earlier_start(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    value = time.perf_counter() - 0.01
    monkeypatch.setenv("POKER_MATRIX_PHASES_COMMAND_STARTED", str(value))
    assert t.registered_origin() == value


@pytest.mark.parametrize("kind", ["outside", "existing", "symlink"])
def test_no_output_overwrite_or_escape(tmp_path: Path, kind: str) -> None:
    path = tmp_path / "results/runs/new"
    if kind == "outside":
        path = tmp_path.parent / "outside"
    elif kind == "existing":
        path.mkdir(parents=True)
        (path / "keep").write_text("retain")
    else:
        path.parent.mkdir(parents=True)
        path.symlink_to(tmp_path.parent)
    with pytest.raises(ValueError):
        t.fresh(tmp_path, path)
    if kind == "existing":
        assert (path / "keep").read_text() == "retain"


def fake_parent(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    c: dict[str, Any] = t.contract(ROOT)
    monkeypatch.setenv("POKER_MATRIX_PHASES_COMMAND_STARTED", str(time.perf_counter()))
    monkeypatch.setattr(
        t,
        "binding",
        lambda *args, **kwargs: (
            copy.deepcopy(c),
            dict(sha256={}, fingerprint="fictional"),
        ),
    )
    monkeypatch.setattr(t, "checked", lambda *args: None)
    monkeypatch.setattr(t, "published_proof", lambda *args: "fictional-proof")
    monkeypatch.setattr(t.original, "control", lambda *args: None)
    return c


@pytest.mark.parametrize("proof", [False, True])
def test_precondition_failure_retained_without_supervision(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, proof: bool
) -> None:
    fake_parent(monkeypatch)
    monkeypatch.setattr(
        t,
        "checked",
        lambda *args: (_ for _ in ()).throw(ArithmeticError("missing source checks")),
    )
    monkeypatch.setattr(
        t,
        "supervise",
        lambda *args: pytest.fail(
            "constructor/reference launched before source checks"
        ),
    )
    output = tmp_path / "results/runs/failed"
    assert (t.proof_run if proof else t.pair_run)(tmp_path, output) == 1
    row = json.loads((output / ("proof.json" if proof else "pair.json")).read_text())
    assert (
        row["status"] == "failed_retained" and row["failure_kind"] == "ArithmeticError"
    )


@pytest.mark.parametrize("proof", [False, True])
def test_failed_supervised_child_retained_no_retry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, proof: bool
) -> None:
    fake_parent(monkeypatch)
    calls = []

    def failed(command: Any, output: Path, cap: float) -> dict[str, Any]:
        calls.append((command, cap))
        output.mkdir()
        (output / "command.log").write_text("fictional partial child\n")
        return dict(returncode=1, seconds=0.1)

    monkeypatch.setattr(t, "supervise", failed)
    output = tmp_path / "results/runs/failed"
    assert (t.proof_run if proof else t.pair_run)(tmp_path, output) == 1
    row = json.loads((output / ("proof.json" if proof else "pair.json")).read_text())
    assert row["status"] == "failed_retained" and len(calls) == 1
    assert 0 < calls[0][1] <= (180 if proof else 900)


def test_both_arms_use_remaining_shared_cap_and_no_retry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    c = fake_parent(monkeypatch)
    calls: list[tuple[Any, float]] = []

    def finish(command: Any, output: Path, cap: float) -> dict[str, Any]:
        calls.append((command, cap))
        output.mkdir()
        (output / "command.log").write_text("fictional success\n")
        return dict(returncode=0, seconds=0.1)

    monkeypatch.setattr(t, "supervise", finish)
    monkeypatch.setattr(t, "verify_pair", lambda *args: {})
    output = tmp_path / "results/runs/pair"
    assert t.pair_run(tmp_path, output) == 0
    assert [cmd[cmd.index("--child") + 1] for cmd, _ in calls] == c["order"]
    assert all(0 < cap <= 900 for _, cap in calls)
    assert json.loads((output / "pair.json").read_text())["admission_evidence"] is False


@pytest.mark.parametrize("mode", ["original_profiled"])
def test_child_precondition_failure_retains_no_reference(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str
) -> None:
    monkeypatch.setattr(
        t,
        "binding",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            ArithmeticError("source missing")
        ),
    )
    monkeypatch.setattr(
        t.original, "child", lambda *args: pytest.fail("original/reference constructed")
    )
    output = tmp_path / mode
    output.mkdir()
    assert t.child(tmp_path, mode, output, time.perf_counter()) == 1
    row = json.loads((output / "child.json").read_text())
    assert (
        row["status"] == "failed_retained" and row["poker_training_performed"] is False
    )


def test_software_child_failure_has_no_fabricated_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        t,
        "binding",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            ArithmeticError("source missing")
        ),
    )
    assert t.software_child(tmp_path, tmp_path, time.perf_counter()) == 1
    row = json.loads((tmp_path / "child.json").read_text())
    assert row["status"] == "failed_retained" and row["reference_constructed"] is False
    assert "constructor_fingerprints" not in row


@pytest.mark.parametrize("operation", ["--prove", "--show", "--show-proof", "--child"])
def test_cli_mutually_exclusive_operations(
    monkeypatch: pytest.MonkeyPatch, operation: str
) -> None:
    args = ["compare", operation, "--proof-child"]
    if operation == "--child":
        args.insert(2, "original_profiled")
    monkeypatch.setattr(sys, "argv", args)
    with pytest.raises(SystemExit) as error:
        t.main()
    assert error.value.code == 2


@pytest.mark.parametrize("mode", ["original_profiled"])
@pytest.mark.parametrize(
    "failure", [None, "proof", "original", "inventory", "changed_source"]
)
def test_child_same_recorders_and_partial_failure_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str, failure: str | None
) -> None:
    c = fake_parent(monkeypatch)
    source = dict(sha256={"fixture": "same"}, fingerprint="fictional", dirty=False)
    steps: list[str] = []
    bindings = []

    def bound(*args: Any, **kwargs: Any) -> tuple[dict[str, Any], dict[str, Any]]:
        bindings.append(True)
        s = copy.deepcopy(source)
        if failure == "changed_source" and len(bindings) > 1:
            s["sha256"] = {"fixture": "changed"}
        return c, s

    def proof(*args: Any) -> str:
        steps.append("proof")
        if failure == "proof":
            raise ArithmeticError("unpublished proof")
        return "pinned"

    @contextmanager
    def recorder(arm: str, folder: Path, maximum: int) -> Any:
        assert arm == "phased" and maximum == 512
        steps.append("constructor_" + arm)
        yield {}
        steps.append("constructor_restored")

    @contextmanager
    def reader(*args: Any) -> Any:
        steps.append("six_regions")
        yield
        steps.append("regions_restored")

    def original(*args: Any) -> int:
        steps.append("original")
        (args[2] / "child.json").write_text("fictional original bytes")
        return 1 if failure == "original" else 0

    monkeypatch.setattr(t, "binding", bound)
    monkeypatch.setattr(t, "published_proof", proof)
    monkeypatch.setattr(t, "runtime", lambda *args: {})
    monkeypatch.setattr(t, "digest", lambda *args: "pinned")
    monkeypatch.setattr(t.prior, "targets", lambda: steps.append("preload"))
    monkeypatch.setattr(t.depth, "constructor_scope", recorder)
    monkeypatch.setattr(t.prior, "reader_observer", reader)
    monkeypatch.setattr(t.original, "child", original)
    monkeypatch.setattr(
        t.prior, "original_result", lambda *args: dict(identity={"fixture": True})
    )
    monkeypatch.setattr(t, "phase_ledgers", lambda *args, **kwargs: [])
    monkeypatch.setattr(
        t.previous,
        "read_constructors",
        lambda *args: ["fingerprint"] * (183 if failure == "inventory" else 184),
    )

    def constructors(*args: Any) -> list[Any]:
        if failure == "inventory":
            raise ArithmeticError("missing constructor")
        return []

    monkeypatch.setattr(t, "constructor_phases", constructors)
    output = tmp_path / mode
    output.mkdir()
    result = t.child(tmp_path, mode, output, time.perf_counter())
    row = json.loads((output / "child.json").read_text())
    assert result == (0 if failure is None else 1)
    assert row["poker_training_performed"] is False
    if failure == "proof":
        assert steps == ["proof"]
    else:
        assert steps == [
            "proof",
            "preload",
            "constructor_phased",
            "six_regions",
            "original",
            "regions_restored",
            "constructor_restored",
        ]
        assert (output / "old/child.json").read_text() == "fictional original bytes"
    if failure is None:
        assert row["status"] == "complete" and row["constructor_calls"] == 184
        assert row["raw_sha256"]["old/child.json"] == "pinned"
    else:
        assert row["status"] == "failed_retained"


def test_broken_internal_symlink_not_a_fresh_destination(tmp_path: Path) -> None:
    link = tmp_path / "results/runs/link"
    link.parent.mkdir(parents=True)
    link.symlink_to(link.parent / "not_created")
    with pytest.raises(ValueError):
        t.fresh(tmp_path, link)
    assert not (link.parent / "not_created").exists()


def test_show_proof_uses_software_default_without_launch(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    paths: list[Path] = []
    monkeypatch.setattr(sys, "argv", ["compare", "--show-proof"])

    def saved(root: Path, output: Path) -> dict[str, bool]:
        paths.append(output)
        return {"fixture": True}

    monkeypatch.setattr(t, "verify_software", saved)
    monkeypatch.setattr(t, "proof_run", lambda *args: pytest.fail("new proof launched"))
    assert t.main() == 0
    assert paths == [ROOT / "results/runs/matrix-phases/software"]
    assert json.loads(capsys.readouterr().out) == {"fixture": True}


def software_fixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, Path]:
    """Fictional qualification; real small constructor, no solver or trajectory."""
    import shutil

    root = tmp_path / "fixture"
    output = root / "results/runs/proof"
    child = output / "child"
    child.mkdir(parents=True)
    c: dict[str, Any] = t.contract(ROOT)
    for key in ("proof_spot", "proof_model"):
        destination = root / c[key]
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / c[key], destination)
    source = dict(sha256={"fictional": "fixture"}, dirty=False)
    monkeypatch.setattr(
        t, "binding", lambda *args, **kwargs: (copy.deepcopy(c), copy.deepcopy(source))
    )
    monkeypatch.setattr(t, "checked", lambda *args: None)
    monkeypatch.setattr(
        t,
        "runtime",
        lambda config: dict(
            requirements=dict(
                distributions=c["required_distributions"],
                metadata_probe=c["metadata_probe"],
            ),
            environment=c["runtime"],
            idle_control=dict(
                c["idle_control"],
                requested=True,
                assertion_state_independently_audited=False,
            ),
        ),
    )
    digest = t.digest
    monkeypatch.setattr(
        t,
        "digest",
        lambda path: (
            "fictional-qualified" if Path(path).name == "checks.json" else digest(path)
        ),
    )
    origin = time.perf_counter()
    assert t.software_child(root, child, origin) == 0
    row = json.loads((child / "child.json").read_text())
    command = [
        c["idle_control"]["path"],
        *c["idle_control"]["arguments"],
        row["executable"],
        str(root / t.ENTRY),
        "--proof-child",
        "--output",
        str(child),
    ]
    (child / "command.log").write_text(
        "fictional supervisor; no process or reference launched\n"
    )
    measurement = dict(
        command=command,
        returncode=0,
        interrupted=None,
        seconds=time.perf_counter() - origin,
        child_sha256=digest(child / "child.json"),
    )
    (child / "measurement.json").write_text(json.dumps(measurement))
    (output / "proof.json").write_text(
        json.dumps(
            dict(
                status="complete",
                admission_evidence=False,
                seconds=time.perf_counter() - origin,
                measurement=measurement,
                command_log_sha256=digest(child / "command.log"),
            )
        )
    )
    return root, output


def test_complete_software_shape_replays_without_builder(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, output = software_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(
        t.depth, "build", lambda *args: pytest.fail("parser constructed game")
    )
    proof = t.verify_software(root, output)
    assert len(proof["expected_negative"]) == 2
    assert len(proof["constructors"]["original"]) == 5
    assert proof["constructors"]["original"] == proof["constructors"]["phased"]
    assert proof["child"]["reference_constructed"] is False


@pytest.mark.parametrize(
    "change", ["cap", "returncode", "command", "raw", "cases", "vector", "reference"]
)
def test_software_proof_rejects_tampering(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: str
) -> None:
    root, output = software_fixture(tmp_path, monkeypatch)
    if change == "raw":
        (output / "child/expected-negative.json").write_text("missing rows\n")
    elif change in ("vector", "reference", "cases"):
        path = output / "child/child.json"
        row = json.loads(path.read_text())
        if change == "vector":
            row["constructor_fingerprints"]["phased"][0] = "changed"
        elif change == "reference":
            row["reference_constructed"] = True
        else:
            row["expected_negative_fixtures"] = {}
        path.write_text(json.dumps(row))
    else:
        path = output / "proof.json"
        row = json.loads(path.read_text())
        if change == "cap":
            row["seconds"] = 180
        elif change == "returncode":
            row["measurement"]["returncode"] = 1
        else:
            row["measurement"]["command"][0] = "unknown"
        path.write_text(json.dumps(row))
    with pytest.raises((ArithmeticError, ValueError)):
        t.verify_software(root, output)


def pair_fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    """Fully fictional supervisor/audit; exercise pair identities and cost report."""
    import hashlib
    import os
    import threading

    root = tmp_path / "fixture"
    output = root / "results/runs/pair"
    c: dict[str, Any] = t.contract(ROOT)
    source = dict(sha256={"fictional": "fixture"}, dirty=False)
    monkeypatch.setattr(
        t, "binding", lambda *args, **kwargs: (copy.deepcopy(c), copy.deepcopy(source))
    )
    monkeypatch.setattr(t, "checked", lambda *args: None)
    monkeypatch.setattr(t, "published_proof", lambda *args: "fictional-proof")
    digest = t.digest
    monkeypatch.setattr(
        t,
        "digest",
        lambda path: (
            (
                "fictional-qualified"
                if Path(path).name == "checks.json"
                else "fictional-proof"
            )
            if not Path(path).exists()
            else digest(path)
        ),
    )
    monkeypatch.setattr(
        t, "raw_files", lambda *args: {"child.json", "measurement.json", "command.log"}
    )
    vectors = ["fictional-fingerprint"] * 184
    monkeypatch.setattr(t.previous, "read_constructors", lambda *args: list(vectors))
    pid = os.getpid()
    thread = threading.get_ident()
    identity = dict(fictional=True)
    constructor_sha = hashlib.sha256(t.canonical(vectors)).hexdigest()
    identity_sha = hashlib.sha256(t.canonical(identity)).hexdigest()
    metadata = dict(
        requirements=dict(
            distributions=c["required_distributions"],
            metadata_probe=c["metadata_probe"],
        ),
        environment=c["runtime"],
        idle_control=dict(
            c["idle_control"],
            requested=True,
            assertion_state_independently_audited=False,
        ),
    )
    measurements = []
    logs = {}
    observation = dict(interval=dict(clocks=dict(process_cpu_seconds=20.0)))
    for i, mode in enumerate(c["order"]):
        folder = output / mode
        folder.mkdir(parents=True)
        row = dict(
            status="complete",
            mode=mode,
            pid=pid + i,
            thread=thread,
            source=source,
            config_sha256=t.CONFIG_SHA,
            qualification_sha256="fictional-qualified",
            proof_sha256="fictional-proof",
            admission_evidence=False,
            poker_training_performed=False,
            reference_output_used_in_training=False,
            reference_constructed=True,
            runtime=metadata,
            original_identity_sha256=identity_sha,
            constructor_calls=184,
            constructors_sha256=constructor_sha,
            executable=sys.executable,
            execution_root=str(root),
            execution_output=str(folder),
        )
        (folder / "child.json").write_text(json.dumps(row))
        (folder / "command.log").write_text("fictional supervisor\n")
        command = [
            c["idle_control"]["path"],
            *c["idle_control"]["arguments"],
            sys.executable,
            str(root / t.ENTRY),
            "--child",
            mode,
            "--output",
            str(folder),
        ]
        m = dict(
            command=command,
            returncode=0,
            interrupted=None,
            seconds=1.0 - i * 0.1,
            child_sha256=digest(folder / "child.json"),
        )
        (folder / "measurement.json").write_text(json.dumps(m))
        measurements.append(m)
        logs[mode] = digest(folder / "command.log")
        (folder / "old").mkdir()
        (folder / "old/parent-resource-reads.json").write_text(
            json.dumps(
                dict(
                    reads=[
                        dict(scope="FICTIONAL", observation=observation)
                        for _ in range(3)
                    ]
                )
            )
        )
        (folder / "inner-reads.json").write_text(
            json.dumps(dict(reads=[dict(observation=observation) for _ in range(3)]))
        )
    extra = {mode + "/old/parent-resource-reads.json" for mode in c["order"]} | {
        mode + "/inner-reads.json" for mode in c["order"]
    }
    monkeypatch.setattr(
        t,
        "raw_files",
        lambda folder, row: {
            "child.json",
            "measurement.json",
            "command.log",
            "old/parent-resource-reads.json",
            "inner-reads.json",
        },
    )
    assert len(extra) == 2

    def original(root: Path, folder: Path, config: Any) -> dict[str, Any]:
        return dict(
            identity=identity,
            card_cache={"fictional": True},
            child_before=dict(pid=pid + c["order"].index(folder.name)),
        )

    def phases(
        folder: Path, row: Any, old: Any, config: Any, **kwargs: Any
    ) -> list[dict[str, Any]]:
        amount = 5.0 if folder.name == "original" else 3.0
        return [
            dict(
                summary=dict(
                    calls=432 if i == 0 else 553,
                    groups={"matrix_build": dict(exclusive_selected_cpu=amount)},
                    selected_union_cpu=amount,
                )
            )
            for i in range(3)
        ]

    monkeypatch.setattr(t.prior, "original_result", original)
    monkeypatch.setattr(t, "phase_ledgers", phases)
    (output / "pair.json").write_text(
        json.dumps(
            dict(
                status="complete",
                admission_evidence=False,
                seconds=2.0,
                measurements=measurements,
                command_log_sha256=logs,
            )
        )
    )
    monkeypatch.setattr(
        t,
        "constructor_phases",
        lambda *args: [
            dict(
                phases={name: dict(cpu=1.0, wall=1.0) for name in t.depth.PHASES},
                remainder=dict(cpu=0.0, wall=0.0),
            )
            for _ in range(184)
        ],
    )
    monkeypatch.setattr(t, "contract", lambda *args: copy.deepcopy(c))
    return root, output


def test_pair_and_cost_report_are_saved_data(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, output = pair_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(
        t, "supervise", lambda *args: pytest.fail("data reader launched process")
    )
    result = t.report(root, output)
    assert result["diagnostic_cost_pass_claim_permitted"] is False
    assert len(result["constructor_phases"]) == 184
    assert result["combined_selected_calls"] == 2458
    assert result["poker_training_performed"] is result["long_run_admitted"] is False


@pytest.mark.parametrize("change", ["vector", "extra", "cap", "admission"])
def test_pair_rejects_changed_identity_or_scope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: str
) -> None:
    root, output = pair_fixture(tmp_path, monkeypatch)
    if change == "vector":
        monkeypatch.setattr(
            t.previous,
            "read_constructors",
            lambda folder, *args: [folder.parent.name] * 183,
        )
    elif change == "extra":
        (output / "unknown.json").write_text("{}")
    elif change == "cap":
        p = output / "pair.json"
        row = json.loads(p.read_text())
        row["seconds"] = 1800
        p.write_text(json.dumps(row))
    else:
        p = output / "original_profiled/child.json"
        row = json.loads(p.read_text())
        row["admission_evidence"] = True
        p.write_text(json.dumps(row))
    with pytest.raises(ArithmeticError):
        t.verify_pair(root, output)


@pytest.mark.parametrize(
    "change",
    [
        "unexpected_success",
        "missing_phase",
        "wrong_error",
        "bool_context",
        "clock",
        "extra_schema",
    ],
)
def test_expected_negative_is_not_a_generic_ignored_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: str
) -> None:
    import hashlib

    root, output = software_fixture(tmp_path, monkeypatch)
    child = json.loads((output / "child/child.json").read_text())
    folder = output / "child/phased-negative"
    state_path = folder / "phases.json"
    state = json.loads(state_path.read_text())
    events_path = folder / "phase-events.jsonl"
    events = [json.loads(x) for x in events_path.read_text().splitlines()]
    if change == "unexpected_success":
        state["status"] = "complete"
    elif change == "missing_phase":
        events.pop(2)
    elif change == "wrong_error":
        events[-2]["failure_kind"] = "RuntimeError"
    elif change == "bool_context":
        events[0]["index"] = False
    elif change == "clock":
        events[-2]["clocks"]["cpu"] = 0.0
    else:
        events[-1]["not_declared"] = True
    raw = ("\n".join(json.dumps(x) for x in events) + "\n").encode()
    events_path.write_bytes(raw)
    state["events_sha256"] = hashlib.sha256(raw).hexdigest()
    state_path.write_text(json.dumps(state))
    with pytest.raises(ArithmeticError):
        t.verify_negative(
            output / "child", t.contract(ROOT), child["pid"], child["thread"]
        )


@pytest.mark.parametrize("proof", [False, True])
@pytest.mark.parametrize("host_uptime", [0.125, 500000.0])
def test_expired_preflight_does_not_launch_or_extend_cap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, proof: bool, host_uptime: float
) -> None:
    monkeypatch.setattr(t.time, "perf_counter", lambda: host_uptime)
    fake_parent(monkeypatch)
    # A freshly booted CI VM can have a monotonic clock below 2000 seconds.
    # Model a valid positive origin and an expired budget independently of uptime.
    monkeypatch.setattr(t.time, "perf_counter", lambda: 5000.0)
    monkeypatch.setenv("POKER_MATRIX_PHASES_COMMAND_STARTED", "3000.0")
    monkeypatch.setattr(
        t, "supervise", lambda *args: pytest.fail("expired budget launched child")
    )
    output = tmp_path / "results/runs/expired"
    assert (t.proof_run if proof else t.pair_run)(tmp_path, output) == 1
    record = json.loads((output / ("proof.json" if proof else "pair.json")).read_text())
    assert (
        record["status"] == "failed_retained"
        and record["failure_kind"] == "TimeoutError"
    )
