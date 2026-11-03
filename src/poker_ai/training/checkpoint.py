"""Atomic, non-pickle checkpoints for this project's own MCCFR state only."""

import json
import os
import tempfile
from pathlib import Path
from typing import Any, cast

import numpy as np
from numpy.random import PCG64, Generator

from poker_ai.training.mccfr import MCCFR, Method, RootFactory, Row

FORMAT = "poker-ai-own-mccfr-v1"


def save_checkpoint(
    solver: MCCFR, path: Path, *, config: dict[str, Any], provenance: dict[str, Any]
) -> None:
    """Save policy accumulators, iteration and exact PCG64 state atomically.

    Reference strategy artifacts are not accepted inputs to this format. Config
    and provenance describe the own training run; the caller supplies them.
    """
    if not isinstance(solver.rng.bit_generator, PCG64):
        raise ValueError("checkpoint format currently requires explicit PCG64")
    payload = {
        "format": FORMAT,
        "config": config,
        "source": provenance,
        "method": solver.method,
        "epsilon": solver.epsilon,
        "iteration": solver.iteration,
        "nodes_visited": solver.nodes_visited,
        "rng": solver.rng.bit_generator.state,
        "rows": [
            {
                "key": key,
                "actions": row.actions,
                "regrets": row.regrets.tolist(),
                "strategy_sum": row.strategy_sum.tolist(),
            }
            for key, row in sorted(solver.rows.items())
        ],
    }
    encoded = (
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
        + "\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", dir=path.parent, encoding="utf-8", delete=False
        ) as stream:
            temporary = Path(stream.name)
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def load_checkpoint(
    path: Path, root_factory: RootFactory, *, expected_config: dict[str, Any]
) -> MCCFR:
    """Restore an own checkpoint only after strict format/config/data checks."""
    payload = json.loads(path.read_text())
    fields = {
        "format",
        "config",
        "source",
        "method",
        "epsilon",
        "iteration",
        "nodes_visited",
        "rng",
        "rows",
    }
    if not isinstance(payload, dict) or set(payload) != fields:
        raise ValueError("invalid own checkpoint fields")
    if payload["format"] != FORMAT or payload["config"] != expected_config:
        raise ValueError("own checkpoint format/config mismatch")
    if payload["method"] not in ("external", "outcome"):
        raise ValueError("invalid sampling method")
    for field in ("iteration", "nodes_visited"):
        if type(payload[field]) is not int or payload[field] < 0:
            raise ValueError("invalid checkpoint counter")
    if (
        not isinstance(payload["rng"], dict)
        or payload["rng"].get("bit_generator") != "PCG64"
    ):
        raise ValueError("invalid checkpoint random generator")
    rng = Generator(PCG64(0))
    rng.bit_generator.state = payload["rng"]
    result = MCCFR(
        root_factory,
        rng,
        method=cast(Method, payload["method"]),
        epsilon=payload["epsilon"],
    )
    if not isinstance(payload["rows"], list):
        raise ValueError("invalid checkpoint rows")
    for row in payload["rows"]:
        if not isinstance(row, dict) or set(row) != {
            "key",
            "actions",
            "regrets",
            "strategy_sum",
        }:
            raise ValueError("invalid checkpoint information set")
        key, actions = row["key"], row["actions"]
        if (
            not isinstance(key, str)
            or key in result.rows
            or not isinstance(actions, list)
            or not actions
            or any(type(a) is not int for a in actions)
            or len(set(actions)) != len(actions)
        ):
            raise ValueError("invalid checkpoint key/actions")
        regrets = np.asarray(row["regrets"], dtype=np.float64)
        mass = np.asarray(row["strategy_sum"], dtype=np.float64)
        if (
            regrets.shape != (len(actions),)
            or mass.shape != regrets.shape
            or not np.all(np.isfinite(regrets))
            or not np.all(np.isfinite(mass))
            or np.any(mass < 0)
        ):
            raise ValueError("invalid checkpoint policy accumulators")
        result.rows[key] = Row(tuple(actions), regrets, mass)
    result.iteration = payload["iteration"]
    result.nodes_visited = payload["nodes_visited"]
    return result
