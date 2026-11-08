"""Select all prespecified frozen OWN profiles; never construct a trained agent."""

import itertools
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from poker_ai.finite import FloatArray
from poker_ai.postflop import learning_protocol, pipeline_cost
from poker_ai.postflop.controlled_checkpoints import unpack_policy
from poker_ai.postflop.controlled_scoring import ScoringContext
from poker_ai.postflop.learning_artifacts import decode, read_archive
from poker_ai.postflop.parallel_profile import same
from poker_ai.postflop.pipeline_report import check_source
from poker_ai.postflop.river_study import digest

CONFIG = "configs/controlled-reply-diagnosis.json"
ENTRIES = (
    "scripts/diagnose_controlled_replies.py",
    "scripts/audit_controlled_replies.py",
    "scripts/report_controlled_replies.py",
    "scripts/inspect_controlled_reply.py",
)
FORMAT = "poker-ai-controlled-within-reply-diagnosis-v1"
TRACE_FORMAT = "poker-ai-controlled-within-loss-traces-v1"
GROUP = ("spot_file", "representation", "traversal", "seed")
MODE = ("regret_rule", "average_weight")
KEY = (*GROUP, *MODE)


def identity(case: dict[str, Any], fields: tuple[str, ...] = KEY) -> str:
    return json.dumps({k: case[k] for k in fields}, sort_keys=True)


def modes(config: dict[str, Any]) -> list[tuple[str, str]]:
    return list(itertools.product(config["regret_rules"], config["average_weights"]))


def expected(config: dict[str, Any]) -> set[str]:
    return {
        identity(
            dict(
                spot_file=game,
                representation=name,
                traversal=traversal,
                seed=seed,
                regret_rule=clip,
                average_weight=weight,
            )
        )
        for game, name, traversal, clip, weight in itertools.product(
            config["spot_files"],
            config["representations"],
            config["traversals"],
            config["regret_rules"],
            config["average_weights"],
        )
        for seed in (config["seeds"] if traversal == "external" else [None])
    }


def validate_config(config: dict[str, Any]) -> None:
    fixed = dict(
        schema_version=1,
        status="preregistered_saved_policy_diagnosis_no_new_postflop_training",
        source_report="results/controlled-learning/own.json",
        source_audit="results/controlled-learning/native.json",
        source_axis="work",
        source_target=10000000,
        regret_weight="linear",
        regret_rules=["signed", "clipped"],
        average_weights=["uniform", "linear"],
        spot_files=[
            "configs/learning-spots/dev_low_oop.json",
            "configs/learning-spots/dev_medium_oop.json",
        ],
        representations=["exact", "texture_range_q8_b8"],
        traversals=["full", "external"],
        seeds=[20261301, 20261302, 20261303],
        expected_source_profiles=64,
        expected_self_target_traces=128,
        expected_cross_profiles=256,
        expected_cross_target_conditions=512,
        maximum_own_seconds=900,
        maximum_native_seconds=900,
        tolerance_chips=1e-9,
        tolerance_unitless=1e-12,
    )
    reference = config["native_reference"]
    pinned_reference = dict(
        name="OpenSpiel",
        version="2.0.2",
        license="Apache-2.0",
        license_sha256=(
            "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30"
        ),
    )
    pins = {
        "configs/controlled-learning-comparison.json",
        "configs/training-isolation.json",
        "results/controlled-learning/own.json",
        "results/controlled-learning/own-profiles.jsonl.gz",
        "results/controlled-learning/native.json",
        "results/controlled-learning/report/summary.json",
    }
    if (
        any(not same(config[k], v) for k, v in fixed.items())
        or set(config["input_sha256"]) != pins
        or any(not same(reference[k], v) for k, v in pinned_reference.items())
    ):
        raise ArithmeticError("controlled reply protocol/prerequisite changed")


def config_inputs(root: Path) -> dict[str, Any]:
    config: dict[str, Any] = json.loads((root / CONFIG).read_text())
    validate_config(config)
    if any(digest(root / p) != value for p, value in config["input_sha256"].items()):
        raise ArithmeticError("controlled reply input hash changed")
    return config


@dataclass(frozen=True)
class SourcePolicy:
    case: dict[str, Any]
    row: dict[str, Any]
    policy: FloatArray

    @property
    def identifier(self) -> str:
        return identity(self.case)

    @property
    def group(self) -> str:
        return identity(self.case, GROUP)

    @property
    def mode(self) -> tuple[str, str]:
        return self.case["regret_rule"], self.case["average_weight"]


@dataclass(frozen=True)
class Inputs:
    config: dict[str, Any]
    original: dict[str, Any]
    contexts: dict[tuple[str, str], ScoringContext]
    policies: tuple[SourcePolicy, ...]

    def context(self, case: dict[str, Any]) -> ScoringContext:
        return self.contexts[case["spot_file"], case["representation"]]


def selected(row: dict[str, Any], config: dict[str, Any]) -> bool:
    case = row["case"]
    return (
        case["bridge"] == "common"
        and case["regret_weight"] == config["regret_weight"]
        and [config["source_axis"], config["source_target"]] in row["labels"]
    )


def load(root: Path) -> Inputs:
    """Check archived native scalars, then stream only the sixty-four own policies.

    The reference namespace's validate function is data-only. It constructs no
    native game/solver/policy and requires no installed reference package. Its
    output never enters a learning algorithm; this module is frozen-policy diagnosis.
    """
    from poker_ai.solver_validation.controlled_learning import validate

    config = config_inputs(root)
    path = root / config["source_report"]
    original, comparison = learning_protocol.read_own(root, path)
    native = json.loads((root / config["source_audit"]).read_text())
    check_source(root, native["source"])
    validate(native, original, path)
    contexts = pipeline_cost.contexts(root, comparison)
    policies = []
    for row, blob in read_archive(
        path.with_name(original["details_file"]),
        original["details_sha256"],
        original["rows"],
    ):
        if not selected(row, config):
            continue
        context = contexts[row["case"]["spot_file"], row["case"]["representation"]]
        detail = decode(blob, context, row)
        policy = unpack_policy(context.partition, detail["policy"])
        policy.flags.writeable = False
        policies.append(SourcePolicy(dict(row["case"]), row, policy))
    ids = [p.identifier for p in policies]
    if len(ids) != 64 or len(set(ids)) != 64 or set(ids) != expected(config):
        raise ArithmeticError("frozen controlled source selection incomplete")
    policies.sort(key=lambda p: p.identifier)
    return Inputs(config, original, contexts, tuple(policies))
