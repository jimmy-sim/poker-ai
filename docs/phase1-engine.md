# Hold'em engine contract and validation

Phase 1 engine acceptance: own 2–6-seat cash-game state transitions, legal actions,
all four betting streets, all-ins, side pots, showdown, private observations,
property tests, and an independent transition comparison. This is a simulation
component; correctness tests make no claim about playing strength.

## Rules and interfaces

`new_hand(stacks, deck, button=..., small_blind=1, big_blind=2)` requires a complete,
explicitly ordered deck and positive built-in integer starting stacks. Chance
comes exclusively from that deck. Heads-up, the button posts the small blind and
acts first preflop; the big blind acts first postflop. At larger tables, dealing
and blinds start left of the button. Each board street burns one card.

`HoldemState` and its transitions are immutable. `Action(RAISE_TO, amount)` means
the player's total commitment on the current street. Legal raise bounds are
inclusive; a short all-in has identical minimum and maximum. Full raises reopen
action; cumulative short raises reopen only after the amount faced since a
player's last action reaches a full raise. Checking before a short opening bet
retains raising rights. A prior caller facing less than a full raise cannot raise.
There is no raising into a dry side pot. A short big blind retains the nominal
preflop bring-in when multiple funded players can contest it.

Contribution caps form main/side pots. Folded contributions remain in the pot;
folded players cannot win an unresolved contested pot. Adjacent layers with
identical eligible players merge. Uncalled top contributions return to their
contributor. A side pot already secured when opponents fold remains awarded even
if its owner later folds the main pot. Tied integer payouts distribute each odd
chip to the next tied winner clockwise left of the button, separately per pot.
Free folds are allowed in this cash-game model, including when checking is free.

Bots receive `state.observe(seat)`: their own cards, public history/board/stacks,
and legal actions when acting. It contains no other hole cards, burn cards,
remaining deck, or dealer-state reference. Do not pass `HoldemState` to a bot.

Excluded: antes, rake, straddles, multiple boards, tournament penalties, table
movement/dead-button administration, and fixed-limit betting (a later phase).
States are constructed through `new_hand` and `apply`; direct dataclass mutation
or arbitrary reconstruction is not a supported game-building interface.

## Independent reference and declared differences

PokerKit **0.7.7**, pinned in the optional `engine-validation` extra, is used only
by `scripts/validate_engine.py`. Its installed full MIT license was read: copyright
2023–2026 University of Toronto Computer Poker Student Research Group; permission
to use, copy, modify and distribute with notice preservation, without warranty.
No reference code is copied into production. See the
[upstream license](https://github.com/uoftcprg/pokerkit/blob/v0.7.7/LICENSE) and
[simulation API](https://pokerkit.readthedocs.io/en/stable/simulation.html).

Four observed limitations are explicit probes in the report:

1. Short big blind `(100,1,100)`: our nominal bring-in is 2; the reference requests
   1. The randomized matched domain starts at 2 chips and covers both blinds.
2. Last-funded free fold after securing a side pot: reference raises an assertion;
   our analytical test retains that side pot. Random drivers check/call in this
   situation; the unsupported reference path is not counted as a matching trace.
3. A prior preflop caller after a short all-in can raise in the reference even
   though it has not faced a full raise. The comparator independently reconstructs
   the street's public wagers and counts only this specific reference allowance.
   Chosen actions always obey our legal set. This is not universal legal-set
   agreement. Upstream snapshot `abf795299eaac41183495a0956ce7136ce38ed64` was also
   tested for this case and did not resolve it; the dependency remains 0.7.7.
4. Default reference rounding can give multiple remainder chips to one tied
   winner. Our rule gives at most one per winner on each pass. The main comparison
   uses the reference's documented `divmod` hook with exact rational division and
   compares unrounded terminal shares. Our integer rounding is checked separately,
   including an eleven-chip pot shared three ways. It is not claimed to match
   every default reference integer payout.

The wagering convention follows the full-raise reopening principle in
[Poker TDA rules, rule 49](https://www.pokertda.com/view-poker-tda-rules/);
odd-chip direction and separate side-pot treatment follow rules 21/23. TDA is a
rules reference, not a claim that every tournament rule applies to this cash model.
A failed prototype trace is preserved in `results/diagnostics/` with its actual
source/dirty status. Differences were reduced to explicit cases before adjusting
the comparison scope; no trace was silently labeled a match.

## Reproduction and limits

```sh
make check
make validate-engine
```

The fixed config specifies 1,000 hands, PCG64 seed 20261107, 2–6 random seats,
2–150 chip stacks, rotating passive/raise-heavy/mixed/postflop action drivers,
and an action budget. Both engines receive the same holes, burns, board, button,
and actions. Compare actor, board, active stacks, street wagers, calls, raise
bounds (with counted exception above), terminal status, and rational payouts.
The report saves source hashes/revision, lock hash, input/trace digest, runtime,
environment, failures, counts, and differences. It exits nonzero on an unexplained
mismatch. `results/engine-validation.json` is generated from committed source.

Hypothesis explores legal complete games with stacks down to one chip and checks
termination, chip conservation/nonnegativity, and exact deck partitioning. Unit
cases cover reopening, private observations, fold settlement, dry side pots,
uncalled returns, folded best hands, secured pots, and odd chips. Random/reference
traces and property tests are sampled coverage, not a proof of all reachable games.
