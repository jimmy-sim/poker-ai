# Measure independent training cells across processes

Issue [#4](https://github.com/jimmy-sim/poker-ai/issues/4), November 8, 2026.
Depends on PR #25; Codex-assisted, personal hands-on time not recorded.

## Fixed question and acceptance criteria before measurements

The serial immutable-node profile passes exact parity but its guarded training
forecast is 12,432.056 seconds, above the unchanged 7,200-second own-stage cap.
Measure 1, 2 and 3 CPU processes on this machine. Every cell has an independent
trainer and RNG; do not split a single training trajectory across processes or
alter update order, seeds, rules, work checkpoints or the 140-cell comparison.
This is operating-system multiprocessing, with no additional AI agents.

Use the frozen cached-node external trainer and unchanged controlled full trainer.
Each worker freshly builds all four static game/representation matrices, then
processes original cell indices congruent to its slot modulo worker count.
Every trainer/cache is fresh per cell. There is no shared mutable strategy/RNG
state and no reference-solver output in training. A spawned interpreter, rather
than a forked inherited state, is required. Request one native-library thread per
child through the five environment variables in the config, and record them;
these settings do not prove an observed OS thread count.

Measure three repeats of the COMPLETE 140-cell short workload for each process
count: 1,260 endpoint rows, 1,000 external / 16 full additional iterations.
Rotate process-count order [1,2,3], [2,3,1], [3,1,2] to balance order positions.
Within each worker keep original cell order; fixed partition, no outcome-based
load balancing or favorable subset. Record unique PIDs, assignments, child setup,
cell timings, actual batch elapsed time, parent and reaped-child CPU time, source,
lock, environment and incomplete outcomes. Extra processes use extra simultaneous
resources and replicated trees; no free-compute or memory-saving claim.

Before any forecast, all 1,260 endpoints must exactly match the pinned serial
profile's stable iteration/work/tree/policy-array/RNG fingerprint fields.
Tests must cover partition completeness/uniqueness, spawned toy-worker parity,
worker exceptions/timeouts and cleanup, changed receipts and conservative forecast
arithmetic. Publish checked code/config before measurements; no training-strength
outcome or large learning run is part of this milestone.

## Accounting and decision

The 1,200-second calibration cap includes input validation, process/interpreter
startup, tree construction, cell initialization/training, IPC, parent collection,
validation and persistence. Record and retain any timeout or failed comparison.
Measure actual batch wall time; do not infer speedup by dividing by CPU count.
Parent/reaped-child CPU deltas report consumed resources, distinct from elapsed
time. Child function timers alone exclude interpreter import cost; OS child CPU
accounting includes it on the supported Mac/Linux runtime.

For each process count, forecast each of the unchanged cells to 10 million total
CFR visits using the maximum of its three measured training estimates. Sum within
the FIXED modulo partitions, then take the largest worker sum. Add measured maximum
worker tree preparation and batch startup/collection overhead; apply the same 2x
margin to that total. Preserve all source timings; report actual short-batch wall
ratios and aggregate CPU cost separately. Prepared node records never replace CFR
visits. Known training/launch cost below 7,200s is only an unresolved pipeline
forecast: scoring, checkpoint writing, own audits and reporting still need a
separate predeclared measurement. No automatic learning admission or best-arm
selection. If it still exceeds the cap, keep the large study off.

## Definition of done

A checked opt-in scheduler, exact endpoint/source-bound receipts, all nine batches,
rerunnable tables, meaningful tests, typing/lint/hooks/hosted CI, and journal/work
log update. Report regeneration validates historical data, not historical timing.
No default/playing-strength/global/river-cause claim. Then measure remaining
pipeline costs if supported by this result, or document the next measured obstacle.

## Implementation checkpoint

The scheduler uses spawned interpreters, worker-local trees/trainers/RNG and fixed
modulo assignments. It streams events to the parent, retains partial events and
terminates/reaps all children on error/timeout. Parent thread environment is restored
after launch. OS reaped-child CPU deltas include interpreter imports, while child
function timers begin later; these fields are kept separate.

Forecast overhead is conservative over observed short batches: maximum worker
elapsed minus its initialization/training timers retains tree preparation,
exports/fingerprints and IPC; maximum batch elapsed minus maximum worker elapsed
retains launch/import/collection/join. Add those maxima once to the largest fixed
worker sum, then apply 2×. Additional future scoring/checkpoint/audit costs remain
unmeasured; passing known-cost forecasts never starts the large learning study.

All 37 new and 95 prior focused tests pass (132 total), with spawned toy endpoints and exception/early-exit/invalid
message/timeout cleanup. The initial fixture import failed under pytest's import
mode; explicit test source-path propagation fixes the child fixture without any
training-math change. Lint/format and strict typing (261 files) pass. Broader local
suites pass: 1076 all-extras each Python 3.11.17 / 3.12.15; base-only 1043
pass / 24 optional skips. All-file hooks pass. Spawned tests also verify positive
OS reaped-child CPU accounting on this Mac in all three environments. Hosted CI
and the fixed calibration remain pending at this checked-code checkpoint.

### Three questions to explain this calibration

1. **Why should parallel scheduling preserve the strategy?** Each cell's trainer,
   seed and update order are independent; worker scheduling changes elapsed time,
   not its random sequence. Every endpoint must still exactly match serial output.
2. **Why not divide the serial forecast by three?** Startup, unequal partitions
   and CPU contention cost time. Measure complete batches and forecast the slowest
   fixed worker from contemporaneous per-cell timings and measured overhead.
3. **Does a cheaper forecast prove the agent is stronger?** No. It measures
   resource feasibility for a later controlled learning experiment. Scoring and
   checkpoint costs remain unknown, and no strength/default decision is made here.

Self-review: independent worker payloads never share mutable trainer/RNG state;
all stable endpoint fields and cache-query/preparation counters are checked against
the pinned serial result. Fixed-partition imbalance and max-of-three/overhead
arithmetic have an independent hand-computed fixture. CPU and elapsed-time fields
are distinct. This is a Codex-assisted solo self-review, not independent human
review. The published prospective gates remain unchanged.

## Recorded complete calibration

Clean checked published source `0dd5af6a366db300ce254b587dd616c79cb2279c`
completed all nine batches in **197.722051s**. Every one of the **1,260 endpoints**
exactly matches the pinned serial state/RNG/work fields and cache counters. All
worker identities, fixed partitions, requested thread settings, timers and clean
exits pass the receipt checks. No rows or repeats were discarded.

| Processes | Median complete short-batch wall | Median serial / batch | Median parent + child CPU | 2× known-cost forecast |
|---|---:|---:|---:|---:|
| 1 | 33.163s | 1.000× | 33.175s | 12250.546s |
| 2 | 18.691s | 1.771× | 37.213s | 6299.036s |
| 3 | 13.827s | 2.400× | 40.795s | 4257.374s |

These are three repeats each on this Mac, with balanced order positions; they are
not population confidence intervals. The three-process batch wall spans
13.817–13.851s; serial spans 32.607–33.228s. Median aggregate CPU rises from
33.175 to 40.795s, about 23%: parallel execution uses simultaneous resources and
replicates setup. It is not free compute or a memory-saving claim.

The three-process forecast uses worker training sums 2126.345 / 2089.681 /
2078.959s, then adds maximum worker nontraining 2.210810s and launch/collection
0.131603s before the 2× margin. The unguarded known-cost estimate is 2128.687s.
The one-process forecast still exceeds 7200s. Two and three processes both remain
`unresolved_unmeasured_pipeline_cost`: passing known cost does not admit learning.
All three counts are retained in the [scripted table](../results/parallel-cell-profile/report/tables.md),
[batch CSV](../results/parallel-cell-profile/report/batches.csv) and
[raw receipt](../results/parallel-cell-profile/profile.json), including source,
lock, hardware/runtime, all child events, assignments and cost breakdowns.
All three report files regenerate byte-identically on Python 3.12.15; this
validates saved evidence, not reproduction of historical timing.

```sh
.venv/bin/python scripts/profile_parallel_cells.py --report results/parallel-cell-profile/profile.json
.venv/bin/python -m pytest -q tests/test_cell_process.py tests/test_parallel_profile.py
```

Hosted CI remains separate and pending at this evidence checkpoint. The code and
prospective protocol were published before measurements. No learning curve,
playing-strength, default or river-cause result was measured here.

## Next decision

Use the three-process schedule as the fixed candidate for a separately declared
pipeline-cost check, because it leaves more known-cost headroom within the same
cap. Implement and verify checkpoint accounting and exact own scoring, using
previously saved own policies for cost calibration. Define metric aggregation and
coverage explicitly before any new learning-quality outcomes. Measure scoring,
checkpoint writing, setup/replay and report costs and apply the same planning
margin; retain the native reference audit as a separate comparison-only stage.
Do not start the 140-cell learning comparison from this timing result alone.
