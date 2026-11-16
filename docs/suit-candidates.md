# Compare boards only after the private-card minimum

Registered November 15, 2026 in [issue #4](https://github.com/jimmy-sim/poker-ai/issues/4#issuecomment-6905294880),
before implementation or measurement. [The preceding lookup](suit-lookup.md#recorded-cost-result--november-15-2026)
passes one cost diagnostic, with a small 0.56% wall difference and a 3.28% matrix
CPU difference. Unchanged worker runtimes also differ. No production benefit,
forecast rescue or stronger agent follows from that point.

## Question and exact argument

The original function chooses the smallest pair `(sorted private, sorted board)`
across all 24 suit renamings. Python compares the private tuple first. A smaller
board can never compensate for a larger private tuple.

For permutation `p`, call those tuples `H_p` and `B_p`, and let `h* = min H_p`.
Then the exact result is `(h*, min B_p over the permutations where H_p == h*)`.
Keep every tie; choosing just one private-minimum permutation could give the
wrong board. This is finite lexicographic minimization, not a poker heuristic,
changed information partition or new strategy.

**Example:** private `2c 3c`, board `4s 5s 6s`. The smallest private tuple keeps
clubs as clubs. The spades can become diamonds, giving canonical board `4d 5d 6d`.
Making the board independently all clubs would break its relation to the private
cards. Only simultaneous suit renamings are allowed.

## Fixed geometry and private scope

[The sealed config](../configs/suit-candidates.json) fixes 68 pinned inputs before
support implementation. Preserve all 415 prior scientific sources; add only the
entry, support and config for 418. Precompute a 52-by-52 ordered private-card
table. The 52 duplicate-card diagonal slots are sentinels; all 2,652 valid slots
record the minimum private tuple and original indices of every tying permutation.
The tie counts are six for same-suit different ranks, two for different-suit
different ranks, and four for a pair. Preserve original index order.

Check every slot independently against all 24 literal rank/suit transformations
and the existing 1,248-entry translation table. Preserve original length/mask
validation before indexing, output values/types, input immutability and original
exceptions. Return fresh outer/private tuples where the original constructs them.
An empty board needs no board-candidate comparison. Unsupported or keyword calls
and changed dependencies use the captured original implementation.

This stores static finite card geometry, including the private minimum. It does
not adaptively memoize full hands, train features or cache strategies/EVs. Both
arms share initialization, guards, counters and full-field observation. Keep main
PID/thread limits, typed accounting, fresh output, nested/changed-hook refusal,
earlier/late alias restoration and primary exceptions. Native spawned workers
keep original code and no private hooks. No production default is changed.

## Acceptance before measurement

Tests cover every table slot and valid private order, the minimum identity, all
tie cardinalities, valid boards, global suits/input orders, invalid/unsupported/
keyword calls, dependency fallback, typed flags/counters, PID/thread/caps,
restoration/primary failure, sealed source, clocks/publication and partial/failing
retention. Complete immutable-head full local bases and relevant optional suites
on both Python versions, then both exact-source hosted roles with actual runtime,
all uv selections and complete tested-tree proof. Publish six receipts and exact
launch/save operators before the formal proof.

One own software proof has the unchanged complete 180-second cap. It checks all
1,248 translations and 2,704 geometry slots, all 2,652 ordered valid preflop
hands, plus 1,024 cases for each board length 3/4/5: 5,724 valid cases. Reuse
software-only PCG64 seed 20261502 for boards; extending deterministic preflop
inputs consumes no RNG. Historical poker seeds/streams remain unchanged.
Compare retained typed original/all/reduced values, all 17 fixed behavior cases,
and complete original/all/reduced fields for all five original builder encodings.
Expected invalid cases stay distinct from actual capture failure. Construct no
learner/reference or new trajectory. Publish complete/failing proof first.

## One all-candidate/reduced-candidate audit pair

Fixed order: `all`, then `reduced`. Control uses PR #77's all-24 translation-table
function; candidate compares boards only within the private-minimum tie set.
Both include the same new eligibility/dependency/counter observer and full fields.
This measures the factorization relative to all-candidate lookup, not an unwrapped
production implementation. Require positive actual reduced-kernel coverage.

Keep original uncached card wrappers, shared recall cache, fictional tiny pre-read,
initial/final own reads, all three native workers, source/publication/scalar checks
and writes. All 432 profiles, 1,152 conditions, three reads, worker/card/source/
scalar identities, original card accounting and all 184 pinned ORIGINAL field
fingerprints per arm must match. Reconcile requests, fallback/original/all/reduced
evaluations and errors; keep the ten-million-request bound.

Six sparse regions remain 1,538 calls per arm, 3,076 combined below 4,096. No
five-phase recorder, per-request timing or global per-frame/per-node profiler.
Whole supervised child 900 seconds each, registered shared 1,800, failure-saving
120, unchanged. Charge imports/static initialization, all original stages,
validation, observers, extraction, final checks and writes. Operator origin starts
immediately before Python launch. One attempt, no favorable retry, changed caps,
seeds/gates, subset or save-reserve success extension. Retain exact ignored and
published complete/partial/failing raw/admin files; failed administration cannot
be usable evidence. Publish raw before posthoc analysis.

Pass requires every correctness/source/coverage/field/counter check, lower
complete supervised wall **and** lower selected exclusive matrix CPU than the
all-candidate control. Keep missing/failing/slower outcomes. Overlapping workers
are not added into wall; one fixed order establishes no confidence interval,
population runtime or stable causal attribution for unrelated stage variation.

## Reporting and current boundary

Archive execution is actual Python 3.11.17/NumPy 2.4.6 with locked extras, CPU
query and temporary idle control. Python 3.12.15/NumPy 2.5.4 is software/saved-data
only. OpenSpiel 2.0.2 remains comparison-only under its recorded Apache 2.0 license;
no commercial solver output or reference strategy enters the agent.

One coherent PR retains source qualification, proof, raw and report. Inspect
plots and reproduce numeric exports with actual poker execution blocked; retain
export failures. Final relevant local and both exact-report-head hosted jobs
precede history-preserving merge and fresh guarded main verification. Preserve
unrelated user bytes, actual dates and AI attribution; keep journal/work log current
and batch mandatory publication boundaries. No subagents, future automation or
C++/Rust core is authorized here.

PR #77 is now merged after both final hosted jobs and guarded main checks.
Its [closing receipts](../results/suit-lookup/final-ci/manifest.json) are batched
with this source increment. This protocol does not change work permissions or scientific limits.
A separately qualified production family, full original end-to-end proof, all
three own publications before any fresh native, all three native costs, original
conservative forecast and checked published admission still precede trajectories.
The 933.89/900 compute and 2.390%-versus-1% accuracy failures remain.

## Three questions

**Why can private cards be considered first?** The original minimum compares the
private tuple before the board. Larger private tuples cannot win regardless of
the board; every tie at the smallest tuple must still be considered.

**Why not choose one tie arbitrarily?** Different tying suit maps can produce
different boards. The second minimum preserves the exact original result.

**What would a faster diagnostic establish?** Only a cost point with exact original
outputs and the declared workload. It would not replace production qualification,
conservative forecasts or strategy-quality evidence.


## Recorded source qualification — November 15, 2026

All six exact-source roles pass on `3a15a53`: local full suites each pass 4,586
(64 skipped, 150 deselected), optional suites each pass 1,098, and both source
GitHub jobs pass 4,586 with the existing warning. Hosted run `43796168210` uses
actual Python 3.11.17/NumPy 2.4.6 and Python 3.12.15/NumPy 2.5.4. Every uv
selection, actual checkout and complete tested tree is verified against the
checked source. These are software-suite durations, not the actual audit's
900-second budget.

[The six receipts](../results/suit-candidates/checks.json), full untrimmed logs,
raw metadata and exact launch/save operators are retained. All 415 prior sources
remain unchanged; effective source is 418, with 68 pinned inputs. Eight extra
fictional failure-routing fixtures pass. All 5,724 software inputs have identical
hashes across both environments; no original/all/reduced request kernel, game,
learner, native or trajectory is evaluated by that input-generation check.
Static geometry metadata may initialize.

Publish these records before the one formal own software proof. Full suites can
exercise toy/fixture solvers; they do not invoke the actual complete-audit target
or a new real trajectory study. No timing result or production admission exists
at this qualification checkpoint.


## Recorded own software proof — November 15, 2026

After qualification publication `d62b657`, the one formal own proof passes.
Complete outer time is **6.4555765409895685 seconds**, registered time
6.42996020798455 and supervised child time 3.901490958989598, all under the
complete 180-second budget. There is no interruption or retry.

All 1,248 translation entries and 2,704 geometry slots pass the independent
specification. Original/all/reduced each complete 5,724 valid cases and 17 fixed
behavior cases, with exact output/type/input checks. All five complete matrix
field vectors match across the three implementations: 15 witnesses total.
Original direct records are own-code baselines, not external solver output and
not invented private-kernel counters. The valid/builder scopes record 12,296
requests per variant, all using its declared kernel, with zero fallbacks/errors.
Expected negative fixed cases are retained separately from actual capture failure.

[Proof](../results/suit-candidates/software/proof.json),
[child](../results/suit-candidates/software/child/child.json) and
[manifest](../results/suit-candidates/raw-software-manifest.json) retain all 62
raw/administrative files plus exact ignored originals; the manifest is the 63rd.
Publish them before the one actual all/reduced pair. No learner/reference/new
trajectory is constructed, no production family is admitted, and there is no
cost verdict yet. Scientific source, caps, seeds and previous failures stay fixed.


## Recorded raw audit pair — November 15, 2026

After own-proof publication `9331d4e`, the single registered all/reduced pair
completed without interruption. Both child processes exited successfully,
within their 900-second limits; the complete command took
829.4326407079934 seconds, within the shared 1,800-second limit.
The original audit identities, complete constructor fields, source bindings,
card and worker checks all pass. This is the only attempt.

[Raw pair](../results/suit-candidates/pair/pair.json) and
[retention manifest](../results/suit-candidates/raw-pair-manifest.json) preserve
53 raw/administrative files and their exact ignored originals. Publish these
files before calculating the cost comparison. There is no cost verdict at this
checkpoint, and this diagnostic does not admit production training.
