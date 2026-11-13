"""New execution contract; the scientific comparison remains byte-identical."""

import json
from pathlib import Path
from typing import Any

from poker_ai.evaluation.compact_opponent_contract import contract as science
from poker_ai.evaluation.compact_opponent_contract import cost_contract as cost_contract
from poker_ai.evaluation.compact_opponent_contract import input_pins as input_pins
from poker_ai.postflop.river_study import digest

CONFIG = "configs/compact-cached-pipeline.json"
CONFIG_SHA = "0a2c16e32779ab6909e749d70da30fadb683905d8fa9038bbe5d16319a89e02b"
FOLDER = "results/compact-cached-learning"


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
    return saved


def contract(root: Path) -> dict[str, Any]:
    variant(root)
    return science(root)
