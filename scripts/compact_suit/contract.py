"""New execution contract; the scientific comparison remains byte-identical."""

import json
from pathlib import Path
from typing import Any

from poker_ai.evaluation.compact_opponent_contract import contract as science
from poker_ai.evaluation.compact_opponent_contract import cost_contract as cost_contract
from poker_ai.evaluation.compact_opponent_contract import input_pins as input_pins
from poker_ai.postflop.river_study import digest

CONFIG = "configs/compact-suit-pipeline.json"
CONFIG_SHA = "443f6a78b7d58bdf9c758bc5f31de31dacd9022a6698b11b3cce64bebc4bf2b0"
FOLDER = "results/compact-suit-learning"


def variant(root: Path) -> dict[str, Any]:
    if digest(root / CONFIG) != CONFIG_SHA:
        raise ArithmeticError("prospective cached execution contract changed")
    saved: dict[str, Any] = json.loads((root / CONFIG).read_text())
    for key in (
        "original_science",
        "original_cost",
        "cache_config",
        "cache_support",
        "historical_cache_manifest",
    ):
        if digest(root / saved[key]) != saved[key + "_sha256"]:
            raise ArithmeticError("pinned cached implementation dependency changed")
    for name, expected in saved["prerequisite_sha256"].items():
        path = root / name
        if (
            path.is_symlink()
            or not path.resolve().is_relative_to(root.resolve())
            or digest(path) != expected
        ):
            raise ArithmeticError("pinned suit-factorization evidence changed")
    return saved


def contract(root: Path) -> dict[str, Any]:
    variant(root)
    return science(root)


def require_prefix_runtime(root: Path) -> None:
    """Newer interpreters qualify software, not bit-exact real archive replay."""
    import sys

    import numpy as np

    expected = contract(root)["prefix_runtime"]
    if (
        sys.version.split()[0] != expected["python"]
        or np.__version__ != expected["numpy"]
    ):
        raise ArithmeticError(
            "original Python/NumPy runtime required for real archive mathematics"
        )
