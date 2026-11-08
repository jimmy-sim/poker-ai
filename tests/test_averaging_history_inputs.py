"""Frozen selection and historical-cost gates, with explicit synthetic timings."""

import copy
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

from poker_ai.evaluation.averaging_history_inputs import (
    HistoryInputs,
    forecast,
    inputs,
    load,
    validate_config,
)
from poker_ai.evaluation.controlled_reply_inputs import Inputs

ROOT = Path(__file__).resolve().parents[1]


def fictional_timings(scale: float = 1.0) -> HistoryInputs:
    """EXPLICIT synthetic seconds/index identities, not research timings."""
    events = [
        dict(phase="trained", index=i, seconds=(i + 1) * scale) for i in range(64)
    ]
    base = SimpleNamespace(
        original=dict(batch=dict(workers=[dict(messages=events)])),
        policies=tuple(
            SimpleNamespace(identifier=f"toy-{i}", row=dict(index=i)) for i in range(64)
        ),
    )
    return HistoryInputs(inputs(ROOT), cast(Inputs, base), {}, {})


def test_exact_64_case_forecast_uses_all_cells_and_the_fixed_formula() -> None:
    result = forecast(fictional_timings())
    assert result["partition_original_seconds"] == [715.0, 672.0, 693.0]
    assert result["guarded_own_seconds"] == 4060.0
    assert result["decision"] == "fits_requires_checked_admission"
    assert len(result["historical_cell_rows"]) == 64
    assert result["new_postflop_training_performed"] is False
    assert [r["index"] for r in result["historical_cell_rows"]] == list(range(64))
    assert (
        forecast(fictional_timings(3))["decision"] == "exceeds_cap_stop_before_replay"
    )


@pytest.mark.parametrize(
    "mode", ["missing", "duplicate", "zero", "negative", "nan", "boolean", "index"]
)
def test_forecast_rejects_missing_or_invalid_historical_rows(mode: str) -> None:
    data = fictional_timings()
    events = data.base.original["batch"]["workers"][0]["messages"]
    if mode == "missing":
        events.pop()
    elif mode == "duplicate":
        events.append(dict(events[0]))
    elif mode == "index":
        events[0]["index"] = False
    else:
        events[0]["seconds"] = dict(
            zero=0.0, negative=-1.0, nan=float("nan"), boolean=True
        )[mode]
    with pytest.raises(ArithmeticError):
        forecast(data)


@pytest.mark.parametrize(
    "key,value",
    [
        ("expected_cells", 63),
        ("seeds", [20261301]),
        ("source_target", 100000000),
        ("current_work_labels", [10000000]),
        ("suffix_windows", [[0, 10000000]]),
        ("regret_weight", "uniform"),
        ("bridge", "cold_target_history_mass"),
        ("worker_count", 2),
        ("maximum_own_seconds", 7200.0),
        ("expected_fixed_opponent_target_conditions", 512),
        ("tolerance_unitless", 1e-9),
    ],
)
def test_changed_selection_windows_or_budgets_are_not_admitted(
    key: str, value: Any
) -> None:
    config = copy.deepcopy(inputs(ROOT))
    config[key] = value
    with pytest.raises(ArithmeticError):
        validate_config(config)


@pytest.mark.parametrize(
    "section,key",
    [
        ("forecast", "guard_multiplier"),
        ("forecast", "fixed_overhead_allowance_seconds"),
        ("forecast", "observation_allowance_multiplier"),
        ("native_reference", "license_sha256"),
        ("native_reference", "version"),
        ("prefix_runtime", "python"),
        ("prefix_runtime", "numpy"),
    ],
)
def test_changed_forecast_reference_or_prefix_runtime_fails(
    section: str, key: str
) -> None:
    config = copy.deepcopy(inputs(ROOT))
    config[section][key] = "changed"
    with pytest.raises(ArithmeticError):
        validate_config(config)


@pytest.mark.slow
def test_all_original_prefixes_and_frozen_replies_load_without_any_learning(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from poker_ai.postflop.controlled_training import ControlledTrainer
    from poker_ai.solver_validation.reference import Reference

    def forbidden(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("no new poker training or native constructor in loader")

    monkeypatch.setattr(ControlledTrainer, "step", forbidden)
    monkeypatch.setattr(ControlledTrainer, "initialize_exact", forbidden)
    monkeypatch.setattr(Reference, "__init__", forbidden)
    data = load(ROOT)
    assert len(data.base.policies) == 64
    assert len(data.prefixes) == 192
    assert len(data.replies) == 128
