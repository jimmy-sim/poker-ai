# Separating training rules before attributing river weakness

Issue [#4](https://github.com/jimmy-sim/poker-ai/issues/4), November 8, 2026.
Codex-assisted work; personal hands-on time not recorded.

## Current milestone and stopping point

The saved-policy swaps locate the large change in river continuation. They do
not identify the training cause. This step defines a common own training harness,
checks its update mathematics exactly, and audits the original work receipts.
Stop after checked code, rerunnable correctness evidence, CI and documentation.
Do **not** run or claim a new postflop learning comparison in this milestone.

The [fixed config](../configs/training-isolation.json) pins the motivating
evidence and preregisters the later comparison before new training outcomes.
Earlier learning failures and defaults remain. Historical source and policies
remain unchanged.

## Differences that need controls

| Choice | Saved full control | Saved sampled control |
|---|---|---|
| Traversal | Full tree | External sampling |
| Regret accumulation | Unit-weighted, clipped after each target pass | Raw iteration-weighted, signed |
| Average time weight | Iteration | Iteration |
| Averaging moment | Own target pass | Other player's target pass |
| Averaging history mass | Own reach, without chance | Expected chance × own reach |
| Initialization | Cold, alternating first iteration | One simultaneous exact uniform iteration |
| Budget | 4096 full iterations | First whole iteration crossing 10 million visits |
| Arithmetic | Explicit fused full backend | NumPy sampled operations |

“Regret” is the accumulated evidence that an action would have done better.
Clipping deletes negative accumulated evidence. Regret weighting and strategy
averaging are separate choices; both old trainers use linear strategy averaging,
but they collect it at different moments and with different history masses.
Equal information groups do not make these procedures identical.

## Common equations

For a frozen joint policy and target player i, a full expected pass computes

`delta_i(I,a) = sum[h in I] chance(h) * reach_other(h) * (v_i(h,a)-v_i(h))`.

To match the external sampler's simple averaging, the same pass accumulates for
the **other** player j

`mass_j(I,a) = sum[h in I] chance(h) * reach_j(h) * sigma_j(I,a)`.

One policy is frozen throughout a pass. Apply all shared-information increments
before optional clipping; then refresh policy for the next player. Iteration t
has passes 0 then 1. Regret weight and average weight independently equal 1 or t.
No full-solver output or reference action enters the sampled trainer.

The common warm start is a simultaneous expected iteration under uniform play:
both passes read that original uniform policy, then commit their updates. Charge
2N node visits. Subsequent full and external iterations alternate normally.
The full-only bridge can instead collect own-pass averages and omit chance mass,
so historical semantics can be checked without changing frozen old code.

Unbiased **raw frozen-pass** increments do not imply identical training paths.
Clipping and regret matching are nonlinear: `E[max(0,R+estimate)]` generally
differs from `max(0,R+E[estimate])`. An exact selector enumeration on an explicitly
labeled nonuniform-chance Kuhn software fixture checks both expectations and
illustrates that distinction. It is not a Hold'em playing-strength result.

## Acceptance before further learning

- Full expected regrets and simple-average increments agree with exhaustive
  external-selector expectations for both targets, biased positive policies and
  zero-support policies; mass sums to one. Use tolerance 1e-12.
- Cold own-pass/history-mass/unit-regret/clipped/linear-average mode matches the
  existing NumPy full CFR+ control. Raw linear signed mode has the documented
  positive-scale equivalence to the existing full linear recurrence; require
  policy tolerance, not bit identity with fused arithmetic.
- External signed mode matches the existing sampled trainer with identical RNG,
  weights and initialization; count every visit. Regret and average weights can
  vary independently. Shared rows aggregate before clipping.
- All 16 rule combinations preserve legal normalized policies, target ownership,
  explicit RNG reproducibility and work accounting. Unsupported sampled averaging
  modes fail rather than pretending to estimate a different expectation.
- Validate config, pinned inputs, complete grids and replay. Do not permit a
  partial receipt, changed source or a correctness result labeled as learning.
- Recompute all historical work rows from pinned reports. Count exact
  initialization and whole-iteration overshoot; retain all controls and seeds.
- Pass lint, format, strict typing, applicable tests and hosted CI; update the
  plain-English journal and work log. No new research training before this gate.

## Later experiment, fixed before outcomes

Use two known games, exact and range-mass representations, and a 2×2×2×2 grid:
traversal (full/external), regret rule (signed/clipped), regret time weight
(uniform/linear), and average time weight (uniform/linear). All other conventions
are common. Eight full cells per game/representation are deterministic; eight
external cells use all three fixed seeds. This gives 32 full and 96 sampled runs.
Work checkpoints are 100k, 1m and 10m visits; iteration checkpoints 16, 64 and 128
are a separate view of the same trajectories. Neither is called the sole fair
comparison. Publish actual visits, iterations, overshoot and runtime.

The full-only bridge first work-matches the old conventions, adds the common warm
start, includes chance mass in own-pass averaging, then changes to other-pass
averaging. Use all four predefined stages, not just a favorable endpoint.
This ordered bridge is path-dependent; it is not a unique allocation of cause.
The matched common factorial changes one rule at a time and reports interactions.
Common RNG seeds are reproducibility aids; changed policies consume different
draws, so they do not guarantee paired identical random events.

Record total exact exploitability, within-partition and extra-information gains,
and river-only gain with an exact prefix, plus coverage and cost. Independently
audit every published policy's values/replies with the already licensed pinned
OpenSpiel reference, comparison only. Export no reference actions. A 7200-second
own-stage cap includes setup and scoring; retain failed/partial evidence without
budget extensions or changing seeds. No automatic remedy or admission follows.
The current milestone does not implement/run that study orchestrator or claim
that the proposed workload fits its cap; profile it before committing to a run.

Finite results could identify effects **in these two games under the fixed
controls**, not a universal reason sampling is weaker or a global Hold'em edge.
Fused/nonfused rounding and changed initialization/averaging must be reported as
bridge differences, not silently attributed to sampling. If correctness fails,
debug it before training.
