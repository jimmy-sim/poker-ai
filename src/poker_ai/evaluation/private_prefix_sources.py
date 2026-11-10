"""Read-only pinned source/context factories; no learner or native construction.

Used old archives are fully checked by the original loader. The later matched
study is a pinned parent receipt/native-schema/original-B1-crossing prerequisite;
its new-prefix policy archive is NOT used or claimed to be rescored here.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from poker_ai.evaluation import matched_update_inputs as parent
from poker_ai.evaluation import private_prefix_correctness as kernel
from poker_ai.evaluation.batch_current_checks import checked_tree
from poker_ai.evaluation.matched_update_capture import barrier
from poker_ai.evaluation.matched_update_lifecycle import measured
from poker_ai.evaluation.private_prefix_design import Design, index_rows
from poker_ai.postflop.controlled_scoring import ScoringContext
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.parallel_profile import same
from poker_ai.postflop.pipeline_report import check_source
from poker_ai.postflop.river_study import digest
from poker_ai.solver_validation.matched_updates import (
    validate as validate_parent_native,
)
from poker_ai.validation.five_card import source_provenance

CONFIG = "configs/private-prefix-pipeline-v2.json"
CONFIG_SHA = "7420d0a45148a161c4e9de9aa9018691bd7ab518711fbed6a173be351171079a"
ENTRY = "scripts/validate_private_prefix_pipeline.py"
FOLDER = "results/private-prefix/"


def contract(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    config = kernel.contract(root)
    if digest(root / CONFIG) != CONFIG_SHA:
        raise ArithmeticError("private-prefix complete pipeline contract changed")
    driver: dict[str, Any] = json.loads((root / CONFIG).read_text())
    if (
        driver["parent_config"] != kernel.CONFIG
        or driver["parent_sha256"] != kernel.CONFIG_SHA
    ):
        raise ArithmeticError("private-prefix parent protocol changed")
    if (
        digest(root / driver["superseded_driver_config"])
        != driver["superseded_driver_sha256"]
    ):
        raise ArithmeticError("superseded accounting record changed")
    return config, driver


def source(root: Path) -> dict[str, Any]:
    contract(root)
    result: dict[str, Any] = source_provenance(
        root, root / kernel.CONFIG, entrypoints=(ENTRY,)
    )
    result["sha256"][CONFIG] = digest(root / CONFIG)
    return result


def kernel_evidence(root: Path) -> dict[str, str]:
    """Verify published-kernel receipt/schema and its observed exact-source CI.

    This reads the retained completed kernel checks; it does not rerun its toy
    learners inside a supposedly read-only real-data input stage.
    """
    _, driver = contract(root)
    receipt_path, checks_path = (
        root / driver["kernel_receipt"],
        root / driver["kernel_checks"],
    )
    saved, checks = (
        json.loads(receipt_path.read_text()),
        json.loads(checks_path.read_text()),
    )
    check_source(root, saved["source"])
    check_source(root, checks["source"])
    if (
        saved["format"] != kernel.FORMAT
        or saved["status"] != kernel.STATUS
        or saved["failure"] is not None
        or len(saved["math"]) != 12
        or len(saved["trajectories"]) != 120
        or sum(r["B1_original_bit_match"] for r in saved["trajectories"]) != 40
        or saved["source_sha256"] != sha(saved["source"]["sha256"])
        or checks["source_sha256"] != saved["source_sha256"]
        or not same(checks["source"]["sha256"], saved["source"]["sha256"])
        or checks["status"] != "kernel_source_checks_passed_not_admission"
        or not same(
            checks["hosted_jobs"], {"Python 3.11": "success", "Python 3.12": "success"}
        )
        or set(checks["local"]) != {"base311", "base312", "optional311", "optional312"}
        or any(checks["local"][k]["status"] != "passed" for k in checks["local"])
        or any(
            saved[k] is not False
            for k in (
                "real_poker_training_performed",
                "reference_constructed",
                "full_shape_proof_complete",
                "forecast_complete",
                "long_run_admitted",
            )
        )
    ):
        raise ArithmeticError(
            "complete checked kernel evidence required, not admission"
        )
    checked_tree(root, checks["checked_commit"], checks["source"]["sha256"])
    return {
        driver["kernel_receipt"]: digest(receipt_path),
        driver["kernel_checks"]: digest(checks_path),
    }


@dataclass(frozen=True)
class Sources:
    parent: parent.Sources
    design: Design
    input_sha256: dict[str, str]
    averages: dict[Any, Any]
    currents: dict[Any, Any]
    masses: dict[Any, Any]
    scored_currents: dict[Any, Any]

    def context(self, index: int) -> ScoringContext:
        if type(index) is not int or not 0 <= index < 48:
            raise ValueError("private-prefix source path outside full grid")
        return self.parent.context(index % 24)


def load(root: Path) -> Sources:
    config, _ = contract(root)
    hashes = {**config["input_sha256"], **kernel_evidence(root)}
    old = parent.load(root)
    # The completed real parent already performed the original-runtime B1 replay.
    # Verify its exact original checkpoints against the now-loaded source inputs.
    path = root / "results/matched-update-study/own.json"
    own = json.loads(path.read_text())
    native = json.loads((root / "results/matched-update-study/native.json").read_text())
    check_source(root, own["source"])
    check_source(root, native["source"])
    measured(root, path, "study")
    measured(root, root / "results/matched-update-study/native.json", "real_native")
    if own["status"] != "completed_own_native_pending" or own["failure"] is not None:
        raise ArithmeticError("completed real matched-update parent required")
    validate_parent_native(native, own, path)
    barrier(
        own["checkpoints"],
        [old.original(i, w) for i in range(24) for w in (100000, 1000000, 10000000)],
    )
    design = Design.build(config, mode="real")
    original = old.archived.own
    result = Sources(
        old,
        design,
        hashes,
        index_rows(
            [r for r in original["rows"] if r["path_index"] < 72],
            ("path_index", "work_label", "id"),
        ),
        index_rows(original["currents"], ("path_index", "work_label")),
        index_rows(original["masses"], ("path_index", "work_label", "id")),
        {r["id"]: r for r in old.scored_currents.values()},
    )
    if (
        len(result.averages),
        len(result.currents),
        len(result.masses),
        len(result.scored_currents),
    ) != (432, 216, 432, 216):
        raise ArithmeticError("complete original baseline inventory required")
    if any(digest(root / p) != h for p, h in hashes.items()):
        raise ArithmeticError("private-prefix input bytes changed while loading")
    return result
