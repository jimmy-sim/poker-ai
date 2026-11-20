# Project roadmap

<a id="approved-roadmap"></a>

I want this to be an ongoing effort to improve the Hold'em agent and understand
its weaknesses. The simulator and learning tools provide the foundation.

Current [issue #4](https://github.com/jimmy-sim/poker-ai/issues/4) tests which card
and range distinctions matter at fixed training work. The guarded
prerequisite skip failed its unchanged work-identity gate; its
[retained result](pinned-prerequisite-skip-result.md) admits no validation
saving. The [known-game river study](river-strength-known-vulnerabilities.md)
was history-merged in PR #97 with a positive descriptive result limited to
its two preselected games and a failed control gate. The
[additional-spot comparison](river-generalization-fixed-spots.md) finished
**negative** under its fixed medium/dry absolute exploitability gates. Its
[saved-policy diagnosis](river-generalization-diagnosis-report.md) found no
candidate information collision on that finite spot; remaining turn and
river best-response gains motivate the [prospectively fixed medium/dry
training-budget test](medium-dry-training-budget.md). PR #98's separate
serial exact-head requalification passed all four local roles, hooks and
final hosted CI, and PR #98 was history-merged. The original failed logs
remain retained. Previous held-out and
fresh-validation cases are known evidence.
Further validation-performance work is deferred
unless it blocks correctness or the prescribed experiment budget. Follow the [learning journal](learning-journal.md)
for the reasoning and the [work log](work-log.md) for experiments and checks.
The [research operating workflow](research-operating-workflow.md) governs
successive bounded issue #4 milestones while preserving every experiment's
prospective contract and stop rule.

The original phase plan follows below. Its order and acceptance rules remain:
state the test before running it, validate the implementation and math, and
record the result and three interview questions at each phase's end. Advance only
after tests and mathematical checks pass.

## Phase 0 — Setup

Approved: repository structure, AGENTS.md, Makefile, and CI.

Definition of done: a clean checkout installs from `uv.lock`; the installed package
imports and includes its type marker; Ruff lint/format checks, strict mypy, and
pytest pass; commit hooks work; CI invokes the same commands. Record local checks
separately from hosted CI, which requires a remote repository and a workflow run.

## Phase 1 — Poker fundamentals

- Own card/deck/hand representation with bitmasks.
- Own fast 5–7 card hand evaluator and Monte Carlo/exact equity calculations.
- Validate against eval7/treys on millions of random hands with fixed seeds.
- Full Texas Hold'em engine: state, legal actions, betting rounds, side pots,
  showdown, and Hypothesis property tests. Default scope is 2–6 seat cash games;
  research agents initially use heads-up play.
- Begin with card encoding and deck invariants, then a transparent evaluator
  reference path before profiling and optimization.

## Phase 2 — Toy games and exact solvers

- Kuhn poker and Leduc Hold'em.
- Vanilla counterfactual regret minimization (CFR), then CFR+, Linear CFR,
  and Discounted CFR.
- Exact best response and exploitability, with documented normalization.
- Plot exploitability versus iterations and compare with OpenSpiel.
- Verify Kuhn's first-player value converges to -1/18 under the documented rules.

## Phase 3 — Heads-up limit, then no-limit Hold'em

- External-sampling and outcome-sampling Monte Carlo CFR.
- Card abstraction: hand-strength distributions, expected hand strength, and
  potential-aware clustering using k-means/earth mover's distance per street.
  Report abstraction sizes and measured information loss.
- No-limit action abstraction and translation of bets outside that abstraction.
- Checkpointing, multiprocessing, memory profiling, and training compute reports.

## Phase 3.5 — External solver validation (gated)

Do not start until Phase 2 exploitability results and a trained Phase 3 agent
exist. Record planning only before then. Full requirements and the eventual
writeup live in [solver_validation.md](solver_validation.md).

- Tier A: match against OpenSpiel CFR on Kuhn/Leduc at equal iterations; report
  exploitability, average-strategy L1 distance, and game-value error. Declare
  tolerances in configs in advance; debug failures before advancing.
- Tier B: 5–10 fully specified postflop spots, permitted open-source reference
  solvers, matched actions/ranges, documented convergence, reach-weighted action
  gaps, node frequencies, cross-play EV gaps, and restricted-spot exploitability.
- Diagnose gaps with controlled bucket-count/iteration ablations; produce tables
  and hand-class heatmaps. Investigate widespread gaps as likely bugs first.
- Read and record selected solver versions/licenses before use. Reference outputs
  are comparison-only and never enter agent training, checkpoints, or strategy.
  Never import, copy, or train on commercial solver outputs.
- Deliver `make validate-solvers`, spot-loader/metric tests including self-gap zero,
  a limitations-aware writeup, README summary, verified claim drafts, and three
  interview Q&As. No validation command or results exist at planning time.

## Phase 4 — Evaluation

- Random, always-call, always-raise, tight-aggressive, and equity-threshold bots.
- Duplicate matches: replay deals with seats exchanged to reduce variance.
- Win rate in milli-big-blinds per hand, confidence intervals, a significance
  test, and AIVAT or a documented variance-reduction alternative.
- Slumbot API benchmark only if its terms permit the intended usage and sample.
- Compare with an OpenSpiel/RLCard baseline and document rule differences.

## Phase 5 — Two quant extensions, selected with the user

Selected on November 2, 2026: **Bayesian opponent modeling and bankroll/risk
analysis**. Begin after Phase 4. Opponent-model learning will use own simulated
opponents, never the comparison-only OpenSpiel/Slumbot outputs. Risk results are
conditional research simulations, not recommendations for real-money play.

Original candidates: Bayesian opponent modeling and safe exploitation; subgame/depth-limited
solving; bankroll paths, risk of ruin, Kelly fraction and rake sensitivity;
or a small Deep CFR-style neural value approximation comparison.

## Phase 6 — Packaging

- README architecture diagram, real results table, convergence/exploitability
  figures, reproduction commands, limitations, and future work.
- 2–3 page technical writeup: methods, experiments, results, and failure analysis.
- 3–4 resume bullets with verified numbers and an interview Q&A cheat sheet.

Every number in published results must come from a rerunnable repository script.

## Continuing research program — user direction, November 9–10, 2026

The original bounded prototype is the foundation for an ongoing effort to
improve the agent. Track successive validated versions, research questions and
the user's understanding. Each milestone keeps a concrete acceptance contract;
the overall project has no claim of completed competitive Hold'em strength.

On November 10, the user reaffirmed that project success and efficiency take
priority over GitHub contribution counts or appearance. Prefer cohesive research
milestones and PRs, grouping related commits and documentation while retaining
every required publication and validation checkpoint. Keep exact-commit research
history reproducible. There is no contribution quota or reason to change dates,
delay completed work, weaken checks or divide work to shape the graph.

A research cycle states a hypothesis and fixed test, implements and validates
it, measures all planned controls, retains unfavorable outcomes, then explains
the next decision. Use fresh cases before generalization claims and prescribed
gates before global training or changing the agent default.

Visible progress uses coherent commits/PRs and dated experiment and learning
records on actual work days. Human hands-on minutes are recorded only when
reported; keep AI execution, experiment wall time and CPU time separate.
Resume claims use verified numbers, actual scope and honest assistance.
This long-term goal creates no automatic schedule; work windows need user
authorization. Historical phase contracts and failed results remain intact.
