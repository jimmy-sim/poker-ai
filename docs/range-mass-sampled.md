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

## Replay portability finding before the complete run

The first hosted checks (run 42446227294) fail in the prior full-control replay:
its diagnostic comparison requires exact equality on Linux. The locally passing
first sampled run was deliberately interrupted at 20/90 snapshots after 259.433
seconds and is retained in `results/range-mass-sampled-initial/`, with clean
source acd3941, incomplete status and no performance admission.

A new replay adapter leaves every historical source/config/evidence byte intact.
It permits absolute differences up to **1e-12 only for the three unitless
uniform-reach collision reductions**. Counts, key/table bytes, identities, contexts
and work remain exact (including types). Policy value/BR replay and native checks
retain the original **1e-9 chips** tolerance. This is a numerical replay repair,
not a change to the candidate or any learning/performance limit. The current
machine's recomputed replay error also does not define artifact identity: compare
bound study/audit hashes and the actual assessment instead. The error must still
pass its numerical tolerance. Two new regression tests cover these distinctions.
A complete rerun must use new checked source, all original seeds and budgets.

## Completed result

**The sampled development gate fails on the deeper game.** The exact controls
pass both games. The range-mass candidate passes low OOP but misses both fixed
accuracy limits on medium OOP. No budget extension, reseeding or feature tuning
was performed. [All tables and both plots](../results/range-mass-sampled/report/tables.md)
retain the complete five-control/two-game/three-seed/three-checkpoint grid.

| Medium OOP, final requested work 10m | Median exploitability (% pot) | Worst seed (% pot) |
|---|---:|---:|
| Exact | 0.233819 | 0.254711 |
| Raw-public | 0.233819 | 0.254711 |
| Texture | 7.369742 | 9.687537 |
| Category | 6.722857 | 7.188975 |
| Range mass | 4.480481 | 5.506634 |
| Fixed exact/candidate limits | 1.0 | 2.5 |

Candidate medium individual seeds, in declared order: **4.480481%, 5.506634%,
3.074980%**. Its low median is **0.00000102590%**, worst **0.000366736%**.
These are exact-game exploitabilities (NashConv/2), divided by initial pot and
multiplied by 100, not empirical win rates. Seed medians/ranges are descriptive;
three seeds do not establish a population confidence interval. The report's
`full-control-reference.csv` retains the unchanged earlier full controls.

All 90 bundled checkpoint/visit pairs replay, including source/config/context,
accumulators, policies, masks, scores and work counters. Own replay error is
**zero** on the recorded Mac. All 90 OpenSpiel value/BR comparisons pass; maximum
error **8.526512829121202e-14 chips**. The independent audit took **15.461 seconds**
including own replay; native output remains comparison-only. The archived engine
mechanics are shared with the reference, so this is not a separate engine proof.

The complete run took **1,254.790 seconds** (about 20.9 minutes), below 7,200.
All final initialized-average coverage is 100%; zero recall violations. Minimum
subsequently sampled uniform-reach coverage on medium is 97.60% for exact/raw,
98.29% texture, 97.77% category and 98.15% range mass. Low minimum is 80% for
all descriptions. Positive averaging after exact initialization and later sampled
visits are distinct facts; neither guarantees a strong policy.
All actual work receipts include initialization and whole-iteration crossing;
the largest recorded overshoot is 40 nodes. Profiles retain all 30 independent
fixed-seed timing repetitions. They do not feed the experiment's solvers.

## Source, storage and interpretation

[PR #19](https://github.com/jimmy-sim/poker-ai/pull/19) records the prospective plan,
checked implementation, real CI failure and retained interruption. Corrected source
**64c0d9de691fc8041c1bf47e12c0432c65e42061** passed local and hosted checks before
the complete run; its recorded dirty status is false. Raw study and own receipts
were published in **f8f4f67f84db608f1180e023a1de3f98029d4652** before the clean-source
native audit. Raw receipts remain unchanged after audit; the report combines them.
Input/config/model/context/lock/source hashes, runtime environment, counters and
package versions are retained in the JSON and gzip bundle.

The reviewed bundle is about 6.6 MiB and includes all 90 original checkpoint/visit
JSON pairs, making offline replay self-contained. Process peak RSS is
**3,008,036,864 bytes**, a cumulative high-water including trees, growing receipt
bundles and serialization, not isolated table memory or a per-representation cost.
Rows/key/table components remain in diagnostics; smaller row counts do not
establish lower total memory or a scalable global system.

The candidate improves medium median exploitability relative to category at the
same sampled work, but is still much weaker than raw-public and fails admission.
Its earlier full-tree result (0.271640% pot) is a separate training condition:
full CFR+ at 4,096 iterations versus linear external-sampling MCCFR at fixed node
work. Their difference does not isolate sampling variance, insufficient work or
representation error. Residual action-conditioned range distinctions remain a
hypothesis, not a newly measured causal explanation. No additional ablation,
fresh games, global training or default-agent change was run here.

**Next decision:** diagnose the saved candidate's exact versus within-partition
best-response gain, and inspect problematic decisions, before proposing a new
representation or larger training budget. Keep #4 open. This completed negative
experiment is the requested stopping milestone.

## Verification and questions

Corrected local `make check`: **886 all-extras tests** on Python 3.11.17/3.12.15;
base-only **857 passed, 20 optional skips**, including **41 new tests**. Ruff,
format, strict mypy and hooks pass. Hosted CI **42446699119** passes both Linux
jobs before the complete run. The previous failed run **42446227294** remains
linked; old source/evidence was not rewritten to hide it. Final evidence CI is
reported separately in the PR. Both plots have been visually inspected.

1. **Why can full-control admission pass while sampled learning fails?** The work
   budgets, traversal and update procedures differ. This result does not identify
   one cause. Diagnose the saved strategy before asserting that more compute fixes it.
2. **Why does 100% average coverage not mean the strategy is good?** Own exact
   initialization populates every row. A populated row can still have inaccurate
   action probabilities; sampled visits and exploitability answer different questions.
3. **What does the independent audit prove?** It checks that own saved policies'
   values and best responses agree numerically on the exported game. A correctly
   measured strategy can fail its strength target. It proves no general win rate.
