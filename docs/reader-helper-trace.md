# Measure helpers inside the complete saved-policy reader

Prospective protocol, November 14, 2026. Continues issue #4 after the narrow
publication check in PR #67. Codex assisted with this plan and implementation.

## Question

How many helper calls occur inside one complete `compact_cached.cli.read` of
`results/compact-cached-learning/cost/0/own.json`, and which categories account
for the observed synchronous intervals and reaped-child CPU increments?
The preceding publication check made 21 calls in roughly 0.6 seconds. That
smaller scope cannot explain the older complete reader's child CPU. Measure the
complete function before choosing an optimization.

## Fixed design

Use the [versioned config](../configs/reader-helper-trace.json). One ordered
control/observed pair, one full read per separate process. Keep the original
reader, loader, provenance checks, archive replay, score computation, error
checks and report checks unchanged. Capture the actual computed summary through
its existing `observed` argument, rather than copying the stored summary.
Run with the original recall-proof cache enabled and a fresh cache per arm;
leave the experimental pure-card cache disabled. This cold-cache condition is
explicit: it does not reproduce the earlier audit's shared toy/real-read cache
history. No toy warm-up, native worker or solver construction is part of this
measurement. The existing read-only isolation still blocks learner/reference
construction and imports. No training, policy edit, source-predicate bypass or
reference output enters a strategy.

Require actual Python 3.11.17/NumPy 2.4.6. Request the same pinned Darwin
`caffeinate -i` utility-lifetime idle prevention for both commands; no display
assertion or persistent setting. Both commands include startup, imports,
source/qualification/input checks, reader, telemetry, verification, writes and
teardown. Keep 900 seconds per complete child and 1800 seconds shared, including
final saved-pair verification. The reader deadline starts at the complete-child
origin, without resetting it at target entry. These diagnostic caps do not
alter the original study's 7200/900 caps, seeds, configs, failed gates or permits.
No retry to seek a timing direction. No RNG or seed is used by this read.

## Observation and source coverage

Use the existing recorder and independent CPython process-event census. Bind all
394 previously published measurement-source files unchanged, plus only the new
entry and config (396 effective files). Place this private diagnostic outside
`src/` to preserve the historical all-src dependency maps; reusable frozen
recorder code remains the implementation of helper classification and resource
boundaries. Publish exact tested source and all six same-head actual-runtime
roles (local base/optional and hosted, both versions) before the first real read.
Fixtures use fictional receipts/tiny temporary Git repos, never a prequalified
real reader invocation. Relevant tests also cover the unchanged reader call,
cache scope, actual-summary capture, caps and complete failure retention.

Record declared read-only Git categories, argument fingerprints and output
fingerprints, not raw arguments, inputs, outputs or environment. Detect cached
run/Popen aliases using the existing separate audit-event count. Require one
process event per successful recorded request, no unsupported/unassigned events
and no failed helper. Coverage applies to this sequential Python subprocess
path, not a security boundary, machine-wide census or Git's descendants.
Store full event/ledger dictionaries in gzip streams to keep repeated resource
records reviewable without changing their values. Entry/exit streaming,
compression, hashing and observer work remain charged. Retain starts, available
partial streams/ledgers and outer failure status on exceptions/timeouts; an
abrupt kill can leave a truncated gzip stream, which cannot qualify as complete.

Counter deltas span synchronous calls. They are not exclusive PID CPU; unrelated
concurrent reaped children would confound them. Clocks are nearby, not atomic;
RSS is cumulative with producer-specific units. Do not stack CPU as wall time,
call subtraction idle time, or infer a machine cause from one ordered pair.

## Acceptance and reporting

Both full returned own dictionaries must equal the pinned input, and both
actual computed summaries must equal the pinned zero-error historical replay:
432 unique profiles, 324 raw profiles, 108 composed profiles, 216 ledgers,
30 warm origins and 1152 fixed conditions, with policy/ledger bits exact.
Require exact control/observed returned identity, computed summary and validation
cache counters. Validate unchanged input/source maps before/after, actual
runtime/hardware, complete command/PID/cap/qualification hashes, every raw
counter delta, gzip stream/ledger identity and fixed file inventory. All counters
and decisions come from the reader; no hand-tuned result or selected subset.

Publish raw complete/partial/failing own evidence BEFORE the report. Preserve
ignored originals and exact retained copies. A read-only reporter verifies
source, published qualification, raw hashes, command scopes and mathematical
identity before grouping helpers by category and argument-fingerprint reuse.
Report counts, distinct fingerprints, maximum repeats, interval wall/parent CPU
and reaped-child user/system CPU, alongside complete-child and reader boundaries.
Show either timing direction descriptively. This pair is not a production
optimization, substitute full-audit forecast, stronger/default/global agent
claim, or permission for the still-unrun training comparison.

Done means a checked and published complete-reader helper inventory with its
raw evidence, readable table, limitations and next decision, or a retained
explicit failure explaining what prevented completeness. Keep one coherent PR,
issue #4, the work log and the learning journal updated. Stop at that milestone;
a new optimizer or broader audit collector is a separate decision.

## Software implementation

The collector invokes the unchanged reader once and captures its one actual
computed summary, complete returned-receipt hash and fresh validation-cache
counters. Gzip events are flushed as calls start/finish; the final/partial ledger
is written in a finally block. Full raw dictionaries survive lossless compression.
The parser checks command-log hashes as well as child/ledger/stream bindings,
rejects changed scopes, counters, caps and symlinks, and groups repeated argument
fingerprints without retaining arguments. A killed stream can remain truncated;
it is retained as incomplete rather than silently repaired.

Fifty-five new software fixtures cover compressed records, reader/cache/deadline
call shape, computed-summary identity, privacy/alias coverage, missing source
qualification, tampering, failures and read-only reporting. Combined with the
previous recorder/collector fixtures, 116 pass on the local3.11 runtime; strict
checking passes for750files. These fixtures do not run the real archive reader.
The six exact-source qualification roles and their publication still precede
formal data. Type-checking initially caught a reused gzip stream variable and
an untyped fixture return; both were corrected without changing reader behavior.

Clock boundaries follow the reused supervisor: each complete-child observation
ends after process teardown and before the supervisor writes that measurement
receipt. The shared pair clock starts at the pair function, includes those
measurement writes and final saved-pair verification, and ends before its own
last receipt write. Parent entry-point import/argument dispatch and that final
self-write are outside the shared recorded interval. The operator records its
invocation separately. These are the existing accounting conventions, not a
relaxation of a study cap or a full-audit runtime claim.

## Source qualification — November 14, 2026

Source0e46992 binds396files, fingerprint
`db1fbed91a6f91613dc7a5c1da4a4b5ed30558100727aa3343d995c03626aad1`.
All394 historical files remain unchanged. Both full local suites pass3748tests
(801.47/786.78seconds), and both relevant optional suites pass260
(12.15/10.62seconds). Hosted43618535981 passes3748tests on each actual runtime:
Python3.11.17/NumPy2.4.6 and3.12.15/2.5.4. Exact heads, uv selections,
installed runtime markers and untrimmed log hashes are verified. A direct log
redirect timed out; the authenticated connector supplied the complete log, with
its companion log verified byte-identical to the successful direct download.
No job or experiment was rerun for that retrieval failure.

[Qualification](../results/reader-helper-trace/checks.json), all six raw role
logs, check runners and the exact forthcoming operator are published before the
one real pair. Qualification is software/source evidence, not a reader timing
result or permission for a training study.

## Retained incomplete attempt — November 14

The original control exits1 after37.860311792complete-child seconds; the shared
pair stops at37.897130209. No observed arm starts and no complete mathematical
summary or helper ledger exists. These are failed-command durations, not a reader
benchmark or a zero helper count. The four available raw files, original ignored
bytes, execution records and manifest were published278fc04 before this analysis.
The receipt records `PackageNotFoundError`, not the missing distribution's name.

A metadata-only inventory shows the launcher used the base environment: NumPy
was present, but Numba, OpenSpiel, Treys, PokerKit and Matplotlib were absent.
The frozen reader explicitly checks Numba's installed version, and other
historical checks use optional package/license metadata. Missing Numba is a
known unmet requirement; the retained error does not prove which package was
queried first. The already-qualified optional environment has the complete locked
extras. No solver construction or real-reader retry was used to diagnose this.

Static review also finds a CPU-brand `sysctl` query in runtime metadata called
by the complete reader. The original Git-only catalog would mark that helper
unsupported. Merely switching environments would therefore be insufficient.
The old collector, config, qualification and failed data now stay frozen.

## Prospective runtime-complete follow-up

Continue the SAME complete-reader question in this PR, before another outcome.
The [new config](../configs/complete-reader-helper-trace.json) fixes ONE new
control/observed pair at a fresh destination. Preserve the preceding failed run;
no attempt is selected or substituted. Unchanged900/1800caps, original reader,
input/archive, cold validation cache, idle-control request, exact mathematics,
successful-helper requirement and all prior study limits still apply. This is
an environment/coverage correction, not a change to poker or an optimization.
Stop after this pair's checked inventory or a retained explicit failure.

Use a new private collector/config, preserving every previously measured396
file byte-for-byte (398effective files). Require installed versions of all
locked extras BEFORE target entry, recording their metadata without importing
a reference. The operator uses the actual all-extras3.11 environment qualified
on this source, rather than the base environment. Missing/mismatched versions
must fail before a real read. Newly changed source requires all six fresh
same-head actual-runtime checks and published qualification before collection.

Extend recognition only for the exact existing read-only CPU-brand command:
`sysctl -n machdep.cpu.brand_string`, with the original check/capture/text
arguments. Verify its resolved binary and hash before collection. All other
non-Git forms stay unsupported, original arguments/results/exceptions remain
unchanged, and raw arguments/contents remain unrecorded. Both validation Git
helpers and this declared metadata helper must succeed for a complete trace;
a failed optional probe is retained as an incomplete trace even if the reader
handles its fallback. Keep the independent process-event census, original
resource deltas, gzip integrity and complete before/after source checks.

Add software fixtures for exact probe recognition, changed property/flags and
unexpected calls, process-event coverage, probe failure retention, dependency
preflight and the prior failure's honest unknown helper count. Keep actual
reader/solver/learner execution blocked in fixtures. Publish all new raw
complete/partial/failing evidence before reporting. Report Git and CPU metadata
separately, and retain the previous attempt in the final writeup. No stronger
agent, forecast rescue, default or new-study admission follows.

### Follow-up software checks

The new collector recognizes the original CPU probe without changing its call,
return or exception. Dependency and binary checks run before target entry and
the recorded requirements are verified on saved-data inspection. Failed probes
remain failures; no validation is suppressed. A metadata-only `--failed-attempt`
report labels the prior helper count unknown, never zero.

The follow-up adds68 fixtures, including missing-dependency target blocking,
exact metadata-probe/failure/alias coverage and altered saved requirements.
Combined184 recorder/collector fixtures pass on each version (5.34/4.11seconds;
see current check logs for exact timings). Strict checking passes752files.
These tests do not run the real reader. The new398-file source needs fresh
full base, optional and hosted qualification before collection.

### Follow-up qualification — November 14

Sourceab69275 binds398files, fingerprint
`e1e5e879d347244cea79ee599e2ce32460a7ab1881e944ecd0f2acd68dfb8752`.
All396 previously measured files remain unchanged. Both full local suites pass
3816tests,64skips/150deselections (781.55/766.57seconds); optional suites pass
328each (15.32/14.09seconds). Hosted43622239051 passes both actual runtime jobs,
3816tests each with the existing warning (736.56/656.41seconds). Installed
Python/NumPy markers, uv versions, source heads and complete connector log
hashes are authenticated. Strict752files and all895lint/format files pass.

The [new qualification](../results/complete-reader-helper-trace/checks.json)
publishes all six raw role logs, source-check runner and the exact operator
before the one corrected pair. The operator selects the actual all-extras3.11
qualification environment and verifies every declared distribution and the probe
binary; the same prerequisites repeat inside both complete child clocks.
The original failure remains independently reproducible with
`python scripts/collect_complete_reader_helpers.py --failed-attempt`.
