# Check matrix depths without repeated whole-tree scans

Registered November 15, 2026 in [issue #4](https://github.com/jimmy-sim/poker-ai/issues/4#issuecomment-6899625741)
before implementation or outcomes. This follows [PR #74](https://github.com/jimmy-sim/poker-ai/pull/74)
and its [loader CPU measurement](reader-load-cpu.md#recorded-result--november-15-2026).

## Question and completion criteria

Matrix construction accounts for 51.360752 of 277.177134 real-read process-CPU
seconds (18.5299%) in the preceding capture. Its final validation masks the
whole node array separately for every information group. Can a grouped integer
check preserve the result and avoid that repeated work? The individual loop has
not been timed; its possible savings are a hypothesis.

Done means a checked, private equivalent constructor, complete source-bound
software proof, one fixed complete-audit comparison, retained raw outcomes,
verified saved-data report, actual tests/CI and journal/work-log entries. A
negative or inconclusive cost result remains visible. This is an optimization
investigation, not a stronger strategy or a replacement training permit.

## Narrow implementation

Preserve all prior 406 source files. Add a private support module and comparison
entry under scripts, plus the new config: expected effective source count 409,
to be verified after implementation. Keep the original constructor available.
The candidate copies its construction body, replacing only the final depth
check with grouped integer minimum/maximum work linear in nodes plus groups.
A group must appear and have exactly one depth. Ignore negative/out-of-range
information IDs as the original per-group masks do. Keep the same ValueError
message and leave the arrays unchanged. No float tolerance or poker math changes.
An AST comparison must prove every other construction statement is identical;
only the private function's explicit cls annotation/decorator adaptation differs.

The scoped wrapper preserves class/subclass binding, arguments, return objects,
primary exceptions, earlier owned aliases and later imports. Reject a changed
baseline, nested installation, unsupported thread/process or exhausted capacity;
restore initial descriptor/alias objects and equivalent late aliases on failure.
Owned aliases include poker_ai modules and the private compact_cached package.
Arbitrary hidden/native references are outside this declared coverage.

Both original and grouped arms use the same successful-construction observer.
Record every dataclass field: array dtype, shape, strides, flags and C-order
bytes; nested tuples and scalar fields; and that source is the exact input
object. Compare ordered whole-child field fingerprints between arms, not
in-process object IDs. Source is an existing input, not a copied output array.
Keep complete/failed/partial constructor records and at most 512 calls per child.
The recorder adds work in both arms; its cost is included, not subtracted later.
Large tuple fields retain full typed content hashes and lengths rather than
repeating every action/key in each event. No elements are sampled or omitted
from those hashes. Array shape, strides, flags and full bytes remain included.

## Software evidence before collection

Independent direct-set predicates and property fixtures cover missing/empty
and mixed-depth groups, ignored IDs, extreme signed integers, input immutability
and malformed schemas. Constructed-field identity, subclass/descriptor/alias
restoration, exceptions, AST tampering, source/qualification/config rejection,
partial output and caps need tests before real measurement.

The source-bound proof uses 256 fixed generated integer cases with PCG64 seed
20261501, explicit edge cases and all five declared encodings on the pinned small
software construction fixture/model. This new fixture seed changes no historical
poker seed. Record inputs, decisions and complete field fingerprints, source,
config/runtime and timing; cap the complete proof at 180 seconds. It constructs
no learner or reference solver. Both full local bases, relevant optional suites
and both exact-source hosted jobs must pass and be published BEFORE this formal
proof or the comparison. Publish the proof and exact launch/save operators before
the one comparison; repeat required source/prerequisite checks inside its clocks.

The [config](../configs/grouped-depth-check.json) SHA-256 is
`8e627b4c8b9dc4a4a2346374a240dc3ed57836ed59c9190c0031cc1be70d03f8`.
It pins 47 inputs, including the previous source/capture/report and the small
software spot/model. Real archive execution remains Python 3.11.17 / NumPy 2.4.6
with the original locked extras and CPU-query/sleep-prevention utilities. Newer
Python qualifies software/data only, never original trajectory replay.

## One complete original/grouped pair

One ordered pair, original then grouped. Both arms install the same six sparse
CPU boundaries and preload the same modules. Retain the original tiny pre-read,
shared recall-proof cache, disabled-reuse card wrappers, initial/final own
mathematical reads, all three independent workers and source/publication/scalar
checks. Native worker processes remain unchanged and uninstrumented. OpenSpiel
2.0.2 and its recorded pinned Apache-2.0 license remain comparison-only;
reference strategies never enter the agent.

Keep 900 seconds per complete child, 1,800 shared, 120 seconds of operator saving
reserve and one attempt. All startup, preconditions, capture, field hashing,
original audit, final verification and required writes stay in their declared
clocks. Preserve the unchanged supervisor's self-measurement convention;
administrative exact canonical copying is outside the child clocks. No favorable
retry, subset, altered cap, seed or acceptance rule. Retain partial/failing
outcomes and original ignored bytes. Publish raw evidence before analysis.

The prepublished launch operator supplies a monotonic origin immediately before
starting Python through `POKER_GROUPED_COMMAND_STARTED`. The parent proof/pair
clock includes that interpreter's imports and orchestration. The unchanged
supervisor separately supplies each complete-child origin. A formal launch
without the operator origin is rejected. Final cap checks occur after the last
self-recording write; the saved elapsed value is taken just before that write.

Each arm must preserve all 432 profiles, 1,152 conditions, three computed reads,
worker/card/scalar and base-admission rejection witnesses. Each six-category
capture must contain 1,538 calls: tiny 432 checkpoints only; each real read 92
matrix, 26 spot-tree, 432 checkpoints and one call to each added loader. Both arms
together must remain below the 4,096 selected-call ceiling. All nesting, clocks,
process/thread identities and restoration checks remain required. Every successful
whole-child constructor fingerprint must match between arms, including calls
outside the selected read windows; missing or failed work is never zero.

The prospective diagnostic cost pass requires complete correctness/coverage,
strictly lower grouped complete-command wall time AND strictly lower grouped
selected-exclusive matrix CPU. Otherwise report fail/inconclusive honestly.
Report full clocks, nested inclusive/exclusive time and observer scope. One order
cannot establish uncertainty or pure causal savings. Inspect plots and require
portable numeric exports to match across actual supported runtimes with poker
execution blocked. Final applicable local and exact-head hosted checks precede
history-preserving merge.

Even a pass does not replace three fresh complete own costs, three fresh complete
native costs, the original conservative forecast or checked published admission.
The 933.889393168007/900 forecast stays failed; no new trajectories, default,
fresh/global admission or competitive-strength claim follows here.

Keep one coherent PR with required publication boundaries, actual dates,
Codex-assisted implementation and plain-English journal explanations. Do not
infer human hours or mastery. Continue until the user stops; no future schedule,
subagents or C++/Rust core. PR #74's pending final CI/merge remains a separate
prerequisite to its closure, not an assumed completed result.

## Three questions

**Why compare constructor fields?** A faster check is useful only if the same
inputs produce the same game representation, including arrays and metadata.

**Why observe both arms?** Matching observation scope avoids attributing the
presence of selected timers to the candidate alone. Observation still costs time.

**Does a faster diagnostic admit training?** No. The full source-bound proof,
all fixed cost repetitions, original conservative forecast and published permit
still decide whether training may begin.
