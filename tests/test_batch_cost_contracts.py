"""Synthetic cost ledgers isolate contracts; these are not profiling evidence."""

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from poker_ai.evaluation import batch_cost_inputs as inputs
from poker_ai.evaluation import batch_cost_run as run
from poker_ai.evaluation.batch_cost_stats import call_accounting
from poker_ai.evaluation.batch_cost_validation import gather, grid
from poker_ai.postflop.cell_process import partition
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.river_study import digest

ROOT = Path(__file__).resolve().parents[1]


def fixture() -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    config = json.loads((ROOT / inputs.CONFIG).read_text())
    original = json.loads((ROOT / config["source_profile"]).read_text())
    selected = [
        next(r for r in original["rows"] if r["index"] == i and r["repetition"] == 0)
        for i in config["selected_source_indices"]
    ]
    rows = []
    for index, source in enumerate(selected):
        point = copy.deepcopy(source)
        point.pop("projected_training_seconds")
        point.pop("index")
        for mode in config["modes"]:
            stats = None
            calls = None
            if mode == "instrumented":
                functions = []
                names = [
                    (
                        "src/poker_ai/training/mccfr.py",
                        "external_updates",
                        point["sampled_traversals"],
                    ),
                    (
                        "src/poker_ai/training/mccfr.py",
                        "visit",
                        point["incremental_visits"],
                    ),
                ]
                if point["path"]["batch_size"] > 1:
                    names.append(
                        (
                            "src/poker_ai/postflop/frozen_batches.py",
                            "mean_updates",
                            2 * (point["iteration"] - 1),
                        )
                    )
                for file, name, count in names:
                    frame = dict(file=file, line=1, name=name)
                    functions.append(
                        dict(
                            **frame,
                            id=sha(frame),
                            primitive_calls=1,
                            total_calls=count,
                            self_seconds=0.01,
                            cumulative_seconds=0.05,
                        )
                    )
                edge = dict(
                    caller=functions[0]["id"],
                    callee=functions[1]["id"],
                    primitive_calls=1,
                    total_calls=point["incremental_visits"],
                    self_seconds=0.01,
                    cumulative_seconds=0.05,
                )
                stats = dict(
                    functions=functions,
                    callers=[edge],
                    frame_count=len(functions),
                    edge_count=1,
                    total_self_seconds=0.01 * len(functions),
                )
                calls = call_accounting(stats, point)
            rows.append(
                dict(
                    index=index,
                    source_index=source["index"],
                    mode=mode,
                    endpoint=copy.deepcopy(point),
                    whole_measure_seconds=100.0,
                    stats=stats,
                    call_accounting=calls,
                )
            )
    batch: dict[str, Any] = dict(
        status="completed", failure=None, assignments=partition(24, 3), workers=[]
    )
    for slot, assigned in enumerate(batch["assignments"]):
        events = []
        for row in rows:
            if row["index"] in assigned:
                events.extend(
                    [
                        dict(
                            kind="prepared",
                            phase="measurement_started",
                            index=row["index"],
                            mode=row["mode"],
                        ),
                        dict(kind="cell", index=row["index"], row=row),
                    ]
                )
        events.append(
            dict(
                kind="done",
                summary=dict(
                    paths=len(assigned),
                    endpoints=2 * len(assigned),
                    function_profiles=len(assigned),
                ),
            )
        )
        batch["workers"].append(dict(slot=slot, exitcode=0, messages=events))
    return config, selected, batch


def test_complete_fictional_grid_checks_schema_and_independent_call_counts() -> None:
    config, selected, batch = fixture()
    rows = gather(batch, selected, config)
    assert len(rows) == 48
    assert sum(r["stats"] is not None for r in rows) == 24
    assert sum(len(r["endpoint"]["prefix_checks"]) for r in rows) == 32


@pytest.mark.parametrize(
    "damage",
    [
        "missing",
        "duplicate",
        "source",
        "guard",
        "work",
        "readout",
        "prefix",
        "projection",
        "nan",
        "elapsed",
        "plain_stats",
        "profiler_work",
        "stats_self_total",
        "caller",
        "mode",
        "index_bool",
    ],
)
def test_altered_cost_endpoint_or_ledger_is_rejected(damage: str) -> None:
    config, selected, batch = fixture()
    rows = gather(batch, selected, config)
    row = rows[1]
    point = row["endpoint"]
    if damage == "missing":
        rows.pop()
    elif damage == "duplicate":
        rows[-1] = copy.deepcopy(rows[0])
    elif damage == "source":
        row["source_index"] += 1
    elif damage == "guard":
        point["guard_sha256"] = "f" * 64
    elif damage == "work":
        point["total_work"] += 1
    elif damage == "readout":
        point["readout_sha256"]["linear"] = "f" * 64
    elif damage == "prefix":
        point["prefix_checks"].pop()
    elif damage == "projection":
        point["projected_training_seconds"] = 1.0
    elif damage == "nan":
        row["whole_measure_seconds"] = float("nan")
    elif damage == "elapsed":
        row["whole_measure_seconds"] = 0.0
    elif damage == "plain_stats":
        rows[0]["stats"] = row["stats"]
    elif damage == "profiler_work":
        row["stats"]["functions"][0]["total_calls"] += 1
    elif damage == "stats_self_total":
        row["stats"]["total_self_seconds"] += 1
    elif damage == "caller":
        row["stats"]["callers"][0]["caller"] = "f" * 64
    elif damage == "mode":
        row["mode"] = "best"
    elif damage == "index_bool":
        row["index"] = False
    with pytest.raises((ArithmeticError, KeyError)):
        grid(rows, selected, config)


@pytest.mark.parametrize(
    "damage",
    [
        "failed",
        "exit",
        "assignment",
        "start_missing",
        "start_duplicate",
        "done",
        "row_assignment",
    ],
)
def test_worker_failures_are_not_complete(damage: str) -> None:
    config, selected, batch = fixture()
    worker = batch["workers"][0]
    if damage == "failed":
        batch["status"] = "incomplete"
    elif damage == "exit":
        worker["exitcode"] = 1
    elif damage == "assignment":
        batch["assignments"][0].pop()
    elif damage == "start_missing":
        worker["messages"].pop(0)
    elif damage == "start_duplicate":
        worker["messages"][2] = copy.deepcopy(worker["messages"][0])
    elif damage == "done":
        worker["messages"].pop()
    elif damage == "row_assignment":
        worker["messages"][1]["index"] = 1
    with pytest.raises((ArithmeticError, KeyError)):
        gather(batch, selected, config)


def test_fixed_cost_protocol_cannot_relax_cap_or_select_another_seed(
    tmp_path: Path,
) -> None:
    config = inputs.config_inputs(ROOT)
    (tmp_path / "configs").mkdir()
    for key, value in [
        ("maximum_seconds", 901),
        ("seed", 20261302),
        ("expected_paths", 23),
    ]:
        changed = copy.deepcopy(config)
        changed[key] = value
        (tmp_path / inputs.CONFIG).write_text(json.dumps(changed))
        with pytest.raises(ArithmeticError):
            inputs.config_inputs(tmp_path)


def test_failed_input_is_saved_with_no_completed_or_attempted_training(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = json.loads((ROOT / inputs.CONFIG).read_text())
    marker = tmp_path / "original.json"
    marker.write_text("{}")
    config["source_profile"] = marker.name
    monkeypatch.setattr(inputs, "config_inputs", lambda root: config)
    monkeypatch.setattr(
        inputs,
        "binding",
        lambda root: (
            {"dirty": False, "sha256": {"EXPLICIT_TEST": "a" * 64}},
            "a" * 64,
        ),
    )
    monkeypatch.setattr(
        inputs, "require_checks", lambda root: dict(source_sha256="a" * 64)
    )
    monkeypatch.setattr(run, "runtime_environment", lambda: config["prefix_runtime"])

    def fail(root: Path) -> Any:
        raise TimeoutError("EXPLICIT_TEST_INPUT_FAILURE")

    monkeypatch.setattr(inputs, "prerequisites", fail)
    output = tmp_path / "attempt/profile.json"
    with pytest.raises(TimeoutError):
        run.run(tmp_path, output)
    saved = json.loads(output.read_text())
    assert saved["status"] == "incomplete" and saved["completed_endpoints"] == 0
    assert saved["short_prefix_training_attempted"] is False
    assert saved["prefix_training_requested"] is True
    assert saved["long_learning_performed"] is False
    with pytest.raises(FileExistsError):
        run.run(tmp_path, output)


def test_checked_cost_source_receipt_and_wrong_observation_rejection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    file = tmp_path / "EXPLICIT_SOURCE.py"
    file.write_text("# test source\n")
    source = dict(dirty=False, git_commit="f" * 40, sha256={file.name: digest(file)})
    h = sha(source["sha256"])
    monkeypatch.setattr(inputs, "source", lambda root: source)
    monkeypatch.setattr(inputs, "config_inputs", lambda root: {})
    ci: dict[str, Any] = dict(
        checked_commit=source["git_commit"],
        source_sha256=h,
        run_id=123,
        jobs=copy.deepcopy(inputs.JOBS),
    )
    local: dict[str, Any] = dict(source_sha256=h, checks=copy.deepcopy(inputs.LOCAL))
    saved = inputs.record_checks(tmp_path, ci, local)
    from poker_ai.postflop.learning_run import persist

    persist(tmp_path / inputs.CHECKED, saved)
    assert inputs.require_checks(tmp_path) == saved
    for damage in ("commit", "hash", "job", "bool_run", "local"):
        c, checked_local = copy.deepcopy(ci), copy.deepcopy(local)
        if damage == "commit":
            c["checked_commit"] = "e" * 40
        elif damage == "hash":
            c["source_sha256"] = "e" * 64
        elif damage == "job":
            c["jobs"]["Python 3.12"] = "pending"
        elif damage == "bool_run":
            c["run_id"] = True
        elif damage == "local":
            checked_local["checks"].pop("slow_integrations")
        with pytest.raises(ArithmeticError):
            inputs.record_checks(tmp_path, c, checked_local)
