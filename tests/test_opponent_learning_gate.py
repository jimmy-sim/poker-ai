"""Local temporary Git fixtures test publication only, not scientific acceptance."""

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from poker_ai.evaluation.opponent_learning_gate import (
    ENTRY,
    REPORT,
    STREAMS,
    clean_source,
    committed,
    publication,
)
from poker_ai.evaluation.opponent_learning_sources import CONFIG, COST_CONFIG
from poker_ai.postflop.river_study import digest


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(root), *args], text=True, stderr=subprocess.PIPE
    ).strip()


@pytest.fixture
def published(tmp_path: Path) -> tuple[Path, Path, dict[str, Any]]:
    root, remote = tmp_path / "repo", tmp_path / "remote.git"
    root.mkdir()
    remote.mkdir()
    git(remote, "init", "--bare")
    git(root, "init", "-b", "main")
    for key, value in (
        ("user.name", "Publication test fixture"),
        ("user.email", "fixture@example.invalid"),
        ("commit.gpgsign", "false"),
        ("core.hooksPath", "/dev/null"),
    ):
        git(root, "config", key, value)
    for filename in (
        "src/example.py",
        ENTRY,
        CONFIG,
        COST_CONFIG,
        "pyproject.toml",
        "uv.lock",
    ):
        path = root / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# publication-only fixture\n")
    git(root, "add", ".")
    git(root, "commit", "-m", "fixture source")
    source, binding = clean_source(root)
    folder = root / "results/fixture"
    (folder / "report").mkdir(parents=True)
    own: dict[str, Any] = dict(
        source=source,
        source_sha256=binding,
        status="completed_own_native_pending",
        failure=None,
        reference_constructed=False,
        reference_output_used_in_training=False,
        new_agent_default=False,
        fresh_global_admission=False,
        report={},
    )
    for stream in STREAMS:
        path = folder / f"own-{stream}.jsonl.gz"
        path.write_bytes(b"fixture bytes; not a real archive or scientific result")
        own[stream + "_file"] = path.name
        own[stream + "_sha256"] = digest(path)
    for filename in REPORT:
        path = folder / "report" / filename
        path.write_bytes(b"publication-only placeholder, not a report/plot")
        own["report"][filename] = digest(path)
    journal = folder / "events.jsonl"
    journal.write_text("fixture journal\n")
    child = folder / "own-child.json"
    child.write_text("fixture child\n")
    own["journal"] = dict(file=journal.name)
    own["complete_command"] = dict(child_file=child.name)
    path = folder / "own.json"
    path.write_text(json.dumps(own, sort_keys=True) + "\n")
    git(root, "add", ".")
    git(root, "commit", "-m", "fixture own files")
    git(root, "remote", "add", "origin", str(remote))
    git(root, "push", "-u", "origin", "main")
    return root, path, own


def test_publication_witness_does_not_claim_scientific_or_human_review(
    published: tuple[Path, Path, dict[str, Any]],
) -> None:
    root, path, own = published
    witness = publication(root, path, own)
    assert witness["own_sha256"] == digest(path)
    assert witness["own_commit"] == witness["upstream_commit"]
    assert "not independent scientific" in witness["scope"]
    # Numeric inventories, actual archives, clocks and all admission gates are
    # separate. These placeholder files can only test the Git publication layer.


@pytest.mark.parametrize(
    "change",
    [
        "dirty",
        "unpushed",
        "archive",
        "report",
        "source",
        "failed",
        "constructed",
        "memory",
    ],
)
def test_incomplete_or_unpublished_own_evidence_is_rejected(
    published: tuple[Path, Path, dict[str, Any]],
    change: str,
) -> None:
    root, path, own = published
    if change == "dirty":
        (root / "uncommitted.txt").write_text("pending")
    elif change == "unpushed":
        (root / "extra.txt").write_text("new own publication checkpoint")
        git(root, "add", ".")
        git(root, "commit", "-m", "not yet pushed")
    elif change == "archive":
        own["captures_sha256"] = "b" * 64
    elif change == "report":
        own["report"].pop("learning.png")
    elif change == "source":
        own["source_sha256"] = "b" * 64
    elif change == "failed":
        own["status"] = "failed"
    elif change == "memory":
        own["status"] = "failed"
    else:
        own["reference_constructed"] = True
    if change not in ("dirty", "unpushed", "memory"):
        # Commit/push the modified metadata too, so these cases exercise the
        # structural/hash guards rather than merely a changed in-memory dict.
        path.write_text(json.dumps(own, sort_keys=True) + "\n")
        git(root, "add", ".")
        git(root, "commit", "-m", "intentionally invalid publication fixture")
        git(root, "push", "origin", "main")
    with pytest.raises((ValueError, ArithmeticError)):
        publication(root, path, own)


def test_changed_or_external_file_cannot_count_as_committed(
    published: tuple[Path, Path, dict[str, Any]],
    tmp_path: Path,
) -> None:
    root, path, _ = published
    path.write_text("changed bytes")
    with pytest.raises(ArithmeticError):
        committed(root, path)
    outside = tmp_path / "outside.json"
    outside.write_text("outside repo")
    with pytest.raises(ArithmeticError):
        committed(root, outside)
