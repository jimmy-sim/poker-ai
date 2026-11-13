"""The posthoc cache report cannot relabel a different diagnostic as its input."""

import importlib
import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
report = importlib.import_module("report_card_cache")


def saved() -> dict[str, Any]:
    return dict(
        config_sha256=report.CONFIG_SHA,
        source=dict(fingerprint=report.SOURCE),
        status="complete_card_cache_audit",
        admission_evidence=False,
        base_admission_rejected=True,
    )


def test_registered_source_and_scope() -> None:
    report.measured(saved())


@pytest.mark.parametrize(
    "key,value",
    [
        ("config_sha256", "changed"),
        ("source", dict(fingerprint="other")),
        ("status", "partial"),
        ("admission_evidence", True),
        ("base_admission_rejected", False),
    ],
)
def test_changed_or_partial_scope_rejected(key: str, value: Any) -> None:
    row = saved()
    row[key] = value
    with pytest.raises(ArithmeticError, match="diagnostic source"):
        report.measured(row)


def test_primitive_guard_precedes_warm_key_lookup() -> None:
    """Python bool/NumPy equality must not turn an invalid input into a hit."""
    import numpy as np

    from poker_ai import evaluator
    from poker_ai.abstraction import potential

    cache = importlib.import_module("card_cache_support")
    tool = importlib.import_module("check_card_cache")
    config = tool.contract(Path(__file__).resolve().parents[1])
    with cache.hooks(config, enabled=True) as stores:
        evaluator.evaluate_best((0, 4, 8, 12, 16))
        potential.canonical_cards((0, 4), ())
        invalid_values: tuple[Any, ...] = (False, np.int64(0))
        for invalid in invalid_values:
            with pytest.raises(TypeError):
                evaluator.evaluate_best((invalid, 4, 8, 12, 16))
            with pytest.raises(TypeError):
                potential.canonical_cards((invalid, 4), ())
    for store in stores.values():
        row = store.summary()
        assert row["hits"] == 0 and row["errors"] == 2 and row["fallbacks"] == 2
