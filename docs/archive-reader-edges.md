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
The source was public before the selected values were extracted. Codex assisted with the query,
tests and documentation; no personal practice or human time is inferred.


## Historical result — November 17

After checked source `b26374f` was published, both actual data readers complete.
The five numerical exports are byte-identical across Python 3.11.17/NumPy 2.4.6
and Python 3.12.15/NumPy 2.5.4. Both runs retain all 2,354 frames and 5,640 edges,
block 104 construction/profiling targets with zero calls, and preserve all 15
raw producer files. [Actual receipts and equality hashes](../results/archive-reader-edges/data-checks/manifest.json)
retain the complete executions.

| Fixed function | Calls | Self seconds | Inclusive seconds |
| --- | ---: | ---: | ---: |
| `reduced_study_run.read_saved` | 2 | 0.000158625 | 125.551543 |
| `reduced_study_protocol.require_admission` | 2 | 0.000514667 | 107.961533 |
| `reduced_study_protocol.expected_admission` | 2 | 0.000803625 | 107.960776 |
| `frozen_batch_inputs.prerequisites` | 14 | 0.004032626 | 121.853417 |
| `averaging_history_inputs.load` | 14 | 0.193814472 | 121.683246 |
| `frozen_batch_validation.gather` | 4 | 0.001370075 | 0.001725667 |
| `frozen_batch_validation.grid` | 2 | 0.0004573 | 0.041549542 |

| Caller of prerequisites | Calls | Direct edge inclusive seconds |
| --- | ---: | ---: |
| `reduced_study_run.read_saved` | 2 | 17.3613196 |
| `frozen_batch_protocol.read_profile` | 12 | 104.492098 |

Largest absolute child/self residual: 1.42108547e-14 seconds.

The reader's own direct admission-check edge is 107.961533 seconds across two
calls; its direct prerequisite edge is 17.361320. Admission reconstruction's
`expected_admission` frame records four direct saved-reduction receipt checks
at 107.683864 seconds. These are nested instrumented totals, not quantities to
add. The small row-gathering and grid checks are not the large direct component.

The prerequisite function serves fourteen calls: two from the archive reader
and twelve from `read_profile`. Its global child `averaging_history_inputs.load`
includes all fourteen, so that aggregate must not be charged to the two direct
reader calls. Its downstream saved-reply checking, trace validation and decoding
also serve those shared callers; no caller-specific grandchild cost is inferred.

**Next decision:** follow the nested receipt/context checks before proposing a
cache or another instrument. The earlier full-context-copy result remains
rejected; these historical values do not establish that reuse would be safe,
what it would save now, or whether the current compute forecast would pass.
A current optimization needs fresh correctness and measured evidence.

[Every selected edge](../results/archive-reader-edges/report/selected-edges.csv),
[all frames](../results/archive-reader-edges/report/all-functions.csv),
[all callers](../results/archive-reader-edges/report/all-callers.csv),
[full-precision summary](../results/archive-reader-edges/report/summary.json).
Regenerate the displayed table after exporting to a fresh folder:

```sh
.venv/bin/python results/archive-reader-edges/data-checks/summarize.py.txt --report results/archive-reader-edges/report --output results/runs/archive-reader-tables.md
```

The real-data regression uses a fresh child even when optional tests have loaded
OpenSpiel in the parent. It checks parent refusal, all 104 construction blocks,
actual runtime and five exact exports. Complete final repository checks remain
pending. There is no new speed, forecast or playing-strength admission.

## Three questions this step should answer

1. **Is the grid validator expensive?** Its direct historical edge is small;
   the admission reconstruction is much larger in this saved profile.
2. **Why not assign all prerequisite time to the reader?** Twelve of its fourteen
   calls come from another caller. The incoming edges preserve that distinction.
3. **Can the checks now be removed?** No. They establish source/result identity.
   Any safe reuse must preserve their meaning and detect changed inputs; this
   saved analysis neither removes them nor proves a speedup.


Pre-final verification: all 54 focused cases pass with real OpenSpiel deliberately
preloaded in the parent on both runtimes (1.31/1.29 seconds); the fresh children
retain all 104 blocks and five exact exports. Strict typing covers 825 files,
lint/format and 539 documentation destinations pass. Full final checks remain
pending. These are software/data checks, not new training or strength evidence.
