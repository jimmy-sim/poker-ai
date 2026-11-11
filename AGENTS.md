# Project conventions

## Project priorities and publishing

- Prioritize model quality, correctness, reproducibility, efficient progress and
  the user's understanding. The user explicitly reaffirmed on November 10, 2026
  that project success comes first. GitHub activity records the work; contribution
  counts, graph appearance and daily activity targets are not project goals.
- The user requested ongoing visible development in `jimmy-sim/poker-ai`.
  Follow `CONTRIBUTING.md`: prospective issue, focused branch/commits, linked PR,
  actual CI/evidence, and an entry in `docs/work-log.md` for substantive work.
- Prefer one focused PR per coherent research question or implementation
  milestone, covering its supporting implementation, validation and report.
  Keep it open through the required stages. Split when scope, risk or independent
  review benefits justify it; do not split to generate activity.
- Group related fixes, tests, documentation, journal updates and evidence at
  meaningful commit boundaries. Keep every separately required publication
  checkpoint: prospective protocol, tested source, admission and own evidence
  before reference comparison. Batching must not bypass these gates.
- Preserve commits referenced by research evidence and their availability in a
  normal clone. Use history-preserving merges for those PRs. Squashing is suitable
  only for housekeeping changes without such dependencies, after checking them.
- On each actual work day, publish coherent checked increments during the session
  or by its end, rather than waiting for an entire multi-day phase. Update the PR
  and dated work log with actual progress and remaining checks. Preserve real
  commit dates; do not distribute completed work artificially across future days.
  This cadence applies to active work and does not resume paused work or create
  an automatic daily work schedule.
- Preserve historical commits and dates. Distinguish retrospective summaries from
  issues/PRs created during the work; do not manufacture activity or review.
- Record actual hands-on time separately from AI sessions and experiment wall
  time. Missing historical time stays unknown; never infer hours from commits.
- Publish only intended committed changes. Preserve unrelated local experiment
  outputs, keep large runs ignored, and report failed research gates honestly.
- Use PR/issue updates for routine status. Commit check receipts when required
  for reproducibility; avoid standalone status commits that add no evidence.
- During iteration, run checks appropriate to the change. Complete every local,
  optional, hosted and source-bound check required by the applicable protocol
  before advancing. Repeat checks when changes, failures or unresolved concerns
  justify them. Documentation-only edits need appropriate diff, format and link
  checks; required hosted CI must still pass before merge.

## Scope and workflow

- Follow `docs/roadmap.md` in order. State each phase's definition of done first.
- Work in small, reviewable steps with one logical commit per step.
- Before each step, explain the action and purpose; afterward, show commands,
  actual verification results, and the next step. Keep explanations concise.
- Explain new game-theoretic concepts when they first appear. Challenge weak
  decisions and explain tradeoffs briefly.
- Maintain `docs/learning-journal.md` with each substantive implementation or
  research milestone, in the same PR. Update its current status and append a
  dated plain-English account: question, change, illustrative example, actual
  checks/result and next decision, linked to evidence. Define terms on first use.
  Preserve earlier failures; label examples and assistance honestly. Add personal
  learning notes only from what the user actually says or does. Do not invent
  experiences, mastery, hours, or first-person authorship. No filler entries or
  automatic work schedule are implied.
- Write tests alongside implementation. Never advance with failing tests or
  unvalidated math. End each phase with three interview questions and answers.
- Use existing poker libraries only as validation references, isolated to
  validation modules and optional dependency groups introduced when needed.
- Keep all gameplay in simulation or public bot benchmarks whose terms permit
  the intended use. Never add real-money client/site integration, scraping,
  input automation, HUDs, real-time assistance, or protocol reverse engineering.
- Request approval before adding a C++ or Rust core. Discuss and select the two
  Phase 5 extensions with the user before implementation.

- External solver validation is a gated Phase 3.5 milestone. Do not start it
  before Phase 2 exploitability results and a trained Phase 3 agent exist; follow
  `docs/solver_validation.md`. Read/record selected pinned solver licenses before
  use. Never import/copy/train on commercial solver outputs. Open-source reference
  outputs are comparison-only and must never enter the agent's strategy/training.
  Declare Tier A tolerances before runs; debug failed gates before advancing.

## Code and mathematical conventions

- Support Python 3.11+. Use explicit types, small functions, and clear names.
- Ruff handles lint and formatting; mypy runs in strict mode.
- Put reusable implementations in `src/poker_ai/`; keep scripts thin.
- State units, payoff signs, player indexing, and numerical tolerances explicitly.
- Explain equations and assumptions in relevant docstrings, particularly regret
  matching, counterfactual values, averaging, and exploitability conventions.
- Pass RNG objects explicitly; avoid hidden global random state.
- Use property tests for invariants and independent references for validation.
- Investigate surprising performance for information leakage, private-card
  access, evaluator errors, and statistical mistakes before claiming an edge.
- Profile before optimizing; add Numba only for measured bottlenecks.

## Reproducibility and compute

- Every published quantitative claim must trace to a rerunnable repository script.
- Record config, seed(s), code revision and dirty status, dependency lock hash,
  runtime, hardware, hyperparameters, raw metrics, and estimator conventions.
- Use explicit seed lists for comparisons; a fixed seed alone does not establish
  statistical confidence. Document uncertainty and dependence between samples.
- Store small reviewed evidence in `results/`; generated runs and checkpoints are
  ignored by default. Document retention/download paths for larger artifacts.
- Mark long tests `slow`; run them explicitly and save reports at phase gates.
- Flag experiments likely to exceed a few hours before running them and offer
  cheaper alternatives. Do not put million-hand sweeps in routine CI.

## Commands

Install uv 0.13.5 before running these commands.

```sh
make setup       # Install from the committed lockfile
make check       # Lint, format check, strict typing, and fast tests
make format      # Apply Ruff fixes and formatting; inspect the diff
make hooks       # Install repository-local commit hooks
make validate-five  # Exhaustive Treys hand-rank check; optional validation extra
make validate-best  # Seeded million-hand checks for six and seven cards
make validate-equity  # Exact Treys counts and fixed-budget Monte Carlo checks
make validate-engine  # Independent action traces and rational payouts
uv run --locked pre-commit run --all-files
```

Regenerate `uv.lock` deliberately with `uv lock` after changing dependencies.
Review and commit both dependency declarations and lockfile changes.

## Definition of done

- Acceptance criteria and relevant mathematical checks pass.
- Lint, formatting, strict typing, and applicable tests pass.
- Documentation explains behavior, assumptions, tradeoffs, and limitations.
- Experimental claims include reproducible evidence; no fabricated numbers.
- Phase completion reports actual checks and three interview Q&As.
- Local checks and hosted CI status are reported separately.
