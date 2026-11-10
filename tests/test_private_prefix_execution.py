"""Controller/forecast failure fixtures; no real trajectory or reference run."""

import json
import subprocess
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import pytest

from poker_ai.evaluation import private_prefix_cli as cli
from poker_ai.evaluation import private_prefix_gates as gates
from poker_ai.evaluation.private_prefix_capture import collect
from poker_ai.evaluation.private_prefix_design import Design
from poker_ai.evaluation.private_prefix_forecast import forecast
from poker_ai.evaluation.private_prefix_journal import Batch, Events, Journal, validate
from poker_ai.evaluation.private_prefix_sources import contract
from poker_ai.evaluation.private_prefix_worker_checks import complete, partial_cells
from poker_ai.postflop.cell_process import Send, partition, run_batch
from poker_ai.postflop.river_study import Deadline, digest

ROOT = Path(__file__).resolve().parents[1]


def timing_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    config, _ = contract(ROOT)
    paths = Design.build(config, mode="real").paths
    rows = []
    for rep in range(3):
        for i, path in enumerate(paths):
            rows.append(
                dict(
                    repeat=rep,
                    index=i,
                    global_index=48 * rep + i,
                    path=path,
                    source_sha256="FIXTURE",
                    backend="StratifiedBatchTrainer",
                    reference_constructed=False,
                    initialization_visits=100,
                    incremental_visits=100020,
                    total_work=100120,
                    previous_work=100080,
                    iteration=101,
                    last_iteration_visits=40,
                    sampled_traversals=200 * path["batch_size"],
                    guard_sha256=f"guard{i}",
                    setup_seconds=0.01 * (i + 1),
                    incremental_seconds=0.001 * (rep + 1),
                    seconds=0.01 * (i + 1) + 0.001 * (rep + 1) + 0.02,
                )
            )
    return rows, config


def test_fixed_forecast_matches_independent_three_worker_arithmetic() -> None:
    rows, config = timing_rows()
    result = forecast(rows, config, "FIXTURE")
    costs = [0.01 * (i + 1) + 0.003 * 9999900 / 100020 for i in range(48)]
    totals = [sum(costs[i] for i in range(slot, 48, 3)) for slot in range(3)]
    assert result["per_path_max_seconds"] == pytest.approx(costs)
    assert result["training_forecast_seconds"] == pytest.approx(max(totals))
    assert result["guarded_seconds"] == pytest.approx(4 * max(totals) + 1200)
    assert result["passes"] and result["long_run_admitted"] is False
    for row in rows:
        row["incremental_seconds"] *= 10000
        row["seconds"] = row["setup_seconds"] + row["incremental_seconds"]
    failed = forecast(rows, config, "FIXTURE")
    assert not failed["passes"] and not failed["long_run_admitted"]


@pytest.mark.parametrize(
    "mutation",
    [
        "missing",
        "duplicate",
        "seed",
        "bool",
        "counter",
        "nan",
        "guard",
        "source",
        "backend",
    ],
)
def test_forecast_rejects_incomplete_changed_or_nonfinite_grid(mutation: str) -> None:
    rows, config = timing_rows()
    if mutation == "missing":
        rows.pop()
    elif mutation == "duplicate":
        rows[-1] = rows[0]
    elif mutation == "seed":
        rows[0]["path"] = dict(rows[0]["path"], seed=4)
    elif mutation == "bool":
        rows[0]["repeat"] = False
    elif mutation == "counter":
        rows[0]["previous_work"] = 100100
    elif mutation == "nan":
        rows[0]["setup_seconds"] = float("nan")
    elif mutation == "guard":
        rows[0]["guard_sha256"] = "different"
    elif mutation == "source":
        rows[0]["source_sha256"] = "wrong"
    else:
        rows[0]["backend"] = "wrong"
    with pytest.raises(ArithmeticError):
        forecast(rows, config, "FIXTURE")


def spawned_fixture(
    slot: int, indices: list[int], payload: dict[str, Any], send: Send
) -> dict[str, Any]:
    for i in indices:
        send(dict(kind="cell", index=i, phase="fixture", value=i * i))
        if payload.get("fail") and slot == 0:
            raise ValueError("intentional retained child failure")
    return dict(paths=len(indices))


@pytest.mark.parametrize("fail", [False, True])
def test_real_spawn_adapter_fsyncs_identical_complete_or_partial_events(
    tmp_path: Path, fail: bool, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Console pytest does not put the repository root on sys.path under
    # importlib mode. Spawn must be able to import this explicit fixture job.
    monkeypatch.syspath_prepend(str(ROOT))
    journal = Journal(tmp_path / "events.jsonl", "FIXTURE", "spawn_fixture")
    batch = Batch(journal)
    if fail:
        with pytest.raises(ChildProcessError, match="intentional retained"):
            run_batch(6, 3, spawned_fixture, dict(fail=True), Deadline(20), batch)
        assert batch["status"] == "incomplete"
        assert any(
            e["kind"] == "error" for w in batch["workers"] for e in w["messages"]
        )
        with pytest.raises(ArithmeticError):
            complete(batch, 6)
    else:
        run_batch(6, 3, spawned_fixture, {}, Deadline(20), batch)
        cells = complete(batch, 6)
        assert sorted(e["index"] for e in cells) == list(range(6))
        wrong = json.loads(json.dumps(batch))
        wrong["workers"][0]["messages"][1]["index"] = 1
        with pytest.raises(ArithmeticError, match="outside"):
            complete(wrong, 6)
    receipt = journal.close()
    assert partial_cells(batch)
    validate(
        journal.path,
        receipt,
        "FIXTURE",
        {w["slot"]: w["messages"] for w in batch["workers"]},
    )
    assert all(w["exitcode"] is not None for w in batch["workers"])


def test_journal_durable_before_close_and_tamper_rejected(tmp_path: Path) -> None:
    journal = Journal(tmp_path / "events.jsonl", "FIXTURE", "partial")
    events = Events(journal, 0)
    events.append(dict(kind="cell", index=0, phase="training_started"))
    assert len(journal.path.read_text().splitlines()) == 2
    receipt = journal.close()
    validate(journal.path, receipt, "FIXTURE", {0: events})
    with pytest.raises(ArithmeticError):
        validate(journal.path, receipt, "WRONG", {0: events})
    lines = journal.path.read_text().splitlines()
    event = json.loads(lines[-1])
    event["sequence"] = 4
    journal.path.write_text(lines[0] + "\n" + json.dumps(event) + "\n")
    receipt["sha256"] = digest(journal.path)
    with pytest.raises(ArithmeticError, match="sequence"):
        validate(journal.path, receipt, "FIXTURE", {0: events})
    with pytest.raises(FileExistsError):
        Journal(journal.path, "FIXTURE", "partial")


def test_worker_to_parent_scoring_boundary_keeps_both_raw_streams(
    tmp_path: Path,
) -> None:
    journal = Journal(tmp_path / "events.jsonl", "FIXTURE", "new_training")
    worker_event = dict(kind="cell", phase="capture", index=0, row={"id": "capture"})
    journal.append(0, worker_event)
    combined = Events(journal, 3, [worker_event])
    score = dict(kind="cell", phase="profile", index=0, row={"id": "scored"})
    combined.append(score)
    # Even without a final own JSON, the later scoring record is already on disk.
    lines = journal.path.read_text().splitlines()
    assert len(lines) == 3 and json.loads(lines[-1])["event"] == score
    receipt = journal.close()
    assert combined == [worker_event, score]
    assert receipt["events"] == 2
    validate(journal.path, receipt, "FIXTURE", {0: [worker_event], 3: [score]})


def test_old_calibration_failure_keeps_copy_events_before_final_receipt(
    tmp_path: Path,
) -> None:
    from poker_ai.evaluation import private_prefix_run as runner
    from poker_ai.evaluation.private_prefix_sources import source

    current = dict(source(ROOT), dirty=False)
    output = tmp_path / "own.json"

    def interrupted_copy(
        root: Path, path: Path, saved: dict[str, Any], *args: Any
    ) -> None:
        saved["events"].append(
            dict(
                kind="cell",
                phase="capture",
                index=0,
                row=dict(
                    id="PARTIAL",
                    path_index=0,
                    work_label=100000,
                    readout="current",
                    file="missing",
                ),
            )
        )
        # The journal must be durable before exception handling writes the JSON.
        assert "PARTIAL" in (tmp_path / "own-events.jsonl").read_text()
        raise ValueError("intentional old copy interruption")

    with (
        patch("poker_ai.evaluation.private_prefix_admission.require_software"),
        patch.object(runner, "source", return_value=current),
        # This synthetic failure test does not need historical Git objects.
        # The separate slow source/archive test verifies real kernel evidence.
        patch.object(runner, "kernel_evidence", return_value={}),
        patch("poker_ai.evaluation.private_prefix_baselines.rows", return_value=[]),
        patch(
            "poker_ai.evaluation.private_prefix_baselines.source_hashes",
            return_value={},
        ),
        patch(
            "poker_ai.evaluation.private_prefix_old.copy", side_effect=interrupted_copy
        ),
    ):
        from types import SimpleNamespace

        sources = SimpleNamespace(parent=SimpleNamespace(fixed=[]))
        with pytest.raises(ValueError, match="intentional old copy"):
            runner.old(ROOT, output, sources=sources)
    saved = json.loads(output.read_text())
    assert saved["status"] == "failed_own_private_prefix_not_admitted"
    assert saved["journal"]["events"] == 1
    assert saved["captures"][0]["id"] == "PARTIAL"
    assert saved["retention_errors"] and saved["training_performed"] is False
    validate(
        tmp_path / saved["journal_file"],
        saved["journal"],
        saved["source_sha256"],
        {0: saved["events"]},
    )


def test_profile_preflight_checks_nested_report_before_launch(tmp_path: Path) -> None:
    output = tmp_path / "profile.json"
    report = tmp_path / "overhead/report"
    report.mkdir(parents=True)
    with patch("poker_ai.evaluation.private_prefix_cli.subprocess.Popen") as launched:
        with pytest.raises(FileExistsError):
            cli.execute(tmp_path, ["profile", "--output", str(output)])
        launched.assert_not_called()
    receipt = json.loads(next((tmp_path / "rejections").iterdir()).read_text())
    assert receipt["long_run_admitted"] is False
    assert report.exists() and not output.exists()


def test_native_preflight_allows_existing_own_report_but_not_journal(
    tmp_path: Path,
) -> None:
    (tmp_path / "report").mkdir()
    path = tmp_path / "native.json"
    cli.preflight(path, "fixture-native")
    (tmp_path / "native-events.jsonl").write_text("retained")
    with pytest.raises(FileExistsError):
        cli.preflight(path, "fixture-native")


def test_whole_timeout_terminates_child_process_group_and_retains_rejection(
    tmp_path: Path,
) -> None:
    process = Mock(pid=12345)
    process.wait.side_effect = [subprocess.TimeoutExpired("fixture", 1), 0]
    with (
        patch(
            "poker_ai.evaluation.private_prefix_cli.subprocess.Popen",
            return_value=process,
        ),
        patch("poker_ai.evaluation.private_prefix_cli.os.killpg") as killed,
    ):
        with pytest.raises(subprocess.TimeoutExpired):
            cli.execute(
                tmp_path, ["profile", "--output", str(tmp_path / "profile.json")]
            )
        killed.assert_called_once()
        assert killed.call_args.args[0] == 12345
    retained = json.loads(next((tmp_path / "rejections").iterdir()).read_text())
    assert retained["failure"]["type"] == "TimeoutExpired"
    assert retained["long_run_admitted"] is False


def test_old_scope_rejected_before_learner_construction(tmp_path: Path) -> None:
    config, _ = contract(ROOT)
    design = Design.build(config, mode="old")
    with patch(
        "poker_ai.evaluation.private_prefix_capture.StratifiedBatchTrainer"
    ) as learner:
        with pytest.raises(ValueError, match="never train"):
            collect(None, design, 0, tmp_path, "FIXTURE", lambda _: None, Deadline(1))  # type: ignore[arg-type]
        learner.assert_not_called()


def test_gates_require_all_real_logs_and_observed_exact_source(tmp_path: Path) -> None:
    log = tmp_path / "log.txt"
    log.write_text("SYNTHETIC TEST FIXTURE\n")
    source = dict(dirty=False, sha256={"fixture": "0" * 64})
    from poker_ai.postflop.learning_artifacts import sha

    binding = sha(source["sha256"])
    ci = dict(source_sha256=binding, jobs=gates.JOBS, run_id=1, checked_commit="0" * 40)
    local: dict[str, Any] = dict(
        source_sha256=binding,
        results={
            k: dict(
                status="passed", tests_passed=1, log="log.txt", log_sha256=digest(log)
            )
            for k in gates.LOCAL
        },
    )
    with (
        patch.object(gates, "contract"),
        patch.object(gates, "source", return_value=source),
        patch.object(gates, "checked_tree", return_value=source),
    ):
        saved = gates.record(tmp_path, ci, local)
        assert saved["long_run_admitted"] is False
        for bad in (
            dict(ci, jobs={"Python 3.11": "success"}),
            dict(ci, source_sha256="wrong"),
        ):
            with pytest.raises(ArithmeticError):
                gates.record(tmp_path, bad, local)
        local["results"].pop("focused_slow312")
        with pytest.raises(ArithmeticError):
            gates.record(tmp_path, ci, local)


def test_fixed_worker_completion_rejects_omitted_or_duplicated_done() -> None:
    batch: dict[str, Any] = dict(
        status="completed",
        failure=None,
        worker_count=3,
        assignments=partition(6, 3),
        workers=[
            dict(
                slot=s, exitcode=0, messages=[dict(kind="done", summary=dict(paths=2))]
            )
            for s in range(3)
        ],
    )
    assert complete(batch, 6) == []
    batch["workers"][0]["messages"] *= 2
    with pytest.raises(ArithmeticError):
        complete(batch, 6)


@pytest.mark.slow
def test_whole_toy_runner_reader_and_partial_failure_retention(tmp_path: Path) -> None:
    from poker_ai.evaluation import private_prefix_run as runner
    from poker_ai.evaluation.private_prefix_read import read
    from poker_ai.evaluation.private_prefix_report import write
    from poker_ai.evaluation.private_prefix_sources import source

    current = dict(source(ROOT), dirty=False)
    path = tmp_path / "complete/own.json"
    # Test-only clean-source stand-in. This is never a published proof receipt.
    with (
        patch.object(runner, "require_checks"),
        patch.object(runner, "source", return_value=current),
        patch.object(
            runner,
            "write_report",
            side_effect=lambda saved, folder, pots: write(
                saved, folder, pots, no_plots=True
            ),
        ),
    ):
        saved = runner.tiny(ROOT, path)
    assert saved["status"] == "completed_own_native_pending"
    assert len(saved["rows"]) == 432 and len(saved["masses"]) == 288
    assert saved["journal"]["events"] > 0
    with patch(
        "poker_ai.postflop.stratified_batches.StratifiedBatchTrainer",
        side_effect=AssertionError("read constructed learner"),
    ):
        replayed, _ = read(ROOT, path, Deadline(120))
    assert replayed["replayed_now"]["baselines"]["profiles"] == 648

    failed_path = tmp_path / "failed/own.json"

    def fail_after_one_row(*args: Any, **kwargs: Any) -> Any:
        kwargs.clear()
        callback = args[6]
        callback(dict(id="INTENTIONAL_PARTIAL_BASELINE", snapshot="missing"))
        raise ValueError("intentional baseline failure")

    with (
        patch.object(runner, "require_checks"),
        patch.object(runner, "source", return_value=current),
        patch.object(runner, "toy_baselines", side_effect=fail_after_one_row),
    ):
        with pytest.raises(ValueError, match="intentional baseline failure"):
            runner.tiny(ROOT, failed_path)
    failed = json.loads(failed_path.read_text())
    assert failed["status"] == "failed_own_private_prefix_not_admitted"
    assert failed["baseline_rows"][0]["id"] == "INTENTIONAL_PARTIAL_BASELINE"
    assert failed[
        "retention_errors"
    ]  # Missing blob is retained as an error, not success.
    assert not failed["reference_constructed"]


def test_native_rejects_unpublished_own_before_any_reference(tmp_path: Path) -> None:
    from poker_ai.evaluation.private_prefix_sources import source
    from poker_ai.solver_validation import private_prefix_run as native

    own = tmp_path / "own.json"
    own.write_text("{}")
    output = tmp_path / "native.json"
    with (
        patch.object(native, "source", return_value=dict(source(ROOT), dirty=False)),
        patch.object(native, "require_checks"),
        patch.object(
            native, "published", side_effect=ArithmeticError("unpublished fixture")
        ),
        patch.object(native, "ScalarReference") as reference,
    ):
        with pytest.raises(ArithmeticError, match="unpublished fixture"):
            native.audit(ROOT, own, output, "tiny_native")
        reference.assert_not_called()
    failed = json.loads(output.read_text())
    assert failed["status"] == "failed_native_private_prefix_not_admitted"
    assert not failed["reference_setup_started"]
    assert failed["journal"]["events"] == 0
