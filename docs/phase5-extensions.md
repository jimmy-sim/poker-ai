# Phase 5 — Bayesian opponents and conditional bankroll risk

The user selected these two extensions on November 2, 2026. This definition of
 done and the versioned configs precede implementation and all extension results.
All learning uses own simulated policies; reference/benchmark outputs are excluded.
No results exist at this planning commit.

## Acceptance criteria

1. Exact finite-hypothesis Bayesian inference on own Kuhn and Leduc. Evidence
   contains own card, public board and public actions, never opponent cards.
   Marginalize all compatible hidden deals, including folded hands. Deliberately
   censor showdown cards/payoff from the learner to isolate public-action learning.
   Verify likelihoods by independent small-tree enumeration and manual examples;
   identical public evidence must produce identical updates despite hidden cards.
2. Distinguish a root mixture of opponent policy types from averaging local action
   probabilities. Convert root mixtures to behavioral policies using each type's
   own realization reach. Verify cross-play EV linearity and a counterexample to
   naive local interpolation. All responses obey information-set constraints.
3. Own CFR+ supplies the fixed blueprint. Best respond to the posterior predictive
   opponent. Limit the root-level mixture with the blueprint using a predeclared
   **0.1 ante-chip per-hand degradation budget relative to blueprint security**.
   Security means minimum exact expected payoff over all opponent strategies.
   For base/candidate securities s0/s1, choose lambda <= budget/(s0-s1) when s1<s0.
   Concavity of minimum payoff gives security(mixture) >= (1-lambda)s0+lambda*s1.
   Recheck the actual mixed policy with exact best response to tolerance 1e-10.
   This is a conservative budget, not zero-cost safe exploitation, and only holds
   in these complete exact games. It is not the gift-budget algorithm in the paper.
4. Fixed configs/seeds/checkpoints; both seats; own uniform/calling/aggressive/value
   types; misspecified and switching opponents. Report posterior weights, held-out
   exact predictive log scores, exact cross-play EV and worst-case security for
   blueprint, unrestricted response and guarded response. No monotone-learning or
   profitable-exploitation threshold: failures are results. Predictive scores use
   the same fixed blueprint logging policy at every checkpoint to avoid changing
   the scoring distribution. Sampling uncertainty across three histories is
   descriptive, not population certainty or Hold'em strength.
5. Bankroll: exact bounded-return expected log-growth optimizer; known binary
   Kelly control; fractional sizing, pot-rake sensitivity and model uncertainty.
   Simulations track finite-horizon threshold crossing and maximum drawdown.
   Fractional wealth >0 is not literal ruin; fixed-stake absorbing ruin is a
   separate process, checked against finite-horizon dynamic programming and the
   eventual gambler's-ruin formula. Report Monte Carlo uncertainty and assumptions.
6. Risk experiments use explicitly synthetic binary laws plus own toy strategies
   against own scripted opponents. No positive real-world edge is assumed from
   earlier non-significant evaluation point estimates. Fees are a specified toy
   pot-rake model; no casino schedule or financial recommendation is implied.
7. One offline command reproduces configs, raw tables, plots and report markers;
   tests cover hidden-card censoring, mixture semantics, security certificates,
   Kelly boundaries, ruin timing and sample dependence. Quality gates on 3.11/3.12;
   methods/limitations, verified claim drafts and three interview Q&As per extension.

## Sources and scope

Read November 2, 2026, as mathematical background; no code/data copied:

- Ganzfried & Sun, [Bayesian Opponent Exploitation in Imperfect-Information Games,
  v6](https://arxiv.org/html/1603.03491v6). Our finite categorical type model is
  narrower than their continuous Dirichlet treatment; no paper replication claim.
- Ganzfried & Sandholm, [Safe Opponent Exploitation](https://www.cs.cmu.edu/~sandholm/safeExploitation.ec12.pdf).
  Our explicit nonzero degradation allowance is weaker than guaranteed game-value
  safety and does not implement their gift-based construction.
- Kelly, [A New Interpretation of Information Rate (1956)](https://bpb-us-w2.wpmucdn.com/u.osu.edu/dist/7/36891/files/2017/07/Kelly1956-1uwz47o.pdf).
  Expected log growth assumes a specified return law; optimality does not remove
  estimation error, finite-horizon loss or model drift.
- Karger & Lynch, [MIT 6.042 Lecture 26 (2000)](https://courses.csail.mit.edu/6.042/past-devel/archive/spring00/archive/lectures/L26.pdf),
  fixed-stake absorbing random walk. It differs from fractional sizing.

The exact-game scope makes the inference and safety arithmetic fully auditable.
It does not attach an unvalidated model or bankroll recommendation to the sparse
Hold'em prototype. Larger-game adaptation remains future work after these checks.
