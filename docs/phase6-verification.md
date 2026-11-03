# Research snapshot packaging and bounded stopping point

November 3, 2026. The original Phase 6 contract is in the roadmap: architecture,
actual results and reproduction commands, a 2–3-page technical writeup, verified
resume drafts and interview answers. Those artifacts now exist. This packages
a research prototype; it does not accept the failed new performance gate.

## Actual verification

| Check | Result |
|---|---|
| Python 3.11.17 with optional extras | 542 passed |
| Python 3.12.15 with optional extras | 542 passed |
| Fresh baseline install, no optional extras | 525 passed, 8 skipped |
| Ruff lint/format, strict mypy, repository hooks | Passed locally |
| Historical frozen evaluation agents | All three load; encoder fingerprints unchanged |
| Frozen own-policy replay | 378 records; zero own replay error |
| Independent value/exploitability checks | Passed; unchanged 1e-9-chip tolerance |
| Full diagnostic reproduction | Completed in 1668.27 seconds; heldout_gate_failed |
| New global comparison | Not launched; prerequisite failed |
| Hosted CI / remote push | Neither performed |

`make validate-holdem-learning` was run end to end. It retrained all four 300k
controls, checked them independently, trained representation/held-out games,
checked frozen policies and regenerated tables/plots. Every own policy artifact
and non-timing training metric agrees exactly with the earlier reviewed study.
The nonzero Make result comes from the performance miss, not a numerical failure.
The rerun remains under `results/holdem-learning/runs/20261103T100048.069770Z/`
in the retained worktree; its metadata is also reviewed in
`results/holdem-learning/reproduction.json`.

The medium-IP held-out median remains **0.01015285879237701 pots**, exceeding
the preset <=0.01 target. The [diagnostic writeup](holdem-strength-v2.md) retains
all failures and controls, coverage caveats, cross-play EVs and numerical checks.

## Deliverables and preservation

- [README](../README.md): architecture, real results, figures and commands.
- [Three-page technical brief](research-brief.pdf): methods, results, failures and
  limits. All pages were rendered and visually inspected; text, page count and
  artifact hash checked. Bundled ReportLab 4.4.9 produced the PDF; input/artifact/
  build-script hashes are in `results/holdem-learning/research-brief-provenance.json`.
- [Four verified resume drafts and interview guide](interview-guide.md).
- [Diagnostic tables](../results/holdem-learning/report/tables.md), figures and
  machine-readable audit. `make report-holdem-learning` regenerates these offline
  from committed own policies, separately reporting the failed performance gate.

Large checkpoints, interrupted runs and preserved unexpected duplicate files stay
in ignored staging in the retained worktree. The normal project keeps the small
reviewed artifacts needed for reporting. The user's nine regenerated Phase 5
files were copied and hashed before merging; they remain user changes. Historical
source/dirty metadata is not rewritten to look clean.

No real-money integration, new public API games, external-teacher training or own
C++/Rust core was added. Optional own Python/Numba follows profiling. Existing
engine/evaluator/card-action encoding files remain unchanged.

## Next work and three interview answers

1. **What is complete?** The bounded diagnostic, independent checks, reproducible
   evidence and research packaging. Its performance target failed; the global
   policy has not been upgraded or shown to be winning.
2. **Why stop this experiment here?** Every declared budget/control completed.
   Extending until a held-out score passes would turn that game into tuning data.
   All four games are now known; a revised procedure needs fresh preregistered
   hold-outs and unchanged accuracy limits.
3. **What next?** Validate expected updates for river-integrated sampling, compare
   at fixed node budgets, then test fresh games before the gated global study.
   Public-aware abstraction also needs memory/coverage/generalization tests;
   tiny exact-board solutions do not establish global strength.
