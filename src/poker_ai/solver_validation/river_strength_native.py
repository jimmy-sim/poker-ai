"""Comparison-only independent scalars for published own river-strength policies."""

import hashlib
import json
import math
import os
import platform
import time
from collections.abc import Callable
from importlib.metadata import distribution, version
from pathlib import Path
from typing import Any

import numpy as np

from poker_ai.evaluation.river_strength_capture import replay_path
from poker_ai.evaluation.river_strength_learning import PathSpec, context, paths
from poker_ai.postflop.controlled_checkpoints import pack_policy, read_snapshot
from poker_ai.postflop.controlled_scoring import ScoringContext
from poker_ai.postflop.learning_training import score_data
from poker_ai.postflop.range_reply import compare as own_compare
from poker_ai.postflop.river_study import Deadline
from poker_ai.solver_validation.matched_array_reference import (
    ScalarReference,
    compare,
)

LICENSE_SHA256 = "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30"


def installed_reference() -> dict[str, Any]:
    """Read actual locked optional runtime and the entire installed license."""
    provider = distribution("open-spiel")
    licenses = [
        item for item in provider.files or () if str(item).endswith("licenses/LICENSE")
    ]
    if len(licenses) != 1:
        raise ArithmeticError("one installed OpenSpiel license required")
    raw = Path(str(provider.locate_file(licenses[0]))).read_bytes()
    result = dict(
        python=platform.python_version(),
        numpy=np.__version__,
        numba=version("numba"),
        open_spiel=version("open-spiel"),
        license_bytes=len(raw),
        license_sha256=hashlib.sha256(raw).hexdigest(),
    )
    if result != dict(
        python="3.11.17",
        numpy="2.4.6",
        numba="0.68.1",
        open_spiel="2.0.2",
        license_bytes=11_358,
        license_sha256=LICENSE_SHA256,
    ):
        raise ArithmeticError("comparison-only runtime/license changed")
    return result


def audit_path(
    scoring: ScoringContext,
    folder: Path,
    spec: PathSpec,
    refs: tuple[ScalarReference, ScalarReference],
    deadline: Deadline,
    retain: Callable[[dict[str, Any]], None],
) -> list[dict[str, Any]]:
    """Compare every own scalar; no native action or policy is returned."""
    saved = replay_path(scoring, folder)
    if saved["path"] != dict(
        index=spec.index, game=spec.game, seed=spec.seed, arm=spec.arm
    ):
        raise ArithmeticError("native path identity changed")
    rows = []
    for row in saved["captures"]:
        deadline.check()
        policy = read_snapshot(
            folder / row["file"], scoring.partition, row["receipt"], row["metadata"]
        )
        own = scoring.score(policy)
        if own_compare(score_data(scoring, own), row["score"]) > 1e-9:
            raise ArithmeticError("own scalar changed before native comparison")
        detail = dict(
            policy=pack_policy(scoring.partition, policy),
            metrics=own.metrics,
            responses=own.responses,
            replies=[
                {
                    name: pack_policy(scoring.exact, reply)
                    for name, reply in group.items()
                }
                for group in own.replies
            ],
        )
        native = compare(scoring, refs, detail)
        if (
            not math.isfinite(native["maximum_error_chips"])
            or native["maximum_error_chips"] > 1e-9
        ):
            raise ArithmeticError("independent river-strength scalar gate failed")
        result = dict(
            path_index=spec.index,
            game=spec.game,
            seed=spec.seed,
            arm=spec.arm,
            work_label=row["metadata"]["work_label"],
            readout=row["metadata"]["readout"],
            own_policy_sha256=row["receipt"]["policy_sha256"],
            native=native,
        )
        retain(result)
        rows.append(result)
    return rows


def audit_all(
    root: Path, own: Path, output: Path, deadline: Deadline
) -> dict[str, Any]:
    """Retain every completed scalar row and a failure receipt on interruption."""
    runtime = installed_reference()
    output.mkdir(parents=True, exist_ok=False)
    events = output / "events.jsonl"
    results: list[dict[str, Any]] = []
    started = time.perf_counter()
    try:
        for spec in paths():
            deadline.check()
            scoring = context(root, spec.game, spec.arm)
            refs = ScalarReference(scoring.exact), ScalarReference(scoring.partition)
            folder = own / "study" / f"path{spec.index:02d}"

            def retain(row: dict[str, Any]) -> None:
                with events.open("a") as stream:
                    stream.write(
                        json.dumps(row, sort_keys=True, allow_nan=False) + "\n"
                    )
                    stream.flush()
                    os.fsync(stream.fileno())

            rows = audit_path(scoring, folder, spec, refs, deadline, retain)
            results.extend(rows)
        if len(results) != 108:
            raise ArithmeticError("incomplete independent 108-profile audit")
        deadline.check()
        result = dict(
            status="completed",
            runtime=runtime,
            rows=results,
            seconds=time.perf_counter() - started,
        )
        (output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
        return result
    except BaseException as error:
        (output / "failure.json").write_text(
            json.dumps(
                dict(
                    status="failed_retained",
                    runtime=runtime,
                    completed_rows=len(results),
                    type=type(error).__name__,
                    reason=str(error),
                ),
                indent=2,
            )
            + "\n"
        )
        raise
