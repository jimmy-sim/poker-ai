"""Independent physical-set oracle and public-information controls."""

import inspect
from dataclasses import FrozenInstanceError

import pytest
from numpy.random import default_rng

from poker_ai.cards import parse_card
from poker_ai.evaluation.range_blocker_features import (
    PublicRanges,
    Ranges,
    compatible_with_own,
    public_ranges,
)


def cards(text: str) -> tuple[int, ...]:
    return tuple(parse_card(c) for c in text.split())


RANGES: Ranges = (
    (cards("Js As"), cards("Tc Td")),
    (cards("Qh Kh"), cards("9c 9d")),
)


def oracle(board: tuple[int, ...], ranges: Ranges) -> PublicRanges:
    # Deliberately use sets, not the production bit-mask operations.
    known = set(board)
    available = tuple(
        tuple(set(hand).isdisjoint(known) for hand in side) for side in ranges
    )
    joint = tuple(
        tuple(
            set(left).isdisjoint(known)
            and set(right).isdisjoint(known)
            and set(left).isdisjoint(right)
            for right in ranges[1]
        )
        for left in ranges[0]
    )
    return PublicRanges(available, joint)


def test_recorded_nine_removal_is_public_and_two_sided() -> None:
    diamond = public_ranges(cards("Ts 9s 4d 2h 9d"), RANGES)
    heart = public_ranges(cards("Ts 9s 4d 2h 9h"), RANGES)
    assert diamond.available == ((True, True), (True, False))
    assert heart.available == ((True, True), (True, True))
    assert diamond.joint == ((True, False), (True, False))
    assert heart.joint == ((True, True), (True, True))
    for target, own in ((0, cards("As Js")), (1, cards("Kh Qh"))):
        expected = (True, False) if target == 0 else (True, True)
        assert compatible_with_own(diamond, RANGES, target, own) == expected


def test_alternative_own_hands_are_not_filtered_by_actual_private_cards() -> None:
    ranges = ((cards("As Kd"), cards("As Qd")), (cards("9h Th"),))
    feature = public_ranges(cards("2c 3d 4h 5s 6c"), ranges)
    assert feature.available[0] == (True, True)
    assert feature.joint == ((True,), (True,))
    assert set(inspect.signature(public_ranges).parameters) == {"board", "ranges"}
    original = feature.record()
    compatible_with_own(feature, ranges, 0, cards("As Kd"))
    assert feature.record() == original


def test_private_intersections_and_zero_worlds_are_retained() -> None:
    ranges = ((cards("As Kd"), cards("Qh Jd")), (cards("As 9d"), cards("Qh Th")))
    feature = public_ranges(cards("2c 3d 4h 5s 6c"), ranges)
    assert feature.available == ((True, True), (True, True))
    assert feature.joint == ((False, True), (True, False))
    all_blocked = public_ranges(cards("As Qh 4h 5s 6c"), ranges)
    assert all_blocked.joint == ((False, False), (False, False))


def test_random_physical_worlds_against_independent_set_oracle() -> None:
    rng = default_rng(41)
    for _ in range(100):
        board = tuple(int(v) for v in rng.choice(52, 5, replace=False))
        ranges = tuple(
            tuple(
                tuple(int(v) for v in rng.choice(52, 2, replace=False))
                for _ in range(n)
            )
            for n in (3, 2)
        )
        if any(len({frozenset(h) for h in side}) != len(side) for side in ranges):
            continue
        assert public_ranges(board, ranges) == oracle(board, ranges)


def test_suit_and_range_order_equivariance_and_board_order_invariance() -> None:
    board = cards("Ts 9s 4d 2h 9d")
    before = public_ranges(board, RANGES)
    suit = (2, 0, 3, 1)

    def swap(card: int) -> int:
        return 4 * (card // 4) + suit[card % 4]

    transformed = tuple(tuple(tuple(swap(c) for c in h) for h in r) for r in RANGES)
    assert public_ranges(tuple(swap(c) for c in board), transformed) == before
    assert public_ranges(tuple(reversed(board)), RANGES) == before
    after = public_ranges(board, tuple(tuple(reversed(r)) for r in RANGES))
    assert after.available == tuple(tuple(reversed(r)) for r in before.available)
    assert after.joint == tuple(tuple(reversed(r)) for r in reversed(before.joint))


def test_joint_is_determined_by_public_masks_and_fixed_intersections() -> None:
    for river in ("9d", "9h", "5c", "Jd", "Th"):
        board = cards("Ts 9s 4d 2h " + river)
        f = public_ranges(board, RANGES)
        assert f.joint == tuple(
            tuple(
                f.available[0][i] and f.available[1][j] and set(left).isdisjoint(right)
                for j, right in enumerate(RANGES[1])
            )
            for i, left in enumerate(RANGES[0])
        )


def test_features_are_immutable_and_records_do_not_alias_them() -> None:
    f = public_ranges(cards("Ts 9s 4d 2h 9d"), RANGES)
    with pytest.raises(FrozenInstanceError):
        f.available = ()  # type: ignore[misc]
    record = f.record()
    record["available"][0][0] = False
    assert f.available[0][0] is True


@pytest.mark.parametrize("board", [(0, 1), (0, 1, 2, 3, 3), (0, 1, 2, 3, 52)])
def test_invalid_board_is_rejected(board: tuple[int, ...]) -> None:
    with pytest.raises(ValueError):
        public_ranges(board, RANGES)


@pytest.mark.parametrize("bad", [True, -1, 52])
def test_invalid_card_values_rejected(bad: int) -> None:
    with pytest.raises((TypeError, ValueError)):
        public_ranges((0, 1, 2, 3, bad), RANGES)


@pytest.mark.parametrize(
    "ranges",
    [
        (),
        ((), ()),
        ((cards("As Kd"),),),
        ((cards("As As"),), (cards("Qh Kh"),)),
        ((cards("As Kd"), cards("Kd As")), (cards("Qh Kh"),)),
    ],
)
def test_invalid_or_duplicate_ranges_rejected(ranges: Ranges) -> None:
    with pytest.raises((TypeError, ValueError)):
        public_ranges(cards("2c 3d 4h 5s 6c"), ranges)


@pytest.mark.parametrize(
    "target,own", [(True, "As Js"), (2, "As Js"), (1, "9c 9d"), (0, "Ac Kc")]
)
def test_invalid_source_own_projection_rejected(target: int, own: str) -> None:
    feature = public_ranges(cards("Ts 9s 4d 2h 9d"), RANGES)
    with pytest.raises((ValueError, ArithmeticError)):
        compatible_with_own(feature, RANGES, target, cards(own))
