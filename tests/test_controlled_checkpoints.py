"""Checkpoint observation preserves uninterrupted arrays, RNG and charged work."""

import copy
import gzip
import hashlib
import itertools
import json
from pathlib import Path
from typing import Any, Literal

import numpy as np
import pytest
from numpy.random import default_rng

from poker_ai.postflop import controlled_checkpoints as checkpoints
from poker_ai.postflop.cached_nodes import CachedNodeTrainer
from poker_ai.postflop.controlled_training import (
    ControlledTrainer,
    Rules,
    Traversal,
    Weight,
)
from poker_ai.postflop.river_study import Deadline
from poker_ai.postflop.row_profile import assert_equal
from poker_ai.postflop.training_isolation import sentinel_tree


@pytest.mark.parametrize(
    "traversal,warm", list(itertools.product(["full", "external"], [False, True]))
)
def test_observed_trajectory_matches_uninterrupted_all_rules(
    traversal: Traversal, warm: bool
) -> None:
    tree = sentinel_tree()
    clips: tuple[Literal["signed", "clipped"], ...] = ("signed", "clipped")
    weights: tuple[Weight, ...] = ("uniform", "linear")
    for clip, rw, aw in itertools.product(clips, weights, weights):
        cls = CachedNodeTrainer if traversal == "external" else ControlledTrainer
        a = cls(tree, default_rng(19), traversal=traversal, rules=Rules(clip, rw, aw))
        b = cls(tree, default_rng(19), traversal=traversal, rules=Rules(clip, rw, aw))
        if warm:
            a.initialize_exact()
            b.initialize_exact()
        packets: list[checkpoints.Observation] = []
        checkpoints.observe(
            a,
            [150, 500],
            [2, 4, 8],
            np.ones(len(tree.keys), dtype=np.bool_),
            packets.append,
            Deadline(10),
        )
        while b.iteration < a.iteration:
            b.step()
        assert_equal(a, b)
        labels = [label for p in packets for label in p.labels]
        assert sorted(labels) == sorted(
            [
                ("work", 150),
                ("work", 500),
                ("iteration", 2),
                ("iteration", 4),
                ("iteration", 8),
            ]
        )
        for p in packets:
            assert not p.policy.flags.writeable
            for axis, requested in p.labels:
                if axis == "work":
                    assert p.previous_work < requested <= p.total_work
                    assert p.overshoots[str(requested)] == p.total_work - requested
                else:
                    assert p.iteration == requested


def test_warm_initialization_labels_coalesce_without_an_extra_step() -> None:
    tree = sentinel_tree()
    solver = ControlledTrainer(tree, default_rng(1))
    solver.initialize_exact()
    initial = solver.nodes_visited
    packets: list[checkpoints.Observation] = []
    checkpoints.observe(
        solver,
        [1, initial],
        [1],
        np.zeros(len(tree.keys), dtype=np.bool_),
        packets.append,
        Deadline(10),
    )
    assert solver.iteration == 1
    assert len(packets) == 1
    assert packets[0].previous_work == 0
    assert packets[0].last_iteration_visits == initial
    assert packets[0].labels == (("work", 1), ("work", initial), ("iteration", 1))


def test_observer_mutation_and_missed_start_rejected() -> None:
    solver = ControlledTrainer(sentinel_tree(), default_rng(1))
    mask = np.ones(len(solver.tree.keys), dtype=np.bool_)

    def mutate(packet: checkpoints.Observation) -> None:
        del packet
        solver.regrets[0, 0] = 17

    with pytest.raises(ArithmeticError, match="mutated"):
        checkpoints.observe(solver, [], [1], mask, mutate, Deadline(10))
    solver.step()
    with pytest.raises(ValueError, match="unreachable"):
        checkpoints.observe(solver, [1], [], mask, lambda packet: None, Deadline(10))


def test_visit_coverage_excludes_warm_initialization_and_empty_river_is_null() -> None:
    tree = sentinel_tree()
    solver = CachedNodeTrainer(tree, default_rng(2))
    solver.initialize_exact()
    all_rows = np.ones(len(tree.keys), dtype=np.bool_)
    d = checkpoints.diagnostics(solver, all_rows)
    assert d["positive_average_coverage"] == 1
    assert d["river_visit_coverage"] == 0
    assert checkpoints.diagnostics(solver, ~all_rows)["river_visit_coverage"] is None
    solver.step()
    d = checkpoints.diagnostics(solver, all_rows)
    assert d["river_partition_rows_visited"] == len(solver.sampled_keys)
    assert d["regret_norm"] == float(np.linalg.norm(solver.regrets))
    full = ControlledTrainer(tree, default_rng(2), traversal="full")
    full.step()
    assert checkpoints.diagnostics(full, all_rows)["river_visit_coverage"] == 1


@pytest.mark.parametrize(
    "work,iterations", [([], []), ([2, 1], []), ([True], []), ([1, 1], []), ([], [0])]
)
def test_invalid_checkpoint_contracts(work: list[int], iterations: list[int]) -> None:
    solver = ControlledTrainer(sentinel_tree(), default_rng(1))
    with pytest.raises(ValueError):
        checkpoints.observe(
            solver,
            work,
            iterations,
            np.zeros(len(solver.tree.keys), dtype=np.bool_),
            lambda p: None,
            Deadline(10),
        )


def test_snapshot_round_trip_preserves_policy_bits_and_metadata(tmp_path: Path) -> None:
    tree = sentinel_tree()
    policy = tree.normalize(tree.legal)
    policy[0, 0] = -0.0
    policy[0, 1] = 1.0
    metadata = dict(source="own-software-fixture", seed=19, labels=[["work", 500]])
    path = tmp_path / "snapshot.json.gz"
    receipt = checkpoints.write_snapshot(path, tree, policy, metadata)
    loaded = checkpoints.read_snapshot(path, tree, receipt, metadata)
    assert loaded.tobytes() == policy.tobytes()
    other = tmp_path / "repeat.json.gz"
    assert checkpoints.write_snapshot(other, tree, policy, metadata) == receipt
    with pytest.raises(FileExistsError):
        checkpoints.write_snapshot(path, tree, policy, metadata)
    with pytest.raises(ArithmeticError):
        checkpoints.read_snapshot(path, tree, receipt, {**metadata, "seed": True})


@pytest.mark.parametrize(
    "mode", ["hash", "policy_bits", "format", "shape", "metadata", "menus", "numeric"]
)
def test_reject_snapshot_tampering(tmp_path: Path, mode: str) -> None:
    tree = sentinel_tree()
    policy = tree.normalize(tree.legal)
    path = tmp_path / "own.json.gz"
    metadata: dict[str, Any] = dict(seed=19)
    receipt = checkpoints.write_snapshot(path, tree, policy, metadata)
    if mode == "hash":
        receipt["sha256"] = "0" * 64
    elif mode == "policy_bits":
        receipt["policy_sha256"] = "0" * 64
    else:
        saved = json.loads(gzip.decompress(path.read_bytes()))
        if mode == "format":
            saved["format"] = "reference-solver-policy"
        elif mode == "shape":
            saved["shape"][0] = True
        elif mode == "menus":
            saved["actions"][0].reverse()
        elif mode == "numeric":
            saved["policy"][0][0] = str(saved["policy"][0][0])
        else:
            saved["metadata"] = dict(seed=20)
        blob = gzip.compress(json.dumps(saved).encode(), mtime=0)
        path.write_bytes(blob)
        receipt = {
            **receipt,
            "sha256": hashlib.sha256(blob).hexdigest(),
            "bytes": len(blob),
        }
    with pytest.raises(ArithmeticError):
        checkpoints.read_snapshot(path, tree, receipt, copy.deepcopy(metadata))


def test_wide_chance_padding_is_not_serialized_and_bits_round_trip(
    tmp_path: Path,
) -> None:
    from dataclasses import replace

    tree = sentinel_tree()
    pad = 44 - tree.legal.shape[1]
    tree = replace(tree, legal=np.pad(tree.legal, ((0, 0), (0, pad))))
    policy = tree.normalize(tree.legal)
    path = tmp_path / "packed.json.gz"
    receipt = checkpoints.write_snapshot(path, tree, policy, {})
    saved = json.loads(gzip.decompress(path.read_bytes()))
    assert saved["shape"][1] == 44
    assert sum(len(row) for row in saved["policy"]) == sum(map(len, tree.actions))
    assert (
        checkpoints.read_snapshot(path, tree, receipt, {}).tobytes() == policy.tobytes()
    )
    policy[0, -1] = -0.0
    with pytest.raises(ValueError, match="padding"):
        checkpoints.write_snapshot(
            tmp_path / "negative-padding.json.gz", tree, policy, {}
        )
