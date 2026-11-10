"""Independent rational interval law, support, boundaries and selector contracts."""

import copy
import itertools
from dataclasses import FrozenInstanceError, replace
from fractions import Fraction as F
from typing import Any

import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st
from numpy.random import default_rng

from poker_ai.evaluation.private_prefix_math import bin_law, proofs
from poker_ai.postflop.cached_nodes import CachedNode, cache_nodes
from poker_ai.postflop.private_prefix import PrefixPlan, PrefixSelector, stratum_point
from poker_ai.postflop.training_isolation import sentinel_tree


def root() -> CachedNode:
    return cache_nodes(sentinel_tree())[0]


def test_joint_original_order_is_marginal_times_conditional_not_seat0_only() -> None:
    node = root()
    node = replace(
        node,
        _children=(
            replace(
                node.child(0),
                actions=(0,),
                _probabilities=(1.0,),
                _children=(node.child(0).child(0),),
            ),
            replace(node.child(1), _probabilities=(0.25, 0.75)),
            replace(node.child(2), _probabilities=(0.0, 1.0)),
        ),
    )
    plan = PrefixPlan.build(node)
    assert plan.paths == ((0, 0), (1, 0), (1, 1), (2, 0), (2, 1))
    np.testing.assert_allclose(
        plan.joint, [0.1, 0.075, 0.225, 0, 0.6], atol=1e-16, rtol=0
    )
    assert plan.choose(0) == (0, 0)
    assert plan.choose(plan.cdf[2]) == (2, 1)  # Skips the zero-probability edge.
    with pytest.raises(FrozenInstanceError):
        plan.first = (1.0,)  # type: ignore[misc]


def test_cdf_boundaries_both_sides_and_zero_support() -> None:
    node = root()
    node = replace(
        node,
        _probabilities=(0, 0.5, 0.5),
        _children=(
            node.child(0),
            replace(node.child(1), _probabilities=(0, 1)),
            node.child(2),
        ),
    )
    plan = PrefixPlan.build(node)
    assert plan.choose(0) == (1, 1)
    for i, value in enumerate(plan.cdf):
        if 0 < value < 1 and plan.joint[i] > 0:
            assert plan.choose(float(np.nextafter(value, 0))) == plan.paths[i]
            assert plan.joint[plan.paths.index(plan.choose(value))] > 0
    assert plan.choose(float(np.nextafter(1, 0))) == (2, 1)


@given(
    st.integers(min_value=1, max_value=1000),
    st.floats(min_value=0, max_value=np.nextafter(1.0, 0.0)),
)
def test_half_open_stratum_even_when_addition_rounds_up(
    count: int, uniform: float
) -> None:
    for i in {0, count // 2, count - 1}:
        u = stratum_point(i, count, uniform)
        assert i / count <= u < (i + 1) / count


@pytest.mark.parametrize("count", [2, 4, 16, 2**53])
def test_largest_uniform_and_upper_index(count: int) -> None:
    assert stratum_point(count - 1, count, float(np.nextafter(1, 0))) < 1


@pytest.mark.parametrize("u", [True, np.bool_(False), -0.1, 1.0, np.nan, np.inf])
def test_invalid_joint_uniform(u: Any) -> None:
    with pytest.raises(ValueError):
        PrefixPlan.build(root()).choose(u)


@pytest.mark.parametrize(
    "i,b,u",
    [
        (-1, 4, 0.2),
        (4, 4, 0.2),
        (True, 4, 0.2),
        (0, True, 0.2),
        (0, 0, 0.2),
        (0, 2**53 + 1, 0.2),
        (0, 4, True),
        (0, 4, 1),
        (0, 4, np.nan),
    ],
)
def test_invalid_stratum(i: Any, b: Any, u: Any) -> None:
    with pytest.raises(ValueError):
        stratum_point(i, b, u)


@pytest.mark.parametrize(
    "values",
    [
        (0, 0, 0),
        (-0.1, 0.5, 0.6),
        (0.1, 0.3, 0.7),
        (0.1, np.nan, 0.9),
        (0.1, np.inf, 0.9),
    ],
)
def test_bad_laws_and_both_required_chance_levels(values: tuple[float, ...]) -> None:
    node = root()
    with pytest.raises(ValueError):
        PrefixPlan.build(replace(node, _probabilities=values))
    with pytest.raises(ValueError):
        PrefixPlan.build(replace(node, chance=False))
    with pytest.raises(ValueError):
        PrefixPlan.build(
            replace(
                node,
                _children=(
                    replace(node.child(0), terminal=True),
                    node.child(1),
                    node.child(2),
                ),
            )
        )


def test_refuse_positive_mass_underflow_or_cdf_support_loss() -> None:
    node = root()
    tiny = float(np.nextafter(0, 1))
    with pytest.raises(ValueError, match="underflow"):
        PrefixPlan.build(replace(node, _probabilities=(tiny, 0, 1)))
    with pytest.raises(ValueError, match="lost in CDF"):
        PrefixPlan.build(replace(node, _probabilities=(1, 1e-20, 0)))


def test_selector_forces_exactly_two_laws_then_ordinary_rng_and_no_aliases() -> None:
    plan = PrefixPlan.build(root())
    rng, peer = default_rng(7), default_rng(7)
    select = PrefixSelector(plan, 0.75, rng)
    before = copy.deepcopy(rng.bit_generator.state)
    with pytest.raises(ArithmeticError, match="consume both"):
        select.finish()
    with pytest.raises(ArithmeticError, match="law changed"):
        select(np.array([0.5, 0.5]))
    assert select.consumed == 0
    first = np.array(plan.first)
    assert select(first) == 2
    assert select(np.array(plan.second[2])) == 1
    select.finish()
    assert rng.bit_generator.state == before
    first[:] = 99
    assert plan.first == (0.1, 0.3, 0.6)
    for _ in range(12):
        assert select(np.array([0.2, 0.8])) == peer.choice(2, p=[0.2, 0.8])
    assert rng.bit_generator.state == peer.bit_generator.state


def test_plan_reads_chance_only_not_payoff_information_or_strategy() -> None:
    node = root()
    modified = replace(
        node,
        _key="DO_NOT_READ_PRIVATE_INFO",
        _value=np.nan,
        _children=tuple(
            replace(c, _key="HIDDEN", _value=np.inf) for c in node._children
        ),
    )
    assert PrefixPlan.build(node) == PrefixPlan.build(modified)


def test_rational_covariance_with_zero_and_unequal_masses() -> None:
    probabilities = [F(0), F(1, 10), F(3, 10), F(3, 5)]
    values = [(F(99), F(-99)), (F(-2), F(3)), (F(4), F(-1)), (F(1), F(2))]
    for batch in (2, 4, 16):
        law = bin_law(probabilities, batch)
        assert all(sum(row) == 1 for row in law)
        assert [sum(row[j] for row in law) / batch for j in range(4)] == probabilities
        mean = [
            sum(p * y[k] for p, y in zip(probabilities, values, strict=True))
            for k in (0, 1)
        ]
        means = [
            [sum(p * y[k] for p, y in zip(row, values, strict=True)) for k in (0, 1)]
            for row in law
        ]
        for a, b in itertools.product(range(2), repeat=2):
            iid_cov = (
                sum(
                    p * (y[a] - mean[a]) * (y[b] - mean[b])
                    for p, y in zip(probabilities, values, strict=True)
                )
                / batch
            )
            strat_cov = (
                sum(
                    sum(
                        p * (y[a] - m[a]) * (y[b] - m[b])
                        for p, y in zip(row, values, strict=True)
                    )
                    for row, m in zip(law, means, strict=True)
                )
                / batch**2
            )
            between = sum((m[a] - mean[a]) * (m[b] - mean[b]) for m in means) / batch**2
            assert iid_cov == strat_cov + between
            if a == b:
                assert strat_cov <= iid_cov


def test_complete_raw_external_moment_checks_against_full_expectation() -> None:
    rows = proofs()
    assert len(rows) == 12
    assert all(max(row["errors"].values()) <= 1e-12 for row in rows)
    assert any(row["maximum_variance_reduction"] > 0.01 for row in rows)
