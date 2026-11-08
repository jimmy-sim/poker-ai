# Run the original controlled-learning comparison

Issue [#4](https://github.com/jimmy-sim/poker-ai/issues/4), November 8, 2026.
Depends on PR #27; Codex-assisted, personal hands-on time not recorded.

## Fixed question and admission before new outcomes

Investigate training differences behind the river vulnerability while preserving
the original information groups. The original configs/training-isolation.json
comparison stays frozen: two known games × exact/range-mass × full/external ×
signed/clipped regrets × uniform/linear regret weight × uniform/linear average
weight, three fixed external seeds. Deterministic full controls run once, plus
three unique bridge cells per game/encoding; the fourth bridge endpoint is the
identical common cell. This is 140 runs, not independent full-seed replications.

The completed cost check forecasts 4674.496s guarded own / 543.838s native, under
7200 / 3600 caps. Before NEW postflop learning: publish checked runner/config,
source-bound toy correctness receipt, complete relevant local checks and both
hosted CI jobs on the checked source. Record that admission explicitly. No new
learning starts merely because a timing estimate fits. No C++/Rust core or new
solver dependency. Existing updater/sampler/normalization/cached nodes and old
evidence stay frozen. No reference output enters strategy construction.

## Runtime, storage and completeness

Three spawned processes, original cell order index modulo three, isolated trainer
and PCG64 RNG per cell, requested one native-library thread per worker. Same
simultaneous exact uniform iteration charged 2N for warm/common cells, same cold
bridge, pass 0 then 1 with refresh between and policy frozen within each pass.
Both full and external visits include terminal/chance/decision nodes. Work labels
100k/1m/10m save the first COMPLETE crossing, including previous work and overshoot.
Iteration labels 16/64/128 save those exact points. Keep axes separate and coalesce
simultaneous labels into one snapshot with all labels retained. Expected 840 logical
checkpoint rows; physical snapshots can be fewer without inventing observations.

Use the checked observer/scorer. Record raw-state/RNG/work fingerprints, average
policy, exact/within/extra/river metrics, signs, coverage definitions, timings and
L2 regret norm. Norms depend on regret weighting; they are not strength rankings.
Warm average coverage can be one before sampled river visits. Callback observation
must not change arrays, RNG, keys or work; verify against uninterrupted toy runs
and the pinned short-prefix serial endpoint checks before the large comparison.

Write atomic own-v1 compact legal-action snapshots, with menus/metadata/hashes and
bit-exact padded restoration. Stream the final compressed JSONL archive and native
reader one record at a time; never decode 840 strategies at once. Each worker
replays its saved policies/metrics without training before it completes, using the
same fixed partition as forecast. Report/table/plot IO and validation belong to
7200s own cap. Native stage gets separate 3600s, all published own snapshots checked
against OpenSpiel 2.0.2 roots and achieved own profiles at 1e-9. Record its previously
read Apache-2.0 license hash and version. Publish own outputs before native timing
for this public study. Reproduction may keep fresh outputs ignored but must keep
source clean, bind immutable own hashes before native evaluation, and train only
before comparison. No reference actions, strategy export or reference warm start.

Retain all cases, checkpoints and failures. Deadline/worker failure records an
incomplete result and surviving scratch files; do not select completed favorable
arms, silently restart a budget or publish an incomplete grid as a full study.
Measured runtime, source/lock/hardware and actual native errors accompany output.

## Contrasts fixed before outcomes

For each game/encoding/checkpoint axis and target, publish all raw cell values and
all external seeds, then arithmetic means. Convert chips to percent initial pot
with the same pot in each fixed game. Report 32 conditional one-factor differences:
second listed level minus first, holding all other factors fixed. Also report all
15 nonempty averaged factorial differences across four binary factors: for a
subset of k factors, 2^k times mean(y × product of their ±1 level signs). These are
averaged k-way differences, not regression significance. Test normalization with
hand-computed synthetic factors before outcomes. Preserve paired seed differences
and interactions; full controls reused across comparisons are not new samples.
No population confidence intervals from three algorithm seeds. Work/iteration
results remain separate. Analyze four full-only bridge points separately, with
last point referencing the common endpoint instead of duplicating it.

## Definition of done and limits

Tested runner/correctness/admission gates, complete own and native receipts or an
honestly retained incomplete outcome, source-bound streaming replay, all raw rows,
contrast/bridge tables and eight primary-metric/axis figures, CI and journal/work
log updates. A rerun command reproduces numerical results from fixed inputs;
recorded timing itself varies. Three interview Q&As explain the final findings.
No best-arm/default/fresh/global admission from this diagnostic alone. External
clipped regrets are an experimental variant; nonlinear clipping does not make an
unbiased estimator of a full clipped trajectory. New full NumPy controls also do
not retroactively reproduce the old fused arithmetic. Shared exported mechanics,
small known ranges, source-policy timing estimates and three fixed seeds limit
what causal contrasts say about the broader Hold'em agent.
