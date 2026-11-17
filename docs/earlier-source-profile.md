# Look inside the earlier-source loader using saved evidence

[Prospective plan](https://github.com/jimmy-sim/poker-ai/issues/4#issuecomment-6954063964),
November 17, 2026. This is a saved-data investigation; no new profiling, poker
training or reference-solver run is part of it.

The [source-loading measurement](source-phase-cpu.md) puts about 33–34 CPU seconds
in checking earlier scientific sources. The label covers more than files: the
loader also builds two games and computes replies to frozen own opponents.
The [context-reuse experiment](context-reuse.md) showed why the next change needs
a measured target: copying complete contexts was slower, and its original
comparison failed. That result stays failed.

Before adding another instrument, this step reads the existing
[complete elapsed-stack profile](compact-native-wall-profile.md). It asks what
its direct caller edges can already tell us about five functions:

- `opponent_learning_sources.load`
- `opponent_learning_sources.build_game`
- `opponent_learning_sources.frozen_opponent`
- `opponent_learning_sources.boundaries`
- `batch_current_inputs.load`

These were selected before their values were extracted. The report keeps every
original function and caller row, and all incoming and outgoing edges for each
selected function. It does not select a favorable top-N.

## What the numbers mean

The old profiler used its built-in elapsed timer. A function's **self time** is
time in its own frame; its **inclusive time** also includes calls below it.
Both include blocked waits and profiling overhead. They are not CPU measurements.
A **caller edge** records calls from one function to another.

**Example from the independent test fixture:** a shared helper takes eight seconds
across all callers. Five belong to the first caller and three to another caller.
Charging all eight seconds to the first caller would misattribute the work.
The report retains both edges instead of assigning the helper's aggregate to one
place. Tables at different depths overlap, so they must not be added together.

Each selected, nonrecursive function must recover its inclusive time from its
self time and all direct outgoing edge times, within a fixed 1e-7-second absolute
roundoff tolerance. Missing or ambiguous frames, changed inputs, incompatible
units and unsupported recursion reject. Duplicate labels retain distinct raw
entry identities rather than being merged.

## Reproduce and browse

After the checked reader is published, these commands read retained evidence:

```sh
.venv/bin/python scripts/inspect_earlier_source_profile.py
.venv/bin/python scripts/inspect_earlier_source_profile.py --function 1
.venv/bin/python scripts/inspect_earlier_source_profile.py --function 3
.venv/bin/python scripts/inspect_earlier_source_profile.py --output results/runs/earlier-source-profile-local
```

The first command lists the five functions. The numbered views show every direct
incoming and outgoing edge. The last exports all original entries and edges,
the selected tables, a numerical summary and the producer-authentication log.
Use a fresh output folder; existing reports are retained. Output inside the
historical producer folder is refused.

The reader authenticates the complete original pair, raw hashes, source commit
trees, scalar/replay identity and elapsed units through the existing saved-data
checker. Selected top-level AST positions and exact producer file hashes bind
code coordinates across reader runtimes; recorded bytecode digests are retained,
not recompiled as if Python minors produced the same bytecode. All raw input
files are checked again after export. The original binary profile is hashed
as provenance, never deserialized or executed.

## Acceptance and next decision

The implementation must pass independent graph and failure fixtures, exact saved
input/source checks, both actual supported reader runtimes and byte-identical
numeric exports with numerical construction paths blocked. Applicable local and
hosted checks precede a history-preserving merge. The prospective selection and
six input hashes live in `configs/earlier-source-profile.json`.

The source was published before selected values were extracted. The result below
decides which code path to inspect next and whether a narrow current measurement
is still needed. Historical elapsed values
cannot be subtracted from the newer 33–34 CPU seconds to estimate savings. This
step cannot admit training, rescue the failed forecast or accuracy gates, or
establish competitive full-game Hold'em strength. Codex assisted with the plan,
implementation and drafting; human hands-on hours were not recorded.

## Three questions to explain the method

1. **Why use a caller edge instead of the callee's total?** The same helper can
   serve several callers. Its aggregate combines them; the direct edge preserves
   the share recorded under one caller. Deeper shared work cannot be assigned to
   an ancestor from that aggregate alone.
2. **Why not call these CPU seconds?** The original instrument measured elapsed
   stack time, including blocked waits. CPU clocks were recorded separately.
   A newer CPU measurement is not interchangeable with these older frame values.
3. **How does this help the model?** It can identify a more defensible target for
   reducing validation cost, which supports faster checked research iterations.
   Reading a saved profile itself changes neither the strategy nor its strength.


## Historical saved-data result — November 17

Source `395575b` was public before extraction. Both actual supported runtimes reproduce all five numerical exports exactly, with 104 construction/profiling targets blocked, zero forbidden calls and all 15 raw producer files unchanged. No new profiling, reference construction or poker training occurred.

These are **aggregate elapsed-stack seconds from the historical instrumented command**, including waits and profiler overhead. They are not current CPU measurements or savings estimates. The two cost reads share their input, and nested rows overlap.

| Preselected function | Calls | Self seconds | Inclusive seconds |
| --- | ---: | ---: | ---: |
| `opponent_learning_sources.load` | 2 | 0.000496088 | 138.044 |
| `opponent_learning_sources.build_game` | 4 | 0.0001785 | 10.8936 |
| `opponent_learning_sources.frozen_opponent` | 48 | 0.00395262 | 0.874028 |
| `opponent_learning_sources.boundaries` | 2 | 0.000248531 | 0.00464088 |
| `batch_current_inputs.load` | 2 | 0.000301291 | 125.609 |

The earlier-source loader records 138.044 seconds across its two calls. Its direct `batch_current_inputs.load` edge accounts for 125.609 seconds; that function's direct `reduced_study_run.read_saved` edge accounts for 125.552. These are nested quantities, so they must not be added.

The loader's direct frozen-opponent edge is 0.860610 seconds across 32 calls. The frozen-opponent function also serves the tiny proof fixture, which explains why its aggregate row shows more calls. The exact incoming edges are:

| Caller of frozen opponent | Calls | Edge inclusive seconds |
| --- | ---: | ---: |
| `opponent_learning_sources.load` | 32 | 0.86061 |
| `opponent_learning_own.fixture` | 16 | 0.0134178 |

Every selected function recovers its inclusive time from self time plus all direct child times within the fixed 1e-7-second tolerance. The largest residual is 1.42109e-14 seconds. Every original frame and edge remains in the complete exports; rounded display values do not replace full-precision records.

**Next decision:** inspect the earlier archive reader before considering a frozen-opponent cache or another profiling run. In this historical profile, archive checking is the large direct component; frozen-opponent construction is small. A current optimization still needs a prospective test and current measurements. This analysis does not rescue either failed research target or establish stronger play.


Full-precision records: [selected functions](../results/earlier-source-profile/report/selected-functions.csv),
[all selected edges](../results/earlier-source-profile/report/selected-edges.csv),
[all original frames](../results/earlier-source-profile/report/all-functions.csv),
[all original caller edges](../results/earlier-source-profile/report/all-callers.csv),
and [summary](../results/earlier-source-profile/report/summary.json).
The [two-runtime equality receipt](../results/earlier-source-profile/data-checks/earlier-source-numeric-equality.json)
and constructor-guard records retain the actual executions. This table can be
regenerated after running the reader:

```sh
.venv/bin/python results/earlier-source-profile/data-checks/summarize.py.txt --report results/earlier-source-profile/report --output results/runs/earlier-source-tables-local.md
```

Final corrected-head checks and protected-main reproduction now pass; see the
[closing checks](../results/earlier-source-profile/final-ci/manifest.json) and
[next archive-reader query](archive-reader-edges.md). No figure is needed for five
rows; the complete edge tables retain the detail behind the summary.


### Optional-suite isolation correction

The first full optional cohort on `03c7022` finds a test-isolation error: earlier
valid tests import OpenSpiel, so the strict own-only guard refuses the new
regression in their shared interpreter. Both optional suites report one failed
and 2,318 passed; the base suites and base-only hosted CI pass. The [complete
failed cohort](../results/earlier-source-profile/failed-qualification-03/manifest.json)
is retained and is not counted as final qualification.

Only the regression changes: it now proves the reference-loaded parent is refused
and executes the saved-data read in a fresh child interpreter. All 31 focused
cases pass on both runtimes with real OpenSpiel deliberately preloaded in the
parent (3.06/3.04 seconds). The child retains all 104 construction/profiling blocks
and five exact export checks. The runtime guard, reader code, config, raw data and
reported numbers remain unchanged. Complete final checks must pass at the fixed
new head before merge.
