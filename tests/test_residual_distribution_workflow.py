"""Fictional publication and admission guards for known-row diagnosis."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from known_turn_residual_distribution import workflow  # noqa: E402


def test_pinned_report_clock_recomputes_conservative_admission(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / workflow.PRIOR_JOB
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "status": "passed",
                "source_head": "published-head",
                "observed_wall_seconds": 284.1626491249772,
            }
        )
    )
    monkeypatch.setattr(workflow, "PRIOR_JOB_SHA256", workflow.digest(path))
    plan = {
        "report_head": "published-head",
        "prior_report_seconds": 284.163,
        "forecast_multiplier": 2,
        "failure_save_reserve_seconds": 120,
        "forecast_seconds": 688.326,
    }
    assert workflow._forecast(tmp_path, plan) == 688.326
    plan["prior_report_seconds"] = 284.162
    with pytest.raises(ArithmeticError, match="runtime"):
        workflow._forecast(tmp_path, plan)


def test_published_stage_checks_member_bytes_and_commit(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    folder = tmp_path / workflow.ARCHIVE / "proof"
    folder.mkdir(parents=True)
    (folder / "result.json").write_text('{"status":"proof_passed"}\n')
    member = folder / "result.json"
    manifest = {
        "status": "proof_passed",
        "source_fingerprint": "synthetic-fingerprint",
        "files": [
            {
                "file": "result.json",
                "bytes": member.stat().st_size,
                "sha256": workflow.digest(member),
            }
        ],
    }
    (folder / "manifest.json").write_text(json.dumps(manifest))
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "-qm",
            "synthetic receipt",
        ],
        cwd=tmp_path,
        check=True,
    )
    assert (
        workflow.require_archive(
            tmp_path, folder, "proof_passed", "synthetic-fingerprint"
        )
        == manifest
    )
    member.write_text("changed\n")
    with pytest.raises(ArithmeticError, match="member bytes"):
        workflow.require_archive(
            tmp_path, folder, "proof_passed", "synthetic-fingerprint"
        )


def test_preflight_failure_is_retained_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def reject(_root: Path) -> str:
        raise ArithmeticError("fictional rejected source")

    monkeypatch.setattr(workflow, "clean_head", reject)
    output = tmp_path / "attempt"
    with pytest.raises(ArithmeticError, match="fictional"):
        workflow.execute(tmp_path, output, "proof")
    failed = json.loads((output / "failed.json").read_text())
    assert failed["status"] == "failed_preflight"
    assert "fictional rejected source" in failed["error"]
    with pytest.raises(FileExistsError):
        workflow.execute(tmp_path, output, "proof")
