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

At the implementation checkpoint there was no new Hold'em learning result. Its tests used
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
fourth-order contrasts. Old selector correctness also replays. At that point no
new postflop training had occurred. Hosted CI `42522375101` passed both Python jobs on checked source `87fb4bc`.
Formal source-bound admission is recorded in `results/controlled-learning/admission.json`. Source hashes bind code/config/lock/entrypoints;
actual learning starts only after these checks and the admission commit are published.

## Completed own stage, published before the independent audit

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
stage. The later independent audit and interpretation follow below. Original failed
learning limits/defaults remain unchanged.

## Independent audit and numerical replay

Own evidence published at `3bd6858ddc2cc9a4346296b6fb7a26a4f74f6974` before
native evaluation. All **840 checkpoints** pass OpenSpiel 2.0.2 comparison-only
EV, exact/restricted response-root and achieved own-reply/hybrid checks.
Maximum error **1.7053025658242404e-13 chips**, below fixed **1e-9**. Native wall
**92.193960s** (<3600); parent / reaped-child CPU 0.222218 / 270.450000s. The
native stage includes streaming own-policy replay. Its installed Apache-2.0
license matches the previously read hash. No reference strategy export/training
or reference output in the learner. Shared own mechanics/export remain a limit
on independence: this is a separate value/BR implementation, not an independent
validation of every Hold'em rule.

Base Python 3.12 / NumPy 2.5.4 replays all 840 owned policies with zero score/reply
error in 64.920820s, validates the archived native comparisons without importing
an installed native runtime, and regenerates all five numerical report files
byte-for-byte: four CSVs and `tables.md`. The summary's figure inventory depends
on `--no-plots`; recorded times and PNG bytes are not claimed to reproduce.

## Findings: several conditional effects, no single universal cause

The focal case remains the previously failing **medium range-mass** game, not a
case selected for a favorable result. Pot is 36 chips. Every number below comes
from the retained `factor-means.csv`, `contrasts.csv`, `bridges.csv` or raw
`checkpoints.csv`; the linked report command regenerates them. All other games,
representations, seeds, checkpoints and contrasts remain published too.

At the **10m total-node-work label**, hold regret weights linear and change only
clipping and strategy-average time weights. Entries are arithmetic means of all
three external seeds; units are **percent initial pot**. Lower total is better.

| Strategy-average weight | Regret rule | Exact exploitability | Within partition | Extra exact information | River-only diagnostic |
|---|---|---:|---:|---:|---:|
| linear | signed | 4.354032 | 0.243207 | 4.110824 | 4.856795 |
| linear | clipped | 2.501852 | 1.811454 | 0.690398 | 1.764998 |
| uniform | signed | 2.664089 | 0.372605 | 2.291484 | 4.052257 |
| uniform | clipped | 3.525759 | 2.918434 | 0.607325 | 1.404964 |

Clipping with linear averaging reduces extra-information value by **3.420426
percentage points**, but increases within-partition gain by **1.568247 points**.
Total falls **1.852179 points**, with paired total changes -1.709274 / -3.365672 /
-0.481592 points in the three declared seeds. With uniform averaging, clipping
instead **raises** total by **0.861670 points**, paired +0.888905 / +0.174850 /
+1.521255. This sign reversal is a measured interaction between clipping and
averaging in these finite runs. It does not establish a universal advantage for
either convention, a confidence interval, or the cause of all remaining error.
Within + extra equals exact exploitability. River-only values use different
hybrid prefixes and must **not** be added to that identity; they can exceed total.

Matched work does not remove every traversal difference. Across all eight common
rule combinations in this focal case, sampled-minus-full mean total is positive
(1.059418–3.928729 points); its average across combinations is **2.170219 points**.
For the same clipped/linear/linear rules shown above, full total is **0.050297%**
versus sampled **2.501852%**. Its full extra-information value is **0.000825%**,
which further demonstrates that the representation's vulnerability is
strategy/opponent-dependent, rather than a fixed 4.11% abstraction floor. This
is a conditional finite-budget traversal result, not proof that the sampler is
buggy or a post-hoc best-arm/default selection.

The work labels are first complete crossings, not identical visit counts: full
medium cells finish at **10,012,410 visits / iteration 235**. The signed/linear/
linear sampled seeds finish at **10,000,021 / 10,000,028 / 10,000,000 visits**, with
**315,528 / 298,022 / 305,206 iterations**. At iteration 128 the full control has
**5,453,568 visits**, versus **47,196 / 47,132 / 47,012** for those sampled seeds.
An iteration match therefore answers a different compute question. Warm average
coverage is 100% even then; sampled river-key read coverage is only
25.7021 / 28.3272 / 24.6642%. Average mass is not proof of sampled exposure.

At matched 10m work, the ordered full bridge totals are **0.386078 / 0.801019 /
0.802919 / 0.803119% pot** for cold-target-history, warm-target-history,
warm-target-chance, common-warm-opponent-chance. These show a larger finite
initialization difference than the later two averaging changes along this one
path. They are not a unique allocation of cause. Initialization always retains
its common chance-weighted mass, so the history-mass bridge mixes conventions
for its first iteration; consistent static scaling cancellation is not refuted.

## What this changes and what it does not

The original compute barrier is overcome, and the original controlled comparison
is completed and audited. The differences cannot all be attributed to the old
unequal work budget: material rule, averaging interaction and traversal effects
remain in the matched-work grid. The evidence does **not** identify one repair
that has passed a fresh-game/seed accuracy gate. The earlier sampled performance
failure remains; no recipe is selected or deployed and the global agent does
not inherit these separately trained tiny-range policies.

Next useful diagnosis: explain where the increased within-partition response
gain occurs when clipping reduces the finer-information gap, and why changing
the time weighting reverses the total effect. Use fixed saved policies and own
response traces before proposing a new remedy. Do not infer that visiting a key
or changing a norm caused an EV improvement. All policy design/training stays
independent of the reference solver's outputs.

## Interview questions and verified claim drafts

1. **What did you learn after matching compute?** The medium range-mass sampling
   gap remains across all eight rule combinations at the 10m label, with an
   averaged sampled-minus-full total of 2.170219 percentage points. Clipping and
   averaging interact; the old budget mismatch alone is not an explanation.
2. **Why not simply enable clipping?** With linear regret weights, clipping lowers
   sampled total from 4.354032% to 2.501852% under linear averaging, but raises it
   from 2.664089% to 3.525759% under uniform averaging. It can move error between
   within-partition and extra-information components. None is a global win rate
   or an admitted strongest recipe.
3. **How are the numbers checked?** A preregistered 140-cell/840-checkpoint runner
   preserves source, seeds, work, all outcomes and exact prefixes. Own replay is
   zero; independent native value/BR checks differ by at most 1.705303e-13 chips.
   All five numerical reports regenerate byte-identically in base Python 3.12.
   Shared exported game mechanics and two known tiny-range games limit the claim.

Verified draft: “Completed a preregistered 140-run poker training comparison with
840 source-bound strategy checkpoints, zero own replay error and independent
value/best-response agreement within 1.71e-13 chips.” This describes the checked
experiment, not personal hours, unaided authorship or competitive playing strength.
