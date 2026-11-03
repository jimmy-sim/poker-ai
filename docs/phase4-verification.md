# Phase 4 acceptance — bounded evaluation

The evaluation milestone is complete. This establishes a tested evaluation path,
not a positive playing-strength result.

- Local fixed-policy duplicate study: 36,000 hands, six opponents, three own
  policies, 1,000 independent shared-deck clusters per comparison. All raw records,
  deck hashes, settlements and pooled statistics passed the offline audit.
- Confidence intervals, mbb/hand units and the predeclared six-test
  Bonferroni–Hoeffding criterion are reported. No positive advantage passed that
  primary criterion. Unfavorable TAG/equity point estimates remain published.
- Duplicate-deal variance reduction replaces AIVAT. Covariance-omitted ratios are
  descriptive; this is not an independent unpaired experiment or AIVAT result.
- OpenSpiel's small seeded Python ISMCTS baseline uses public observations and
  explicit hidden-world resampling. Independent native traces matched 2,824
  actions and 1,000 hand payouts. OpenSpiel/ACPC licenses and scope are documented.
- The permitted public Slumbot pilot completed its predeclared 100 hands at
  200bb: no missing or replacement hands, no retries, 255 paced requests. Source
  was clean `406b3de`; all 100 settlements/statistics replay offline. Net loss and
  wide intervals remain published. Off-grid approximation is measured explicitly.
- Server deal seeds and strategy version are opaque. Recorded public statistics
  replay; identical live outcomes cannot be reproduced. This exception is stated,
  and these outcomes do not enter the reproducible open-source solver comparison.
- Reference/benchmark outputs remain comparison-only. There is no adaptation or
  training from OpenSpiel or Slumbot policies/outcomes.

Python 3.11: **453 tests passed**, Ruff formatting/lint and strict mypy passed
(98 files). Python 3.12: **447 passed, 6 optional-reference skips**, with the same quality
checks. All-file commit hooks passed. Hosted CI
has not run. The detailed methods, generated local/public summaries and three
interview answers are in [phase4-evaluation.md](phase4-evaluation.md).

```sh
make check
make evaluate-agents    # new fixed-seed local match run and offline audit/report
make report-evaluation # existing local raw-record audit/report; no matches
uv run --locked python scripts/render_public_pilot.py \
  --report results/slumbot/public-pilots/pilot-20261103T072514.940829Z.json
```

`make benchmark-slumbot` starts a new live public simulation session and cannot
recreate the recorded deals. Routine tests/reporting never make game requests.
Phase 5 follows with the user's selected Bayesian modeling and bankroll/risk pair.
