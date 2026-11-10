"""Real source factory and contract rejection, with learning/reference blocked."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from poker_ai.evaluation import matched_update_inputs as inputs
from poker_ai.postflop.controlled_training import ControlledTrainer
from poker_ai.solver_validation.reference import Reference

ROOT = Path(__file__).resolve().parents[1]


def test_duplicate_source_identifiers_cannot_be_silently_overwritten() -> None:
    with pytest.raises(ArithmeticError, match="duplicate"):
        inputs.unique([dict(id="one"), dict(id="one")], ("id",))


def test_fixed_pipeline_config_rejects_changed_cap(tmp_path: Path) -> None:
    path = tmp_path / inputs.CONFIG
    path.parent.mkdir(parents=True)
    config = json.loads((ROOT / inputs.CONFIG).read_text())
    config["maximum_own_seconds"] += 1
    path.write_text(json.dumps(config))
    with pytest.raises(ArithmeticError, match="config changed"):
        inputs.config_inputs(tmp_path)


@pytest.mark.slow
def test_real_complete_factory_never_trains_or_constructs_reference() -> None:
    with (
        patch.object(
            ControlledTrainer, "__init__", side_effect=AssertionError("no training")
        ),
        patch.object(Reference, "__init__", side_effect=AssertionError("no reference")),
    ):
        sources = inputs.load(ROOT)
    assert len(sources.paths) == 24
    assert len(sources.manifest["iteration_targets"]) == 48
    assert len(sources.manifest["self_pairs"]) == 144
    for index in range(24):
        assert len(sources.targets(index)) == 2
        for label in (100000, 1000000, 10000000):
            row = sources.original(index, label)
            assert row["path_index"] == index
            assert set(row["readouts"]) == {"uniform", "linear"}
            assert row["total_work"] >= label
            assert all(len(r["mass_sha256"]) == 64 for r in row["readouts"].values())
    for invalid in (-1, 24, True):
        with pytest.raises(ValueError):
            sources.context(invalid)
