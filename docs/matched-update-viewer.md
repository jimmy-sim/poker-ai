# Inspect both compute axes and the saved decisions

Prospective data-only milestone, November 10, issue #4. The matched-update study
and independent audit are complete. This plan uses their published bytes; it
adds no training, reference construction, policy editing or admission.

## Acceptance before new report generation

- Pin the own/native receipt hashes in `configs/matched-update-viewer.json`.
  Validate complete original source/admission/archives and both complete-command
  receipts. Preserve all earlier scientific source and data.
- Join every 144 matched target/readout pair to its original B1 final endpoint.
  Emit all 288 self contrasts across equal-work-label and equal-update axes,
  plus all 2,304 fixed-target contrasts. Actual node work and updates stay visible.
  The 72 B1 final readouts are shared across batch comparisons, not new learners.
- Normalize chips by each versioned spot's initial pot. Report arithmetic means
  of all three declared seeds, raw values and complete groups. No confidence
  intervals, selected best seed/readout, default or fresh/global claim.
- Use explicit CSV column order. The frozen original renderer produces the same
  numeric rows after JSON replay but can reorder CSV columns; preserve that
  historical output and fix determinism only in this new presentation module.
- Three heatmaps show all game/encoding/regret contexts and both axes/batches,
  one per readout. Each has its own labeled color scale. Include complete self
  and fixed raw/group tables, provenance and a plain-English reading guide.
- The terminal browser selects one complete matched pair, ranks all owned rows
  by unweighted action-probability L1, and displays the same update count with
  actual unequal work. L1 is not EV loss or reach-weighted importance. Show only
  a representative own hand/visible board; do not present it as every group member.
  Load/validate once, show progress messages, then support n/p/q and clean EOF.
- Test units/signs/self-zero, joins, missing/duplicate seed groups, nonfinite
  inputs, canonical output order, invalid selections, row ownership and browsing.
  Replay actual archives with learner/reference constructors blocked. Complete
  relevant local base/optional checks on both Python versions and hosted CI.

Own/native scalar agreement checks the exported bounded games, not every engine
rule or equality to a solver's strategy. Games have tiny declared ranges; three
seeds and shared trajectories/readouts are dependent. This milestone reports
existing evidence and does not change the agent.

## Reading the two axes

Both sides are strategies produced by this project. B1 takes one sampled
traversal per target pass; B4 and B16 average larger frozen batches. The external
program checks scalar calculations; it is not supplying either strategy.

- `same_work_label`: compare the original B1 final policy with the batch's final
  policy at the 10-million-node budget label. The last complete update overshoots
  the label, so actual visits can differ slightly.
- `same_updates`: compare an earlier B1 prefix with the batch at exactly the same
  update count. B1 usually spends much less work here; the actual ratio is shown.

A self delta is B1 minus batch exact exploitability, in percentage points of the
spot's initial pot. A negative value favors B1; a positive value favors the
batch. The heatmaps use blue for the former and orange for the latter. Each
readout has a separately labeled color scale. Compare numbers and colorbars,
not just colors across images. This is not a win rate or a confidence interval.

Fixed-target EV uses the responding seat's sign and keeps the opponent frozen.
A positive EV delta favors B1 against that particular opponent. Gain has the
opposite sign. That is a different question from security against a best
response; all opponents and both seats remain in the raw tables.

## Terminal commands after merge

Run each command on its own line at the normal shell prompt:

```sh
cd /Users/jimmysim/Projects/poker-ai
.venv/bin/python scripts/inspect_matched_updates.py --interactive
```

The first load verifies the full saved source/admission chain and archives and
can take several minutes. Progress messages distinguish validation from loading
the selected pair. It does not train or construct a reference solver. Once the
pair is in memory, type `n`, `p`, or `q` and press Enter. A displayed hand/board is
one representative of a shared information row. Large L1 means different action
probabilities, not that the decision is important or that either action is good.

Choose another declared comparison, or create a new report directory:

```sh
.venv/bin/python scripts/inspect_matched_updates.py --batch 16 --readout current --seat 1
.venv/bin/python scripts/summarize_matched_updates.py --no-plots --output results/runs/my-two-axis-report
.venv/bin/python -m pytest -q -m 'not slow' tests/test_matched_update_presentation.py tests/test_matched_update_viewer.py
```

Omit `--no-plots` in the research environment for all three PNG heatmaps. Existing
output directories are refused before loading. Old CSVs remain unchanged; new
exports use canonical columns and retain all raw values. Neither selecting a
viewer row nor examining a favorable seed selects a new agent default.

## Development checks before full source gates

29 focused checks pass, including an explicit tuple-keyed source regression.
The first actual reader test failed before producing a report because it assumed
string keys in an older loader's index. Rekeying the explicit archived row IDs
fixes the join; original scientific source and results stay unchanged. Both
failure logs are retained under `results/matched-update-viewer/development-failures/`.
Corrected actual constructor-blocked integration passes on both base runtimes:
1 test / 10 deselected, 206.54 s on3.11.17/NumPy2.4.6 and198.42 s on
3.12.15/NumPy2.5.4. It replays all144 policies/96ledgers/1152fixed targets,
extracts all288/2304 contrasts, writes all six numeric/text report files and
checks both an averaged medium/q8 pair and a current low/exact pair, both seats.
These checks do not establish a stronger agent. Complete local/hosted source
checks precede publication of the new summary output.
