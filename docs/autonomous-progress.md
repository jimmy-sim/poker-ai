# Autonomous progress

The user authorized continuing in roadmap order until stopped. Phases 0–5 are
complete within their documented bounded scopes; competitive poker strength has
not been established. The user requested a good stopping point; work stops at the verified Phase 5
boundary. Bayesian opponent modeling and bankroll/risk analysis were explicitly
selected by the user. Next milestone: Phase 6 final packaging.

Acceptance records:

- [Phase 1](phase1-verification.md): own cards/evaluation/equity and 2–6-seat engine,
  independent references and millions of evaluator comparisons.
- [Phase 2](phase2-solvers.md): exact Kuhn/Leduc CFR variants, best responses and
  matched OpenSpiel numerical checks.
- [Phase 3](phase3-verification.md): own sampled-CFR, abstractions, checkpoints,
  bounded training and explicit inference fallbacks.
- [Phase 3.5](phase3.5-verification.md): all exact-game gates passed; five postflop
  spots expose a large strategy gap. Full command and numerical replay passed.
- [Phase 4](phase4-verification.md): 36,000 local hands with 1,000 shared-deck
  clusters, honest significance limits and a completed 100-hand public pilot.

- [Phase 5](phase5-verification.md): 72,000 censored toy observations, 360 exact
  profiles, 120 conditional risk cells and 45 measured own-baseline cells;
  security/prediction/risk limits are explicit.

All learning in Phase 5 uses own simulated opponents. External reference and
public-benchmark outputs remain comparison-only. Risk analysis uses conditional
research simulations. No real-money integration or unapproved C++/Rust core.
Every quantitative claim must retain real source/dirty status, configs, seeds,
hashes, environment and estimator assumptions. Hosted CI has not run.
