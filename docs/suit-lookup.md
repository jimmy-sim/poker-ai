# Compute card-suit normalization with a fixed lookup

Registered November 15, 2026 in [issue #4](https://github.com/jimmy-sim/poker-ai/issues/4#issuecomment-6903489482),
before implementation or measurement. [PR #76's capture](matrix-phases.md#recorded-cpu-result--november-15-2026)
locates 44.433599 of 52.715310 matrix CPU seconds in information/key creation.
That is a target for investigation, not a measured saving from this candidate.

## Question and completion criteria

The original normalization considers all 24 suit permutations. Each repeatedly
computes `4 * (card // 4) + permutation[card % 4]`. Test a private fixed 24-by-52
translation table, keeping the original sorted tuples and lexicographic minimum.
Compute every permutation on every request. This is not a card-result cache.

Done means checked private support/runner, complete source qualification and a
published own software proof, one original/lookup full-audit pair, retained raw
success/partial/failure, portable data-only tables/plot, final local/hosted checks,
work log and plain-English journal. Diagnostic pass requires all correctness,
coverage, field and counter checks, lower complete-command wall **and** lower
selected exclusive matrix CPU. No prior failure or acceptance rule is changed.

## Exact private scope

Preserve all 412 prior source files; expect 415 effective files after adding
entry/support/config. [The config](../configs/suit-lookup.json) seals inputs,
software cases, immutable table hash and caps before new code or results.
The 24 rows follow the original `SUIT_PERMUTATIONS` order. Validate all 1,248
builtin integer entries independently against rank/suit arithmetic.

Primitive supported calls may use the private kernel. Unsupported types/keywords
or changed captured card-validation/permutation dependencies execute the captured
original. Preserve validation order, exceptions, input immutability, output types,
sorting and minimum semantics. No sorting/coercion of the input cache key, result
memoization, RNG, feature/payoff/policy cache or reference-strategy input exists.
Restore earlier and late owned aliases even on primary failure. Main PID/thread
only; reject nesting and changed hooks. Reference workers use original code and
no private hooks. Their common imports/startup still belong to complete clocks.

Both modes install the same private eligibility/dependency/counter observation:
control calls the original arithmetic; candidate uses the table when supported.
Record requests, original/private evaluations, fallbacks, errors, restoration and
alias inventory, with a ten-million-request safety ceiling per child. This is
algorithm request accounting, not timed per-frame/per-node profiling. Cost is
relative to this instrumented control, not an unwrapped historical command.

## Qualification and own software proof

Tests cover every entry, all preflop pairs, valid/invalid/unsupported/keyword
behavior, suit and input permutations, changed dependencies, counters, PID/thread,
restoration/primary failure, source/schema/clock/cap refusal and partial retention.
Complete immutable exact-head local bases and relevant optional suites on both
Python versions, then both hosted roles with actual Python/NumPy/uv and full
tested-tree proof. Publish all six receipts and exact launch/save operators.

One complete 180-second own software proof follows that publication: all 1,248
table entries, all 1,326 unordered two-card preflop pairs, and 1,024 valid cases
for each board lengths 3/4/5 (3,072 total), from software-only PCG64 seed 20261502.
There are 4,398 valid hand cases. Historical game seeds/RNG streams stay unchanged.
The fixed call catalog additionally checks invalid and unsupported behavior;
record expected software exceptions separately from failed real collection.
Compare the five original builder encodings on the pinned small fixture/model
with the same complete field observer. Construct no learner/reference or new
trajectory. Publish complete or failing own proof before any actual audit.

## One complete original/lookup pair

Only a usable published software proof permits the one pair, in that fixed order.
Keep uncached original card-result wrappers, shared recall cache, fictional tiny
pre-read, initial/final own mathematical reads, all three original native workers,
source/publication/scalar checks and writes. All 432 profiles, 1,152 conditions, three
computed reads/worker/card/source/scalar identities and original uncached card
request/computation counters must match. Both arms must match all 184 pinned
original constructor field vectors. The full-field observer is the same in both.

Retain the existing six sparse global regions: 1,538 calls per arm, 3,076 combined
below 4,096. Do not add PR #76's 920 phase intervals to this pair or install a
global per-frame/per-node profiler. Record complete process/library CPU clocks;
respect nesting and never add parents, children or parallel workers twice.

Whole child 900 seconds each, shared command 1,800, failure-saving reserve 120.
Charge table initialization/imports, source/check/proof validation, all original
stages, observation, extraction, final verification and writes. Operator origin
begins immediately before Python launch. One attempt, no favorable retry, subset,
changed seed/cap/gate, or use of failure-saving time to make a pass. Retain ignored
originals and exact raw/admin copies, including partial failures. Failed outer
administration never yields a usable proof. Publish raw before posthoc analysis.

Archive execution uses actual Python 3.11.17/NumPy 2.4.6 and locked extras, CPU query and
temporary idle control. Python 3.12/NumPy 2.5.4 is software/saved-data only.
OpenSpiel 2.0.2 remains comparison-only under its recorded pinned Apache 2.0 license;
its strategy outputs never enter the agent. No commercial solver input is used.

## Reporting and boundaries

Report all values/counters/field identities, total/body/read/worker clocks,
inclusive/exclusive region CPU and old/current scope limitations. Inspect plots
and verify portable numeric exports with actual poker execution blocked. Retain
export failures. Explicit legacy 3.11 sequential CPU association may reproduce
frozen-parser bookkeeping within its existing 1e-9 CPU-second arithmetic allowance;
no raw/poker/tolerance/gate change or recapture follows from reporting differences.

Final relevant local and both exact-report-head hosted jobs precede a
history-preserving merge. One coherent PR through required publication stages;
batch related changes, keep issue/work log/journal current, actual dates and
truthful AI attribution. Preserve unrelated user bytes and source history.
No subagents, future automation, C++ or Rust core is authorized here. The active
user instruction continues work until stopped; it sets no new scientific caps.

A diagnostic pass is one ordered historical cost case, not population runtime,
peak memory, competitive full-game strength or production/default admission.
The old grouped-depth/card-cache timing failures, 933.89/900 production forecast
failure and 2.390%-versus-1% accuracy failure remain. A separately qualified
production family, prescribed full original end-to-end proof, all three own
publications before any fresh native construction, all three native costs,
original conservative forecast and checked published admission still precede
real trajectories. PR #76 is merged with final hosted and main verification retained in its
[closing receipts](../results/matrix-phases/final-ci/manifest.json).

## Three questions

**Why can the table preserve the result?** It stores each original integer
translation for the same 24 permutations and 52 card IDs; sorting and minimum
remain unchanged. Exhaustive entry checks and original-output comparisons test it.

**Why keep the original control instrumented?** Both arms pay the same guards,
counters and field observer. The resulting claim is relative to that control;
it is not a measurement of an unwrapped production implementation.

**Would a faster point prove stronger poker?** No. Software/cost admission and
later strategy-quality evidence are separate. All production and learning gates
remain in force, including unfavorable historical outcomes.
