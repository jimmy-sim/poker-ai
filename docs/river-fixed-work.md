# Issue #2 fixed-work comparison

## Session acceptance, before experiment outcomes

This November 4 session resumes the experiments deferred by PR #7. The unchanged
prospective config is `configs/river-integration-study.json`; all four games are
known development evidence. No fresh hold-out or global Hold'em claim follows.

Definition of done for this block:

1. Implement and test a bounded runner for both frozen-policy update error and
   learning at the published total-node thresholds. Include the 2*N initial
   expectation, complete-iteration overshoot, runtime and initial-only rows.
2. Commit the checked runner before the main experiment. Retain every prescribed
   seed/variant/budget and any cap failure. Never select the best seed or prefix.
3. Freeze own policies and hash source/config/lock/game/policy artifacts. Recompute
   exploitability with OpenSpiel's independent native value/best-response code,
   used only after training. Its outputs must never enter an agent.
4. Derive tables and learning/error plots from the saved report. Report all
   performance gates, missing cells, numerical discrepancies and limitations.
5. Pass applicable local checks and hosted CI; update the issue, PR and work log.
   Stop at the resulting evidence/report milestone, even if the hypothesis fails.

The two-hour study cap includes setup, frozen panels, own controls, checkpoint
serialization and metric evaluation. Independent post-training audit/report time
is recorded separately. Frozen panels use unweighted single-target increments;
their MSE*mean visits describes IID frozen-pass averaging, not adaptive training.
The two methods consume different random tapes and iteration counts at equal work.

## Run and inspect

```sh
make study-river-integration      # Full own study, native audit, then report
make report-river-integration    # Replay reviewed policies/audit; no training
uv run --locked pytest -q tests/test_river_study.py tests/test_river_sampling.py
```

The full command writes under ignored `results/runs/river-integration-reproduction/`.
It refuses to overwrite a previous run. Select another preserved directory with
`make study-river-integration RIVER_OUTPUT=results/runs/river-reproduction-2`.
The report command regenerates the reviewed tables/plots from committed raw data.
Both commands return nonzero for a failed candidate performance gate, after
retaining the complete report. Numerical/audit failures stop before publication.

The runner freezes each own policy and saves an own sampler/RNG checkpoint at
each work threshold. Large checkpoints live in ignored `results/river-integration/runs/study/`
for the original local run and under the selected run directory for reproductions;
their SHA256 receipts are in the raw rows. Small frozen policy exports are
published with the report and suffice to replay every reported value and best
response without a checkpoint download. Checkpoints are reproducible, not remote
downloads promised to exist.

## Metric conventions and comparison limits

- **Restricted exploitability:** NashConv/2, in net chips per hand, divided by the
  spot's initial pot. Zero is equilibrium in this finite game, not in full Hold'em.
  The best response chooses one action per information set across hidden worlds.
- **Work:** actual recursive visits, including terminal/chance nodes, plus 2*N
  initialization equivalents. Complete iterations can overshoot a threshold by
  less than 2*N; raw rows retain the actual work. Full CFR+ uses 2*N per iteration
  as a separate diagnostic control, not an equal-work treatment.
- **Frozen error:** squared L2 of the entire sampled regret/averaging increment
  minus its full-tree expectation, including zero increments at unvisited rows.
  Regret error has units chips squared; averaging error has units squared update
  mass. Turn-only regret restricts the sum to unrevealed-river information sets.
  Both opponents and private cards remain sampled. No strict variance dominance
  or convergence theorem is inferred from integration.
- **Cost ratio:** equal-sized seed batches are pooled before dividing integrated
  MSE by ordinary MSE; multiply by the pooled mean-visit ratio for the frozen IID
  averaging efficiency diagnostic. A ratio below one favors integration. Zero
  baseline error gives an unavailable ratio. Per-seed means, within-batch sample
  standard deviations and pass counts remain in the raw panel.
- **Uncertainty:** three fixed seeds provide descriptive min–max ranges, not
  confidence intervals. The same seed labels do not provide matched random tapes;
  target/policy cells also reuse labels. There is no independent fresh-game test.
- **Coverage:** positive average mass includes the exact initial expectation.
  Initial-only row counts and reach-weighted subsequent visits are reported
  separately. The predeclared 95% average-row gate must not be read as 95% later
  exploration.
- **Time:** cumulative per-run times include initialization and preceding
  checkpoint/report overhead. Setup, frozen panels and total study time are
  separate. Quality checks and report development ran concurrently on the host;
  elapsed times are observations under that load, not controlled speed benchmarks.
- **Independent check:** OpenSpiel 2.0.2 native EFG value/best response, Apache-2.0,
  [previously read and recorded](solver_validation.md#solvers-versions-and-licenses),
  evaluates frozen own policies only. It shares our exported mechanics; it checks
  arithmetic/information-set alignment, not an independently implemented engine.
  No reference strategy or value enters the own learner.

Results and three review questions follow after the complete run and native audit.
