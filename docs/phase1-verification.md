# Phase 1 verification

Acceptance gate passed locally on 2026-11-02. Cards/decks, own hand ranking,
heads-up equity and 2–6-seat no-limit Hold'em mechanics are implemented. These
are correctness and throughput results, not evidence of a strong poker agent.

| Component | Evidence | Scope |
| --- | --- | --- |
| Cards/decks | Unit and property tests | Strict card IDs, masks, uniqueness, immutable deals, explicit RNG |
| Five-card evaluator | `results/five-card-exhaustive.json` | All 2,598,960 physical hands, 7,462 ranks, zero Treys disagreements |
| Direct six/seven-card evaluator | `results/best-five-direct-validation.json` | Two million seeded sampled hands, zero Treys disagreements |
| Profile/paired performance | `results/evaluator-comparison.json` | Same fixed inputs, repeated timings, preserved subset reference |
| Exact/Monte Carlo equity | `results/equity-validation.json` | Five predeclared cases; exact Treys counts and bounded MC intervals |
| Hold'em engine | `results/engine-validation.json` | 1,000 hands, 10,039 actions, 920 board runouts, 471 side-pot hands |
| Fast local quality gate | `make check`, Python 3.11.17 and 3.12 | 326 tests; Ruff lint/format and strict mypy passed |

Initial engine evidence was generated from clean commit `23823ab`. The current
report records its own source revision; a later reporting correction separates
five-card board completions from contested showdowns (a river fold is not a
showdown). The transition corpus and comparison scope are unchanged. Three instances of the
reference's additional short-all-in raise allowance were counted; other checks
passed within the declared domain. Read [the engine contract](phase1-engine.md)
before interpreting this as agreement: the reference has short-blind/free-fold
limitations and a different default odd-chip rule. Terminal payouts were compared
as exact rational shares; own integer payouts have analytical regression tests.
The report probes each difference. This is not exhaustive engine verification.

Reproduce `make check`, `make validate-five`, `make validate-best`,
`make validate-equity`, and `make validate-engine` from a locked installation.
Long sweeps are intentionally outside routine CI. Published timing evidence is
machine-specific. Historical reports preserve their actual source revisions,
including dirty flags; later implementation changes do not rewrite those records.
Hosted GitHub CI has not run; local 3.11/3.12 checks are recorded separately.

## Interview questions

**Why keep the slow evaluator?** It is a readable implementation that enumerates
five-card subsets. It makes optimizations easier to inspect and measure. Treys
adds an independent implementation; agreement with our own reference alone would
not establish independence.

**Why can a Monte Carlo confidence interval have positive width after all wins?**
Zero observed variance does not prove the true win probability is one. The fixed-N
Hoeffding interval bounds fractional outcomes in [0,1] without estimating variance.
It is conservative; its coverage is a repeated-sampling statement. Exact equity
has no Monte Carlo sampling uncertainty for the fully specified range model.

**How did independent validation reveal engine weaknesses?** Traces exercised
short raises, dry side pots and free folds; minimized regressions caught mistakes
in our own engine before commit. Other minimized cases exposed reference rule
choices/limitations. We recorded those cases and narrowed the comparison claim
explicitly instead of treating the reference as an infallible oracle. Card/chip
conservation properties and analytical payouts remain separate checks.
