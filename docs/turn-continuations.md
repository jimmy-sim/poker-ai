# Keep the turn fixed while changing the river continuation

This prospective issue #4 diagnostic follows [PR #50](https://github.com/jimmy-sim/poker-ai/pull/50)
and [its complete saved-policy result](own-opponent-decisions.md).
Issue comment [6798673089](https://github.com/jimmy-sim/poker-ai/issues/4#issuecomment-6798673089)
states the question and acceptance criteria before implementation/output.
The [config](../configs/turn-continuations.json) freezes the exact prior report
hashes and complete panel. No new learning or independent solver is authorized
by this data-only protocol; the original superiority failure remains unchanged.

## Question

Two turn calls account for much of the unfavorable seed's fine-reply gain.
Would those calls be valuable with the saved river play, with the best river
play allowed by the saved information groups, or only with finer legal river
information? A turn-attributed loss uses an optimal later suffix; it cannot
answer that question by itself.

## Complete frozen comparison

Retain both known games, all three original seeds, four methods, final10m primary
linear averages:24profiles, both responding seats,48conditions. For every
condition, compute four root values and all legal action values at **every own
exact turn row**, including rows with zero counterfactual support:

1. Original saved continuation.
2. Optimize only own river rows using the saved declared information partition.
3. Optimize only own river rows with fine legal own-card/public-board information.
4. The original complete fine best reply, which may also change own turn play.

The first three keep every target turn row and opposite-seat row bit-identical
to saved. The fourth is explicitly a different control. Fine-self's declared
partition is already fine, so its two river-optimization panels must coincide.
Top10turn groups affect browsing only; all owned turn rows/menus remain saved.
Order displayed groups by the prior report's turn-row loss, then group index.

All values are responding-seat net chips. Conditional action values integrate
chance times opponent reach across hidden histories **before** choosing an
action. They exclude own prefix reach. Unsupported rows retain zero values and
zero support and must not be ranked as meaningful decisions. These conditional
values are not additive root losses or general poker advice.

## Acceptance and safeguards

- Validate frozen prior config/manifest/summary, bound original own/native hashes,
  every prior cached output, current source and complete24/48/192root inventory.
  Replay the complete original own math and retain prior native comparison scope.
- Masked own dynamic programming preserves perfect recall and all unselected
  policy rows. Reject wrong-seat/non-boolean/wrong-shape masks and invalid policy.
  Use the exact first legal maximizer after information-set aggregation.
- Check source baseline/full-reply roots and fingerprints, original best-reply
  river slices on these turn-start games, input/policy/game immutability and all
  turn/action/support inventories. All four Q panels have the same support.
- Check saved<=restricted-river<=fine-river<=full-fine root values within1e-9chips.
  Their three increments telescope to the original unilateral gap. Those stages
  differ from the earlier turn/river attribution and must not be mixed together.
  Restricted continuation values can trade off fine rows, so per-row/action
  monotonicity is deliberately not an acceptance rule.
- Independent closed-form/finite pure-enumeration fixtures check both target
  signs, hidden-history aggregation, zero support, ties and fixed-prefix masks.
  A generic fixture must fail the shortcut of slicing a full reply when future
  unselected decisions are supposed to remain saved.
- Block learner/reference construction. No reference actions, new model strategy,
  default promotion or real-learning admission. New calculations have no new
  native audit; original reference outputs remain comparison-only.
- Refuse existing destinations and retain each completed profile plus partial/
  failure records. One separate900-second command bound includes original replay,
  all analysis and writes from thin entry; interpreter startup is excluded.
  Original7200/900learning/audit caps, source, seeds and failed gates stay fixed.
- Relevant full local bases, focused optional checks and both hosted source/
  final-artifact jobs pass before merge. A cached hash-checked terminal browser
  shows the different continuations and their limitations without full replay.

## Status and next decision

Implementation checkpoint: 62 focused tests pass in 0.82 seconds. Independent
terminal enumeration matches the closed-form four-stage values on both seat
signs. Controls catch hidden-history maximization, full-reply slicing with a
fixed future, zero support, exact ties, wrong masks, bad root/row inventories,
source fingerprints and interrupted-profile retention. A genuine uniform-policy
fixture uses the own low-SPR engine without training. An actual hash-checked
read of the prior 24-profile cache passes; mocked cache tests remain UNIT-only.
The terminal browser distinguishes four continuation columns and their scope.
Whole-repository lint, format and strict typing pass; complete local runtime/
optional/hosted checks and the actual full diagnostic remain pending.

No continuation measurements or new learning result is claimed. Explain whether
river learning, missing river
information or earlier-turn choices remain plausible only after the full panel
passes its accounting checks. Any later learning study needs its own prospective
contract and prescribed source-bound admission. Codex assists; personal practice
and human minutes are recorded only when actually reported.
