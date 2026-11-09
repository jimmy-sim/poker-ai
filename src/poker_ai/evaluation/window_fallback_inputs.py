"""Pinned completed OWN windows; archived native scalars are prerequisites only."""

import json
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from poker_ai.evaluation import averaging_history_run
from poker_ai.evaluation.averaging_history_artifacts import array_sha, decode_mass
from poker_ai.evaluation.averaging_history_inputs import HistoryInputs
from poker_ai.evaluation.averaging_history_math import window_mass
from poker_ai.evaluation.averaging_history_replay import archive_path
from poker_ai.evaluation.controlled_reply_inputs import SourcePolicy
from poker_ai.evaluation.window_fallback_math import LABELS, MASKS
from poker_ai.finite import FloatArray
from poker_ai.postflop.controlled_checkpoints import unpack_policy
from poker_ai.postflop.controlled_scoring import BoolArray, ScoringContext
from poker_ai.postflop.learning_artifacts import decode, read_archive
from poker_ai.postflop.parallel_profile import same
from poker_ai.postflop.pipeline_report import check_source
from poker_ai.postflop.river_study import Deadline, digest

CONFIG = "configs/window-fallback.json"
ENTRIES = (
    "scripts/diagnose_window_fallback.py",
    "scripts/audit_window_fallback.py",
    "scripts/report_window_fallback.py",
)
PINS = {
    "configs/averaging-history.json",
    "results/averaging-history/correctness.json",
    "results/averaging-history/admission.json",
    "results/averaging-history/own.json",
    "results/averaging-history/own-profiles.jsonl.gz",
    "results/averaging-history/own-masses.jsonl.gz",
    "results/averaging-history/native.json",
}


def validate_config(config: dict[str, Any]) -> None:
    fixed = dict(
        schema_version=1,
        status="preregistered_saved_window_fallback_intervention_no_training",
        source_report="results/averaging-history/own.json",
        source_native="results/averaging-history/native.json",
        spot_files=[
            "configs/learning-spots/dev_low_oop.json",
            "configs/learning-spots/dev_medium_oop.json",
        ],
        representations=["exact", "texture_range_q8_b8"],
        traversals=["full", "external"],
        seeds=[20261301, 20261302, 20261303],
        regret_rules=["signed", "clipped"],
        average_weights=["uniform", "linear"],
        suffix_variants=["suffix_5m_10m", "suffix_9m_10m"],
        fill_masks=[list(t) for t in MASKS],
        fill_labels=list(LABELS),
        fixed_opponent_fill_labels=["raw", "fill_both"],
        expected_source_cases=64,
        expected_source_windows=128,
        expected_self_profiles=512,
        expected_fixed_target_conditions=2048,
        expected_raw_window_controls=128,
        expected_full_windows=32,
        expected_additivity_panels=128,
        maximum_own_seconds=900,
        maximum_native_seconds=900,
        tolerance_chips=1e-9,
        tolerance_unitless=1e-12,
    )
    reference = dict(
        name="OpenSpiel",
        version="2.0.2",
        license="Apache-2.0",
        license_sha256="cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30",
    )
    if (
        any(not same(config[k], v) for k, v in fixed.items())
        or set(config["input_sha256"]) != PINS
        or any(not same(config["native_reference"][k], v) for k, v in reference.items())
    ):
        raise ArithmeticError("window fallback selection, tolerance or budget changed")


def inputs(root: Path) -> dict[str, Any]:
    config: dict[str, Any] = json.loads((root / CONFIG).read_text())
    validate_config(config)
    if any(digest(root / p) != value for p, value in config["input_sha256"].items()):
        raise ArithmeticError("window fallback source bytes changed")
    return config


@dataclass(frozen=True)
class FallbackInputs:
    config: dict[str, Any]
    history: HistoryInputs
    saved: dict[str, Any]
    path: Path
    replay: dict[str, Any]
    native: dict[str, Any]


def load(root: Path, deadline: Deadline) -> FallbackInputs:
    """Only read/replay old policies; no new learner or native constructor."""
    from poker_ai.solver_validation.averaging_history import validate

    config = inputs(root)
    path = root / config["source_report"]
    saved, history, proof = averaging_history_run.replay(root, path, deadline)
    native = json.loads((root / config["source_native"]).read_text())
    check_source(root, native["source"])
    native_proof = validate(native, saved, path, history)
    deadline.check()
    return FallbackInputs(config, history, saved, path, proof, native_proof)


@dataclass(frozen=True)
class Window:
    index: int
    source: SourcePolicy
    row: dict[str, Any]
    context: ScoringContext
    policy: FloatArray
    mass: FloatArray
    river: BoolArray


def windows(data: FallbackInputs, deadline: Deadline) -> Iterator[Window]:
    """Retain one source case's dense arrays at a time; recheck every raw window."""
    saved, history, path = data.saved, data.history, data.path
    profiles = read_archive(
        archive_path(path, saved["details_file"]),
        saved["details_sha256"],
        saved["rows"],
    )
    masses = read_archive(
        archive_path(path, saved["mass_details_file"]),
        saved["mass_details_sha256"],
        saved["masses"],
    )
    count = 0
    for index, source in enumerate(history.base.policies):
        deadline.check()
        context = history.base.context(source.case)
        tree = context.partition
        first = np.unique(context.exact_to_partition, return_index=True)[1]
        river = (context.river_masks[0] | context.river_masks[1])[first]
        boundaries = {}
        for order, label in enumerate(history.config["cumulative_mass_work_labels"]):
            row, blob = next(masses)
            if not same(
                [row["index"], row["order"], row["work_label"]], [index, order, label]
            ):
                raise ArithmeticError("window source mass stream changed")
            boundaries[label] = decode_mass(blob, tree, row)
        for order in range(8):
            row, blob = next(profiles)
            if not same([row["index"], row["order"]], [index, order]):
                raise ArithmeticError("window source policy stream changed")
            if order < 5:
                continue
            policy = unpack_policy(tree, decode(blob, context, row)["policy"])
            if order == 5:
                if array_sha(policy) != array_sha(source.policy):
                    raise ArithmeticError("window whole average differs from source")
                continue
            left, right = history.config["suffix_windows"][order - 6]
            mass = window_mass(tree, boundaries[left], boundaries[right])
            if policy.tobytes() != tree.normalize(mass).tobytes():
                raise ArithmeticError("window source does not reconstruct from mass")
            policy.flags.writeable = river.flags.writeable = False
            yield Window(count, source, row, context, policy, mass, river)
            count += 1
    if (
        next(profiles, None) is not None
        or next(masses, None) is not None
        or count != 128
    ):
        raise ArithmeticError("window source archive inventory incomplete or extended")
