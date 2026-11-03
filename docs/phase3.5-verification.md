# Phase 3.5 acceptance — external solver validation

The bounded milestone is complete. This is an honest measurement gate, not a
playing-strength threshold: the own Hold'em prototype is substantially weaker
than the reference in these restricted games.

| Requirement | Actual evidence |
| --- | --- |
| Prerequisites/order | Phase 2 exact results and trained Phase 3 agents existed before execution; Tier A passed before Tier B. |
| Exact-game comparison | Four variants, Kuhn/Leduc at matched iterations; predeclared exploitability/L1/value/BR criteria passed. |
| Permitted independent reference | OpenSpiel 2.0.2 Apache 2.0, full license read/recorded; Treys 0.1.8 MIT helper license also read. No commercial data. |
| Fully specified spots | Five versioned turn subgames, two combos per range, dry/wet/IP/OOP/high/low SPR; all configured private pairs and rivers enumerated. |
| Reference convergence | Two consecutive scheduled checkpoints below 0.001 root pots of exploitability in every spot. Achieved epsilon/iterations retained. |
| Complete metrics | Weighted action MAE overall/street, every primary decision/class and public-node frequencies, both common-opponent EV gaps, native restricted-game BR/exploitability. |
| Diagnosis | Bucket/iteration curves, fallback EV identity, reference-policy stability, exact-information alias counts, matched-action and mechanics controls. |
| Honest weakness | Equal-spot/three-seed mean action gap 36.84 pp; higher restricted exploitability and lower hero EV versus the reference opponent in all five spots. No full-game win rate. |
| Reproduction/reporting | `make validate-solvers` reproduces all tables, every spot's heatmap and ablation plots; README summary, detailed writeup, generated claim drafts and three interview answers. |
| Numerical replay | 135 comparisons / 58,812 detailed decision rows reproduce exactly versus the first full run; five reference-policy artifacts byte-identical. |
| Local quality gate | Python 3.11: 421 passed. Python 3.12: 418 passed, 3 optional-reference skips. Ruff, strict mypy and all-file commit hooks passed. Hosted CI has not run. |

The final extended command ran from **clean `be1badc`** in **595.73 seconds** on
the recorded Apple M4 environment. Every experiment stage and the report renderer
recorded clean source provenance. Numeric replay excludes timing/provenance-bearing
checkpoint hashes and figure styling. Runtime is a local observation, not a
cross-machine speed claim.

See [the complete methodology, limitations and interview answers](solver_validation.md),
[run manifest](../results/solver-validation/manifest.json),
[raw comparison](../results/solver-validation/postflop.json), and
[numeric replay audit](../results/solver-validation/reproducibility.json).
The native parser/solver/BR are independent; mechanics/export remain own code.
Independent evaluator controls and earlier engine validation narrow that shared
mechanics risk without proving every possible Hold'em implementation property.

Reproduce from the repository root:

```sh
make check
make validate-solvers
uv run --locked python scripts/check_solver_reproduction.py \
  --reference-commit caf50a7 \
  --output results/solver-validation/reproducibility.json
```

The replay audit needs the retained Git history; the primary reproduction command
rebuilds its numerical results from configs/seeds and own training checkpoints.
No reference strategy is loaded into the own agent. Phase 4 may now measure actual
matches against declared baseline policies with duplicate-deal uncertainty.
