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
bit-exact padded restoration. Store each own reply profile's fingerprint; rebuild
it from the saved own policy and frozen own scorer for replay/native comparison.
This avoids retaining six redundant full reply arrays per checkpoint. Their
fingerprints and root values must match before comparison. Stream the final compressed JSONL archive and native
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
Matching seed labels couples RNG initial states, not identical sampled histories:
changed policies can change branch lengths and later random-draw consumption.
These are conditional finite-seed diagnostics, not population causal estimates.
No population confidence intervals from three algorithm seeds. Work/iteration
results remain separate. Analyze four full-only bridge points separately, with
last point referencing the common endpoint instead of duplicating it. The warm
uniform iteration always uses common chance/own-reach, opponent-pass averaging,
even when later bridge iterations use history mass. Ordered bridge differences
can interact with that retained initial mass; they are not a unique attribution
of cause. Consistent static per-information-group scaling can cancel after
normalization, so do not infer a universal chance-weight effect from one bridge.

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

## Commands and solo review before admission

Fresh reproduction, after this source's committed correctness/admission receipts
exist (requires the locked research and solver-validation extras):

```sh
make compare-controlled-learning
```

This uses `results/runs/controlled-learning-reproduction/`, which must be fresh.
An existing receipt or partial archive is retained, never silently overwritten.
Use `CONTROLLED_RUN_DIR=results/runs/another-name` for a separately labeled rerun.
The recorded study uses explicit `--output results/controlled-learning/own.json`,
then publishes own evidence before the separate native audit command. Reproduction
can keep its immutable own outputs ignored between stages; no reference strategy
is loaded into training. The recorded training runtime is Python 3.11 / locked
NumPy 2.4.6; software and saved-output checks also run on Python 3.12. Exact prefix
fingerprints can reject a different numerical runtime rather than silently claim
bit-identical trajectories. Recorded CPU/wall times and PNG bytes vary by machine.

Read-only review in the user's existing environment, without `uv` on PATH:

```sh
.venv/bin/python scripts/report_controlled_learning.py --no-plots
```

This replays all own policies on three processes, verifies a present native audit,
and regenerates the numerical tables in an ignored folder. Omitting `--no-plots`
also makes all eight figures when Matplotlib is installed. It does not retrain.
Before learning is admitted, this command has no completed study to read.

Solo self-review keeps the exact work units and first crossings, reuses the
frozen combined prefix lookup for both backends, checks immutable config/source
chains, rejects typed/nonfinite/partial grids, and retains worker errors/files.
Own reply arrays are regenerated and fingerprint-checked with the own scorer;
reference actions and policy export remain blocked by tests. Native code has a
separate namespace and returns scalar comparisons. Each worker replays assigned
checkpoints before its completion receipt; report IO is charged before own-stage
completion. No independent human reviewer or measured RAM claim is implied.

The implementation checkpoint has no new Hold'em learning result. Its tests use
toy worlds, old own policies and visibly labeled synthetic figures. A prefix-
inventory test caught a lookup that initially omitted the full backend's rows;
using the frozen combined lookup fixes orchestration without changing learning.

## Checked implementation evidence, before Hold'em learning

Protocol `8b8256a`, code `87fb4bce247083df1f9cced6fa26052df94dc6ae`.
58 new fast checks pass both Python versions and both base environments. Full
all-extras: 1190 passed / 9 slow excluded each Python 3.11.17 / 3.12.15 (265.87 /
255.54s). Complete base make check: 1157 passed / 24 optional skips / 9 slow
excluded each (218.83 / 209.18s); final focused checks after validation tightening
and clean non-incremental strict typing pass both base versions (293 files).
Ruff checks 373 files and commit hooks pass. Two final-source native/render
integrations pass 39.74 / 38.26s; no new poker training or reference policy export.
Earlier integration runs 34.35 / 37.24s remain test history, not timing forecasts.

Clean published code produces the source-bound toy receipt in 0.539277s: 32
trajectories, 136 physical policy round trips and hand-computed first through
fourth-order contrasts. Old selector correctness also replays. No new postflop
training has occurred. Hosted CI `42522375101` passed both Python jobs on checked source `87fb4bc`.
Formal source-bound admission is recorded in `results/controlled-learning/admission.json`. Source hashes bind code/config/lock/entrypoints;
actual learning starts only after these checks and the admission commit are published.

## Completed own stage; independent audit still pending

Clean published `70fe2f27557af8e72c1039c941a639121122cee1` completes all 140 cells
and 840 physical/logical checkpoints in **2161.351771s** (36.02 minutes), below
7200s. Batch 2148.667566s includes all three worker preparation/training/scoring/
replay and collection. Every serial prefix check passes; workers save/replay
282 / 282 / 276 snapshots with maximum own replay error **zero**, exit codes zero.
Replay wall inside workers 62.285469 / 64.062871 / 62.598497s. Parent / reaped-child
CPU 3.489438 / 6446.210000s; these are process costs, not personal work hours.

The complete compact archive is 8,725,389 bytes, SHA-256
`8a0e2494584763365e2dd607be16992984f553b32397d7d3c92f19ae21e9e054`.
Its 840 owned policies and own-reply fingerprints remain available for replay.
All raw checkpoint rows, 1536 factor means, 4512 paired conditional/factorial
metric rows, 96 bridge rows, endpoint tables and eight figures are retained.
These counts include four metrics, both axes and every checkpoint/group; they
are not 4512 independent experiments. Plot filenames identify the chip metric;
the plotted values are converted to **percent initial pot**, as labeled on axes.
The actual extra-information/work plot was inspected for layout. Temporary
Matplotlib font-cache startup is charged to own wall time; no RAM claim is made.

Header/grid/prefix/admission/source checks pass. The recorded own receipts,
archive and reports are published before the separate comparison-only native
stage. Chip outcomes and training-cause interpretation await that complete
independent audit. Original failed learning limits/defaults remain unchanged.
