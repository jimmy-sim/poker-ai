# Issue 2: river-integrated external sampling

## Session boundary and acceptance, before outcomes

This session resumes [issue #2](https://github.com/jimmy-sim/poker-ai/issues/2)
for protocol and correctness only. Stop after the protocol, estimator tests,
checkpoint tests and quality checks form a reviewable PR. Do not start the
frozen-policy variance panel or training runs in this session. Issue #2 remains
open until its fixed-work experiments and reports are complete.

Definition of done for this block:

1. Publish the versioned prospective protocol before experiment outcomes.
2. Derive the regret/average update weights and test exact expectations, including
   nonuniform chance and conditional private-world probabilities with card removal.
3. Enumerate hidden river outcomes without adding hidden cards to policy keys.
   Keep policies frozen within each target pass and accumulate repeated infos.
4. Count every recursive visit, including terminals. Preserve the ordinary
   sampler's trajectory and old checkpoint semantics; integrated continuation
   must restore its algorithm, weighting, RNG, rows and visit audit exactly.
5. Pass relevant tests, lint/format/strict typing and hosted CI; record actual
   results in the work log. No strength/variance improvement is claimed by tests.

## Estimator and weight derivation

The existing own materialized game samples both private hands, then samples a
hidden river before betting. Policies only observe revealed cards. The proposed
variant samples the private world normally and enumerates all 44 legal river
outcomes with their conditional probabilities. Opponent actions remain sampled;
the updating player's actions remain enumerated. A turn-only guard rejects flop
trees rather than silently changing the integration domain.

Let m be the product of probabilities on enumerated chance edges along the current
prefix; m starts at 1. At an integrated chance node with probabilities p(a), return
sum_a p(a)*V(child(a)), and recurse with prefix weight m*p(a). At a sampled chance
or opponent edge, sample on-policy and do not multiply m by that edge probability:
its selection frequency already provides that factor in expectation.

For target player i at a decision, compute local conditional action values v(a)
and v=sum_a sigma(a)*v(a). Accumulate **m*(v(a)-v)** as regret. At a visited
opponent decision, accumulate **m*sigma** as the existing two-player simple
external-averaging update. Terminal return values and local values are not
multiplied by m; m scales updates only. This avoids applying the integrated
probability twice. Repeated information sets across hidden worlds accumulate
before any policy update. Both target passes alternate as in the existing solver.

Induction over chance nodes gives the same expected regret and simple-average
increments as ordinary external sampling under a frozen policy. For sampled edges,
expectation sums their on-policy probabilities; for enumerated edges, the explicit
sum supplies exactly the same factors. The outer deterministic linear iteration
weight t multiplies both completed regret and average increments, preserving this
expectation. The own uniform full-tree initialization is unchanged and charged.

Enumerated worlds use separate subsequent opponent draws. This is not a claim of
strict Rao-Blackwell variance dominance under a shared random tape. Private-world
and opponent noise remain, and higher work per iteration can erase a per-pass
variance benefit. The experiments must measure both variance and work.

Background: [Lanctot et al., MCCFR (2009)](https://www.cs.cmu.edu/~kwaugh/publications/nips09b.pdf).
This project tests its own estimator; it claims no new convergence theorem.

## Implementation and correctness checks

`postflop/river_sampling.py` contains the selected-chance update function and
`RiverIntegratedMCCFR`. The ordinary sampler retains its original update function;
both classes share the iteration weighting, deferred update application and visit
audit. The integrated class accepts indexed turn games only. Policy keys and
action menus come from the existing observation-only matrix adapter.

```sh
make test-river-sampling
make check
```

The finite synthetic test enumerates every selector tape and compares its weighted
updates to independent closed-form values, for both target players. Nonuniform
private/river probabilities, chance before and after a decision, and nested chance
integration exercise the prefix/return distinction. A physical Hold'em fixture
conditions product-weighted ranges on a blocked card pair and checks both players'
expected regret and averaging increments against full-tree calculations. Privacy
checks cover all 44 hidden rivers and alternate opponent cards at the same root.

Checkpoints retain the ordinary sampler's v1 visit sidecar. Integrated checkpoints
use a v2 sidecar bound to the core SHA, sampler and config. Continue them with
`load_learning_checkpoint(..., solver_class=RiverIntegratedMCCFR)` and a learning
config containing `sampler: river_integrated` and the actual `sampling_weighting`.
The default loader rejects them; the integrated loader rejects ordinary v1 files.
Always use this learning loader for weighted/integrated training continuation,
rather than inferring the algorithm from the generic core's `external` label.
Byte-identical continuation tests cover both weights, with/without initialization,
including RNG, epsilon, raw rows, sampled keys and initialization work. Invalid
mode/config, incomplete sidecars and wrong core methods fail closed.

## Frozen prospective experiment

`configs/river-integration-study.json` fixes the primary procedure and budget:

- Exact-card encoding, unchanged actions/ranges, linear weighting and one exact
  own initial expectation for both ordinary and river-integrated sampling.
- All four earlier games are development data now, including files named
  `heldout_*`. Their earlier failed gate remains historical evidence. New unseen
  games require issue #3; no zero-shot generalization claim follows here.
- Three fixed training seeds and total-work thresholds 100k, 1m and 10m node
  visits/equivalents. Initial cost is 2*N, with N the materialized tree's nodes.
  Existing N values are 2,999 / 21,303 / 2,999 / 6,871, so all warm starts fit
  below the first threshold. Charge every integrated child and terminal visit.
- Stop after a complete iteration crosses a threshold and report actual work,
  iteration count and overshoot. One iteration is bounded by 2*N visits. These
  are common work thresholds with bounded overshoot, not identical visit totals.
- Report exact restricted NashConv/2 in chips and initial-pot units, every seed,
  initial-only versus subsequently sampled rows, coverage, runtime and node work.
  A shared initial seed does not imply identical random trajectories across methods.
  At common work thresholds the methods also have different iteration counts, so
  linear iteration weighting and warm-start amortization differ. A learning gap
  cannot be attributed solely to estimator variance; the frozen panel isolates
  per-pass update error and cost separately.
- A separate frozen-policy panel compares update MSE to full-tree expected updates
  at uniform and own CFR+ iteration-256 policies. Keep per-seed results, all-info
  and turn-only regret errors, averaging error, cost and MSE*mean cost. This last
  metric diagnoses efficiency of averaging IID frozen passes, not training strength.
- The same predeclared 0.001/0.01/0.025-pot accuracy and 95% coverage limits remain
  descriptive development checks. One expectation initializes every row, so positive
  average mass is not evidence of subsequent exploration. Retain initial-only rows.
- Materialized trees are capped at 200k nodes; total study wall-time cap is two
  hours. Budget failures retain data and stop. Do not publish a favorable partial
  prefix. Profile before increasing the budget or adding optimizations.

Reference outputs remain comparison-only. Only own game mechanics, own policies
and own updates enter training. The future report will record config, seeds,
source/dirty state, lock/game/policy hashes, runtime and hardware.

## Three review questions

1. **Why does only the update get prefix weight m?** Conditional return values
   already combine descendants through their local chance expectations. Multiplying
   returned values by m again would count an enumerated probability twice.
2. **Why compare nodes rather than iterations?** One integrated pass traverses many
   river branches, while an ordinary pass samples one. More iterations or lower
   per-pass variance alone does not establish better progress per unit of work.
3. **Can this block establish a stronger agent?** No. It establishes a tested
   estimator and reproducible continuation. Fixed-work experiments, independent
   metrics and fresh held-out validation are separate remaining steps.
