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
The installed Darwin getrusage(2) manual was checked on November13 and specifies
ru_maxrss in bytes. Reaped-child counters include all completed subprocesses in that interval:
parent-wide intervals can include parallel native workers and metadata tools.
They are not an additional wall interval. RSS is a cumulative per-process peak,
not interval allocation;
units are explicit
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

## Completed diagnostic — November 13

All six actual-runtime source checks were public64172d0 before collection.
The pair finishes0 with exact432scores,1152fixed conditions,three computed
reads,card counts and unchanged worker summaries. All three read boundaries and
three source/runtime/PID-bound worker records validate. Both commands stay below
900seconds; shared1078.7796968330076 stays below1800. All original raw bytes,
exact retained copies,execution and read-only verification are preserved.

| Complete-command observation | Uncached | Cached |
|---|---:|---:|
| Whole elapsed seconds |551.6211327499914|527.1198560829944|
| Parent body CPU seconds |285.656045|260.792604|
| Native-worker batch elapsed seconds |168.3006215409987|167.0785949580022|

The timing direction is lower in this separate diagnostic, under its explicit
idle-prevention request and extra observer source checks. It is descriptive;
it does not overturn the older481.84→595.65failure, establish a production
speedup, identify an idle-sleep cause or supply a replacement budget forecast.
The card hit/original-call counts remain exactly those of the previous pair;
no errors,fallbacks or evictions occurred. No new learner or strategy was trained.

The new [clock and resource exports](../results/card-audit-clock-trace/report/)
show that parent CPU alone omits active work in other programs. Selected raw
intervals, rounded here only for reading:

| Interval | Elapsed s | Process CPU s | Reaped-child user CPU s | Reaped-child system CPU s |
|---|---:|---:|---:|---:|
| Uncached initial own read |161.59|139.15|21.46|1.30|
| Cached initial own read |149.92|127.11|21.92|1.28|
| Uncached final own read |163.93|140.93|21.97|1.31|
| Cached final own read |151.16|128.18|21.97|1.29|
| Uncached worker0 |168.10|124.74|39.54|2.56|
| Cached worker0 |166.92|124.28|39.52|2.53|

These are OS-reported counters at matching boundaries. They are not additive
wall intervals; child counters include all reaped subprocesses and do not name
the program responsible. The trace adds effective-source checks around workers,
so its costs are not the uninstrumented production costs. Existing source code
launches Git metadata helpers, but this trace has no per-command CPU ledger and
cannot assign all child CPU to a particular helper or diagnose the old run.
The earlier elapsed profile is a different measured copy. The next useful test
is per-helper attribution and accounting, before another optimization is chosen.

The [inspected chart](../results/card-audit-clock-trace/report/resource-clocks.png)
keeps elapsed stacks separate from process CPU bars. A blue/orange difference
must not be called idle time: child CPU is separately exported. All16clock
intervals,288counter rows and32peak records survive. Reaped-child RSS is kept
as the OS aggregate field and is not interpreted as process-tree memory or a
memory-saving claim. Peaks remain cumulative,with explicit producer units.

A postcollection direct-child API sanity fixture checks the parent's child-CPU
increment against that child's self-reported CPU for fixed integer work, with
0.1second accounting tolerance. It is a small software check, not a poker timing
experiment or a causal test. A separate report fixture's exact comparison to2
exposed ordinary floating subtraction1.9999999999999998 on Python3.12; its assertion
now uses approximate comparison. Both versions pass all9report/accounting tests.
The390measurement-source files, all recorded values and original failures stay
unchanged. This does not backfill an unperformed precollection test.

```sh
.venv/bin/python scripts/trace_card_audit.py --show results/card-audit-clock-trace/pair
open results/card-audit-clock-trace/report/resource-clocks.png
.venv/bin/python -m pytest -q tests/test_card_audit_clock_trace.py tests/test_card_clock_report.py
```
