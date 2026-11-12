"""Scalar-only OpenSpiel audit of already-published OWN sampled/cost policies."""

import json
import time
from pathlib import Path
from typing import Any

from poker_ai.evaluation import compact_sampled_cost as cost
from poker_ai.evaluation import compact_sampled_inputs as inputs
from poker_ai.evaluation import compact_sampled_own as own
from poker_ai.evaluation.compact_sampled_clock import measurement
from poker_ai.postflop import compact_full_artifacts as files
from poker_ai.postflop.compact_full_run import runtime
from poker_ai.postflop.compact_sampled_native_checks import (
    FORMAT,
    REFERENCE,
    compare,
    validate,
)
from poker_ai.postflop.river_study import digest
from poker_ai.solver_validation.controlled_pipeline import license_record
from poker_ai.solver_validation.matched_array_reference import ScalarReference


def run(
    root: Path, own_path: Path, output: Path, started: float, operation: str
) -> dict[str, Any]:
    if output.exists():
        raise FileExistsError("retain sampled native comparison")
    original = json.loads(own_path.read_text())
    scope = original["scope"]
    expected = {"software-native": "software", "cost-native": "cost", "audit": "real"}
    if expected.get(operation) != scope:
        raise ValueError("native operation does not match the own evidence scope")
    saved: dict[str, Any] = dict(
        format=FORMAT,
        scope=scope,
        status="running",
        failure=None,
        source=inputs.source(root),
        runtime=runtime(),
        own_sha256=digest(own_path),
        comparisons=[],
        reference=REFERENCE,
        reference_output_used_in_training=False,
        actual_admission=False,
        fresh_global_admission=False,
        scope_note=(
            "Independent scalar arithmetic on exported OWN mechanics, "
            "not independent engine validation"
        ),
    )
    cap = 180 if scope == "software" else 900

    def clock() -> None:
        if time.perf_counter() - started >= cap:
            raise TimeoutError("sampled complete native cap")

    def persist() -> None:
        saved["seconds"] = time.perf_counter() - started
        files.atomic(output, saved)

    try:
        persist()
        clock()
        saved["own_publication_commit"] = files.published(root, own_path)
        measurement(
            own_path,
            {"software": "software-own", "cost": "cost-own", "real": "study"}[scope],
        )
        for name in (own_path.stem + "-child.json",):
            files.published(root, own_path.with_name(name))
        if scope == "cost":
            saved["own_replay"] = cost.replay(root, own_path)
            for point in original["points"]:
                files.published(
                    root,
                    own_path.parent
                    / original["state_directory"]
                    / point["state_receipt"]["file"],
                )
            iterator = cost.policy_rows(root, own_path, original)
        else:
            saved["own_replay"] = own.replay(root, own_path)
            for point in original["points"]:
                files.published(
                    root, own_path.parent / "states" / point["state_receipt"]["file"]
                )
            for warm in original["warms"]:
                files.published(
                    root, own_path.parent / "warms" / warm["receipt"]["file"]
                )
            for journal in original["journals"]:
                files.published(root, own_path.with_name(journal["file"]))
            iterator = own.policy_rows(root, own_path, original)
        if saved["source"]["fingerprint"] != original["source"]["fingerprint"]:
            raise ArithmeticError("sampled own/native source cohort differs")
        saved["installed_license"] = license_record(dict(native_reference=REFERENCE))
        game = None
        reference = None
        for context, row, policy in iterator:
            clock()
            if game != context.spot_file:
                reference = ScalarReference(context.scoring.exact)
                game = context.spot_file
            assert reference is not None
            before = files.array_sha(policy)
            values = dict(
                value_player_zero_chips=reference.value(policy),
                best_response_zero_chips=reference.response_value(policy, 0),
                best_response_one_chips=reference.response_value(policy, 1),
            )
            if files.array_sha(policy) != before:
                raise ArithmeticError("native mutated own strategy")
            saved["comparisons"].append(compare(row, values))
            persist()
        clock()
        inputs.check_source(root, saved["source"])
        if digest(own_path) != saved["own_sha256"]:
            raise ArithmeticError("own evidence changed during audit")
        saved["status"] = "completed"
        validate(original, saved, digest(own_path))
    except (Exception, KeyboardInterrupt) as error:
        saved.update(
            status="incomplete",
            failure=dict(type=type(error).__name__, reason=str(error)),
        )
    finally:
        persist()
    return saved
