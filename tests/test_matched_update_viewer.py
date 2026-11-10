"""Selection and browsing use explicit tiny fixtures, not measured poker values."""

import copy
from dataclasses import replace
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from poker_ai.evaluation import matched_update_data as data_module
from poker_ai.evaluation import matched_update_viewer as viewer
from poker_ai.evaluation.averaging_history_software import toy_context


def saved() -> dict[str, Any]:
    row = dict(
        id="EXPLICIT-prefix",
        comparison_batch_size=4,
        case=dict(
            spot_file="configs/learning-spots/dev_medium_oop.json",
            representation="texture_range_q8_b8",
            regret_rule="signed",
            seed=20261301,
        ),
    )
    pair = dict(
        planned_prefix_id=row["id"],
        reused_profile_id="EXPLICIT-batch",
        readout="linear_average",
        target_iteration=100,
    )
    return dict(rows=[row], self_pairs=[pair])


@pytest.mark.parametrize(
    "field,value",
    [
        ("seed", True),
        ("batch", True),
        ("batch", 1),
        ("readout", "best"),
        ("rule", "unknown"),
        ("game", "new"),
    ],
)
def test_invalid_selection_rejected(field: str, value: Any) -> None:
    with pytest.raises(ValueError):
        replace(viewer.Selection(), **{field: value})


def test_unique_pair_selection_without_strength_ranking() -> None:
    data = saved()
    pair, row = viewer.select(data, viewer.Selection())
    assert row["id"] == "EXPLICIT-prefix" and pair["target_iteration"] == 100
    other = copy.deepcopy(data)
    other["self_pairs"] *= 2
    with pytest.raises(ArithmeticError):
        viewer.select(other, viewer.Selection())
    with pytest.raises(ArithmeticError):
        viewer.select(data, replace(viewer.Selection(), seed=20261302))


def comparison() -> viewer.Comparison:
    context = toy_context()
    policy = context.partition.normalize(context.partition.legal)
    row = dict(
        iteration=100, total_work=250, metrics=dict(exact_exploitability_chips=2)
    )
    return viewer.Comparison(
        context,
        viewer.Selection(),
        row,
        dict(row, total_work=1000),
        policy,
        policy,
        100,
    )


def example() -> dict[str, Any]:
    return dict(
        hole=["As", "Ad"],
        board=["2c", "3d", "4h", "5s"],
        street="TURN",
        pot=100,
        exact_members=2,
        actions=["check", "raise_to10"],
    )


def test_display_same_updates_unequal_work_and_no_importance_claim() -> None:
    with patch.object(viewer, "example", return_value=example()):
        text = viewer.display(comparison(), 0, 1)
    assert (
        "Matched updates:100" in text.replace(" ", "") or "Matched updates: 100" in text
    )
    assert "0.250000" in text and "not EV loss" in text
    assert "one example" in text and "2.000000%" in text


def test_browse_bounds_invalid_command_quit_and_eof() -> None:
    model = comparison()
    commands = iter(["p", "bad", "n", "q"])
    lines: list[str] = []
    with patch.object(viewer, "example", return_value=example()):
        viewer.browse(model, 0, 1, read=lambda _: next(commands), write=lines.append)
        viewer.browse(
            model,
            0,
            1,
            read=lambda _: (_ for _ in ()).throw(EOFError()),
            write=lines.append,
        )
    assert "Use n, p or q." in lines
    with pytest.raises(ValueError):
        viewer.display(model, 0, 0)
    with pytest.raises(ValueError):
        model.rows(True)


def test_missing_published_inputs_fail_before_heavy_load(tmp_path: Path) -> None:
    with patch.object(
        data_module, "read_saved", side_effect=AssertionError("heavy read")
    ) as heavy:
        with pytest.raises(FileNotFoundError):
            data_module.load(tmp_path)
    heavy.assert_not_called()


@pytest.mark.slow
def test_actual_audited_data_readers_with_constructors_blocked(tmp_path: Path) -> None:
    from poker_ai.evaluation.matched_update_parent_io import activate
    from poker_ai.evaluation.matched_update_presentation import views, write
    from poker_ai.evaluation.matched_update_replay import replay_real
    from poker_ai.postflop.controlled_training import ControlledTrainer
    from poker_ai.postflop.river_study import Deadline
    from poker_ai.solver_validation.matched_array_reference import ScalarReference

    root = Path(__file__).resolve().parents[1]
    with (
        patch.object(
            ControlledTrainer, "__init__", side_effect=AssertionError("no learner")
        ),
        patch.object(
            ScalarReference, "__init__", side_effect=AssertionError("no reference")
        ),
    ):
        data = data_module.load(root, lambda _: None)
        with activate(root):
            proof = replay_real(
                root / data_module.OWN, data.own, data.sources, Deadline(900)
            )
        assert proof["maximum_error_chips"] == 0 and proof["profiles"] == 144
        points, fixed = views(data)
        assert len(points) == 288 and len(fixed) == 2304
        files = write(data, tmp_path / "report", no_plots=True)
        assert set(files) == {
            "self-points.csv",
            "self-groups.csv",
            "fixed-points.csv",
            "fixed-groups.csv",
            "summary.json",
            "tables.md",
        }
        for selection in (
            viewer.Selection(),
            viewer.Selection(
                game="dev_low_oop", representation="exact", batch=16, readout="current"
            ),
        ):
            comparison = viewer.from_data(data, selection)
            assert comparison.left["iteration"] == comparison.right["iteration"]
            assert not comparison.left_policy.flags.writeable
            for seat in (0, 1):
                text = viewer.display(comparison, seat, 1)
                assert "Matched updates:" in text
                assert all(
                    comparison.context.partition.owners[i] == seat
                    for i, _ in comparison.rows(seat)
                )
