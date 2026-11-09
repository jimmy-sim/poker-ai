"""Prospective pins and old archived source loading; no new intervention scores."""

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from poker_ai.evaluation import window_fallback_inputs as source
from poker_ai.postflop.controlled_training import ControlledTrainer
from poker_ai.postflop.river_study import Deadline

ROOT = Path(__file__).resolve().parents[1]


def test_prospective_config_and_all_seven_input_byte_pins_match() -> None:
    config = source.inputs(ROOT)
    assert len(config["input_sha256"]) == 7
    assert config["expected_self_profiles"] == 512
    assert config["expected_fixed_target_conditions"] == 2048


@pytest.mark.parametrize(
    "key,value",
    [
        ("fill_masks", [[], [0], [1], [1, 0]]),
        ("fill_masks", [[], [False], [1], [0, 1]]),
        ("fill_labels", ["raw", "fill_0", "fill_1"]),
        ("suffix_variants", ["suffix_9m_10m"]),
        ("seeds", [20261301]),
        ("expected_self_profiles", 512.0),
        ("expected_full_windows", 31),
        ("expected_additivity_panels", True),
        ("maximum_own_seconds", 901),
        ("maximum_native_seconds", 901),
        ("tolerance_unitless", 1e-9),
        ("tolerance_chips", 1e-8),
        ("fixed_opponent_fill_labels", ["raw", "fill_0", "fill_both"]),
    ],
)
def test_selection_counts_masks_and_limits_are_fixed(key: str, value: Any) -> None:
    config = json.loads((ROOT / source.CONFIG).read_text())
    config[key] = value
    with pytest.raises(ArithmeticError):
        source.validate_config(config)


@pytest.mark.parametrize("mode", ["pin", "version", "license"])
def test_source_grid_and_reference_are_fixed(mode: str) -> None:
    config = copy.deepcopy(source.inputs(ROOT))
    if mode == "pin":
        config["input_sha256"]["unplanned.json"] = "0" * 64
    elif mode == "version":
        config["native_reference"]["version"] = "changed"
    else:
        config["native_reference"]["license_sha256"] = "0" * 64
    with pytest.raises(ArithmeticError):
        source.validate_config(config)


def test_changed_input_bytes_fail_even_when_schema_is_unchanged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(source, "digest", lambda path: "0" * 64)
    with pytest.raises(ArithmeticError, match="source bytes changed"):
        source.inputs(ROOT)


def forbidden(*args: Any, **kwargs: Any) -> None:
    raise AssertionError(
        "new learning/native construction forbidden in archived loader"
    )


@pytest.mark.slow
def test_every_old_window_loads_with_training_and_native_construction_blocked(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from poker_ai.solver_validation.reference import Reference

    monkeypatch.setattr(ControlledTrainer, "step", forbidden)
    monkeypatch.setattr(ControlledTrainer, "initialize_exact", forbidden)
    monkeypatch.setattr(Reference, "__init__", forbidden)
    data = source.load(ROOT, Deadline(900))
    count = 0
    for window in source.windows(data, Deadline(900)):
        assert window.index == count
        assert window.row["kind"] == "suffix"
        assert window.row["variant"] in data.config["suffix_variants"]
        assert (
            window.policy.tobytes()
            == window.context.partition.normalize(window.mass).tobytes()
        )
        assert not any(
            a.flags.writeable for a in (window.policy, window.mass, window.river)
        )
        count += 1
    assert count == 128
    assert data.replay["maximum_error_chips"] == 0
    assert data.native["self_profiles"] == 512
