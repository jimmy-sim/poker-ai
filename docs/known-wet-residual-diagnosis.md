# Prospective diagnosis of residual exact-turn losses

**Issue #4; November 24, 2026 (PST).** This protocol precedes any new
candidate-ranked decision trace. [PR #110](known-wet-turn-mechanism-result.md)
history-merged with a **negative** strength result on one already known
medium/wet out-of-position game. At equal 10,117,956 charged nodes, exact
acting turn information reduced final linear-average restricted-game
NashConv/2 from 2.226492 to 1.072987 chips, but 0.029805 initial pots
still missed the frozen 0.01 final and 0.025 worst gates. Its residual
best-response gain was 0.804478 chips on turn and 0.268508 on river.
The final current policy had *higher* turn gain (3.171919 chips) but
*lower* river gain (0.126300 chips) than the final linear average. Those
already published totals motivate a closer saved-decision diagnosis;
they are not new outcomes or a reason to revise PR #110's gates.

## Fixed question, inputs and definition of done

Are the exact-turn candidate's remaining turn and river best-response gains
concentrated in a few exact acting decisions, and which of those decisions
account for the observed current-versus-average river difference? This can
identify a bounded next training hypothesis; it cannot establish that a
different average, more work, or another representation improves play.

Use only the 12 already published [PR #110 own policies](../results/known-wet-turn-mechanism/own/manifest.json):
q8-turn/exact-river control and exact-acting-turn/exact-river candidate,
PCG64 seed **0** each, first complete **100k, 1m and 10m** charged-work
crossings, both **current and linear-average** readouts. The sole input is
the already structurally and outcome-inspected `Qs Kd As 3c` turn-start
game in the [parent protocol](known-wet-turn-mechanism.md). All twelve
policies, not a favorable subset, are fixed. Their [native scalar audit](../results/known-wet-turn-mechanism/native/manifest.json),
[report](../results/known-wet-turn-mechanism/report/manifest.json) and
[final check receipt](../results/known-wet-turn-mechanism/final-checks/manifest.json)
are prerequisites pinned by SHA-256 in the [machine contract](../configs/known-wet-residual-diagnosis.json).
No new training, reference strategy, policy change, checkpoint, seed,
spot, or default is allowed. The definition of done is one complete
reproducible report or a retained failed/partial diagnostic under the cap,
with its numerical and source checks reported separately from poker
interpretation.

## Frozen ranking and readouts

For every saved policy, compute exact-information best replies for seats
0 and 1 against the other seat's **fixed saved policy**. Use the existing
additive trace convention: divide unilateral row gain by two, so all exact
row contributions sum to NashConv/2 in **acting-seat chips**. Verify the
two-seat row sum against each saved own exploitability within **1e−9 chips**,
nonnegative contribution up to **1e−12 chips** numerical slack, policy
snapshot and metadata hashes, zero recall violations, exact source and
archive pins, and previously audited own/native scalar error at most
**1e−9 chips**. Failure is a correctness stop, not a strength result.

Rank **all** final candidate **linear-average** exact turn rows by
additive gain, descending, breaking ties by exact information index;
independently rank all final candidate river rows the same way. Freeze
the top **ten per street** from those two rankings, then show these same
20 exact rows for both arms, all three work labels and both readouts,
including zero-gain/zero-reach observations. No row may be replaced after
seeing a control or earlier-checkpoint value. Report each selected row's
acting seat, board, private cards, pot, legal concrete actions, saved
probabilities, chance-times-opponent counterfactual reach, full saved-prefix
reach, optimized-reply-continuation alternative-action values, and additive
gain. Give each arm/readout/work's full turn and river gain, positive-reach
counts, whole and post-initial-river coverage, work, memory and runtime
from saved receipts. Reconcile the full street totals to the prior report.

The predeclared descriptive split is **concentrated** on a street if its
final candidate-average top ten contribute at least **50%** of that
street's total gain; otherwise it is **diffuse**. Report both exact shares.
Compare those fixed rows across checkpoints and current versus average,
but do not call changes causal or asymptotic convergence: each readout
also has a different saved opponent and reach. The game begins on the
turn, and the candidate already has exact acting keys on turn and river;
verify that its exact-to-abstract mapping is an identity and that there
are no turn/river collisions. This finite game contains no modeled flop
decision, so it cannot test an earlier-street grouping explanation.
Numerical identity and existing independent scalar agreement can reject
specified integration faults, but cannot prove the absence of all defects.
Values assume this restricted game's saved opponent and optimized reply
continuation; they are not universal poker advice or the causal value of
one action swap.

## Compute, publication and stopping rule

The parent fixed report replayed exactly these **12 policies / 24 seat
traces** in **68.30351770902053 seconds** on the recorded Apple M4. The
predeclared conservative data-only forecast is
`2 × 68.30351770902053 + 120 = 256.60703541804106 < 900` seconds.
Verify and publish a separate admission record from the pinned parent
job state before the real diagnostic. There is **one 900-second whole-process
hard cap**, including startup, archive validation, all traces and report
writing; no budget extension or favorable retry. Retain partial traces,
events and failures. A failed source, mathematical, admission, timeout or
archive gate stops this milestone and is documented honestly.

Publish this protocol and machine contract before any new ranking. Put
implementation in new isolated modules with focused fictional trace and
ranking tests, then complete exact-source local base/optional Python
3.11/3.12, all-file hooks and hosted CI before a small fictional proof.
Publish tested source and proof, then admission, before the one saved-policy
diagnostic. Publish own diagnostic bytes and a plain-English report;
complete required final exact-report local/optional/hooks/hosted checks,
solo review and history-preserving merge. The existing pinned OpenSpiel
2.0.2 comparison is **comparison-only** and complete for all selected
policies; no new reference strategy or reference run is part of this
diagnostic. Any subsequent training experiment needs a separate prospective
protocol, fixed controls and compute gate. Human hands-on time and personal
learning were not reported.
