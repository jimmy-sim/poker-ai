"""Read-only complete graph and semantic checks for archived prerequisites."""

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from context_reuse_support import Graph

from poker_ai.evaluation.averaging_history_inputs import HistoryInputs
from poker_ai.evaluation.controlled_reply_inputs import Inputs, SourcePolicy
from poker_ai.evaluation.controlled_reply_math import Reply
from poker_ai.evaluation.frozen_batch_inputs import CONFIG as BATCH_CONFIG
from poker_ai.evaluation.frozen_batch_inputs import config_inputs
from poker_ai.postflop.river_study import digest


class PrerequisiteGraph(Graph):
    """The existing exact graph witness plus the four prerequisite records."""

    def __init__(self) -> None:
        super().__init__()
        self.allowed = (*self.allowed, HistoryInputs, Inputs, SourcePolicy, Reply)


@dataclass(frozen=True)
class Observation:
    witness: str
    semantic_sha256: str
    mutable_count: int
    array_count: int


def semantic_inventory(data: HistoryInputs) -> dict[str, Any]:
    """Check independent expected inventories; no selected game is recomputed."""
    policies = data.base.policies
    identifiers = [policy.identifier for policy in policies]
    labels = data.config["original_average_replay_labels"]
    if (
        len(policies) != 64
        or len(set(identifiers)) != 64
        or len(data.prefixes) != 192
        or len(data.replies) != 128
        or set(data.prefixes)
        != {(key, label) for key in identifiers for label in labels}
        or len(data.base.contexts) != 4
    ):
        raise ArithmeticError("prerequisite semantic inventory changed")
    return {
        "policy_ids": identifiers,
        "policy_sha256": [
            hashlib.sha256(p.policy.tobytes()).hexdigest() for p in policies
        ],
        "prefix_keys": sorted([key, label] for key, label in data.prefixes),
        "reply_keys": sorted([key, target] for key, target in data.replies),
        "context_keys": sorted([spot, rep] for spot, rep in data.base.contexts),
        "input_sha256": data.config["input_sha256"],
    }


def observe(data: HistoryInputs) -> tuple[PrerequisiteGraph, Observation]:
    graph = PrerequisiteGraph()
    graph.visit(data)
    semantic = semantic_inventory(data)
    encoded = json.dumps(semantic, sort_keys=True, separators=(",", ":")).encode()
    return graph, Observation(
        graph.hash.hexdigest(),
        hashlib.sha256(encoded).hexdigest(),
        len(graph.mutables),
        len(graph.arrays),
    )


def disjoint(left: PrerequisiteGraph, right: PrerequisiteGraph) -> None:
    """Fresh outputs may not share mutable objects or NumPy storage."""
    if left.mutables & right.mutables:
        raise ArithmeticError("fresh prerequisite graphs share mutable objects")
    if any(np.shares_memory(a, b) for a in left.arrays for b in right.arrays):
        raise ArithmeticError("fresh prerequisite graphs share array storage")


def pinned_bytes(root: Path) -> dict[str, str]:
    """Hash the declared prerequisite pins and audit protocol bytes."""
    from poker_ai.evaluation.averaging_history_inputs import CONFIG as HISTORY_CONFIG
    from poker_ai.evaluation.averaging_history_inputs import inputs

    batch = config_inputs(root)
    history = inputs(root)
    names = {
        BATCH_CONFIG,
        HISTORY_CONFIG,
        "uv.lock",
        *batch["input_sha256"],
        *history["input_sha256"],
    }
    return {name: digest(root / name) for name in sorted(names)}
