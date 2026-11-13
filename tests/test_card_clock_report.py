"""Resource reports preserve units, producer scope and raw versus derived data."""

import copy
import importlib
import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
report = importlib.import_module("report_card_clock_trace")
resources = importlib.import_module("card_clock_support")


def saved() -> dict[str, Any]:
    return dict(
        config_sha256=report.CONFIG_SHA,
        source=dict(fingerprint=report.SOURCE),
        scope="RESOURCE_DIAGNOSTIC_COMPLETE_SAVED_AUDIT_NOT_PERFORMANCE_ADMISSION",
        status="complete_card_clock_trace",
        admission_evidence=False,
    )


def test_complete_measured_source() -> None:
    report.measured(saved())


@pytest.mark.parametrize(
    "key,value",
    [
        ("config_sha256", "other"),
        ("source", dict(fingerprint="other")),
        ("scope", "timing pass"),
        ("status", "partial"),
        ("admission_evidence", True),
    ],
)
def test_wrong_or_partial_scope_rejected(key: str, value: Any) -> None:
    row = saved()
    row[key] = value
    with pytest.raises(ArithmeticError, match="resource diagnostic"):
        report.measured(row)


def test_export_keeps_cpu_separate_and_peak_out_of_deltas() -> None:
    a = resources.snapshot()
    b = copy.deepcopy(a)
    b["perf_seconds"] += 1
    b["process_cpu_seconds"] += 2
    b["self_usage"]["ru_maxrss"] += 123
    clock, counters, peaks = report.exports(
        "uncached", "fixture", resources.record(a, b)
    )
    assert clock["perf_seconds"] == 1 and clock["process_cpu_seconds"] == 2
    assert all(
        row["counter"] != "ru_maxrss" and row["zero_does_not_prove_absence"] is True
        for row in counters
    )
    assert len(peaks) == 2 and all(
        row["cumulative_peak_not_interval_allocation"] is True for row in peaks
    )
    assert peaks[0]["rss_unit"] == a["rss_unit"]


def test_export_rechecks_derived_counters() -> None:
    row = resources.record(resources.snapshot(), resources.snapshot())
    row["interval"]["resources"]["self_usage"]["delta"]["ru_minflt"] += 1
    with pytest.raises(ArithmeticError):
        report.exports("cached", "fixture", row)
