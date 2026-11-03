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
