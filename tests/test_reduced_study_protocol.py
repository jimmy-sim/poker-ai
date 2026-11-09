"""Conditional gates with synthetic metadata, never invented observed CI/results."""

import copy
from pathlib import Path
from typing import Any

import pytest

from poker_ai.evaluation import reduced_study_inputs as inputs
from poker_ai.evaluation import reduced_study_protocol as protocol
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.learning_run import persist
from poker_ai.postflop.river_study import digest

ROOT = Path(__file__).resolve().parents[1]


def fixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[dict[str, Any], dict[str, Any]]:
    c = inputs.config_inputs(ROOT)
    p = inputs.protocol(ROOT)
    marker = tmp_path / "EXPLICIT_FICTIONAL_SOURCE.py"
    marker.write_text("# fictional contract only\n")
    source = dict(
        dirty=False, git_commit="e" * 40, sha256={marker.name: digest(marker)}
    )
    h = sha(source["sha256"])
    proof = dict(source=source, source_sha256=h)
    persist(tmp_path / inputs.SOFTWARE, proof)
    monkeypatch.setattr(inputs, "config_inputs", lambda root: c)
    monkeypatch.setattr(inputs, "protocol", lambda root: p)
    monkeypatch.setattr(inputs, "source", lambda root: copy.deepcopy(source))
    monkeypatch.setattr(protocol, "validate_correctness", lambda *a: None)
    ci = dict(
        checked_commit=source["git_commit"],
        source_sha256=h,
        run_id=123,
        jobs=protocol.JOBS,
        scope="FICTIONAL_NOT_OBSERVED",
    )
    local = dict(source_sha256=h, checks=protocol.LOCAL, scope="FICTIONAL_NOT_EXECUTED")
    return ci, local


def test_fixed_protocol_cannot_change_seeds_caps_or_scope(tmp_path: Path) -> None:
    assert len(inputs.paths(inputs.config_inputs(ROOT))) == 72
    p = inputs.protocol(ROOT)
    p["maximum_own_seconds"] = 7201
    persist(tmp_path / inputs.CONFIG, p)
    with pytest.raises(ArithmeticError, match="protocol"):
        inputs.protocol(tmp_path)


@pytest.mark.parametrize("field", ["checked_commit", "source_sha256", "jobs", "run_id"])
def test_exact_observed_code_checks_required(
    field: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ci, local = fixture(tmp_path, monkeypatch)
    ci[field] = None
    with pytest.raises(ArithmeticError):
        protocol.record_code_checks(tmp_path, ci, local)


def test_code_gate_is_not_long_admission(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ci, local = fixture(tmp_path, monkeypatch)
    checked = protocol.record_code_checks(tmp_path, ci, local)
    persist(tmp_path / inputs.CHECKS, checked)
    assert protocol.require_code_checks(tmp_path) == checked
    with pytest.raises(FileNotFoundError):
        protocol.require_admission(tmp_path)


def prepare_admission(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, decision: str, guarded: float
) -> None:
    ci, local = fixture(tmp_path, monkeypatch)
    persist(tmp_path / inputs.CHECKS, protocol.record_code_checks(tmp_path, ci, local))
    p = inputs.protocol(tmp_path)
    for n in (
        "reduction_correctness",
        "reduction_profile",
        "reduction_code_checks",
        "reduction_config",
        "base_config",
    ):
        persist(tmp_path / p[n], dict(scope="FICTIONAL_GATE_BYTES"))
    persist(tmp_path / inputs.CONFIG, p)

    def fake(root: Path, path: Path) -> dict[str, Any]:
        return dict(
            scope="FICTIONAL_SCHEMA_ONLY",
            kind="correctness" if path.name == "correctness.json" else "profile",
            source=inputs.source(tmp_path),
            forecast=dict(decision=decision, guarded_own_seconds=guarded),
        )

    monkeypatch.setattr(protocol, "replay_reduction", fake)


@pytest.mark.parametrize(
    "decision,guarded",
    [
        ("exceeds_cap_stop_before_long_learning", 7201.492438541833),
        ("fits_requires_checked_admission", 7200.0),
        ("fits_requires_checked_admission", float("nan")),
        ("fits_requires_checked_admission", 0.0),
    ],
)
def test_failed_or_nonfinite_compute_gate_never_admits(
    decision: str, guarded: float, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    prepare_admission(tmp_path, monkeypatch, decision, guarded)
    with pytest.raises(ArithmeticError, match="compute gate"):
        protocol.record_admission(tmp_path)


def test_admission_pins_every_prerequisite_byte_and_can_expire(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    prepare_admission(tmp_path, monkeypatch, "fits_requires_checked_admission", 6000.0)
    saved = protocol.record_admission(tmp_path)
    persist(tmp_path / inputs.ADMITTED, saved)
    assert protocol.require_admission(tmp_path) == saved
    p = inputs.protocol(tmp_path)
    persist(
        tmp_path / p["reduction_code_checks"], dict(scope="CHANGED_FICTIONAL_BYTES")
    )
    with pytest.raises(ArithmeticError, match="admission changed"):
        protocol.require_admission(tmp_path)


def test_explicit_factory_is_the_checked_reduction_backend() -> None:
    from poker_ai.postflop.batch_reduction import ReducedDispatchBatchTrainer
    from poker_ai.postflop.training_isolation import sentinel_tree

    path = inputs.paths(inputs.config_inputs(ROOT))[0]
    assert type(inputs.trainer(sentinel_tree(), path)) is ReducedDispatchBatchTrainer


@pytest.mark.slow
def test_actual_source_bound_complete_toy_proof_roundtrip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from unittest.mock import patch

    from poker_ai.postflop.controlled_training import ControlledTrainer
    from poker_ai.solver_validation.reference import Reference

    source = inputs.source(ROOT)
    source["dirty"] = False
    monkeypatch.setattr(inputs, "binding", lambda root: (source, sha(source["sha256"])))
    output = tmp_path / "software.json"
    saved = protocol.run_correctness(ROOT, output)
    assert saved["status"] == "passed_explicit_backend_toy_IO_no_postflop_learning"
    with (
        patch.object(
            ControlledTrainer,
            "__init__",
            side_effect=AssertionError("reader learner forbidden"),
        ),
        patch.object(
            Reference, "__init__", side_effect=AssertionError("reader native forbidden")
        ),
    ):
        protocol.validate_correctness(ROOT, saved, inputs.config_inputs(ROOT))
    changed = copy.deepcopy(saved)
    changed["software"]["replay"]["mass_reconstructions"] = 431
    with pytest.raises(ArithmeticError):
        protocol.validate_correctness(ROOT, changed, inputs.config_inputs(ROOT))
