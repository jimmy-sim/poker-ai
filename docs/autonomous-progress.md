# Autonomous progress checkpoint

The user authorized continued autonomous work on 2026-11-02, following the roadmap
in order until stopped. The active goal continues through Phase 4; Phase 5 choices
and any C++/Rust core require the already-stated user decisions.

## Current phase: 3

Completed and committed:

- Card IDs, masks, immutable decks, explicit RNGs.
- Five-card evaluator; complete physical-hand comparison against Treys.
- Six/seven-card subset reference and direct rank-mask evaluator.
- Profile first, then paired direct/reference timings on identical fixed inputs.
- Independent direct-evaluator two-million-hand Treys comparison.
- Exact and Monte Carlo heads-up equity, card removal, explicit budgets,
  fractional ties, descriptive variance, estimated SE, bounded confidence intervals.
- Five exact-reference/Monte Carlo validation cases; raw evidence is in results/.

- Own immutable 2–6-seat Hold’em engine; 26 engine tests and independent traces.
- Full Phase 1 gate: 326 tests, Ruff, strict mypy on Python 3.11 and 3.12.

- Phase 2 own Kuhn/Leduc rules and all four full-tree CFR variants.
- Exact best response: known equilibrium, exhaustive Kuhn pure strategies, ten
  seeded independent policy checks, and matched OpenSpiel solver comparisons.
- All predeclared Phase 2 gates passed at clean e561a28; failed Linear arithmetic
  comparison is retained with diagnosis and unchanged thresholds.
- 338 tests and quality gates on Python 3.11/3.12; raw tables and plots committed.

- Phase 3 sampled CFR with exact uniform/nonuniform expectation checks.
- Own-format atomic PCG64 checkpoints; both samplers resume bit identically.
- Fully funded fixed-limit adapter and public-only information keys.
- 18-run, three-seed multiprocessing pilot at clean 16c8554 with saved metrics,
  memory/runtime records and own checkpoints. Sparse exact-card limit coverage is
  explicitly not a playing-strength result.
- Current/future equity features, suit canonicalization, k-means/W1 k-medians,
  and own card model formats. Abstract keys retain past buckets.
- Disjoint-state 2/4/8-bucket loss experiment at clean 3e917b7; actual mixed
  results, measurement disagreement, occupied counts and limitations recorded.
- Abstract limit checkpoint resumes bit identically with an empty feature cache.
- Bounded abstracted limit training: 12 runs, three seeds/method/model combination,
  36 own checkpoints through 500 iterations at clean 7cbfcad; no strength claim.
- Legal pot-relative raise grids and local nearest/pseudo-harmonic translation
  tested; complete off-tree shadow-policy adapter remains pending.
- Current gate: 374 fast tests, lint and strict types.

Next: no-limit training adapter and bounded compute guards; full off-tree public
shadow-state reconciliation, mapped-policy decoding, and no-limit training.
Phase 3.5 remains gated until Phase 3 has a trained agent and its gate passes.

Standard commands are in AGENTS.md. Every experiment must keep its real revision,
dirty-state flag, config/seeds, hashes, environment, and actual metrics. Historical
reports refer to their recorded revisions; do not rewrite provenance to look clean.
