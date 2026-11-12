"""Check the actual complete saved-data diagnosis and all reported controls."""

import csv
import json
from contextlib import ExitStack
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from poker_ai.evaluation.opponent_decision_run import BLOCKED, forbidden
from poker_ai.evaluation.range_blocker_io import FLAGS, FOLDER, Cache, load
from poker_ai.evaluation.range_blocker_probe import CONTROLS
from poker_ai.postflop.river_study import digest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def publication() -> Cache:
    folder = ROOT / FOLDER
    before = {p.name: digest(p) for p in folder.iterdir() if p.is_file()}
    with ExitStack() as stack:
        for name in BLOCKED:
            stack.enter_context(patch(name, forbidden))
        cache = load(ROOT, folder)
        for profile in cache.profiles:
            cache.detail(profile)
    assert before == {p.name: digest(p) for p in folder.iterdir() if p.is_file()}
    return cache


def test_complete_actual_two_sided_publication(publication: Cache) -> None:
    m = publication.manifest
    assert len(publication.profiles) == len(publication.decoded) == 24
    assert m["responses"] == 48 and m["suffix_conditions"] == 96
    assert m["range_panels"] == 192 and m["group_panels"] == 960
    row_count = sum(
        len(r["river_info_ids"]) for p in publication.profiles for r in p["responses"]
    )
    assert row_count == m["profile_river_rows"] == 44160
    assert 2 * row_count == m["suffix_river_rows"] == 88320
    assert 0 <= m["seconds"] <= m["maximum_seconds"] == 900
    assert m["maximum_source_chip_error"] <= 1e-9
    assert m["maximum_unitless_error"] <= 1e-12
    assert m["constructors_blocked"] is True
    assert all(m[k] is False for k in FLAGS)
    # Input-specific redundancy: no hypothetical cross-seat hands share a card.
    # Old actual-own compatibility therefore already gives the opponent's PUBLIC
    # mask. The separate UNIT overlap fixture tests the general nonredundant case.
    for sides in publication.book.ranges.values():
        assert all(
            set(left).isdisjoint(right) for left in sides[0] for right in sides[1]
        )
    for p in publication.profiles:
        new, source = publication.decoded[p["source_id"]]
        for target in (0, 1):
            rows = source["responses"][target]["suffixes"][0]["rows"]
            expected = {r["exact_info"] for r in rows}
            geometry = new["responses"][target]["partitions"]
            for partition in geometry:
                infos = [i for g in partition["groups"] for i in g["infos"]]
                assert len(infos) == len(set(infos)) == len(expected)
                assert set(infos) == expected
            assert {tuple(g["infos"]) for g in geometry[2]["groups"]} == {
                tuple(g["infos"]) for g in geometry[3]["groups"]
            }
            assert {tuple(g["infos"]) for g in geometry[1]["groups"]} == {
                tuple(g["infos"]) for g in geometry[2]["groups"]
            }


def test_complete_report_matches_all_actual_control_panels(publication: Cache) -> None:
    folder = ROOT / "results/two-sided-report"
    receipt = json.loads((folder / "receipt.json").read_text())
    assert receipt["input_manifest_sha256"] == digest(ROOT / FOLDER / "manifest.json")
    assert receipt["scientific_source_sha256"] == publication.manifest["source_sha256"]
    assert receipt["analysis_record_sha256"] == digest(
        ROOT / "results/two-sided-blockers-checks/complete/render_report.py.txt"
    )
    assert set(receipt["outputs"]) == {
        "effects.csv",
        "tables.md",
        "examples.json",
        "dev_low_oop.png",
        "dev_medium_oop.png",
    }
    assert all(receipt[k] is False for k in FLAGS)
    assert receipt["cached_inputs_unchanged"] is True
    for path, checksum in receipt["outputs"].items():
        assert digest(folder / path) == checksum
    with (ROOT / FOLDER / "panels.csv").open() as stream:
        raw = list(csv.DictReader(stream))
    fields = ("game", "seed", "arm", "target", "suffix", "range_weights")
    originals = {tuple(r[k] for k in (*fields, "group_control")): r for r in raw}
    with (folder / "effects.csv").open() as stream:
        effects = list(csv.DictReader(stream))
    assert len(raw) == len(originals) == 960
    assert len(effects) == len({tuple(r[k] for k in fields) for r in effects}) == 192
    numeric: list[dict[str, Any]] = []
    for e in effects:
        key = tuple(e[k] for k in fields)
        costs = {}
        for c in CONTROLS:
            r = originals[(*key, c)]
            costs[c] = float(r["local_sharing_cost_chips_per_weighted_decision"])
            assert float(e[c + "_cost"]) == costs[c]
            for short, full in (
                ("conflicts", "strict_conflicting_groups"),
                ("groups", "total_groups"),
                ("supported", "supported_groups"),
                ("resolved", "source_conflicting_groups_resolved"),
            ):
                assert int(e[c + "_" + short]) == int(r[full])
        assert costs["both_public"] == pytest.approx(
            costs["both_public_joint"], abs=1e-9, rel=0
        )
        assert costs["exact_information"] == 0
        expected = dict(
            own_public_reduction=costs["source_static"] - costs["own_public"],
            additional_both_public_reduction=costs["own_public"] - costs["both_public"],
            total_public_reduction=costs["source_static"] - costs["both_public"],
        )
        for name, value in expected.items():
            assert float(e[name]) == value
            assert value >= -1e-9
        assert float(e["supported_uniform_weight"]) == float(
            originals[(*key, CONTROLS[0])]["supported_uniform_decision_weight"]
        )
        numeric.append(expected | dict(residual=costs["both_public"]))
    for field, metric in (
        ("own_public_reduction", "own_public_cost_decreases"),
        ("additional_both_public_reduction", "additional_both_public_cost_decreases"),
        ("total_public_reduction", "total_public_cost_decreases"),
        ("residual", "public_residual_positive_panels"),
    ):
        assert sum(e[field] > 1e-9 for e in numeric) == receipt[metric]
