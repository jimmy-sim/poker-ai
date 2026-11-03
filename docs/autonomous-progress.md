# Autonomous progress checkpoint

The user authorized continued autonomous work on 2026-11-02, following the roadmap
in order until stopped. The active goal continues through Phase 4; Phase 5 choices
and any C++/Rust core require the already-stated user decisions.

## Current phase: 1

Completed and committed:

- Card IDs, masks, immutable decks, explicit RNGs.
- Five-card evaluator; complete physical-hand comparison against Treys.
- Six/seven-card subset reference and direct rank-mask evaluator.
- Profile first, then paired direct/reference timings on identical fixed inputs.
- Independent direct-evaluator two-million-hand Treys comparison.
- Exact and Monte Carlo heads-up equity, card removal, explicit budgets,
  fractional ties, descriptive variance, estimated SE, bounded confidence intervals.
- Five exact-reference/Monte Carlo validation cases; raw evidence is in results/.

Next: implement the own 2–6-seat no-limit Hold'em engine and test state transitions,
legal betting/reopening, all-ins, side pots, showdown, chip conservation, and private
player observations. Validate behavior against optional PokerKit. Do not advance
to Phase 2 until the full Phase 1 gate passes. Phase 2 introduces toy games/CFR;
Phase 3.5 external strategy-solver validation remains gated after Phase 3 training.

Standard commands are in AGENTS.md. Every experiment must keep its real revision,
dirty-state flag, config/seeds, hashes, environment, and actual metrics. Historical
reports refer to their recorded revisions; do not rewrite provenance to look clean.
