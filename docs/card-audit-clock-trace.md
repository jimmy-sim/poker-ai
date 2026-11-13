# Trace active work and elapsed time around the complete audit

Prospective protocol, November 13, 2026; issue #4; Codex assisted.
The previous parent-card cache pair completed identical mathematics but failed
its timing gate:481.84seconds uncached,595.65cached. Parent CPU fell283.80to261.25;
unchanged reference-worker CPU stayed about123seconds each, yet worker elapsed
time rose134to165. Tiny-read and other elapsed time also rose. Preserve that
failure. No production integration or budget rescue follows.

This separate diagnostic asks what additional resource observations can and
cannot explain the discrepancy. It reuses the exact old pure-card cache source,
limits, inputs, order and kernels. It changes instrumentation and explicitly
controls idle-sleep prevention for BOTH commands; it does not rerun the old
protocol or reclassify its timing failure. Register [the fixed config](../configs/card-audit-clock-trace.json)
before implementation/outcome.

Collect nearby perf/UTC/process/thread clocks and own/reaped-child resource
snapshots at parent/body and each of the three real own-read boundaries. Wrap
each unchanged spawned reference worker with two own-process snapshots and a
source-bound separate sidecar; leave its numerical summary untouched. Capture
OS-provided user/system CPU, peak RSS, faults, swaps, block I/O and voluntary/
involuntary context-switch counters. Raw snapshots and derived deltas survive.
RSS is a cumulative per-process peak, not interval allocation; units are explicit
(Darwin bytes; Linux KiB in software fixtures). Zero/unsupported counters do not
prove an event absent. Calls are nearby, not atomic. CPU is not stacked as wall
intervals or summed across parallel workers. UTC is observational, not a cap clock.

Use installed `/usr/bin/caffeinate -i` only for each command's utility lifetime,
with its binary hash pinned. The locally read Apple manual describes this as
preventing system idle sleep while the utility runs. No display assertion or
persistent setting; the complete supervisor clock includes control startup and
teardown. Process-group termination still kills all children on timeout. This
new condition cannot establish what happened in the old pair; no sleep history
or machine-wide/private process log is collected. Scheduling, I/O, memory
pressure, idle behavior and instrumentation remain hypotheses, not causes.

All effective old387files remain byte-identical; add the entry, resource helper
and config explicitly. Six same-head actual-runtime base/optional/hosted checks
must be public before formal collection. Then ONEcomplete uncached/cached fixed
cost0pair,900seconds per command,1800shared,1800finalCI+120save reserve before
9a.m.Pacific. No retry, cap extension, altered seed/work or new poker learning.
All initial/final own replays,three native workers,loading/checks/writes remain.
Preserve full and partial outcomes. OpenSpiel2.0.2Apache2.0 remains comparison-only
under its recorded pinned license; no reference strategies enter training.

Definition of done is exact432scores/1152fixed conditions/three computed reads,
matching original worker/card counters, authenticated complete resource sidecars
and valid clock/counter accounting within caps. Report either timing direction
as a descriptive observation. There is no performance admission in this step.
A resource pattern can support a hypothesis but this single ordered pair cannot
prove a machine-level cause or population runtime. All older accuracy, compute,
CPU-profiler and runtime-record failures remain. No default/global claim, permit
or real trajectory tonight; the latest reserved learning start has passed.
