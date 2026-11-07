"""Made-category semantics, observable keys, recall and bounded admission evidence."""

import copy
import itertools
import json
import shutil
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from poker_ai.abstraction.made_category import (
    MadeCategoryAbstraction,
    made_category_history,
)
from poker_ai.abstraction.model import CardAbstraction
from poker_ai.cards import parse_card
from poker_ai.postflop import made_admission as admission
from poker_ai.postflop import made_admission_report as reporting
from poker_ai.postflop.game import SpotState, load_spot
from poker_ai.postflop.matrix import MatrixTree, observation_key, recall_violations
from poker_ai.postflop.tree import SpotTree
from poker_ai.solver_validation import made_admission as native

ROOT = Path(__file__).resolve().parents[1]


def cards(text: str) -> tuple[int, ...]:
    return tuple(parse_card(c) for c in text.split())


@pytest.mark.parametrize(
    "hole,board,expected",
    [
        ("9c 9d", "", ()),
        ("9c 9d", "Ts 9s 4d", (3,)),
        ("9c 9d", "Ts 9s 4d 2h 2d", (3, 3, 6)),
        ("9c 9d", "Ts 9s 4d 2h 9h", (3, 3, 7)),
        ("Kh Qh", "Ts 9s 4d 2h Jd", (0, 0, 4)),
        ("Kh Qh", "Ts 9s 4d 2h Kd", (0, 0, 1)),
    ],
)
def test_category_history_meaning(
    hole: str, board: str, expected: tuple[int, ...]
) -> None:
    assert made_category_history(cards(hole), cards(board)) == expected


@pytest.mark.parametrize(
    "hole,board",
    [((0,), ()), ((0, 0), ()), ((0, 1), (2,)), ((0, 1), (0, 2, 3)), ((0, True), ())],
)
def test_category_history_rejects_invalid_cards(
    hole: tuple[int, ...], board: tuple[int, ...]
) -> None:
    with pytest.raises((TypeError, ValueError)):
        made_category_history(hole, board)


def test_category_symmetry_flop_order_and_prefix_memory() -> None:
    hole, board = cards("9c 9d"), cards("Ts 9s 4d 2h 9h")
    history = made_category_history(hole, board)
    for suits in itertools.permutations(range(4)):
        renamed_hole = tuple(4 * (c // 4) + suits[c % 4] for c in hole)
        renamed_board = tuple(4 * (c // 4) + suits[c % 4] for c in board)
        assert made_category_history(renamed_hole, renamed_board) == history
    for flop in itertools.permutations(board[:3]):
        assert made_category_history(hole, flop + board[3:]) == history
    for n in (3, 4, 5):
        assert made_category_history(hole, board[:n]) == history[: n - 2]


@pytest.fixture(scope="module")
def models() -> tuple[CardAbstraction, MadeCategoryAbstraction]:
    base = CardAbstraction.load(ROOT / "results/card-models/potential-8.json")
    return base, MadeCategoryAbstraction(base.models, base.config)


@pytest.mark.parametrize(
    "own_index,first_river,second_river", [(1, "2d", "9h"), (0, "Jd", "Kd")]
)
def test_candidate_splits_retained_category_conflicts(
    models: tuple[CardAbstraction, MadeCategoryAbstraction],
    own_index: int,
    first_river: str,
    second_river: str,
) -> None:
    base, richer = models
    spot = load_spot(ROOT / "configs/learning-spots/dev_medium_oop.json")
    observations = []
    for river in (first_river, second_river):
        state = (
            SpotState(spot)
            .child(0)
            .child(own_index)
            .child(parse_card(river))
            .child(1)
            .child(1)
            .child(3)
        )
        assert state.dealer is not None
        observations.append(state.dealer.observe(state.actor))
    assert observation_key(observations[0], "texture_b8", base) == observation_key(
        observations[1], "texture_b8", base
    )
    assert observation_key(observations[0], "texture_b8", richer) != observation_key(
        observations[1], "texture_b8", richer
    )
    assert (
        json.loads(richer.information(observations[0]))[0] == "made-category-history-v1"
    )


def test_richer_key_hides_actual_opponent_and_future_and_rejects_wrong_seat(
    models: tuple[CardAbstraction, MadeCategoryAbstraction],
) -> None:
    base_model, richer = models
    spot = load_spot(ROOT / "configs/learning-spots/dev_low_oop.json")
    base = SpotState(spot).child(0).child(0)
    other = SpotState(spot).child(0).child(1)
    worlds = (
        base.child(base.actions[0]),
        base.child(base.actions[1]),
        other.child(other.actions[0]),
    )
    observations = []
    for world in worlds:
        assert world.dealer is not None
        observations.append(world.dealer.observe(world.actor))
    old = base_model.information(observations[0])
    assert len({richer.information(o) for o in observations}) == 1
    assert json.loads(richer.information(observations[0]))[1] == old
    assert base_model.information(observations[0]) == old
    for invalid in (
        replace(observations[0], terminal=True),
        replace(observations[0], seat=1 - observations[0].seat),
    ):
        with pytest.raises(ValueError):
            richer.information(invalid)


@pytest.mark.parametrize("game", ["dev_low_oop", "dev_medium_oop"])
def test_candidate_refines_texture_and_preserves_menus_and_recall(
    models: tuple[CardAbstraction, MadeCategoryAbstraction],
    game: str,
) -> None:
    base, richer = models
    source = SpotTree.build(load_spot(ROOT / f"configs/learning-spots/{game}.json"))
    texture = MatrixTree.build(source, "texture_b8", base)
    candidate = MatrixTree.build(source, "texture_b8", richer)
    assert recall_violations(candidate) == 0
    for info in range(len(candidate.keys)):
        assert (
            len(set(texture.exact_to_abstract[candidate.exact_to_abstract == info]))
            == 1
        )


def fixture_source(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return {"dirty": False, "sha256": {}, "git_commit": "test-fixture"}


@pytest.fixture(scope="module")
def tiny_report(
    tmp_path_factory: pytest.TempPathFactory,
) -> tuple[Path, dict[str, Any]]:
    directory = tmp_path_factory.mktemp("made-admission-fixture")
    config = json.loads((ROOT / "configs/made-category-admission.json").read_text())
    config.update(
        spot_files=config["spot_files"][:1],
        full_tree_checkpoints=[1, 2],
        full_tree_backend="numpy",
    )
    cfg = directory / "config.json"
    cfg.write_text(json.dumps(config))
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(admission, "source_provenance", fixture_source)
        report = admission.run_admission(ROOT, cfg, directory / "study.json")
    assert report["status"] == "completed", report["failure"]
    return directory / "study.json", report


def test_complete_full_only_fixture_replays_without_global_claim(
    tiny_report: tuple[Path, dict[str, Any]],
) -> None:
    path, _ = tiny_report
    report, policies, error = admission.replay(ROOT, path)
    assert error == 0 and len(policies) == 8
    assert report["acceptance"]["complete"]
    assert (
        report["sampled_learning"] == "not_run"
        and report["fresh_global_admission"] is False
    )
    with pytest.raises(FileExistsError):
        admission.run_admission(ROOT, path.parent / "config.json", path)


@pytest.mark.parametrize(
    "change", ["missing", "duplicate", "work", "diagnostic", "global"]
)
def test_incomplete_or_changed_admission_cannot_replay(
    tiny_report: tuple[Path, dict[str, Any]],
    tmp_path: Path,
    change: str,
) -> None:
    original, raw = tiny_report
    report = copy.deepcopy(raw)
    shutil.copyfile(
        original.parent / raw["own_policies_file"], tmp_path / raw["own_policies_file"]
    )
    if change == "missing":
        report["rows"].pop()
    elif change == "duplicate":
        report["rows"].append(report["rows"][-1])
    elif change == "work":
        report["rows"][0]["total_node_work"] += 1
    elif change == "diagnostic":
        report["diagnostics"][0]["key_utf8_bytes"] += 1
    else:
        report["fresh_global_admission"] = True
    path = tmp_path / "study.json"
    path.write_text(json.dumps(report))
    with pytest.raises((ArithmeticError, ValueError)):
        admission.replay(ROOT, path)


def test_full_admission_requires_both_accuracy_and_compression(
    tiny_report: tuple[Path, dict[str, Any]],
) -> None:
    _, report = tiny_report
    rows, diagnostics = (
        copy.deepcopy(report["rows"]),
        copy.deepcopy(report["diagnostics"]),
    )
    for row in rows:
        row.update(
            exploitability_pot_fraction=0.0, uniform_reach_average_row_coverage=1.0
        )
    for diagnostic in diagnostics:
        diagnostic["information_sets"] = (
            500 if diagnostic["representation"] == "texture_made_b8" else 1000
        )
    assert admission.acceptance(rows, diagnostics, report["config"])[
        "own_full_control_gate_passed"
    ]
    next(d for d in diagnostics if d["representation"] == "texture_made_b8")[
        "information_sets"
    ] = 751
    assert not admission.acceptance(rows, diagnostics, report["config"])[
        "own_full_control_gate_passed"
    ]
    for diagnostic in diagnostics:
        diagnostic["information_sets"] = (
            500 if diagnostic["representation"] == "texture_made_b8" else 1000
        )
    next(
        r
        for r in rows
        if r["representation"] == "texture_made_b8" and r["iteration"] == 2
    )["exploitability_pot_fraction"] = 0.006
    assert not admission.acceptance(rows, diagnostics, report["config"])[
        "own_full_control_gate_passed"
    ]


def test_native_audit_and_report_fixture(
    tiny_report: tuple[Path, dict[str, Any]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pytest.importorskip("pyspiel")
    path, _ = tiny_report
    monkeypatch.setattr(native, "source_provenance", fixture_source)
    audit_path = tmp_path / "audit.json"
    result = native.audit(ROOT, path.parent / "config.json", path, audit_path)
    assert result["status"] == "passed" and len(result["comparisons"]) == 8
    report, _, _ = admission.replay(ROOT, path)
    assert reporting.checked_audit(path, report, result) <= 1e-9
    bad = copy.deepcopy(result)
    bad["comparisons"].append(bad["comparisons"][-1])
    with pytest.raises(ArithmeticError):
        reporting.checked_audit(path, report, bad)
    monkeypatch.setattr(reporting, "plots", lambda *a: None)
    summary = reporting.render(ROOT, path, audit_path, tmp_path / "report")
    assert (
        summary["sampled_learning"] == "not_run"
        and summary["fresh_global_admission"] is False
    )


def test_admission_plot_smoke(
    tiny_report: tuple[Path, dict[str, Any]], tmp_path: Path
) -> None:
    pytest.importorskip("matplotlib")
    reporting.plots(tiny_report[1], tmp_path)
    assert {p.name for p in tmp_path.glob("*.png")} == {
        "full-controls.png",
        "row-counts.png",
    }
