"""Fictional admission metadata tests; these are not actual hosted CI evidence."""

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from poker_ai.evaluation import averaging_history_protocol as protocol
from poker_ai.evaluation.averaging_history_inputs import inputs
from poker_ai.postflop.learning_artifacts import sha

ROOT = Path(__file__).resolve().parents[1]


def fictional_proof() -> dict[str, Any]:
    return dict(
        status="all_averaging_history_profiles_and_windows_replayed",
        new_postflop_training_performed=False,
        seconds=0.5,
        source_cases=64,
        profiles=512,
        cumulative_boundaries=192,
        suffix_reconstructions=128,
        whole_reconstructions=64,
        identical_current_pairs=160,
        fixed_opponent_target_conditions=2048,
        maximum_error_chips=0.0,
        maximum_error_unitless=0.0,
        maximum_fixed_identity_error_chips=0.0,
    )


def fictional_correctness(
    config: dict[str, Any], source: dict[str, Any]
) -> dict[str, Any]:
    return dict(
        format=protocol.CORRECTNESS,
        status="completed_software_and_forecast_no_new_poker_learning",
        failure=None,
        config=config,
        source=source,
        source_sha256=sha(source["sha256"]),
        new_postflop_training_performed=False,
        software=dict(
            scope="EXPLICIT_SOFTWARE_FIXTURE_NOT_POKER_RESULTS",
            status="passed_software_roundtrip_no_new_poker_training",
            failure=None,
            new_postflop_training_performed=False,
            original_prefix_checks=192,
            fixed_opponent_targets=2048,
            replay=fictional_proof(),
        ),
        forecast=dict(
            decision="fits_requires_checked_admission",
            new_postflop_training_performed=False,
            source_cells=64,
            historical_cell_rows=[dict(FICTIONAL_SCHEMA_INDEX=i) for i in range(64)],
            guarded_own_seconds=1234.0,
            cap_seconds=7200,
        ),
    )


@pytest.fixture
def admission_fixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Any, ...]:
    config = inputs(ROOT)
    source_file = tmp_path / "fixtures/source.py"
    source_file.parent.mkdir()
    source_file.write_text("# EXPLICIT SOFTWARE FIXTURE, not project source\n")
    source = dict(
        dirty=False,
        git_commit="c" * 40,
        sha256={
            "fixtures/source.py": hashlib.sha256(source_file.read_bytes()).hexdigest()
        },
    )
    correctness = fictional_correctness(config, source)
    path = tmp_path / config["correctness_receipt"]
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(correctness))
    monkeypatch.setattr(protocol, "inputs", lambda root: config)
    monkeypatch.setattr(protocol, "source", lambda root: source)
    monkeypatch.setattr(protocol, "load", lambda root: object())
    monkeypatch.setattr(protocol, "forecast", lambda data: correctness["forecast"])
    ci = dict(
        checked_commit=source["git_commit"],
        source_sha256=correctness["source_sha256"],
        run_id=123,
        jobs=dict(protocol.CI_JOBS),
    )
    local = dict(
        source_sha256=correctness["source_sha256"], checks=dict(protocol.LOCAL_CHECKS)
    )
    return tmp_path, config, source, correctness, ci, local


def test_fictional_admission_round_trip_and_read_only_future_module_exception(
    admission_fixture: tuple[Any, ...],
) -> None:
    root, config, source, _, ci, local = admission_fixture
    admitted = protocol.record_admission(root, ci, local)
    path = root / config["admission_receipt"]
    path.write_text(json.dumps(admitted))
    assert protocol.require_admission(root, config) == admitted
    source["sha256"]["fixtures/future.py"] = "0" * 64
    with pytest.raises(ArithmeticError):
        protocol.require_admission(root, config)
    assert protocol.require_admission(root, config, require_clean=False) == admitted


@pytest.mark.parametrize(
    "mode", ["ci", "ci_sha", "commit", "ci_id", "local", "local_sha", "dirty"]
)
def test_incomplete_or_unbound_observed_metadata_cannot_admit(
    admission_fixture: tuple[Any, ...], mode: str
) -> None:
    root, _, source, _, old_ci, old_local = admission_fixture
    ci, local = copy.deepcopy(old_ci), copy.deepcopy(old_local)
    if mode == "ci":
        ci["jobs"].pop("Python 3.12")
    elif mode == "ci_sha":
        ci["source_sha256"] = "0" * 64
    elif mode == "commit":
        ci["checked_commit"] = "0" * 40
    elif mode == "ci_id":
        ci["run_id"] = True
    elif mode == "local":
        local["checks"].pop("slow_integrations")
    elif mode == "local_sha":
        local["source_sha256"] = "0" * 64
    else:
        source["dirty"] = True
    with pytest.raises(ArithmeticError):
        protocol.record_admission(root, ci, local)


@pytest.mark.parametrize(
    "key,value",
    [
        ("profiles", 511),
        ("identical_current_pairs", 160.0),
        ("new_postflop_training_performed", True),
        ("maximum_error_chips", 1.1e-9),
        ("maximum_error_unitless", 2e-11),
        ("seconds", float("nan")),
    ],
)
def test_replay_count_and_unitless_limits_cannot_inherit_chip_tolerance(
    key: str, value: Any
) -> None:
    proof = fictional_proof()
    proof[key] = value
    with pytest.raises(ArithmeticError):
        protocol.validate_replay(proof, inputs(ROOT))


@pytest.mark.parametrize("mode", ["missing", "over_cap", "changed", "source_file"])
def test_forecast_and_actual_source_bindings_are_checked(
    admission_fixture: tuple[Any, ...], monkeypatch: pytest.MonkeyPatch, mode: str
) -> None:
    root, config, _, correctness, ci, local = admission_fixture
    if mode == "missing":
        correctness["forecast"]["historical_cell_rows"].pop()
    elif mode == "over_cap":
        correctness["forecast"]["guarded_own_seconds"] = 7200.0
    elif mode == "changed":
        monkeypatch.setattr(protocol, "forecast", lambda data: {"changed": True})
    else:
        (root / "fixtures/source.py").write_text("# changed after recorded checks\n")
    if mode in ("missing", "over_cap"):
        (root / config["correctness_receipt"]).write_text(json.dumps(correctness))
    with pytest.raises(ArithmeticError):
        protocol.record_admission(root, ci, local)


def test_prefix_runtime_is_strict_for_poker_replay() -> None:
    config = inputs(ROOT)
    protocol.require_prefix_runtime(config, dict(python="3.11.17", numpy="2.4.6"))
    for environment in (
        dict(python="3.12.15", numpy="2.4.6"),
        dict(python="3.11.17", numpy="2.5.4"),
    ):
        with pytest.raises(ArithmeticError):
            protocol.require_prefix_runtime(config, environment)
