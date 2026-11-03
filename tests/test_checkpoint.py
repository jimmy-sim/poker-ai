"""Resume must reproduce uninterrupted own training, including random draws."""

import json
from pathlib import Path

import numpy as np
import pytest
from numpy.random import PCG64, Generator

from poker_ai.toy.games import ToyState
from poker_ai.training.checkpoint import load_checkpoint, save_checkpoint
from poker_ai.training.mccfr import MCCFR, Method


@pytest.mark.parametrize("method", ["external", "outcome"])
def test_resumed_training_is_bit_identical(tmp_path: Path, method: Method) -> None:
    def factory(rng: Generator) -> ToyState:
        return ToyState("kuhn")

    whole = MCCFR(factory, Generator(PCG64(20261114)), method=method)
    partial = MCCFR(factory, Generator(PCG64(20261114)), method=method)
    whole.train(100)
    partial.train(40)
    path = tmp_path / "own-checkpoint.json"
    config = {"game": "kuhn", "seed": 20261114}
    save_checkpoint(partial, path, config=config, provenance={"test": True})
    restored = load_checkpoint(path, factory, expected_config=config)
    restored.train(60)
    assert whole.iteration == restored.iteration == 100
    assert whole.nodes_visited == restored.nodes_visited
    assert whole.rng.bit_generator.state == restored.rng.bit_generator.state
    assert whole.rows.keys() == restored.rows.keys()
    for key in whole.rows:
        np.testing.assert_array_equal(
            whole.rows[key].regrets, restored.rows[key].regrets
        )
        np.testing.assert_array_equal(
            whole.rows[key].strategy_sum, restored.rows[key].strategy_sum
        )


def test_reference_artifacts_and_mismatched_configs_cannot_be_resumed(
    tmp_path: Path,
) -> None:
    def factory(rng: Generator) -> ToyState:
        return ToyState("kuhn")

    path = tmp_path / "checkpoint.json"
    path.write_text(json.dumps({"reference_strategy": {"some_node": [0.1, 0.9]}}))
    with pytest.raises(ValueError, match="own checkpoint"):
        load_checkpoint(path, factory, expected_config={})
    solver = MCCFR(factory, Generator(PCG64(9)))
    solver.train(1)
    save_checkpoint(solver, path, config={"game": "kuhn"}, provenance={})
    with pytest.raises(ValueError, match="config mismatch"):
        load_checkpoint(path, factory, expected_config={"game": "leduc"})
    payload = json.loads(path.read_text())
    payload["rows"][0]["strategy_sum"][0] = -1
    path.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="accumulators"):
        load_checkpoint(path, factory, expected_config={"game": "kuhn"})
