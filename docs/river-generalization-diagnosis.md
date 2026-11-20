# Prospective read-only diagnosis of the medium/dry river study

This plan is published before computing any new decision ranking. It extends
[draft PR #98](https://github.com/jimmy-sim/poker-ai/pull/98) and issue #4
without changing its experiment. The bounded comparison remains **negative**:
candidate medium/dry median/worst exploitability of 3.566% and 3.954% failed
the fixed 1%/2.5% gates. Final local base qualification is **incomplete**,
with retained 20-second spawned-fixture timeouts; hosted CI on the final
receipt now passes. The candidate is neither merged nor promoted.

## Definition of done and frozen inputs

The [machine-readable plan](../configs/river-generalization-diagnosis.json)
pins the saved medium/dry spot, own archive, native archive and all-readout
report by SHA-256. Historical `src/`, river-strength source, original
generalization adapters, receipts and policy snapshots remain unchanged.
This step reads published policies and scores only. No new training, ablation,
reference strategy or gameplay action is executed.

Inspect candidate **linear-average** snapshots at first complete 100k, 1m
and 10m node work for every original seed 20261371–73, and control
linear-average snapshots at 10m for the same seeds. These 12 saved policies
give 24 responding-seat traces. Existing current and uniform-average report
rows may be compared as context, without new traces. No seed, checkpoint,
street or row may be replaced after seeing its outcome.

## Fixed ranking and interpretation

For each saved policy, compute an exact-information best reply separately for
seat 0 and seat 1 against the **other seat's fixed saved policy**. At each
responding information row, the existing `trace_losses` helper uses the saved
policy's full prefix reach and the responding seat's best-reply continuation
to assign an additive unilateral loss in chips. Divide by two because the
published exploitability is NashConv/2. Check that summing all exact-row
contributions across both seats reproduces each saved exploitability within
1e-9 chips. The primary ranking is the **mean of the three fixed final
candidate seed contributions per exact row**, descending, with exact-row
index breaking ties. Show the top ten across both seats and the top five for
every final seed and responding seat, including zero-support counts. The top
ten is descriptive; no threshold or intervention is inferred from it.

For representative rows report acting seat, own cards, five-card river board
or four-card turn board, legal concrete actions, saved action probabilities,
chance-times-opponent counterfactual reach, full saved-prefix reach,
best-reply-suffix alternative-action values in acting-seat chips, and the
additive contribution. A separate **local diagnostic** may show alternative
action values if the saved policy continues after the action. That local
one-step score is not additive exploitability and may overlap across nodes.
Hidden histories are summed within the acting player's information row before
maximizing; opponent private cards are never available to the acting policy.
None of these values is universal poker advice or the expected effect of
retraining.

Break down exact additive contributions by turn and river using observed board
length. Count candidate abstract-key collisions by street and their reach and
loss where present. Compare each candidate checkpoint and the fixed final
control on the same exact game. A change over work may suggest training or
convergence behavior, but three checkpoint snapshots cannot isolate its
cause. Check snapshot hashes, source/input pins, score and response identities,
nonnegative trace accounting, zero recall, and the already published native
scalar tolerance. These can detect specified integration defects; they cannot
prove no implementation defect exists. Label unsupported explanations as
hypotheses.

## Budget, publication and stop

The one read-only diagnostic has a **900-second wall cap including startup,
verification, all 24 traces and report writing**. The existing 287-second
12-path training and 55.6-second 108-scalar native audit provide scale for a
forecast below this cap; they do not guarantee diagnostic runtime. Publish
this plan before ranking any node. Publish tested
isolated diagnostic source before the one run, then retain complete or partial
rows and a reproducible report. A failure or timeout stops with evidence; do
not increase the cap or retry for a favorable explanation. New training or an
ablation would require a separate prospective protocol and user
authorization. Stop after one report and recommend one bounded next
experiment, or state that the saved evidence cannot distinguish causes.

Codex assisted; human hands-on time was not recorded.
