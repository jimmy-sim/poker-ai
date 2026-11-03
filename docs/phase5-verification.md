# Phase 5 acceptance — selected Bayesian and risk extensions

The selected extensions are complete within the declared scope: exact own toy
opponents, conditional bankroll laws and measured own-baseline block resampling.
This milestone does not establish competitive Hold'em strength or profitability.

| Requirement | Actual evidence |
| --- | --- |
| User choice/order | Bayesian modeling and bankroll/risk selected explicitly; implementation followed Phase 4 acceptance. |
| Hidden-card inference | Own-card/public-board/action evidence only; folded and showdown cards marginalized, no opponent card/payoff in learner records. Independent recursive likelihood checks and manual fold likelihood passed. |
| Mixture semantics | Realization-equivalent root mixtures; naive local interpolation counterexample and exact cross-play linearity tests passed. |
| Bounded exploitation | 360 exact checkpoint profiles across two games, both seats, six scenarios and three histories. Every guarded response meets the 0.1 ante-chip degradation allowance versus blueprint security, checked by exact best response. |
| Bayesian experiment | 72,000 censored observations. Held-out prediction improves for included stationary types; misspecified/switching failures remain reported. EV gains relative to blueprint include prior-based exploitation, so they do not isolate learning's incremental EV benefit. |
| Independent posterior replay | Batch log-likelihood sums reproduce online weights within 1.28e-12; all 360 exact metrics rechecked. |
| Conditional risk | 120 fixed synthetic/own-toy cells, 10,000 independent paths/cell, 1,000 steps/path; exact Kelly and finite/eventual ruin controls. Paths/cells are not pooled as independent hands. |
| Dependence stress | In the specified p=.55/full-Kelly binary model, threshold-crossing estimates are 18.11% (IID) and 72.47% (persistence .8). The threshold is 20% of initial wealth, not bankruptcy. |
| Measured-return follow-up | 45 additional cells from all five own baselines; 1,000 original six-hand deck clusters/opponent, 10,000 paths/cell × 1,000 blocks. All five confidence-robust fractions are zero before fees. No positive real-world edge or realistic-rake survival claim. |
| Reproduction | `make analyze-extensions` runs learning, risk, measured-return study, audits, tables and PNG/SVG figures offline. Numeric replay matches all 360 Bayesian rows, 120 original risk cells, own profiles and censored observations against the earlier complete run. The empirical follow-up did not exist in that earlier run. |
| Boundary | No external solver/public benchmark policy or outcome trains the model. Reference-format risk input is rejected. No live API requests in this command or routine tests. |

The final integrated command ran from **clean `159185c`** in **64.51 seconds** on
Apple M4 / Python 3.11.17 / NumPy 2.4.6. Every producer and renderer recorded clean
source provenance. Timings describe this local run only. Raw reports/configs,
model-family definitions, transcript catalog, block-source hashes, exact metrics,
Monte Carlo intervals and artifact hashes are retained in `results/extensions/`.

Local checks: Python 3.11 **496 passed**; Python 3.12 **490 passed, 6 optional
reference skips**. Ruff lint/format and strict mypy passed. All-file hooks pass
at the acceptance commit. Hosted GitHub Actions has not run. Tests do not prove
all numerical/software properties; exact-game scope and modeling assumptions
remain substantive limits. See [methods and six interview answers](phase5-extensions.md).

## View and verify locally

Run from `/Users/jimmysim/Projects/poker-ai`:

```sh
.venv/bin/python -m pytest -q
make check
make analyze-extensions
open results/extensions/bayesian-leduc.png
open results/extensions/bankroll-risk.png
open results/extensions/empirical-bankroll.png
```

`make` commands require uv 0.13.5 on PATH. The first command uses the existing
environment directly. The full extension command took about one minute here;
training is own-only, uses fixed configs/seeds and makes no network game requests.

For recorded-data inspection without rerunning simulations:

```sh
cat results/extensions/opponent-summary.csv
cat results/extensions/empirical-summary.md
.venv/bin/python scripts/audit_opponent_records.py
```

Historical exact numerical comparison (the first directory is an ignored local
run cache, retained on this machine):

```sh
.venv/bin/python scripts/check_extension_reproduction.py \
  --first results/extensions/runs/20261103T075245.608606Z
```

The historical input is not required for fresh reproduction. To compare two
future runs, pass their retained directories using `--first` and `--second`.
Checkpoint metadata/timing differ across runs and are excluded explicitly.

## Stopping point

The user requested a good stopping point. Stop at this verified Phase 5 boundary;
there are no background training/API jobs. Next milestone: Phase 6 packaging
(architecture diagram, concise technical writeup, consolidated interview guide
and final resume bullets). Existing per-phase methods, verified claim drafts and
figures are available; no claim is made that final packaging is already complete.
