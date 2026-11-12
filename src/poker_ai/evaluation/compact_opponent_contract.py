"""Prospective compact-learner design; contains no saved policies or references."""

import json
from pathlib import Path
from typing import Any

from poker_ai.postflop.river_study import digest

CONFIG = "configs/compact-own-opponent-learning.json"
CONFIG_SHA = "46922073b88796463ae5c911e6de5eea29de788f7b3fbd3e96275d11c9845d8d"
COST_CONFIG = "configs/compact-own-opponent-cost-standins.json"
COST_CONFIG_SHA = "bf590525ab8c1cb206d6b1afb6562ce4c628ad3943edc93a33259eb181c58ca3"
FOLDER = "results/compact-own-opponent-learning"


def contract(root: Path) -> dict[str, Any]:
    if digest(root / CONFIG) != CONFIG_SHA:
        raise ArithmeticError("prospective compact own-opponent design changed")
    result: dict[str, Any] = json.loads((root / CONFIG).read_text())
    return result


def cost_contract(root: Path) -> dict[str, Any]:
    if digest(root / COST_CONFIG) != COST_CONFIG_SHA:
        raise ArithmeticError("prospective compact cost projection changed")
    result: dict[str, Any] = json.loads((root / COST_CONFIG).read_text())
    if result["parent_config"] != CONFIG or result["parent_sha256"] != CONFIG_SHA:
        raise ArithmeticError("compact cost contract names a different parent")
    contract(root)
    return result


def input_pins(root: Path) -> dict[str, str]:
    pins: dict[str, str] = contract(root)["input_sha256"]
    for filename, expected in pins.items():
        path = root / filename
        if (
            path.is_symlink()
            or not path.resolve().is_relative_to(root.resolve())
            or digest(path) != expected
        ):
            raise ArithmeticError("compact own-opponent input path/bytes changed")
    return dict(pins)
