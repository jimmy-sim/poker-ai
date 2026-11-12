"""Comparison-only OpenSpiel scalar audit of already-published OWN archives."""

import json
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

from poker_ai.postflop import compact_full_artifacts as artifacts
from poker_ai.postflop.compact_full_clock import measurement
from poker_ai.postflop.compact_full_context import contexts
from poker_ai.postflop.compact_full_native_checks import (
    FORMAT,
    REFERENCE,
    comparison,
    validate,
)
from poker_ai.postflop.compact_full_run import replay, runtime
from poker_ai.postflop.public_range_definition import contract
from poker_ai.postflop.river_study import digest
from poker_ai.solver_validation.controlled_pipeline import license_record
from poker_ai.solver_validation.matched_array_reference import ScalarReference


def run(root: Path, own_path: Path, output: Path, *, started: float) -> dict[str, Any]:
    if output.exists():
        raise FileExistsError("retain prior native output")
    own: dict[str, Any] = json.loads(own_path.read_text())
    cap = (
        180 if own["software_only"] else contract(root)["full"]["maximum_audit_seconds"]
    )

    def clock() -> None:
        if time.perf_counter() - started >= cap:
            raise TimeoutError("complete independent-audit cap reached")

    saved: dict[str, Any] = dict(
        format=FORMAT,
        status="running",
        failure=None,
        software_only=own["software_only"],
        own_sha256=digest(own_path),
        source=artifacts.source(root, clean=True),
        runtime=runtime(),
        reference=REFERENCE,
        comparisons=[],
        actual_admission=False,
        fresh_global_admission=False,
        started_at_utc=datetime.now(UTC).isoformat(),
        scope=(
            "independent EFG value and BR arithmetic, not independent poker mechanics"
        ),
    )

    def persist() -> None:
        saved["seconds"] = time.perf_counter() - started
        artifacts.atomic(output, saved)

    try:
        persist()
        clock()
        measurement(own_path, "software-own" if own["software_only"] else "own")
        saved["own_publication_commit"] = artifacts.published(root, own_path)
        for row in own["rows"]:
            artifacts.published(
                root, own_path.parent / "snapshots" / row["snapshot"]["file"]
            )
        saved["own_replay"] = replay(root, own_path)
        if saved["source"]["fingerprint"] != own["source"]["fingerprint"]:
            raise ArithmeticError("own/native source cohort differs")
        saved["installed_license"] = license_record(dict(native_reference=REFERENCE))
        reference = None
        game = None
        for context in contexts(root, software=own["software_only"]):
            clock()
            if context.spot_file != game:
                reference = ScalarReference(context.scoring.exact)
                game = context.spot_file
            assert reference is not None
            for row in own["rows"]:
                if (row["spot_file"], row["representation"]) != (
                    context.spot_file,
                    context.representation,
                ):
                    continue
                clock()
                raw = artifacts.load_snapshot(
                    own_path.parent / "snapshots", row["snapshot"]
                )
                artifacts.decode(context, raw)
                policy = context.scoring.expand(
                    np.asarray(raw["policy"], dtype=np.float64)
                )
                before = artifacts.array_sha(policy)
                native = dict(
                    value_player_zero_chips=reference.value(policy),
                    best_response_zero_chips=reference.response_value(policy, 0),
                    best_response_one_chips=reference.response_value(policy, 1),
                )
                if artifacts.array_sha(policy) != before:
                    raise ArithmeticError("comparison mutated own policy")
                saved["comparisons"].append(comparison(row, native))
                persist()
        clock()
        if digest(own_path) != saved["own_sha256"]:
            raise ArithmeticError("own manifest changed during native audit")
        artifacts.check_source(root, saved["source"])
        saved["status"] = "completed"
        validate(own, saved, digest(own_path))
    except (Exception, KeyboardInterrupt) as error:
        saved.update(
            status="incomplete",
            failure=dict(type=type(error).__name__, reason=str(error)),
        )
    finally:
        persist()
    return saved
