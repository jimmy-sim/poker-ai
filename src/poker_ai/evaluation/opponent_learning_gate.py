"""Source and actual Git publication checks before independent construction.

These are software/publication checks, not a real trajectory admission. The
upstream witness is Git's locally recorded remote ref after a successful push;
the receipt names that witness rather than claiming a separate human review.
"""

import json
import subprocess
from pathlib import Path
from typing import Any

from poker_ai.evaluation.opponent_learning_sources import CONFIG, COST_CONFIG
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.parallel_profile import same
from poker_ai.postflop.river_study import digest
from poker_ai.validation.five_card import source_provenance

ENTRY = "scripts/validate_opponent_learning.py"
STREAMS = ("captures", "masses", "warms", "composed", "details")
REPORT = {
    "arm-points.csv",
    "fixed-conditions.csv",
    "summary.json",
    "learning.png",
    "paired-gaps.png",
    "fixed-gain.png",
}


def source(root: Path) -> dict[str, Any]:
    current: dict[str, Any] = dict(
        source_provenance(root, root / CONFIG, entrypoints=(ENTRY,))
    )
    hashes = dict(current["sha256"])
    hashes[COST_CONFIG] = digest(root / COST_CONFIG)
    current["sha256"] = hashes
    return current


def clean_source(root: Path) -> tuple[dict[str, Any], str]:
    current = source(root)
    if current["dirty"] is not False:
        raise ValueError("publish the exact own-opponent source before this stage")
    return current, sha(current["sha256"])


def committed(root: Path, path: Path) -> None:
    resolved = path.resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise ArithmeticError("publication member escapes the repository")
    relative = str(resolved.relative_to(root.resolve()))
    result = subprocess.run(
        ["git", "-C", str(root), "show", "HEAD:" + relative],
        capture_output=True,
        check=False,
    )
    if result.returncode != 0 or result.stdout != path.read_bytes():
        raise ArithmeticError(
            "own evidence must be committed unchanged before comparison"
        )


def publication(root: Path, path: Path, own: dict[str, Any]) -> dict[str, Any]:
    """Check source/header/all archives/reports and pushed own receipt BEFORE refs."""
    current, binding = clean_source(root)
    if (
        not same(json.loads(path.read_text()), own)
        or own["source"]["dirty"] is not False
        or own["source_sha256"] != sha(own["source"]["sha256"])
        or not same(own["source"]["sha256"], current["sha256"])
        or own["source_sha256"] != binding
        or own["status"] != "completed_own_native_pending"
        or own["failure"] is not None
        or own["reference_constructed"] is not False
        or own["reference_output_used_in_training"] is not False
        or own["new_agent_default"] is not False
        or own["fresh_global_admission"] is not False
        or set(own["report"]) != REPORT
    ):
        raise ArithmeticError(
            "complete originally clean own-only evidence required before reference"
        )
    committed(root, path)
    inputs = {str(path.relative_to(root)): digest(path)}
    for name in STREAMS:
        member = path.parent / own[name + "_file"]
        if digest(member) != own[name + "_sha256"]:
            raise ArithmeticError("published own archive bytes changed")
        committed(root, member)
        inputs[str(member.relative_to(root))] = digest(member)
    for name, expected in own["report"].items():
        member = path.parent / "report" / name
        if digest(member) != expected:
            raise ArithmeticError("published own report bytes changed")
        committed(root, member)
        inputs[str(member.relative_to(root))] = expected
    # The raw event journal and complete-command child are publication evidence
    # too, not ignored scratch files or a substitute final summary.
    for member in (
        path.with_name(own["journal"]["file"]),
        path.with_name(own["complete_command"]["child_file"]),
    ):
        committed(root, member)
        inputs[str(member.relative_to(root))] = digest(member)
    branch = subprocess.check_output(
        ["git", "-C", str(root), "symbolic-ref", "--short", "HEAD"],
        text=True,
    ).strip()
    remote = "refs/remotes/origin/" + branch
    remote_head = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "--verify", remote],
        text=True,
    ).strip()
    contained = subprocess.run(
        ["git", "-C", str(root), "merge-base", "--is-ancestor", "HEAD", remote],
        capture_output=True,
        check=False,
    )
    if contained.returncode != 0:
        raise ArithmeticError(
            "push the complete own checkpoint before reference construction"
        )
    return dict(
        own_commit=current["git_commit"],
        locally_recorded_upstream=remote,
        upstream_commit=remote_head,
        own_sha256=digest(path),
        published_input_sha256=inputs,
        source_sha256=binding,
        scope="Git publication witness, not independent scientific or human review",
    )
