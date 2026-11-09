"""Explicit new-study inputs; all scientific fields delegate the frozen design."""

import json
from pathlib import Path
from typing import Any

from poker_ai.evaluation import frozen_batch_inputs as old
from poker_ai.evaluation.batch_reduction_measure import trainer as trainer
from poker_ai.evaluation.frozen_batch_inputs import WEIGHTS as WEIGHTS
from poker_ai.evaluation.frozen_batch_inputs import case as case
from poker_ai.evaluation.frozen_batch_inputs import check_prefix as check_prefix
from poker_ai.evaluation.frozen_batch_inputs import paths as paths
from poker_ai.evaluation.frozen_batch_inputs import prefix_map as prefix_map
from poker_ai.evaluation.frozen_batch_inputs import prerequisites as prerequisites
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.parallel_profile import same
from poker_ai.postflop.river_study import digest
from poker_ai.validation.five_card import source_provenance

CONFIG = "configs/reduced-batch-study.json"
CONFIG_SHA = "767bbfa378e9935980e08f3925ef277c0507e8c5b91b1f855fc4e19828f3cfb5"
FORMAT = "poker-ai-reduced-dispatch-batch-study-v1"
FOLDER = "results/reduced-batch-study/"
SOFTWARE = FOLDER + "correctness.json"
CHECKS = FOLDER + "code-checks.json"
ADMITTED = FOLDER + "admission.json"
ENTRIES = tuple(
    "scripts/" + n + "_reduced_batches.py"
    for n in ("check", "study", "audit", "report")
)


def protocol(root: Path) -> dict[str, Any]:
    if digest(root / CONFIG) != CONFIG_SHA:
        raise ArithmeticError("fixed reduced-study protocol changed")
    p: dict[str, Any] = json.loads((root / CONFIG).read_text())
    base = old.config_inputs(root)
    for k in (
        "worker_count",
        "start_method",
        "work_labels",
        "maximum_own_seconds",
        "maximum_native_seconds",
        "tolerance_chips",
        "tolerance_unitless",
    ):
        if not same(p[k], base[k]):
            raise ArithmeticError("reduced study changed frozen design")
    return p


def config_inputs(root: Path) -> dict[str, Any]:
    protocol(root)
    return old.config_inputs(root)


def source(root: Path) -> dict[str, Any]:
    return source_provenance(root, root / CONFIG, entrypoints=ENTRIES)


def binding(root: Path) -> tuple[dict[str, Any], str]:
    current = source(root)
    if current["dirty"] is not False:
        raise ValueError("publish reduced-study source first")
    return current, sha(current["sha256"])
