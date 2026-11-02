"""Card IDs, card-set bitmasks, and immutable ordered decks.

A card is a built-in int in [0, 51]: ``4 * (rank - 2) + suit``, where ranks
are 2 through 14 (ace) and suits are clubs, diamonds, hearts, spades (0 through 3).
The card's bit is ``1 << card``. Masks represent sets, so they discard deal order.
Human-readable cards use exactly two characters, e.g. ``Th`` or ``As``.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Final, Self

from numpy.random import Generator

RANKS: Final = "23456789TJQKA"
SUITS: Final = "cdhs"
DECK_SIZE: Final = 52
FULL_DECK_MASK: Final = (1 << DECK_SIZE) - 1


def _require_int_in_range(value: int, name: str, low: int, high: int) -> None:
    """Avoid implicit coercion, including bools and fixed-width NumPy integers."""
    if type(value) is not int:
        raise TypeError(f"{name} must be a built-in int")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in [{low}, {high}], got {value}")


def make_card(rank: int, suit: int) -> int:
    """Encode rank 2–14 and suit 0–3 as a card ID; ace has rank 14."""
    _require_int_in_range(rank, "rank", 2, 14)
    _require_int_in_range(suit, "suit", 0, 3)
    return 4 * (rank - 2) + suit


def parse_card(text: str) -> int:
    """Parse canonical notation: rank in 23456789TJQKA, suit in cdhs.

    Input is case-sensitive; ten is T. Reject whitespace and Unicode suits to
    keep serialization unambiguous. Raise TypeError for non-string inputs.
    """
    if not isinstance(text, str):
        raise TypeError("card notation must be a string")
    if len(text) != 2 or text[0] not in RANKS or text[1] not in SUITS:
        raise ValueError(f"invalid card notation: {text!r}")
    return make_card(RANKS.index(text[0]) + 2, SUITS.index(text[1]))


def format_card(card: int) -> str:
    """Format a valid card ID as canonical two-character notation."""
    _require_int_in_range(card, "card", 0, DECK_SIZE - 1)
    return RANKS[card // 4] + SUITS[card % 4]


def rank_of(card: int) -> int:
    """Return rank 2–14; ace remains 14, including in wheel straights."""
    _require_int_in_range(card, "card", 0, DECK_SIZE - 1)
    return card // 4 + 2


def suit_of(card: int) -> int:
    """Return suit index: clubs=0, diamonds=1, hearts=2, spades=3."""
    _require_int_in_range(card, "card", 0, DECK_SIZE - 1)
    return card % 4


def card_bit(card: int) -> int:
    """Return the unique bit for a valid card ID."""
    _require_int_in_range(card, "card", 0, DECK_SIZE - 1)
    return 1 << card


def cards_to_mask(cards: Iterable[int]) -> int:
    """Encode a card set, rejecting invalid IDs and duplicate physical cards.

    Duplicate rejection matters: simply OR-ing input bits would silently erase
    an impossible deal. An empty iterable represents the empty set, mask zero.
    """
    mask = 0
    for card in cards:
        bit = card_bit(card)
        if mask & bit:
            raise ValueError(f"duplicate card: {format_card(card)}")
        mask |= bit
    return mask


def mask_to_cards(mask: int) -> tuple[int, ...]:
    """Decode a valid 52-bit mask into ascending card IDs.

    ``mask & -mask`` isolates the lowest set bit. Removing that bit after each
    iteration visits exactly the cards present, in canonical ID order.
    """
    _require_int_in_range(mask, "mask", 0, FULL_DECK_MASK)
    cards = []
    while mask:
        bit = mask & -mask
        cards.append(bit.bit_length() - 1)
        mask ^= bit
    return tuple(cards)


@dataclass(frozen=True, slots=True)
class Deck:
    """An immutable ordered tuple of remaining cards, dealt from the front.

    Deck() creates an ordered full deck; use shuffled() for a random deal. Partial
    and empty decks are valid. Draws produce a new deck, preserving the original
    for replay and state-transition tests. This clarity-first implementation
    validates each constructed deck; profile before replacing it with a cursor.
    """

    cards: tuple[int, ...] = tuple(range(DECK_SIZE))

    def __post_init__(self) -> None:
        if not isinstance(self.cards, tuple):
            raise TypeError("deck cards must be an immutable tuple")
        cards_to_mask(self.cards)

    def __len__(self) -> int:
        """Return the number of undealt cards."""
        return len(self.cards)

    @property
    def mask(self) -> int:
        """Return the set of remaining cards; this loses their deal order."""
        return cards_to_mask(self.cards)

    @classmethod
    def shuffled(cls, rng: Generator, *, excluded_mask: int = 0) -> Self:
        """Shuffle available cards using only the supplied NumPy RNG.

        Excluded bits represent already-known cards and must form a valid mask.
        The caller owns seeding and RNG lifetime. Reusing the generator advances
        its stream; this method never creates or seeds a hidden generator.
        """
        if not isinstance(rng, Generator):
            raise TypeError("rng must be an explicit numpy.random.Generator")
        _require_int_in_range(excluded_mask, "excluded_mask", 0, FULL_DECK_MASK)
        available = mask_to_cards(FULL_DECK_MASK ^ excluded_mask)
        # NumPy returns fixed-width scalars; convert at the representation boundary.
        return cls(tuple(int(card) for card in rng.permutation(available)))

    def draw(self, count: int) -> tuple[tuple[int, ...], "Deck"]:
        """Return (drawn cards, remaining deck), rejecting overdrawing.

        Drawing zero is valid. Failed draws leave this immutable deck unchanged.
        The count must be a built-in int between zero and len(self), inclusive.
        """
        _require_int_in_range(count, "draw count", 0, len(self))
        return self.cards[:count], Deck(self.cards[count:])
