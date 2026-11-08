"""Admission requires exact checked source, correctness and both real-CI receipts."""

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from poker_ai.postflop import learning_protocol as protocol
from poker_ai.postflop.learning_artifacts import sha

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def admission(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Any, ...]:
    (tmp_path / "checked.py").write_text("# explicit software fixture\n")
    hashes = {
        "checked.py": hashlib.sha256((tmp_path / "checked.py").read_bytes()).hexdigest()
    }
    source = dict(dirty=False, git_commit="a" * 40, sha256=hashes)
    correctness = dict(
        format=protocol.CORRECTNESS,
        status="passed_toy_correctness_no_postflop_learning",
        source=source,
    )
    path = tmp_path / "correctness.json"
    path.write_text(json.dumps(correctness))
    receipt = dict(
        format=protocol.ADMISSION,
        status="admitted_original_diagnostic_only",
        correctness_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        checked_commit="a" * 40,
        source_sha256=sha(hashes),
        ci_run=123,
        ci_jobs={"Python 3.11": "success", "Python 3.12": "success"},
        local_checks=dict(
            base_311="passed",
            base_312="passed",
            all_extras_311="passed",
            all_extras_312="passed",
            slow_integrations="passed",
        ),
    )
    (tmp_path / "admission.json").write_text(json.dumps(receipt))
    monkeypatch.setattr(protocol, "source", lambda root: copy.deepcopy(source))
    return (
        tmp_path,
        dict(
            correctness_receipt="correctness.json", admission_receipt="admission.json"
        ),
        receipt,
        source,
    )


def test_complete_gate_accepts_checked_source_and_readonly_extra_sources(
    admission: tuple[Any, ...],
) -> None:
    root, config, receipt, source = admission
    assert protocol.require_admission(root, config) == receipt
    source["sha256"]["new-module.py"] = "b" * 64
    source["dirty"] = True
    # Reading historical checked source remains possible in the user's dirty checkout.
    assert protocol.require_admission(root, config, require_clean=False) == receipt
    with pytest.raises(ValueError, match="publish"):
        protocol.require_admission(root, config)


@pytest.mark.parametrize(
    "mode",
    [
        "ci_missing",
        "ci_failed",
        "ci_bool",
        "wrong_commit",
        "local_failed",
        "wrong_correctness",
        "wrong_source",
        "dirty",
        "changed_file",
    ],
)
def test_reject_missing_failed_or_changed_admission(
    admission: tuple[Any, ...], mode: str
) -> None:
    root, config, receipt, source = admission
    if mode == "ci_missing":
        receipt["ci_jobs"].pop("Python 3.12")
    elif mode == "ci_failed":
        receipt["ci_jobs"]["Python 3.12"] = "failure"
    elif mode == "ci_bool":
        receipt["ci_run"] = True
    elif mode == "wrong_commit":
        receipt["checked_commit"] = "b" * 40
    elif mode == "local_failed":
        receipt["local_checks"]["base_312"] = "failure"
    elif mode == "wrong_correctness":
        receipt["correctness_sha256"] = "0" * 64
    elif mode == "wrong_source":
        source["sha256"]["unreviewed.py"] = "b" * 64
    elif mode == "dirty":
        source["dirty"] = True
    else:
        (root / "checked.py").write_text("# changed\n")
    (root / "admission.json").write_text(json.dumps(receipt))
    with pytest.raises((ValueError, ArithmeticError)):
        protocol.require_admission(root, config)


def test_original_grid_prefixes_and_pins_remain_complete_without_training() -> None:
    config, comparison, cells = protocol.inputs(ROOT)
    assert len(cells) == 140
    assert config["checkpoint_labels"]["work"] == comparison["node_work_checkpoints"]
    assert len(protocol.prefixes(ROOT, cells)) == 140


def test_incomplete_run_keeps_partial_events_and_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from poker_ai.postflop import learning_run

    config, comparison, cells = protocol.inputs(ROOT)
    monkeypatch.setattr(protocol, "inputs", lambda root: (config, comparison, cells))
    monkeypatch.setattr(
        protocol,
        "require_admission",
        lambda root, conf: {"test": "explicit software fixture"},
    )
    monkeypatch.setattr(protocol, "source", lambda root: dict(sha256={}, dirty=False))
    monkeypatch.setattr(protocol, "prefixes", lambda root, cs: {})

    def fail(*args: Any) -> None:
        record = args[-1]
        record.update(
            status="incomplete",
            workers=[
                dict(
                    messages=[
                        dict(kind="cell", phase="snapshot", row={"test": "partial"})
                    ]
                )
            ],
        )
        raise TimeoutError("deliberate software fixture")

    monkeypatch.setattr(learning_run, "run_batch", fail)
    output = tmp_path / "own.json"
    with pytest.raises(TimeoutError, match="deliberate"):
        learning_run.run(tmp_path, output)
    saved = json.loads(output.read_text())
    assert saved["status"] == "incomplete"
    assert saved["failure"]["type"] == "TimeoutError"
    assert saved["batch"]["workers"][0]["messages"][0]["row"]["test"] == "partial"
    with pytest.raises(FileExistsError):
        learning_run.run(tmp_path, output)
