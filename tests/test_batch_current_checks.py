"""Real temporary Git trees prove byte identity across documentation-only commits."""

import hashlib
import subprocess
from pathlib import Path

import pytest

from poker_ai.evaluation.batch_current_checks import checked_tree


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(
        [
            "git",
            "-C",
            str(root),
            "-c",
            "user.name=EXPLICIT SOFTWARE FIXTURE",
            "-c",
            "user.email=fixture@example.test",
            "-c",
            "core.hooksPath=/dev/null",
            *args,
        ],
        text=True,
    ).strip()


def commit(root: Path) -> str:
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "explicit temporary fixture")
    return git(root, "rev-parse", "HEAD")


def test_complete_source_tree_accepts_docs_only_but_rejects_changed_added_deleted_code(
    tmp_path: Path,
) -> None:
    git(tmp_path, "init", "-q")
    (tmp_path / "src").mkdir()
    (tmp_path / "src/a.py").write_text("value=1\n")
    (tmp_path / "config.json").write_text("{}\n")
    first = commit(tmp_path)
    paths = ("src/a.py", "config.json")
    expected = {
        p: hashlib.sha256((tmp_path / p).read_bytes()).hexdigest() for p in paths
    }
    assert checked_tree(tmp_path, first, expected)["git_commit"] == first
    (tmp_path / "journal.md").write_text("# explicit software note\n")
    commit(tmp_path)
    assert checked_tree(tmp_path, first, expected)["sha256"] == expected
    (tmp_path / "src/a.py").write_text("value=2\n")
    changed = commit(tmp_path)
    with pytest.raises(ArithmeticError, match="differs"):
        checked_tree(tmp_path, changed, expected)
    (tmp_path / "src/b.py").write_text("# explicit new source\n")
    added = commit(tmp_path)
    with pytest.raises(ArithmeticError, match="inventory"):
        checked_tree(tmp_path, added, expected)
    (tmp_path / "src/a.py").unlink()
    deleted = commit(tmp_path)
    with pytest.raises(ArithmeticError, match="inventory"):
        checked_tree(tmp_path, deleted, expected)


@pytest.mark.parametrize("value", ["a" * 7, "g" * 40, True, None])
def test_checked_commit_requires_full_hex_identity(
    tmp_path: Path, value: object
) -> None:
    with pytest.raises(ArithmeticError):
        checked_tree(tmp_path, value, {})
