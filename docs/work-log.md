# Development work log

Use this log with [issues](https://github.com/jimmy-sim/poker-ai/issues),
[pull requests](https://github.com/jimmy-sim/poker-ai/pulls),
[commits](https://github.com/jimmy-sim/poker-ai/commits/main/) and
[hosted CI](https://github.com/jimmy-sim/poker-ai/actions). The
[contribution workflow](../CONTRIBUTING.md) defines how each new task becomes a
reviewable result.

Dates below use America/Los_Angeles unless marked UTC. Entries describe actual
work; elapsed agent/process time is not a record of personal hands-on hours.

## 2026-11-04 — Issue #2 fixed-work experiment session

- **Start:** 00:17 Pacific (08:17 UTC), from the session clock.
- **Scope:** Resume the unchanged river-integration protocol with a bounded
  frozen-policy panel, fixed-work learning comparisons and a retained report.
  Acceptance is stated in [the experiment document](river-fixed-work.md).
- **Status at session publication:** Runner and experiments pending. No benefit
  of integration has been measured; all four earlier games are development data.
- **Assistance / time:** Codex implements and checks the runner and executes the
  study. Developer hands-on time is not recorded. Experiment and audit wall times
  will be recorded separately from assistant session elapsed time.

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
