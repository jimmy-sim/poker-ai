"""Pin-only and fictional PR #118 guards; never calculate a real score."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from known_turn_half_policy_mixture.admission import forecast  # noqa: E402
from known_turn_half_policy_mixture.plan import contract  # noqa: E402
from known_turn_half_policy_mixture.proof import fictional  # noqa: E402


def test_published_eight_parent_contract_is_unchanged() -> None:
    data = contract(ROOT)
    assert len(data["inputs"]) == 8
    assert [row["path_index"] for row in data["inputs"]] == list(range(8))


def test_strict_own_and_native_forecasts_admit_below_caps() -> None:
    result = forecast(ROOT)
    assert result["status"] == "admitted"
    assert result["own_forecast_seconds"] == pytest.approx(688.326)
    assert result["native_forecast_seconds"] == pytest.approx(886.088)


def test_fictional_proof_has_no_saved_parent() -> None:
    result = fictional()
    assert result["status"] == "proof_passed"
    assert result["fictional_rows"] == 8340
    assert result["invalid_parent_rejected"]
    assert result["real_policy_opened"] is False
