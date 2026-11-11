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

## Implementation checkpoint

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

At that software checkpoint, continuation measurements were still pending.
The complete result follows. Any later learning study needs its own prospective
contract and prescribed source-bound admission. Codex assists; personal practice
and human minutes are recorded only when actually reported.

## Complete recorded result — November 11, 2026

The read-only command passes in **137.917452209 seconds**, below its separate
900-second cap. It retains all **24 profiles, 48 responding-seat conditions,
192 root values and 384 owned turn rows**, including unsupported rows. Baseline,
complete-reply fingerprints, river slices, turn action values and support agree
with the bound source; maximum source/accounting discrepancy is **0 chips** on
the original Python 3.11.17/NumPy 2.4.6 runtime. Every root ordering, telescoping
and immutable-policy/game/input check passes. No learner or reference is built.

The [manifest](../results/turn-continuations/manifest.json),
[complete summary](../results/turn-continuations/summary.json) and 24 compressed
detail files bind source `8e347e23fc6e3d149d61e3311c3f7bbecd4bc2b1`, fingerprint
`45bb7d825589a22a71151620e5efd84f8854ae6938052a0e8128723239c7a0dc`.
The [check records](../results/turn-continuation-checks/) retain both local bases
(2,687 passed, 58 skipped, 149 deselected each), relevant optional tests
(62 passed in 0.96/0.92 seconds), runtime/source guards, hooks and actual command
output. Hosted source CI43041865392 passes both jobs: 2,687 passed, 58 skipped,
149 deselected and one retained historical roundoff warning each, in
889.03/467.53 seconds. Final-artifact CI is checked separately before merge. An agent-run
actual-cache smoke test covers all 48 game/seed/method/seat selections in one load,
with learner/reference constructors blocked, invalid-key/rank handling and quit.
This records no user practice, human time or new independent numerical audit.

### The two calls need finer river distinctions in this saved matchup

For medium seed 20261302/mixed, responding seat 1 faces a 36-chip turn bet on
`Ts 9s 4d 2h`, with pot 72. These are the two groups selected by the prior trace's
largest losses, rather than by the new continuation outcome. Values are net
chips under each later continuation; folding is -18 throughout.

| Own hand | Saved call | Best declared-group river call | Best fine river call | Full fine reply call |
| --- | ---: | ---: | ---: | ---: |
| `9c 9d` | -25.894981 | -18.808061 | -16.994315 | -16.994315 |
| `Qh Kh` | -29.023136 | -18.439778 | -17.446327 | -17.446327 |

Both calls remain worse than folding after optimizing the current river groups.
Only the fine-information river continuation makes them better than folding.
For these calls, the last two columns coincide: the profitable call does not
need additional earlier turn changes after the call. This supports a specific
missing-river-information explanation for the fixed saved opponent; improving
learning within the same river groups alone does not flip these two choices.
It is not a universal abstraction floor or proof that a new feature will improve
training. A different opponent strategy can remove the opportunity entirely.

### Why a small river-only root gain can hide an important river distinction

For that same responding seat, the four root values are:

| Panel | Target root net chips | Increase from preceding panel |
| --- | ---: | ---: |
| Saved | -18.041926835 | — |
| Restricted river, saved turns | -18.009389411 | +0.032537424 |
| Fine river, saved turns | -18.001955752 | +0.007433659 |
| Full fine reply | -17.363717490 | +0.638238263 |

The increments sum to the original 0.678209346-chip unilateral gap. Most turn
calls are still folded in the first three panels, so the fine river response
gets little opportunity to realize its conditional value. Allowing the complete
reply to call those turns exposes that value. The small +0.007434 root stage
does not show that fine river information is unimportant.

These are controlled stages with saved turn play, not the earlier
`river_only_gain_exact_prefix` metric, whose prefix already uses the complete
fine reply. They also differ from the full within-partition/extra-information
decomposition. For this condition, that other decomposition is
0.053625672 + 0.624583674 = 0.678209346 chips. Do not add the two decompositions.
In these turn-start trees, the first two new stages together match the earlier
river-attributed loss, and the last stage matches the turn-attributed loss;
the new split explains which river information is needed. None is a measured
gain after retraining.

### All harder-spot seeds and methods remain

The table gives responding-seat 1 root increments in chips. Source roots for
both seats and all low-SPR conditions remain in the complete report; this table
does not replace that inventory or the original failed learning assessment.

| Seed | Method | Restricted river | Additional fine river | Complete reply turns | Total unilateral gap |
| --- | --- | ---: | ---: | ---: | ---: |
| 20261301 | ordinary coarse | 0.009279 | 0.014026 | 1.911475 | 1.934780 |
| 20261301 | paired coarse | 0.048596 | 0.082185 | 3.462473 | 3.593254 |
| 20261301 | mixed | 0.043708 | 0.010743 | 0.001486 | 0.055937 |
| 20261301 | fine self | 0.067476 | 0 | 0.010713 | 0.078190 |
| 20261302 | ordinary coarse | 0.009143 | 0.002723 | 0.230072 | 0.241937 |
| 20261302 | paired coarse | 0.024394 | 0.006431 | 0.300169 | 0.330994 |
| 20261302 | mixed | 0.032537 | 0.007434 | 0.638238 | 0.678209 |
| 20261302 | fine self | 0.071280 | 0 | 0.305288 | 0.376568 |
| 20261303 | ordinary coarse | 0.025413 | 0.023417 | 2.321307 | 2.370137 |
| 20261303 | paired coarse | 0.075314 | 0.045041 | 2.165173 | 2.285528 |
| 20261303 | mixed | 0.054137 | 0.015632 | 0.227953 | 0.297722 |
| 20261303 | fine self | 0.037550 | 0 | 0.014597 | 0.052146 |

For the mixed nines call, seed 20261301's fine-river value is -18.076721, below
the -18 fold value; seed 20261303's is -17.507963, above it. The important
opportunity is opponent/profile dependent. Fine-self's restricted/fine river
panels coincide as required. Low-SPR additional fine-river root increments are
zero in every condition; its original tiny total gaps and failure remain.

## Browse or reproduce

From the repository root:

```sh
.venv/bin/python scripts/inspect_turn_continuations.py
.venv/bin/python scripts/inspect_turn_continuations.py --rank 2
.venv/bin/python scripts/inspect_turn_continuations.py --interactive
.venv/bin/python scripts/diagnose_turn_continuations.py --output results/runs/turn-continuations-local
```

The browser checks cached source/input/output hashes once. Use n/p for groups,
s for seeds, o for methods, g for games, t for responding seats and q to leave.
It shows public betting history, saved turn probability, support, four action
value columns and their continuation-specific preferred choices. Full replay
takes time and deliberately requires a new destination; failed/partial evidence
is retained. New calculations are own diagnostics without a new native audit.

## Next decision and practice questions

The two calls expose a specific representational difference against the saved
opponent. Next inspect which conditional range weights and river decisions differ
inside those shared river groups, keeping all profiles and legal observable
inputs. That can test a betting-conditioned range explanation before choosing a
feature or another training change. Static-refinement failures remain relevant;
the new result alone does not accept a remedy or admit a trajectory.

- **Why does the best call change across columns?** Later river choices change
  the expected outcome after calling now. The current groups cannot realize the
  same continuation as the fine legal information in this fixed matchup.
- **Why is the river-only root increase small?** Saved turn play mostly folds
  before that river opportunity. A conditional call value and a whole-game root
  change weight different opportunities.
- **Does this make the agent stronger?** This step explains a saved weakness.
  It neither retrains nor deploys a policy; a remedy still needs prospective
  learning, compute, independent-check and generalization gates.
