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
The longer-work study's isolated source passed serial local base/optional
roles and both hosted jobs after a retained first hosted 3.11 timeout; its
source receipt precedes the capped synthetic proof and compute profile.
The synthetic proof passed, but the one fixed 18-path profile rejected the
longer-work study: its strict `10055.934`-second forecast exceeds the
`7200`-second cap. The 100m strength comparison therefore did not run;
the candidate remains unpromoted and its poker-strength effect at 100m is
unknown. PR #99 was history-merged with its [retained profile
failure](medium-dry-training-budget.md), final checks and self-review. The
next distinct [clipped-regret comparison](medium-dry-clipped-regret.md) asked
whether changing the learning update at the old 10m work cap reduces the
known medium/dry weakness without degrading the known low/wet spot. Its
[fixed matched-work result](medium-dry-clipped-regret-result.md) is **negative**:
all three paired seeds worsened on both known spots, and medium/dry missed its
unchanged absolute gates. Complete own policies preceded the pinned
comparison-only scalar audit. Neither spot is unseen; no default was promoted.
PR #100 was history-merged after all required checks. The next distinct
[batch-one comparison](medium-dry-b1-updates-result.md) reused immutable
PR #100 B4 controls. Its one fixed 10m run on the two known spots is
**negative**: medium/dry B1 median/worst exploitability 0.040640/0.042400
initial pots miss the unchanged 0.01/0.025 gates, with paired median
+0.001098. Low/wet's absolute gate passes but paired median is slightly
worse. Own raw policies preceded the pinned comparison-only audit. PR #101
was history-merged after final local/hosted qualification and solo review;
post-merge main CI remains separately tracked. No default is promoted. The
next [prospective average-readout question](river-uniform-readout-spots.md)
compares two policy averages of the same unchanged B4 signed path on a fixed
structurally selected card/range cohort. It is distinct from another B1 attempt.
The [prospective diagnostic detail](river-uniform-readout-diagnostic-addendum.md)
fixes control-only row ranking and a 900-second saved-policy trace cap before
selection; it changes no outcome criterion.
The one [structurally selected cohort](../configs/river-uniform-readout-freeze.json)
was frozen before any game-tree, policy or score measurement. Its
[fixed profile](river-uniform-readout-result.md) completed all 36 prescribed
100k-work paths, but the conservative 10m forecast was **8,885.117 seconds**
against the **7,200-second** cap. The compute gate rejected the longer run;
the uniform-versus-linear poker-strength comparison is **inconclusive**.
No 10m study, reference audit or default promotion occurred. A next question
requires a distinct prospective protocol supported by this failure.
The [prospective B8 matched-work test](medium-dry-b8-updates.md) completed its
one admitted comparison on two **known** river spots. The
[fixed report](medium-dry-b8-updates-result.md) is **negative**: medium/dry
B8 final median/worst exploitability is 0.036102/0.042155 initial pots,
missing the frozen 0.01/0.025 absolute gates. Its paired B8-minus-B4 median
is +0.000447; one seed improves and two worsen. The low/wet absolute gate
passes. The fixed 18-path profile passed its strict 3,831.907 < 7,200-second
compute admission, and the single six-path 10m study completed within cap.
Own policies were published before the comparison-only OpenSpiel audit, which
passed all 54 saved policies within `6.395e-14` chips maximum error.
Final report-head local base/optional, hooks and both hosted jobs passed;
[PR #103](https://github.com/jimmy-sim/poker-ai/pull/103) was history-merged
as `79db2fb`. Post-merge main CI passed both Python versions.
Neither spot is unseen; no default was promoted. The next distinct question
tests [full expected updates at matched work](medium-dry-full-expectation.md)
under a new prospective contract. It asks whether eliminating trajectory
sampling noise, while retaining signed linear update rules, improves known
medium/dry river decisions. Its isolated adapter passed focused tiny-game
math and replay checks, exact-source base and optional local suites, hooks,
and [both hosted jobs](https://github.com/jimmy-sim/poker-ai/actions/runs/45166698139).
The [source-check archive](../results/medium-dry-full-expectation/source-checks/manifest.json)
retains those checks and earlier corrected failures. One
[fictional proof](../results/medium-dry-full-expectation/own-proof/manifest.json)
passed capture and replay within its cap; the fixed real-game profile and
compute admission are next. The one fixed six-path
[profile](../results/medium-dry-full-expectation/profile/manifest.json)
completed under its cap and forecasts `1381.300294 < 7200` seconds under the
registered conservative rule. The separate data-only
[admission](../results/medium-dry-full-expectation/admission/manifest.json)
recomputed that unchanged bound and passed; the one 10m own study is next
after admission publication. The single admitted
[own study](../results/medium-dry-full-expectation/own/manifest.json)
completed both known spots with full saved-average coverage and zero recall
violations. The pinned comparison-only
[scalar audit](../results/medium-dry-full-expectation/native/manifest.json)
matched all 12 saved candidate policies within `5.684e-14` chips. The fixed
[B4 comparison and decision report](medium-dry-full-expectation-result.md)
classifies the two-known-spot result **positive** under its frozen rule:
medium/dry final exploitability 0.006700 initial pots versus the B4 control
median 0.035656, while low/wet also improves. The candidate was worse at
earlier medium/dry work labels. Final report-head qualification and review
passed all four local roles, all-file hooks and both hosted jobs; the
[final receipt](../results/medium-dry-full-expectation/final-checks/manifest.json)
binds those checks. PR #104 was history-merged as `804c4ed` after receipt-head
CI passed on both Python versions and solo review; main-branch CI is tracked
separately. No default changed or unseen-game claim follows. The next distinct
[prospective broader-input comparison](river-full-broader-spots.md) tests the
unchanged full expected candidate against fresh B4 paths at matched work on
two structurally selected card/range inputs. Its protocol precedes selection
and outcomes; the public templates and prior spot inputs remain known. The
[one-time cohort](../configs/river-full-broader-freeze.json) is now frozen and
GitHub-byte-verified, with no policy or score measurement. PR #104's separate
post-merge main CI was canceled at the fixed 35-minute limit for Python 3.11
after 3.12 passed; its receipt-head CI had passed both. The new exact-source
qualification passed all four local roles, hooks and both hosted jobs; the
[source receipt](../results/river-full-broader/source-checks/manifest.json)
was published and GitHub-byte-verified. The one
[fictional proof](../results/river-full-broader/own-proof/manifest.json)
passed its capture/replay and 180-second cap; publication and byte verification
of that proof preceded the fixed real-game compute profile. The one
[complete profile](../results/river-full-broader/profile/manifest.json) gives
the prescribed conservative bound 3,436.576 seconds under the 7,200-second
cap. The separate [admission](../results/river-full-broader/admission/manifest.json)
recomputed the identical bound; publish and verify its receipt before the
single fixed 10m study. That one eight-path study completed and its
[own archive](../results/river-full-broader/own/manifest.json) must be
published and verified before the pinned reference audit. That
[48-row audit](../results/river-full-broader/native/manifest.json) passed
the `1e-9`-chip gate; publish and verify it before the fixed report. No
classified poker-strength outcome existed at that checkpoint. The
[frozen report](river-full-broader-spots-result.md) now classifies the
two-input test **negative**: medium/dry fails its absolute and paired gates,
while low/wet passes its fixed rules. Final report publication, all four local base/optional roles, hooks and
both hosted jobs passed; the [final receipt](../results/river-full-broader/final-checks/manifest.json)
awaits publication/verification and solo review. No default promotion or
retry. [PR #105](https://github.com/jimmy-sim/poker-ai/pull/105) was
history-merged after the negative result and required checks; its first
receipt-head Python 3.11 CI canceled at the unchanged time limit, and one
targeted same-SHA operational requalification passed. Main post-merge CI
was pending at this entry. The next
[prospective saved-policy diagnosis](river-turn-loss-diagnosis.md) ranks the
full candidate's largest turn losses and counts actual information-row
collisions on the already evaluated, **known** medium/dry input before
choosing another strength experiment. No new diagnostic outcome exists yet. Isolated diagnostic source and
five focused tests passed; full exact-source qualification, fictional proof
and the one capped real-policy analysis remain pending.
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
