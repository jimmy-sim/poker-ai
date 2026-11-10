"""Source-bound kernel-only checks, explicitly insufficient for real admission."""

import json
import time
from pathlib import Path
from typing import Any

from poker_ai.evaluation.private_prefix_math import proofs
from poker_ai.evaluation.private_prefix_oracle import parity
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.learning_run import persist
from poker_ai.postflop.parallel_profile import finite, same
from poker_ai.postflop.pipeline_report import check_source
from poker_ai.postflop.river_study import digest
from poker_ai.reproducibility import runtime_environment
from poker_ai.validation.five_card import source_provenance

CONFIG = "configs/private-prefix-stratification.json"
CONFIG_SHA = "d992c619b1b25b76ceca07fbe2e1dea69a9c8775b462d6f55fca1fec78de1c3a"
ENTRY = "scripts/check_private_prefix.py"
FORMAT = "poker-ai-private-prefix-kernel-correctness-v1"
STATUS = "passed_kernel_correctness_only_not_study_admission"


def contract(root: Path) -> dict[str, Any]:
    if digest(root / CONFIG) != CONFIG_SHA:
        raise ArithmeticError("prospective private-prefix protocol changed")
    config: dict[str, Any] = json.loads((root / CONFIG).read_text())
    if any(digest(root / p) != h for p, h in config["input_sha256"].items()):
        raise ArithmeticError("private-prefix pinned parent receipt changed")
    return config


def run(root: Path, output: Path) -> dict[str, Any]:
    if output.exists() or output.is_symlink() or output.with_suffix(".tmp").exists():
        raise FileExistsError("retain existing private-prefix correctness output")
    started = time.perf_counter()
    saved: dict[str, Any] = dict(
        format=FORMAT,
        status="running",
        failure=None,
        source=None,
        source_sha256=None,
        config=None,
        math=[],
        trajectories=[],
        environment=runtime_environment(),
        scope="NONUNIFORM_KUHN_KERNEL_ONLY_NOT_FULL_PIPELINE_PROOF",
        real_poker_training_performed=False,
        reference_constructed=False,
        full_shape_proof_complete=False,
        forecast_complete=False,
        long_run_admitted=False,
    )
    try:
        saved["config"] = contract(root)
        source = source_provenance(root, root / CONFIG, entrypoints=(ENTRY,))
        check_source(root, source)
        saved.update(source=source, source_sha256=sha(source["sha256"]))
        persist(output, saved)
        saved["math"] = proofs()
        persist(output, saved)
        saved["trajectories"] = parity()
        saved["status"] = STATUS
    except BaseException as error:
        saved.update(
            status="failed_kernel_correctness_not_admitted",
            failure=dict(type=type(error).__name__, reason=str(error)),
        )
        raise
    finally:
        saved["seconds"] = time.perf_counter() - started
        persist(output, saved)
    return saved


def replay(root: Path, path: Path) -> dict[str, Any]:
    saved: dict[str, Any] = json.loads(path.read_text())
    json.dumps(saved, allow_nan=False)
    expected_header = dict(
        format=FORMAT,
        status=STATUS,
        failure=None,
        config=contract(root),
        scope="NONUNIFORM_KUHN_KERNEL_ONLY_NOT_FULL_PIPELINE_PROOF",
        real_poker_training_performed=False,
        reference_constructed=False,
        full_shape_proof_complete=False,
        forecast_complete=False,
        long_run_admitted=False,
    )
    if any(not same(saved.get(k), v) for k, v in expected_header.items()) or not finite(
        saved.get("seconds"), positive=True
    ):
        raise ArithmeticError("changed or partial private-prefix kernel header")
    check_source(root, saved["source"])
    if sha(saved["source"]["sha256"]) != saved["source_sha256"]:
        raise ArithmeticError("private-prefix kernel source inventory changed")
    if not same(saved["math"], proofs()) or not same(saved["trajectories"], parity()):
        raise ArithmeticError("private-prefix independent kernel checks changed")
    return saved
