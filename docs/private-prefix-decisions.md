# Which saved decisions account for the remaining weakness?

November 10, 2026. This post-hoc diagnostic follows the complete negative study
and its component report. The panel is registered before generating local
decision tables in issue #4, comment 6775611715.

Keep all three fixed seeds and all B1, IID B4 and stratified B4 controls for the
medium-game, q8, signed, final ten-million-node, linear-average primary: nine
saved profiles and both responding seats. No new poker training runs.

Use the existing own exact best-response trace. Retain every owned exact row
and reply profile in a detail archive. Summarize TURN/RIVER losses, and show the
five merged groups with greatest total loss per responding seat. Within a
group, display up to four examples using the existing deterministic distinct-
action-first selection. Preserve the complete archive even when examples are
shorter than a group.

These row losses add to TOTAL unilateral reply gain against a fixed saved
opponent. They do not isolate the extra-information component, establish an
irreducible representation floor, or measure a causal benefit from retraining.
Averaging the two seat gains gives exact exploitability in the saved game.

Acceptance: complete nine-profile/eighteen-response inventory; source, own,
native, raw-journal and whole-clock checks; constructors blocked; policy hashes
and roots match independently audited source; every row/street/root identity
within 1e-9 chips; all numbers finite; input arrays unchanged; deterministic
ranking; fresh outputs and partial retention; relevant tests and both hosted
jobs before merge. Keep the frozen model source and all historical data intact.

Next decision: use concrete contrasting actions to define a controlled future
question. Do not repeat unchanged training until it appears favorable. No
further long trajectory starts in the midnight–noon window.

## Implementation checkpoint

The experiment-specific entrypoint reuses the frozen archive reader and the
existing own reply analysis. It checks the complete bound study/native receipt
with all learner/reference constructors blocked, restores the nine exact saved
policies, and compares trace roots with their independently audited metrics.
Every original policy array is fingerprinted before and after analysis.

Sixteen fictional checks pass (0.58 seconds): complete panel and controls,
missing/duplicate/typed identities, both payoff signs, root/street/nonfinite/
negative-loss failures, separate river-switch semantics, preserving an existing
output before reading, cached-report/input tampering and all browser controls.
Ruff, formatting and strict typing pass. Full local/hosted checks and actual
decision results remain pending.

Run .venv/bin/python scripts/trace_private_prefix_decisions.py to perform the
complete saved-data replay and write a fresh report. Then run
.venv/bin/python scripts/inspect_private_prefix_decisions.py --interactive to
check the cached report/input hashes and browse without rerunning poker analysis.

Use n/p to change group, s to change seed, o to change method, t to change
responding seat, and q to quit. The displayed responding cards belong to the
best-response player; saved probabilities are the strategy being diagnosed.
Counterstrategy choices are conditional on that fixed saved opponent and reply
continuation.

## Review safeguards before the final saved-data reproduction

The first complete report is retained with exact source at commit b64822f and
results/private-prefix/decisions-initial57f. Its nine profiles/eighteen responses
finish in 358.294262 seconds; initial base suites pass 2,294 tests each and
optional suites pass 2,350 each. This is a complete initial diagnostic, not a
new learner or a training retry.

Review adds explicit per-seat gain identities, full owned-row/menu/support
checks and a deterministic detail file for each completed profile before
advancing. A later failure retains those details and the cumulative summary.
The cached browser also handles a seat with no positive-loss groups. Its new
zero-loss fixture initially exposed an indexing error, which was corrected.
All 26 focused checks now pass (0.48 seconds), including canceling-seat errors
and interrupted-detail retention. Final suites and the saved-data reproduction
are next. No scientific source, strategy, seed, cap or threshold changes.

## Recorded result — November 10

The safeguarded replay completes all nine profiles, eighteen responses and
30,024 owned exact-row records in 357.455549 seconds. Learner/reference
constructors are blocked, every audited root and row/street identity passes,
and the saved arrays stay unchanged. The final summary and full detail archive
are byte-identical to the retained initial version; the added safeguards change
verification and interruption retention, not the measured outcome.

The table shows seat-balanced total and street contributions in **chips**,
against each fixed saved strategy. Turn plus river equals total up to roundoff.

| Seed | Method | Total | Turn | River |
| --- | --- | ---: | ---: | ---: |
| 20261301 | B1 | 1.612973 | 1.570235 | 0.042738 |
| 20261301 | IID | 1.005585 | 0.972863 | 0.032722 |
| 20261301 | stratified | 0.832227 | 0.802346 | 0.029881 |
| 20261302 | B1 | 1.982388 | 1.905523 | 0.076865 |
| 20261302 | IID | 0.135103 | 0.126583 | 0.008521 |
| 20261302 | stratified | 1.618149 | 1.590942 | 0.027207 |
| 20261303 | B1 | 1.106993 | 1.073060 | 0.033932 |
| 20261303 | IID | 1.205810 | 1.169741 | 0.036069 |
| 20261303 | stratified | 1.168461 | 1.125874 | 0.042587 |

Most total gain appears at turn decisions. For responding seat 1, every
profile's largest group is row 819: pocket 9c 9d on Ts 9s 4d 2h, facing a bet.
This group has only one exact member. A large turn loss therefore does not by
itself show missing turn-card distinctions. Best-response suffixes include
future river choices.

For the unfavorable candidate seed 20261302, this group contributes 2.123817
chips to seat 1's 3.205207-chip unilateral gain. The saved strategy folds with
probability 0.995270. Under the exact own best-response continuation, calling
has value -12.721224 chips versus folding's -18 chips. Those are net target
chips conditional on this fixed opponent and reply continuation; they are not
general poker advice. Both players' gains are averaged for exploitability.

This does not contradict the large separate river-switch diagnostic. A total
loss trace attributes gain along the saved prefix and optimized suffix. The
river switch holds an exact reply prefix and changes river rows. These answer
different questions and must not be added together.

The [full report](../results/private-prefix/decisions/) retains all seeds,
controls, top groups and owned rows. Every completed profile also has a
deterministic partial detail file, so a later failure can preserve earlier work.

Both final local base suites pass 2,304 tests, 47 skipped and 148 deselected,
in 380.77 / 368.58 seconds. Both optional suites pass 2,360 tests, 148 deselected,
in 413.90 / 402.76 seconds. Cross-runtime saved-data reproduction and final
hosted CI are separate checks.

## What to try in Terminal

The committed cached report loads without training or a full poker replay:

```sh
cd /Users/jimmysim/Projects/poker-ai
.venv/bin/python scripts/inspect_private_prefix_decisions.py --interactive
```

Use n/p for groups, s for seeds, o for methods, t for the responding seat and q
to quit. To inspect the large seat-1 example directly:

```sh
.venv/bin/python scripts/inspect_private_prefix_decisions.py --seed 20261302 --role stratified --seat 1
```

Full saved-data reproduction takes several minutes. Use a clean research
checkout, retain existing outputs, and choose a fresh destination with
--output results/runs/private-prefix-decisions-local. The cached browser checks
the committed report's hashes; it is separate from that full replay.

## Three questions to explain

1. **Why can a turn row show loss from river limitations?** Its action values
   include future choices. Improving a later continuation can make calling now
   preferable even when the current turn group has no merged card situations.
2. **Do row losses equal extra-information value?** They sum to total unilateral
   reply gain. Extra-information value compares exact and constrained replies;
   the two decompositions are different.
3. **Do 30,024 rows establish general strength?** No. They are dependent records
   from nine saved profiles on one known restricted game and three fixed seeds.
   They locate decisions to investigate without establishing a full-game edge.

Next, compare exact, constrained and hybrid river continuations on all
previously ranked groups before choosing a representation or training change.
