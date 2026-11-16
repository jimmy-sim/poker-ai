"""Own-family protocol, clocks, failures and complete-run orchestration fixtures."""

import copy
import importlib
import json
import sys
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
t = importlib.import_module("check_suit_lookup")


def test_sealed_contract_and_all60_pins() -> None:
    c = t.contract(ROOT)
    assert len(c["input_sha256"]) == 60
    assert c["maximum_child_seconds"] == 900 and c["maximum_pair_seconds"] == 1800
    assert c["maximum_software_proof_seconds"] == 180
    assert c["order"] == ["original", "lookup"]
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
        monkeypatch.delenv("POKER_SUIT_LOOKUP_COMMAND_STARTED", raising=False)
    else:
        monkeypatch.setenv("POKER_SUIT_LOOKUP_COMMAND_STARTED", value)
    with pytest.raises(ArithmeticError):
        t.registered_origin()


def test_registered_origin_includes_earlier_start(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    value = time.perf_counter() - 0.01
    monkeypatch.setenv("POKER_SUIT_LOOKUP_COMMAND_STARTED", str(value))
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
    monkeypatch.setenv("POKER_SUIT_LOOKUP_COMMAND_STARTED", str(time.perf_counter()))
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


@pytest.mark.parametrize("mode", ["original", "lookup"])
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
        args.insert(2, "original")
    monkeypatch.setattr(sys, "argv", args)
    with pytest.raises(SystemExit) as error:
        t.main()
    assert error.value.code == 2


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
    assert paths == [ROOT / "results/runs/suit-lookup/software"]
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
        t.fields, "build", lambda *args: pytest.fail("parser constructed game")
    )
    monkeypatch.setattr(
        t.kernel,
        "translated_cards",
        lambda *args: pytest.fail("data parser computed canonical cards"),
    )
    monkeypatch.setattr(
        t.kernel,
        "BASE",
        lambda *args, **kwargs: pytest.fail(
            "data parser called original canonical cards"
        ),
    )
    proof = t.verify_software(root, output)
    assert proof["valid_cases"] == 4398 and proof["table_entries"] == 1248
    assert len(proof["constructors"]["original"]) == 5
    assert proof["constructors"]["original"] == proof["constructors"]["lookup"]
    assert proof["child"]["reference_constructed"] is False


@pytest.mark.parametrize(
    "change", ["cap", "returncode", "command", "raw", "cases", "vector", "reference"]
)
def test_software_proof_rejects_tampering(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: str
) -> None:
    root, output = software_fixture(tmp_path, monkeypatch)
    if change == "raw":
        (output / "child/original-cards.jsonl").write_text("missing rows\n")
    elif change in ("vector", "reference", "cases"):
        path = output / "child/child.json"
        row = json.loads(path.read_text())
        if change == "vector":
            row["constructor_fingerprints"]["lookup"][0] = "changed"
        elif change == "reference":
            row["reference_constructed"] = True
        else:
            row["valid_completed"]["original"] = 4397
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
    monkeypatch.setattr(t.fields, "read_constructors", lambda *args: list(vectors))
    monkeypatch.setattr(t, "pinned_constructors", lambda *args: None)
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
        kernel_row = dict(
            status="complete",
            mode=mode,
            maximum=c["maximum_kernel_requests"],
            pid=pid + i,
            thread=thread,
            requests=100,
            original_evaluations=100 if mode == "original" else 0,
            lookup_evaluations=100 if mode == "lookup" else 0,
            fallbacks=0,
            errors=0,
            restored=True,
            aliases_remaining=0,
            table_sha256=c["lookup_table_sha256"],
            scope=t.kernel.SCOPE,
        )
        (folder / "kernel.json").write_text(json.dumps(kernel_row))
        row = dict(
            kernel_requests=100,
            kernel_sha256=digest(folder / "kernel.json"),
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
            "kernel.json",
        },
    )
    assert len(extra) == 4

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
    return root, output


def test_pair_and_cost_report_are_saved_data(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, output = pair_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(
        t, "supervise", lambda *args: pytest.fail("data reader launched process")
    )
    result = t.report(root, output)
    assert result["diagnostic_cost_passed"] is True
    assert result["constructor_calls"] == dict(original=184, lookup=184)
    assert len(result["rows"]) == 6
    assert result["poker_training_performed"] is result["long_run_admitted"] is False


def test_slower_lookup_command_retains_failed_diagnostic(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, output = pair_fixture(tmp_path, monkeypatch)
    p = output / "pair.json"
    pair = json.loads(p.read_text())
    pair["measurements"][1]["seconds"] = 1.1
    (output / "lookup/measurement.json").write_text(json.dumps(pair["measurements"][1]))
    p.write_text(json.dumps(pair))
    result = t.report(root, output)
    assert result["diagnostic_cost_passed"] is False
    assert result["diagnostic_cost_checks"]["lower_complete_command_wall"] is False
    assert (
        result["diagnostic_cost_checks"]["lower_selected_exclusive_matrix_cpu"] is True
    )


@pytest.mark.parametrize("change", ["vector", "extra", "cap", "admission"])
def test_pair_rejects_changed_identity_or_scope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: str
) -> None:
    root, output = pair_fixture(tmp_path, monkeypatch)
    if change == "vector":
        monkeypatch.setattr(
            t.fields,
            "read_constructors",
            lambda folder, *args: [folder.parent.name] * 184,
        )
    elif change == "extra":
        (output / "unknown.json").write_text("{}")
    elif change == "cap":
        p = output / "pair.json"
        row = json.loads(p.read_text())
        row["seconds"] = 1800
        p.write_text(json.dumps(row))
    else:
        p = output / "lookup/child.json"
        row = json.loads(p.read_text())
        row["admission_evidence"] = True
        p.write_text(json.dumps(row))
    with pytest.raises(ArithmeticError):
        t.verify_pair(root, output)


@pytest.mark.parametrize("proof", [False, True])
@pytest.mark.parametrize("host_uptime", [0.125, 500000.0])
def test_expired_preflight_independent_of_host_uptime(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, proof: bool, host_uptime: float
) -> None:
    monkeypatch.setattr(t.time, "perf_counter", lambda: host_uptime)
    fake_parent(monkeypatch)
    monkeypatch.setattr(t, "registered_origin", lambda: 3000.0)
    monkeypatch.setattr(t.time, "perf_counter", lambda: 5000.0)
    monkeypatch.setattr(t, "supervise", lambda *args: pytest.fail("expired launch"))
    output = tmp_path / "results/runs/expired"
    assert (t.proof_run if proof else t.pair_run)(tmp_path, output) == 1
    row = json.loads((output / ("proof.json" if proof else "pair.json")).read_text())
    assert row["status"] == "failed_retained" and row["failure_kind"] == "TimeoutError"


@pytest.mark.parametrize("mode", ["original", "lookup"])
def test_interrupted_original_child_unwinds_all_scopes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str
) -> None:
    fake_parent(monkeypatch)
    monkeypatch.setattr(t, "runtime", lambda *args: {})
    original_digest = t.digest
    monkeypatch.setattr(
        t,
        "digest",
        lambda path: (
            "fixture-qualified"
            if Path(path).name == "checks.json"
            else original_digest(path)
        ),
    )
    monkeypatch.setattr(t.prior, "targets", lambda: None)
    events: list[str] = []

    @contextmanager
    def scope(*args: Any) -> Iterator[None]:
        events.append("enter")
        try:
            yield
        finally:
            events.append("exit")

    monkeypatch.setattr(t.fields, "constructor_scope", scope)
    monkeypatch.setattr(t.prior, "reader_observer", scope)

    def interrupted(*args: Any) -> int:
        assert events == ["enter", "enter"]
        assert t.kernel.potential.canonical_cards is not t.kernel.BASE
        assert t.kernel.potential.canonical_cards((0, 1), ()) == t.kernel.BASE(
            (0, 1), ()
        )
        raise KeyboardInterrupt("fixture interruption")

    monkeypatch.setattr(t.original, "child", interrupted)
    output = tmp_path / mode
    output.mkdir()
    assert t.child(tmp_path, mode, output, time.perf_counter()) == 130
    assert events == ["enter", "enter", "exit", "exit"]
    assert t.kernel.potential.canonical_cards is t.kernel.BASE
    row = json.loads((output / "kernel.json").read_text())
    assert row["status"] == "failed_retained" and row["restored"] is True
    assert row["requests"] == 1
    child = json.loads((output / "child.json").read_text())
    assert (
        child["failure_kind"] == "KeyboardInterrupt"
        and child["status"] == "failed_retained"
    )


@pytest.mark.parametrize(
    "change",
    [
        "index_bool",
        "card_bool",
        "duplicate",
        "unsorted",
        "ranks",
        "board",
        "error",
        "mutation",
    ],
)
def test_card_record_rejects_typed_or_geometric_corruption(change: str) -> None:
    row: dict[str, Any] = dict(
        index=0,
        value=[[0, 5], [10, 15, 16]],
        types="tuple(tuple(int),tuple(int))",
        error=None,
        inputs_unchanged=True,
    )
    case = dict(hole=[0, 5], board=[10, 15, 16])
    t.validate_card_record(row, 0, case)
    if change == "index_bool":
        row["index"] = False
    elif change == "card_bool":
        row["value"][0][0] = False
    elif change == "duplicate":
        row["value"][1][0] = 0
    elif change == "unsorted":
        row["value"][0].reverse()
    elif change == "ranks":
        row["value"][0][1] = 9
    elif change == "board":
        row["value"][1].clear()
    elif change == "error":
        row["error"] = dict(kind="ValueError", message="failure")
    else:
        row["inputs_unchanged"] = False
    with pytest.raises(ArithmeticError):
        t.validate_card_record(row, 0, case)


@pytest.mark.parametrize(
    "change", ["requests", "fallbacks", "coverage", "scope", "counter_bool"]
)
def test_pair_rejects_rebound_kernel_corruption(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: str
) -> None:
    root, output = pair_fixture(tmp_path, monkeypatch)
    folder = output / "lookup"
    path = folder / "kernel.json"
    row = json.loads(path.read_text())
    if change == "requests":
        row["requests"] = row["lookup_evaluations"] = 99
    elif change == "fallbacks":
        row.update(fallbacks=1, original_evaluations=1, lookup_evaluations=99)
    elif change == "coverage":
        row.update(original_evaluations=100, lookup_evaluations=0)
    elif change == "scope":
        row["scope"] = "different observer"
    else:
        row["fallbacks"] = False
    path.write_text(json.dumps(row))
    child_path = folder / "child.json"
    child = json.loads(child_path.read_text())
    child.update(kernel_sha256=t.digest(path), kernel_requests=row["requests"])
    child_path.write_text(json.dumps(child))
    pair_path = output / "pair.json"
    pair = json.loads(pair_path.read_text())
    pair["measurements"][1]["child_sha256"] = t.digest(child_path)
    (folder / "measurement.json").write_text(json.dumps(pair["measurements"][1]))
    pair_path.write_text(json.dumps(pair))
    with pytest.raises(ArithmeticError):
        t.verify_pair(root, output)
