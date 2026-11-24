# Prospective exact-turn regret-recency test on two known games

**Issue #4; November 24, 2026 (PST).** This protocol precedes any new
candidate trajectory, policy, score, profile, or decision trace. The
[PR #111 diagnosis](known-wet-residual-diagnosis-result.md) used the
already evaluated `Qs Kd As 3c` turn-start game. Its exact-turn
candidate's final linear average still had `0.804478` chips of turn
best-response gain, 71.38% of it in two seat-one exact rows, even though
[PR #110](known-wet-turn-mechanism-result.md) improved the q8 control at
matched work. PR #110 remains **negative** under its absolute gates.
The candidate's final current/average turn gains differ markedly, but
that contrast does not establish why or imply that a new update helps.

## Question, controls, and scope

Does a fixed asymmetric discount of accumulated **signed regrets** reduce
the wet game's residual turn weakness and whole-policy exploitability at
the same charged work, without materially degrading the already studied
medium/dry exact-turn game? Regret is the running counterfactual advantage
of an action over the current mixed choice; positive accumulated regret
sets the next action probabilities. This is a learning-rule experiment,
not a new representation, more work, or a deployment proposal.

Use exactly two **known, outcome-inspected** turn-start games: the PR #110
medium/wet OOP input `Qs Kd As 3c` with five weighted private combos per
seat, and the PR #108 medium/dry OOP input `As Jc 5d 3h` with two per seat.
Their exact files and SHA-256 hashes are in the
[machine contract](../configs/known-turn-regret-recency.json). The board,
ranges, chance, action menu, evaluator, payoffs, target order, exact acting
turn and river information keys, and 36-chip initial pot stay fixed for
each game. There is no spot or seed search and no unseen/general-strength
claim. The games and candidate mechanism were chosen from prior outcomes;
both are development cases, not untouched validation.

The immutable **control** for each game is the published PR #110/PR #108
`signed_full_exact_turn_river` trajectory, respectively. Reuse its six
saved current/linear-average policies at the first complete 100k, 1m,
and 10m charged-node crossings; verify the pinned own, native, report,
and final-check archives and each control snapshot hash. Do **not**
retrain these completed controls. The **candidate** uses the same exact
representation, full expected target-zero-then-one passes, PCG64(0),
uniform exact initialization, signed linear `t`-weighted regret increments,
linear `t`-weighted opponent-pass/chance-own-reach strategy averaging,
and zero-reach node charges. Full traversal consumes no RNG, so one path
per game is deterministic and gives no seed-based confidence interval.

Only after each target's normal signed update at complete iteration
`t >= 2`, the candidate multiplies that target's **positive or zero**
accumulated legal-action regret by `t^1.5 / (1 + t^1.5)` and its
**negative** regret by `1/2`. Apply this to all owned legal rows after
aggregation, including zero-update rows; leave padding, strategy sums,
and the charged exact uniform initialization unchanged. The positive
and negative factors are the fixed Phase 2 Discounted CFR factors, but
this one-axis adapter **retains the parent linear increment and average**:
it is not a claim to reproduce textbook Discounted CFR. The choice is
prospective, not tuned to the two games' new outcomes. Clipped regret,
batch-one/eight, uniform/suffix average and extra-work outcomes remain
separate, including their failures.

## Fixed work, readouts, and decision rule

Train exactly one new candidate path per game, wet then dry. Save current
and primary linear-average policies at the first complete target-pair
crossing of **100,000, 1,000,000, and 10,000,000 charged nodes**. Require
the candidate's actual work at each crossing to equal its archived
same-game control (`266,262 / 1,065,048 / 10,117,956` wet;
`127,818 / 1,022,544 / 10,012,410` dry). A work mismatch is a
correctness stop, not an adjustable comparison. Save every policy,
regret/average-state guard, RNG state, work overshoot, and partial/failure
event; do not restart an unfavorable scientific path.

Primary lower-is-better metric is exact restricted-game NashConv/2 in
acting-seat chips divided by that game's **36-chip initial pot** at the
final linear average. Report every candidate/control policy and paired
delta at all labels and both readouts; each seat's best-response gain,
turn/river additive contribution, whole and post-initial-river positive
average reach coverage, recall violations, policy bytes, runtime,
hardware, and peak worker RSS. Preserve the exact control scores and
native audits. Report no confidence interval for the deterministic two
known cases; the two games are related development evidence, not two
independent samples or a population estimate.

For the wet game, inspect the **same 20 fixed exact rows** from PR #111:
turn `1611, 4041, 7506, 1618, 4824, 1619, 40, 0, 5838, 1596` and
river `1679, 1697, 1821, 1839, 2, 2361, 1152, 7974, 7507, 1689`.
For dry, inspect the already diagnosed `2445, 30, 1`. Do not replace a
zero-reach or unfavorable row. At all checkpoints and readouts show board,
private cards, legal concrete actions, saved probabilities,
chance-times-opponent counterfactual reach, full saved-prefix reach,
optimized-continuation alternative-action values, and additive gain.
Track the wet top-two and full turn/river gains as mechanism readouts,
not extra optimized acceptance gates. Local values assume each saved
opponent and optimized reply continuation; they are not causal action
swaps or universal poker advice.

Apply the existing absolute gates to **both** new final averages:
exploitability at most **0.01 initial pots**, one-path worst at most
**0.025**, whole coverage at least **0.95**, and zero recall violations.
**Positive on these two known games** additionally requires wet
candidate-minus-archived-control at most **−0.001 pots** and dry
candidate-minus-control at most **+0.001 pots**. **Negative** means an
absolute gate fails on either game, wet worsens by more than **+0.001**,
or dry worsens by more than **+0.001**. Every other complete outcome is
**inconclusive**. Publish paired deltas even if an absolute gate fails.
No classification promotes a default or revises PR #108/#110's results.

## Qualification, conservative admission, and publication

The old candidate full paths took 47.429 wet and 13.601 dry seconds on
the recorded Mac; their combined ~61.03 path-seconds are planning context.
Allowing threefold time gives a rough `T ≈ 183.09` and
`2 × (2 × T + 600) ≈ 1,932.36 < 7,200` seconds, **not admission**.
The extra vector update, archive IO, hardware, and scoring may change
runtime. There is no paid compute or ceiling increase.

Implement the adapter and all new orchestration in new modules only.
Before known-game training, pass independent tiny-game update arithmetic,
same-initialization/zero-discount equivalence, ownership/padding,
work-identity, replay, failure-retention and historical-pin tests.
Complete exact-source local base and optional Python 3.11/3.12 suites,
all-file hooks and both hosted jobs; publish and GitHub-byte-verify the
tested source receipt. Publish/verify one fictional own proof under
**180 seconds**. Then profile each candidate path **three times** to its
first complete **1m** crossing, six fixed paths under a **900-second**
whole cap including construction, scoring, capture and replay. Use two
workers, wet in worker zero and dry in worker one. For each game take
the maximum of its three complete `whole_path_seconds × 10m /
actual_final_work` estimates; let `T` be the larger of those two maxima.
Publish and byte-verify every repeat before a **separate data-only
admission** requiring strictly `2 × (2 × T + 600) < 7,200` seconds.
Failure or equality blocks the 10m study; do not pick a faster repeat.

At most one admitted two-path own study has a **7,200-second whole-process
cap**, with **120 seconds reserved for failure save**. Publish and verify
all complete/partial own policies, state guards, scores and logs **before**
any reference work. Then audit all **12 new candidate scalar policies**
against comparison-only OpenSpiel **2.0.2**, installed Apache-2.0 license
SHA-256 `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`,
within **1e−9 chips** and a **900-second whole cap**. Reuse and verify
the already published independent control audits; do not import any
reference strategy into training. Publish/verify the new native audit,
then build the fixed comparison and decision report from published bytes.
Complete final exact-report local/optional/hooks/hosted qualification,
retain failures, solo review and history-preserving merge if eligible.

A failed mathematical, source, historical-pin, publication, compute,
native-scalar or time gate stops measurement with complete or partial
evidence. A failed poker-strength or coverage gate yields the frozen
negative classification after required audits and ends this experiment.
Do not extend work, redraw, change parameters,
weaken thresholds, reclassify old failures or retry scientific outcomes
to obtain a positive result. A software defect may be fixed with retained
failure evidence and full requalification. Human hands-on time and
personal learning were not reported.
