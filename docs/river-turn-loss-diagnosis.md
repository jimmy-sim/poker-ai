# Prospective diagnosis of the new medium/dry turn loss

**Issue #4; November 23, 2026 (PST).** This read-only plan precedes any new
candidate-ranked decision trace or collision count. [PR #105's fixed test](river-full-broader-spots-result.md)
is **negative**: the unchanged full expected candidate reached 0.025118160532
initial-pot exploitability on the new medium/dry card/range input, versus
0.015306735247 and 0.017145152714 for two of its three matched-work B4
controls. Its final turn gain is 0.861096 chips, versus 0.043158 on the river.
The earlier [PR #98 diagnosis](river-generalization-diagnosis-report.md)
found **zero turn collisions on a different known medium/dry input**. These
facts make collision versus training behavior an important unresolved cause;
neither proves an explanation for the current finite game. Both inputs and
their public betting templates are known and previously inspected.

## Fixed question and inputs

Which exact turn decisions contribute most to the saved full expected
candidate's final best-response gain, and do they share an abstract
information row with another exact decision? Compare the same decisions at
the earlier fixed work checkpoints and with every saved B4 control. A
diagnosis can rule out a collision mechanism in this finite game if no
collisions exist; it cannot prove that more work or a new representation would
improve play.

Read only the published PR #105
[own](../results/river-full-broader/own/manifest.json),
[native](../results/river-full-broader/native/manifest.json), and
[report](../results/river-full-broader/report/manifest.json) archives,
the [one-time freeze](../configs/river-full-broader-freeze.json), and exact
source on main merge `c84302b58c8ee18220d39a2d8130abae803a779a`.
Their SHA-256 pins are in the [machine contract](../configs/river-turn-loss-diagnosis.json).
Use only `full_new_medium_dry_oop`, candidate seed 0 and B4 seeds
**20261511, 20261512, 20261513**, all **linear-average** policies at the
first complete 100k, 1m and 10m charged-node crossings. This is exactly 12
saved policies and 24 responding-seat traces. No new training, checkpoint,
seed, case, reference output, strategy or gameplay action. Low/wet is
context from the published parent result only; it is not a case-selection
alternative. Retain partial evidence if a declared input is missing or bad.

## Ranking, metrics and decision rule

For each policy, compute exact-information best replies for seats 0 and 1
against the **other seat's fixed saved policy**. The existing additive
`trace_losses` accounting divides total unilateral gain by two, matching
NashConv/2 exploitability in acting-seat chips. Verify both seats' row gains
sum to the saved policy's exact exploitability within **1e-9 chips**; verify
snapshot hashes, source/input/archive pins, native scalar error at most
**1e-9 chips**, zero recall violations and nonnegative accounting. A failed
identity or pin is a correctness failure, not a poker-strength result.

Rank **all final candidate turn exact rows** by additive gain descending,
breaking ties by exact information index. Publish the top ten turn rows and
top five river rows ranked separately. Fix these 15 exact indices before
looking at controls or earlier checkpoints; display the **same** indices
for all four arms at all three work labels, including zero-reach cases.
Also report each arm's aggregate turn and river gain, top-ten turn share,
positive-reach count, whole coverage and actual charged work from saved
receipts. Candidate-minus-each-B4 and median turn/river differences are
descriptive matched-work values; the single deterministic candidate is shared
among three dependent contrasts, so they provide no candidate-seed confidence
interval.

Count exact acting information rows grouped by the frozen
`q8_turn_exact_river` key separately on turn and river: collided abstract
groups, collided exact rows, and the candidate's final turn loss and
saved-prefix reach on collided rows. For each selected decision show board,
own cards, acting seat, legal concrete actions, saved probabilities,
chance-times-opponent counterfactual reach, full saved-prefix reach,
best-reply-continuation alternative-action values and additive gain.
Values use the saved opponent and an optimized reply continuation; local
scores are not universal poker advice or an estimate of retraining effect.

**Interpretation fixed now:** if turn collision count is zero, turn grouping
cannot explain these measured losses. If collided turn rows exist and account
for at least **50%** of candidate final turn loss with at least one in the
top ten, flag grouping as a *prospective test candidate*, never as a proven
cause. Otherwise prioritize the work-checkpoint trajectory and algorithmic
convergence as hypotheses. Three checkpoints cannot establish asymptotic
convergence or distinguish every implementation defect. This diagnostic does
not revise the parent negative classification, promote a default or tune the
candidate. Any next training comparison must use a distinct prospective
protocol and newly selected inputs, not call this evaluated case unseen.

## Compute, qualification and stop

The earlier read-only diagnosis completed 24 responding-seat traces in
7.170 seconds on a similarly sized known medium/dry game. Replaying 12
published policies and accounting for collisions adds work; plan **180
seconds** and enforce a **900-second whole-process hard cap**, including
startup, archive verification and report writing. This forecast is an
estimate, not permission to extend the cap. Run the one fixed diagnostic
once after publishing this protocol, isolated source, focused tests and
exact-source local base/optional Python 3.11/3.12, all-file hooks and hosted
CI. A small fictional proof must confirm trace-additivity and key grouping
before the real saved policies are read. Retain every completed/partial trace
and failed log. A timeout, missing pin or numerical gate failure stops this
diagnosis; no replacement input, expanded cap or favorable retry.

Publish the raw report and a plain-English interpretation, then finish
applicable final exact-source local/optional/hosted checks and solo review.
No new OpenSpiel comparison is needed: all selected saved policies already
have pinned scalar audits. Reference strategies remain comparison-only and
never enter this diagnostic's input. Codex assisted; human hands-on time and
personal learning were not reported.
