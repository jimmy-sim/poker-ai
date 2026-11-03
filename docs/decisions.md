# Design decisions

## 2026-11-03 — Bounded learning diagnostic and research packaging

- Reuse an own finite-game array backend across toy and materialized postflop
  games. Training imports no reference solver or comparison policies.
- Preserve all initial, 100k and 300k outcomes. The preselected candidate's held-out
  median misses its unchanged target; no gated global experiment is launched.
- Public-board refinement is a local diagnostic only. Test global linear-weighted
  checkpoint compatibility, but do not substitute an unvalidated global policy.
- Use optional Numba only after paired profiling. Explicit FMA controls address
  the measured numerical trajectory discrepancy; no own C++/Rust core is added.
  Full installed LICENSE files were read: Numba 0.68.1 and llvmlite 0.50.0 use
  BSD-2-Clause notices. Package versions and LICENSE hashes are recorded in
  `results/holdem-learning/compiler-licenses.json`. These are compiler dependencies,
  not poker teachers; OpenSpiel licensing remains in `solver_validation.md`.
- Separate successful evidence audits from performance acceptance. The offline
  report can audit successfully while stating a failed learning gate. The full
  reproduction command returns nonzero for that failed gate and retains staging.
- Package verified results and limitations, including negative results, in a
  three-page technical snapshot and an interview guide. Preserve user-regenerated
  Phase 5 reports and original metadata; do not recast reruns as independent data.

## 2026-11-02 — Phase 0 foundation

- Use Python 3.11-compatible code and uv 0.13.5 with a committed lockfile.
  Test Python 3.11 and 3.12 to exercise the baseline and another supported runtime.
- Use a `src/` package layout and pytest's importlib mode so installation mistakes
  are observable instead of hidden by source-directory path manipulation.
- Start with NumPy and the approved test/quality tools. Add Numba after profiling.
  Add reference poker libraries in optional groups when validation needs them.
- Pin the build backend, uv version, and GitHub Actions commit SHAs. Dependency
  upgrades require an explicit lockfile diff and verification.
- Use local pre-commit hooks invoking locked Ruff instead of a second separately
  resolved Ruff environment. Hooks check; `make format` applies changes explicitly.
- Keep large validation sweeps out of routine CI. A smoke test checks packaging;
  it provides no evidence about evaluator, engine, or solver correctness.
- Pass RNGs explicitly when stochastic code arrives. Save config, seeds, code and
  environment provenance, and raw evidence before reporting results. Fixed seeds
  support reruns; uncertainty analysis still needs an appropriate sampling design.

Tool documentation:

- https://docs.astral.sh/uv/concepts/projects/sync/
- https://docs.astral.sh/uv/guides/integration/github/
- https://github.com/actions/checkout/releases/tag/v7.0.1
- https://github.com/astral-sh/setup-uv/releases/tag/v9.0.0

## 2026-11-02 — Phase 1 card representation

- Use rank-major integer IDs: 4 * (rank - 2) + suit. Ace has rank 14; suit order
  is clubs, diamonds, hearts, spades. Canonical notation is case-sensitive.
- Validate built-in integers at public representation boundaries. Reject booleans,
  NumPy scalars, out-of-range values, duplicate cards, and masks with invalid bits.
  Convert NumPy shuffle output to built-in integers explicitly.
- Use bitmasks for unordered card sets and immutable tuples for ordered decks.
  Draws return a new deck. Revalidation and slicing are clarity-first choices;
  measure them before optimizing.
- Require an explicit NumPy Generator for shuffling. Tests use explicit PCG64
  streams and deterministic Hypothesis settings under the committed lockfile.
- Let mypy target its running interpreter. NumPy's Python 3.12 stubs use syntax
  rejected by a Python 3.11 type-checking target. The Python 3.11 CI job still
  enforces baseline compatibility; the Python 3.12 job checks its own environment.
  No dependency versions change for this adjustment.

Details and review questions: [card representation](phase1-cards.md).

## 2026-11-02 — Five-card evaluation

- Return an immutable, ordered HandRank with category then explicit tie-breakers.
  Higher means stronger; suits never break ties. Encode the wheel straight as
  five-high; a royal flush is an ace-high straight flush.
- Use independent Python rank counts/group sorting for a readable correctness
  baseline. Preserve input validation and defer optimization until profiling.
- Pin Treys 0.1.8 as a validation-only optional dependency (MIT license inspected).
  Production evaluation imports no reference library or reference output.
- Validate equality classes in both directions, their total order, and the exact
  category census. Use exhaustive enumeration for five cards and a seeded smoke
  config to estimate costs; keep the full sweep outside routine CI.
- Record source hashes, revision/dirty status, config, environment, input digest,
  and runtime. Commit implementation before generating the published full report.
- Type-check thin reproduction scripts alongside production code and tests.

Protocol and review questions: [five-card evaluator](phase1-five-card.md).

## 2026-11-02 — Six/seven-card evaluation

- Add evaluate_best for five through seven cards, taking the strongest rank over
  every five-card subset. Validate the entire input, including discarded cards.
  Preserve evaluate_five's classification logic and comparison-key semantics.
- Allow any five available cards, including an entire Hold'em board. Returning a
  rank avoids selecting an arbitrary physical subset when several subsets tie.
- Keep the readable subset baseline, including repeated validation, until measured
  profiling justifies optimization. Six and seven cards require six and 21 subsets.
- Calibrate all five-card rank classes against optional Treys, then compare exact
  sampled best-five keys. Keep the map exclusively in validation code.
- Declare one million draws per size and independent PCG64 seeds in configs.
  Pilot runtime first; keep the full check outside fast CI and record provenance.
- Generalize the provenance helper's entrypoint list so each runner hashes its
  actual CLI script. Preserve the five-card runner's default entrypoint.

Details and review questions: [best-five evaluation](phase1-best-five.md).

## 2026-11-02 — Heads-up equity

- Expose fixed-opponent and uniform-opponent conditional showdown equity. Validate
  all known/dead cards jointly so card removal is shared across opponent/runout.
- Count exact states before enumeration and impose an explicit budget. Prefer
  bounded Monte Carlo for uniform-opponent preflop calculations.
- Define tie payoff as half a pot share. Separate outcome variance, estimated
  standard error, and fixed-budget confidence intervals.
- Use conservative Hoeffding intervals for bounded fractional payoffs; retain
  nonzero interval width at all-win/all-loss samples. No normal/binomial shortcut.
- Independently enumerate tractable reference cases with Treys and record fixed
  Monte Carlo seeds and simultaneous-coverage interpretation.

Details: [heads-up equity](phase1-equity.md).
