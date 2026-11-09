"""Saved current/average sources; no learner or reference strategy inputs."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from poker_ai.evaluation.averaging_history_inputs import HistoryInputs
from poker_ai.evaluation.averaging_history_replay import archive_path
from poker_ai.evaluation.frozen_batch_validation import full_sources
from poker_ai.evaluation.reduced_study_run import read_saved
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.river_study import digest
from poker_ai.solver_validation.reduced_batches import read as read_native
from poker_ai.validation.five_card import source_provenance

CONFIG = "configs/batch-current-diagnosis.json"
CONFIG_SHA = "3f453a0cbc28558bd5dbad0996cea0941da28a69b1b0d3c5ba40b395e2b3dcde"
FORMAT = "poker-ai-saved-batch-current-diagnosis-v1"
FOLDER = "results/batch-current-diagnosis/"
CHECKS = FOLDER + "code-checks.json"
ADMITTED = FOLDER + "admission.json"
ENTRIES = tuple(
    "scripts/" + n + "_batch_currents.py"
    for n in ("check", "diagnose", "audit", "report")
)


@dataclass(frozen=True)
class Sources:
    own_path: Path
    own: dict[str, Any]
    data: HistoryInputs
    native: dict[str, Any]


def config_inputs(root: Path) -> dict[str, Any]:
    if digest(root / CONFIG) != CONFIG_SHA:
        raise ArithmeticError("fixed batch-current protocol changed")
    config: dict[str, Any] = json.loads((root / CONFIG).read_text())
    return config


def source(root: Path) -> dict[str, Any]:
    return source_provenance(root, root / CONFIG, entrypoints=ENTRIES)


def binding(root: Path) -> tuple[dict[str, Any], str]:
    current = source(root)
    if current["dirty"] is not False:
        raise ValueError("publish checked current-diagnosis source first")
    return current, sha(current["sha256"])


def load(root: Path) -> Sources:
    config = config_inputs(root)
    path = root / config["source_own"]
    own, data = read_saved(root, path)
    proof = read_native(root, root / config["source_native"], own, path)
    if proof["profiles"] != 480 or proof["maximum_error_chips"] > 1e-9:
        raise ArithmeticError("complete source independent audit required")
    for k in ("details", "mass_details", "current_details"):
        if digest(archive_path(path, own[k + "_file"])) != own[k + "_sha256"]:
            raise ArithmeticError("source batch archive bytes changed")
    if (
        own["current_details_file"] != config["source_current_archive"]
        or len(own["currents"]) != 216
    ):
        raise ArithmeticError("saved current source grid changed")
    controls = full_sources(data)
    if len(controls) != 16:
        raise ArithmeticError("original full control grid incomplete")
    return Sources(path, own, data, proof)


def candidates(sources: Sources) -> list[dict[str, Any]]:
    final = sources.own["config"]["work_labels"][-1]
    result = []
    for key, variant in (("currents", "current"), ("rows", "average")):
        for row in sources.own[key]:
            if row["path_index"] >= 72 or row["work_label"] != final:
                continue
            kind = (
                variant
                if variant == "current"
                else row["case"]["average_weight"] + "_average"
            )
            result.append(
                dict(
                    id=row["id"],
                    path_index=row["path_index"],
                    case=row["case"],
                    work_label=row["work_label"],
                    batch_size=row["batch_size"],
                    variant=kind,
                    policy_sha256=row["receipt"]["policy_sha256"],
                )
            )
    result.sort(key=lambda r: r["id"])
    if len(result) != 216 or len({r["id"] for r in result}) != 216:
        raise ArithmeticError("final current/average candidates missing or duplicate")
    return result


def source_hashes(root: Path, sources: Sources) -> dict[str, str]:
    config = config_inputs(root)
    paths = [config["source_own"], config["source_native"]]
    result = {p: digest(root / p) for p in paths}
    for key in ("details", "mass_details", "current_details"):
        p = archive_path(sources.own_path, sources.own[key + "_file"])
        result[str(p.relative_to(root))] = digest(p)
    return result
