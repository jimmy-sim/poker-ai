"""Fictional-only lift, half-mixture, and failure-retention proof."""

import json
import os
import time
from pathlib import Path
from typing import Any

import numpy as np

from known_turn_half_policy_mixture.gate import (
    clean_head,
    require_source,
    source_fingerprint,
)
from known_turn_half_policy_mixture.math import half_mix


def _save(path: Path, value: dict[str, Any]) -> None:
    with path.open("x") as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def fictional() -> dict[str, Any]:
    """Check a two-group lift and rejection of a corrupted fictional parent."""
    mapping = np.arange(8340) % 2
    abstract = np.array([[0.2, 0.8], [0.7, 0.3]], dtype=np.float64)
    other = np.tile(np.array([0.6, 0.4]), (8340, 1))
    legal = np.ones((8340, 2), dtype=np.float64)
    mixed = half_mix(abstract[mapping], other, legal)
    if not np.allclose(mixed[::2], [0.4, 0.6], rtol=0, atol=1e-15) or not np.allclose(
        mixed[1::2], [0.65, 0.35], rtol=0, atol=1e-15
    ):
        raise ArithmeticError("fictional lift/mixture arithmetic failed")
    damaged = other.copy()
    damaged[17] = [0.9, 0.9]
    try:
        half_mix(abstract[mapping], damaged, legal)
    except ArithmeticError:
        rejected = True
    else:
        rejected = False
    if not rejected:
        raise ArithmeticError("fictional invalid parent was accepted")
    return {
        "status": "proof_passed",
        "fictional_rows": 8340,
        "abstract_groups": 2,
        "weight_each": 0.5,
        "even_first_action": float(mixed[0, 0]),
        "odd_first_action": float(mixed[1, 0]),
        "invalid_parent_rejected": rejected,
        "real_policy_opened": False,
    }


def run(root: Path, output: Path) -> None:
    """Retain one bounded proof and its partial/failure state."""
    started = time.perf_counter()
    head = clean_head(root)
    fingerprint = source_fingerprint(root)
    require_source(root, fingerprint)
    if output.exists():
        raise FileExistsError("retain prior half-mixture proof")
    output.mkdir(parents=True)
    _save(
        output / "started.json",
        {
            "status": "started",
            "head": head,
            "source_fingerprint": fingerprint,
            "real_policy_opened": False,
        },
    )
    try:
        result = fictional()
        elapsed = time.perf_counter() - started
        if elapsed >= 180:
            raise TimeoutError("half-mixture proof cap reached")
        _save(
            output / "result.json",
            {
                **result,
                "head": head,
                "source_fingerprint": fingerprint,
                "seconds": elapsed,
            },
        )
    except BaseException as error:
        _save(
            output / "failure.json",
            {
                "status": "failed_retained",
                "head": head,
                "source_fingerprint": fingerprint,
                "seconds": time.perf_counter() - started,
                "failure": {"type": type(error).__name__, "reason": str(error)},
            },
        )
        raise
