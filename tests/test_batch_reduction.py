"""Independent sparse arithmetic, unchanged rejection and exact trajectory gates."""

import copy
import itertools
from typing import Any

import numpy as np
import pytest
from numpy.random import PCG64, Generator

from poker_ai.postflop.batch_reduction import (
    ReducedDispatchBatchTrainer,
    array_mean_updates,
)
from poker_ai.postflop.controlled_training import Rules
from poker_ai.postflop.frozen_batches import (
    BatchPoint,
    FrozenBatchTrainer,
    guard,
    mean_updates,
    observe,
)
from poker_ai.postflop.river_study import Deadline
from poker_ai.postflop.training_isolation import sentinel_tree
from poker_ai.training.mccfr import Updates


def equal(a: Updates, b: Updates) -> None:
    assert a.visited == b.visited
    for name in ("regrets", "averages"):
        left, right = getattr(a, name), getattr(b, name)
        assert list(left) == list(right)
        for key in left:
            assert left[key].dtype == right[key].dtype
            assert left[key].tobytes() == right[key].tobytes()


def test_sparse_math_missing_rows_order_cancellation_and_aliases() -> None:
    samples = [
        Updates(
            {"b": np.array([1e16, -1e16]), "a": np.array([6.0, -6.0])},
            {"x": np.array([0.25, 0.75])},
            3,
        ),
        Updates({"b": np.array([-1e16, 1e16])}, {"y": np.array([1.0, 0.0])}, 7),
        Updates({"b": np.array([1.0, -1.0])}, {"x": np.array([0.75, 0.25])}, 11),
    ]
    before = copy.deepcopy(samples)
    result = array_mean_updates(iter(samples), 3)
    equal(result, mean_updates(iter(samples), 3))
    assert result.visited == 21
    assert list(result.regrets) == ["b", "a"]
    np.testing.assert_array_equal(result.regrets["b"], [1 / 3, -1 / 3])
    np.testing.assert_array_equal(result.regrets["a"], [2, -2])
    np.testing.assert_array_equal(result.averages["x"], [1 / 3, 1 / 3])
    np.testing.assert_array_equal(result.averages["y"], [1 / 3, 0])
    for actual, old in zip(samples, before, strict=True):
        equal(actual, old)
        for name in ("regrets", "averages"):
            for key, v in getattr(actual, name).items():
                assert not np.shares_memory(v, getattr(result, name)[key])


def test_independent_B2_product_expectation_variance_and_clipping() -> None:
    # Independent finite distribution, not derived from either implementation.
    values = [np.array([-2.0, 2.0]), np.array([4.0, -4.0])]
    weights = [0.75, 0.25]
    means = []
    probabilities = []
    for i, j in itertools.product(range(2), repeat=2):
        result = array_mean_updates(
            [Updates({"r": values[k]}, {}, 1) for k in (i, j)], 2
        )
        np.testing.assert_array_equal(result.regrets["r"], (values[i] + values[j]) / 2)
        means.append(result.regrets["r"])
        probabilities.append(weights[i] * weights[j])
    expected = sum(p * v for p, v in zip(probabilities, means, strict=True))
    np.testing.assert_array_equal(expected, [-0.5, 0.5])
    variance = sum(
        p * (v - expected) ** 2 for p, v in zip(probabilities, means, strict=True)
    )
    single = sum(p * (v - expected) ** 2 for p, v in zip(weights, values, strict=True))
    np.testing.assert_array_equal(variance, single / 2)
    assert not np.array_equal(
        sum(p * np.maximum(v, 0) for p, v in zip(probabilities, means, strict=True)),
        np.maximum(expected, 0),
    )


def bad_cases() -> list[tuple[list[Updates], Any]]:
    cases: list[tuple[list[Updates], Any]] = [([], n) for n in (0, -1, True, 1.0, "2")]
    cases += [([], 1), ([Updates({}, {}, 1)], 2), ([Updates({}, {}, 1)] * 2, 1)]
    cases += [([Updates({}, {}, n)], 1) for n in (0, -1, True, 1.0)]  # type: ignore[arg-type]
    cases += [([Updates({k: np.array([1.0])}, {}, 1)], 1) for k in ("", 7)]  # type: ignore[dict-item]
    cases += [
        ([Updates({"a": v}, {}, 1)], 1)
        for v in (
            np.array([]),
            np.array(1.0),
            np.array([[1.0]]),
            np.array([np.nan]),
            np.array([np.inf]),
            np.array([-np.inf]),
        )
    ]
    cases += [([Updates({}, {"a": np.array([-1.0])}, 1)], 1)]
    cases += [
        (
            [
                Updates({"a": np.array([1.0])}, {}, 1),
                Updates({"a": np.array([1.0, 2.0])}, {}, 1),
            ],
            2,
        )
    ]
    cases += [([Updates({"a": np.array([1e308])}, {}, 1)] * 2, 2)]
    return cases


@pytest.mark.parametrize("samples,count", bad_cases())
def test_same_invalid_stream_exception_without_input_mutation(
    samples: list[Updates], count: Any
) -> None:
    before = copy.deepcopy(samples)
    with np.errstate(over="ignore", invalid="ignore"):
        try:
            mean_updates(iter(samples), count)
        except (ValueError, ArithmeticError) as error:
            expected = type(error)
        else:
            pytest.fail("invalid independent fixture accepted by original")
        with pytest.raises(expected):
            array_mean_updates(iter(samples), count)
    for actual, old in zip(samples, before, strict=True):
        equal(actual, old)


@pytest.mark.parametrize("clip", ["signed", "clipped"])
@pytest.mark.parametrize("batch", [1, 4, 16])
@pytest.mark.parametrize("seed", [7, 19, 31])
def test_every_tiny_trajectory_array_rng_counter_and_observer_matches(
    clip: Any, batch: int, seed: int
) -> None:
    tree = sentinel_tree()
    old = FrozenBatchTrainer(
        tree,
        Generator(PCG64(seed)),
        batch_size=batch,
        rules=Rules(clip, "linear", "linear"),
    )
    new = ReducedDispatchBatchTrainer(
        tree,
        Generator(PCG64(seed)),
        batch_size=batch,
        rules=Rules(clip, "linear", "linear"),
    )
    old.initialize_exact()
    new.initialize_exact()
    for _ in range(25):
        assert guard(old) == guard(new)
        for name in ("regrets", "strategy_sum", "uniform_sum", "warm_sum"):
            assert getattr(old, name).tobytes() == getattr(new, name).tobytes()
        for weight in ("uniform", "linear"):
            assert old.readout_fingerprint(weight) == new.readout_fingerprint(weight)
        old.step()
        new.step()
    assert guard(old) == guard(new)
    labels = [old.nodes_visited + 1, old.nodes_visited + 200]
    # observe requires initialized learners, so use fresh independent copies.
    a = FrozenBatchTrainer(
        tree,
        Generator(PCG64(seed)),
        batch_size=batch,
        rules=Rules(clip, "linear", "linear"),
    )
    b = ReducedDispatchBatchTrainer(
        tree,
        Generator(PCG64(seed)),
        batch_size=batch,
        rules=Rules(clip, "linear", "linear"),
    )
    a.initialize_exact()
    b.initialize_exact()
    pa: list[BatchPoint] = []
    pb: list[BatchPoint] = []
    observe(a, labels, pa.append, Deadline(10))
    observe(b, labels, pb.append, Deadline(10))
    assert pa == pb and guard(a) == guard(b)


@pytest.mark.parametrize("dtype", [np.float32, np.float64])
@pytest.mark.parametrize("readonly", [False, True])
def test_standard_strided_arrays_keep_dtype_bytes_and_do_not_alias(
    dtype: Any, readonly: bool
) -> None:
    a = np.array([1.0, 99.0, -1.0, 99.0], dtype=dtype)[::2]
    b = np.array([0.25, 99.0, 0.75, 99.0], dtype=dtype)[::2]
    a.flags.writeable = not readonly
    b.flags.writeable = not readonly
    samples = [Updates({"r": a}, {"x": b}, 3), Updates({"r": -a}, {"x": b}, 5)]
    actual = array_mean_updates(samples, 2)
    expected = mean_updates(samples, 2)
    equal(actual, expected)
    assert not np.shares_memory(actual.regrets["r"], a)
    assert not np.shares_memory(actual.averages["x"], b)
