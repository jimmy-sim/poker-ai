"""Complete tiny archive and failure fixtures; never a real poker study permit."""

import copy
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from poker_ai.evaluation import compact_sampled_inputs as inputs
from poker_ai.evaluation.compact_sampled_clock import measurement, schedule
from poker_ai.evaluation.compact_sampled_own import (
    check_batch,
    gather,
    journal_rows,
    partial,
)
from poker_ai.evaluation.compact_sampled_report import summaries
from poker_ai.postflop.cell_process import THREAD_ENV, partition
from poker_ai.postflop.compact_sampled_capture import Journal, collect
from poker_ai.postflop.compact_sampled_native_checks import (
    FORMAT,
    REFERENCE,
    compare,
    validate,
)
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.public_range_definition import CANDIDATE, contract
from poker_ai.postflop.river_study import Deadline

ROOT = Path(__file__).resolve().parents[1]
FINGERPRINT = "f" * 64


@pytest.fixture(scope="module")
def archive(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, dict[str, Any]]:
    folder = tmp_path_factory.mktemp("sampled-grid")
    lookup = inputs.game_contexts(ROOT, "software")
    cases = inputs.cases(ROOT, "software")
    workers = []
    for slot, indices in enumerate(partition(36, 3)):
        journal = Journal(
            folder / f"worker-{slot}.jsonl", FINGERPRINT, "software", slot
        )
        journal.add("worker_started", indices=indices, pid=100 + slot)
        messages: list[dict[str, Any]] = [
            dict(kind="started", pid=100 + slot, thread_environment=THREAD_ENV),
            dict(kind="prepared", seconds=0.01),
        ]
        for index in indices:
            case = cases[index]
            result = collect(
                lookup[case["spot_file"], case["representation"]],
                case,
                index,
                "software",
                [1000, 3000, 10000],
                folder,
                FINGERPRINT,
                journal,
                Deadline(60),
            )
            messages.append(dict(kind="cell", phase="trained", index=index, row=result))
        summary = dict(
            paths=12, checkpoints=36, readouts=108, peak_process_rss_bytes=1000
        )
        journal.add("worker_done", summary=summary)
        messages.append(
            dict(kind="done", seconds=1.0, cpu_seconds=0.9, summary=summary)
        )
        workers.append(dict(slot=slot, pid=100 + slot, exitcode=0, messages=messages))
    batch = dict(
        status="completed",
        failure=None,
        worker_count=3,
        assignments=partition(36, 3),
        workers=workers,
        seconds=2.0,
        parent_cpu_seconds=0.1,
        reaped_children_cpu_seconds=2.0,
    )
    saved = dict(
        scope="software", source=dict(fingerprint=FINGERPRINT), training_batch=batch
    )
    return folder, saved


def test_whole_grid_and_independent_pipe_journal_agreement(
    archive: tuple[Path, dict[str, Any]],
) -> None:
    folder, saved = archive
    captured = gather(ROOT, folder, saved, score=True)
    check_batch(saved, captured)
    assert len(captured["warms"]) == 36
    assert len(captured["points"]) == 108
    assert len(captured["rows"]) == 324
    assert captured["sampled_training_performed"] is False
    assert all(
        r["previous_node_work"] < r["work_checkpoint"] <= r["total_node_work"]
        for r in captured["points"]
    )


@pytest.mark.parametrize(
    "mutation", ["missing", "duplicate", "pid", "row", "thread", "time", "exit"]
)
def test_worker_receipt_failures(
    archive: tuple[Path, dict[str, Any]], mutation: str
) -> None:
    folder, original = archive
    saved = copy.deepcopy(original)
    captured = gather(ROOT, folder, saved, score=False)
    worker = saved["training_batch"]["workers"][0]
    if mutation == "missing":
        worker["messages"].pop(3)
    elif mutation == "duplicate":
        worker["messages"][3] = copy.deepcopy(worker["messages"][2])
    elif mutation == "pid":
        worker["pid"] += 1
    elif mutation == "row":
        worker["messages"][2]["row"]["confirmed_work"] += 1
    elif mutation == "thread":
        worker["messages"][0]["thread_environment"] = {}
    elif mutation == "time":
        worker["messages"][-1]["cpu_seconds"] = float("nan")
    else:
        worker["exitcode"] = 1
    with pytest.raises(ArithmeticError):
        check_batch(saved, captured)


def test_partial_journal_retains_torn_tail_and_stops_at_first_invalid(
    tmp_path: Path,
) -> None:
    path = tmp_path / "worker-0.jsonl"
    journal = Journal(path, FINGERPRINT, "software", 0)
    journal.add("worker_started", indices=[0], pid=12)
    with path.open("ab") as stream:
        stream.write(b'{"bad":true}\n{"sequence":1}\n{"unfinished":')
    result = partial(tmp_path)["journals"][0]
    assert result["confirmed_events"] == 1
    assert result["progress_after_last_event"] == "unknown"
    assert result["unfinished_bytes"] > 0
    assert result["invalid_prefix_reason"]
    with pytest.raises((ArithmeticError, KeyError)):
        journal_rows(path, FINGERPRINT, "software", 0, complete=True)


def test_torn_last_write_not_recovered_as_a_complete_checkpoint(tmp_path: Path) -> None:
    path = tmp_path / "worker-0.jsonl"
    journal = Journal(path, FINGERPRINT, "software", 0)
    journal.add("worker_started", indices=[0], pid=12)
    with path.open("ab") as stream:
        stream.write(b'{"sequence":1')
    rows, receipt = journal_rows(path, FINGERPRINT, "software", 0, complete=False)
    assert len(rows) == 1 and receipt["unfinished_bytes"] > 0
    with pytest.raises(ArithmeticError):
        journal_rows(path, FINGERPRINT, "software", 0, complete=True)


@pytest.mark.parametrize(
    "field,value",
    [
        ("sequence", 5),
        ("sequence", True),
        ("slot", True),
        ("scope", "real"),
        ("source_fingerprint", "e" * 64),
    ],
)
def test_journal_source_sequence_failures(
    tmp_path: Path, field: str, value: Any
) -> None:
    path = tmp_path / "worker-0.jsonl"
    journal = Journal(path, FINGERPRINT, "software", 0)
    journal.add("worker_started", indices=[0], pid=12)
    row = json.loads(path.read_text())
    row[field] = value
    path.write_text(json.dumps(row) + "\n")
    with pytest.raises(ArithmeticError):
        journal_rows(path, FINGERPRINT, "software", 0, complete=True)


def native_fixture(rows: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]]:
    own = dict(scope="software", rows=rows, source=dict(fingerprint=FINGERPRINT))
    native = dict(
        format=FORMAT,
        status="completed",
        failure=None,
        scope="software",
        source=own["source"],
        own_sha256="a" * 64,
        reference=REFERENCE,
        installed_license=dict(
            sha256=REFERENCE["license_sha256"],
            previously_read_record="docs/solver_validation.md",
        ),
        actual_admission=False,
        fresh_global_admission=False,
        reference_output_used_in_training=False,
        comparisons=[
            compare(
                row,
                {
                    k: row[k]
                    for k in (
                        "value_player_zero_chips",
                        "best_response_zero_chips",
                        "best_response_one_chips",
                    )
                },
            )
            for row in rows
        ],
    )
    return own, native


def test_native_self_comparison_is_zero(archive: tuple[Path, dict[str, Any]]) -> None:
    folder, saved = archive
    original, native = native_fixture(gather(ROOT, folder, saved, score=True)["rows"])
    validate(original, native, "a" * 64)
    assert all(r["maximum_error_chips"] == 0 for r in native["comparisons"])


@pytest.mark.parametrize(
    "mutation",
    [
        "missing",
        "duplicate",
        "root",
        "fake_error",
        "license",
        "scope",
        "source",
        "training",
        "input",
        "profile",
    ],
)
def test_native_failure_receipts(
    archive: tuple[Path, dict[str, Any]], mutation: str
) -> None:
    folder, saved = archive
    original, native = native_fixture(gather(ROOT, folder, saved, score=True)["rows"])
    if mutation == "missing":
        native["comparisons"].pop()
    elif mutation == "duplicate":
        native["comparisons"][-1] = copy.deepcopy(native["comparisons"][0])
    elif mutation == "root":
        native["comparisons"][0]["native"]["best_response_one_chips"] += 1
    elif mutation == "fake_error":
        native["comparisons"][0]["maximum_error_chips"] = 0.01
    elif mutation == "license":
        native["installed_license"]["sha256"] = "b" * 64
    elif mutation == "scope":
        native["scope"] = "real"
    elif mutation == "source":
        native["source"] = dict(fingerprint="e" * 64)
    elif mutation == "training":
        native["reference_output_used_in_training"] = True
    elif mutation == "input":
        native["own_sha256"] = "b" * 64
    else:
        native["comparisons"][0]["own_profile_sha256"] = "b" * 64
    with pytest.raises(ArithmeticError):
        validate(original, native, "a" * 64)


@pytest.mark.parametrize("bad", [True, float("nan"), float("inf"), "0.1"])
def test_native_invalid_scalar(bad: Any) -> None:
    with pytest.raises(ValueError):
        compare(
            {},
            dict(
                value_player_zero_chips=bad,
                best_response_zero_chips=1,
                best_response_one_chips=1,
            ),
        )


def test_full_deadline_reserve_is_not_reduced_by_fast_forecast() -> None:
    now = datetime(2026, 11, 12, 14, 55, tzinfo=UTC)
    schedule("study", "2026-11-12T18:00:00Z", now)
    with pytest.raises(TimeoutError):
        schedule("study", "2026-11-12T18:00:00Z", now + timedelta(seconds=1))
    with pytest.raises(ValueError):
        schedule("study", "2026-11-12T18:00:00", now)


def test_clock_rejects_fabricated_success(tmp_path: Path) -> None:
    path = tmp_path / "own.json"
    child = tmp_path / "own-child.json"
    raw = dict(status="completed")
    child.write_text(json.dumps(raw))
    path.write_text(
        json.dumps(
            dict(
                raw,
                complete_command=dict(
                    operation="study",
                    returncode=0,
                    interrupted=None,
                    retained_temporary=None,
                    seconds=7200,
                    child_file=child.name,
                    child_sha256=sha(raw),
                ),
            )
        )
    )
    with pytest.raises(ArithmeticError):
        measurement(path, "study")


def test_signed_result_keeps_unfavorable_seeds() -> None:
    config = contract(ROOT)
    rows = [
        dict(
            spot_file=spot,
            representation=rep,
            seed=seed,
            work_checkpoint=work,
            readout=readout,
            exploitability_pot=0.1 if rep == CANDIDATE else 0.05,
        )
        for spot in config["spot_files"]
        for rep in config["representations"]
        for seed in config["sampled"]["seeds"]
        for work in config["sampled"]["node_work_checkpoints"]
        for readout in inputs.READOUTS
    ]
    result = summaries(rows, config)
    assert len(result["final_linear_paired"]) == 30
    assert all(
        r["candidate_minus_baseline_pot"] > 0 for r in result["final_linear_paired"]
    )
    assert not any(
        r.get("both_games_paired_median_better", False)
        for r in result["baseline_specific_superiority"]
    )
    with pytest.raises(ArithmeticError):
        summaries(rows[:-1], config)
