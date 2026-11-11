"""CLI ordering/partial fixtures; mocked source identity never admits real work."""

import json
import socket
import time
from pathlib import Path
from typing import Any

import pytest

from poker_ai.evaluation import opponent_learning_admission as gates
from poker_ai.evaluation import opponent_learning_cli as cli
from poker_ai.evaluation.opponent_learning_design import TOY
from poker_ai.evaluation.opponent_learning_gate import source as source_record
from poker_ai.evaluation.opponent_learning_report import write as report_write
from poker_ai.evaluation.private_prefix_journal import validate as journal_validate


def fixture_source(monkeypatch: pytest.MonkeyPatch, *, dirty: bool = False) -> None:
    # Explicit unit-only identity: not a real commit, checked source or admission.
    monkeypatch.setattr(
        cli,
        "source",
        lambda root: dict(
            git_commit="UNIT_FIXTURE_NOT_A_COMMIT",
            dirty=dirty,
            git_status=["fixture dirty"] if dirty else [],
            sha256={"fixture": "a" * 64},
        ),
    )
    monkeypatch.setattr(cli, "contract", lambda root: {"fixture_only": True})
    monkeypatch.setattr(cli, "input_pins", lambda root: {})
    monkeypatch.setattr(gates, "require_checks", lambda root: {"unit_only": True})
    monkeypatch.setenv("POKER_OPPONENT_COMMAND_STARTED", repr(time.perf_counter()))


def test_dirty_source_retains_failure_before_any_learner(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture_source(monkeypatch, dirty=True)

    def forbidden(*a: Any, **k: Any) -> None:
        raise AssertionError("dirty source reached toy learner")

    monkeypatch.setattr(cli, "run_batch", forbidden)
    with pytest.raises(ValueError, match="clean source"):
        cli.child_main(
            tmp_path, ["software-own", "--output", "results/own.json", "--_child"]
        )
    saved = json.loads((tmp_path / "results/own.json").read_text())
    assert saved["status"] == "failed_retained"
    assert saved["source"]["dirty"] is True
    assert saved["journal"]["events"] == 0
    assert saved["long_run_admitted"] is False


def test_publication_check_precedes_native_output_and_constructor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture_source(monkeypatch)
    monkeypatch.setattr(
        cli,
        "measurement",
        lambda *a: dict(
            hostname=socket.gethostname(),
            started_perf_counter=time.perf_counter() - 5,
            seconds=1.0,
        ),
    )
    monkeypatch.setattr(cli, "read", lambda *a: {"fixture_only": True, "scope": TOY})

    def denied(*a: Any, **k: Any) -> None:
        assert not (tmp_path / "results/native.json").exists()
        assert not (tmp_path / "results/native-events.jsonl").exists()
        raise ArithmeticError("fixture own evidence not published")

    def forbidden(*a: Any, **k: Any) -> None:
        raise AssertionError("unpublished own data constructed native reference")

    monkeypatch.setattr(cli, "publication", denied)
    monkeypatch.setattr(
        "poker_ai.solver_validation.matched_array_reference.ScalarReference.__init__",
        forbidden,
    )
    with pytest.raises(ArithmeticError, match="not published"):
        cli.child_main(
            tmp_path, ["software-audit", "--output", "results/native.json", "--_child"]
        )
    saved = json.loads((tmp_path / "results/native.json").read_text())
    assert saved["status"] == "failed_preflight_retained"
    assert saved["long_run_admitted"] is False
    assert saved["events"] == []


def test_interrupted_own_stage_keeps_raw_events_and_denies_admission(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture_source(monkeypatch)

    def interrupted(
        size: int, workers: int, job: Any, payload: Any, deadline: Any, batch: Any
    ) -> None:
        batch.update(workers=[dict(slot=0, messages=[])])
        batch["workers"][0]["messages"].append(
            dict(kind="cell", phase="warm", index=0, fixture_only=True)
        )
        raise KeyboardInterrupt("unit interruption")

    monkeypatch.setattr(cli, "run_batch", interrupted)
    with pytest.raises(KeyboardInterrupt):
        cli.child_main(
            tmp_path, ["software-own", "--output", "results/own.json", "--_child"]
        )
    saved = json.loads((tmp_path / "results/own.json").read_text())
    assert saved["status"] == "failed_retained"
    assert saved["failure"]["type"] == "KeyboardInterrupt"
    assert saved["journal"]["events"] == 1
    assert saved["events"] == []
    assert len(saved["training_batch"]["workers"][0]["messages"]) == 1
    assert saved["long_run_admitted"] is False
    assert (tmp_path / "results/own-events.jsonl").exists()


def test_existing_scratch_rejects_before_a_new_learning_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture_source(monkeypatch)
    scratch = tmp_path / "old-scratch"
    scratch.mkdir()
    (scratch / "keep.txt").write_text("retained bytes")

    def forbidden(*a: Any, **k: Any) -> None:
        raise AssertionError("existing scratch reached learner")

    monkeypatch.setattr(cli, "run_batch", forbidden)
    with pytest.raises(FileExistsError):
        cli.child_main(
            tmp_path,
            [
                "software-own",
                "--output",
                "results/own.json",
                "--scratch",
                "old-scratch",
                "--_child",
            ],
        )
    assert (scratch / "keep.txt").read_text() == "retained bytes"
    assert (
        json.loads((tmp_path / "results/own.json").read_text())["status"]
        == "failed_retained"
    )


@pytest.mark.parametrize("operation", ["study", "audit"])
def test_missing_study_permit_blocks_before_any_training_or_native(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    operation: str,
) -> None:
    fixture_source(monkeypatch)

    def forbidden(*a: Any, **k: Any) -> None:
        raise AssertionError("missing permit reached a worker")

    monkeypatch.setattr(cli, "run_batch", forbidden)
    with pytest.raises(FileNotFoundError):
        cli.child_main(
            tmp_path, [operation, "--output", "results/blocked.json", "--_child"]
        )
    s = json.loads((tmp_path / "results/blocked.json").read_text())
    assert s["status"] == "failed_preflight_retained"
    assert s["long_run_admitted"] is False
    assert s["events"] == []


def test_missing_source_checks_block_before_toy_training(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture_source(monkeypatch)

    def denied(root: Path) -> None:
        raise ArithmeticError("unit missing source checks")

    def forbidden(*a: Any, **k: Any) -> None:
        raise AssertionError("unchecked software reached a worker")

    monkeypatch.setattr(gates, "require_checks", denied)
    monkeypatch.setattr(cli, "run_batch", forbidden)
    with pytest.raises(ArithmeticError, match="source checks"):
        cli.child_main(
            tmp_path, ["software-own", "--output", "results/blocked.json", "--_child"]
        )
    s = json.loads((tmp_path / "results/blocked.json").read_text())
    assert s["status"] == "failed_retained"
    assert s["journal"]["events"] == 0


def test_full_fictional_child_uses_three_workers_and_checked_archives(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # This mocked gate is UNIT COVERAGE ONLY on draft source. It cannot be
    # published as a clean-source proof, forecast or actual training admission.
    root = Path(__file__).resolve().parents[1]
    source = dict(source_record(root), dirty=False)
    monkeypatch.setattr(cli, "source", lambda r: source)
    monkeypatch.setattr(gates, "require_checks", lambda r: {"unit_only": True})
    monkeypatch.setenv("POKER_OPPONENT_COMMAND_STARTED", repr(time.perf_counter()))
    # Numerical CSV/summary are exercised; plot rendering has separate visual QA.
    monkeypatch.setattr(
        cli,
        "write_report",
        lambda p, s, d, scales: report_write(p, s, d, scales, no_plots=True),
    )
    output = tmp_path / "draft-unit-own.json"
    assert (
        cli.child_main(
            root,
            [
                "software-own",
                "--output",
                str(output),
                "--scratch",
                str(tmp_path / "scratch"),
                "--_child",
            ],
        )
        == 0
    )
    s = json.loads(output.read_text())
    assert s["status"] == "completed_own_native_pending"
    assert len(s["training_batch"]["workers"]) == 3
    assert s["own_replay"]["unique_profiles"] == 432
    assert s["own_replay"]["fixed_conditions"] == 1152
    assert s["reference_constructed"] is s["long_run_admitted"] is False
    groups = {
        3: s["events"],
        **{w["slot"]: w["messages"] for w in s["training_batch"]["workers"]},
    }
    journal_validate(
        output.with_name(s["journal"]["file"]), s["journal"], s["source_sha256"], groups
    )
