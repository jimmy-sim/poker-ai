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

Results, actual commands, and three review questions will be added after the run.
