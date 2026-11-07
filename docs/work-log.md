# Development work log

Use this log with [issues](https://github.com/jimmy-sim/poker-ai/issues),
[pull requests](https://github.com/jimmy-sim/poker-ai/pulls),
[commits](https://github.com/jimmy-sim/poker-ai/commits/main/) and
[hosted CI](https://github.com/jimmy-sim/poker-ai/actions). The
[contribution workflow](../CONTRIBUTING.md) defines how each new task becomes a
reviewable result.

Dates below use America/Los_Angeles unless marked UTC. Entries describe actual
work; elapsed agent/process time is not a record of personal hands-on hours.

For a guided explanation of the ideas and results, start with the
[plain-English learning journal](learning-journal.md).

## 2026-11-06 — Collision diagnosis and replacement admission

- **Request / issue:** Continue issue #4 after the texture accuracy failure.
  Diagnose concrete merges using frozen own controls, then define and test one
  replacement candidate before larger sampled/fresh/global work.
- **Before diagnosis outcomes:** Fix the two continuation panels, normalized
  decision weighting, hidden-history aggregation, support/tie handling and local
  sharing-score definition in
  [board-collision-diagnosis.md](board-collision-diagnosis.md). Input report and
  own-policy hashes are fixed in the config. No external solver outputs enter
  the diagnostic or learner.
- **Checks before diagnosis:** 686 tests pass with all extras on Python
  3.11.17/3.12.15, plus lint/format/strict typing/hooks. Ten new tests cover
  hidden-history aggregation, player signs/opponent reach, zero support,
  sharing-score math/self-zero, input retention and the terminal viewer.
- **Status:** Publish checked diagnostic code before computing retained-case
  results; actual diagnosis and candidate selection/admission are pending.
- **Diagnosis:** Clean published `9189c40` produces 7/115 conflicting low/medium
  rows under own exact continuation, versus 4/0 under uniform. Retain both panels.
  One row merges a full house and quads for pocket nines, with opposite preferred
  fold/call actions under the fixed own control. The local score is not game loss.
- **Before candidate outcomes:** Select only texture plus own made-hand-category
  history. Publish its input-bound config and unchanged full accuracy/compression
  targets before implementation/partition measurement. Scope is 48 full snapshots
  and native admission only; no fixed-work sampled/fresh/global comparison here.
- **Candidate implementation checks:** 712 all-extras tests pass on both Python
  versions, including 26 new candidate/admission tests. Optional encoder source
  and a bounded full-control runner/audit/report are published before the trial.
  Existing model/matrix/learner/report dependency bytes remain unchanged.
- **Assistance / time:** Codex implements and checks this block. Developer
  hands-on time is not recorded. Prior study outcomes/defaults remain unchanged.

## 2026-11-06 — Public-board fixed-work comparison

- **Request / scope:** Continue issue #4 with the unchanged fixed-work protocol,
  GitHub publication, journal updates and a bounded stopping point.
- **Before full outcomes:** Implement runner, collision/work/coverage checks,
  checkpoint replay, native frozen-policy/cross-play audit and offline figures.
  Clarify measurement conventions in
  [public-board-comparison.md](public-board-comparison.md) without changing the
  preregistered config. Tiny test fixtures are not development evidence.
- **Assistance / time:** Codex implements and executes this block. Developer
  hands-on time is not recorded; study runtime is recorded separately.
- **Checks before outcomes:** `make check` passes on Python 3.11.17/3.12.15
  with all optional extras: 676 tests each, lint/format and strict mypy. The 26
  new tests include native checks of a tiny fixture's 20 policies/100 profiles,
  coverage/work/receipt replay, missing-grid rejection and negative-gate retention.
  These fixture outcomes are software checks, not development results.
- **Initial status:** Runner code published before training; full-study results
  were pending at the entry's first publication. No fresh/global training.
- **Hosted fixture failure:** Initial CI on `48051de` fails because the timeout
  unit fixture inherits the optional JIT backend in a base-only environment.
  Correct the test to select NumPy; no learner/source/config/limit change. The
  all-extras local checks had hidden this fixture dependency. Retain the failed
  CI run and verify the base environment before advancing to result admission.
- **Raw grid retained:** Clean training source `48051de` completed all 150 own
  snapshots in 1205.044s, with all ten cells profiled three times. Source/input
  hashes match at completion. Exact controls pass; the texture candidate's raw
  learning gate fails on medium OOP despite meeting the compression requirement.
  Publish complete raw evidence before native audit; interpretation remains
  provisional until those independent checks finish. Test-only fix `3e1d374`
  changes no captured source/script/config; its hosted CI passes both jobs.
- **Audit / result:** All 150 policies, 800 ordered final cross-play profiles
  and 90 checkpoint/visit pairs pass. Native maximum error 1.63425e-13 chips;
  own replay error zero; audit wall time including replay 14.267s. Texture reduces
  raw-public rows 364→92 on low and 3,336→1,392 on medium. Medium sampled median
  7.369742% pot versus raw-public 0.233819%; worst 9.687537%. Full excess over exact
  2.522334 percentage points versus a 0.5 limit. Candidate fails unchanged accuracy
  gates despite passing compression. No result was dropped or retuned.
- **Evidence / limits:** [Tables/figures](../results/public-board/report/tables.md),
  [method and diagnosis](public-board-comparison.md), journal step 16,
  [PR #13](https://github.com/jimmy-sim/poker-ai/pull/13). Canonical keys add no
  row sharing here; all ten representations have zero abstract recall violations.
  Initialized coverage is separated from later sampled rows. Storage counters
  exclude shared tree/container costs; RSS is cumulative. Profiles precede their
  individual learning cells rather than one upfront batch; timings are descriptive.
- **Stopping point:** Bounded comparison and audit complete. Issue #4 stays open
  for a more informative representation; no fresh cases/global training/default
  changes. Final local/hosted quality checks are attached to the PR. Human hands-on
  time remains unrecorded; the study/audit times above are process wall time.

## 2026-11-06 — Public-board protocol and correctness

- **Scope / PR:** Resumed [issue #4](https://github.com/jimmy-sim/poker-ai/issues/4),
  [PR #12](https://github.com/jimmy-sim/poker-ai/pull/12). Stop at optional
  representation code/correctness; no new training or compression study.
- **Before outcomes:** Published protocol/config in `d120490`, fixing five
  controls, the texture candidate, three seeds, node-work thresholds, runtime
  cap and accuracy/compression limits. See
  [public-board-abstraction.md](public-board-abstraction.md).
- **Changes:** Added suit-canonical public boards and a coarse per-street texture
  history, plugged into the finite-game matrix as optional encodings. Kept
  existing keys/defaults. Added a read-only board inspector and journal step 15.
- **Actual verification:** `make check` passes with all optional extras on
  Python 3.11.17 and 3.12.15: 650 tests each, lint/format and strict types.
  Of these, 29 new tests cover board features, symmetry, hidden information,
  original-key compatibility, menus and recall on both development games.
  One additional historical-source regression confirms freeze rejection.
  Hosted CI is separate and attached to the PR.
- **Failure retained / resolved:** The first full run failed because its old
  positive admission test assumed current source matched historical evidence.
  Production rejection stays intact. Gate unit tests now explicitly use matching
  metadata in memory; the historical manifest/report/receipts remain unchanged.
  README/protocol identify the original revision for historical reproduction.
- **Limits / stopping point:** No measured learning benefit or memory reduction.
  Texture deliberately merges public information; canonical public suits do not
  preserve private blocker detail or guarantee equivalence under asymmetric
  ranges. Issue #4 stays open for the fixed-work runner and comparisons.
- **Assistance / time:** Codex implemented, checked and documented this block.
  Developer hands-on time is not recorded. No training experiment wall time.
  Unrelated user experiment outputs are excluded from the branch.

## 2026-11-05 — Fresh validation session

- **Start:** 10:03 Pacific (18:03 UTC), session clock. Resumed issue #3.
- **Prospective scope:** Freeze the ordinary procedure, select new cases by
  published card/position rules, verify the development gate, then retain a
  bounded fixed-work study and independent audit if admitted. Acceptance:
  [fresh-validation.md](fresh-validation.md). No fresh outcomes exist at publication.
- **Before outcomes:** Protocol published in `25e85cc`; runner/admission/selection
  code published in `1fbc9c8` after 26 new tests and 620 full local tests passed,
  plus lint/format/strict typing/hooks. The four structurally selected inputs and
  source/input freeze are published next, before admission or fresh training.
- **Admission:** Cohort/freeze published in `1a86d28`; real gate passes with
  16 final development/control policies replayed and zero own metric error.
  Input/source hashes, unchanged limits and linked native audit are verified.
  [Hosted cohort CI](https://github.com/jimmy-sim/poker-ai/actions/runs/42083487841)
  passed both Python jobs. The admission receipt is committed before fresh training.
- **Fresh result:** Clean `9442bca` completed all 44 sampled/control snapshots in
  499.560s. Raw outcomes/frozen own policies were published in `6e4d3d5` before
  native audit. All four cases pass the unchanged final procedure limits; the
  closest median is 0.9670% of pot against 1%, worst 0.9845% against 2.5%.
- **Independent checks:** All 44 native value/BR comparisons pass within
  8.53e-14 chips; audit wall time 2.450s. Own replay error is zero. All 36 original
  checkpoint/visit hash receipts and work counters were verified. Runtime
  provenance and a separate post-run hardware observation are retained.
- **Coverage/limits:** The medium wet case retains up to 1,545 initial-only rows
  and 94.6657% subsequent uniform-reach coverage, despite passing initialized
  average-row coverage. Four tiny per-case learners do not establish global
  strength or zero-shot play. The old failed hold-out stays failed.
- **Verification / PR:** [#11](https://github.com/jimmy-sim/poker-ai/pull/11);
  620 local all-extras tests passed on both Python versions, with quality checks
  and hooks. Cohort hosted CI passed; final evidence checks are attached to the
  PR. Figures and linked artifact hashes were inspected.
- **User learning:** The developer reports completing the suggested terminal
  commands and getting the expected results. No further mastery or hands-on
  duration is inferred; the report is added to the journal's personal notes.
- **Assistance / time:** Codex prepares and executes the research block.
  Developer hands-on time is not recorded; experiment time is recorded separately.
- **Stopping point:** Fresh procedure validation complete. Ordinary default
  retained. No global training/comparison, new abstraction or extra seed sweep
  was started; representation work remains issue #4.

## 2026-11-04 — Plain-English learning journal

- **Request / issue:** [#9](https://github.com/jimmy-sim/poker-ai/issues/9), create
  one guide to understand the project step by step and keep it current.
- **Change:** Added a retrospective 13-step walkthrough, labeled examples,
  evidence links, glossary, graph-reading help, local commands and optional
  personal-note prompts. It covers the work through the completed issue #2 study.
- **Maintenance:** README/work log link to the journal. Project instructions,
  contribution guidance and PR template require updates with substantive future
  milestones. This does not start experiments or schedule background work.
- **Assistance / time:** Codex drafted the guide from recorded project evidence.
  Developer hands-on time and personal learning progress are not recorded.
- **Verification:** Evidence/relative-link review and ordered-chapter/code-fence
  checks passed. Both suggested test commands passed together (116 tests; the
  sandbox reported an unwritable optional pytest cache). Full local checks passed
  lint/format/strict typing and 594 tests; hooks passed. Hosted CI is attached to
  the PR linked from issue #9. No new research run.

## 2026-11-04 — Issue #2 fixed-work experiment session

- **Start:** 00:17 Pacific (08:17 UTC), from the session clock.
- **Scope:** Resume the unchanged river-integration protocol with a bounded
  frozen-policy panel, fixed-work learning comparisons and a retained report.
  Acceptance is stated in [the experiment document](river-fixed-work.md).
- **Status at session publication:** Runner and experiments pending. No benefit
  of integration has been measured; all four earlier games are development data.
- **PR:** [#8](https://github.com/jimmy-sim/poker-ai/pull/8). The scope was published
  in `9400b71`, checked runner in `aebed7b`, audit/report pipeline in `fb4f04d`
  with optional-dependency/rerun fixes in `a781086`, and full raw outcomes in
  `80ed3f0` before native audit. Real commit dates are preserved.
- **Observed study:** All 80 learning/control policies and 96 frozen seed cells
  retained from clean `aebed7b`; 972.029s study wall time. Native audit took
  3.126s, passed all 80 policies within 9.95e-14 chips; own replay error was zero.
  All 72 original checkpoint/visit receipts and work counters were checked.
- **Finding:** Both variants pass final development limits. Integration has a
  lower final median in one game and higher in three; empirical frozen regret
  MSE times visits is higher in 14/16 cells. Keep the ordinary default. The
  [report](river-fixed-work.md) retains initial-only coverage and unstable
  panel-ratio limitations; no global strength/fresh hold-out claim follows.
- **Verification:** 594 all-extras local tests passed on each of Python 3.11 and
  3.12, with lint/format/strict typing/hooks. Hosted Python jobs passed on
  [pipeline CI](https://github.com/jimmy-sim/poker-ai/actions/runs/41799867893);
  final evidence checks are tracked on PR #8. Plots were visually inspected.
- **Assistance / time:** Codex implements and checks the runner and executes the
  study. Developer hands-on time is not recorded. Experiment and audit wall times
  are recorded separately from assistant session elapsed time.
- **Stopping point:** Bounded fixed-work investigation complete. No fresh games,
  abstraction study, global training or additional seed sweep was started.

## 2026-11-04 — Issue #2 estimator correctness

- **PR:** [#7](https://github.com/jimmy-sim/poker-ai/pull/7), partial progress on
  issue #2. The protocol was published first in `445adc2` on November 3 Pacific.
- **Implementation:** Selected hidden-river chance integration with probability
  weights on updates, deferred target passes, explicit node accounting and
  algorithm-bound checkpoint restoration. Existing ordinary behavior stays tested.
- **Checks observed:** 37 new tests passed. Full Python 3.11 checks passed lint,
  formatting, strict typing and 579 tests with optional extras. Full Python 3.12
  checks also passed 579 tests and strict typing. Targeted `make test-river-sampling`
  passed 44 checks; hooks passed. [Implementation CI](https://github.com/jimmy-sim/poker-ai/actions/runs/41797026396)
  passed both hosted Python jobs; final-head checks are tracked on PR #7.
- **Meaning:** Exact expected-update and continuation checks, not measured variance
  reduction or stronger play. No training/variance panel has run this session.
- **Assistance / time:** Codex implemented and checked the estimator/tests;
  developer hands-on time is not recorded. Session start is recorded below.
- **Stopping point:** Correctness foundation ready for review; fixed-work variance
  and learning experiments remain for the next block. No benchmark was run to
  fill the session, and no strength result is inferred from passing tests.

## 2026-11-03 — Issue #2 protocol and correctness session

- **Start:** 23:50 Pacific (07:50 UTC November 4), from the session clock.
- **Scope:** Resumed [issue #2](https://github.com/jimmy-sim/poker-ai/issues/2)
  for a bounded protocol/correctness block. Training and variance experiments
  remain deferred to the next block.
- **Prospective protocol:** [Study config](../configs/river-integration-study.json)
  and [derivation/acceptance](river-integration.md), committed before outcomes.
  All four previously inspected spots are known development games now.
- **Assistance / time:** Codex prepares the protocol, implementation and tests.
  Developer hands-on time is not recorded; session and process time are separate.
- **Status at protocol publication:** Implementation and correctness checks pending;
  no sampled-training or frozen-policy variance results have been collected.

## 2026-11-03 — Same-day publication preference

- **Request:** Make ongoing contributions visible across the days of actual work.
- **Change:** Recorded same-day publication of coherent checked increments,
  dated PR/work-log updates, and real commit dates in the project instructions.
- **Scope:** Documentation only. Issue #2 remains paused; no training or research
  experiment was started. A daily publishing cadence is not a recurring job.
- **Assistance / time:** Codex updated the instructions from the developer's
  request. Personal hands-on time was not recorded.
- **Verification:** Diff review and documentation formatting checks; hosted CI
  is attached to the PR containing this entry.

## 2026-11-03 — Public development workflow

- **Question:** How can progress be visible and reviewable on GitHub as work happens?
- **Decision:** Publish the existing history as a baseline, then use prospective
  issues, focused branches, PRs, CI and evidence-linked log entries.
- **Implementation:** Added issue forms, a PR template, contribution guidance and
  this log. README links point to live progress and CI.
- **Tracking:** [Publication/workflow issue #1](https://github.com/jimmy-sim/poker-ai/issues/1).
- **Assistance:** Codex prepared repository setup and workflow files. The developer
  selected the public repository and completed account sign-in. This entry does
  not claim personal implementation/review time that was not logged.
- **Hands-on time:** Not recorded.
- **Validation:** Local `make check` passed lint, formatting, strict typing and
  525 tests (8 optional skips). Issue-form YAML and local document links checked.
  Hosted Python 3.11/3.12 jobs passed for the
  [published baseline](https://github.com/jimmy-sim/poker-ai/actions/runs/41746694808)
  and the [initial PR head](https://github.com/jimmy-sim/poker-ai/actions/runs/41746822968).
- **PR:** [#5 — visible development workflow](https://github.com/jimmy-sim/poker-ai/pull/5).
  Later documentation commits receive their own CI; the links above identify
  the exact runs observed when this entry was written.
- **Next:** [Milestone: bounded strength-v3 validation](https://github.com/jimmy-sim/poker-ai/milestone/1)
  contains the prospective estimator, fresh hold-out and abstraction tasks.

## Retrospective baseline: November 2–3, 2026

This index was prepared on November 3. The 82 local commits through `932ea68`
already existed before GitHub publication. Their original history is preserved;
the rows below do not represent historical GitHub issues, reviews or PRs.

| Milestone | Recorded implementation/evidence | Review entry point |
|---|---|---|
| Fundamentals | Cards, five-to-seven-card evaluation, equity, immutable engine | [Phase 1 verification](phase1-verification.md) |
| Exact solvers | Kuhn/Leduc, CFR variants, exact best responses, OpenSpiel comparisons | [Phase 2](phase2-solvers.md) |
| Sampled training | MCCFR, abstraction, checkpoints, bounded limit/no-limit runs | [Phase 3](phase3-verification.md) |
| External comparison | Licensed comparison-only reference and retained strategy gaps | [Solver validation](solver_validation.md) |
| Evaluation | Duplicate deals, uncertainty, bounded public protocol pilot | [Phase 4](phase4-verification.md) |
| Quant extensions | Own Bayesian models and conditional risk analysis | [Phase 5](phase5-verification.md) |
| Learning diagnosis | Four controls, public-board comparison, retained held-out failure | [Hold'em diagnostic](holdem-strength-v2.md) |
| Research packaging | Technical brief, verified claims, actual checks | [Snapshot verification](phase6-verification.md) |

Most implementation and experiment execution was AI-assisted by Codex. Human
hands-on time for this baseline was not recorded. Commit counts and timestamp
spans must not be converted into hours worked.

One measured process interval is available: the full postflop reproduction took
**1668.27 seconds (27.8 minutes) of pipeline wall time**, including training,
independent checks and rendering. Source: the `seconds` field in
[reproduction.json](../results/holdem-learning/reproduction.json). This interval
is not human work time or a CPU-hours measurement and may overlap other activity.
Its actual outcome is `heldout_gate_failed`; passing numerical checks did not
change the preset performance target.

## Template for the next session

```text
Date / issue / PR:
Question or problem:
Decision and reason:
Changes and commit(s):
Commands, actual outcomes and artifact links:
Failure or remaining uncertainty:
AI assistance:
Developer's own review / experiment / learning note:
Hands-on time (recorded, otherwise unknown):
Experiment wall time (source; note overlaps):
Next step:
```
