"""Pure native-receipt schema/math checks; imports no reference implementation."""

import math
from typing import Any

from poker_ai.postflop import compact_full_artifacts as artifacts
from poker_ai.postflop.learning_artifacts import canonical

FORMAT = "compact-full-native-scalars-v1"
REFERENCE = dict(
    name="OpenSpiel",
    version="2.0.2",
    license="Apache-2.0",
    license_sha256="cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30",
)
FIELDS = (
    "value_player_zero_chips",
    "best_response_zero_chips",
    "best_response_one_chips",
)


def comparison(own: dict[str, Any], native: dict[str, Any]) -> dict[str, Any]:
    """Recompute signed roots, aggregation and error fields; never trust error=0."""
    if set(native) != set(FIELDS):
        raise ValueError("all three native scalars required, no strategies accepted")
    for value in native.values():
        if type(value) not in (int, float) or not math.isfinite(value):
            raise ValueError("finite numeric native scalar required")
    eps = (native["best_response_zero_chips"] + native["best_response_one_chips"]) / 2
    if eps < -1e-9:
        raise ArithmeticError("native negative NashConv")
    errors = {key: abs(native[key] - own["metrics"][key]) for key in FIELDS}
    return dict(
        **{k: own[k] for k in (*artifacts.IDENTITY, "context_sha256")},
        native=native,
        native_exploitability_chips=max(0.0, eps),
        value_error_chips=errors[FIELDS[0]],
        best_response_zero_error_chips=errors[FIELDS[1]],
        best_response_one_error_chips=errors[FIELDS[2]],
        exploitability_error_chips=abs(
            max(0.0, eps) - own["metrics"]["exploitability_chips"]
        ),
        maximum_error_chips=max(errors.values()),
    )


def validate(own: dict[str, Any], audit: dict[str, Any], own_sha: str) -> None:
    if (
        audit["format"] != FORMAT
        or audit["status"] != "completed"
        or audit["failure"] is not None
        or audit["own_sha256"] != own_sha
        or audit["software_only"] is not own["software_only"]
        or audit["source"]["fingerprint"] != own["source"]["fingerprint"]
        or audit["reference"] != REFERENCE
        or audit["installed_license"]["sha256"] != REFERENCE["license_sha256"]
        or audit["installed_license"]["previously_read_record"]
        != "docs/solver_validation.md"
        or audit["actual_admission"] is not False
        or audit["fresh_global_admission"] is not False
    ):
        raise ArithmeticError("partial/mismatched native source/input/scope")
    by = {tuple(r[k] for k in artifacts.IDENTITY): r for r in own["rows"]}
    rows = audit["comparisons"]
    ids = [tuple(r[k] for k in artifacts.IDENTITY) for r in rows]
    if len(ids) != len(set(ids)) or set(ids) != set(by):
        raise ArithmeticError("native comparison grid incomplete or duplicated")
    for row in rows:
        key = tuple(row[k] for k in artifacts.IDENTITY)
        expected = comparison(by[key], row["native"])
        if (
            canonical(row) != canonical(expected)
            or expected["maximum_error_chips"] > 1e-9
            or expected["exploitability_error_chips"] > 1e-9
        ):
            raise ArithmeticError("native scalar/error/context agreement failed")
