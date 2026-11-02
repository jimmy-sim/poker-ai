# Phase 1 — Card representation and decks

## Full phase acceptance gate

Phase 1 is complete only when all of the following pass:

- Card encoding, set conversion, exclusion, shuffle, and deal invariants.
- Own 5–7 card evaluator with category, kicker, tie, wheel-straight, and order
  invariance checks; fixed-seed validation against eval7/treys on millions of hands.
- Exact and Monte Carlo equity with documented tie handling, sampling assumptions,
  uncertainty, and checks against tractable exact cases.
- Full Hold'em engine for the approved seat range, covering legal betting,
  all-ins, raise/reopening rules, side pots, showdown, and chip conservation using
  unit and property tests.
- Reproducible validation runners and saved evidence; all project checks pass.

Only the first item is implemented in this step. No evaluator or playing-strength
claim follows from these representation tests.

## Encoding contract

The public representation uses built-in Python integers:

```text
card_id = 4 * (rank - 2) + suit
rank: 2 through 14, with ace = 14
suit: clubs = 0, diamonds = 1, hearts = 2, spades = 3
card_bit = 1 << card_id
```

| Card | Rank | Suit index | ID |
| --- | --- | --- | --- |
| 2c | 2 | 0 | 0 |
| Th | 10 | 2 | 34 |
| As | 14 | 3 | 51 |

Notation is case-sensitive: `23456789TJQKA` followed by `cdhs`. Invalid values
raise ValueError; invalid types raise TypeError. Booleans and NumPy integer scalars
are rejected at public integer boundaries; shuffle output is converted explicitly
to built-in integers. This avoids implicit coercion and fixed-width bitwise
arithmetic in the representation layer. Suit indices are encoding choices and do
not establish a poker ranking between suits.

## Sets and order serve different purposes

A mask is a set of cards. It fits within the lowest 52 bits, and the empty set is
zero. `cards_to_mask` rejects duplicates instead of silently erasing an impossible
deal. `mask_to_cards` returns ascending IDs; it cannot recover input order.

Given valid masks A and B, `A & B` detects shared cards, `A | B` forms their union,
and `A.bit_count()` counts cards. A complement must be restricted to the deck:
`FULL_DECK_MASK ^ A`; plain `~A` includes bits outside the valid card space.

A `Deck` preserves deal order as an immutable tuple. `draw(n)` returns the drawn
prefix and a new deck. Zero draws are valid, overdraws fail, and neither successful
nor failed draws mutate the original. Partial and empty decks are valid.

```python
from numpy.random import PCG64, Generator

from poker_ai.cards import Deck, cards_to_mask, format_card, parse_card

known = tuple(map(parse_card, ("As", "Ah")))
rng = Generator(PCG64(20261102))
deck = Deck.shuffled(rng, excluded_mask=cards_to_mask(known))
flop, remaining = deck.draw(3)
assert len(deck) == 50
assert len(remaining) == 47
assert not (remaining.mask & cards_to_mask(flop))
assert not (deck.mask & cards_to_mask(known))
print(tuple(map(format_card, flop)))
```

`Deck.shuffled` uses the supplied generator and advances its stream; the caller
owns seeding and lifetime. Reconstructing the same PCG64 stream reproduces deals
under the locked environment. Exclusion removes already-known cards before the
shuffle. NumPy's [permutation API](https://numpy.org/doc/stable/reference/random/generated/numpy.random.Generator.permutation.html)
returns a shuffled copy of the available card sequence.

## Validation and limits

Tests cover every card ID, known encoding examples, invalid inputs, duplicate
rejection, masks, deal order, exhaustion, immutable state, reproducible RNG streams,
and shuffled decks excluding known cards. Property tests generate card sets and
masks and check round trips, set identities, and conservation/disjointness through
draws. These tests check structural correctness, not a statistical claim about
shuffle frequencies.

`tests/conftest.py` loads deterministic Hypothesis settings with up to 200 examples
per property and no wall-clock deadline. Persist minimized failures as explicit
regressions before changing dependencies or test definitions. See the
[Hypothesis settings reference](https://hypothesis.readthedocs.io/en/latest/reference/api.html#hypothesis.settings).

Run the canonical checks with `make check` and the hooks with
`uv run --locked pre-commit run --all-files`. Use `pytest tests/test_cards.py`
through `uv run --locked` for the focused representation suite.

Deck slicing and validation favor clarity. Computing `Deck.mask` scans its cards;
constructing the remaining deck also validates its contents. These are deliberate
correctness-first costs, not a performance benchmark. Profile actual workloads
before caching masks, introducing a cursor, or adding Numba.

## Local verification — 2026-11-02

Tests were added before the module: the initial focused run failed because
`poker_ai.cards` did not exist. After implementation and fixes:

| Environment | `make check` |
| --- | --- |
| CPython 3.11.17, NumPy 2.4.6 | Lint, format, strict typing, and all 102 tests pass |
| CPython 3.12.15, NumPy 2.5.4 | Lint, format, strict typing, and all 102 tests pass |

Both environments use the existing committed lockfile. Dependency versions were
unchanged. mypy now uses its running interpreter so each matrix job parses the
matching NumPy stubs; Python 3.11 remains the baseline compatibility gate.
These are local macOS results; hosted Ubuntu CI has not been run for this step.

## Review questions

1. **Why use both a tuple and a mask?** The tuple preserves future deal order;
   the mask makes set overlap and membership operations simple. A set cannot
   encode order.
2. **Why reject duplicate cards before making a mask?** Bitwise OR would collapse
   duplicates and conceal an impossible game state or evaluator input.
3. **Why pass an RNG explicitly?** It makes the source of randomness visible,
   supports stream replay, and avoids accidental shared global state. Exact
   replay also depends on recording the environment and call sequence.

Next: a transparent five-card evaluator, then best-of-five evaluation for six and
seven cards. Establish ranking correctness before optimizing it.
