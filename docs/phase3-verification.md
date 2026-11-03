# Phase 3 bounded implementation acceptance

The predeclared implementation/compute gate is complete. Own heads-up limit and
no-limit agents exist with reproducible checkpoints and observation-only inference.
This is a bounded research prototype, not a solved or competitively strong agent.
No full-Hold'em exploitability or win rate has been established.

| Requirement | Verification | Scope/limits |
| --- | --- | --- |
| External/outcome MCCFR | Exact sampled-update expectation tests on uniform/nonuniform Kuhn; seeded toy convergence pilot | Two players; simple external averaging; outcome importance weights can have high variance |
| Limit before no-limit | Funded capped limit adapter and 12 limit runs through 500 iterations, then 12 NL runs through 300 | Limit stacks cover all capped wagers; no short-limit-all-in completion model |
| Card abstractions | Current EHS, final distributions, future-street marginal potential; 2/4/8 buckets; k-means/W1 medians; disjoint-state errors | Noisy finite prototypes, uniform-opponent features, no joint future-trajectory representation or strategic error bound |
| Action abstraction/translation | Rational pot-relative legal grids; nearest/pseudo-harmonic mapping; separate public shadow ledger and mapped probabilities | Explicit clipping/failure/fallback diagnostics; no preserved-exploitability guarantee |
| Checkpoints/resumption | Atomic own format; exact PCG64 restoration; bit-identical resumed arrays, including rebuilt feature caches; CLI smoke tests | Exact continuation requires recorded config/models/core implementation |
| Multiprocessing/memory | Independent spawned seed runs, traced interval allocations and RSS conventions, CPU/timing records | Earlier limit workers reused; NL workers isolated; concurrency/tracing affect timings |
| Own inference boundary | Own-format/model/encoder checks; rejects reference JSON; 30-hand/78-decision audit | Sparse table coverage; all 12 constructed off-grid stress cases fell back |
| Local quality | 392 tests; Ruff lint/format and strict mypy on Python 3.11 and 3.12 | Hosted CI has not run |

The [complete methodology and results](phase3-training.md) link every raw report.
Main evidence: `results/mccfr-pilot.json`, `results/card-abstraction.json`,
`results/limit-training.json`, `results/no-limit-training.json`, and
`results/agent-interface-validation.json`. Every report preserves its actual
committed source, config/seeds/hashes, timing and environment. Large own checkpoints
stay under ignored `results/runs/` with recorded SHA256; commands reproduce them.

## Reproduction

```sh
make check
make train-mccfr-pilot
make build-card-abstraction
make train-limit
make train-no-limit
make verify-agent
```

The toy/card experiments are small; traced multi-seed Hold'em runs take minutes
on the recorded M4. No-limit passes/runs have explicit abort budgets. Aborted
iterations never export truncated strategy updates as completed checkpoints.

## Interview questions

**How can sampling the tree produce correct regret updates?** External sampling
integrates chance/opponent behavior through their sampling probabilities while
enumerating own actions. Outcome sampling estimates action values with behavior
likelihood corrections; prefix weights exclude own reach for regrets and include
it for averaging. Exact finite Kuhn expectations test those formulas before use
in Hold'em. Unbiased updates can still have high variance and slow convergence.

**Why did richer card models not win every feature comparison?** Small noisy
prototypes, different fitting objectives and finite held-out data matter. A final
histogram k-means objective differs from all-street W1 reconstruction; averaging
can also denoise noisy measurements. We report all outcomes/occupied counts and
measurement disagreement. Feature error is not a certificate about game value or
a substitute for strategy evaluation.

**Why isn't off-tree size translation enough to deploy a policy?** Off-grid bets
change public pot/stack histories. We keep actual accounting intact, replay a
virtual abstract history, use actual own cards/board for lookup, and translate
probability mass back to legal actual actions. Virtual all-ins can make a history
irreconcilable; unseen/unaveraged rows also need explicit fallbacks. Our stress
audit exposed those limitations. Legality and reproducibility do not prove strength.

Phase 2 exploitability results and trained Phase 3 agents now satisfy the Phase 3.5
prerequisites. External strategy comparisons may begin; their results are not
claimed by this report and reference outputs remain comparison-only.
