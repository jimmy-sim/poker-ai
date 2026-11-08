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

## Implementation and verification

`controlled_training.py` implements the common updater without modifying the
historical trainers. Its dense arrays and full normalization are diagnostic
conveniences; they do not establish sampled efficiency or global scalability.
It supports independent weights, shared-row aggregation before clipping, a
charged simultaneous initialization and complete-iteration work checkpoints.
`training_isolation.py` exhaustively enumerates adaptive selector tapes and
checks the pinned historical receipts. No native strategy is involved here.

The focused tests also compare the actual range-mass adapter against the old
sampled updater in **both known games** for a short, fixed software regression
trace. That is not a learning experiment or strength measurement. The old NumPy
full CFR+ and linear controls are checked separately on the nonuniform fixture.
Fused historical trajectories are not claimed bit-identical to the new backend.

The chance-mass convention deserves care: with perfect recall, own realization
reach is constant within an information row. Static chance masses can then just
rescale that row and cancel in its normalized average, if used consistently
across iterations. A test verifies this null effect on the fixture. Averaging
on a different player's pass can still change the stored average because the
joint policy changes between passes. A warm start with separately specified
mass can also break the across-iteration rescaling argument. We report these
conventions without presuming each changes poker strength.

Focused checks: 20 tests pass. Local `make check` passes **964 all-extras tests**
on Python 3.11.17 and 3.12.15; base-only **931 passed / 24 optional skips**.
Ruff lint/format, strict mypy (243 files) and hooks pass. Both hosted jobs pass
for checked source `b8ed1d4a3c2a7ad9c04d4e10f8d40d0b1f6dbcb7` in
[code CI 42466613135](https://github.com/jimmy-sim/poker-ai/actions/runs/42466613135)
before the reviewed receipt was recorded.

## Recorded correctness and work evidence

The [receipt](../results/training-isolation/correctness.json) was recorded from
clean `b8ed1d4` after code CI passed. All four cases, **54 joint selector tapes**,
and **30 historical work rows** pass. Software-audit runtime is **0.042211s**;
this is not training or human work time. Replay passes on Python 3.11 and 3.12.

| Fixture policy | Target | Selector tapes | Max raw regret error | Max average error | E[clip] − clip(E), max absolute |
|---|---:|---:|---:|---:|---:|
| Positive | 0 | 24 | 8.326673e-17 | 5.551115e-17 | 0.05208333 |
| Positive | 1 | 18 | 2.775558e-17 | 0 | 0.07142857 |
| Zero support | 0 | 6 | 0 | 0 | 0 |
| Zero support | 1 | 6 | 0 | 0 | 0 |

These utility discrepancies use **fixture chips**, not Hold'em EV, and the
clipping comparison starts from zero regret. Probability masses sum to one
within 1e-12. This verifies frozen-pass estimators and demonstrates nonlinearity;
it does not claim the expected nonlinear training trajectory equals full CFR.

All five controls and every historical seed are retained in the receipt.
The motivating range-mass endpoints show the work mismatch clearly:

| Known game | Full visits at 4096 iterations | Sampled visits across 3 seeds | Full / sampled work, approximately |
|---|---:|---:|---:|
| Low OOP | 24,567,808 | 10,000,000–10,000,009 | 2.45678 |
| Medium OOP | 174,514,176 | 10,000,000–10,000,028 | 17.4514 |

The medium sampled trajectories complete 298,022–315,528 iterations, versus
4096 full iterations. Neither matched work nor matched iterations can be inferred
from those old endpoints. Initialization and each whole-iteration overshoot are
checked explicitly. Visits are the declared work proxy, not equal FLOPs or wall
time. This audit measures the mismatch, **not how much of the river weakness it
caused**. The later controlled learning experiment remains not run. No new
postflop policy, strength number, remedy/default or admission change is produced.

## Commands

After publishing checked source, `make check-training-isolation` creates a new
receipt in ignored `results/runs/training-isolation/`. Existing outputs fail
rather than being overwritten. `make report-training-isolation` replays the
reviewed receipt after publication. Neither trains a postflop agent.

## Three questions to explain this step

1. **Why was the earlier comparison not a sampling experiment?** It changed
   clipping, regret weights, averaging, initialization, work and arithmetic too.
   Fixed card groups alone do not control those differences.
2. **Does an unbiased sampled update reproduce full CFR?** Its raw frozen-pass
   expectation can match. Nonlinear clipping and normalization, and refreshing
   the next pass's policy, can still produce different trajectories. We check
   raw expectations, not equality of expected learned strategies.
3. **What would a causal result mean?** A predefined one-rule contrast under
   common conventions could establish a finite effect in these known games at
   the stated budget. Interactions, different cost axes and solver/abstraction
   limits still prevent a universal or competitive Hold'em claim.
