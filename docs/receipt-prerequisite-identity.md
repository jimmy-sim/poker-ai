# Audit repeated prerequisite outputs

[Prospective issue #4 protocol](https://github.com/jimmy-sim/poker-ai/issues/4#issuecomment-6977198494) — November 18, 2026. This is a read-only validation study. It does not implement reuse or estimate a saving.

The [current receipt-cost report](receipt-source-cpu.md#november-18-what-the-current-clocks-show) locates 25.227/25.360 parent CPU seconds per observed cost read in six nested prerequisite loads. Those calls include original hash checks, saved receipt validation, trace reading, context construction and archive decoding. The question here is whether their returned data is identical across repeated fresh calls and whether those fresh results share mutable storage. Seven calls represent one direct and six nested loads as an audit inventory; standalone calls do not reproduce their complete-reader context.

## Definition of done for this step

- On actual locked Python 3.11.17/NumPy 2.4.6 and Python 3.12.15/NumPy 2.5.4, sequentially run seven original `frozen_batch_inputs.prerequisites(root)` calls in a fresh child under a 180-second outer wall cap, including startup. Retain partial/failing evidence. No OpenSpiel construction, learning, new real Hold'em trajectory or reference strategy is involved.
- Authenticate the exact code revision and clean status, lockfile and pinned input bytes before and after. Every original prerequisite call runs completely. Check all declared fields through a closed graph traversal. Compare exact type/bit/array-layout/content/internal-alias witnesses, plus independent semantic inventories of 64 own policies, 192 prefixes and 128 reply summaries. Require seven equal complete witnesses and no shared mutable object or NumPy storage across outputs. Unknown graph shapes or unsupported arrays reject explicitly.
- Test graph alias, overlapping array, changed field/input, unsupported type, partial retention and runtime/cap failures. Publish source and qualification before running actual archived inputs. Then publish the raw outputs before a data-only report, with original readers blocked during report reproduction. Complete applicable local, optional and hosted checks before history-preserving merge.

A pass establishes only the stated output identities and fresh-object isolation. Sharing one result inside the complete reader remains unproved. It requires a separate prospective complete comparison with every original validation, work counter and scalar/computed-replay identity unchanged, original 180/900/1800/120-second scientific caps, and no strength or forecast admission from one pair. A failure is retained as a negative result. The prior 912.54/900 forecast, 2.390%/1% accuracy and rejected full-context-copy experiment remain failed.

## First source qualification attempt — November 18

The first published source head `47852ff` passes both full local base suites
(5,574 passed, 71 skipped, 150 deselected each), Ruff, strict typing, hooks
and both hosted CI jobs. Its optional 3.11 scope passes 2,481 tests but fails
two new synthetic child tests. Earlier optional tests preloaded `pyspiel` in
the pytest process, so those in-process synthetic calls correctly met the
real child's reference-free guard. The [complete failure and passing base/CI
record](../results/prerequisite-identity/failed-source-478/manifest.json) is
retained. No actual archived-input audit was started. The test fixture now
supplies an isolated synthetic module view and independently checks that the
real child guard rejects a preloaded reference. Nine focused tests pass with
`pyspiel` preloaded in each optional environment. Full exact-head
qualification must be repeated on the corrected commit.

## Corrected source qualification — November 18

At `4f040ff`, both local base suites pass 5,575 tests, 71 skips and 150
deselections each, with Ruff, strict typing of 832 files, all-files hooks and
clean source guards. Both optional suites pass 2,484 selected tests each,
including the synthetic child isolation tests in their full suite order. Hosted
[CI #558](https://github.com/jimmy-sim/poker-ai/actions/runs/44301595530)
passes Python 3.11.17/NumPy 2.4.6 and Python 3.12.15/NumPy 2.5.4 on the same
whole source tree. The [six-role receipt and complete logs](../results/prerequisite-identity/source-checks/manifest.json)
are retained. The first source head's optional failure remains failed. These
are software checks; the seven actual archived loads have not run. Publication
and a successful public-source guard precede that collection.

## Raw identity audit — November 18

The [raw seven-load receipts](../results/prerequisite-identity/raw/manifest.json)
were published at `76952fe` before a report. Python 3.11.17 finishes its
seven-load outer command in 47.721 seconds, with 46.936 parent CPU seconds;
Python 3.12.15 finishes in 43.013 and 42.251 seconds respectively. Both are
below the 180-second child limit. Each fresh output contains 148,034 mutable
graph nodes and 148 arrays. All seven complete graph witnesses and independent
semantic inventories match within each runtime, and the witnesses match
exactly across runtimes. Each call executes the original archived checks; the
producer verifies no mutable object or NumPy storage is shared across its seven
fresh returned graphs. All fourteen pinned input files remain unchanged.

These standalone calls do not establish that one result can be safely shared
inside the complete reader. The observed run times are not estimated savings.
The published verifier authenticates the raw members and source without
executing a loader. A data-only two-runtime report is the next step.
