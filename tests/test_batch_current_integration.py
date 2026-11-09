"""Real analytic tiny-game IO; no training, no reference and no poker claims."""

import copy
import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from poker_ai.evaluation import batch_current_inputs as inputs
from poker_ai.evaluation import batch_current_protocol as protocol
from poker_ai.evaluation import batch_current_run as own
from poker_ai.evaluation.batch_current_fixture import SCOPE, job, prepare
from poker_ai.evaluation.batch_current_report import write_report
from poker_ai.evaluation.batch_current_validation import grid
from poker_ai.postflop.controlled_training import ControlledTrainer
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.learning_run import persist
from poker_ai.postflop.river_study import digest
from poker_ai.solver_validation.reference import Reference

pytestmark = pytest.mark.slow
ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def complete(
    tmp_path_factory: pytest.TempPathFactory,
) -> tuple[dict[str, Any], inputs.Sources, Path]:
    root = tmp_path_factory.mktemp("saved-current") / "analytic"
    base = json.loads((ROOT / "configs/frozen-pass-batches.json").read_text())
    with (
        patch.object(
            ControlledTrainer,
            "__init__",
            side_effect=AssertionError("analytic fixture cannot train"),
        ),
        patch.object(
            Reference,
            "__init__",
            side_effect=AssertionError("own fixture cannot construct native"),
        ),
    ):
        sources = prepare(root, base)
    config = copy.deepcopy(inputs.config_inputs(ROOT))
    config.update(
        status=SCOPE,
        source_own="source-own.json",
        source_native="EXPLICIT_NATIVE_SCHEMA.json",
    )
    persist(
        root / config["source_native"],
        dict(scope="FICTIONAL_SOURCE_GATE_ONLY_NO_NATIVE_RUN"),
    )
    persist(root / inputs.CONFIG, config)
    marker = root / "EXPLICIT_SOURCE.py"
    marker.write_text("# fictional source metadata for IO only\n")
    source = dict(
        git_commit="a" * 40,
        dirty=False,
        git_status=[],
        sha256={marker.name: digest(marker)},
    )
    h = sha(source["sha256"])
    with pytest.MonkeyPatch.context() as m:
        m.setattr(inputs, "config_inputs", lambda root: config)
        m.setattr(inputs, "source", lambda root: copy.deepcopy(source))
        m.setattr(inputs, "load", lambda root: sources)
        m.setattr(
            protocol, "checked_tree", lambda root, commit, hashes: copy.deepcopy(source)
        )
        ci = dict(
            checked_commit=source["git_commit"],
            source_sha256=h,
            run_id=123,
            jobs=protocol.JOBS,
            scope="FICTIONAL_NOT_OBSERVED_CI",
        )
        local = dict(
            source_sha256=h, checks=protocol.LOCAL, scope="FICTIONAL_NOT_EXECUTED_LOCAL"
        )
        persist(root / inputs.CHECKS, protocol.record_checks(root, ci, local))
        persist(root / inputs.ADMITTED, protocol.record_admission(root))
        m.setattr(own, "job", job)
        with (
            patch.object(
                ControlledTrainer,
                "__init__",
                side_effect=AssertionError("evaluator cannot train"),
            ),
            patch.object(
                Reference,
                "__init__",
                side_effect=AssertionError("own evaluator cannot construct native"),
            ),
        ):
            saved = own.run(root, root / "attempt/own.json")
    return saved, sources, root


def test_full_three_process216current1728fixed_and_no_input_mutation(
    complete: tuple[dict[str, Any], inputs.Sources, Path],
) -> None:
    saved, sources, root = complete
    assert (
        saved["status"] == "completed_own_native_pending"
        and saved["config"]["status"] == SCOPE
    )
    assert len(saved["rows"]) == 216 and len(saved["fixed_matches"]) == 1728
    assert (
        saved["completed_current_profiles"] == 216
        and saved["completed_fixed_targets"] == 1728
    )
    assert saved["own_replay"]["maximum_error_chips"] == 0
    assert saved["training_performed"] is False and saved["policies_modified"] is False
    source = json.loads(sources.own_path.read_text())
    assert source == sources.own
    grid(saved["rows"], saved["fixed_matches"], sources, saved["source_sha256"])
    assert (root / "source-currents.jsonl.gz").exists()


@pytest.mark.parametrize(
    "damage",
    [
        "missing_current",
        "duplicate_current",
        "current_hash",
        "current_guard",
        "current_work",
        "current_unknown",
        "missing_fixed",
        "duplicate_fixed",
        "fixed_target",
        "fixed_opponent",
        "fixed_policy",
        "fixed_root",
        "fixed_gain",
        "fixed_unknown",
    ],
)
def test_complete_source_or_numerical_corruption_rejected(
    complete: tuple[dict[str, Any], inputs.Sources, Path], damage: str
) -> None:
    saved, sources, _ = complete
    rows = copy.deepcopy(saved["rows"])
    fixed = copy.deepcopy(saved["fixed_matches"])
    if damage == "missing_current":
        rows.pop()
    elif damage == "duplicate_current":
        rows[-1] = rows[0]
    elif damage == "current_hash":
        rows[0]["receipt"]["policy_sha256"] = "b" * 64
    elif damage == "current_guard":
        rows[0]["source_guard_sha256"] = "b" * 64
    elif damage == "current_work":
        rows[0]["iteration"] += 1
    elif damage == "current_unknown":
        rows[0]["unknown"] = 1
    elif damage == "missing_fixed":
        fixed.pop()
    elif damage == "duplicate_fixed":
        fixed[-1] = fixed[0]
    elif damage == "fixed_target":
        fixed[0]["target"] = False
    elif damage == "fixed_opponent":
        fixed[0]["opponent_profile_id"] = "unknown"
    elif damage == "fixed_policy":
        fixed[0]["own_policy_sha256"] = "b" * 64
    elif damage == "fixed_root":
        fixed[0]["restricted_reply_value_chips"] += 1
    elif damage == "fixed_gain":
        fixed[0]["gain_chips"] = float("nan")
    else:
        fixed[0]["unknown"] = 1
    with pytest.raises((ArithmeticError, KeyError)):
        grid(rows, fixed, sources, saved["source_sha256"])


def test_read_only_replay_and_six_numerical_report_files(
    complete: tuple[dict[str, Any], inputs.Sources, Path],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    saved, sources, root = complete
    monkeypatch.setattr(inputs, "config_inputs", lambda root: saved["config"])
    monkeypatch.setattr(inputs, "source", lambda root: copy.deepcopy(saved["source"]))
    monkeypatch.setattr(inputs, "load", lambda root: sources)
    with (
        patch.object(
            ControlledTrainer,
            "__init__",
            side_effect=AssertionError("reader cannot train"),
        ),
        patch.object(
            Reference,
            "__init__",
            side_effect=AssertionError("reader cannot construct native"),
        ),
    ):
        replayed, _, proof = own.replay(root, root / "attempt/own.json")
    assert proof["maximum_error_chips"] == 0 and replayed == saved
    report = write_report(root, saved, sources, tmp_path, plots=False)
    assert report["numerical_sha256"] == saved["report"]["numerical_sha256"]
    assert (
        len(report["numerical_sha256"]) == 6 and report["paired_fixed_targets"] == 1152
    )
    assert all(
        (root / "attempt/report" / n).stat().st_size > 1000
        for n in saved["report"]["figures"]
    )


def test_real_published_source_and_native_gate_constructs_no_learner_or_solver() -> (
    None
):
    with (
        patch.object(
            ControlledTrainer,
            "__init__",
            side_effect=AssertionError("source loader cannot train"),
        ),
        patch.object(
            Reference,
            "__init__",
            side_effect=AssertionError("source loader cannot construct native"),
        ),
    ):
        sources = inputs.load(ROOT)
    assert len(sources.own["rows"]) == 480 and len(sources.own["currents"]) == 216
    assert (
        sources.native["profiles"] == 480
        and sources.native["maximum_error_chips"] <= 1e-9
    )
    assert (
        len(inputs.candidates(sources)) == 216
        and len(inputs.source_hashes(ROOT, sources)) == 5
    )
