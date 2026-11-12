"""Scalar-only reference checks AFTER immutable own diagnostic publication."""

import json
import time
from pathlib import Path
from typing import Any

from poker_ai.evaluation import compact_fixed_inputs as inputs
from poker_ai.evaluation.compact_fixed_clock import measurement
from poker_ai.evaluation.compact_fixed_run import NATIVE, replay, validate_native
from poker_ai.postflop import compact_full_artifacts as files
from poker_ai.postflop.compact_full_run import runtime
from poker_ai.postflop.river_study import digest
from poker_ai.solver_validation.controlled_pipeline import license_record
from poker_ai.solver_validation.matched_array_reference import ScalarReference, compare


def run(
    root: Path, own_path: Path, output: Path, started: float, software: bool
) -> dict[str, Any]:
    if output.exists():
        raise FileExistsError("retain prior native diagnostic")
    original = json.loads(own_path.read_text())
    reference = inputs.config(root)["native_reference"]
    saved: dict[str, Any] = dict(
        format=NATIVE,
        status="running",
        failure=None,
        scope="software" if software else "real",
        source=inputs.source(root),
        runtime=runtime(),
        own_sha256=digest(own_path),
        reference=reference,
        comparisons=[],
        new_training=False,
        reference_output_used_in_training=False,
        actual_admission=False,
        fresh_global_admission=False,
    )
    cap = 180 if software else 900

    def clock() -> None:
        if time.perf_counter() - started >= cap:
            raise TimeoutError("complete native diagnostic cap")

    def persist() -> None:
        saved["seconds"] = time.perf_counter() - started
        files.atomic(output, saved)

    try:
        persist()
        saved["own_publication_commit"] = files.published(root, own_path)
        measurement(own_path, "software-own" if software else "own")
        files.published(root, own_path.with_name(own_path.stem + "-child.json"))
        if original["scope"] != saved["scope"]:
            raise ArithmeticError("native/own scope mismatch")
        saved["own_replay"] = replay(root, own_path)
        if original["source"]["fingerprint"] != saved["source"]["fingerprint"]:
            raise ArithmeticError("diagnostic own/native source cohorts differ")
        for row in original["rows"]:
            files.published(root, own_path.parent / "details" / row["receipt"]["file"])
        saved["installed_license"] = license_record(dict(native_reference=reference))
        contexts = {
            (p.context.spot_file, p.context.representation): p.context
            for p in inputs.pairs(root, software)
        }
        refs = {}
        for row in original["rows"]:
            clock()
            key = row["spot_file"], row["representation"]
            context = contexts[key]
            if key not in refs:
                refs[key] = (
                    ScalarReference(context.scoring.exact),
                    ScalarReference(context.scoring.partition),
                )
            packet = files.load_snapshot(own_path.parent / "details", row["receipt"])
            result = compare(context.scoring, refs[key], packet)
            saved["comparisons"].append(
                dict(
                    **{k: row[k] for k in inputs.FIELDS},
                    detail_sha256=row["receipt"]["sha256"],
                    **result,
                )
            )
            persist()
        saved["status"] = "completed"
        validate_native(original, saved, digest(own_path), reference)
        inputs.check_source(root, saved["source"])
        clock()
        if digest(own_path) != saved["own_sha256"]:
            raise ArithmeticError("own evidence changed during reference comparison")
    except (Exception, KeyboardInterrupt) as error:
        saved.update(
            status="incomplete",
            failure=dict(type=type(error).__name__, reason=str(error)),
        )
    finally:
        persist()
    return saved
