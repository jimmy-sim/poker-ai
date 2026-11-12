"""Pure independent-receipt arithmetic; no reference implementation import."""

import math
from typing import Any

from poker_ai.evaluation.compact_sampled_inputs import IDENTITY, identity
from poker_ai.postflop.learning_artifacts import canonical, sha

FORMAT = "compact-sampled-native-scalars-v1"
FIELDS = (
    "value_player_zero_chips",
    "best_response_zero_chips",
    "best_response_one_chips",
)
REFERENCE = dict(
    name="OpenSpiel",
    version="2.0.2",
    license="Apache-2.0",
    license_sha256="cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30",
)


def compare(own: dict[str, Any], native: dict[str, Any]) -> dict[str, Any]:
    if set(native) != set(FIELDS):
        raise ValueError("only value and BOTH best-response scalars accepted")
    if any(
        type(v) not in (int, float) or not math.isfinite(v) for v in native.values()
    ):
        raise ValueError("finite numeric native scalars required")
    eps = (native[FIELDS[1]] + native[FIELDS[2]]) / 2
    if eps < -1e-9:
        raise ArithmeticError("negative native NashConv")
    errors = {k: abs(own[k] - native[k]) for k in FIELDS}
    return dict(
        **{k: own[k] for k in (*IDENTITY, "context_sha256")},
        own_profile_sha256=sha(own),
        native=native,
        native_exploitability_chips=max(0.0, eps),
        value_error_chips=errors[FIELDS[0]],
        best_response_zero_error_chips=errors[FIELDS[1]],
        best_response_one_error_chips=errors[FIELDS[2]],
        exploitability_error_chips=abs(max(0.0, eps) - own["exploitability_chips"]),
        maximum_error_chips=max(errors.values()),
    )


def validate(own: dict[str, Any], saved: dict[str, Any], own_sha: str) -> None:
    if (
        saved["format"] != FORMAT
        or saved["status"] != "completed"
        or saved["failure"] is not None
        or saved["scope"] != own["scope"]
        or saved["source"]["fingerprint"] != own["source"]["fingerprint"]
        or saved["own_sha256"] != own_sha
        or saved["reference"] != REFERENCE
        or saved["installed_license"]["sha256"] != REFERENCE["license_sha256"]
        or saved["installed_license"]["previously_read_record"]
        != "docs/solver_validation.md"
        or saved["actual_admission"] is not False
        or saved["fresh_global_admission"] is not False
        or saved["reference_output_used_in_training"] is not False
    ):
        raise ArithmeticError("partial/mismatched native source/input/scope/license")
    own_rows = {identity(r, IDENTITY): r for r in own["rows"]}
    rows = saved["comparisons"]
    ids = [identity(r, IDENTITY) for r in rows]
    if (
        len(own["rows"]) != 324
        or len(own_rows) != 324
        or len(ids) != 324
        or len(set(ids)) != 324
        or set(ids) != set(own_rows)
    ):
        raise ArithmeticError("all324 unique independent comparisons required")
    for row in rows:
        expected = compare(own_rows[identity(row, IDENTITY)], row["native"])
        if (
            canonical(expected) != canonical(row)
            or expected["maximum_error_chips"] > 1e-9
            or expected["exploitability_error_chips"] > 1e-9
        ):
            raise ArithmeticError("native BOTH-root/value/error-field agreement failed")
