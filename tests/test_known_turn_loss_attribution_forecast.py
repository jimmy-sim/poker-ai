"""Prospective pins and strict separate data-only compute arithmetic."""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from known_turn_loss_attribution import forecast as module  # noqa: E402
from known_turn_loss_attribution.plan import contract  # noqa: E402


def test_published_contract_and_prior_clocks() -> None:
    plan = contract(ROOT)
    assert len(plan["games"]) == 2
    assert len(plan["prerequisite_sha256"]) == 12
    assert plan["saved_policy_cases"] == 4
    result = module.forecast(ROOT)
    assert result["status"] == "admitted"
    assert result["strict_bound_seconds"] == pytest.approx(353.5350115839974)
    assert result["strict_bound_seconds"] < result["hard_cap_seconds"] == 900


def test_strict_equality_rejects_and_bad_clocks_stop(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = {
        "prior_wet_diagnosis_wall_seconds": 195.0,
        "prior_recency_report_wall_seconds": 195.0,
        "forecast_bound_seconds": 900.0,
    }
    monkeypatch.setattr(module, "contract", lambda _root: plan)
    for path in (module.WET_DIAGNOSIS, module.RECENCY_REPORT):
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(
                {
                    "status": "passed",
                    "cap_seconds": 900 if path == module.WET_DIAGNOSIS else 3600,
                    "observed_wall_seconds": 195.0,
                }
            )
        )
    assert module.forecast(tmp_path)["status"] == "rejected"
    bad = tmp_path / module.WET_DIAGNOSIS
    data = json.loads(bad.read_text())
    data["observed_wall_seconds"] = 194.0
    bad.write_text(json.dumps(data))
    with pytest.raises(ArithmeticError, match="clocks"):
        module.forecast(tmp_path)
