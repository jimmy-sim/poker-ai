# Project conventions

## Scope and workflow

- Follow `docs/roadmap.md` in order. State each phase's definition of done first.
- Work in small, reviewable steps with one logical commit per step.
- Before each step, explain the action and purpose; afterward, show commands,
  actual verification results, and the next step. Keep explanations concise.
- Explain new game-theoretic concepts when they first appear. Challenge weak
  decisions and explain tradeoffs briefly.
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
