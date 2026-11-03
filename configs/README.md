# Experiment configurations

Add versioned configurations alongside experiment runners in the relevant phase.
Include explicit seed lists, game/rule conventions, hyperparameters, stopping
criteria, and evaluation budgets. Five-card validation configs:

- `five-card-smoke.json`: fixed-seed random sample for a quick reference check.
- `five-card-exhaustive.json`: complete lexicographic enumeration; no RNG.

See [the protocol](../docs/phase1-five-card.md).
