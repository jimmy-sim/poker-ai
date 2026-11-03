# Autonomous progress checkpoint

The user authorized continued autonomous work on 2026-11-02, following the roadmap
in order until stopped. The active goal continues through Phase 4; Phase 5 choices
and any C++/Rust core require the already-stated user decisions.

## Current phase: 2

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

Next: Kuhn and Leduc rules, full-tree CFR variants, exact information-set best
response/exploitability, independent OpenSpiel comparisons, and convergence plots.
See phase1-verification.md for the completed foundation and reference limitations.
Phase 3.5 external strategy-solver validation remains gated after Phase 3 training.

Standard commands are in AGENTS.md. Every experiment must keep its real revision,
dirty-state flag, config/seeds, hashes, environment, and actual metrics. Historical
reports refer to their recorded revisions; do not rewrite provenance to look clean.
