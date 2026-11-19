# Source audit before skipping prerequisite loads

The [prospective issue #4 question](https://github.com/jimmy-sim/poker-ai/issues/4#issuecomment-6999055328)
asks what a future skipped-work cache would omit. This audit reads source and
the already published [complete pair](../results/validated-sharing-count-gate/pair-raw/manifest.json)
at merged revision `5017f8a`. It starts no archived read, solver or training.
Its definition of done is a traceable call map, a list of checks that would
disappear, and a fail-closed contract for a later implementation question.

## Why the complete archive has seven calls

The complete [saved reader](../src/poker_ai/evaluation/reduced_study_run.py)
checks its saved format, status, source and admission, then calls
`frozen_batch_inputs.prerequisites` directly once. Its
[admission path](../src/poker_ai/evaluation/reduced_study_protocol.py)
also replays reduction correctness and reduction profile. The profile replay
recursively replays correctness, so there are three reduction replays. Each
[reduction replay](../src/poker_ai/evaluation/batch_reduction_run.py) calls
`batch_reduction_inputs.prerequisites`, which reads a frozen timing profile
and also replays a cost profile. That [cost replay](../src/poker_ai/evaluation/batch_cost_run.py)
calls `batch_cost_inputs.prerequisites`, which reads the same frozen timing
profile. Each [frozen timing read](../src/poker_ai/evaluation/frozen_batch_protocol.py)
loads `frozen_batch_inputs.prerequisites` once. Therefore three reduction
replays × two nested loads = six, plus one direct load = seven per archive
root. The published pair's two roots per child show this exact six-nested,
one-direct order. These are dynamic calls through a few source locations,
not seven distinct source statements.

| Path in one root | Original loads | Validation retained by the caller |
| --- | ---: | --- |
| Reduction correctness replay | 2 nested | Reduction receipt, cost receipt, frozen timing rows and prefix identities |
| Reduction profile replay | 2 nested | The same checks, plus profile receipt and forecast |
| Recursive correctness replay from profile | 2 nested | Correctness binding, source and work rows |
| Saved reader after admission | 1 direct | Own archive grid, saved replay receipt and admission checks |

## What the original loader validates

Every [frozen prerequisite call](../src/poker_ai/evaluation/frozen_batch_inputs.py)
checks the frozen config hash and its declared input hashes, then calls
[`averaging_history_inputs.load`](../src/poker_ai/evaluation/averaging_history_inputs.py).
That load validates the averaging-history config and nine declared input
hashes; reads and checks the controlled-reply own receipt and source; loads
its 64 policies; validates the archived native receipt; checks all 128
controlled-reply trace records; decodes selected original-history archive
rows against saved contexts; and requires 192 unique prefixes and 128
replies. The native receipt is comparison evidence, not a training target.
No new solver is constructed by this load.

The calling layers separately check the frozen timing receipt and its
prefix identities, the cost and reduction receipts, the saved-study
source/admission and the final own replay. Those caller checks still run if
only the prerequisite loader is replaced, but their inputs would come from
the earlier graph. The existing [validated sharing wrapper](../scripts/validated_prerequisite_sharing_support.py)
keeps every original loader and its checks before forwarding that graph;
its successful complete pair establishes behavior identity **with no work
skipped**.

## Boundary for a future optimizer

Returning the first graph on six later calls in a root would skip six full
loader executions: five nested and the direct call. It would bypass each
skipped call's config/input hashing, controlled own/source and native
receipt checks, trace validation, archive decode, graph construction and
inventory checks. Two roots would skip twelve loads in one complete child.
The published one-pair wall times cannot estimate the saving because that
pair still ran all fourteen original loads and added observation work.

An optimizer needs a new prospective protocol before changing any loader.
At minimum it must bind one donor to one root and read, prove the same
arguments and pinned bytes at every skipped site, check donor integrity
before and after consumers, restore aliases on all exits, and independently
preserve or replace every validation listed above with an explicit test.
It must state in advance which loader and work counters are *expected* to
change; all other saved result, work, scalar, replay, context and native
identities must remain exact. A previously failed exact-work gate cannot
be relaxed after observing a pair. Mutation, changed pin/source/receipt,
unexpected call order, unsupported graph shape or partial failure must
reject. Source qualification and public own proof must precede any new
reference-bearing pair; raw bytes must precede its report. Keep the
original 180/900/1,800/120-second caps and fixed seeds unless a separate
prospective decision changes them.

This audit does not establish that inexpensive independent validation is
possible. It does not admit a cache, CPU saving, new strategy or training.
The earlier 912.54/900 forecast, 2.390%/1% accuracy and rejected reuse
pairs stay failed. Codex assisted with the source audit; human hands-on time
was not recorded.

## Checks on this documentation step

The seven mapped source modules parse. The existing sharing gate and
report tests pass on both locked runtimes: 24 passed and one expected skip
on each. The new audit, current-status, journal and work-log relative links
resolve. No implementation or scientific data file changed. Hosted CI on
this documentation commit remains required before merge.
