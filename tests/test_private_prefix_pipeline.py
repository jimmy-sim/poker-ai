"""Complete toy archive/paired-report replay and retained partial IO contracts.

All temporary outputs are explicit software fixtures, never real poker studies
or published scientific proof receipts. Native scalar schema fixtures do not
construct a solver or claim independent agreement.
"""

import copy
import json
from contextlib import ExitStack
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from poker_ai.evaluation.private_prefix_archive import replay
from poker_ai.evaluation.private_prefix_correctness import contract
from poker_ai.evaluation.private_prefix_exercise import exercise
from poker_ai.evaluation.private_prefix_io import (
    archive,
    destinations,
    fresh,
    gather,
    retain_partial,
)
from poker_ai.evaluation.private_prefix_pairs import (
    fixed_pairs,
    metric_difference,
    self_pairs,
)
from poker_ai.evaluation.private_prefix_report import plots, write
from poker_ai.evaluation.private_prefix_toy import (
    baselines,
    fixture,
    maps,
    replay_baselines,
)
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.river_study import Deadline


def build(folder: Path) -> tuple[Any, ...]:
    config = contract(Path(__file__).resolve().parents[1])
    design, context, opponents = fixture(config)
    binding = sha({"EXPLICIT_SOFTWARE_FIXTURE": "0" * 64})
    saved: dict[str, Any] = dict(
        scope=design.scope,
        config=config,
        manifest=design.manifest(),
        source={"sha256": {"EXPLICIT_SOFTWARE_FIXTURE": "0" * 64}},
        source_sha256=binding,
        events=[],
        captures=[],
        masses=[],
        rows=[],
        fixed_matches=[],
    )
    deadline = Deadline(120)
    scratch = folder / "scratch"
    saved["baseline_rows"], saved["baseline_fixed"] = baselines(
        design, context, opponents, scratch, binding, deadline
    )
    path = folder / "own.json"
    archive(path, saved, scratch, "baseline_rows", "baseline")
    exercise(
        path, saved, design, lambda _: context, opponents.matches, scratch, deadline
    )
    selves, targets = maps(design, saved["baseline_rows"], saved["baseline_fixed"])
    saved["self_pairs"] = self_pairs(design, saved["rows"], selves)
    saved["fixed_pairs"] = fixed_pairs(saved["fixed_matches"], targets)
    path.write_text(json.dumps(saved, sort_keys=True, allow_nan=False))
    return path, saved, design, context, opponents


@pytest.mark.slow
def test_complete432_policy288_book1152_fixed_shape_and_all_baseline_pairs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path, saved, design, context, opponents = build(tmp_path)
    assert len(saved["captures"]) == len(saved["rows"]) == 432
    assert len(saved["masses"]) == 288 and len(saved["fixed_matches"]) == 1152
    assert len(saved["baseline_rows"]) == 648 and len(saved["baseline_fixed"]) == 1728
    assert len(saved["self_pairs"]) == 864 and len(saved["fixed_pairs"]) == 2304
    assert (
        saved["training_attempted_paths"] == saved["initialized_training_paths"] == 48
    )

    def forbidden(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("archive reader constructed learner or reference")

    with ExitStack() as stack:
        for name in (
            "poker_ai.postflop.controlled_training.ControlledTrainer.__init__",
            "poker_ai.solver_validation.matched_array_reference.ScalarReference.__init__",
            "poker_ai.solver_validation.reference.Reference.__init__",
        ):
            stack.enter_context(patch(name, forbidden))
        own = replay(
            path, saved, design, lambda _: context, opponents.matches, Deadline(60)
        )
        old = replay_baselines(path, saved, design, context, opponents, Deadline(60))
    assert (
        own["maximum_error_chips"]
        == own["maximum_error_unitless"]
        == old["maximum_error_chips"]
        == 0
    )
    pots = {p["spot_file"]: 2.0 for p in design.paths}
    files = write(saved, tmp_path / "report", pots, no_plots=True)
    assert len(files) == 4
    other = write(saved, tmp_path / "report-again", pots, no_plots=True)
    assert files == other
    assert all(b"\r\n" not in (tmp_path / "report" / f).read_bytes() for f in files)
    with pytest.raises(FileExistsError):
        write(saved, tmp_path / "report", pots, no_plots=True)
    # This protects shared-crossing movement replay: B16 can cross two or more
    # tiny work labels in one complete update, retaining one predecessor guard.
    assert any(
        a["iteration"] == b["iteration"]
        for a in saved["captures"]
        for b in saved["captures"]
        if a["path_index"] == b["path_index"]
        and a["readout"] == b["readout"]
        and a["work_label"] != b["work_label"]
    )
    damaged = copy.deepcopy(saved)
    damaged["fixed_matches"][0]["target"] = True
    with pytest.raises(ArithmeticError):
        replay(
            path, damaged, design, lambda _: context, opponents.matches, Deadline(60)
        )
    archive_path = path.with_name(saved["masses_file"])
    original = archive_path.read_bytes()
    archive_path.write_bytes(original + b"corrupt")
    with pytest.raises(ArithmeticError, match="hash changed"):
        replay(path, saved, design, lambda _: context, opponents.matches, Deadline(60))


@pytest.mark.parametrize("kind", ["existing", "broken_symlink"])
def test_every_preflight_destination_including_partial_archive_refuses_reuse(
    tmp_path: Path, kind: str
) -> None:
    path = tmp_path / "own.json"
    for target in destinations(path):
        target.parent.mkdir(parents=True, exist_ok=True)
        if kind == "existing":
            target.write_text("retain")
        else:
            target.symlink_to(tmp_path / "missing")
        with pytest.raises(FileExistsError):
            fresh(path)
        assert (
            target.is_symlink()
            if kind == "broken_symlink"
            else target.read_text() == "retain"
        )
        target.unlink()
    fresh(path)


def test_partial_events_retained_and_invalid_route_fails(tmp_path: Path) -> None:
    row = dict(
        id="explicit-partial",
        path_index=0,
        work_label=1,
        readout="current",
        file="snapshot.gz",
        receipt={"sha256": "0" * 64},
    )
    saved: dict[str, Any] = dict(
        events=[
            dict(kind="cell", phase="training_started", index=0),
            dict(kind="cell", phase="training_initialized", index=0),
            dict(kind="cell", phase="capture", index=0, row=row),
        ]
    )
    gather(saved)
    assert saved["initialized_training_paths"] == 1 and saved["captures"] == [row]
    retain_partial(tmp_path / "own.json", saved, tmp_path / "missing-scratch")
    assert saved["retention_errors"] and "captures_file" not in saved
    assert saved["events"][-1]["row"] == row
    saved["events"].append(dict(kind="cell", phase="training_started", index=True))
    with pytest.raises(ArithmeticError, match="outside"):
        gather(saved)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), True])
def test_metric_functions_reject_nonfinite_bool_and_names(value: Any) -> None:
    with pytest.raises(ArithmeticError):
        metric_difference({"value": value}, {"value": 0.0})
    with pytest.raises(ArithmeticError):
        metric_difference({"a": 0.0}, {"b": 0.0})


def test_self_comparison_is_zero_with_preserved_ev_signs() -> None:
    metrics = dict(value_player_zero_chips=-1.5, exact_exploitability_chips=0.7)
    assert metric_difference(metrics, metrics) == dict(
        value_player_zero_chips=0, exact_exploitability_chips=0
    )
    assert metric_difference({"ev": 2.0}, {"ev": 3.0}) == {"ev": -1.0}


def test_optional_plot_boundary_with_explicit_fictional_values(tmp_path: Path) -> None:
    pytest.importorskip("matplotlib")
    import itertools

    from poker_ai.evaluation.private_prefix_design import READOUTS, TOY

    groups: list[dict[str, Any]] = []
    for game, rep, rule, readout, kind, batch, label in itertools.product(
        ("EXPLICIT_TOY_LOW", "EXPLICIT_TOY_MEDIUM"),
        ("exact", "q8"),
        ("signed", "clipped"),
        READOUTS,
        ("B1", "IID"),
        (4, 16),
        (100000, 1000000, 10000000),
    ):
        groups.append(
            dict(
                spot_file=game,
                representation=rep,
                regret_rule=rule,
                readout=readout,
                baseline_kind=kind,
                batch_size=batch,
                work_label=label,
                mean_delta_pct_pot=(len(groups) - 144) / 288,
            )
        )
    plots(TOY, groups, tmp_path)
    assert len(list(tmp_path.glob("*.png"))) == 3
    assert all(
        p.read_bytes().startswith(bytes.fromhex("89504e470d0a1a0a"))
        for p in tmp_path.glob("*.png")
    )
