"""Check the actual committed local diagnostic and every reported comparison."""

import csv
import json
from pathlib import Path
from typing import Any

import pytest

from poker_ai.evaluation.river_range_io import FOLDER, load, load_detail
from poker_ai.postflop.river_study import digest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def publication() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    folder = ROOT / FOLDER
    manifest: dict[str, Any] = json.loads((folder / "manifest.json").read_text())
    profiles = load(ROOT, folder)
    details = [load_detail(folder, p) for p in profiles]
    return manifest, details


def test_complete_actual_local_range_cache(
    publication: tuple[dict[str, Any], list[dict[str, Any]]],
) -> None:
    manifest, details = publication
    assert len(details) == 24
    assert sum(len(p["responses"]) for p in details) == 48
    suffixes = [s for p in details for r in p["responses"] for s in r["suffixes"]]
    assert len(suffixes) == 96
    assert sum(len(s["rows"]) for s in suffixes) == manifest["suffix_river_rows"]
    assert manifest["suffix_river_rows"] == 2 * manifest["profile_river_rows"]
    assert manifest["local_panels"] == 192
    assert manifest["group_control_csv_rows"] == 384
    assert manifest["seconds"] <= manifest["maximum_seconds"] == 900
    assert manifest["maximum_source_chip_error"] <= 1e-9
    assert manifest["maximum_unitless_error"] <= 1e-12
    assert manifest["constructors_blocked"] is True
    for name in (
        "training_performed",
        "reference_constructed",
        "new_independent_audit",
        "feature_deployed",
        "new_agent_default",
        "fresh_global_admission",
    ):
        assert manifest[name] is False


def test_every_reported_pair_and_plot_matches_the_complete_publication(
    publication: tuple[dict[str, Any], list[dict[str, Any]]],
) -> None:
    folder = ROOT / "results/river-range-report"
    receipt = json.loads((folder / "receipt.json").read_text())
    assert receipt["input_manifest_sha256"] == digest(ROOT / FOLDER / "manifest.json")
    assert receipt["scientific_source_sha256"] == publication[0]["source_sha256"]
    assert receipt["analysis_record_sha256"] == digest(
        ROOT / "results/river-range-checks/complete/render_report.py.txt"
    )
    assert set(receipt["outputs"]) == {
        "effects.csv",
        "tables.md",
        "examples.json",
        "dev_low_oop.png",
        "dev_medium_oop.png",
    }
    for path, checksum in receipt["outputs"].items():
        assert digest(folder / path) == checksum
    fields = ("game", "seed", "arm", "target", "suffix", "group_control")
    with (ROOT / FOLDER / "panels.csv").open() as stream:
        rows = list(csv.DictReader(stream))
    originals = {tuple(r[k] for k in (*fields, "range_weights")): r for r in rows}
    with (folder / "effects.csv").open() as stream:
        pairs = list(csv.DictReader(stream))
    assert len(rows) == len(originals) == 384
    assert len(pairs) == len({tuple(r[k] for k in fields) for r in pairs}) == 192
    for row in pairs:
        key = tuple(row[k] for k in fields)
        actual = originals[(*key, "actual_posterior")]
        prior = originals[(*key, "compatible_prior")]
        a = float(actual["local_sharing_cost_chips_per_weighted_decision"])
        p = float(prior["local_sharing_cost_chips_per_weighted_decision"])
        assert float(row["actual_cost"]) == a
        assert float(row["prior_cost"]) == p
        assert float(row["actual_minus_prior"]) == a - p
        assert row["total_groups"] == actual["total_groups"] == prior["total_groups"]
        assert row["actual_conflicts"] == actual["strict_conflicting_groups"]
        assert row["prior_conflicts"] == prior["strict_conflicting_groups"]
    differences = [float(r["actual_minus_prior"]) for r in pairs]
    assert sum(d > 1e-9 for d in differences) == receipt["positive_deltas"]
    assert sum(d < -1e-9 for d in differences) == receipt["negative_deltas"]
    assert sum(abs(d) <= 1e-9 for d in differences) == receipt["unchanged_within_1e9"]
