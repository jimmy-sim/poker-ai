"""Pin-only tests that do not open or trace mixed policy snapshots."""

from pathlib import Path

import pytest
from known_mixture_residual_map.admission import forecast
from known_mixture_residual_map.own import fixed_parent_rows
from known_mixture_residual_map.plan import contract

ROOT = Path(__file__).resolve().parents[1]


def test_published_contract_and_data_only_forecast() -> None:
    data = contract(ROOT)
    assert len(data["mixed_files"]) == 4
    assert forecast(ROOT)["status"] == "admitted"


def test_changed_mixed_snapshot_is_rejected(tmp_path: Path) -> None:
    fake = tmp_path / "configs"
    fake.mkdir()
    (fake / "known-mixture-residual-map.json").write_text("{}")
    with pytest.raises((ArithmeticError, FileNotFoundError)):
        contract(tmp_path)


def test_fixed_control_ranked_rows_reject_incomplete_set() -> None:
    prior = {
        "diagnostics": [
            {
                "game": "fixed",
                "exact_info": info,
                "control_final_rank_within_street": info,
            }
            for info in range(6)
        ]
    }
    assert fixed_parent_rows(prior, "fixed") == set(range(6))
    prior["diagnostics"].pop()
    with pytest.raises(ArithmeticError, match="row set"):
        fixed_parent_rows(prior, "fixed")
