"""Read-only checkpoint observations and source-bound own-policy round trips."""

import gzip
import hashlib
import json
import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from poker_ai.finite import ArrayTree, FloatArray
from poker_ai.postflop.controlled_scoring import BoolArray
from poker_ai.postflop.controlled_training import ControlledTrainer
from poker_ai.postflop.parallel_profile import same
from poker_ai.postflop.river_study import Deadline
from poker_ai.postflop.row_profile import fingerprint

FORMAT = "poker-ai-controlled-own-policy-snapshot-v1"


def pack_policy(tree: ArrayTree, policy: FloatArray) -> list[list[float]]:
    """Serialize only legal columns; chance width need not be decision width.

    Reject noncanonical negative-zero padding rather than silently changing its
    bits. Legal negative zeros are retained. Numerical trainer arrays stay padded.
    """
    tree.validate_policy(policy)
    if np.any(np.signbit(policy) & (tree.legal == 0)):
        raise ValueError("own artifact requires canonical positive-zero padding")
    return [policy[i, : len(menu)].tolist() for i, menu in enumerate(tree.actions)]


def unpack_policy(tree: ArrayTree, rows: Any) -> FloatArray:
    if (
        not isinstance(rows, list)
        or len(rows) != len(tree.keys)
        or any(
            not isinstance(row, list)
            or len(row) != len(menu)
            or any(type(p) not in (int, float) for p in row)
            for row, menu in zip(rows, tree.actions, strict=True)
        )
    ):
        raise ArithmeticError("packed own policy requires legal numeric rows")
    policy = np.zeros_like(tree.legal)
    for i, row in enumerate(rows):
        policy[i, : len(row)] = row
    tree.validate_policy(policy)
    return policy


@dataclass(frozen=True)
class Observation:
    labels: tuple[tuple[str, int], ...]
    iteration: int
    previous_work: int
    total_work: int
    last_iteration_visits: int
    overshoots: dict[str, int]
    state_sha256: str
    policy: FloatArray
    diagnostics: dict[str, Any]


def diagnostics(solver: ControlledTrainer, river: BoolArray) -> dict[str, Any]:
    if river.dtype != np.bool_ or river.shape != (len(solver.tree.keys),):
        raise ValueError("invalid river diagnostic mask")
    if not np.all(np.isfinite(solver.strategy_sum)) or np.any(solver.strategy_sum < 0):
        raise ArithmeticError("invalid stored average mass")
    norm = float(np.linalg.norm(solver.regrets))
    if not math.isfinite(norm):
        raise ArithmeticError("nonfinite regret norm")
    count = int(river.sum())
    visited = (
        sum(
            key in solver.sampled_keys
            for key, active in zip(solver.tree.keys, river, strict=True)
            if active
        )
        if solver.traversal == "external"
        else count
        if solver.iteration > 0
        else 0
    )
    return dict(
        regret_norm=norm,
        positive_average_coverage=float((solver.strategy_sum.sum(axis=1) > 0).mean()),
        river_visit_coverage=visited / count if count else None,
        river_partition_rows=count,
        river_partition_rows_visited=visited,
    )


def observe(
    solver: ControlledTrainer,
    work: Sequence[int],
    iterations: Sequence[int],
    river: BoolArray,
    capture: Callable[[Observation], None],
    deadline: Deadline,
) -> None:
    """Observe first whole-iteration crossings; never interpolate or pool axes.

    Exact warm initialization is iteration one and charged work. If it already
    crosses a requested work threshold, its prior work is zero. Exported policy
    arrays are independent and read-only. Mutation by a capture callback is an
    error, checked against mathematical arrays, RNG, keys and work counters.
    """
    if (
        not work
        and not iterations
        or solver.iteration not in (0, 1)
        or (solver.iteration == 0 and solver.nodes_visited != 0)
        or (
            solver.iteration == 1
            and (
                solver.nodes_visited != solver.initialization_visits
                or solver.initialization_visits != 2 * len(solver.tree.player)
            )
        )
        or any(type(v) is not int or v <= 0 for v in (*work, *iterations))
        or list(work) != sorted(set(work))
        or list(iterations) != sorted(set(iterations))
        or any(v < solver.iteration for v in iterations)
    ):
        raise ValueError("invalid/unreachable checkpoint labels")
    pending_work, pending_iterations = list(work), list(iterations)
    previous, last = 0, solver.nodes_visited

    def identity() -> tuple[Any, ...]:
        return (
            fingerprint(solver),
            solver.iteration,
            solver.nodes_visited,
            solver.initialization_visits,
            getattr(solver, "row_evaluations", None),
            getattr(solver, "last_pass_rows", None),
        )

    while pending_work or pending_iterations:
        deadline.check()
        crossed = [v for v in pending_work if v <= solver.nodes_visited]
        exact = [v for v in pending_iterations if v == solver.iteration]
        if crossed or exact:
            if any(previous >= v for v in crossed):
                raise ArithmeticError("checkpoint missed its first work crossing")
            before = identity()
            policy = solver.average_policy.copy()
            policy.flags.writeable = False
            packet = Observation(
                tuple(
                    [("work", v) for v in crossed] + [("iteration", v) for v in exact]
                ),
                solver.iteration,
                previous,
                solver.nodes_visited,
                last,
                {str(v): solver.nodes_visited - v for v in crossed},
                str(before[0]),
                policy,
                diagnostics(solver, river),
            )
            capture(packet)
            if identity() != before:
                raise ArithmeticError("checkpoint observer mutated training state")
            pending_work = [v for v in pending_work if v not in crossed]
            pending_iterations = [v for v in pending_iterations if v not in exact]
            if not pending_work and not pending_iterations:
                return
        previous = solver.nodes_visited
        solver.step()
        last = solver.nodes_visited - previous
        if last <= 0:
            raise ArithmeticError("checkpoint iteration did not charge positive work")


def write_snapshot(
    path: Path, tree: ArrayTree, policy: FloatArray, metadata: dict[str, Any]
) -> dict[str, Any]:
    """Own finite policy snapshot, not a resumable trainer or native strategy."""
    if path.exists():
        raise FileExistsError("retain own snapshot")
    tree.validate_policy(policy)
    envelope = dict(
        format=FORMAT,
        dtype="<f8",
        shape=list(policy.shape),
        actions=[list(a) for a in tree.actions],
        metadata=metadata,
        policy=pack_policy(tree, policy),
    )
    raw = json.dumps(
        envelope, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()
    blob = gzip.compress(raw, mtime=0)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    if tmp.exists():
        raise FileExistsError("retain partial own snapshot")
    tmp.write_bytes(blob)
    tmp.replace(path)
    return dict(
        sha256=hashlib.sha256(blob).hexdigest(),
        policy_sha256=hashlib.sha256(
            np.asarray(policy, dtype="<f8").tobytes()
        ).hexdigest(),
        bytes=len(blob),
    )


def read_snapshot(
    path: Path, tree: ArrayTree, receipt: dict[str, Any], metadata: dict[str, Any]
) -> FloatArray:
    blob = path.read_bytes()
    if (
        len(blob) != receipt["bytes"]
        or hashlib.sha256(blob).hexdigest() != receipt["sha256"]
    ):
        raise ArithmeticError("own snapshot bytes/hash changed")
    saved = json.loads(gzip.decompress(blob))
    json.dumps(saved, allow_nan=False)
    if (
        set(saved) != {"format", "dtype", "shape", "actions", "metadata", "policy"}
        or saved["format"] != FORMAT
        or saved["dtype"] != "<f8"
        or not same(saved["shape"], list(tree.legal.shape))
        or not same(saved["actions"], [list(a) for a in tree.actions])
        or not same(saved["metadata"], metadata)
    ):
        raise ArithmeticError("own snapshot schema/metadata changed")
    policy = unpack_policy(tree, saved["policy"])
    if (
        hashlib.sha256(np.asarray(policy, dtype="<f8").tobytes()).hexdigest()
        != receipt["policy_sha256"]
    ):
        raise ArithmeticError("own snapshot policy bits changed")
    return policy
