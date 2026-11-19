"""Fixed river-strength grid and B4 software behavior before Hold'em outcomes."""

import json
import shutil
from pathlib import Path
from typing import Any

import pytest

from poker_ai.evaluation.opponent_learning_contexts import software_context
from poker_ai.evaluation.river_strength_learning import (
    ARMS,
    GAMES,
    LABELS,
    READOUTS,
    SEEDS,
    config_grid,
    contract,
    paths,
    train,
)
from poker_ai.finite import FloatArray
from poker_ai.postflop.batch_reduction import ReducedDispatchBatchTrainer
from poker_ai.postflop.frozen_batches import BatchPoint
from poker_ai.postflop.river_study import Deadline

ROOT = Path(__file__).resolve().parents[1]


def test_prospective_grid_is_complete_and_paired() -> None:
    config: dict[str, Any] = json.loads(
        (ROOT / "configs/river-strength-known-vulnerabilities.json").read_text()
    )
    config_grid(config)
    assert len(paths()) == 12
    assert [p.index for p in paths()] == list(range(12))
    assert [(p.game, p.seed, p.arm) for p in paths()] == [
        (g, s, a) for g in GAMES for s in SEEDS for a in ARMS
    ]
    assert LABELS == (100_000, 1_000_000, 10_000_000)
    assert READOUTS == ("current", "uniform_average", "linear_average")
    changed = {**config, "seeds": [SEEDS[0], SEEDS[0], SEEDS[2]]}
    with pytest.raises(ValueError, match="grid changed"):
        config_grid(changed)


def test_public_contract_rejects_changed_config_and_input(tmp_path: Path) -> None:
    config = contract(ROOT)
    for name in [
        "configs/river-strength-known-vulnerabilities.json",
        *config["input_sha256"],
    ]:
        destination = tmp_path / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, destination)
    assert contract(tmp_path) == config
    spot = tmp_path / "configs/learning-spots/dev_low_oop.json"
    spot.write_bytes(spot.read_bytes() + b"changed")
    with pytest.raises(ArithmeticError, match="pinned river-strength input"):
        contract(tmp_path)
    spot.write_bytes((ROOT / "configs/learning-spots/dev_low_oop.json").read_bytes())
    protocol = tmp_path / "configs/river-strength-known-vulnerabilities.json"
    protocol.write_bytes(protocol.read_bytes() + b"changed")
    with pytest.raises(ArithmeticError, match="prospective river-strength contract"):
        contract(tmp_path)


def test_tiny_b4_path_crossings_and_readouts_are_deterministic() -> None:
    tree = software_context(0).coarse

    def run() -> tuple[list[tuple[int, int, bytes, bytes, bytes]], int]:
        rows: list[tuple[int, int, bytes, bytes, bytes]] = []

        def capture(
            point: BatchPoint,
            solver: ReducedDispatchBatchTrainer,
            policies: dict[str, FloatArray],
        ) -> None:
            assert solver.nodes_visited == point.total_work
            assert point.labels and point.total_work >= point.labels[-1]
            assert set(policies) == set(READOUTS)
            assert all(not p.flags.writeable for p in policies.values())
            rows.append(
                (
                    point.labels[0],
                    point.total_work,
                    policies["current"].tobytes(),
                    policies["uniform_average"].tobytes(),
                    policies["linear_average"].tobytes(),
                )
            )

        solver = train(tree, SEEDS[0], (80, 240, 720), Deadline(10), capture)
        return rows, solver.nodes_visited

    first, work = run()
    second, repeated = run()
    assert first == second and work == repeated
    assert [r[0] for r in first] == [80, 240, 720]
    assert all(r[1] >= r[0] for r in first)


def test_capture_cannot_mutate_b4_training_state() -> None:
    tree = software_context(0).coarse

    def corrupt(
        point: BatchPoint,
        solver: ReducedDispatchBatchTrainer,
        policies: dict[str, FloatArray],
    ) -> None:
        del point, policies
        solver.uniform_sum[0, 0] += 1

    with pytest.raises(ArithmeticError, match="mutated training state"):
        train(tree, SEEDS[0], (80,), Deadline(10), corrupt)
