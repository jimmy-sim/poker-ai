# Poker AI

A poker AI research project built from first principles, emphasizing expected
value, variance, statistical testing, and game-theoretic reasoning. Implementations
will be validated independently before any performance claims are published.

Current scope: Phase 1 includes card IDs, bitmasks, immutable decks, a
[five-card evaluator](docs/phase1-five-card.md), and
[six/seven-card best-five selection](docs/phase1-best-five.md). See the
[encoding contract and full phase acceptance gate](docs/phase1-cards.md).
Profile-guided direct evaluation and [heads-up equity](docs/phase1-equity.md)
are implemented; the game engine follows before solvers. The intended engine
supports 2–6 seats and side pots; research agents initially play heads-up.
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
The five-card evaluator has been checked against Treys over **2,598,960 hands**,
with **zero disagreements** across all **7,462 distinct ranks**. The category
census also matches independent combinatorial formulas. Reproduce with
`make validate-five`; see [the protocol](docs/phase1-five-card.md) and
[raw validation report](results/five-card-exhaustive.json). Full enumeration is
deterministic and uses no RNG.

Six/seven-card best-five selection matched Treys on
**2,000,000 seeded sampled hands** with **zero disagreements**:

| Cards | Sampled hands | Seed | Disagreements |
| --- | ---: | ---: | ---: |
| 6 | 1,000,000 | 20261103 | 0 |
| 7 | 1,000,000 | 20261104 | 0 |

Reproduce with `make validate-best`; see
[the protocol and limits](docs/phase1-best-five.md) and
[raw report](results/best-five-validation.json). These are sampled checks,
not exhaustive six/seven-card coverage. The game engine remains the next Phase 1 component.

The current direct rank-mask evaluator preserves the subset implementation as
`evaluate_best_reference`. It passed a separate two-million-hand revalidation;
see [performance methodology and paired measurements](docs/evaluator-performance.md)
and [direct validation evidence](results/best-five-direct-validation.json).
`make validate-best` now targets that direct evaluator report.

Exact and Monte Carlo [heads-up equity](docs/phase1-equity.md) passed five
predeclared reference cases. Exact outcome counts matched Treys; each configured
Monte Carlo interval covered its exact counterpart. Reproduce with
`make validate-equity`; see [raw counts and intervals](results/equity-validation.json).

Long validation sweeps use explicit configurations/seeds or deterministic complete
enumeration, with saved reports, separately from fast CI checks.

See [the roadmap](docs/roadmap.md), [design decisions](docs/decisions.md), and
[contributor instructions](AGENTS.md). Local setup verification is recorded in
[the Phase 0 report](docs/phase0-verification.md); hosted CI has not run yet.
