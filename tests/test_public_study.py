"""Small fixtures: grid integrity, exact work, replay, native audits and reporting."""

import copy
import gzip
import json
import shutil
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from poker_ai.abstraction.model import CardAbstraction
from poker_ai.postflop import public_evidence as evidence
from poker_ai.postflop import public_metrics as metrics
from poker_ai.postflop import public_report as reporting
from poker_ai.postflop import public_study as study
from poker_ai.postflop.game import load_spot
from poker_ai.postflop.learning import decision_mass
from poker_ai.postflop.matrix import MatrixTree
from poker_ai.postflop.river_study import digest
from poker_ai.postflop.tree import SpotTree
from poker_ai.solver_validation import public_board as native

ROOT = Path(__file__).resolve().parents[1]


def config() -> dict[str, Any]:
    result: dict[str, Any] = json.loads(
        (ROOT / "configs/public-board-study.json").read_text()
    )
    return result


def fixture_source(*args: Any, **kwargs: Any) -> dict[str, Any]:
    # Explicit unit fixture, not a historical admission or publication receipt.
    return {"git_commit": "test-fixture", "dirty": False, "sha256": {}}


@pytest.fixture(scope="module")
def tiny_report(
    tmp_path_factory: pytest.TempPathFactory,
) -> tuple[Path, dict[str, Any]]:
    directory = tmp_path_factory.mktemp("public-board-fixture")
    raw = config()
    raw.update(
        development_spots=raw["development_spots"][:1],
        seeds=[17],
        sampled_node_checkpoints=[6000, 6200],
        full_tree_checkpoints=[1, 2],
        full_tree_backend="numpy",
        profile_iterations=2,
        profile_repetitions=2,
    )
    path = directory / "config.json"
    path.write_text(json.dumps(raw))
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(study, "source_provenance", fixture_source)
        report = study.run_study(ROOT, path, directory / "study.json")
    assert report["status"] == "completed", report["failure"]
    return directory / "study.json", report


def copy_report(source: Path, directory: Path) -> Path:
    directory.mkdir()
    raw = json.loads(source.read_text())
    shutil.copyfile(
        source.parent / raw["own_policies_file"], directory / raw["own_policies_file"]
    )
    path = directory / "study.json"
    path.write_text(json.dumps(raw))
    return path


def save_payload(path: Path, payload: dict[str, Any]) -> None:
    raw = json.loads(path.read_text())
    policy_path = path.parent / raw["own_policies_file"]
    policy_path.write_bytes(gzip.compress(json.dumps(payload).encode(), mtime=0))
    raw["own_policies_sha256"] = digest(policy_path)
    path.write_text(json.dumps(raw))


def test_complete_grid_exact_work_profiles_masks_and_checkpoint_receipts(
    tiny_report: tuple[Path, dict[str, Any]],
) -> None:
    path, raw = tiny_report
    report, policies, replay = evidence.replay(ROOT, path, check_checkpoints=True)
    assert len(policies) == len(report["rows"]) == 20
    assert report["acceptance"]["complete"]
    assert replay["maximum_own_replay_error_chips"] == 0
    assert replay["checkpoint_receipts_checked"] == 10
    assert len(replay["crossplay"]) == 100
    for row in report["rows"]:
        if row["method"] == "external":
            assert row["warm_node_equivalent"] == 5998
            assert (
                row["total_node_work"]
                == row["warm_node_equivalent"] + row["recursive_visits"]
            )
            assert (
                row["node_threshold"]
                <= row["total_node_work"]
                < row["node_threshold"] + 5998
            )
            assert row["uniform_reach_average_row_coverage"] == pytest.approx(1)
    for diagnostic in report["diagnostics"]:
        profiles = diagnostic["profiles"]
        assert (
            len(profiles) == 2
            and profiles[0]["total_node_work"] == profiles[1]["total_node_work"]
        )
        assert diagnostic["recall_violations"] == 0
    with pytest.raises(FileExistsError):
        study.run_study(ROOT, path.parent / "config.json", path)
    assert raw["config"] == report["config"]


@pytest.mark.parametrize(
    "change",
    ["missing", "duplicate", "profile", "work", "diagnostic", "model", "source"],
)
def test_missing_or_changed_evidence_cannot_be_replayed(
    tiny_report: tuple[Path, dict[str, Any]],
    tmp_path: Path,
    change: str,
) -> None:
    path = copy_report(tiny_report[0], tmp_path / change)
    raw = json.loads(path.read_text())
    if change == "missing":
        raw["rows"].pop()
    elif change == "duplicate":
        raw["rows"].append(raw["rows"][-1])
    elif change == "profile":
        raw["diagnostics"][0]["profiles"].pop()
    elif change == "work":
        next(r for r in raw["rows"] if r["method"] == "external")[
            "recursive_visits"
        ] += 1
    elif change == "diagnostic":
        raw["diagnostics"][0]["key_utf8_bytes"] += 1
    elif change == "source":
        raw["source"]["sha256"]["src/poker_ai/postflop/public_study.py"] = "changed"
    else:
        raw["model_sha256"] = "changed"
    path.write_text(json.dumps(raw))
    with pytest.raises((ArithmeticError, ValueError)):
        evidence.replay(ROOT, path)


@pytest.mark.parametrize(
    "change", ["duplicate", "missing", "active", "visit", "policy"]
)
def test_frozen_policy_and_coverage_mutations_are_detected(
    tiny_report: tuple[Path, dict[str, Any]],
    tmp_path: Path,
    change: str,
) -> None:
    path = copy_report(tiny_report[0], tmp_path / change)
    raw = json.loads(path.read_text())
    payload = json.loads(
        gzip.decompress((path.parent / raw["own_policies_file"]).read_bytes())
    )
    if change == "duplicate":
        payload["policies"].append(payload["policies"][-1])
    elif change == "missing":
        payload["policies"].pop()
    else:
        snapshot = next(
            p
            for p in payload["policies"]
            if p["encoding"] == "legacy_b8" and p["method"] == "external"
        )
        if change == "active":
            snapshot["average_active"][0] = 0
        elif change == "visit":
            snapshot["sampled"][0] = 1 - snapshot["sampled"][0]
        else:
            # A legal row may still contradict other exact infos in its bucket.
            row = snapshot["policy"][0]
            snapshot["policy"][0] = [
                float(i == int(np.argmin(row))) for i in range(len(row))
            ]
    save_payload(path, payload)
    with pytest.raises((ArithmeticError, ValueError)):
        evidence.replay(ROOT, path)


def test_candidate_gate_requires_accuracy_compression_and_all_intermediate_cells(
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
    for row in diagnostics:
        row["information_sets"] = 500 if row["encoding"] == "texture_b8" else 1000
    cfg = report["config"]
    assert metrics.acceptance(rows, diagnostics, cfg)["candidate_learning_gate_passed"]
    bad = copy.deepcopy(diagnostics)
    next(r for r in bad if r["encoding"] == "texture_b8")["information_sets"] = 751
    assert not metrics.acceptance(rows, bad, cfg)["candidate_learning_gate_passed"]
    bad_rows = copy.deepcopy(rows)
    next(
        r
        for r in bad_rows
        if r["encoding"] == "texture_b8"
        and r["method"] == "external"
        and r["node_threshold"] == cfg["sampled_node_checkpoints"][-1]
    )["exploitability_pot_fraction"] = 1.0
    assert not metrics.acceptance(bad_rows, diagnostics, cfg)[
        "candidate_learning_gate_passed"
    ]
    for changed in (rows[:-1], rows + [rows[-1]], rows[:1] + rows[2:]):
        assert not metrics.acceptance(changed, diagnostics, cfg)["complete"]
        assert not metrics.acceptance(changed, diagnostics, cfg)[
            "candidate_learning_gate_passed"
        ]


@pytest.mark.parametrize(
    "change", ["seed", "threshold", "candidate", "seconds", "profile", "tolerance"]
)
def test_invalid_protocol_is_rejected(change: str) -> None:
    raw = config()
    if change == "seed":
        raw["seeds"].append(raw["seeds"][0])
    elif change == "threshold":
        raw["sampled_node_checkpoints"].reverse()
    elif change == "candidate":
        raw["candidate"] = "canonical_b8"
    elif change == "seconds":
        raw["maximum_seconds"] = float("nan")
    elif change == "profile":
        raw["profile_repetitions"] = 0
    else:
        raw["limits"]["independent_value_br_tolerance_chips"] = 1.0
    with pytest.raises(ValueError):
        metrics.validate_config(raw)


def test_dirty_code_cannot_start_an_experiment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(study, "source_provenance", lambda *a, **k: {"dirty": True})
    with pytest.raises(ValueError, match="publish"):
        study.run_study(
            ROOT, ROOT / "configs/public-board-study.json", tmp_path / "study.json"
        )
    assert not (tmp_path / "study.json").exists()


def test_budget_abort_is_retained_and_never_accepted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    raw = config()
    raw["maximum_seconds"] = 1e-12
    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps(raw))
    monkeypatch.setattr(study, "source_provenance", fixture_source)
    path = tmp_path / "study.json"
    report = study.run_study(ROOT, cfg, path)
    assert (
        report["status"] == "incomplete" and report["failure"]["type"] == "TimeoutError"
    )
    assert not report["acceptance"]["complete"]
    with pytest.raises(ValueError, match="partial"):
        study.checked_artifacts(path)


def test_collision_weights_agree_with_pairwise_physical_observations() -> None:
    source = SpotTree.build(load_spot(ROOT / "configs/learning-spots/dev_low_oop.json"))
    exact = MatrixTree.build(source)
    model = CardAbstraction.load(ROOT / "results/card-models/potential-8.json")
    abstract = MatrixTree.build(source, "legacy_b8", model)
    mass = decision_mass(exact, exact.normalize(exact.legal))
    assert (
        metrics.collision_summary(exact, mass)["uniform_decision_reach_any_collision"]
        == 0
    )
    observations = []
    for node in source.representatives:
        state = source.states[node]
        assert state.dealer is not None
        observations.append(state.dealer.observe(state.actor))
    flags = []
    for i, observation in enumerate(observations):
        flags.append(
            any(
                abstract.exact_to_abstract[i] == abstract.exact_to_abstract[j]
                and observation.board != other.board
                for j, other in enumerate(observations)
            )
        )
    diagnostic = metrics.collision_summary(abstract, mass)
    assert diagnostic["uniform_decision_reach_public_collision"] == pytest.approx(
        mass @ np.array(flags) / mass.sum()
    )
    with pytest.raises(ValueError):
        metrics.collision_summary(abstract, np.zeros(len(source.keys)))


def synthetic_native(
    path: Path, report: dict[str, Any], crossplay: list[dict[str, Any]]
) -> dict[str, Any]:
    # Matching-number fixture tests validator/report behavior, NOT native evidence.
    return {
        "status": "passed",
        "input_sha256": digest(path),
        "tolerance_chips": report["config"]["limits"][
            "independent_value_br_tolerance_chips"
        ],
        "checkpoint_receipts_checked": sum(
            r["method"] == "external" for r in report["rows"]
        ),
        "seconds": 0,
        "comparisons": [
            {
                **{k: r[k] for k in metrics.IDENTITY},
                "native_value_chips": r["value_player_zero_chips"],
                "native_exploitability_chips": r["exploitability_chips"],
                "value_error_chips": 0,
                "exploitability_error_chips": 0,
            }
            for r in report["rows"]
        ],
        "crossplay": [
            {
                "spot_file": r["spot_file"],
                "first": r["first"],
                "second": r["second"],
                "native_value_player_zero_chips": r["value_player_zero_chips"],
                "native_seat_balanced_first_chips": r["seat_balanced_first_chips"],
                "value_error_chips": 0,
                "balanced_error_chips": 0,
            }
            for r in crossplay
        ],
    }


def test_crossplay_self_zero_antisymmetry_and_complete_report(
    tiny_report: tuple[Path, dict[str, Any]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path, report = tiny_report
    _, _, own = evidence.replay(ROOT, path)
    crossplay = own["crossplay"]
    lookup = {
        (r["first"], r["second"]): r["seat_balanced_first_chips"] for r in crossplay
    }
    for (first, second), value in lookup.items():
        assert value == -lookup[second, first]
        if first == second:
            assert value == 0
    audit = synthetic_native(path, report, crossplay)
    assert reporting.checked_native(path, report, crossplay, audit) == 0
    for change in ("missing", "duplicate", "number", "nan"):
        bad = copy.deepcopy(audit)
        if change == "missing":
            bad["crossplay"].pop()
        elif change == "duplicate":
            bad["comparisons"].append(bad["comparisons"][-1])
        elif change == "number":
            bad["comparisons"][0]["native_exploitability_chips"] += 1
        else:
            bad["crossplay"][0]["balanced_error_chips"] = float("nan")
        with pytest.raises(ArithmeticError):
            reporting.checked_native(path, report, crossplay, bad)
    audit_path = tmp_path / "native-fixture.json"
    audit_path.write_text(json.dumps(audit))
    monkeypatch.setattr(reporting, "plots", lambda *args: None)
    summary = reporting.render(ROOT, path, audit_path, tmp_path / "report")
    assert summary["own_policies_replayed"] == 20
    assert (
        summary["candidate_development_gate_passed"]
        == report["acceptance"]["candidate_learning_gate_passed"]
    )
    assert len((tmp_path / "report/crossplay.csv").read_text().splitlines()) == 101


def test_native_values_br_crossplay_and_core_checkpoints(
    tiny_report: tuple[Path, dict[str, Any]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pytest.importorskip("pyspiel")
    path, report = tiny_report
    monkeypatch.setattr(native, "source_provenance", fixture_source)
    result = native.audit(
        ROOT, path.parent / "config.json", path, tmp_path / "native.json"
    )
    assert result["status"] == "passed" and len(result["comparisons"]) == 20
    assert (
        len(result["crossplay"]) == 100 and result["checkpoint_receipts_checked"] == 10
    )
    _, _, own = evidence.replay(ROOT, path)
    assert reporting.checked_native(path, report, own["crossplay"], result) <= 1e-9


def test_plot_smoke_all_figures(
    tiny_report: tuple[Path, dict[str, Any]], tmp_path: Path
) -> None:
    pytest.importorskip("matplotlib")
    path, report = tiny_report
    _, _, own = evidence.replay(ROOT, path)
    reporting.plots(
        report, reporting.learning_summary(report), own["crossplay"], tmp_path
    )
    assert {p.name for p in tmp_path.glob("*.png")} == {
        "learning-work.png",
        "full-tree.png",
        "representation-size.png",
        "crossplay.png",
    }
