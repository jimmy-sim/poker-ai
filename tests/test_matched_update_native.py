"""Complete explicit tiny scalar audit and strict partial/schema failures."""

import copy
import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from poker_ai.evaluation.averaging_history_software import toy_context
from poker_ai.evaluation.matched_update_inputs import config_inputs
from poker_ai.evaluation.matched_update_software import exercise
from poker_ai.evaluation.matched_update_software_inputs import SCOPE, build
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.river_study import Deadline, digest
from poker_ai.solver_validation.controlled_pipeline import license_record
from poker_ai.solver_validation.matched_array_reference import ScalarReference
from poker_ai.solver_validation.matched_update_audit import audit_rows
from poker_ai.solver_validation.matched_updates import FORMAT, audit, validate

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def corpus(
    tmp_path_factory: pytest.TempPathFactory,
) -> tuple[dict[str, Any], dict[str, Any], Path]:
    pytest.importorskip("pyspiel")
    license_record(dict(native_reference=config_inputs(ROOT)["reference"]))
    folder = tmp_path_factory.mktemp("EXPLICIT-native-fixture")
    path = folder / "own.json"
    fixture = build("a" * 64, Deadline(30))
    own = dict(
        scope=SCOPE,
        source_sha256="a" * 64,
        scratch=str(folder / "scratch"),
        captures=[],
        masses=[],
        checkpoints=[],
        rows=[],
        fixed_matches=[],
        self_pairs=[],
        fixed_pairs=[],
    )
    exercise(path, own, fixture, Deadline(30))
    path.write_text(json.dumps(own))
    reference = ScalarReference(toy_context().partition)
    events: list[dict[str, Any]] = []

    def opponent(peer: dict[str, Any]) -> Any:
        policy, replies = fixture.controls[peer["opponent_profile_id"]]
        return policy, replies[peer["target"]]

    summary = audit_rows(
        path,
        own,
        list(range(24)),
        lambda _: toy_context(),
        {i: (reference, reference) for i in range(24)},
        opponent,
        events.append,
        Deadline(30),
    )
    source = dict(sha256={"EXPLICIT-fixture": "a" * 64})
    saved = dict(
        format=FORMAT,
        scope=SCOPE,
        status="completed",
        failure=None,
        own_sha256=digest(path),
        details_sha256=own["details_sha256"],
        source=source,
        source_sha256=sha(source["sha256"]),
        publication=dict(own_sha256=digest(path)),
        reference_setup_started=True,
        reference_setup_completed=True,
        training_performed=False,
        reference_actions_exported=False,
        reference_output_used_in_training=False,
        long_run_admitted=False,
        rows=[e["result"] for e in events if e["phase"] == "self"],
        fixed=[e["result"] for e in events if e["phase"] == "fixed"],
        completed_profiles=144,
        completed_fixed_targets=1152,
        seconds=1.0,
        maximum_error_chips=summary["maximum_error_chips"],
        batch={},
        summary=summary,
    )
    return own, saved, path


def test_all144_profiles_and1152_fixed_native_targets(
    corpus: tuple[dict[str, Any], dict[str, Any], Path],
) -> None:
    own, saved, path = corpus
    proof = validate(saved, own, path)
    assert proof["profiles"] == 144 and proof["fixed_targets"] == 1152
    assert proof["maximum_error_chips"] < 1e-12
    assert proof["reference_actions_exported"] is False
    assert proof["long_run_admitted"] is False


@pytest.mark.parametrize(
    "kind",
    [
        "missing_profile",
        "duplicate_profile",
        "missing_fixed",
        "duplicate_fixed",
        "own_hash",
        "archive_hash",
        "policy_hash",
        "reply_hash",
        "root_value",
        "nan_value",
        "summary_error",
        "actions_exported",
        "training",
        "late",
        "bool_count",
        "incomplete",
    ],
)
def test_native_partial_schema_and_scalar_corruption_rejected(
    corpus: tuple[dict[str, Any], dict[str, Any], Path], kind: str
) -> None:
    own, saved, path = corpus
    bad = copy.deepcopy(saved)
    if kind == "missing_profile":
        bad["rows"].pop()
    elif kind == "duplicate_profile":
        bad["rows"][-1] = copy.deepcopy(bad["rows"][0])
    elif kind == "missing_fixed":
        bad["fixed"].pop()
    elif kind == "duplicate_fixed":
        bad["fixed"][-1] = copy.deepcopy(bad["fixed"][0])
    elif kind == "own_hash":
        bad["own_sha256"] = "f" * 64
    elif kind == "archive_hash":
        bad["details_sha256"] = "f" * 64
    elif kind == "policy_hash":
        bad["rows"][0]["policy_sha256"] = "f" * 64
    elif kind == "reply_hash":
        bad["fixed"][0]["reply_sha256"] = "f" * 64
    elif kind == "root_value":
        bad["rows"][0]["responses"][0]["exact_root_chips"] += 1
    elif kind == "nan_value":
        bad["fixed"][0]["gain_chips"] = float("nan")
    elif kind == "summary_error":
        bad["maximum_error_chips"] = 1.0
    elif kind == "actions_exported":
        bad["reference_actions_exported"] = True
    elif kind == "training":
        bad["training_performed"] = True
    elif kind == "late":
        bad["seconds"] = 180
    elif kind == "bool_count":
        bad["completed_profiles"] = True
    else:
        bad["status"] = "incomplete"
    with pytest.raises(ArithmeticError):
        validate(bad, own, path)


def test_native_pre_input_failure_retains_receipt_and_never_constructs_reference(
    tmp_path: Path,
) -> None:
    output = tmp_path / "native.json"
    with (
        patch(
            "poker_ai.solver_validation.matched_updates.source",
            side_effect=OSError("missing source"),
        ),
        patch.object(
            ScalarReference, "__init__", side_effect=AssertionError("no reference")
        ),
    ):
        with pytest.raises(OSError):
            audit(tmp_path, tmp_path / "own.json", output, tiny=True)
    saved = json.loads(output.read_text())
    assert saved["status"] == "incomplete"
    assert saved["reference_setup_started"] is False
    assert saved["completed_profiles"] == saved["completed_fixed_targets"] == 0
    assert saved["failure"]["type"] == "OSError"


def test_shared_tiny_publication_clock_expiry_blocks_reference(tmp_path: Path) -> None:
    import socket
    import time

    own = tmp_path / "own.json"
    own.write_text(
        json.dumps(
            dict(
                proof_host=socket.gethostname(),
                proof_started_perf_counter=time.perf_counter() - 181,
            )
        )
    )
    output = tmp_path / "native.json"
    with (
        patch(
            "poker_ai.solver_validation.matched_updates.source",
            return_value=dict(dirty=False, sha256={}),
        ),
        patch(
            "poker_ai.solver_validation.matched_updates.inputs.config_inputs",
            return_value=config_inputs(ROOT),
        ),
        patch(
            "poker_ai.solver_validation.matched_updates.published",
            return_value=dict(own_sha256=digest(own)),
        ),
        patch.object(
            ScalarReference,
            "__init__",
            side_effect=AssertionError("expired proof cannot construct reference"),
        ),
    ):
        with pytest.raises(ArithmeticError, match="expired"):
            audit(tmp_path, own, output, tiny=True)
    saved = json.loads(output.read_text())
    assert saved["status"] == "incomplete"
    assert saved["reference_setup_started"] is False
    assert saved["completed_profiles"] == 0


def test_native_constructor_failure_records_started_without_completed(
    tmp_path: Path,
) -> None:
    import socket
    import time

    own = tmp_path / "own.json"
    own.write_text(
        json.dumps(
            dict(
                proof_host=socket.gethostname(),
                proof_started_perf_counter=time.perf_counter(),
            )
        )
    )
    output = tmp_path / "native.json"
    fixture_own = dict(scope=SCOPE, details_sha256="a" * 64)
    with (
        patch(
            "poker_ai.solver_validation.matched_updates.source",
            return_value=dict(dirty=False, sha256={}),
        ),
        patch(
            "poker_ai.solver_validation.matched_updates.inputs.config_inputs",
            return_value=config_inputs(ROOT),
        ),
        patch(
            "poker_ai.solver_validation.matched_updates.published",
            return_value=dict(own_sha256=digest(own)),
        ),
        patch(
            "poker_ai.solver_validation.matched_updates.software.read",
            return_value=(fixture_own, None, {}),
        ),
        patch(
            "poker_ai.solver_validation.matched_updates.license_record", return_value={}
        ),
        patch.object(
            ScalarReference,
            "__init__",
            side_effect=OSError("injected native constructor failure"),
        ),
    ):
        with pytest.raises(OSError, match="constructor failure"):
            audit(tmp_path, own, output, tiny=True)
    saved = json.loads(output.read_text())
    assert saved["status"] == "incomplete"
    assert saved["reference_setup_started"] is True
    assert saved["reference_setup_completed"] is False
    assert saved["completed_profiles"] == 0
    assert saved["failure"]["type"] == "OSError"
