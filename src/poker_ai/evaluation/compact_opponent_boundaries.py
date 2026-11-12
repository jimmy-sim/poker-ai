"""Translate all36 original compact/exact snapshots into unchanged B4 barriers.

Only names/serialization differ. Dense probability/book bytes and original state
fingerprints must match exactly; no numerical tolerance or probability mapping
is used. This reader constructs neither a learner nor a reference solver.
"""

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from poker_ai.evaluation import compact_sampled_inputs as original
from poker_ai.evaluation.averaging_history_artifacts import array_sha
from poker_ai.evaluation.opponent_learning_design import REAL, WORK, Design
from poker_ai.finite import ArrayTree, FloatArray
from poker_ai.postflop import compact_full_artifacts as files
from poker_ai.postflop.compact_full_context import Context
from poker_ai.postflop.compact_sampled_state import decode
from poker_ai.postflop.public_range_definition import CANDIDATE


def readout_fingerprint(
    tree: ArrayTree,
    raw: dict[str, Any],
    arrays: dict[str, FloatArray],
    policies: dict[str, FloatArray],
    weight: str,
) -> str:
    """Literal old observer hash on decoded arrays, without a trainer instance."""
    if weight not in ("uniform", "linear"):
        raise ValueError("choose one of the two original average books")
    h = hashlib.sha256()
    for values in (
        arrays["regrets"],
        arrays[weight + "_sum"],
        policies["current"],
        policies[weight],
    ):
        h.update(np.asarray(values, dtype="<f8").tobytes())
    h.update(json.dumps(raw["rng_state"], sort_keys=True).encode())
    keys = sorted(
        k for k, flag in zip(tree.keys, raw["sampled_rows"], strict=True) if flag
    )
    h.update(json.dumps(keys).encode())
    return h.hexdigest()


def select_points(saved: dict[str, Any]) -> list[tuple[int, dict[str, Any]]]:
    """Select every seed/work for both ordinary paths; reject bool identities."""
    design = Design(REAL, WORK)
    selected = []
    for index in range(30):
        path = design.path(index)
        if path["path_kind"] not in ("coarse0", "fine"):
            continue
        representation = CANDIDATE if index % 5 == 0 else "exact"
        for work in WORK:
            matches = [
                row
                for row in saved["points"]
                if row["representation"] == representation
                and row["spot_file"] == path["spot_file"]
                and type(row["seed"]) is int
                and row["seed"] == path["seed"]
                and type(row["work_checkpoint"]) is int
                and row["work_checkpoint"] == work
            ]
            if len(matches) != 1:
                raise ArithmeticError(
                    "one original compact/exact snapshot per boundary required"
                )
            selected.append((index, matches[0]))
    if len(selected) != 36:
        raise ArithmeticError("all36 original compact/exact boundaries required")
    return selected


def boundaries(
    folder: Path, saved: dict[str, Any], contexts: dict[tuple[str, str], Context]
) -> tuple[dict[str, Any], ...]:
    """Caller authenticates original whole archive/source before using this list."""
    result = []
    for index, point in select_points(saved):
        context = contexts[point["spot_file"], point["representation"]]
        raw = files.load_snapshot(folder / "states", point["state_receipt"])
        warm = files.load_snapshot(folder / "warms", point["warm_receipt"])
        arrays, policies = decode(
            context, raw, warm, saved["source"]["fingerprint"], "real"
        )
        for key in (
            "path_index",
            "seed",
            "work_checkpoint",
            "iteration",
            "previous_node_work",
            "total_node_work",
            "last_iteration_work",
            "initialization_work",
            "sampled_traversals",
            "guard_sha256",
        ):
            if type(point[key]) is not type(raw[key]) or point[key] != raw[key]:
                raise ArithmeticError(
                    "original boundary selector differs from raw state"
                )
        current = array_sha(policies["current"])
        result.append(
            dict(
                path_index=index,
                original_path_index=point["path_index"],
                work_label=point["work_checkpoint"],
                iteration=raw["iteration"],
                previous_work=raw["previous_node_work"],
                total_work=raw["total_node_work"],
                last_iteration_visits=raw["last_iteration_work"],
                initialization_visits=raw["initialization_work"],
                sampled_traversals=raw["sampled_traversals"],
                guard_sha256=raw["guard_sha256"],
                current_sha256=current,
                current_policy_sha256=current,
                readouts={
                    w: dict(
                        policy_sha256=array_sha(policies[w]),
                        state_sha256=readout_fingerprint(
                            context.scoring.partition, raw, arrays, policies, w
                        ),
                    )
                    for w in ("uniform", "linear")
                },
                mass_sha256={
                    w: array_sha(arrays[w + "_sum"]) for w in ("uniform", "linear")
                },
            )
        )
    return tuple(result)


def load_contexts(root: Path) -> dict[tuple[str, str], Context]:
    return original.game_contexts(root, "real")
