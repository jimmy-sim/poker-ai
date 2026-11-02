# Design decisions

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
