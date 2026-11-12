"""Frozen candidate definition and input/factory binding; constructs no learner."""

import json
from pathlib import Path
from typing import Any

from poker_ai.abstraction.model import CardAbstraction
from poker_ai.abstraction.public_range import PublicOwnRangeAbstraction
from poker_ai.postflop.game import load_spot
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.matrix import MatrixTree
from poker_ai.postflop.range_protocol import build_representation_control, range_context
from poker_ai.postflop.river_study import digest
from poker_ai.postflop.tree import SpotTree

CONFIG = "configs/compact-public-range.json"
CONFIG_SHA = "f2a5d7630580e8731c652c29363f970a361a76e10b040850e5bb57e546f31314"
SPEC_SHA = "794c4938ce7bbe9d1170fcc091e5dc5f02ab7583f58e776eec461a4cb07d5d70"
CANDIDATE = "texture_range_q8_own_q8_b8"


def validate(config: dict[str, Any]) -> None:
    if sha(config) != SPEC_SHA:
        raise ValueError("frozen compact public-range definition changed")


def contract(root: Path) -> dict[str, Any]:
    if digest(root / CONFIG) != CONFIG_SHA:
        raise ArithmeticError("published compact public-range config bytes changed")
    c: dict[str, Any] = json.loads((root / CONFIG).read_text())
    validate(c)
    return c


def check_inputs(root: Path, config: dict[str, Any]) -> dict[str, str]:
    validate(config)
    if any(
        digest(root / n) != checksum for n, checksum in config["input_sha256"].items()
    ):
        raise ArithmeticError("compact definition input hash changed")
    contexts = {
        n: range_context(load_spot(root / n)).identifier for n in config["spot_files"]
    }
    if contexts != config["contexts"]:
        raise ArithmeticError("canonical declared-prior contexts changed")
    return contexts


def build_control(source: SpotTree, name: str, model: CardAbstraction) -> MatrixTree:
    if name == CANDIDATE:
        return MatrixTree.build(
            source,
            "texture_b8",
            PublicOwnRangeAbstraction(model, range_context(source.spot)),
        )
    return build_representation_control(source, name, model)
