# Poker AI

A poker AI research project built from first principles, emphasizing expected
value, variance, statistical testing, and game-theoretic reasoning. Implementations
will be validated independently before any performance claims are published.

Current scope: Phase 0 development foundation. Poker mechanics, solvers, and
playing-strength results will arrive in the approved phase order. The intended
engine supports 2–6 seats and side pots; research agents initially play heads-up.
All gameplay is restricted to simulation and permitted public bot benchmarks.

## Development

Requirements: Git, Make, and [uv](https://docs.astral.sh/uv/getting-started/installation/)
0.13.5. uv can provision the Python version selected by `.python-version`.

From the repository root:

```sh
uv --version
make setup
make check
make hooks
```

`uv.lock` fixes resolved dependencies. `--locked` rejects stale declarations
rather than silently changing the lockfile. The Python baseline is 3.11; CI tests
3.11 and 3.12 on Ubuntu. Local hooks run the same locked Ruff installation as CI.

```sh
make format                              # Apply lint fixes and formatting
uv run --locked pre-commit run --all-files
```

## Layout

- `src/poker_ai/`: installable, typed Python package.
- `tests/`: unit, property, and reference-validation tests as phases progress.
- `configs/`: versioned experiment inputs.
- `scripts/`: reproducible experiment and validation entry points.
- `results/`: reviewed metrics and figures with provenance.
- `docs/`: roadmap, design decisions, and phase verification records.

The `src/` layout and pytest import mode check the installed package rather than
implicitly importing source from the working directory.

## Validation and results

The Phase 0 smoke test checks distribution installation and inclusion of the
`py.typed` marker. It makes no claim about poker correctness or playing strength.
Long validation sweeps will use explicit configurations and seeds, with saved
reports, separately from fast CI checks.

See [the roadmap](docs/roadmap.md), [design decisions](docs/decisions.md), and
[contributor instructions](AGENTS.md). Local setup verification is recorded in
[the Phase 0 report](docs/phase0-verification.md); hosted CI has not run yet.
