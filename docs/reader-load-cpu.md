# Locate CPU work inside saved-input loading

Registered November 15, 2026 in [issue #4](https://github.com/jimmy-sim/poker-ai/issues/4#issuecomment-6891701494)
before implementation or collection.
This follows [PR #73](https://github.com/jimmy-sim/poker-ai/pull/73) and its
[coarse CPU result](coarse-reader-cpu.md#recorded-result--november-14-2026).

## Question

The previous two real reader calls used 294.714306 seconds of process CPU.
The three selected operations explained 52.97%; 138.599270 seconds, or 47.03%,
lay outside them. Which input-loading and historical-replay branches account
for that remainder? These are saved old own cost stand-ins, not new training.

The older elapsed profile supplies low-frequency leads, not present CPU
measurements. Keep the three original boundaries and add three ordinary
functions:

| Category | Boundary |
|---|---|
| `matrix_build` | `MatrixTree.build` |
| `spot_tree_build` | `SpotTree.build` |
| `checkpoint_replay` | `learning_training.replay_snapshot` |
| `comparison_inputs` | `evaluation.compact_opponent_sources.load` |
| `legacy_inputs` | `evaluation.opponent_learning_sources.load` |
| `sampled_source_replay` | `evaluation.compact_fixed_inputs.replay_sources` |

The loaders can contain each other and the original operations. Use the
recorded call forest to subtract immediate selected children before adding
category totals. Keep inclusive CPU, selected-exclusive CPU, root union and
outside-selected CPU as distinct fields. They measure process/library CPU
observed during regions, including observation cost and library threads; they
are not instruction samples, pure function self time or a wall-time partition.
Keep floating residuals and the existing 1e-9 CPU-second arithmetic allowance.
No poker-score tolerance changes.

## Implementation and coverage

A private entry reuses the checked coarse collector under an explicit bounded
extension context. Preserve every prior 404 source file. The new entry and
[config](../configs/reader-load-cpu.json) should form a 406-file effective map;
verify that count and its exact fingerprint after implementation. This private
placement preserves the frozen all-src contracts and older readers.

Extend only the collector's category registry, target factory and owned-module
alias iterator. Do not replace its original contract, binding, qualification,
entry or output globals with a new family's permit. The new runner has its own
complete source binding, six-role qualification, output namespace and report.
Reject an already changed or nested extension and restore original objects on
success and failure. Prove that the old three-category collector still works
after the extension exits.

The existing alias iterator covers `poker_ai.*`. Add the owned `compact_cached`
package and submodules because its command module imports `load` directly.
Cover defining attributes, existing aliases and late imports; restore initial
alias objects and equivalent late aliases. Arbitrary hidden closures or native
references remain outside this declared coverage. Reject generator targets:
timing a factory call would miss work performed when its iterator advances.
The selected loader functions are ordinary calls.

Preload the same six targets and command aliases in both arms, before original
card hooks. Only the profiled arm records selected entry/exit events during the
original three reader calls. Keep serial main-thread coverage, process/thread
identity, full events, original results and primary exceptions. No global
per-function profiler or low-level clock callback is installed. Native workers
have no active selected capture.

## Fixed workload, limits and acceptance

Run **one control / profiled pair** through the unchanged original uncached audit:
tiny pre-read, shared recall-proof cache, disabled-reuse card wrappers, nested
original observers, initial and final mathematical reads, three native workers,
source/publication checks and original scalar verification all remain.
Common preloading does not reconstruct historical machine/process state.

The config pins 41 inputs: the preceding 37 plus the coarse raw manifest,
profiled source anchor, numeric summary and render manifest. Its SHA-256 is
`ddc766c5357cfabc831113d158f6a3e25df161a9f5bfacc3b3408848a15f44a3`.
Python 3.11.17 / NumPy 2.4.6, locked optional packages and the declared Darwin
CPU query/sleep-prevention utilities remain required. OpenSpiel 2.0.2 and its
pinned Apache-2.0 license remain comparison-only, under the existing installed
license check and read record. Reference strategies never enter the agent.

Limits remain **900 seconds per complete child, 1,800 seconds shared**, with
120 seconds of operator saving reserve and **4,096 selected calls** across all
three reads. Child startup, checks, original work, capture and final validation
remain charged. The unchanged supervisor excludes its own measurement-receipt
write from the child clock; parent orchestration and final pair verification
belong to the shared clock. Administrative canonical copies remain outside,
with original ignored outputs retained. One attempt; no favorable retry, subset,
smaller workload or cap extension. Preserve partial and failing outcomes.

Require complete original 432-profile, 1,152-condition, three-replay, worker,
card-counter and scalar identity against the historical original and both arms.
Require complete restored six-category capture and all original resources.
The original three per-read call inventories must also match the coarse archive:

| Read | Matrix | Spot-tree | Checkpoint |
|---|---:|---:|---:|
| Tiny software pre-read | 0 | 0 | 432 |
| Initial real read | 92 | 26 | 432 |
| Final real read | 92 | 26 | 432 |

Require every new category somewhere in the completed capture. The old elapsed
profile's two calls per added function supply a capacity lead, not an acceptance
count. A complete empty category for one read is legitimate; missing or partial
work is never reported as zero. All intervals must nest inside their reader and
selected parents with monotone clocks, supported identities and original
computed witnesses. Retain the base-family admission rejection.

Before collection, tests cover the bounded extension and its restoration,
private command aliases, nested six-category accounting, cross-family and
schema rejection, changed baseline counts, missing events, primary exceptions,
unsupported generators/threads, caps and partial retention. Full local bases,
relevant optional suites on both versions and both same-source hosted jobs must
pass with actual runtime/uv/PR-head evidence. Publish exact source qualification
and launch/retention operators before the single pair, then publish raw evidence
before analysis. Keep one PR and batch local work before the initial source push.

## Reporting and next decision

Report all three read inventories, nested inclusive and selected-exclusive CPU,
union/remainder, control/profiled read/body/worker/command clocks and provenance.
Do not add overlapping regions or worker CPU to explain wall time. One order
cannot isolate pure observation overhead or estimate runtime uncertainty.
Inspect the figure, verify portable saved-data extraction with poker execution
blocked, and compare numeric exports under actual Python 3.12.15 / NumPy 2.5.4.
That newer runtime qualifies software/data only, not real trajectory replay.
Final applicable local checks and both exact-head hosted jobs precede merge.

Use a complete result to choose the next measured target. If coverage fails,
retain unknown work and debug the instrument before selecting an optimizer.
No strategy, algorithm, seed, scientific cap, quality target or default changes.
The failed 933.89/900 forecast and old child-CPU discrepancy remain unresolved;
this diagnostic cannot admit a new Hold'em study or competitive-strength claim.

Continue issue #4 under the current request until interrupted. The chosen
priority is validation and training improvement before a Chipzen adapter.
This creates no future automation and authorizes no C++/Rust core or subagents.
Codex assists with implementation and reporting; personal hours and mastery
are not inferred.

## Three questions

**Why retain the original counters?** Their per-read inventory checks that the
new view still observes the same named work, rather than losing calls while
assigning more time to parent regions.

**Why include private command aliases?** Replacing a defining function does not
replace an earlier imported copy. The actual reader entry must be covered and
restored, including on exceptions.

**Does assigning the remainder fix the runtime limit?** It supplies a target.
An optimizer still needs its own correctness and complete cost/forecast checks;
no hash receipt replaces a required mathematical replay.
