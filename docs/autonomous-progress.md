# Autonomous progress

The user authorized continuing in roadmap order until stopped. Phases 0–5 are
complete within their documented bounded scopes; competitive poker strength has
not been established. After the verified Phase 5 stopping point, the user
authorized another autonomous work session. Bayesian opponent modeling and
bankroll/risk analysis remain the selected extensions.

The [new Hold'em learning diagnostic](holdem-strength-v2.md) now has own finite
postflop training, exact/public/bucket controls, all four fixed 300k factorial
cells, two held-out games, and 378 independently checked frozen policy records.
Its preselected candidate passes development, but the medium-IP held-out median
misses the unchanged 1% pot target (1.0153%). The learning gate remains failed;
the proposed global training/match comparison has not run. Numerical checks and
tests pass separately. See the new offline report command and retained failures
in that document. Packaging records this bounded diagnostic, not stronger global
play or successful acceptance.

[Research packaging verification](phase6-verification.md) records the three-page
brief, verified claims/interview guide, full reproduction and software checks.
The full command reproduced all frozen own policies and the failed gate in
27.8 minutes. This is the verified bounded stopping point for this work session;
the next strength step requires a new experiment and fresh held-out games.

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
hashes, environment and estimator assumptions.

On November 3, the existing history was published to
[jimmy-sim/poker-ai](https://github.com/jimmy-sim/poker-ai). The first
[hosted baseline CI](https://github.com/jimmy-sim/poker-ai/actions/runs/41746694808)
passed on Python 3.11 and 3.12. Earlier phase reports retain their historical
local-only status. New work follows the linked [work log](work-log.md), issues,
PRs and actual hosted checks.
