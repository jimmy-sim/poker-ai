"""Explicit fictional timing fixtures test audits/forecasts, never benchmark data."""

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from poker_ai.postflop import controlled_profile as original
from poker_ai.postflop import parallel_profile as study
from poker_ai.postflop.cell_process import THREAD_ENV, partition
from poker_ai.validation.five_card import source_provenance

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def receipt() -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    config = json.loads((ROOT / study.CONFIG).read_text())
    prior, cells, _ = study.inputs(ROOT, config)
    reference = study.endpoint_reference(prior)
    diagnostics = {
        original.identity(d): d for d in prior["cache_diagnostics"] if d["repeat"] == 0
    }
    trees = {
        json.dumps((r["spot_file"], r["representation"])): r["tree_nodes"]
        for r in reference.values()
    }
    batches: list[dict[str, Any]] = []
    for repeat, order in enumerate(study.ORDERS):
        for p in order:
            assignments = partition(len(cells), p)
            workers: list[dict[str, Any]] = []
            for slot, indices in enumerate(assignments):
                messages: list[dict[str, Any]] = [
                    dict(
                        kind="started", pid=1000 + slot, thread_environment=THREAD_ENV
                    ),
                    dict(kind="prepared", seconds=2.0, tree_nodes=trees),
                ]
                for index in indices:
                    peer = reference[original.identity(cells[index])]
                    row = {
                        k: peer[k] for k in (*original.KEY, *original.STABLE)
                    } | dict(initialization_seconds=0.1, incremental_seconds=1.0)
                    diag = {}
                    if row["traversal"] == "external":
                        old = diagnostics[original.identity(row)]
                        diag = {
                            k: old[k]
                            for k in (
                                "row_evaluations",
                                "last_pass_rows",
                                "node_records_prepared",
                            )
                        } | dict(node_setup_seconds=0.01)
                    messages.append(
                        dict(
                            kind="cell",
                            index=index,
                            row=row,
                            diagnostics=diag,
                            seconds=1.2,
                            cpu_seconds=1.0,
                        )
                    )
                messages.append(
                    dict(
                        kind="done",
                        seconds=2.5 + 1.2 * len(indices),
                        cpu_seconds=1.0 + len(indices),
                        summary=dict(cells=len(indices)),
                    )
                )
                workers.append(
                    dict(slot=slot, pid=1000 + slot, messages=messages, exitcode=0)
                )
            batches.append(
                dict(
                    repeat=repeat,
                    worker_count=p,
                    assignments=assignments,
                    workers=workers,
                    status="completed",
                    failure=None,
                    seconds=max(w["messages"][-1]["seconds"] for w in workers) + 0.5,
                    parent_cpu_seconds=0.1,
                    reaped_children_cpu_seconds=140.0 + p,
                )
            )
    source = source_provenance(ROOT, ROOT / study.CONFIG, entrypoints=(study.ENTRY,))
    source["dirty"] = False  # Synthetic test fixture, never a published measurement.
    saved: dict[str, Any] = dict(
        format=study.FORMAT,
        status="completed",
        failure=None,
        config=config,
        source=source,
        environment={},
        batches=batches,
        seconds=sum(b["seconds"] for b in batches) + 10,
        strength_comparison_performed=False,
    )
    return saved, prior, cells


def test_complete_synthetic_receipt_report(
    receipt: tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]], tmp_path: Path
) -> None:
    saved, prior, cells = receipt
    study.validate(saved, prior, cells)
    path = tmp_path / "synthetic.json"
    path.write_text(json.dumps(saved))
    _, summary = study.report(ROOT, path)
    assert summary["endpoint_rows"] == 1260
    assert len(summary["batches"]) == 9
    assert set(summary["forecasts"]) == {"1", "2", "3"}
    assert summary["strength_comparison_performed"] is False
    assert "No automatic learning admission" in study.tables(summary)


@pytest.mark.parametrize(
    "change",
    [
        "batch",
        "order",
        "repeat_type",
        "partition",
        "pid",
        "environment",
        "exit",
        "missing_event",
        "cell_index",
        "state",
        "work_type",
        "extra_metric",
        "cache",
        "cpu",
        "setup",
        "cell_time",
        "worker_time",
        "elapsed",
    ],
)
def test_reject_incomplete_or_changed_evidence(
    receipt: tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]], change: str
) -> None:
    saved, prior, cells = receipt
    batch = saved["batches"][1]  # two workers
    worker = batch["workers"][0]
    event = next(e for e in worker["messages"] if e["kind"] == "cell")
    if change == "batch":
        saved["batches"].pop()
    elif change == "order":
        saved["batches"][0], saved["batches"][1] = (
            saved["batches"][1],
            saved["batches"][0],
        )
    elif change == "repeat_type":
        batch["repeat"] = False
    elif change == "partition":
        batch["assignments"][0][0] = 1
    elif change == "pid":
        batch["workers"][1]["pid"] = worker["pid"]
        batch["workers"][1]["messages"][0]["pid"] = worker["pid"]
    elif change == "environment":
        worker["messages"][0]["thread_environment"] = {}
    elif change == "exit":
        worker["exitcode"] = -15
    elif change == "missing_event":
        worker["messages"].pop(2)
    elif change == "cell_index":
        event["index"] = True
    elif change == "state":
        event["row"]["state_sha256"] = "a" * 64
    elif change == "work_type":
        event["row"]["initialization_visits"] = float(
            event["row"]["initialization_visits"]
        )
    elif change == "extra_metric":
        event["row"]["exploitability_chips"] = 0.0
    elif change == "cache":
        e = next(
            e
            for w in batch["workers"]
            for e in w["messages"]
            if e["kind"] == "cell" and e["row"]["traversal"] == "external"
        )
        e["diagnostics"]["node_records_prepared"] = 0
    elif change == "cpu":
        batch["reaped_children_cpu_seconds"] = float("nan")
    elif change == "setup":
        worker["messages"][1]["tree_nodes"] = {}
    elif change == "cell_time":
        event["seconds"] = 0.01
    elif change == "worker_time":
        worker["messages"][-1]["seconds"] = 0.01
    else:
        saved["seconds"] = 1.0
    with pytest.raises(ArithmeticError):
        study.validate(saved, prior, cells)


def test_reject_changed_source_scope_status_and_config(
    receipt: tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]], tmp_path: Path
) -> None:
    saved, _, _ = receipt
    for mode in ("source", "dirty", "status", "scope", "config"):
        changed = copy.deepcopy(saved)
        if mode == "source":
            changed["source"]["sha256"] = {}
        elif mode == "dirty":
            changed["source"]["dirty"] = True
        elif mode == "status":
            changed["status"] = "incomplete"
        elif mode == "scope":
            changed["strength_comparison_performed"] = True
        else:
            changed["config"]["worker_counts"] = [1, 3]
        path = tmp_path / (mode + ".json")
        path.write_text(json.dumps(changed))
        with pytest.raises((ArithmeticError, ValueError)):
            study.report(ROOT, path)


def test_forecast_fixed_partition_maxima_and_overhead() -> None:
    cells = [
        dict(
            spot_file="synthetic",
            representation=str(i),
            traversal="external",
            regret_rule="signed",
            regret_weight="linear",
            average_weight="linear",
            seed=1,
            bridge="common",
        )
        for i in range(3)
    ]
    batches: list[dict[str, Any]] = []
    for repeat in range(3):
        workers: list[dict[str, Any]] = []
        for indices in partition(3, 2):
            events: list[dict[str, Any]] = []
            for i in indices:
                # Cell 0's maximum is in the second repeat; cell 2 is always heavy.
                loop = [2.0, 5.0, 3.0][repeat] if i == 0 else 2.0 if i == 1 else 4.0
                events.append(
                    dict(
                        kind="cell",
                        row={
                            **cells[i],
                            "initialization_seconds": 1.0,
                            "incremental_seconds": loop,
                            "initialization_visits": 20,
                            "incremental_visits": 10,
                        },
                    )
                )
            total = sum(
                e["row"]["initialization_seconds"] + e["row"]["incremental_seconds"]
                for e in events
            )
            events.append(dict(kind="done", seconds=total + 3.0))
            workers.append(dict(messages=events))
        batches.append(
            dict(
                worker_count=2,
                workers=workers,
                seconds=max(w["messages"][-1]["seconds"] for w in workers) + 4.0,
            )
        )
    config = dict(
        forecast_target_node_work=100,
        forecast_guard_multiplier=2.0,
        own_stage_cap_seconds=150,
    )
    result = study.forecast(batches, cells, config)
    assert result["worker_training_seconds"] == [74.0, 17.0]
    assert result["maximum_worker_nontraining_seconds"] == 3.0
    assert result["maximum_launch_collection_seconds"] == 4.0
    assert result["known_training_launch_forecast_seconds"] == 81.0
    assert result["guarded_known_seconds"] == 162.0
    assert result["decision"] == "known_cost_exceeds_cap"
    config["own_stage_cap_seconds"] = 200
    assert (
        study.forecast(batches, cells, config)["decision"]
        == "unresolved_unmeasured_pipeline_cost"
    )


def test_recursive_equality_rejects_boolean_and_float_integer_substitutions() -> None:
    assert not study.same([(0, 1)], [(False, 1)])
    assert not study.same([1], [1.0])
