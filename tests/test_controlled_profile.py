"""Profiling workload/receipts with explicit synthetic timings, not benchmarks."""

import copy
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from poker_ai.postflop import controlled_profile as profile
from poker_ai.postflop.river_study import Deadline, digest
from poker_ai.postflop.training_isolation import sentinel_tree
from poker_ai.validation.five_card import source_provenance

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def config() -> dict[str, Any]:
    result: dict[str, Any] = json.loads((ROOT / profile.CONFIG).read_text())
    return result


@pytest.fixture
def workload(config: dict[str, Any]) -> list[dict[str, Any]]:
    protocol = profile.load_inputs(ROOT, config)
    return profile.cells(protocol["future_comparison"])


def test_all_cells_seeds_and_bridge_endpoint_deduplication(
    workload: list[dict[str, Any]],
) -> None:
    assert len(workload) == len({profile.identity(c) for c in workload}) == 140
    assert sum(c["traversal"] == "external" for c in workload) == 96
    assert sum(c["bridge"] != "common" for c in workload) == 12
    assert (
        sum(c["bridge"] == "common" and c["traversal"] == "full" for c in workload)
        == 32
    )
    assert {c["seed"] for c in workload if c["traversal"] == "external"} == {
        20261301,
        20261302,
        20261303,
    }


@pytest.fixture
def timing_rows(
    config: dict[str, Any], workload: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    rows = []
    for cell in workload:
        steps = config[f"{cell['traversal']}_iterations_after_initialization"]
        warm = cell["bridge"] != "cold_target_history_mass"
        initial = 20 if warm else 0
        visits = (20 if cell["traversal"] == "full" else 8) * steps
        for repeat in range(3):
            rows.append(
                {
                    **cell,
                    "repeat": repeat,
                    "iterations": steps + int(warm),
                    "initialization_visits": initial,
                    "incremental_visits": visits,
                    "total_visits": initial + visits,
                    "initialization_seconds": 0.1,
                    "incremental_seconds": 1.0,
                    "state_sha256": "a" * 64,
                    "tree_nodes": 10,
                    "information_sets": 2,
                    "width": 2,
                }
            )
    return rows


def test_forecast_maximum_not_minimum_guard_and_gate(
    workload: list[dict[str, Any]],
) -> None:
    base = {
        **workload[0],
        "initialization_visits": 20,
        "incremental_visits": 10,
        "initialization_seconds": 1.0,
        "incremental_seconds": 2.0,
    }
    slower_setup = {**base, "initialization_seconds": 3.0, "incremental_seconds": 1.0}
    other = {
        **base,
        "seed": 20261302,
        "initialization_visits": 0,
        "incremental_visits": 25,
        "initialization_seconds": 0.5,
        "incremental_seconds": 1.0,
    }
    blocked = profile.forecast([base, slower_setup, other], 100, 2.0, 40)
    assert blocked["training_only_forecast_seconds"] == 21.5
    assert blocked["guarded_training_seconds"] == 43.0
    assert blocked["decision"] == "training_only_guarded_forecast_exceeds_cap"
    unresolved = profile.forecast([base, slower_setup, other], 100, 2.0, 50)
    assert unresolved["decision"] == "unresolved_unmeasured_pipeline_cost"
    assert unresolved["strength_comparison_performed"] is False


@pytest.mark.parametrize(
    "change",
    [
        "missing",
        "duplicate",
        "typed_seed",
        "typed_repeat",
        "work",
        "trajectory",
        "time",
        "score",
    ],
)
def test_reject_changed_profile_grid_and_trajectory(
    timing_rows: list[dict[str, Any]],
    workload: list[dict[str, Any]],
    config: dict[str, Any],
    change: str,
) -> None:
    profile.validate_rows(timing_rows, workload, config)
    if change == "missing":
        timing_rows.pop()
    elif change == "duplicate":
        timing_rows[-1] = timing_rows[0]
    elif change == "typed_seed":
        row = next(r for r in timing_rows if r["seed"] is not None)
        row["seed"] = float(row["seed"])
    elif change == "typed_repeat":
        timing_rows[0]["repeat"] = False
    elif change == "work":
        timing_rows[0]["incremental_visits"] += 1
    elif change == "trajectory":
        timing_rows[0]["state_sha256"] = "b" * 64
    elif change == "time":
        timing_rows[0]["incremental_seconds"] = 0
    else:
        timing_rows[0]["exploitability_chips"] = 0
    with pytest.raises(ArithmeticError):
        profile.validate_rows(timing_rows, workload, config)


def test_measured_toy_repeats_and_profile_instrumentation_match(
    workload: list[dict[str, Any]],
) -> None:
    import cProfile

    tree = sentinel_tree()
    for traversal in ("full", "external"):
        cell = next(
            c
            for c in workload
            if c["traversal"] == traversal and c["bridge"] == "common"
        )
        first = profile.measure(tree, cell, 8, Deadline(10))
        instrument = cProfile.Profile()
        second = profile.measure(tree, cell, 8, Deadline(10), instrument)
        assert all(first[k] == second[k] for k in profile.STABLE)
        assert first["initialization_visits"] == 2 * len(tree.player)
        assert first["incremental_seconds"] > 0
        assert len(profile.hotspots(instrument, ROOT, 25)) == 25
    with pytest.raises(TimeoutError):
        expired = Deadline(1)
        expired.started -= 2
        profile.measure(tree, cell, 8, expired)


def test_pinned_legacy_cli_bridge_and_source_tampering(
    config: dict[str, Any],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = ROOT / config["baseline_receipt"]
    assert profile.replay_correctness(ROOT, path)["status"] == "passed_correctness_only"
    before = path.read_bytes()
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/check_training_isolation.py"),
            "--replay",
            str(path),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    assert "4 exact selector checks, 30 historical work rows" in result.stdout
    assert path.read_bytes() == before
    corrupt = json.loads(before)
    corrupt["historical_work"][0]["full_node_work"] += 1
    changed = tmp_path / "changed.json"
    changed.write_text(json.dumps(corrupt))
    with pytest.raises(ArithmeticError):
        profile.replay_correctness(ROOT, changed)
    real = digest

    def changed_source(p: Path) -> str:
        return "0" * 64 if str(p).endswith("controlled_training.py") else real(p)

    monkeypatch.setattr(profile, "digest", changed_source)
    with pytest.raises(ArithmeticError, match="compatibility source"):
        profile.replay_correctness(ROOT, path)


def test_complete_synthetic_receipt_report_and_partial_rejection(
    config: dict[str, Any],
    timing_rows: list[dict[str, Any]],
    tmp_path: Path,
) -> None:
    source = source_provenance(
        ROOT, ROOT / profile.CONFIG, entrypoints=(profile.ENTRYPOINT,)
    )
    source["dirty"] = False  # Explicit synthetic software receipt, never published.
    profiles = []
    for cell in config["profiler_cases"]:
        row = copy.deepcopy(
            next(
                r for r in timing_rows if profile.identity(r) == profile.identity(cell)
            )
        )
        row.pop("repeat")
        row["hotspots"] = [
            dict(
                file="software-fixture.py",
                line=i,
                function="fixture",
                calls=1,
                primitive_calls=1,
                self_seconds=0.0,
                cumulative_seconds=0.01,
            )
            for i in range(25)
        ]
        profiles.append(row)
    saved: dict[str, Any] = {
        "format": profile.FORMAT,
        "status": "completed",
        "failure": None,
        "source": source,
        "config": config,
        "rows": timing_rows,
        "profiles": profiles,
        "seconds": 500.0,
        "setup_seconds": 0.1,
        "strength_comparison_performed": False,
    }
    output = tmp_path / "synthetic.json"
    output.write_text(json.dumps(saved))
    _, summary = profile.report(ROOT, output)
    assert len(summary["cells"]) == 140
    assert "no strength comparison" in profile.tables(summary)
    for change in (
        "status",
        "source",
        "profile",
        "instrumentation",
        "wall_time",
        "claim",
    ):
        altered = copy.deepcopy(saved)
        if change == "status":
            altered["status"] = "incomplete"
        elif change == "source":
            altered["source"]["sha256"] = {}
        elif change == "profile":
            altered["profiles"].pop()
        elif change == "instrumentation":
            altered["profiles"][0]["state_sha256"] = "c" * 64
        elif change == "wall_time":
            altered["seconds"] = 1.0
        else:
            altered["strength_comparison_performed"] = True
        output.write_text(json.dumps(altered))
        with pytest.raises(ArithmeticError):
            profile.report(ROOT, output)
