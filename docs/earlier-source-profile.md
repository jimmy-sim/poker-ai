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

No selected historical values have been extracted at this protocol stage. The
result will decide whether saved evidence identifies a useful bounded target or
whether a narrow current measurement is still needed. Historical elapsed values
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
