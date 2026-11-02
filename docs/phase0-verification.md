# Phase 0 verification — 2026-11-02

## Acceptance and observed results

The approved development foundation is implemented. All local acceptance checks
pass. No poker implementation or playing-strength experiment has been run.

| Check | Observed result |
| --- | --- |
| Python 3.11.17: locked install and `make check` | Pass: Ruff lint/format, strict mypy, 1 smoke test |
| Python 3.12.15: clean staged source copy, locked install and `make check` | Pass: Ruff lint/format, strict mypy, 1 smoke test |
| `pre-commit validate-config` | Pass |
| `pre-commit run --all-files` | Both Ruff hooks pass |
| `make hooks` | Repository-local pre-commit hook installed |
| `uv build --offline` | Source distribution and wheel built successfully |
| Wheel installed into the isolated Python 3.12 environment | Smoke test passes; package imports from site-packages |
| Workflow YAML syntax and proposal checks | Parses; main push trigger, read-only permissions, and matrix match |
| Hosted Ubuntu GitHub Actions | Pending a push to a remote repository |

Environment: macOS 27.2, ARM64, uv 0.13.5. Both interpreters, the bootstrap uv,
caches, and the clean validation copy were provisioned inside the enclosing
workspace. The repository's `.venv/` is ignored.

Lockfile SHA256:
`9b680f3afdea4e808ff0f396eb27b01c79814bfb11e46114825508a3c63e0dbd`

The universal lockfile selects NumPy 2.4.6 on Python 3.11 and 2.5.4 on Python 3.12
using Python-version markers. Both selections are locked. Future experiment
reports must record the actual interpreter and resolved environment.

## Reproduce the routine checks

With uv 0.13.5 on PATH, run from a fresh clone:

```sh
make setup
make check
make hooks
uv run --locked pre-commit validate-config
uv run --locked pre-commit run --all-files
uv build
```

Exercise both Python versions locally, replacing the virtual environment as
needed; restore the default Python selection afterward:

```sh
for poker_python in 3.11 3.12; do
    UV_PYTHON="$poker_python" make setup
    UV_PYTHON="$poker_python" make check
done
make setup
```

To repeat the wheel smoke test using the locked development environment, after
`make setup` and `uv build`, replace the editable package with the wheel and
restore editable development afterward:

```sh
uv pip install --python .venv/bin/python --no-deps --reinstall \
    dist/poker_ai-0.1.0-py3-none-any.whl
.venv/bin/python -m pytest -q -m 'not slow'
make setup
```

No seed is required for these deterministic packaging checks. Later stochastic
validation must use explicit seeds.

## Limits of this evidence

The smoke test establishes installation and type-marker inclusion. It cannot
establish poker correctness or solver quality. A local YAML parse cannot establish
that hosted actions execute successfully; actual Ubuntu CI remains unverified.

## Interview questions

1. **Why use a src layout?** It prevents accidental imports from an uninstalled
   source tree, helping tests reveal packaging and installation mistakes.
2. **Does a lockfile make an experiment reproducible?** It fixes dependency
   resolution, but we must also record interpreter/platform, source revision,
   configuration, seeds, and raw evidence. Statistical uncertainty is a separate
   requirement from repeatability.
3. **Why separate large validation sweeps from CI?** Fast checks provide timely
   regression feedback. Large independent-reference sweeps provide broader
   evidence at phase gates; small deterministic regressions still belong in CI.

## Next step

Phase 1 begins with card encoding and deck invariants. Define valid card IDs and
52-bit card sets, test uniqueness and rejection of invalid/duplicate inputs, and
establish an explicit-RNG shuffle interface before implementing hand evaluation.
