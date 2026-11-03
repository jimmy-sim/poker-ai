# Hold'em strength iteration 2 — own postflop learning diagnostic

The user authorized continued work while away, following the proposed learning /
representation / coverage diagnosis. Existing evaluation and Phase 5 reports are
historical evidence; user-terminal reproduction changes remain untouched.

## Definition of done, before implementation or results

1. Own finite turn–river mechanics and materialized trees are reusable without
   importing reference solvers or comparison policies into training. Preserve the
   old validation API and verify mechanics/export results remain unchanged.
2. Own full-tree CFR+ and own external-sampling MCCFR learn on two predeclared
   development games with limited physical ranges. Exact-card information is the
   first control. All policy outputs use own formats; OpenSpiel only checks values,
   best responses and matched full-tree iterations in a separate validation stage.
3. Diagnose exact versus existing potential-8 keys versus potential-8 with explicit
   public-board recall. Keep range/action/game parameters identical. Every key
   uses acting-player observations only. Test private/future-card invariance,
   legal menus, perfect recall, nonuniform chance and sampled regret expectations.
4. Gate the exact representation before representation comparisons: final own
   full-tree CFR+ exploitability <=0.001 initial pots; external-sampling median
   across three fixed seeds <=0.01 pots, every seed <=0.025 pots. Trained average
   rows cover >=95% of uniform-policy decision reach. These are initial acceptance
   targets, not promises. If a gate fails, retain the failure and diagnose it;
   do not loosen tolerances or silently run held-out cases anyway.
5. Profile short runs first. Fixed checkpoints and node/time budgets; initial
   total experiment cap under two hours. Stop at declared checkpoints, never
   publish favorable partial prefixes. A failed budget/gate remains explicit.
6. After development acceptance, freeze code/config choices and apply the same
   training/evaluation procedure to two held-out games. These games receive their
   own self-play training: this tests a training procedure, not zero-shot board
   generalization. No reference strategy trains any agent. Existing five solver
   spots remain known regression cases, not newly unseen tests.
7. Report exact restricted-game exploitability, independent checks, cross-play EV,
   chance-weighted fallback coverage, key collisions and runtime/node counts. Plot
   learning curves across all fixed seeds. Distinguish local game solutions from
   a usable global Hold'em agent. Implement a global change only if evidence
   supports it; do not claim improved full-game strength from spot learning alone.
8. Quality gates on 3.11/3.12, replayable commands, reviewed evidence, limitations
   and three interview Q&As. Preserve user changes and old benchmark provenance.

## Scope

All games use the existing full-pot/all-in grid and own engine/evaluator. The two
physical combos per seat deliberately keep the exact control affordable; these
are learning diagnostics, not realistic full ranges. Own self-play may use game
configs/rules, never reference actions, values, distributions or checkpoints.

The original MCCFR methodology is described in
[Lanctot et al. (2009)](https://www.cs.cmu.edu/~kwaugh/publications/nips09b.pdf).
The experiment tests our implementation under these specific mechanics; no new
algorithmic convergence theorem or competitive poker claim is intended.

## Retained initial failure and follow-up hypotheses

The initial exact-card run completed from clean `3be994c` in 121.50 seconds.
Both development gates failed, so no held-out game was run. Full-tree CFR+ passes
its accuracy threshold in both games. Sampled low-SPR accuracy is already below
its threshold, but uniform-decision-reach average-row coverage stalls below 95%;
on-policy coverage is nearly complete. Medium-SPR sampled exploitability improves
substantially but remains above the unchanged threshold at 100,000 iterations.
The reviewed initial report and all frozen policies are retained in
`results/holdem-learning/initial/`. Independent checking follows separately.

Before collecting any follow-up results, declare a 2×2 diagnostic of:

- Uniform versus linear iteration weighting of BOTH sampled regrets and averaging.
  Linear weighting uses raw cumulative sum(t*delta); regret matching is invariant
  to the common positive normalization in the existing full-tree Linear CFR.
  Conditional sampled updates retain their original expectations after multiplying
  by deterministic iteration weights. No claim of exact sampled trajectory matching.
- No initialization versus ONE full-tree expectation of the frozen uniform policy's
  counterfactual-regret and chance-weighted averaging updates. Both players use
  that same frozen policy for this initial simultaneous update; later sampled
  iterations alternate normally. Every initialized row receives an actual own-game
  regret/average calculation. Initial-only rows must be identified separately from
  subsequently sampled rows: coverage must not be presented as evidence of extra
  sampled experience. This is affordable only for the small finite games.

The original no-initialization/uniform cell already exists. Run the three new
versioned configs at the SAME seeds/checkpoints/accuracy/coverage thresholds.
Preselect **linear + one exact initial expectation** as the follow-up candidate;
retain every other cell regardless of outcome. This is an explicit new experiment
after a failed gate, not a retroactive rewrite of that gate. Do not run held-out
games until the selected candidate passes the unchanged development thresholds
and independent checks. Additional full-tree initialization cost is reported.

This experiment tests whether initial sampling noise and averaging/regret weighting
explain the failure. It cannot establish that a full-tree initialization scales to
global Hold'em, nor that public-board refinement improves a global sparse table.
