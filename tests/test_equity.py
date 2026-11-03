"""Known exact equities, card removal, bounded-payoff uncertainty, and RNG replay."""

import math
from typing import cast

import pytest
from hypothesis import given
from hypothesis import strategies as st
from numpy.random import PCG64, Generator

from poker_ai.cards import parse_card
from poker_ai.equity import (
    EquityResult,
    equity_state_count,
    exact_equity,
    monte_carlo_equity,
)


def cards(text: str) -> tuple[int, ...]:
    return tuple(map(parse_card, text.split()))


def test_royal_board_is_a_tie_for_fixed_and_unknown_opponents() -> None:
    board = cards("Tc Jc Qc Kc Ac")
    fixed = exact_equity(cards("2d 3h"), cards("4d 5h"), board)
    unknown = exact_equity(cards("2d 3h"), board=board)
    assert (fixed.wins, fixed.ties, fixed.losses, fixed.trials) == (0, 1, 0, 1)
    assert (unknown.wins, unknown.ties, unknown.losses) == (0, 990, 0)
    assert fixed.equity == unknown.equity == 0.5
    assert fixed.confidence_interval is None and fixed.standard_error is None


def test_turn_case_has_one_losing_out_among_44_cards() -> None:
    result = exact_equity(cards("Ah Ad"), cards("Kh Kd"), cards("Ac Kc 2c 3d"))
    assert (result.wins, result.ties, result.losses) == (43, 0, 1)
    assert result.equity == pytest.approx(43 / 44)


def test_excluding_the_only_losing_out_changes_card_removal_and_denominator() -> None:
    result = exact_equity(
        cards("Ah Ad"), cards("Kh Kd"), cards("Ac Kc 2c 3d"), dead_cards=cards("Ks")
    )
    assert (result.wins, result.ties, result.losses) == (43, 0, 0)
    assert result.equity == 1


def test_flopped_royal_flush_always_wins() -> None:
    result = exact_equity(cards("As Ks"), cards("Qh Qd"), cards("Qs Js Ts"))
    assert (result.wins, result.ties, result.losses) == (990, 0, 0)


@given(known=st.lists(st.integers(0, 51), min_size=9, max_size=9, unique=True))
def test_fixed_hand_swap_complements_equity(known: list[int]) -> None:
    hero, villain, board = known[:2], known[2:4], known[4:]
    first = exact_equity(hero, villain, board)
    second = exact_equity(villain, hero, board)
    assert first.equity + second.equity == 1
    assert first.wins == second.losses and first.ties == second.ties


def test_monte_carlo_replays_stream_and_agrees_with_exact_turn_case() -> None:
    args = (cards("Ah Ad"), cards("Kh Kd"), cards("Ac Kc 2c 3d"))
    first = monte_carlo_equity(*args, rng=Generator(PCG64(20261106)), samples=20000)
    replay = monte_carlo_equity(*args, rng=Generator(PCG64(20261106)), samples=20000)
    assert first == replay
    assert first.trials == 20000
    bounds = first.confidence_interval
    assert bounds is not None
    assert bounds[0] <= exact_equity(*args).equity <= bounds[1]


def test_uniform_opponent_sampling_respects_a_locked_board() -> None:
    result = monte_carlo_equity(
        cards("2d 3h"),
        board=cards("Tc Jc Qc Kc Ac"),
        rng=Generator(PCG64(3)),
        samples=100,
    )
    assert result.ties == result.trials == 100
    assert result.equity == 0.5


def test_fractional_ties_and_sample_standard_error() -> None:
    result = EquityResult(4, 2, 4, "monte_carlo", 0.95)
    assert result.trials == 10 and result.equity == 0.5
    assert result.outcome_variance == pytest.approx(0.2)
    assert result.standard_error == pytest.approx(math.sqrt(2 / 90))
    bounds = result.confidence_interval
    assert bounds is not None
    radius = math.sqrt(math.log(40) / 20)
    assert bounds == pytest.approx((0.5 - radius, 0.5 + radius))


@pytest.mark.parametrize(("wins", "losses"), [(1000, 0), (0, 1000)])
def test_boundary_samples_do_not_claim_zero_uncertainty(wins: int, losses: int) -> None:
    result = EquityResult(wins, 0, losses, "monte_carlo", 0.95)
    assert result.standard_error == 0
    bounds = result.confidence_interval
    assert bounds is not None and bounds[0] < bounds[1]
    assert 0 <= bounds[0] <= result.equity <= bounds[1] <= 1


def test_one_monte_carlo_sample_has_no_variance_estimate() -> None:
    assert EquityResult(1, 0, 0, "monte_carlo", 0.95).standard_error is None


def test_state_count_and_budget_guard_prevent_accidental_giant_enumerations() -> None:
    assert (
        equity_state_count(cards("Ah Ad"), cards("Kh Kd"), cards("Ac Kc 2c 3d")) == 44
    )
    assert equity_state_count(cards("2d 3h"), board=cards("Tc Jc Qc Kc Ac")) == 990
    assert equity_state_count(cards("Ah Ad")) > 2000000
    with pytest.raises(ValueError, match="Monte Carlo"):
        exact_equity(cards("Ah Ad"))
    with pytest.raises(ValueError, match="max_states"):
        exact_equity(cards("Ah Ad"), cards("Kh Kd"), cards("Ac Kc 2c 3d"), max_states=1)


@pytest.mark.parametrize("role", ["hero", "villain", "board", "dead"])
def test_duplicate_cards_across_roles_are_rejected(role: str) -> None:
    hero, villain, board = cards("Ah Ad"), cards("Kh Kd"), cards("Ac Kc 2c")
    dead: tuple[int, ...] = ()
    if role == "hero":
        hero = cards("Ah Ah")
    elif role == "villain":
        villain = cards("Ah Kd")
    elif role == "board":
        board = cards("Ah Kc 2c")
    else:
        dead = cards("Ah")
    with pytest.raises(ValueError, match="duplicate"):
        exact_equity(hero, villain, board, dead_cards=dead)


@pytest.mark.parametrize(
    ("hero", "villain", "board"),
    [((0,), (1, 2), ()), ((0, 1), (2,), ()), ((0, 1), (2, 3), tuple(range(4, 10)))],
)
def test_invalid_role_sizes(
    hero: tuple[int, ...], villain: tuple[int, ...], board: tuple[int, ...]
) -> None:
    with pytest.raises(ValueError):
        exact_equity(hero, villain, board)


@pytest.mark.parametrize("samples", [0, -1])
def test_invalid_monte_carlo_budget(samples: int) -> None:
    with pytest.raises(ValueError):
        monte_carlo_equity(cards("Ah Ad"), rng=Generator(PCG64(0)), samples=samples)


def test_requires_explicit_generator() -> None:
    with pytest.raises(TypeError):
        monte_carlo_equity(cards("Ah Ad"), rng=cast(Generator, None))


@pytest.mark.parametrize("level", [0.0, 1.0, float("nan"), float("inf")])
def test_invalid_confidence_level(level: float) -> None:
    with pytest.raises(ValueError):
        monte_carlo_equity(
            cards("Ah Ad"), rng=Generator(PCG64(0)), confidence_level=level
        )
