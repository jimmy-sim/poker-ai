"""Source/CI/timing gates use explicit synthetic metadata, never invented CI runs."""

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from poker_ai.evaluation import frozen_batch_inputs as inputs
from poker_ai.evaluation import frozen_batch_protocol as protocol
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.learning_run import persist
from poker_ai.postflop.river_study import digest

ROOT = Path(__file__).resolve().parents[1]


def mock_checked_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Isolate admission metadata logic; complete mathematical/IO proof is separate."""
    config = json.loads((ROOT / inputs.CONFIG).read_text())
    file = tmp_path / "EXPLICIT_SOFTWARE_SOURCE.py"
    file.write_text("# fictional gate source\n")
    source = dict(dirty=False, git_commit="f" * 40, sha256={file.name: digest(file)})
    binding = sha(source["sha256"])
    correctness = dict(source=source, source_sha256=binding, config=config)
    persist(tmp_path / protocol.SOFTWARE, correctness)
    monkeypatch.setattr(inputs, "config_inputs", lambda root: config)
    monkeypatch.setattr(inputs, "source", lambda root: copy.deepcopy(source))
    monkeypatch.setattr(protocol, "validate_correctness", lambda *a: None)
    ci = dict(
        checked_commit=source["git_commit"],
        source_sha256=binding,
        run_id=123,
        jobs=copy.deepcopy(protocol.JOBS),
        scope="FICTIONAL_SCHEMA_ONLY_NOT_OBSERVED_CI",
    )
    local = dict(
        source_sha256=binding,
        checks=copy.deepcopy(protocol.LOCAL),
        scope="FICTIONAL_SCHEMA_ONLY_NOT_EXECUTED_CHECKS",
    )
    return config, ci, local


def test_fixed_config_and_inputs_are_byte_bound(tmp_path: Path) -> None:
    config = inputs.config_inputs(ROOT)
    assert len(inputs.paths(config)) == 72
    assert all(p["batch_size"] == 1 for p in inputs.paths(config)[:24])
    (tmp_path / "configs").mkdir()
    for damage in ("seed", "cap", "fixture"):
        changed = copy.deepcopy(config)
        if damage == "seed":
            changed["seeds"][0] += 1
        elif damage == "cap":
            changed["maximum_own_seconds"] = 7201
        else:
            changed["status"] = "EXPLICIT_SOFTWARE_FIXTURE"
        (tmp_path / inputs.CONFIG).write_text(json.dumps(changed))
        with pytest.raises(ArithmeticError, match="protocol bytes"):
            inputs.config_inputs(tmp_path)


def test_code_receipt_binds_actual_supplied_identity_and_is_not_long_admission(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config, ci, local = mock_checked_source(tmp_path, monkeypatch)
    checked = protocol.record_code_checks(tmp_path, ci, local)
    assert checked["status"] == "checked_code_not_long_study_admission"
    persist(tmp_path / protocol.CHECKS, checked)
    assert protocol.require_code_checks(tmp_path, config) == checked
    with pytest.raises(FileNotFoundError):
        protocol.require_admission(tmp_path)


@pytest.mark.parametrize(
    "damage",
    [
        "ci_commit",
        "ci_hash",
        "ci_job",
        "ci_bool",
        "local_hash",
        "local_missing",
        "source_dirty",
        "source_changed",
    ],
)
def test_wrong_observed_check_metadata_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    damage: str,
) -> None:
    _, ci, local = mock_checked_source(tmp_path, monkeypatch)
    if damage == "ci_commit":
        ci["checked_commit"] = "e" * 40
    elif damage == "ci_hash":
        ci["source_sha256"] = "b" * 64
    elif damage == "ci_job":
        ci["jobs"]["Python 3.12"] = "pending"
    elif damage == "ci_bool":
        ci["run_id"] = True
    elif damage == "local_hash":
        local["source_sha256"] = "b" * 64
    elif damage == "local_missing":
        local["checks"].pop("slow_integrations")
    elif damage == "source_dirty":
        monkeypatch.setattr(inputs, "source", lambda root: dict(dirty=True, sha256={}))
    elif damage == "source_changed":
        # A different complete inventory must not reuse the old checked proof.
        monkeypatch.setattr(
            inputs,
            "source",
            lambda root: dict(dirty=False, sha256={"DIFFERENT": "b" * 64}),
        )
    with pytest.raises((ArithmeticError, ValueError)):
        protocol.record_code_checks(tmp_path, ci, local)


def admitted_fixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, guarded: float
) -> tuple[dict[str, Any], dict[str, Any]]:
    config, ci, local = mock_checked_source(tmp_path, monkeypatch)
    checked = protocol.record_code_checks(tmp_path, ci, local)
    persist(tmp_path / protocol.CHECKS, checked)
    profile = dict(
        source=inputs.source(tmp_path),
        source_sha256=checked["source_sha256"],
        forecast=dict(
            guarded_own_seconds=guarded,
            decision="fits_requires_checked_admission"
            if guarded < 7200
            else "exceeds_cap_stop_before_long_learning",
        ),
    )
    persist(tmp_path / protocol.TIMING, profile)
    monkeypatch.setattr(protocol, "read_profile", lambda *a: copy.deepcopy(profile))
    return config, profile


@pytest.mark.parametrize("guarded", [7200.0, 7200.01, 10000.0])
def test_failed_or_equal_cap_never_admits_long_learning(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, guarded: float
) -> None:
    admitted_fixture(tmp_path, monkeypatch, guarded)
    with pytest.raises(ArithmeticError, match="compute gate"):
        protocol.record_admission(tmp_path)
    assert not (tmp_path / protocol.ADMITTED).exists()


def test_all_receipts_are_required_and_hash_bound(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    admitted_fixture(tmp_path, monkeypatch, 7000.0)
    admitted = protocol.record_admission(tmp_path)
    persist(tmp_path / protocol.ADMITTED, admitted)
    assert protocol.require_admission(tmp_path) == admitted
    changed = json.loads((tmp_path / protocol.TIMING).read_text())
    changed["altered"] = True
    persist(tmp_path / protocol.TIMING, changed)
    with pytest.raises(ArithmeticError):
        protocol.require_admission(tmp_path)


def test_failed_correctness_attempt_is_retained(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    mock_checked_source(tmp_path, monkeypatch)

    def fail() -> Any:
        raise ArithmeticError("EXPLICIT_TEST_MATH_FAILURE")

    monkeypatch.setattr(protocol, "proofs", fail)
    output = tmp_path / "failed/correctness.json"
    with pytest.raises(ArithmeticError):
        protocol.run_correctness(tmp_path, output)
    saved = json.loads(output.read_text())
    assert (
        saved["status"] == "incomplete"
        and saved["failure"]["reason"] == "EXPLICIT_TEST_MATH_FAILURE"
    )
    assert saved["new_postflop_training_performed"] is False
    with pytest.raises(FileExistsError):
        protocol.run_correctness(tmp_path, output)


@pytest.mark.slow
def test_actual_source_bound_complete_software_receipt_roundtrip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = json.loads((ROOT / inputs.CONFIG).read_text())
    marker = tmp_path / "EXPLICIT_SOFTWARE_SOURCE.py"
    marker.write_text("# explicit source binding fixture\n")
    source = dict(
        dirty=False, git_commit="f" * 40, sha256={marker.name: digest(marker)}
    )
    monkeypatch.setattr(inputs, "config_inputs", lambda root: config)
    monkeypatch.setattr(inputs, "source", lambda root: source)
    output = tmp_path / "actual-software.json"
    saved = protocol.run_correctness(tmp_path, output)
    protocol.validate_correctness(tmp_path, saved, config)
    assert len(saved["math"]) == 4 and len(saved["parity"]) == 120
    assert saved["software"]["replay"]["profiles"] == 480
    for key, value in [("status", "incomplete"), ("seconds", float("nan"))]:
        changed = copy.deepcopy(saved)
        changed[key] = value
        with pytest.raises(ArithmeticError):
            protocol.validate_correctness(tmp_path, changed, config)
    changed = copy.deepcopy(saved)
    changed["software"]["replay"]["mass_reconstructions"] = 431
    with pytest.raises(ArithmeticError):
        protocol.validate_correctness(tmp_path, changed, config)
    marker.write_text("# changed after source capture\n")
    with pytest.raises(ArithmeticError):
        protocol.validate_correctness(tmp_path, saved, config)
