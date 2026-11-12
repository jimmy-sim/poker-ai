"""Public availability of complete alternative ranges, never actual hidden hands."""

from dataclasses import dataclass

from poker_ai.cards import cards_to_mask

Ranges = tuple[tuple[tuple[int, ...], ...], ...]


@dataclass(frozen=True)
class PublicRanges:
    available: tuple[tuple[bool, ...], ...]
    joint: tuple[tuple[bool, ...], ...]

    def record(self) -> dict[str, list[list[bool]]]:
        return {
            "available": [list(row) for row in self.available],
            "joint": [list(row) for row in self.joint],
        }


def public_ranges(board: tuple[int, ...], ranges: Ranges) -> PublicRanges:
    """Use public board + ALL declared alternatives, not actual own hole cards.

    An alternative own hand may share cards with the actual own hand: those
    hands are mutually exclusive hypotheses, not simultaneous physical cards.
    Joint(i,j) refers to one hypothetical hand per player. It is determined by
    both public masks and their fixed pairwise private-card intersections.
    Blocked rows/columns, including an all-zero matrix, remain explicit.
    """
    if len(board) != 5 or len(ranges) != 2 or any(not r for r in ranges):
        raise ValueError("need river board and two complete nonempty ranges")
    known = cards_to_mask(board)
    masks = []
    for declared in ranges:
        if any(len(hand) != 2 for hand in declared):
            raise ValueError("every declared hand needs two physical cards")
        row = tuple(cards_to_mask(hand) for hand in declared)
        if len(set(row)) != len(row):
            raise ValueError("duplicate unordered hand in a declared range")
        masks.append(row)
    available = tuple(tuple(not bool(h & known) for h in row) for row in masks)
    joint = tuple(
        tuple(
            available[0][i] and available[1][j] and not bool(left & right)
            for j, right in enumerate(masks[1])
        )
        for i, left in enumerate(masks[0])
    )
    return PublicRanges(available, joint)


def compatible_with_own(
    features: PublicRanges, ranges: Ranges, target: int, own: tuple[int, ...]
) -> tuple[bool, ...]:
    """Validate the source actual-own row AFTER constructing the public feature.

    This projection never changes alternatives or feeds an actual private hand
    into public_ranges. No actual opponent hand is accepted by either API.
    """
    if type(target) is not int or target not in (0, 1) or len(own) != 2:
        raise ValueError("source own-row projection needs seat zero/one and two cards")
    mask = cards_to_mask(own)
    matches = [i for i, h in enumerate(ranges[target]) if cards_to_mask(h) == mask]
    if len(matches) != 1 or not features.available[target][matches[0]]:
        raise ArithmeticError("source actual own hand is absent or publicly blocked")
    index = matches[0]
    return (
        features.joint[index]
        if target == 0
        else tuple(row[index] for row in features.joint)
    )
