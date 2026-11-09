"""Preflight and retained failure boundaries, without any new Hold'em scoring."""

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from poker_ai.evaluation import window_fallback_run as own
from poker_ai.evaluation.window_fallback_inputs import inputs
from poker_ai.evaluation.window_fallback_validation import FORMAT
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.river_study import Deadline, digest
from poker_ai.solver_validation import window_fallback as native

ROOT = Path(__file__).resolve().parents[1]


def forbidden(*args: Any, **kwargs: Any) -> None:
    raise AssertionError("gate did not stop downstream work")


@pytest.mark.parametrize(
    "name", ["own.json", "own.tmp", "own-profiles.jsonl.gz", "own-profiles.jsonl.tmp"]
)
def test_any_prior_receipt_or_archive_blocks_preflight(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    path = tmp_path / name
    path.write_bytes(b"EXPLICIT_RETAINED_FIXTURE")
    monkeypatch.setattr(own, "inputs", forbidden)
    with pytest.raises(FileExistsError):
        own.run(ROOT, tmp_path / "own.json")
    assert path.read_bytes() == b"EXPLICIT_RETAINED_FIXTURE"


def test_unpublished_source_cannot_load_any_old_or_new_policy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(own, "source", lambda root: dict(dirty=True))
    monkeypatch.setattr(own, "load", forbidden)
    with pytest.raises(ValueError, match="publish checked"):
        own.run(ROOT, tmp_path / "own.json")
    assert not (tmp_path / "own.json").exists()


def fail(*args: Any, **kwargs: Any) -> None:
    raise TimeoutError("EXPLICIT_SOFTWARE_FIXTURE_INPUT_TIMEOUT")


def test_failed_own_input_replay_is_retained_and_not_overwritten(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        own,
        "source",
        lambda root: dict(dirty=False, sha256={"EXPLICIT_FIXTURE": "f" * 64}),
    )
    monkeypatch.setattr(own, "load", fail)
    path = tmp_path / "own.json"
    with pytest.raises(TimeoutError):
        own.run(ROOT, path)
    before = path.read_bytes()
    saved = json.loads(before)
    assert saved["status"] == "incomplete"
    assert saved["failure"]["type"] == "TimeoutError"
    assert saved["upstream_replay"] is saved["own_replay"] is None
    assert saved["rows"] == saved["panels"] == saved["fixed_matches"] == []
    assert Path(saved["scratch"]).exists()
    with pytest.raises(FileExistsError):
        own.run(ROOT, path)
    assert path.read_bytes() == before


def test_native_requires_own_publication_before_reading(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(own, "source", lambda root: dict(dirty=True))
    monkeypatch.setattr(own, "replay", forbidden)
    with pytest.raises(ValueError, match="publish complete own"):
        native.run(ROOT, tmp_path / "missing.json", tmp_path / "native.json")
    assert not (tmp_path / "native.json").exists()


def test_failed_native_input_replay_retained_before_any_reference_construction(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = dict(dirty=False, sha256={"EXPLICIT_FIXTURE": "f" * 64})
    monkeypatch.setattr(own, "source", lambda root: source)
    monkeypatch.setattr(own, "replay", fail)
    monkeypatch.setattr(native, "references", forbidden)
    path = tmp_path / "own.json"
    output = tmp_path / "native.json"
    path.write_text(
        json.dumps(dict(source_sha256=sha(source["sha256"]), details_sha256="a" * 64))
    )
    with pytest.raises(TimeoutError):
        native.run(ROOT, path, output)
    before = output.read_bytes()
    saved = json.loads(before)
    assert saved["status"] == "incomplete"
    assert saved["failure"]["type"] == "TimeoutError"
    assert saved["own_replay"] is None
    assert saved["self_comparisons"] == saved["fixed_comparisons"] == []
    assert saved["license"] is None
    with pytest.raises(FileExistsError):
        native.run(ROOT, path, output)
    assert output.read_bytes() == before


@pytest.mark.parametrize(
    "mode",
    [
        "partial",
        "failure",
        "training",
        "reference",
        "cap",
        "nan",
        "source",
        "input_hash",
        "proof_count",
        "proof_unitless",
    ],
)
def test_changed_own_headers_fail_before_loading_inputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str
) -> None:
    config = inputs(ROOT)
    source = dict(dirty=False, sha256={"EXPLICIT_HEADER_ONLY": "f" * 64})
    proof = dict(
        status="all_window_fallback_profiles_and_targets_replayed",
        new_postflop_training_performed=False,
        source_windows=128,
        profiles=512,
        raw_window_controls=128,
        full_windows=32,
        additivity_panels=128,
        fixed_target_conditions=2048,
        maximum_error_chips=0.0,
        maximum_error_unitless=0.0,
        maximum_full_control_error_chips=0.0,
        maximum_full_realization_change=0.0,
        seconds=0.1,
    )
    saved: dict[str, Any] = dict(
        format=FORMAT,
        status="completed_own_native_pending",
        failure=None,
        config=config,
        training_performed=False,
        reference_output_used_in_training=False,
        seconds=10.0,
        source=source,
        source_sha256=sha(source["sha256"]),
        source_report_sha256=digest(ROOT / config["source_report"]),
        own_replay=proof,
    )
    saved = copy.deepcopy(saved)
    if mode == "partial":
        saved["status"] = "incomplete"
    elif mode == "failure":
        saved["failure"] = {"reason": "EXPLICIT_FIXTURE"}
    elif mode == "training":
        saved["training_performed"] = True
    elif mode == "reference":
        saved["reference_output_used_in_training"] = True
    elif mode == "cap":
        saved["seconds"] = 900.0
    elif mode == "nan":
        saved["seconds"] = float("nan")
    elif mode == "source":
        saved["source_sha256"] = "0" * 64
    elif mode == "input_hash":
        saved["source_report_sha256"] = "0" * 64
    elif mode == "proof_count":
        saved["own_replay"]["profiles"] = 511
    else:
        saved["own_replay"]["maximum_error_unitless"] = 2e-11
    monkeypatch.setattr(own, "load", forbidden)
    monkeypatch.setattr(own, "check_source", lambda *args: None)
    path = tmp_path / "EXPLICIT_HEADER_NOT_RESEARCH.json"
    path.write_text(json.dumps(saved))
    with pytest.raises(ArithmeticError):
        own.read_saved(ROOT, path, Deadline(900))


def test_actual_old_native_scalar_records_fit_the_new_noop_panel_adapter() -> None:
    """Use pinned past reference scalars, not fabricated or newly trained output."""
    config = inputs(ROOT)
    old = json.loads((ROOT / config["source_native"]).read_text())
    source = old["self_comparisons"][0]
    rows = [
        dict(source, index=0, order=order, id=f"EXPLICIT_NOOP_{order}")
        for order in range(4)
    ]
    result = native.panel(rows)
    assert result["maximum_error_chips"] <= 1e-9
    assert result["baseline_ev_interaction_chips"] == 0
