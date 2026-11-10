"""Published old-policy timing aliases preserve actual source work/iteration/hashes."""

import json
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

from poker_ai.evaluation.matched_update_grid import manifest
from poker_ai.evaluation.matched_update_inputs import Sources, unique
from poker_ai.evaluation.matched_update_timing_corpus import corpus

ROOT = Path(__file__).resolve().parents[1]


def sources() -> Sources:
    old = json.loads((ROOT / "results/reduced-batch-study/own.json").read_text())
    current = json.loads(
        (ROOT / "results/batch-current-diagnosis/own.json").read_text()
    )
    averages = [
        dict(r, weight=r["case"]["average_weight"])
        for r in old["rows"]
        if r["path_index"] < 24
    ]
    # Explicit metadata-only adapter: no context, learning or admission API.
    return cast(
        Sources,
        SimpleNamespace(
            manifest=manifest(ROOT),
            averages=unique(averages, ("path_index", "weight", "work_label")),
            currents=unique(
                [r for r in old["currents"] if r["path_index"] < 24],
                ("path_index", "work_label"),
            ),
            scored_currents=unique(current["rows"], ("id",)),
            fixed=current["fixed_matches"],
        ),
    )


def test_all_old_aliases_keep_actual_final_b1_coordinate_and_source_policy() -> None:
    source = sources()
    original = json.loads(json.dumps(source.manifest))
    grid, right, fixed = corpus(source)
    assert source.manifest == original
    assert len(grid["iteration_targets"]) == 48
    assert len(right) == 144 and len(fixed) == 1152
    assert len({r["id"] for r in right}) == 144
    assert all(r["id"].startswith("OLD-TIMING-RIGHT-") for r in right)
    for target in grid["iteration_targets"]:
        index = target["baseline_path_index"]
        actual = source.averages[index, "linear", 10000000]
        assert target["target_iteration"] == actual["iteration"]
        planned = next(
            t for t in original["iteration_targets"] if t["id"] == target["id"]
        )
        assert target["planned_new_prefix_iteration"] == planned["target_iteration"]
    for row in right:
        index = row["path_index"]
        assert (
            row["total_work"]
            == source.averages[index, "linear", 10000000]["total_work"]
        )
        readout = next(
            p["readout"]
            for p in grid["self_pairs"]
            if p["reused_profile_id"] == row["id"]
        )
        want = (
            source.scored_currents[(source.currents[index, 10000000]["id"],)]
            if readout == "current"
            else source.averages[index, readout.removesuffix("_average"), 10000000]
        )
        assert row["receipt"] == want["receipt"]
        assert row["metrics"] == want["metrics"]
        assert len([r for r in fixed if r["own_snapshot_id"] == row["id"]]) == 8


def test_timing_corpus_cannot_drop_a_fixed_opponent_target() -> None:
    source = sources()
    identifier = source.currents[0, 10000000]["id"]
    source.fixed.remove(
        next(r for r in source.fixed if r["own_snapshot_id"] == identifier)
    )
    with pytest.raises(ArithmeticError, match="incomplete"):
        corpus(source)
