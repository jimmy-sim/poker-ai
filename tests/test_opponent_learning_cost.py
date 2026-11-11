"""Fictional old-source COST fixtures, never a forecast or poker trajectory."""

import copy
from pathlib import Path
from typing import Any
from unittest.mock import patch

import numpy as np
import pytest

from poker_ai.evaluation import opponent_learning_cost as cost_inputs
from poker_ai.evaluation import opponent_learning_sources as source_inputs
from poker_ai.evaluation.frozen_batch_replay import warm_mass
from poker_ai.evaluation.opponent_learning_capture import trainer
from poker_ai.evaluation.opponent_learning_cost import OldMember, Standins, collect
from poker_ai.evaluation.opponent_learning_design import (
    COST,
    READOUTS,
    WEIGHTS,
    WORK,
    Design,
)
from poker_ai.evaluation.opponent_learning_own import finish_own, fixture, replay
from poker_ai.evaluation.opponent_learning_replay import metadata
from poker_ai.evaluation.opponent_learning_report import assessment, points
from poker_ai.evaluation.opponent_learning_sources import cost_contract
from poker_ai.postflop.controlled_checkpoints import write_snapshot
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.river_study import Deadline

ROOT = Path(__file__).resolve().parents[1]
BINDING = "b" * 64


def old_fixture() -> Standins:
    contexts, _ = fixture()
    members = {}
    for coordinate in range(6):
        for kind in ("coarse", "fine"):
            tree = contexts[coordinate // 3].tree(kind)
            for label in WORK:
                for readout in (*READOUTS, *WEIGHTS):
                    # Deliberately fictional old records: no learned regrets/RNG.
                    mass = warm_mass(tree) * (label // 100_000 + 2)
                    if readout == "linear":
                        mass = mass * 7
                    values = mass if readout in WEIGHTS else tree.normalize(mass)
                    values.flags.writeable = False
                    key = (coordinate, kind, label, readout)
                    members[key] = OldMember(
                        values,
                        dict(
                            id=f"FICTIONAL_OLD_OWN_{key}",
                            old_work_label=label,
                            old_total_work=label + 13,
                            old_iteration=11,
                        ),
                    )
    return Standins(members, lambda c: contexts[c // 3])


@pytest.fixture(scope="module")
def complete(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Any]:
    folder = tmp_path_factory.mktemp("fictional-cost-pipeline")
    scratch = folder / "scratch"
    design = Design(COST, WORK)
    standins = old_fixture()
    _, opponents = fixture()

    def forbidden(*a: Any, **k: Any) -> None:
        raise AssertionError("old cost fixture constructed a learner/reference")

    with (
        patch("poker_ai.evaluation.opponent_learning_capture.trainer", forbidden),
        patch("poker_ai.solver_validation.reference.Reference.__init__", forbidden),
        patch(
            "poker_ai.solver_validation.matched_array_reference.ScalarReference.__init__",
            forbidden,
        ),
    ):
        paths = [
            collect(
                standins, scratch, design, i, BINDING, lambda e: None, Deadline(180)
            )
            for i in range(30)
        ]
        saved = finish_own(
            folder,
            scratch,
            design,
            paths,
            standins.context_for,
            opponents,
            BINDING,
            lambda e: None,
            Deadline(180),
            standins=standins,
        )
    return dict(
        folder=folder,
        scratch=scratch,
        saved=saved,
        design=design,
        standins=standins,
        opponents=opponents,
    )


def test_frozen_supplement_does_not_change_parent_contract() -> None:
    c = cost_contract(ROOT)
    assert c["new_training_nodes"] == 0
    assert c["new_learning_iterations"] is c["new_learning_rng_entropy"] is None
    assert c["real_training_admission"] is False


def test_complete_cost_shape_cannot_claim_new_learning(
    complete: dict[str, Any],
) -> None:
    s = complete["saved"]
    assert s["scope"] == COST
    assert len(s["profiles"]) == 432
    assert len(s["fixed_conditions"]) == 1152
    assert s["own_replay"]["maximum_error"] == 0
    assert s["training_paths"] == []
    assert len(s["cost_paths"]) == 30
    assert s["initialized_training_paths"] == 0
    assert s["actual_toy_training_work"] == s["actual_poker_training_work"] == 0
    assert s["poker_training_performed"] is s["toy_learning_performed"] is False
    assert s["long_run_admitted"] is s["new_agent_default"] is False
    assert s["original_B4_boundaries"] == []
    assert all(
        r["iteration"] is r["guard_sha256"] is r["rng_entropy"] is None
        for r in s["captures"]
    )
    assert all(a["charged_work"]["total_work"] == 0 for a in s["arms"])
    rows = points(s, complete["design"], (10.0, 20.0))
    assert all(r["units"] == "percent initial pot" for r in rows)
    assert all(r["total_charged_work"] == 0 for r in rows)
    assert all(
        g["accuracy_limits_pass"] is g["paired_improvement_pass"] is None
        for g in assessment(rows, complete["design"])["groups"]
    )


def test_half_labels_retain_actual_old_endpoint_and_both_mixed_sources(
    complete: dict[str, Any],
) -> None:
    captures = complete["saved"]["captures"]
    half = next(
        r
        for r in captures
        if r["path_index"] == 2
        and r["work_label"] == 50_000
        and r["readout"] == "current"
    )
    assert half["actual_old_work_label"] == 100_000
    assert half["nominal_work_label"] == 50_000
    assert len(half["old_own_source_members"]) == 2
    assert half["mixed_tables_learned_together"] is False
    path = complete["design"].path(2)
    projected = complete["standins"].project(path, 50_000, "current").values
    contexts = complete["standins"].context_for(0)
    view = contexts.views[0]
    coarse = complete["standins"].members[0, "coarse", 100_000, "current"].values
    fine = complete["standins"].members[0, "fine", 100_000, "current"].values
    own = contexts.coarse.owners == 0
    other = contexts.fine.owners != 0
    assert np.array_equal(projected[view.coarse_own_to_view[own]], coarse[own])
    assert np.array_equal(projected[view.fine_to_view[other]], fine[other])
    assert not projected.flags.writeable


@pytest.mark.parametrize(
    "change",
    [
        "no_sources",
        "new_work",
        "learning_flag",
        "path",
        "source_policy",
        "mixed_identity",
    ],
)
def test_cost_replay_rejects_invented_or_altered_history(
    complete: dict[str, Any],
    change: str,
) -> None:
    s = copy.deepcopy(complete["saved"])
    standins = complete["standins"]
    if change == "no_sources":
        standins = None
    elif change == "new_work":
        s["actual_poker_training_work"] = 1
    elif change == "learning_flag":
        s["poker_training_performed"] = True
    elif change == "path":
        s["cost_paths"][0]["final_iteration"] = 2
    else:
        # Repack a complete valid snapshot/archive, so hashes alone cannot save it.
        row = s["captures"][0 if change == "source_policy" else 54]
        meta = metadata(row)
        if change == "mixed_identity":
            meta["mixed_tables_learned_together"] = True
        tree = standins.context_for(row["coordinate"]).tree(row["tree_kind"])
        values = standins.project(
            complete["design"].path(row["path_index"]),
            row["work_label"],
            row["readout"],
        ).values.copy()
        if change == "source_policy":
            values[0] = [0.1, 0.9]
        filename = f"bad-{change}.json.gz"
        receipt = write_snapshot(complete["scratch"] / filename, tree, values, meta)
        row.update(file=filename, receipt=receipt, metadata_sha256=sha(meta))
        # Only raw replay is needed to exercise the source reconstruction guard.
        from poker_ai.evaluation.opponent_learning_cost import replay as raw

        with pytest.raises(ArithmeticError):
            raw(
                complete["scratch"],
                complete["design"],
                s["captures"],
                s["masses"],
                s["warms"],
                standins.context_for,
                BINDING,
                Deadline(180),
                standins,
            )
        return
    with pytest.raises(ArithmeticError):
        replay(
            complete["folder"],
            s,
            complete["design"],
            complete["standins"].context_for,
            complete["opponents"],
            BINDING,
            Deadline(180),
            standins=standins,
        )


def test_cost_scope_cannot_construct_actual_learner() -> None:
    standins = old_fixture()
    with pytest.raises(ValueError, match="cannot construct"):
        trainer(standins.context_for(0).coarse, Design(COST, WORK), 0)


@pytest.mark.slow
def test_all180_original_own_archive_members_decode_without_new_learning() -> None:
    def forbidden(*a: Any, **k: Any) -> None:
        raise AssertionError("old archive reader constructed a trainer/reference")

    with (
        patch("poker_ai.evaluation.opponent_learning_capture.trainer", forbidden),
        patch("poker_ai.solver_validation.reference.Reference.__init__", forbidden),
        patch(
            "poker_ai.solver_validation.matched_array_reference.ScalarReference.__init__",
            forbidden,
        ),
    ):
        sources = source_inputs.load(ROOT)
        standins = cost_inputs.load(ROOT, sources, Deadline(180))
    assert len(standins.members) == 180
    assert all(
        not member.values.flags.writeable for member in standins.members.values()
    )
    for coordinate in range(6):
        path = Design(COST, WORK).path(5 * coordinate)
        old = standins.project(path, 50_000, "current")
        assert old.identity["actual_old_work_label"] == 100_000
        assert old.identity["old_own_source_members"][0]["old_total_work"] >= 100_000
