# Reproduction scripts

Keep entry points thin and import implementations from `poker_ai`. Each future
experiment or validation runner must accept an explicit config/seed and save its
inputs, provenance, raw metrics, and runtime.

`validate_five.py` compares the project's five-card evaluator with optional Treys,
saves provenance and raw validation counts, and returns nonzero on failure. Use
`make validate-five` for the exhaustive config; see
[the protocol](../docs/phase1-five-card.md).

`validate_best.py` calibrates all five-card rank classes and compares sampled
six/seven-card ranks with Treys. Use `make validate-best` for the full fixed-seed
config; see [the protocol](../docs/phase1-best-five.md).
