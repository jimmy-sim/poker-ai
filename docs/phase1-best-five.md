# Phase 1 — Six/seven-card best-five evaluation

## Contract and method

`evaluate_best(cards)` accepts five to seven distinct valid card IDs and returns
the strongest five-card `HandRank`. Larger ranks are stronger, using the same
[category/tie-breaker contract](phase1-five-card.md). It validates the entire
input before selection, including cards that would be discarded. It accepts a
one-pass iterable and does not mutate inputs.

The method computes the maximum of `evaluate_five(subset)` over every five-card
subset. There is one subset for five cards, six for six cards, and 21 for seven
cards. This reuses the exhaustively validated five-card implementation as a
readable correctness baseline. It deliberately retains repeated subset validation
and allocation costs; profile actual workloads before optimization.

Hold'em permits any five of the seven available cards, including all five board
cards. The function imposes no requirement to use exactly two hole cards.

```python
from poker_ai.cards import parse_card
from poker_ai.evaluator import HandCategory, HandRank, evaluate_best

cards = tuple(map(parse_card, "Ac Ad Ah Kc Kd Kh 2s".split()))
assert evaluate_best(cards) == HandRank(HandCategory.FULL_HOUSE, (14, 13))

board = tuple(map(parse_card, "Tc Jc Qc Kc Ac".split()))
first = evaluate_best(board + tuple(map(parse_card, "2d 3h".split())))
second = evaluate_best(board + tuple(map(parse_card, "4d 5h".split())))
assert first == second  # Both players play the royal flush on the board.
```

## Acceptance criteria

- Known best-hand cases: two trips, three pairs, competing full houses, quad
  kickers, long flushes, overlapping straights, and straight flushes.
- Board-only ties and hole cards improving a board's kicker.
- Card-order and suit-relabeling invariance; adding a card cannot weaken the best
  hand. Five-card inputs agree with `evaluate_five`.
- Reject bad hand sizes, duplicate cards, invalid IDs/types, and invalid cards
  even when a valid strongest hand is already present among the other cards.
- Strict typing, formatting, lint, unit/property/harness checks on Python 3.11
  and 3.12; zero sampled reference disagreements at the declared budgets below.

## Reference calibration and sampling

The existing optional Treys 0.1.8 dependency remains comparison-only. No reference
map or library is imported into production evaluation. This hand-evaluation check
is separate from the future gated strategy-solver validation milestone.

First, generate a canonical physical representative of each five-card rank class:
iterate rank multisets, exclude five-of-a-kind, use distinct suits for repeated
ranks, and create flush/nonflush representatives for five distinct ranks. Compare
the previously validated five-card keys to Treys scores. Require all 7,462 classes,
a bijection, and the correct order. This calibrates opposite scoring directions.

Next, independently sample six/seven-card inputs and ask Treys to evaluate each
complete input. Convert its score through the calibrated map and compare the
exact category and tie-breakers with `evaluate_best`. This can detect selecting
the wrong five-card subset even if the error preserves sampled relative ordering.
The calibration relies on the earlier five-card validation; Treys independently
performs the six/seven-card selection.

Declare full budgets before execution in `configs/best-five-validation.json`:

| Cards | Sampled hands | PCG64 seed | Allowed disagreements |
| --- | ---: | ---: | ---: |
| 6 | 1,000,000 | 20261103 | 0 |
| 7 | 1,000,000 | 20261104 | 0 |

Sampling is without replacement within a hand and independent between draws;
whole deals can repeat. The smoke config uses the same streams with smaller
budgets for cost estimation. Calibration errors raise; sampled mismatches stop
the run with a concrete witness and nonzero exit status. Empty plans cannot pass.
Harness tests exercise complete calibration, wrong order, false ties, and
deliberately incorrect reference scores. Synthetic test oracles test the harness;
published results use actual Treys.

Reports save per-size actual/configured counts, category counts, observed rank
classes, input digests, seeds, failures, source/config/entrypoint/lock hashes,
revision/dirty status, environment, and timing. Timings include validation and
oracle work, so they are not isolated evaluator benchmarks.

## Reproduce

From the repository root with uv 0.13.5 on PATH:

```sh
make check
make validate-best
```

The full command installs the declared optional extra and writes
`results/best-five-validation.json`. The million-hand checks stay outside routine
CI. To run the pilot separately:

```sh
uv run --locked --extra validation python scripts/validate_best.py \
    --config configs/best-five-smoke.json \
    --output results/runs/best-five-smoke.json
```

Focused unit/property/harness checks require no reference library:

```sh
.venv/bin/python -m pytest -q tests/test_best_of_five.py tests/test_best_validation.py
```

## Verification status

Local `make check` passes on CPython 3.11.17 and 3.12.15: all 273 tests,
Ruff lint/format, and strict typing of implementation, tests, and scripts.
Tests were added before evaluate_best; the first focused run failed because that
entry point did not exist. Hosted Ubuntu CI has not run for this step.

Full sampled results will be added after execution from a committed clean source
revision. The five-card classifier's AST was checked against the prior revision
and is unchanged; only the new selection wrapper was added.

## Interpretation and next work

Random samples are not exhaustive six/seven-card proofs. Agreement on hand ranks
does not validate equity sampling, betting rules, side pots, or playing strength.
Those remain later Phase 1 tasks. The five-card exhaustive result retains its
recorded source revision; its classification logic is unchanged in this step.

Next: profile this baseline before choosing evaluator optimizations and building
exact/Monte Carlo equity calculations.

## Interview questions

1. **Why enumerate five-card subsets?** The definition of a best-five hand is the
   strongest rank among those subsets. A complete small enumeration is clear and
   provides a correctness reference for a faster direct evaluator.
2. **Why allow a player to use neither hole card?** Hold'em chooses any five from
   the two hole cards and board. A board royal flush is therefore a tie for all
   remaining players.
3. **What do the external checks establish?** They check exact rank agreement on
   reproducible sampled hands, anchored by complete five-card class calibration.
   They do not enumerate every six/seven-card deal or establish game-engine
   correctness or an agent's strategic quality.
