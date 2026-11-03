# Verified results

`five-card-exhaustive.json` records the complete five-card reference check against
Treys, including raw counts, checks, source revision/dirty status, hashes, environment,
input digest, and runtime. Reproduce with `make validate-five`; see
[the protocol and interpretation](../docs/phase1-five-card.md).

`best-five-validation.json` records the seeded six/seven-card comparison after
complete five-card class calibration. Reproduce with `make validate-best`; see
[the protocol and sampling limits](../docs/phase1-best-five.md). It includes both
requested and actual runs, input digests, exact source/config/entrypoint hashes,
environment, category counts, and timings.

No playing-strength results have been produced yet. Every future published metric
must trace to a rerunnable script and explicit config/seeds or complete enumeration.
Record estimator conventions and uncertainty for statistical experiments.

`results/runs/` is ignored for exploratory runs. Promote small reviewed evidence
to tracked paths deliberately; document storage and retrieval for large artifacts.
