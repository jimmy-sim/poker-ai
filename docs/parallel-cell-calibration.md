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
