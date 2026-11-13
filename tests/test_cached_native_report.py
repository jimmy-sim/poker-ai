"""Elapsed accounting must keep overlapping child CPU separate from wall time."""

import importlib.util
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def tool() -> Any:
    spec = importlib.util.spec_from_file_location(
        "native_report", ROOT / "scripts/report_cached_native.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def reads() -> list[dict[str, Any]]:
    return [
        dict(whole_read_wall_seconds=x, parent_read_cpu_seconds=9999)
        for x in [1.0, 2.0, 3.0]
    ]


def test_elapsed_partition_ignores_overlapping_cpu_and_accounts_every_second(
    tool: Any,
) -> None:
    parts = tool.elapsed_parts(20.0, reads(), 4.0)
    assert sum(parts.values()) == 20.0
    assert parts["other_elapsed"] == 10.0 and parts["reference_worker_batch"] == 4.0
    assert parts["initial_own_read"] == 2.0 and parts["final_own_read"] == 3.0


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -1.0, 0.0, True])
def test_invalid_complete_clock_rejected(tool: Any, bad: Any) -> None:
    with pytest.raises(ArithmeticError, match="finite complete clocks"):
        tool.elapsed_parts(bad, reads(), 4.0)


def test_missing_final_read_and_overlap_rejected(tool: Any) -> None:
    with pytest.raises(ArithmeticError, match="three complete"):
        tool.elapsed_parts(20.0, reads()[:-1], 4.0)
    with pytest.raises(ArithmeticError, match="overlapping"):
        tool.elapsed_parts(5.0, reads(), 4.0)


@pytest.mark.parametrize("damage", ["scope", "config", "source"])
def test_other_instrument_units_cannot_be_relabelled(tool: Any, damage: str) -> None:
    from profile_cached_native_wall import CONFIG_SHA

    child = dict(
        scope="DIAGNOSTIC_COMPLETE_NATIVE_ELAPSED_STACK_PROFILE_NOT_ADMISSION",
        config_sha256=CONFIG_SHA,
        source=dict(
            fingerprint="7fdfe7db600b65c945fb93384e1eb30643474e547492202bf8436f880d2afa5c"
        ),
    )
    tool.metric_identity(child)
    if damage == "scope":
        child["scope"] = "CPU_PROFILE"
    elif damage == "config":
        child["config_sha256"] = "other-instrument"
    else:
        child["source"] = dict(fingerprint="prior-cpu-source")
    with pytest.raises(ArithmeticError, match="source and units"):
        tool.metric_identity(child)
