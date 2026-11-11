"""Fixed forecast arithmetic and fail-closed permits; no study is admitted."""

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from poker_ai.evaluation import opponent_learning_admission as gates
from poker_ai.evaluation.opponent_learning_design import COST
from poker_ai.postflop.cell_process import partition
from poker_ai.postflop.river_study import digest

ROOT = Path(__file__).resolve().parents[1]


def original() -> dict[str, Any]:
    saved: dict[str, Any] = json.loads(
        (ROOT / "results/reduced-batch-study/own.json").read_text()
    )
    return saved


def test_conservative_training_cost_uses_all24_and_no_half_discount() -> None:
    forecast = gates.training_forecast(original())
    rows = forecast["original_complete_paths"]
    assert len(rows) == 24
    assert {r["index"] for r in rows} == set(range(24, 48))
    games = sorted({r["case"]["spot_file"] for r in rows})
    maxima = [
        max(r["seconds"] for r in rows if r["case"]["spot_file"] == g) for g in games
    ]
    expected = [maxima[i // 15] for i in range(30)]
    assert forecast["path_seconds"] == expected
    assert forecast["assignments"] == partition(30, 3)
    assert forecast["T"] == max(
        sum(expected[i] for i in group) for group in partition(30, 3)
    )
    assert forecast["half_budget_discount_applied"] is False


@pytest.mark.parametrize("change", ["missing", "duplicate", "setup", "work", "nan"])
def test_original_timing_inventory_and_complete_work_cannot_be_edited(
    change: str,
) -> None:
    data = original()
    messages = next(
        w["messages"]
        for b in data["batches"]
        for w in b["workers"]
        if any(
            r.get("phase") == "trained" and r.get("index") == 24 for r in w["messages"]
        )
    )
    row = next(
        r for r in messages if r.get("phase") == "trained" and r.get("index") == 24
    )
    if change == "missing":
        messages.remove(row)
    elif change == "duplicate":
        messages.append(copy.deepcopy(row))
    elif change == "setup":
        row["initialization_seconds"] = row["seconds"] + 1
    elif change == "work":
        row["work"] = 9_999_999
    else:
        row["seconds"] = float("nan")
    with pytest.raises(ArithmeticError):
        gates.training_forecast(data)


def costs(seconds: list[float]) -> list[dict[str, Any]]:
    # Synthetic timing numbers only, never persisted as actual measurements.
    return [
        dict(scope=COST, repetition=i, complete_command=dict(seconds=v))
        for i, v in enumerate(seconds)
    ]


def test_fixed_forecast_uses_complete_maxima_and_strict_inequalities() -> None:
    result = gates.forecast(
        {"T": 100}, costs([10.0, 30.0, 20.0]), costs([15.0, 17.0, 11.0])
    )
    assert (result["T"], result["D"], result["N"]) == (100, 30, 17)
    assert result["guarded_own_seconds"] == 2 * (2 * 100 + 30 + 600)
    assert result["guarded_native_seconds"] == 2 * (17 + 60)
    assert result["strict_own_pass"] is result["strict_native_pass"] is True
    boundary = gates.forecast({"T": 1400}, costs([200.0] * 3), costs([390.0] * 3))
    assert boundary["guarded_own_seconds"] == 7200
    assert boundary["guarded_native_seconds"] == 900
    assert boundary["strict_own_pass"] is boundary["strict_native_pass"] is False
    assert result["long_run_admitted"] is False


@pytest.mark.parametrize("change", ["missing", "duplicate", "bool", "scope", "nan"])
def test_forecast_never_uses_a_favorable_subset_or_wrong_scope(change: str) -> None:
    own, native = costs([1.0, 2.0, 3.0]), costs([4.0, 5.0, 6.0])
    if change == "missing":
        own.pop()
    elif change == "duplicate":
        native[2]["repetition"] = 1
    elif change == "bool":
        own[0]["repetition"] = False
    elif change == "scope":
        own[0]["scope"] = "real"
    else:
        native[0]["complete_command"]["seconds"] = float("nan")
    with pytest.raises(ArithmeticError):
        gates.forecast({"T": 100}, own, native)


def test_missing_published_permit_blocks_real_work(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        gates.require_admission(tmp_path, "a" * 64)


@pytest.mark.parametrize(
    "change",
    ["none", "status", "source", "gate", "arithmetic", "missing_repetition", "input"],
)
def test_permit_schema_needs_complete_published_forecast_and_unchanged_inputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    change: str,
) -> None:
    # Entirely synthetic gate fixture. No actual CI, solver, timing or permit.
    folder = tmp_path / "results/opponent-information"
    folder.mkdir(parents=True)
    checks = folder / "code-checks.json"
    checks.write_text("unit check placeholder")
    data = tmp_path / "old-own-fixture.txt"
    data.write_text("unit-only source bytes")
    f = gates.forecast({"T": 100}, costs([10.0, 20.0, 30.0]), costs([40.0, 50.0, 60.0]))
    hashes = {"old-own-fixture.txt": digest(data)}
    saved: dict[str, Any] = dict(
        status="complete_fixed_cost_forecast",
        failure=None,
        source_sha256="UNIT_ONLY_NOT_A_CHECKED_SOURCE",
        forecast=copy.deepcopy(f),
        verified_input_sha256=dict(hashes),
    )
    monkeypatch.setattr(
        gates,
        "require_checks",
        lambda r: dict(
            source_sha256="UNIT_ONLY_NOT_A_CHECKED_SOURCE",
            ci=dict(checked_commit="UNIT_ONLY_NOT_A_COMMIT", run_id=1),
        ),
    )
    monkeypatch.setattr(gates, "published", lambda *a: None)
    monkeypatch.setattr(gates, "committed", lambda *a: None)
    monkeypatch.setattr(gates, "measurement", lambda *a: {"unit_only": True})
    monkeypatch.setattr(gates, "sealed_costs", lambda r: (f, hashes))
    if change == "status":
        saved["status"] = "partial"
    elif change == "source":
        saved["source_sha256"] = "wrong"
    elif change == "gate":
        saved["forecast"]["strict_native_pass"] = False
    elif change == "arithmetic":
        saved["forecast"]["guarded_own_seconds"] -= 1
    elif change == "missing_repetition":
        saved["forecast"]["own_repetition_seconds"].pop()
    elif change == "input":
        data.write_text("changed input bytes")
    (folder / "forecast.json").write_text(json.dumps(saved))
    if change == "none":
        permit = gates.permit(tmp_path, saved)
        assert permit["status"] == "own_opponent_learning_admitted"
        assert permit["maximum_own_seconds"] == 7200
        assert permit["maximum_native_seconds"] == 900
        assert permit["new_agent_default"] is permit["fresh_global_admission"] is False
    else:
        with pytest.raises(ArithmeticError):
            gates.permit(tmp_path, saved)
