# Test range weights inside the saved river groups

Prospective issue #4 comment
[6799471551](https://github.com/jimmy-sim/poker-ai/issues/4#issuecomment-6799471551)
registers this read-only question before implementation or output. The
[config](../configs/river-range-reweighting.json) binds the complete
[saved-decision](own-opponent-decisions.md) and
[fixed-turn continuation](turn-continuations.md) reports. Their original
learning failure, source, seeds, caps and defaults remain unchanged.

## Question and fixed controls

The two important turn calls need finer river information against one saved
opponent. Do different betting-conditioned beliefs about the opponent's cards
account for action conflicts inside the shared river groups? Or do conflicts
remain after replacing those beliefs with the same compatible declared prior,
while keeping future action values fixed?

A **posterior** is a range updated by the observed public betting history. Here
it comes from integrating the same saved opponent's possible card combinations
and action probabilities, not from observing its actual private cards. The
compatible prior uses only the declared weights and known card removal. This
intervention is a local mechanism test; it does not define a new globally
consistent poker strategy.

The declared ranges are given at the spot root. The fixed earlier public prefix
sets that root's pot, stacks and board; this diagnostic updates weights only
from actions inside the enumerated spot. It does not infer a preflop range from
the historical prefix or from real opponents.

Retain both known games, all three seeds, all four methods, final10m primary
linear averages:24profiles and48responding-seat conditions. Each uses both
original own fine-best and restricted-best **river suffixes**, against its same
saved opponent:96suffix conditions. Compare actual posterior and compatible
prior in each:192local panels. These are **not**192new root values. Retain every
owned exact river row, legal action and compatible declared combo, including
unsupported cases. A top10display never selects the assessment.

For each local panel, report costs/conflicts under the saved declared partition
and its full-static-probe refinement: own full rank, ordered range compatibility
and ordered showdown relations. These are diagnostic controls, not deployed
features. Keep group denominators separate and retain signed changes.

## Mixture and weighting

At river information row I, group all hidden histories by the opponent's
declared combo. Evaluate each action using the frozen own suffix and saved
opponent future; check within-combo history consistency. Recompose the conditional
action value as the sum of posterior(combo|I) times that combo's continuation
value. The actual mixture must match the original own conditional-value
calculator within1e-9chips. Replacing only the weights with the compatible prior
keeps those same continuation values. Never maximize separately by hidden deal.

Use one fixed game/seat weighting: chance times both players' uniform-action
full reach, summed at own river infos and normalized **before** support filtering.
Compare the same positive actual-opponent-support rows in both range panels.
Do not renormalize after filtering; report the supported weight. Zero actual
support stays explicit and unranked. Saved own reach is separate: a counterfactual
decision can have positive support even when the saved own strategy avoids it.

Local sharing cost is sum(w_i max Q_i) minus max(sum(w_i Q_i)), summed over
groups. Its unit is chips per decision under this declared weighting. It is not
root EV, exploitability, additive game loss or gain after retraining. A strict
conflict means no legal action lies within1e-9chips of the best action in every
supported row of that group. Floating calculations use1e-9chip and1e-12unitless
checks; no new effect-size threshold is chosen after outcomes.

## Acceptance before interpreting results

- Complete24/48/96/192 inventories and all owned river rows/actions/compatible
  range entries. Bind prior config/manifest/summary, original own/native/archive
  hashes and current source. Replay original own math and verify saved reply
  fingerprints. Existing scientific source/data remain immutable.
- Check combo/history consistency, blocker zeros, actual/prior normalization,
  exact menu/range indices and mixture reconstruction on both target signs.
  Replies and conditional values respect own legal information. Unsupported
  rows are never used to invent a preference or improve coverage by filtering.
- Independent analytic/recursive terminal mixtures catch hidden-deal
  clairvoyance, wrong labels/weights, missing/duplicate rows, nonfinite values,
  zero support, identical-weight zero change and singleton zero cost/conflict.
  Refining groups cannot increase convex sharing cost beyond tolerance.
- Block learner/reference constructors; no imported reference strategy, new
  policy/feature deployment or agent/default change. New calculations have no
  new independent audit. A removed conflict is only a fixed-suffix local effect,
  not a proof that a posterior feature will improve learning or generalize.
- Separate900-second data-only command clock starts at thin entry before
  numerical imports and includes complete replay/analysis/writes; interpreter
  startup is excluded. Original7200/900learning/audit caps and gates stay fixed.
  Refuse existing output; retain each complete profile before advancing, plus
  partial/failure records. Preserve unfavorable results.
- Relevant full local bases, focused optional checks and both hosted source/
  final-artifact jobs pass before merge. A cached hash-checked terminal reader
  shows range order, compatible prior/posterior, own/public observations, action
  values, support and fixed-suffix/local-weight scope. No live game inputs.

## Status and next decision

Implementation checkpoint: 72 focused tests pass in8.44seconds. Independent
terminal sums check both target signs, hidden-history mixtures, declared range
order and own-prefix exclusion. Uniform UNIT policies in both own poker games
reconstruct all conditional river values/support and preserve fixed suffixes.
Cache/schema tests reject missing/duplicate rows, wrong weights/menus/groups,
nonfinite values, tampered publications and changed lazy-loaded detail bytes.
Actual partial-profile integration retains completed evidence after interruption;
learner/reference construction is blocked before input replay. Cached terminal
browsing distinguishes both own suffixes, actual versus prior weights and local
scope. Whole-repository lint/format/strict typing pass. These tests do not contain
a measured saved-policy range result or a deployed feature.

Complete local runtime/optional/hosted source checks and the actual complete
comparison remain pending. After the full panel, determine whether posterior replacement
removes the relevant conflicts or whether frozen future-policy/board effects
still suffice. Do not drop a seed, alter the failed original gate or deploy a
feature on a diagnostic result. A later candidate needs its own prospective
learning and source-bound admission. Codex assists; human practice/time are
recorded only when actually reported.
