# Offline saved-strategy viewer — prospective November 9

Issue #4 now has independently audited saved-current and average-policy results.
The next software milestone makes the action tables inspectable. This plan is
published before implementation. It does not run a new learning experiment.

Select two retained OWN policies by known game, encoding, regret rule, seed,
work label, batch size and current/uniform-average/linear-average readout. Verify
the complete published diagnosis/source/native receipt chain and archive hashes;
verify selected policy bytes, source identity and action menus. Never construct
a learner or a reference solver. Preserve all earlier scientific source/data.

For the selected seat, rank its information rows by the unweighted action-
probability L1 difference, sum(abs(left-right)), in [0,2], then by row index for
stable ties. This is a distribution difference, NOT EV loss, reach weighting,
importance, measured strength or a best-action recommendation. Include zero
rows. Display both saved action distributions and actual work/update counts.
Equal work labels do not guarantee equal charged overshoot or update counts.

Show a representative acting-player observation: only own hole cards, public
board, street and pot. Disclose that a compressed row can have multiple exact
members and that the representative does not summarize every member. No
opponent private cards, live poker input, play automation or policy edits.

Default prints one selected rank and exits. Optional terminal mode accepts n/p/q
for next/previous/quit; EOF exits and invalid input explains the available keys.
Load validated data once for browsing. No scientific cap/seed/gate changes.

Acceptance: independent self-zero, symmetry, [0,2] bounds, deterministic tie/
owner ranking, malformed/illegal/nonfinite probability and menu checks; unique
selection/work/readout validation; representative actor/privacy guards; scripted
n/p/q/EOF/invalid navigation; constructor-blocked actual saved-archive CLI checks
on both runtimes. Run relevant base/optional suites, lint/format/strict types and
hosted CI; update work log and plain-English journal step40 with actual outcomes,
terminal examples and limits. No new performance/default/fresh/global claim.

## Implemented viewer and first actual checks

The viewer validates the complete published source/own/native receipt chain,
scans immutable archive inventories and verifies both selected policy hashes
and action menus. It displays only the acting player's observation. It loads
once; checking the full saved chain can take a minute or more before browsing.
No learner or reference is constructed, including in the actual saved-data tests.

Twenty-four focused fast tests pass, including an independently summed L1,
self-zero, symmetry, opposite-action bound2, owner/tie ordering, bad mass/menu/
selection/context and navigation/EOF cases. Three actual archive/card/navigation
tests pass71.81s on base3.11. The first real CLI example is a river row with own
Tc Td and public Ts 9s 4d 2h Js: latest folds with probability1 while the linear
average calls with probability approximately1. This is an unweighted difference
example, not proof that either action is best or that this row matters on-path.
Both readouts have80,741updates and10,000,119charged node visits.

Full base/optional suites on both runtimes and final hosted CI are running. The
first two fixture failures assumed Kuhn had no padded third column; the fixture
was corrected before source publication. The inherited legal mask is numeric,
so the viewer now uses the existing tree policy validator rather than duplicating
it. These were software-development findings, not failed research outcomes.

After merge, from your existing project checkout:

```sh
.venv/bin/python scripts/inspect_batch_strategy.py
.venv/bin/python scripts/inspect_batch_strategy.py --interactive
.venv/bin/python scripts/inspect_batch_strategy.py --left linear_average --right linear_average --left-batch 1 --right-batch 4
.venv/bin/python scripts/inspect_batch_strategy.py --seat 1 --rank 2
```

The default compares current versus linear average for B4, medium known game,
signed regrets, first seed and10m work label. `--help` lists retained choices.
In interactive mode use n/p/q; it stops at the first/last rank instead of wrapping.
EOF also exits. Nothing is written to an agent or published evidence.

## Questions to explain the tool

**What does L1=2 mean?** The two distributions put all their probability on
different actions. Identical distributions give0; this says nothing about EV.

**Why rank rows if some are unreachable?** This is an honest distribution
inspection tool, not an impact ranking. It includes every owned row, labels the
absence of reach weighting, and does not choose a training remedy from the list.

**Why show only a representative board?** A compressed row can share one
distribution across several exact observations. Showing one observation makes
the table readable, but cannot establish that every member prefers one action.
The example uses only own cards/public board and declares the member count.

## Complete local verification

Both full base suites pass1,897tests with24optional skips (270.11/257.66s).
Both full optional suites pass1,930tests (298.10/285.85s). Three actual archive/
privacy/navigation checks pass on both base runtimes65.71/62.01s, with learner
and reference constructors blocked. The default3.11 CLI and scripted3.12n/p/q
CLI both run on real retained policies. Ruff/format541 and strict445 pass.
Published source and final hosted CI remain distinct from local checks.

The underlying diagnosis PR36 is mergedde4755d after both final hosted jobs
42635166354pass. Main2published tests pass0.32s; full216/1728own replay has zero
error47.488662458s, native receipt validates, all6numeric files are byte-identical.
All10unrelated modified outputs retain their original hashes. No new training
or playing-strength claim follows this viewer.
