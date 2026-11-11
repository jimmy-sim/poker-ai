"""Pinned source identities and all original B4 barriers, without new poker runs."""

import copy
import json
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

from poker_ai.evaluation import batch_current_inputs as historical
from poker_ai.evaluation.opponent_learning_design import REAL, WORK, Design
from poker_ai.evaluation.opponent_learning_sources import (
    boundaries,
    build_game,
    contract,
    input_pins,
    verify_boundaries,
)

ROOT = Path(__file__).resolve().parents[1]


def archived() -> historical.Sources:
    # The extraction function needs only the published own metadata, not a new
    # source loader, native reference or learner. This stub is not an admission.
    own = json.loads((ROOT / "results/reduced-batch-study/own.json").read_text())
    return cast(historical.Sources, SimpleNamespace(own=own))


def test_fixed_protocol_and_all_source_input_hashes() -> None:
    config = contract(ROOT)
    assert len(input_pins(ROOT)) == len(config["input_sha256"])
    assert config["maximum_own_seconds"] == 7200
    assert config["maximum_native_seconds"] == 900
    assert config["maximum_software_seconds"] == 180
    assert config["long_run_admitted"] is False
    assert len(config["frozen_controls"]) == 16


@pytest.mark.parametrize("game", [0, 1])
def test_actual_structural_factory_preserves_both_known_game_views(game: int) -> None:
    c = build_game(ROOT, game)
    assert c.fine.player.shape == c.coarse.player.shape
    assert c.views[0].fine_sha256 == c.views[1].fine_sha256
    assert c.views[0].coarse_sha256 == c.views[1].coarse_sha256
    assert c.scoring["coarse"].exact is c.fine
    for index in (-1, 2, True):
        with pytest.raises(ValueError):
            build_game(ROOT, index)


def test_all36_original_barrier_metadata_is_complete() -> None:
    expected = boundaries(archived())
    assert len(expected) == 36
    assert len({(r["path_index"], r["work_label"]) for r in expected}) == 36
    assert {r["path_index"] % 5 for r in expected} == {0, 4}
    assert {r["original_path_index"] for r in expected}.issubset(set(range(24, 48)))
    assert all(
        set(r["readouts"]) == set(r["mass_sha256"]) == {"uniform", "linear"}
        for r in expected
    )


@pytest.mark.parametrize(
    "change", ["none", "current", "average", "ledger", "work", "missing"]
)
def test_barrier_checks_bits_and_work_not_just_number_of_rows(change: str) -> None:
    d = Design(REAL, WORK)
    manifest = d.manifest()
    captures, masses = manifest["captures"], manifest["masses"]
    by_id = {r["id"]: r for r in captures + masses}
    expected = boundaries(archived())
    for peer in expected:
        i, w = peer["path_index"], peer["work_label"]
        fields = {
            k: peer[k]
            for k in (
                "iteration",
                "previous_work",
                "total_work",
                "last_iteration_visits",
                "initialization_visits",
                "sampled_traversals",
                "guard_sha256",
                "current_sha256",
            )
        }
        current = by_id[d.raw(i, w, "current")["id"]]
        current.update(
            fields, receipt=dict(policy_sha256=peer["current_policy_sha256"])
        )
        for weight in ("uniform", "linear"):
            average = by_id[d.raw(i, w, weight + "_average")["id"]]
            average.update(fields, **peer["readouts"][weight])
            average["receipt"] = dict(
                policy_sha256=peer["readouts"][weight]["policy_sha256"]
            )
            mass = by_id[d.mass(i, w, weight)["id"]]
            mass.update(
                guard_sha256=peer["guard_sha256"],
                receipt=dict(mass_sha256=peer["mass_sha256"][weight]),
            )
    bad = list(copy.deepcopy(expected))
    if change == "none":
        result = verify_boundaries(d, captures, masses, tuple(bad))
        assert result["original_work_boundaries"] == 36
        assert result["original_policy_bits"] == 108
        assert result["original_ledger_bits"] == 72
        return
    if change == "current":
        bad[0]["current_policy_sha256"] = "b" * 64
    elif change == "average":
        bad[0]["readouts"]["linear"]["state_sha256"] = "b" * 64
    elif change == "ledger":
        bad[0]["mass_sha256"]["uniform"] = "b" * 64
    elif change == "work":
        bad[0]["iteration"] = True
    else:
        bad.pop()
    with pytest.raises(ArithmeticError):
        verify_boundaries(d, captures, masses, tuple(bad))
