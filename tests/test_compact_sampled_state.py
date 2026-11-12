"""Tiny unit fixtures, not source-bound proof or real poker study admission."""

import copy
import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from numpy.random import PCG64, Generator

from poker_ai.evaluation import compact_sampled_inputs as inputs
from poker_ai.postflop import compact_full_artifacts as files
from poker_ai.postflop.batch_reduction import ReducedDispatchBatchTrainer
from poker_ai.postflop.compact_full_context import Context
from poker_ai.postflop.compact_sampled_capture import Journal, collect, payload
from poker_ai.postflop.compact_sampled_state import (
    decode,
    policies,
    rng_state,
    scores,
    table,
    unpack,
)
from poker_ai.postflop.controlled_training import Rules
from poker_ai.postflop.frozen_batches import FrozenBatchTrainer, guard
from poker_ai.postflop.river_study import Deadline

ROOT = Path(__file__).resolve().parents[1]
FINGERPRINT = "f" * 64


@pytest.fixture(scope="module")
def context() -> Context:
    return next(iter(inputs.game_contexts(ROOT, "software").values()))


def warm_fixture(context: Context) -> dict[str, Any]:
    solver = ReducedDispatchBatchTrainer(
        context.scoring.partition,
        Generator(PCG64(20261301)),
        batch_size=4,
        rules=Rules("signed", "linear", "linear"),
    )
    solver.initialize_exact()
    return payload(
        context,
        dict(
            spot_file=context.spot_file,
            representation=context.representation,
            seed=20261301,
        ),
        0,
        "software",
        FINGERPRINT,
        solver,
        None,
        None,
    )


def test_warm_is_exact_and_not_sampled(context: Context) -> None:
    warm = warm_fixture(context)
    arrays, profiles = decode(context, warm, None, FINGERPRINT, "software")
    assert warm["iteration"] == 1
    assert (
        warm["initialization_work"]
        == warm["total_node_work"]
        == 2 * len(context.scoring.partition.player)
    )
    assert warm["sampled_traversals"] == 0
    result = scores(context, warm, arrays, profiles)
    for row in result:
        if row["readout"] != "current":
            assert row["coverage"] == pytest.approx(1)
            assert row["support"]["all"]["post_warm"]["rows"] == 0
            assert row["support"]["all"]["sampled"]["rows"] == 0


def test_actual_capture_three_shared_readouts(tmp_path: Path, context: Context) -> None:
    case: dict[str, Any] = dict(
        spot_file=context.spot_file,
        representation=context.representation,
        seed=20261301,
    )
    journal = Journal(tmp_path / "worker-0.jsonl", FINGERPRINT, "software", 0)
    result = collect(
        context,
        case,
        0,
        "software",
        [1000, 3000, 10000],
        tmp_path,
        FINGERPRINT,
        journal,
        Deadline(30),
    )
    assert result["checkpoints"] == 3 and result["readouts"] == 9
    assert result["confirmed_work"] >= 10000
    events = [json.loads(line) for line in journal.path.read_text().splitlines()]
    independent = FrozenBatchTrainer(
        context.scoring.partition,
        Generator(PCG64(case["seed"])),
        batch_size=4,
        rules=Rules("signed", "linear", "linear"),
    )
    independent.initialize_exact()
    warm_event = next(e for e in events if e["kind"] == "warm")
    warm = files.load_snapshot(tmp_path / "warms", warm_event["receipt"])
    for event in [e for e in events if e["kind"] == "checkpoint"]:
        state = files.load_snapshot(tmp_path / "states", event["receipt"])
        arrays, profiles = decode(context, state, warm, FINGERPRINT, "software")
        while independent.nodes_visited < event["work_checkpoint"]:
            independent.step()
        assert guard(independent) == state["guard_sha256"]
        np.testing.assert_array_equal(independent.regrets, arrays["regrets"])
        np.testing.assert_array_equal(independent.uniform_sum, arrays["uniform_sum"])
        np.testing.assert_array_equal(independent.strategy_sum, arrays["linear_sum"])
        assert (
            state["previous_node_work"]
            < state["work_checkpoint"]
            <= state["total_node_work"]
        )
        assert (
            state["total_node_work"] - state["previous_node_work"]
            == state["last_iteration_work"]
        )
        assert len(scores(context, state, arrays, profiles)) == 3
    with pytest.raises(FileExistsError):
        collect(
            context,
            case,
            0,
            "software",
            [1000, 3000, 10000],
            tmp_path,
            FINGERPRINT,
            journal,
            Deadline(30),
        )


def test_reduced_backend_remains_bit_exact_to_frozen_b4(context: Context) -> None:
    a = FrozenBatchTrainer(
        context.scoring.partition,
        Generator(PCG64(20261301)),
        batch_size=4,
        rules=Rules("signed", "linear", "linear"),
    )
    b = ReducedDispatchBatchTrainer(
        context.scoring.partition,
        Generator(PCG64(20261301)),
        batch_size=4,
        rules=Rules("signed", "linear", "linear"),
    )
    a.initialize_exact()
    b.initialize_exact()
    for _ in range(16):
        a.step()
        b.step()
        assert guard(a) == guard(b)
        np.testing.assert_array_equal(a.regrets, b.regrets)
        np.testing.assert_array_equal(a.uniform_sum, b.uniform_sum)
        np.testing.assert_array_equal(a.strategy_sum, b.strategy_sum)


@pytest.mark.parametrize(
    "field",
    [
        "format",
        "scope",
        "source_fingerprint",
        "binding",
        "actions",
        "seed",
        "path_index",
        "iteration",
        "total_node_work",
        "initialization_work",
        "sampled_traversals",
        "guard_sha256",
    ],
)
def test_changed_warm_metadata_is_rejected(context: Context, field: str) -> None:
    saved = warm_fixture(context)
    saved[field] = True
    with pytest.raises((ArithmeticError, ValueError, TypeError)):
        decode(context, saved, None, FINGERPRINT, "software")


@pytest.mark.parametrize("field", ["regrets", "uniform_sum", "linear_sum", "warm_sum"])
@pytest.mark.parametrize("value", [True, "0.1", float("nan"), float("inf")])
def test_invalid_tables_are_rejected(context: Context, field: str, value: Any) -> None:
    saved = warm_fixture(context)
    saved[field][0][0] = value
    with pytest.raises((ArithmeticError, ValueError)):
        decode(context, saved, None, FINGERPRINT, "software")


def test_signed_regrets_do_not_allow_negative_average_mass(context: Context) -> None:
    tree = context.scoring.partition
    values = np.zeros_like(tree.legal)
    values[0, 0] = -1
    packed = table(tree, values, signed=True)
    np.testing.assert_array_equal(unpack(tree, packed, signed=True), values)
    with pytest.raises(ValueError):
        unpack(tree, packed, signed=False)


def test_cost_cannot_construct_sampler(tmp_path: Path, context: Context) -> None:
    journal = Journal(tmp_path / "cost.jsonl", FINGERPRINT, "cost", 0)
    with pytest.raises(ValueError, match="COST"):
        collect(
            context,
            dict(seed=20261301),
            0,
            "cost",
            [1000],
            tmp_path,
            FINGERPRINT,
            journal,
            Deadline(30),
        )


def test_warm_rng_did_not_consume_a_draw(context: Context) -> None:
    saved = warm_fixture(context)
    rng = rng_state(saved["rng_state"])
    rng.random()
    saved["rng_state"] = copy.deepcopy(rng.bit_generator.state)
    with pytest.raises(ArithmeticError):
        decode(context, saved, None, FINGERPRINT, "software")


@pytest.mark.parametrize("value", [True, -1, 2**128])
def test_bad_rng_integer_rejected(context: Context, value: Any) -> None:
    saved = warm_fixture(context)["rng_state"]
    saved["state"]["state"] = value
    with pytest.raises(ValueError):
        rng_state(saved)


def test_current_policies_depend_only_on_regrets(context: Context) -> None:
    warm = warm_fixture(context)
    arrays, _ = decode(context, warm, None, FINGERPRINT, "software")
    before = policies(
        context.scoring.partition,
        arrays["regrets"],
        arrays["uniform_sum"],
        arrays["linear_sum"],
    )
    changed = arrays["linear_sum"] * 7
    after = policies(
        context.scoring.partition, arrays["regrets"], arrays["uniform_sum"], changed
    )
    np.testing.assert_array_equal(before["current"], after["current"])


def test_protocol_grid_has324_readouts_and108_states() -> None:
    assert len(inputs.expected(ROOT, "real", readouts=True)) == 324
    assert len(inputs.expected(ROOT, "real", readouts=False)) == 108
    assert len(inputs.cases(ROOT, "real")) == 36
