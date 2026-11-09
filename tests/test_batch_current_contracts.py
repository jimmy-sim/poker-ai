"""Source/CI/admission and retained failure contracts, explicitly fictional metadata."""

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from poker_ai.evaluation import batch_current_inputs as inputs
from poker_ai.evaluation import batch_current_protocol as protocol
from poker_ai.evaluation import batch_current_run as own
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.learning_run import persist
from poker_ai.postflop.river_study import digest
from poker_ai.solver_validation import batch_currents as native

ROOT = Path(__file__).resolve().parents[1]


def mock_gate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[dict[str, Any], dict[str, Any]]:
    marker = tmp_path / "EXPLICIT_SOURCE.py"
    marker.write_text("# fictional metadata only\n")
    source = dict(
        git_commit="e" * 40,
        dirty=False,
        git_status=[],
        sha256={marker.name: digest(marker)},
    )
    config = copy.deepcopy(inputs.config_inputs(ROOT))
    config["status"] = "EXPLICIT_SCHEMA_NOT_SCIENTIFIC_EVIDENCE"
    monkeypatch.setattr(inputs, "source", lambda root: copy.deepcopy(source))
    monkeypatch.setattr(inputs, "config_inputs", lambda root: config)

    def checked(root: Path, commit: Any, hashes: Any) -> dict[str, Any]:
        if commit != source["git_commit"] or hashes != source["sha256"]:
            raise ArithmeticError("fictional identity mismatch")
        return copy.deepcopy(source)

    monkeypatch.setattr(protocol, "checked_tree", checked)
    ci = dict(
        checked_commit=source["git_commit"],
        source_sha256=sha(source["sha256"]),
        run_id=123,
        jobs=protocol.JOBS,
        scope="FICTIONAL_NOT_OBSERVED",
    )
    local = dict(
        source_sha256=sha(source["sha256"]),
        checks=protocol.LOCAL,
        scope="FICTIONAL_NOT_EXECUTED",
    )
    persist(tmp_path / inputs.CONFIG, config)
    return ci, local


def test_fixed_protocol_does_not_accept_fixture_or_changed_caps(tmp_path: Path) -> None:
    original = inputs.config_inputs(ROOT)
    for key, value in [
        ("maximum_own_seconds", 3601),
        ("maximum_native_seconds", 901),
        ("status", "EXPLICIT_SOFTWARE"),
    ]:
        c = copy.deepcopy(original)
        c[key] = value
        persist(tmp_path / inputs.CONFIG, c)
        with pytest.raises(ArithmeticError):
            inputs.config_inputs(tmp_path)


@pytest.mark.parametrize("field", ["checked_commit", "source_sha256", "run_id", "jobs"])
def test_wrong_observed_metadata_is_not_a_code_gate(
    field: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ci, local = mock_gate(tmp_path, monkeypatch)
    ci[field] = None
    with pytest.raises(ArithmeticError):
        protocol.record_checks(tmp_path, ci, local)


def test_code_gate_without_complete_source_study_cannot_admit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ci, local = mock_gate(tmp_path, monkeypatch)
    persist(tmp_path / inputs.CHECKS, protocol.record_checks(tmp_path, ci, local))
    assert (
        protocol.require_checks(tmp_path)["status"]
        == "checked_code_not_scoring_admission"
    )

    def missing(root: Path) -> Any:
        raise FileNotFoundError("incomplete source own/native study")

    monkeypatch.setattr(inputs, "load", missing)
    with pytest.raises(FileNotFoundError):
        protocol.record_admission(tmp_path)


def test_admission_binds_every_source_byte_not_just_status(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ci, local = mock_gate(tmp_path, monkeypatch)
    persist(tmp_path / inputs.CHECKS, protocol.record_checks(tmp_path, ci, local))
    sourcefile = tmp_path / "EXPLICIT_SOURCE_DATA.json"
    persist(sourcefile, dict(scope="FICTIONAL_ONLY"))
    monkeypatch.setattr(inputs, "load", lambda root: None)
    monkeypatch.setattr(
        inputs,
        "source_hashes",
        lambda root, sources: {sourcefile.name: digest(sourcefile)},
    )
    admitted = protocol.record_admission(tmp_path)
    persist(tmp_path / inputs.ADMITTED, admitted)
    assert protocol.require_admission(tmp_path) == admitted
    persist(sourcefile, dict(scope="CHANGED_FICTIONAL_BYTES"))
    with pytest.raises(ArithmeticError):
        protocol.require_admission(tmp_path)


@pytest.mark.parametrize("after_start", [False, True])
def test_failed_own_attempt_retains_actual_partial_counts(
    after_start: bool, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    mock_gate(tmp_path, monkeypatch)
    monkeypatch.setattr(
        protocol, "require_admission", lambda *a, **k: {"scope": "FICTIONAL_GATE"}
    )
    if not after_start:

        def fail(root: Path) -> Any:
            raise ArithmeticError("injected before scoring")

        monkeypatch.setattr(inputs, "load", fail)
    else:
        source = type(
            "FictionalSource", (), {"own": {"config": {"native_reference": {}}}}
        )()
        monkeypatch.setattr(inputs, "load", lambda root: source)
        monkeypatch.setattr(inputs, "source_hashes", lambda *a: {})

        def partial(*args: Any) -> None:
            args[-1].update(
                status="incomplete",
                workers=[
                    dict(
                        messages=[
                            dict(
                                kind="cell",
                                phase="profile",
                                row={"scope": "FICTIONAL_PARTIAL"},
                            )
                        ]
                    )
                ],
            )
            raise TimeoutError("injected after scoring")

        monkeypatch.setattr(own, "run_batch", partial)
    path = tmp_path / "attempt/own.json"
    with pytest.raises((ArithmeticError, TimeoutError)):
        own.run(tmp_path, path)
    saved = json.loads(path.read_text())
    assert saved["status"] == "incomplete" and saved["training_performed"] is False
    assert (
        saved["completed_current_profiles"] == int(after_start)
        and saved["completed_fixed_targets"] == 0
    )
    with pytest.raises(FileExistsError):
        own.run(tmp_path, path)


def test_native_failure_before_reference_is_retained(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    mock_gate(tmp_path, monkeypatch)
    path = tmp_path / "EXPLICIT_OWN.json"
    persist(path, dict(scope="FICTIONAL_SOURCE_ONLY"))

    def fail(*a: Any) -> Any:
        raise ArithmeticError("injected own replay failure")

    monkeypatch.setattr(native, "replay", fail)
    output = tmp_path / "native.json"
    with pytest.raises(ArithmeticError, match="injected"):
        native.run(tmp_path, path, output)
    saved = json.loads(output.read_text())
    assert (
        saved["status"] == "incomplete"
        and saved["reference_setup_started"] is False
        and saved["reference_setup_completed_workers"] == 0
    )
    assert saved["training_performed"] is False
    with pytest.raises(FileExistsError):
        native.run(tmp_path, path, output)


def test_native_partial_reference_attempt_is_not_reported_as_no_work(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    profile = dict(
        scope="FICTIONAL_PARTIAL_ONLY",
        details_sha256="a" * 64,
        reference=inputs.config_inputs(ROOT)["native_reference"],
    )
    path = tmp_path / "FICTIONAL_OWN.json"
    persist(path, profile)
    saved = dict(
        license=dict(scope="FICTIONAL_LICENSE_ONLY"),
        own_replay=dict(scope="FICTIONAL_PARTIAL_PROOF"),
    )
    mock_gate(tmp_path, monkeypatch)
    monkeypatch.setattr(
        native, "replay", lambda *a: (profile, None, saved["own_replay"])
    )
    monkeypatch.setattr(native, "license_record", lambda config: saved["license"])

    def partial(*args: Any) -> None:
        args[-1].update(
            status="incomplete",
            workers=[
                dict(messages=[dict(kind="prepared", phase="reference_setup_started")])
            ],
        )
        raise TimeoutError("injected after reference setup began")

    monkeypatch.setattr(native, "run_batch", partial)
    output = tmp_path / "partial-native.json"
    with pytest.raises(TimeoutError):
        native.run(tmp_path, path, output)
    result = json.loads(output.read_text())
    assert (
        result["reference_setup_started"] is True
        and result["reference_setup_completed_workers"] == 0
    )
    assert result["status"] == "incomplete"
