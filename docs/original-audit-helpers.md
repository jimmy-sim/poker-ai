# Measure helpers in the original audit context

Registered November 14, 2026 in [issue #4](https://github.com/jimmy-sim/poker-ai/issues/4#issuecomment-6889171302),
after the [saved-boundary reconciliation](reader-helper-trace.md#saved-boundary-reconciliation--november-14-2026)
and before implementation or new timing data.

## Question

The older complete audit recorded about 21–22 seconds of reaped child user CPU
inside each real reader call. The standalone reader later recorded about 0.24.
The saved arithmetic and source bytes agree, but the surrounding calls differ.
Does that reading reproduce when the original complete audit runs again, and do
its reader helpers account for the child-counter increments?

Run one ordered **control / observed** pair. Both invoke the frozen
`trace_card_audit.child` in its `uncached` mode. This preserves the tiny pre-read,
shared existing recall-proof cache, card-function wrappers with reuse disabled,
nested original read observers, all own-publication checks, initial real read,
three native workers, final real read, worker/source telemetry and complete
scalar verification. No poker implementation or original source file changes.

Only the observed half adds helper recording around each numerical reader call,
inside the original outer observers. Each inner interval retains its snapshots,
actual computed witness, helper ledgers and independent CPython process-event
counts. The control has no new inner observer. Both receive the same new startup
qualification and runtime checks, so this restores the original audit's call
context, not every aspect of the historical process lifetime or machine state.

This pair controls the new observer. It does not isolate card wrappers from cache
history, prove pure observer overhead, or turn the old standalone run into a
concurrent causal control. Whole-command, body, read, helper and worker clocks
have different scopes. CPU and overlapping worker clocks are not additive wall
partitions; reaped-child counters are not exclusive per-PID attribution.

## Fixed source and collection contract

[Config](../configs/original-audit-helpers.json) fixes 31 input hashes, original
Python 3.11.17 / NumPy 2.4.6, locked optional versions, exact Darwin utility
binaries and one attempt. The private entry/config preserve all 398 prior
measurement files and both PR #71 checker/config files; the effective source
map has 402 files. All earlier failures, raw results, seeds, compute caps and
acceptance criteria remain intact. No per-call CPU profiler is installed.

Before either real child, publish all six checks at one tested source head:
full local base suites and relevant optional suites on 3.11.17 and 3.12.15,
and both hosted jobs with actual installed Python/NumPy and uv selection checked.
Publish qualification logs and exact launch/retention operator before collection.
Newer software/data environments do not become eligible real-archive runtimes.

Each complete child is capped at **900 seconds**, the pair at **1,800 seconds**,
including startup, source/qualification/input checks, original work, observer
compression/validation, writes and final pair verification. Keep a separate
120-second operator saving reserve. Existing destinations are refused. On any
failure or timeout, retain all available original and new partial files, stop
the pair, and publish them; no favorable retries, smaller workloads or longer
caps. Publish raw evidence before interpretation. This diagnostic is rejected
as base-family admission and cannot rescue the 933.89/900 failed forecast.

## Acceptance and software checks

Require exact equality of all original 432 scalar profiles, 1,152 fixed
conditions, three computed replays, three worker summaries and disabled-card
cache counters against the historical original control and between halves.
Validate every original read/worker resource record. Every observed inner read
must remain inside its original outer interval with the same producer, scope
and actual computed result. Each helper must remain inside its inner interval.

Helper coverage requires complete original dictionaries/stream starts and ends,
recognized read-only Git commands or the exact CPU metadata query, successful
calls, one recorded CPython launch per request and no unassigned launch or
observer/retention error. Unknown/failed/bypassed calls retain their execution
and partial evidence but fail coverage. Counting excludes native worker launches
outside reader calls; it is not a machine-wide or native-launch census.

Tests cover forwarding and restoration, call shape and witness identity, the
three-read inventory, nested intervals, helper coverage, source/input and raw
file changes, missing extras/qualification, base-admission rejection, timeouts,
partial retention and data-only reporting. The first 37 fixtures pass; full
source qualification still precedes any real measurement. Successful software
checks do not imply a successful timing result or stronger poker strategy.

## Reference and reporting limits

The unchanged native adapter checks the previously published own archives before
comparison. OpenSpiel 2.0.2 remains an Apache-2.0 scalar-only reference; no solver
strategy enters the agent. The complete installed license was reread for this
step and matches the [recorded license hash](solver_validation.md#solvers-versions-and-licenses).
No new Hold'em training or opponent strategy is created here.

Report both full or partial outcomes, all reader intervals, helper groups and
resource sums, original scalar identity, body/worker context and limits. A small
helper total means helper launches are a poor optimization target in this case;
a large total first needs attribution/context checks. Either direction stays
visible. Stop after this report or an explicit retained failure, before choosing
an optimizer, changing forecasts/admission or starting another measurement.

## Three questions

**What does the pair control?** Both halves run the same original audit; only the
added helper observer differs. One fixed order cannot separate every machine or
cache effect, so timings remain descriptive.

**Why keep the workers if the question concerns readers?** Removing them would
change the original audit context and the required final read. Their own clocks
stay separate from reader-helper attribution.

**Does matching every scalar establish agent strength?** It checks that the
instrument preserved the old comparison. It neither trains an agent nor supplies
fresh-game evidence, a successful forecast or competitive full-game strength.
