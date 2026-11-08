# Range-mass fixed-work sampled comparison

Issue [#4](https://github.com/jimmy-sim/poker-ai/issues/4), November 7, 2026.
Codex-assisted implementation/reporting; personal hands-on time not recorded.

## Question and definition of done

Does the range-mass candidate's full-control improvement survive ordinary external
sampling at equal node work? The unchanged
[`range-mass-protocol.json`](../configs/range-mass-protocol.json) already fixes
five representations, both known development games, three seeds
20261301/20261302/20261303 and 100k/1m/10m work checkpoints. Retain all 90 policies,
checkpoint accumulators/visit receipts and negative results. No feature, limit,
seed, game, action or averaging change is permitted by this milestone.

The [full-control admission](range-mass-admission.md) must replay and independently
pass before any sampled training. Bind its raw study/audit hashes and actual
checked assessment to this run; never feed its policies or native results into
the learner. New solvers start from one exact expectation of the own uniform
policy, then use ordinary external sampling, linear weighting and explicit
PCG64 generators. Work counts include the exact initialization (`2 * tree_nodes`)
and recursive visits. Finish the first complete iteration crossing each budget;
retain the previous count and actual last-iteration visits, never round down.

The existing 7,200-second cap includes setup, prerequisite replay, profiling,
initialization, training and receipt persistence. Profile each representation for
1,000 sampled iterations, three repeats of the first fixed seed, using separate
solvers that never feed the measured study. Record wall time, work, table/key
bytes, process-lifetime RSS and both initialized-average and subsequently sampled
coverage. The profile is a local timing observation, not a hardware-independent
speed claim.

At final work, exact and candidate must each have median exploitability <=1% of
initial pot and worst seed <=2.5%, on each game. All five final controls require
at least 95% uniform-reach average coverage and zero abstract-recall violations.
Require the complete grid, correct range/input/source/work bindings and all 90
OpenSpiel 2.0.2 (Apache-2.0) value/BR checks within 1e-9 chips. Reference outputs
are comparison-only; [license and shared-mechanics limits](solver_validation.md)
still apply. Three seeds are not a population confidence interval.

Publish checked runner, replay, audit, renderer and tests before measured outcomes.
Replay checkpoint accumulators and visits against each frozen policy, the declared
context and actual counters; independently audit every saved policy after training.
Generate curves (individual seeds and median at matched requested work) and tables
from fixed receipts, including overshoot and the unchanged full-control baseline.
Reviewed evidence lives in `results/range-mass-sampled/`; reruns and temporary
checkpoint files live under ignored `results/runs/` or nested `runs/`. Retain
compressed checkpoint receipts with reviewed evidence so replay needs no download.

Stop after audited development results and journal step 22, even if the gate
passes. Fresh-game admission, global training and default changes remain separate.
A failed gate is a completed investigation, not permission to retune this run.

## Commands and software receipts

`make study-range-mass` reproduces the fixed run, native audit and figures into
ignored `results/runs/range-mass-sampled/` in a clean checkout. Existing receipts
cause an error. The fixed 7,200-second budget is the training-stage cap; the native
audit and later offline report have separate timings. To publish reviewed evidence,
use the script defaults and commit the raw study/bundle before the clean-source
native audit. `make report-range-sampled` only replays and renders reviewed files.

The gzip bundle retains original own checkpoint and visits JSON for all snapshots,
plus their policy and masks. Replay loads the strict own-checkpoint format into
temporary files, verifies source/config/context and counters, recomputes probabilities
from accumulators, and compares both average/visit masks and all saved scores.
The crossing receipt is checked against actual checkpoint counters and the runner's
previous/last-iteration counters. It is not an independent rerun of every training
iteration. Hashes provide reproducibility/integrity, not cryptographic authorship.

Tests use a labeled one-game/one-seed/two-budget software fixture, with an explicitly
mocked prerequisite solely for that fixture. Production has no prerequisite bypass.
The actual published full-control prerequisite is also replayed in tests. These
fixtures measure software behavior and never establish learning strength.

## Status

Prospective plan published in [PR #19](https://github.com/jimmy-sim/poker-ai/pull/19)
before implementation/outcomes. All 39 focused tests pass. Local `make check`
passes 884 all-extras tests on Python 3.11.17 and 3.12.15; base-only checks pass
855 with 20 optional skips. Ruff lint/format, strict mypy and hooks pass.
No new research outcomes have been measured at this code-publication checkpoint.
