"""Independent audit core and published-own gate for matched-update evidence."""

import hashlib
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

from poker_ai.evaluation.averaging_history_replay import archive_path
from poker_ai.evaluation.controlled_reply_math import Reply
from poker_ai.evaluation.matched_update_replay import ContextFor
from poker_ai.finite import FloatArray
from poker_ai.postflop.cell_process import Send
from poker_ai.postflop.controlled_checkpoints import unpack_policy
from poker_ai.postflop.learning_artifacts import read_archive
from poker_ai.postflop.learning_training import replay_detail
from poker_ai.postflop.river_study import Deadline, digest
from poker_ai.solver_validation.averaging_history import fixed_error
from poker_ai.solver_validation.frozen_batches import error as self_error
from poker_ai.solver_validation.matched_array_reference import ScalarReference, compare
from poker_ai.solver_validation.matched_update_values import Cache, fixed

OpponentFor = Callable[[dict[str, Any]], tuple[FloatArray, Reply]]


def published(root: Path, path: Path) -> dict[str, Any]:
    """Require exact own bytes at a pushed commit before reference construction.

    origin/* is evidence of the completed push/fetch in this checkout, not a new
    live network lookup. The workflow separately observes GitHub publication.
    """
    relative = str(path.resolve().relative_to(root.resolve()))
    commit = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    blob = subprocess.run(
        ["git", "-C", str(root), "show", commit + ":" + relative],
        check=True,
        capture_output=True,
    ).stdout
    refs = subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "for-each-ref",
            "--contains",
            commit,
            "--format=%(refname)",
            "refs/remotes/origin",
        ],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    if hashlib.sha256(blob).hexdigest() != digest(path) or not refs:
        raise ArithmeticError("publish exact own evidence before native construction")
    return dict(commit=commit, own_sha256=digest(path), origin_refs=refs)


def audit_rows(
    path: Path,
    own: dict[str, Any],
    indices: list[int],
    context_for: ContextFor,
    refs: dict[int, tuple[ScalarReference, ScalarReference]],
    opponent_for: OpponentFor,
    send: Send,
    deadline: Deadline,
) -> dict[str, Any]:
    peers: dict[str, list[dict[str, Any]]] = {}
    for row in own["fixed_matches"]:
        peers.setdefault(row["own_snapshot_id"], []).append(row)
    cache: Cache = {}
    profiles = targets = 0
    maximum = 0.0
    for row, blob in read_archive(
        archive_path(path, own["details_file"]), own["details_sha256"], own["rows"]
    ):
        deadline.check()
        index = row["path_index"]
        if index not in indices:
            continue
        context = context_for(index)
        _, detail = replay_detail(context, row, blob, 1e-9)
        result = dict(
            id=row["id"],
            path_index=index,
            work_label=row["work_label"],
            policy_sha256=row["receipt"]["policy_sha256"],
            own_reply_sha256=row["reply_sha256"],
            **compare(context, refs[index], detail),
        )
        error = self_error(result, row)
        if error > 1e-9:
            raise ArithmeticError("independent matched own-profile audit failed")
        send(dict(kind="cell", phase="self", index=index, result=result))
        profiles += 1
        maximum = max(maximum, error)
        policy = unpack_policy(context.partition, detail["policy"])
        for peer in peers[row["id"]]:
            opponent, reply = opponent_for(peer)
            result = fixed(peer, policy, opponent, reply, refs[index][1], cache)
            error = fixed_error(result, peer)
            if error > 1e-9:
                raise ArithmeticError("independent matched fixed audit failed")
            send(dict(kind="cell", phase="fixed", index=index, result=result))
            targets += 1
            maximum = max(maximum, error)
    deadline.check()
    return dict(
        paths=len(indices),
        profiles=profiles,
        fixed_targets=targets,
        cached_opponent_targets=len(cache),
        maximum_error_chips=maximum,
    )
