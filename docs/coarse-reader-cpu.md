# Locate CPU work inside saved-policy validation

Registered November 14, 2026 in [issue #4](https://github.com/jimmy-sim/poker-ai/issues/4#issuecomment-6890391633),
before implementation or timing data. This follows the [original-context audit](original-audit-helpers.md)
from [PR #72](https://github.com/jimmy-sim/poker-ai/pull/72). Implementation and evidence
are in [PR #73](https://github.com/jimmy-sim/poker-ai/pull/73).

## Question and fixed scope

The current original audit spends about 141–158 seconds of own-process CPU in a
real saved-policy read, while child-helper counters stay below one second.
Which broad operations account for that process work?

The older [elapsed profile](compact-native-wall-profile.md) supplies three leads:
`MatrixTree.build` (184 historical calls), `SpotTree.build` (52), and
`learning_training.replay_snapshot` (1,296). Those are historical counts and
wait-inclusive frame times, not present CPU measurements or a required current
inventory. A previous global CPU-callback profiler exceeded its 900-second cap;
that failure remains retained. This instrument times only the selected coarse
boundaries and installs no cProfile or global per-function callback.

Run one ordered **control / profiled** pair through the unchanged original audit
child in `uncached` mode. Keep its tiny pre-read, shared recall-proof cache,
disabled-reuse card wrappers, nested original reader observers, complete initial
and final mathematical reads, native workers, source checks, own-publication
checks and scalar verification. Both arms preload the same target modules;
only the profiled arm adds selected wrappers during each reader call. This is
a controlled current context, not an exact reconstruction of historical machine
or process state, and one order cannot estimate pure observer overhead.

## Instrument and units

Record process CPU and wall clocks at selected entry/exit, category, read index,
parent, process/thread identity, full start/end events and failures. Preserve
class-method descriptors, subclass binding, original arguments/results and
primary exception identity. Replace known loaded module aliases, capture late
imports from the patched defining attribute, and restore original descriptors
and initial alias objects plus equivalent late aliases. This covers the named
attributes and module aliases, not arbitrary hidden closure or native references.

Only a serial main-thread call stack is supported. Reject reentrant capture,
changed threads/processes, incomplete events, invalid nesting or clock order,
and more than 4,096 selected calls over the three reads. Require all three
categories somewhere in the completed inventory. A complete empty selected-call
ledger for an individual read is valid; an incomplete ledger is never zero work.
Keep partial files and original exceptions on failures.

Inclusive CPU includes selected descendants. Derive **selected-exclusive CPU**
by subtracting immediate selected children, and compute the selected union from
root intervals. Outside-selected read CPU is the remaining inner-read CPU.
These are process/library CPU observed during regions, including observation
cost and any library threads, not instruction samples or pure function self CPU.
Selected-exclusive means exclusive of these three selected regions only.
Preserve floating residuals; a 1e-9 CPU-second roundoff allowance validates
subtraction, without changing any poker-score tolerance. Never sum overlapping
inclusive regions, worker CPU or CPU clocks into a wall-time partition.

## Source, limits and acceptance

[Config](../configs/coarse-reader-cpu.json) pins 37 inputs, selected categories,
original Python 3.11.17 / NumPy 2.4.6, locked extras and Darwin utilities.
The new private entry/config preserve all 402 prior source files and form a
404-file effective map, without changing the frozen all-src aggregate.
No algorithm, seed, accepted policy, original output, scientific cap or gate
changes. OpenSpiel 2.0.2 remains the pinned Apache-2.0 scalar-only reference;
its installed license and the existing read record stay bound by the original
adapter. Reference strategies never enter the agent.

Both complete children must fit **900 seconds** each and **1,800 seconds** shared,
including startup, source/qualification/input checks, all original work,
capture/extraction/writes and final validation; keep 120 seconds of operator
saving reserve. One attempt, fresh ignored destinations, no favorable retry,
smaller workload or cap extension. Retain and publish partial/failing outcomes.
The unchanged supervisor times each complete spawned command through reaping;
its own measurement-receipt write belongs to parent orchestration rather than
the child-command clock. Parent orchestration and final pair verification are
charged to the shared clock. Canonical copying/publication is administrative
preservation outside these clocks, retaining the original ignored outputs.
Diagnostic data remain rejected as base-family admission and cannot replace
the failed 933.89/900 forecast or the old CPU-profiler/card-cache failures.

Require exact original 432-profile, 1,152-condition, three-replay, worker and
card-counter identity against the historical original control and both halves;
all original resources; complete selected events and restoration; valid CPU/wall
nesting inside each read. The first 70 fixtures cover nested accounting,
clock/schema changes, aliases/descriptors/subclasses/late imports, primary
exceptions, unsupported coverage, caps, partial retention and data-only reports.

Full local bases and relevant optional suites on both supported versions, then
both same-source hosted jobs with actual runtimes/uv/head verified, precede
qualification publication and the one pair. Finish local implementation/review
and checks before the initial source push. Publish exact qualification and
operators before collection, then raw evidence before analysis. Keep one PR
through these required boundaries; routine progress edits its description.

## Interpretation and next decision

Report the complete or partial inventory, inclusive/selected-exclusive/union
CPU, outside-selected CPU, control/profiled read/body/worker clocks, exact
identity, raw provenance and limits. Do not select an optimizer from missing or
invalid coverage. A complete result supplies a measured region for a separately
specified optimization; it does not itself improve the agent or admit training.
The old child-CPU discrepancy remains unresolved.

The initial and final real reads replay the same saved own strategies around
independent reference work. They are repeated validation, not new training or
independent playing-strength samples. Differences in their timings describe
this execution; they do not show the strategy improving between reads.

Current authorization permits continued issue #4 work after this bounded step,
using each verified result to define the next question. It creates no future
automation, permits no C++/Rust core without approval, and changes no research
acceptance rule. Codex assistance and actual dates are recorded; personal hours,
mastery and independent human review are not inferred.

## Three questions

**Why use coarse boundaries?** They require far fewer callbacks than timing every
Python frame. The complete command cap still decides whether the instrument is
usable; the earlier global CPU-profiler failure remains a failure.

**Can inclusive CPU values be added?** Only after removing nested selected
children. Report the union of selected roots and the outside remainder, while
retaining the original inclusive values and their nesting.

**Does the largest region automatically name the remedy?** It identifies a lead.
An optimization still needs its own correctness, source, cost and acceptance
checks, and measured savings cannot silently replace the failed forecast.


## Published source qualification, November 14

Source8970bc556697d684b6482be82f431699a76128d7 preserves the prior402files and
binds404effective files, fingerprint
`00a339915681bbb109d04c9ee15a90d245a8bd6672b5d01b4081b17d44d3e8db`.
All [six roles](../results/coarse-reader-cpu/checks.json) pass: full local bases
3,951/64skipped/150deselected each; optional463each; both hosted jobs in
[CI43688723951](https://github.com/jimmy-sim/poker-ai/actions/runs/43688723951)
3,951/64/150 each plus the retained historical roundoff warning. Complete decoded
logs and actual Python/NumPy/uv/head evidence are retained. Python3.12.15 with
NumPy2.5.4 qualifies software only; the real archive remains3.11.17/2.4.6.

The exact [launch](../results/coarse-reader-cpu/checks/operator_launch.py.txt) and
[retention](../results/coarse-reader-cpu/checks/operator_retention.py.txt)
operators are published with this qualification before any collection. No pair
has run at this checkpoint. Complete/partial evidence will be copied exactly,
with original ignored files retained, and published before posthoc analysis.
