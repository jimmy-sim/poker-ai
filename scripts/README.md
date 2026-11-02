# Reproduction scripts

Keep entry points thin and import implementations from `poker_ai`. Each future
experiment or validation runner must accept an explicit config/seed and save its
inputs, provenance, raw metrics, and runtime. No experiment runner exists yet.
