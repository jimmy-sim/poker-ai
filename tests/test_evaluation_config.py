"""Settings that prevent inflated sample sizes and missing multiplicity control."""

import json
from pathlib import Path

import pytest

from poker_ai.evaluation.experiment import load_config

CONFIG = Path(__file__).resolve().parents[1] / "configs/match-evaluation.json"


@pytest.mark.parametrize("mutation", ["duplicate_agents", "smaller_test_family"])
def test_invalid_inference_design_is_rejected(tmp_path: Path, mutation: str) -> None:
    raw = json.loads(CONFIG.read_text())
    if mutation == "duplicate_agents":
        raw["agent_seeds"][1] = raw["agent_seeds"][0]
    else:
        raw["inference"]["family_size"] = 5
    path = tmp_path / "config.json"
    path.write_text(json.dumps(raw))
    with pytest.raises(ValueError):
        load_config(path)
