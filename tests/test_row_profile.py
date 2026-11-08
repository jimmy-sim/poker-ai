"""Synthetic paired timing receipts; no measured benchmark outcomes in CI."""

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from poker_ai.postflop import controlled_profile as old
from poker_ai.postflop import row_profile as study
from poker_ai.validation.five_card import source_provenance

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def receipt() -> tuple[dict[str, Any], dict[str, Any]]:
    config = json.loads((ROOT / study.CONFIG).read_text())
    previous, protocol = study.inputs(ROOT, config)
    workload = old.cells(protocol["future_comparison"])
    result: dict[str, Any] = dict(
        format=study.FORMAT,
        status="completed",
        failure=None,
        config=config,
        strength_comparison_performed=False,
        seconds=1000.0,
        parity=[],
        timings={"dense": [], "rows": []},
        profiles=[],
        pair_orders=[],
        cache_diagnostics=[],
    )
    source = source_provenance(ROOT, ROOT / study.CONFIG, entrypoints=(study.ENTRY,))
    source["dirty"] = False  # Explicit synthetic fixture, never published.
    result["source"] = source
    external = [c for c in workload if c["traversal"] == "external"]
    for cell in workload:
        ext = cell["traversal"] == "external"
        steps = 1000 if ext else 16
        warm = cell["bridge"] != "cold_target_history_mass"
        initial = 20 if warm else 0
        increment = steps * (8 if ext else 20)
        for repeat in range(3):
            base = {
                **cell,
                "repeat": repeat,
                "iterations": steps + int(warm),
                "initialization_visits": initial,
                "incremental_visits": increment,
                "total_visits": initial + increment,
                "initialization_seconds": 0.1,
                "incremental_seconds": 1.0,
                "state_sha256": "a" * 64,
                "tree_nodes": 10,
                "information_sets": 2,
                "width": 2,
            }
            result["timings"]["dense"].append(base)
            if ext:
                result["timings"]["rows"].append({**base, "incremental_seconds": 0.5})
                i = external.index(cell)
                result["pair_orders"].append(
                    {
                        **cell,
                        "repeat": repeat,
                        "order": ["dense", "rows"]
                        if (i + repeat) % 2 == 0
                        else ["rows", "dense"],
                    }
                )
                result["cache_diagnostics"].append(
                    {
                        **cell,
                        "repeat": repeat,
                        "row_evaluations": 1000,
                        "last_pass_rows": [1, 1],
                    }
                )
        if ext:
            result["parity"].extend(
                {
                    **cell,
                    "iteration": t,
                    "total_visits": 20 + (t - 1) * 8,
                    "state_sha256": "a" * 64,
                }
                for t in study.PARITY
            )
    for cell in previous["profiler_cases"]:
        for engine in (
            ["dense", "rows"] if cell["traversal"] == "external" else ["dense"]
        ):
            row = copy.deepcopy(
                next(
                    r
                    for r in result["timings"][engine]
                    if old.identity(r) == old.identity(cell)
                )
            )
            row.pop("repeat")
            result["profiles"].append(
                {
                    **row,
                    "engine": engine,
                    "hotspots": [
                        dict(
                            file="fixture.py",
                            line=i,
                            function="fixture",
                            calls=1,
                            primitive_calls=1,
                            self_seconds=0.0,
                            cumulative_seconds=0.01,
                        )
                        for i in range(25)
                    ],
                }
            )
    return result, protocol


def test_full_grid_shared_full_cells_and_pair_order_balance(
    receipt: tuple[dict[str, Any], dict[str, Any]],
    tmp_path: Path,
) -> None:
    saved, protocol = receipt
    study.validate(saved, protocol)
    assert len(saved["parity"]) == 576
    assert [len(saved["timings"][k]) for k in ("dense", "rows")] == [420, 288]
    assert sum(o["order"][0] == "dense" for o in saved["pair_orders"]) == 144
    path = tmp_path / "synthetic.json"
    path.write_text(json.dumps(saved))
    _, summary = study.report(ROOT, path)
    assert summary["median_paired_ratio"] == 2.0
    assert all(len(f["cells"]) == 140 for f in summary["forecasts"].values())
    assert "No learning sweep" in study.tables(summary)
    a, b = summary["forecasts"]["dense"]["cells"], summary["forecasts"]["rows"]["cells"]
    assert [r for r in a if r["traversal"] == "full"] == [
        r for r in b if r["traversal"] == "full"
    ]


@pytest.mark.parametrize(
    "change", ["parity", "state", "order", "repeat", "work", "cache", "profile"]
)
def test_reject_partial_or_changed_parity_and_timing(
    receipt: tuple[dict[str, Any], dict[str, Any]],
    change: str,
) -> None:
    saved, protocol = receipt
    if change == "parity":
        saved["parity"].pop()
    elif change == "state":
        saved["timings"]["rows"][0]["state_sha256"] = "b" * 64
    elif change == "order":
        saved["pair_orders"][0]["order"].reverse()
    elif change == "repeat":
        saved["timings"]["rows"][0]["repeat"] = False
    elif change == "work":
        saved["timings"]["rows"][0]["incremental_visits"] += 1
    elif change == "cache":
        saved["cache_diagnostics"].pop()
    else:
        saved["profiles"].pop()
    with pytest.raises(ArithmeticError):
        study.validate(saved, protocol)


def test_report_rejects_source_scope_or_total_time_tampering(
    receipt: tuple[dict[str, Any], dict[str, Any]],
    tmp_path: Path,
) -> None:
    saved, _ = receipt
    for change in ("source", "status", "scope", "time"):
        copy_saved = copy.deepcopy(saved)
        if change == "source":
            copy_saved["source"]["sha256"] = {}
        elif change == "status":
            copy_saved["status"] = "incomplete"
        elif change == "scope":
            copy_saved["strength_comparison_performed"] = True
        else:
            copy_saved["seconds"] = 0
        path = tmp_path / "invalid.json"
        path.write_text(json.dumps(copy_saved))
        with pytest.raises(ArithmeticError):
            study.report(ROOT, path)
