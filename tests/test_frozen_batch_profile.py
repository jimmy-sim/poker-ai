"""Fictional timing rows test contracts, not benchmark or solver evidence."""

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from poker_ai.evaluation import frozen_batch_inputs as inputs
from poker_ai.evaluation import frozen_batch_profile as profile
from poker_ai.evaluation import frozen_batch_protocol as protocol
from poker_ai.postflop.cell_process import partition

ROOT = Path(__file__).resolve().parents[1]


def fixture() -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    config = json.loads((ROOT / inputs.CONFIG).read_text())
    rows = []
    for index, path in enumerate(inputs.paths(config)):
        for repeat in range(3):
            setup, seconds = 0.1 + repeat * 0.01, 0.01 + repeat * 0.001
            rows.append(
                dict(
                    index=index,
                    path=path,
                    repetition=repeat,
                    initialization_visits=1000,
                    incremental_visits=100000,
                    total_work=101000,
                    previous_work=100900,
                    last_iteration_visits=100,
                    iteration=1001,
                    sampled_traversals=2 * path["batch_size"] * 1000,
                    overshoot=0,
                    guard_sha256="a" * 64,
                    readout_sha256={"uniform": "b" * 64, "linear": "c" * 64},
                    prefix_checks=[{"scope": "FICTIONAL_SCHEMA_ONLY"}] * 2
                    if path["batch_size"] == 1
                    else [],
                    setup_and_warm_seconds=setup,
                    incremental_seconds=seconds,
                    cpu_seconds=seconds,
                    projected_training_seconds=setup + seconds * 9999000 / 100000,
                )
            )
    batch: dict[str, Any] = dict(
        status="completed", failure=None, assignments=partition(72, 3), workers=[]
    )
    for slot, assigned in enumerate(batch["assignments"]):
        events = [
            dict(
                kind="cell",
                index=r["index"],
                row={k: v for k, v in r.items() if k != "index"},
            )
            for r in rows
            if r["index"] in assigned
        ]
        events.append(
            dict(
                kind="done",
                summary=dict(paths=len(assigned), timing_rows=3 * len(assigned)),
            )
        )
        batch["workers"].append(dict(slot=slot, exitcode=0, messages=events))
    return config, rows, batch


def test_complete_forecast_uses_max_repeat_and_two_sequential_phase_partitions() -> (
    None
):
    config, rows, batch = fixture()
    assert profile.gather(batch, config) == rows
    result = profile.forecast(rows, config)
    maximum = rows[2]["projected_training_seconds"]
    assert result["training_barrier_forecast_seconds"] == pytest.approx(24 * maximum)
    assert result["guarded_own_seconds"] == pytest.approx(2 * (2 * 24 * maximum + 600))
    assert result["repeated_B1_readout_prefix_checks"] == 144
    assert result["decision"] == "fits_requires_checked_admission"
    assert result["strength_scores_measured"] is False


@pytest.mark.parametrize(
    "damage",
    [
        "missing",
        "duplicate",
        "path",
        "repeat",
        "negative_time",
        "nan",
        "work_bool",
        "overshoot",
        "last_visits",
        "traversals",
        "projection",
        "repeat_state",
        "prefixes",
    ],
)
def test_timing_failures_cannot_become_a_complete_forecast(damage: str) -> None:
    config, rows, _ = fixture()
    if damage == "missing":
        rows.pop()
    elif damage == "duplicate":
        rows[-1] = copy.deepcopy(rows[0])
    elif damage == "path":
        rows[0]["path"]["seed"] = 999
    elif damage == "repeat":
        rows[0]["repetition"] = True
    elif damage == "negative_time":
        rows[0]["incremental_seconds"] = -1
    elif damage == "nan":
        rows[0]["cpu_seconds"] = float("nan")
    elif damage == "work_bool":
        rows[0]["iteration"] = True
    elif damage == "overshoot":
        rows[0]["overshoot"] = 1
    elif damage == "last_visits":
        rows[0]["last_iteration_visits"] = 0
    elif damage == "traversals":
        rows[0]["sampled_traversals"] = 0
    elif damage == "projection":
        rows[0]["projected_training_seconds"] += 1
    elif damage == "repeat_state":
        rows[0]["guard_sha256"] = "d" * 64
    elif damage == "prefixes":
        rows[0]["prefix_checks"] = []
    with pytest.raises(ArithmeticError):
        profile.forecast(rows, config)


def test_exceeding_forecast_is_retained_as_failure_not_grid_reduction() -> None:
    config, rows, _ = fixture()
    for row in rows:
        row["incremental_seconds"] *= 1000
        row["projected_training_seconds"] = (
            row["setup_and_warm_seconds"]
            + row["incremental_seconds"] * 9999000 / 100000
        )
    result = profile.forecast(rows, config)
    assert result["decision"] == "exceeds_cap_stop_before_long_learning"
    assert result["timing_rows"] == 216
    assert result["guarded_own_seconds"] > 7200


@pytest.mark.parametrize(
    "damage", ["failed", "assignment", "exit", "done", "missing", "duplicate"]
)
def test_timing_worker_failures_are_rejected(damage: str) -> None:
    config, _, batch = fixture()
    if damage == "failed":
        batch["status"] = "incomplete"
    elif damage == "assignment":
        batch["assignments"][0].pop()
    elif damage == "exit":
        batch["workers"][0]["exitcode"] = 1
    elif damage == "done":
        batch["workers"][0]["messages"].pop()
    elif damage == "missing":
        batch["workers"][0]["messages"].pop(0)
    elif damage == "duplicate":
        batch["workers"][0]["messages"][0] = copy.deepcopy(
            batch["workers"][0]["messages"][1]
        )
    with pytest.raises(ArithmeticError):
        profile.gather(batch, config)


def test_prefix_input_failure_is_saved_before_training_and_not_overwritten(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config, _, _ = fixture()
    monkeypatch.setattr(inputs, "config_inputs", lambda root: config)
    monkeypatch.setattr(
        inputs,
        "binding",
        lambda root: (
            {"dirty": False, "sha256": {"SOFTWARE_ONLY": "a" * 64}},
            "a" * 64,
        ),
    )
    monkeypatch.setattr(protocol, "require_code_checks", lambda *a: {})
    monkeypatch.setattr(
        profile, "runtime_environment", lambda: config["prefix_runtime"]
    )

    def fail(root: Path) -> Any:
        raise TimeoutError("EXPLICIT_TEST_INPUT_FAILURE")

    monkeypatch.setattr(inputs, "prerequisites", fail)
    path = tmp_path / "profile.json"
    with pytest.raises(TimeoutError):
        profile.run(tmp_path, path)
    saved = json.loads(path.read_text())
    assert saved["status"] == "incomplete"
    assert saved["failure"]["reason"] == "EXPLICIT_TEST_INPUT_FAILURE"
    assert saved["batch"] == {}
    assert saved["rows"] == []
    original = path.read_bytes()
    with pytest.raises(FileExistsError):
        profile.run(tmp_path, path)
    assert original == path.read_bytes()
