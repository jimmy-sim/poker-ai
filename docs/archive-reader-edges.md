# Follow the earlier archive checks

The [first saved-graph result](earlier-source-profile.md#historical-saved-data-result--november-17)
locates most historical earlier-source loading time in `read_saved`, the reader
for a previous training archive. This follow-up asks which direct checks account
for that work, before adding another instrument or choosing an optimization.
The [selection was recorded before extraction](https://github.com/jimmy-sim/poker-ai/issues/4#issuecomment-6957605618).

## The fixed question

Seven defining functions are selected:

- `reduced_study_run.read_saved`
- `reduced_study_protocol.require_admission`
- `reduced_study_protocol.expected_admission`
- `frozen_batch_inputs.prerequisites`
- `averaging_history_inputs.load`
- `frozen_batch_validation.gather`
- `frozen_batch_validation.grid`

`prerequisites` is imported into other modules; the defining source file is the
identity used here. Reading the code shows that `read_saved` checks admission
receipts, loads prior contexts and verifies saved worker rows and the complete
grid. It checks a replay receipt; it does not launch new training or call the
archive trajectory replayer. Some receipt checks recursively check earlier
receipts. That recursion is kept as an edge, not treated as a selected
nonrecursive partition.

The query reuses the [qualified reader](earlier-source-profile.md) and its entire
authenticated lossless graph. The original source, raw pair and units are checked
unchanged. Each selected definition must match its producer source hash, AST
line, name and argument list. Missing, duplicate or recursive selected frames
reject. All incoming and outgoing edges remain, with the original identities;
self time plus all direct child times must recover inclusive time within the
existing absolute 1e-7-second tolerance. The output retains every original frame
and edge, without a top-N cutoff, and refuses an existing output directory.

These are the same historical **elapsed-stack seconds** as the earlier report.
They include blocked waits and profiling overhead. Nested pages overlap, and a
shared callee's total covers several callers. A caller's direct edge identifies
its own calls; grandchildren cannot be divided between callers from aggregate
rows alone. This is dependent exploratory evidence, not current CPU, predicted
savings or an independent confirmation of the earlier result.

## Browse or reproduce

After the checked query source is published:

```sh
.venv/bin/python scripts/inspect_archive_reader.py
.venv/bin/python scripts/inspect_archive_reader.py --function 1
.venv/bin/python scripts/inspect_archive_reader.py --function 4
.venv/bin/python scripts/inspect_archive_reader.py --output results/runs/archive-reader-local
```

The numbered view shows every direct edge. Export writes the complete function
and caller tables, the seven selected function rows and their edges, a numerical
summary and the original authentication log. Use a fresh folder. The binary
profile is hashed for provenance and never loaded.

## Checks and next decision

Independent fixtures cover caller sharing, changed source/coordinates, duplicate
identities, recursion, conservation, output retention and raw-input mutation.
Before extraction, publish the fixed source and config with their checks. Both
actual supported runtimes must reproduce all five numerical exports exactly,
with all 104 construction/profiling targets blocked and raw inputs unchanged.
Retain partial or failing outcomes. Complete applicable local, optional and hosted
checks before a history-preserving merge.

No new profiler, solver or poker trajectory is run. No caching, verification
shortcut or strategy change is introduced. The 912.54/900-second forecast and
2.390%/1% known-game accuracy failures stay failed. The result will guide the next
code inspection; any later optimization needs its own correctness and current
measurement evidence.

All 53 focused cases pass on both actual runtimes. Strict typing passes for 825
files, lint/format checks pass, and 532 local documentation destinations pass.
Both 104-target guard setups and four exact entry-exit fixtures pass.
[Source-check records](../results/archive-reader-edges/source-checks/manifest.json)
retain initial import/fixture/typing failures and their corrections.
Selected historical values are not yet extracted. Codex assisted with the query,
tests and documentation; no personal practice or human time is inferred.
