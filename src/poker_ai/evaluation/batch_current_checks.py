"""Verify the checked commit's complete code inventory across data-only merges."""

import hashlib
import subprocess
from pathlib import Path
from typing import Any


def checked_tree(root: Path, commit: Any, expected: dict[str, str]) -> dict[str, Any]:
    if (
        not isinstance(commit, str)
        or len(commit) != 40
        or any(c not in "0123456789abcdef" for c in commit)
    ):
        raise ArithmeticError("checked source commit must be a full hash")
    result = subprocess.run(
        ["git", "-C", str(root), "ls-tree", "-r", "--name-only", commit, "--", "src"],
        capture_output=True,
        text=True,
        check=True,
    )
    paths = {p for p in result.stdout.splitlines() if p.endswith(".py")}
    if paths != {p for p in expected if p.startswith("src/")}:
        raise ArithmeticError("checked commit has different complete source inventory")
    hashes = {}
    for path in expected:
        result_bytes = subprocess.run(
            ["git", "-C", str(root), "show", commit + ":" + path],
            capture_output=True,
            check=True,
        ).stdout
        hashes[path] = hashlib.sha256(result_bytes).hexdigest()
    if hashes != expected:
        raise ArithmeticError(
            "checked commit differs from current exact source/config/entrypoints"
        )
    return dict(git_commit=commit, dirty=False, git_status=[], sha256=hashes)
