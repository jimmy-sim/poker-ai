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
