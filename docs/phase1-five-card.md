# Phase 1 — Five-card hand evaluator

## Contract and acceptance criteria

`evaluate_five(cards)` accepts an iterable of exactly five distinct valid card IDs
and returns an immutable `HandRank`. Incorrect hand sizes and duplicate/out-of-range
cards raise ValueError; incorrect card types raise TypeError. Inputs are consumed
once and never mutated. The earlier [card encoding contract](phase1-cards.md)
applies unchanged.

This step requires correct categories, tie-breakers, ace-low straights, ties across
suits, order invariance, input validation, strict typing, and an independent
reference check. Exact reference agreement has zero allowed failures. Phase 1's
six/seven-card evaluation, equity calculations, and full betting engine remain
separate subsequent steps.

## Comparing hands

`HandRank` orders first by category, then lexicographically by its rank tuple.
**Larger means stronger.** Tuples contain only the information that breaks ties;
suits have no ranking. Values express order, not equity, win probability, or EV.

| Category, weakest first | Tie-breakers, highest priority first |
| --- | --- |
| High card | All five ranks, descending |
| One pair | Pair rank, then three descending kickers |
| Two pair | Higher pair, lower pair, kicker |
| Three of a kind | Trip rank, then two descending kickers |
| Straight | Highest rank; A-2-3-4-5 uses 5 |
| Flush | All five ranks, descending |
| Full house | Trip rank, pair rank |
| Four of a kind | Quad rank, kicker |
| Straight flush | Highest rank; A-2-3-4-5 uses 5 |

A royal flush is an ace-high straight flush. Ace remains rank 14 in card encoding;
only the straight comparison key changes for the exact wheel rank set. Sequences
such as Q-K-A-2-3 do not wrap around into straights.

```python
from poker_ai.cards import parse_card
from poker_ai.evaluator import HandCategory, HandRank, evaluate_five

wheel = evaluate_five(map(parse_card, "Ac 2d 3h 4s 5c".split()))
six_high = evaluate_five(map(parse_card, "2c 3d 4h 5s 6c".split()))
assert wheel == HandRank(HandCategory.STRAIGHT, (5,))
assert six_high > wheel
```

## Algorithm and tradeoffs

Validate through the existing card-set boundary. Count ranks and sort
`(multiplicity, rank)` groups descending. This puts the pair/trip/quad ranks ahead
of kickers and orders equal-sized groups by rank. Inspect suit equality for a
flush and distinct rank sequences for a straight. Apply category precedence
explicitly, including straight flush before flush or straight.

This is a readable reference implementation using Python counters and sorting.
No poker-library lookup table or reference output enters production evaluation.
Its allocation/validation costs should be profiled when six/seven-card traversal
and simulation workloads exist; no optimized-core speed claim is made here.

## Independent reference protocol

Treys 0.1.8 is pinned in the optional `validation` extra. The installed package's
MIT license was read, including its copyright/permission notice and warranty
disclaimer. See the [upstream project and license](https://github.com/ihendley/treys).
Treys is a hand-evaluation library used only for validation, separate from the
future gated external **strategy-solver** validation milestone.

The reference uses lower integers for stronger hands, opposite to our HandRank.
The harness checks a two-way mapping between own ranks and reference scores: own
ties must be reference ties, and reference ties must be own ties. It then sorts
all observed own ranks and requires strictly decreasing reference scores. This
checks tie-breaker ordering, not just category labels.

The exhaustive config enumerates every physical five-card combination in
lexicographic order. It additionally checks category totals against independent
combinatorial formulas and the expected number of distinct rank classes. No RNG
is involved; `seed: null` explicitly records that. The smaller smoke config uses
an explicit PCG64 seed for repeatable random sampling.

Reports include raw category counts, failure witnesses, rank-class counts, input
digest, source/config/lock hashes, Git revision/dirty status, library/interpreter
versions, machine details, and validation runtime. These are validation timings,
not isolated evaluator benchmarks. Failed checks write evidence and return a
nonzero exit code. Harness tests deliberately introduce false ties, false
distinctions, and incorrect ordering to check detection.

## Reproduce

From the repository root with the documented uv version on PATH:

```sh
make setup
make check
make validate-five
```

`make validate-five` installs only the declared optional validation extra and
writes `results/five-card-exhaustive.json`. It stays outside routine CI. A rerun
updates provenance and timing while exact hand counts and agreement should match.

For a smaller run or an alternate output path:

```sh
uv run --locked --extra validation python scripts/validate_five.py \
    --config configs/five-card-smoke.json \
    --output results/runs/five-card-smoke.json
```

The focused tests need no reference library:

```sh
.venv/bin/python -m pytest -q tests/test_evaluator.py tests/test_five_card_validation.py
```

## Verification status

Local `make check` passes on CPython 3.11.17 and 3.12.15: all 202 tests,
Ruff lint/format checks, and strict typing of implementation, tests, and scripts.
The initial evaluator test run failed because the module did not exist; tests
were added first. Hosted Ubuntu CI has not been run for this step.

The exhaustive run **passed** on clean source revision `ff3302eb63e95874e242f14540f1c1325a6c4db4`.
All **2,598,960** physical five-card hands agree with Treys on equality classes
and rank ordering, covering **7,462** distinct ranks with zero failures.
The complete category census also matches the independent combinatorial formulas.

| Category | Observed physical hands | Combinatorial expectation |
| --- | ---: | ---: |
| High Card | 1,302,540 | 1,302,540 |
| One Pair | 1,098,240 | 1,098,240 |
| Two Pair | 123,552 | 123,552 |
| Three Of A Kind | 54,912 | 54,912 |
| Straight | 10,200 | 10,200 |
| Flush | 5,108 | 5,108 |
| Full House | 3,744 | 3,744 |
| Four Of A Kind | 624 | 624 |
| Straight Flush | 40 | 40 |

The [raw report](../results/five-card-exhaustive.json) records exact source/config
hashes, input digest, environment, and measured validation time. The report's
revision precedes the documentation/results commit so that its source tree was
clean when validation started. Reproduce its exact code with that revision and
`make validate-five`; a new run will have its own provenance/timing fields.

This establishes five-card reference agreement under the tested high-poker rules.
It does not establish six/seven-card selection, equity estimates, legal betting,
chip payouts, or playing strength. Those retain their own Phase 1 acceptance gates.

## Interview questions

1. **How do you encode tie-breakers correctly?** Category is compared first;
   within it, rank tuples follow poker priority, such as trip rank before pair
   rank in a full house. Suits never break ties.
2. **Why does checking categories alone miss bugs?** Two hands can share a
   category yet differ in their second or third kicker. A reference bijection
   plus rank ordering checks both equality classes and all strength comparisons.
3. **Does exhaustive five-card validation establish the whole engine?** It
   establishes agreement over five-card inputs under the tested rules. Best-of-five
   selection, equity sampling, legal betting, and payouts require their own tests.

Next: six/seven-card best-of-five evaluation and its independent checks, before
profiling and optimization.
