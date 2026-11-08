"""Software fixtures for replay integrity, not evidence about agent strength."""

import copy
import gzip
import json
import shutil
from pathlib import Path
from typing import Any

import pytest

from poker_ai.postflop import range_admission as admission
from poker_ai.postflop import range_admission_report as reporting
from poker_ai.postflop.learning import full_solver
from poker_ai.postflop.matrix import MatrixTree
from poker_ai.postflop.river_study import Deadline, digest
from poker_ai.solver_validation import range_admission as native

ROOT = Path(__file__).resolve().parents[1]


def fixture_source(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return {"dirty": False, "sha256": {}, "git_commit": "software-fixture-not-research"}


def fixture_solver(tree: MatrixTree, backend: str) -> Any:
    assert backend == "fused_numba"
    # Only the software fixture uses NumPy, including base-only CI. Production
    # retains the unchanged fused backend, with no CLI/backend override.
    return full_solver(tree, "numpy")


@pytest.fixture(scope="module")
def tiny(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, dict[str, Any]]:
    directory = tmp_path_factory.mktemp("range-admission-fixture")
    config = json.loads((ROOT / "configs/range-mass-protocol.json").read_text())
    config.update(spot_files=config["spot_files"][:1], full_tree_checkpoints=[1, 2])
    config["spot_sha256"] = {p: config["spot_sha256"][p] for p in config["spot_files"]}
    cfg = directory / "config.json"
    cfg.write_text(json.dumps(config))
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(admission, "source_provenance", fixture_source)
        patch.setattr(admission, "full_solver", fixture_solver)
        report = admission.run_admission(ROOT, cfg, directory / "study.json")
    assert report["status"] == "completed", report["failure"]
    return directory / "study.json", report


def test_complete_negative_fixture_replays_without_native_or_global_claim(
    tiny: tuple[Path, dict[str, Any]],
) -> None:
    path, _ = tiny
    report, policies, error = admission.replay(ROOT, path)
    assert len(policies) == 10 and error == 0
    assert report["acceptance"]["own_grid_complete"]
    assert not report["acceptance"]["complete"]
    assert not report["acceptance"]["eligible_for_sampled_comparison"]
    assert report["acceptance"]["independent_audit"] == "pending"
    assert report["sampled_learning"] == "not_run"
    assert report["fresh_global_admission"] is False
    assert any(not c["passed"] for c in report["acceptance"]["checks"])
    with pytest.raises(FileExistsError):
        admission.run_admission(ROOT, path.parent / "config.json", path)


def duplicate_fixture(
    tiny: tuple[Path, dict[str, Any]], directory: Path
) -> tuple[Path, dict[str, Any]]:
    original, raw = tiny
    report = copy.deepcopy(raw)
    shutil.copyfile(
        original.parent / raw["own_policies_file"], directory / raw["own_policies_file"]
    )
    return directory / "study.json", report


@pytest.mark.parametrize(
    "change",
    [
        "missing",
        "duplicate",
        "work",
        "diagnostic",
        "global",
        "sampled",
        "context",
        "row_context",
        "diag_context",
        "status",
        "nan",
        "source",
        "model",
    ],
)
def test_changed_receipts_rejected(
    tiny: tuple[Path, dict[str, Any]],
    tmp_path: Path,
    change: str,
) -> None:
    path, report = duplicate_fixture(tiny, tmp_path)
    if change == "missing":
        report["rows"].pop()
    elif change == "duplicate":
        report["rows"].append(report["rows"][-1])
    elif change == "work":
        report["rows"][0]["total_node_work"] += 1
    elif change == "diagnostic":
        report["diagnostics"][0]["key_utf8_bytes"] += 1
    elif change == "global":
        report["fresh_global_admission"] = True
    elif change == "sampled":
        report["sampled_learning"] = "passed"
    elif change == "context":
        report["range_contexts"][report["config"]["spot_files"][0]] = "wrong"
    elif change == "row_context":
        report["rows"][-1]["range_context_sha256"] = "wrong"
    elif change == "diag_context":
        report["diagnostics"][-1]["range_context_sha256"] = "wrong"
    elif change == "status":
        report["status"] = "incomplete"
    elif change == "nan":
        report["rows"][0]["value_player_zero_chips"] = float("nan")
    elif change == "source":
        report["source"]["sha256"]["uv.lock"] = "wrong"
    else:
        report["model_sha256"] = "wrong"
    # Update derived assessment as an attacker might: replay must verify raw facts.
    if change not in ("nan", "row_context", "diag_context", "context"):
        report["acceptance"] = admission.acceptance(
            report["rows"],
            report["diagnostics"],
            report["config"],
            report["range_contexts"],
            report["seconds"],
        )
    path.write_text(json.dumps(report))
    with pytest.raises((ArithmeticError, ValueError)):
        admission.replay(ROOT, path)


@pytest.mark.parametrize(
    "change",
    [
        "hash",
        "missing",
        "duplicate",
        "context",
        "active",
        "shape",
        "policy",
        "value",
    ],
)
def test_changed_own_policy_rejected(
    tiny: tuple[Path, dict[str, Any]],
    tmp_path: Path,
    change: str,
) -> None:
    path, report = duplicate_fixture(tiny, tmp_path)
    policies_path = path.parent / report["own_policies_file"]
    payload = json.loads(gzip.decompress(policies_path.read_bytes()))
    snapshot = payload["policies"][-1]
    if change == "missing":
        payload["policies"].pop()
    elif change == "duplicate":
        payload["policies"].append(snapshot)
    elif change == "context":
        snapshot["range_context_sha256"] = "wrong"
    elif change == "active":
        snapshot["average_active"][0] = 2
    elif change == "shape":
        snapshot["average_active"].pop()
    elif change == "policy":
        snapshot["policy"][0] = [1.0]  # Wrong legal menu.
    elif change == "value":
        report["rows"][-1]["value_player_zero_chips"] += 1
    else:
        snapshot["average_active"][0] = 2
    policies_path.write_bytes(gzip.compress(json.dumps(payload).encode(), mtime=0))
    if change != "hash":
        report["own_policies_sha256"] = digest(policies_path)
    path.write_text(json.dumps(report))
    with pytest.raises((ArithmeticError, ValueError)):
        admission.replay(ROOT, path)


def test_deadline_retains_partial_evidence(
    tiny: tuple[Path, dict[str, Any]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(admission, "source_provenance", fixture_source)

    def expired(*args: Any) -> None:
        raise TimeoutError("software fixture deadline")

    monkeypatch.setattr(Deadline, "check", expired)
    result = admission.run_admission(
        ROOT, tiny[0].parent / "config.json", tmp_path / "partial.json"
    )
    assert result["status"] == "incomplete" and not result["rows"]
    assert result["failure"]["type"] == "TimeoutError"
    with pytest.raises(ValueError):
        admission.replay(ROOT, tmp_path / "partial.json")


def test_native_and_offline_report(
    tiny: tuple[Path, dict[str, Any]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pytest.importorskip("pyspiel")
    path, report = tiny
    monkeypatch.setattr(native, "source_provenance", fixture_source)
    audit_path = tmp_path / "audit.json"
    result = native.audit(ROOT, path.parent / "config.json", path, audit_path)
    assert result["status"] == "passed" and len(result["comparisons"]) == 10
    assert reporting.checked_audit(path, report, result) <= 1e-9
    for mutation in ("duplicate", "context", "native_value", "error", "input"):
        bad = copy.deepcopy(result)
        if mutation == "duplicate":
            bad["comparisons"].append(bad["comparisons"][-1])
        elif mutation == "context":
            bad["comparisons"][-1]["range_context_sha256"] = "wrong"
        elif mutation == "native_value":
            bad["comparisons"][-1]["native_value_chips"] += 1
        elif mutation == "error":
            bad["comparisons"][-1]["value_error_chips"] = -1
        else:
            bad["input_sha256"] = "wrong"
        with pytest.raises(ArithmeticError):
            reporting.checked_audit(path, report, bad)
    monkeypatch.setattr(reporting, "plots", lambda *a: None)
    summary = reporting.render(ROOT, path, audit_path, tmp_path / "report")
    assert summary["acceptance"]["complete"]
    assert not summary["full_control_admission_passed"]
    assert summary["sampled_learning"] == "not_run"
    assert summary["fresh_global_admission"] is False


def test_plot_smoke(tiny: tuple[Path, dict[str, Any]], tmp_path: Path) -> None:
    pytest.importorskip("matplotlib")
    reporting.plots(tiny[1], tmp_path)
    assert {p.name for p in tmp_path.glob("*.png")} == {
        "full-controls.png",
        "row-counts.png",
    }
