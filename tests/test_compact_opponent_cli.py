"""CLI ordering/partial fixtures; mocked source identity never admits real work."""

import json
import socket
import time
from itertools import product
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np
import pytest

from poker_ai.evaluation import compact_opponent_admission as gates
from poker_ai.evaluation import compact_opponent_cli as cli
from poker_ai.evaluation.compact_opponent_source import source as source_record
from poker_ai.evaluation.opponent_learning_design import REAL, TOY
from poker_ai.evaluation.opponent_learning_own import fixture as own_fixture
from poker_ai.evaluation.opponent_learning_report import write as report_write
from poker_ai.evaluation.opponent_learning_score import scoring
from poker_ai.evaluation.private_prefix_journal import validate as journal_validate
from poker_ai.postflop.controlled_checkpoints import unpack_policy
from poker_ai.postflop.learning_artifacts import decode, read_archive
from poker_ai.postflop.river_study import digest


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
    monkeypatch.setattr(
        cli, "contract", lambda root: {"fixture_only": True, "study_id": "UNIT_ONLY"}
    )
    monkeypatch.setattr(cli, "input_pins", lambda root: {})
    monkeypatch.setattr(gates, "require_checks", lambda root: {"unit_only": True})
    monkeypatch.setenv("POKER_COMPACT_OPPONENT_STARTED", repr(time.perf_counter()))


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


def test_missing_other_own_costs_block_before_native_cost_constructor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture_source(monkeypatch)
    monkeypatch.setattr(cli, "read", lambda *a: {"scope": TOY, "UNIT": True})
    monkeypatch.setattr(cli, "publication", lambda *a: {"UNIT": True})
    monkeypatch.setattr(gates, "software", lambda *a: {"UNIT": True})

    def missing(*args: Any) -> list[dict[str, Any]]:
        raise ArithmeticError("all three own cost publications required")

    def forbidden(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("incomplete own costs reached reference worker")

    monkeypatch.setattr(gates, "all_own_costs_published", missing)
    monkeypatch.setattr(cli, "run_batch", forbidden)
    output = tmp_path / "native.json"
    with pytest.raises(ArithmeticError, match="all three"):
        cli.child_main(
            tmp_path,
            ["cost-audit", "--repetition", "0", "--output", str(output), "--_child"],
        )
    saved = json.loads(output.read_text())
    assert saved["status"] == "failed_preflight_retained"
    assert saved["reference_constructed"] is False
    assert saved["reference_construction_attempted"] is False
    assert saved["events"] == []


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
    monkeypatch.setenv("POKER_COMPACT_OPPONENT_STARTED", repr(time.perf_counter()))
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
    # Direct terminal sums and exhaustive pure choices are independent of the
    # production tree-value/BR routines. Check this NEW spawned dataset, not
    # only identity aliases or a previously published software archive.
    contexts, _ = own_fixture()
    positive_gaps = 0
    for row, blob in read_archive(
        output.parent / s["details_file"], s["details_sha256"], s["rows"]
    ):
        game = row["coordinate"] // 3
        context = scoring(contexts[game], row)
        detail = decode(blob, context, row)
        fine = context.expand(unpack_policy(context.partition, detail["policy"]))

        def value(p: np.ndarray[Any, Any], game: int = game) -> float:
            a, b, c, d = p
            v = 0.5 * (a[1] * (c[0] - c[1]) + b[1] * (-d[0] + d[1]))
            return float(v if game == 0 else -v)

        assert abs(value(fine) - row["metrics"]["value_player_zero_chips"]) < 1e-12
        for target in (0, 1):
            choices = []
            owned = np.flatnonzero(context.exact.owners == target)
            for moves in product((0, 1), repeat=len(owned)):
                p = fine.copy()
                for info, action in zip(owned, moves, strict=True):
                    p[info] = 0
                    p[info, action] = 1
                choices.append((1 if target == 0 else -1) * value(p))
            expected = max(choices)
            assert (
                abs(expected - row["responses"][target]["exact_reply_value_chips"])
                < 1e-12
            )
            positive_gaps += (
                row["responses"][target]["extra_information_gap_chips"] > 1e-9
            )
    assert positive_gaps > 0


@pytest.mark.parametrize("witnessed", [False, True])
def test_interrupted_real_label_records_unknown_or_witnessed_training_truthfully(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    witnessed: bool,
) -> None:
    # Synthetic REAL LABEL tests plumbing only. Both admission and source are
    # mocked; no real game factory, learner, poker trajectory or solver runs.
    fixture_source(monkeypatch)
    games, opponents = own_fixture()
    monkeypatch.setattr(
        gates,
        "require_admission",
        lambda *a: {"long_run_admitted": True, "unit_only_not_a_real_permit": True},
    )
    permit = tmp_path / gates.ADMISSION
    permit.parent.mkdir(parents=True)
    permit.write_text("UNIT ONLY NOT A REAL PERMIT")
    monkeypatch.setattr(
        cli,
        "load",
        lambda r, deadline: SimpleNamespace(
            games=games,
            context=lambda i: games[i // 3],
            opponents=opponents,
            original_boundaries=(),
        ),
    )
    output = tmp_path / "partial.json"
    running: dict[str, Any] = {}

    def interrupted(
        size: int, workers: int, job: Any, payload: Any, deadline: Any, batch: Any
    ) -> None:
        running.update(json.loads(output.read_text()))
        batch.update(workers=[dict(slot=0, messages=[])])
        if witnessed:
            for phase, row in (
                ("warm", dict(initialization_visits=12)),
                ("capture", dict(total_work=45)),
            ):
                batch["workers"][0]["messages"].append(
                    dict(
                        kind="cell",
                        phase=phase,
                        index=0,
                        row=dict(row, scope=REAL, path_index=0),
                    )
                )
        raise KeyboardInterrupt("synthetic interruption, no actual training")

    monkeypatch.setattr(cli, "run_batch", interrupted)
    with pytest.raises(KeyboardInterrupt):
        cli.child_main(tmp_path, ["study", "--output", str(output), "--_child"])
    saved = json.loads(output.read_text())
    assert saved["poker_training_performed"] is (True if witnessed else None)
    assert running["poker_training_performed"] is None
    assert saved["actual_poker_training_work"] is None
    assert saved["observed_training_work_lower_bound"] == (45 if witnessed else 0)
    assert saved["long_run_admitted"] is True  # Mock permit, not a strength claim.
    assert saved["compute_permit_checked"] is True


@pytest.mark.parametrize("witnessed", [False, True])
def test_interrupted_native_attempt_does_not_claim_no_construction(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    witnessed: bool,
) -> None:
    # Entirely mocked native-stage messages. No independent solver is built.
    fixture_source(monkeypatch)
    own_path = tmp_path / "results/compact-own-opponent-learning/software/own.json"
    own_path.parent.mkdir(parents=True)
    own_path.write_text("UNIT ONLY NOT OWN SCIENTIFIC EVIDENCE")
    monkeypatch.setattr(
        cli,
        "measurement",
        lambda *a: dict(
            hostname=socket.gethostname(),
            started_perf_counter=time.perf_counter() - 1,
            seconds=0.1,
        ),
    )
    monkeypatch.setattr(cli, "read", lambda *a: dict(scope=TOY))
    monkeypatch.setattr(
        cli, "publication", lambda *a: dict(own_sha256=digest(own_path))
    )
    monkeypatch.setattr(
        "poker_ai.solver_validation.controlled_pipeline.license_record",
        lambda *a: {"unit_only_not_a_license_check": True},
    )
    output = tmp_path / "native.json"
    running: dict[str, Any] = {}

    def interrupted(
        size: int, workers: int, job: Any, payload: Any, deadline: Any, batch: Any
    ) -> None:
        running.update(json.loads(output.read_text()))
        batch.update(workers=[dict(slot=0, messages=[])])
        if witnessed:
            batch["workers"][0]["messages"].append(
                dict(
                    kind="cell",
                    phase="self",
                    index=0,
                    result={"unit_only_not_a_scalar_comparison": True},
                )
            )
        raise KeyboardInterrupt("synthetic native interruption, no solver")

    monkeypatch.setattr(cli, "run_batch", interrupted)
    with pytest.raises(KeyboardInterrupt):
        cli.child_main(
            tmp_path, ["software-audit", "--output", str(output), "--_child"]
        )
    saved = json.loads(output.read_text())
    assert saved["reference_constructed"] is (True if witnessed else None)
    assert running["reference_constructed"] is None
    assert running["reference_construction_attempted"] is True
    assert saved["poker_training_performed"] is False
    assert saved["reference_output_used_in_training"] is False
