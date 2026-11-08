# Compute gate for the controlled training comparison

Issue [#4](https://github.com/jimmy-sim/poker-ai/issues/4), November 8, 2026.
Codex-assisted; personal hands-on hours not recorded.

## Question and stopping point

Can the common trainer support the preregistered comparison within its two-hour
own-stage cap? Profile before optimizing or starting that study. This milestone
measures training cost, records hotspots, and stops at verified profiling evidence.
No EV/exploitability is measured, no winning arm selected, and no playing-strength
or training-cause claim follows. The prior failed learning gate remains.

The [profile config](../configs/controlled-training-profile.json) binds the
unchanged [comparison protocol](training-isolation.md) and correctness receipt.
Historical trainers, mathematical source, game inputs and policies remain
unchanged. The correctness CLI keeps its behavior through an explicitly pinned
entrypoint compatibility bridge. This is orchestration around the existing trainer, not a new update
algorithm. Profiling's short training traces are discarded; only state digests
and work counts remain as timing-repeat checks, not deployable policies.

## Fixed workload before timing outcomes

Use both known games, exact and range-mass groups, all eight rule combinations
(clipping, regret time weight, average time weight), and both traversals. All
three original seeds are used for external sampling; full traversal has one
deterministic cell. This gives 32 full and 96 external cells. Add the three unique
full-only bridge predecessors for each game/representation: another 12 cells.
The final bridge endpoint is the corresponding common full cell, not a repeated
independent observation. **140 cells × three timing repetitions = 420 rows**.

Every repetition uses a fresh trainer/RNG. Warm starts are charged and timed
separately. Time 1000 additional iterations for external sampling and 16 for full
traversal. Count actual node visits, chance and terminals included. Record final
iteration, regret/average/policy and RNG digests, initial/total/incremental work,
uniform dimensions and environment. Repetitions of one cell must reproduce those
deterministic diagnostics exactly on this environment. Do not interpret three
timing repetitions as independent poker experiments.

Use `cProfile` separately on four fixed first-seed candidate cases: full
clipped/unit-regret/linear-average and external signed/linear/linear, in each
game. Save the top 25 cumulative-time functions, self time and call counts.
Instrumented times do not enter speed/forecast estimates. Cumulative function
times overlap; do not sum them as independent cost components.

## Forecast and gate, fixed in advance

For each cell, estimate training to 10m total visits by initialization time plus
remaining visits × observed seconds per incremental visit. Use the **maximum**
of three per-cell estimates; sum all 140 cells. Multiply by a fixed 2× planning
guard. The 100k/1m and iteration 16/64/128 views lie on those same trajectories;
do not charge separate full runs. This assumes approximately stable visit cost.
Policies and visit distributions change later, so this is an environment-specific
planning extrapolation, not an upper bound or confidence interval. Setup, scoring,
checkpoint serialization and native audit are not extrapolated from training.

If guarded training alone exceeds 7200s, report
`training_only_guarded_forecast_exceeds_cap`. Otherwise report
`unresolved_unmeasured_pipeline_cost`. Neither admits or launches the full study.
Keep every cell, seed, slow timing and failure. No best-seed/arm filtering,
iteration/budget extension, feature change or changed learning gate. Own profiling
has a separate 900s cap including setup, correctness replay and instrumented runs;
retain incomplete data if exceeded.

## Replay compatibility

PR #22's original replay requires its source manifest to equal today's complete
source-file inventory. Adding the profiling library therefore requires a
versioned adapter. The full old receipt is pinned byte-for-byte. The adapter
checks every old source hash except its CLI entrypoint, whose old and new hashes
are explicitly recorded in the profile config. Only that CLI's import/dispatch
changes; the old checker, update equations and numerical receipt are untouched.
It reruns the old mathematical evidence and checks typed identities and its
1e-12 numerical bound. Newly created correctness receipts retain original replay.
Tests exercise the existing terminal command, changed source and changed data.
This compatibility revision was defined before profiling outcomes.

## Acceptance and reproduction

- Publish tested script/config before timings; source must be clean.
- Replay the pinned correctness receipt and verify all pinned inputs before and
  after profiling. The earlier terminal replay command must still work.
- Require the complete 420-row timing grid and four distinct profiler cases,
  exact repeat identities/state digests and integer work accounting.
- Test cell enumeration, bridge deduplication, forecast arithmetic/guards,
  missing/duplicate/tampered rows and incomplete receipts. Timing values themselves
  cannot be reproduced exactly; reporting validates recorded measurements and
  recomputes forecasts rather than pretending to replay wall time.
- Pass applicable lint/format/typing/tests, hosted CI and update journal/work log.
- `make profile-controlled-training` writes fresh ignored results and refuses
  overwrite. `make report-controlled-training` checks recorded evidence and emits
  timing/forecast tables. Neither produces a trained-agent strength result.

Stop after verified timing evidence and an explicit next decision. Any subsequent
optimization must target measured hotspots and preserve update/RNG/work semantics
before a learning run; no optimization is part of this initial profiling gate.

## Implementation checks

Thirteen new tests plus the previous twenty focused tests pass. Full local
checks pass 977 all-extras tests each Python 3.11.17/3.12.15; base-only 944 with
24 optional skips. Ruff lint/format, strict mypy (246 files) and hooks pass.
Hosted CI was running when timing collection began; it is tracked separately
from the completed local checks. No scoring/learning comparison was launched.

## Three questions to explain the compute gate

1. **Why not just start the big experiment?** A short, fixed profile can reveal
   that training alone exceeds the compute cap before spending hours on an
   incomplete comparison. We retain failures instead of trimming inconvenient arms.
2. **Does repeating a timing reproduce the same wall time?** No. We verify the
   same final algorithm/RNG state and work, retain all times, and use a predefined
   planning rule. Timing noise is not poker-strength uncertainty.
3. **Does passing the forecast establish strength or feasibility?** Neither.
   Strategy scoring/checkpoint costs remain unmeasured and the forecast can
   change as later policies change. Only a complete audited learning comparison
   could support its specific strategy claims.

## Recorded compute gate

All **420 timing rows**, **140 cells** and **four instrumented cases** complete
from clean `44da3984b3d9c618887e77b9a656895d597a502c`. Every repetition and
instrumented case matches its deterministic algorithm/RNG-state digest and
work. Total profiling wall time **179.069551s**, below 900s; tree/representation
setup **1.948073s**. [Raw evidence](../results/controlled-training-profile/profile.json)
and [derived tables](../results/controlled-training-profile/report/tables.md).

| Quantity | Seconds | Hours |
|---|---:|---:|
| Training-only forecast, summed per-cell maxima | 15,235.392 | 4.232 |
| With predefined 2× planning guard | 30,470.783 | 8.464 |
| Existing complete own-stage cap | 7,200 | 2.000 |

Decision: **`training_only_guarded_forecast_exceeds_cap`**. The projected hours
were **not spent** running the full comparison. They exclude setup, scoring,
checkpoint and native-audit costs and are not a statistical bound. Later policy
changes can change visits and per-visit cost. All arms/seeds/slow repetitions
remain; no budget, seed or learning gate was changed to accept the workload.

### Measured hotspots and next decision

External cells contribute **98.395% of the training-only forecast**. In the fixed
medium candidate's external signed/linear/linear profiler case, `current_policy`
is called **2000 times in 1000 additional iterations** and accounts for **49.43%**
of instrumented `step` cumulative time. The low candidate case is **20.26%**.
The nested `normalize` routine scans the full table; its time is already included,
so these fractions must not be added together. These are instrumented, first-seed
case observations, not an attribution across every arm or a promised speedup.
Menu reconstruction, recursive traversal, random selection and update validation
also cost time. Full traversal's hotspots include expected-pass evaluation and
update validation, but its aggregate forecast is much smaller.

Next: an opt-in sampled implementation that avoids repeated whole-table policy
construction and measured menu overhead, with exact state/RNG/work equivalence
tests against this frozen trainer. Reprofile before launching the unchanged
learning comparison. One optimization may not suffice; do not promise the cap
will pass or change semantics to force it. No optimizer was implemented here.

The complete report is regenerated from the same recorded receipt on Python
3.12; summary, both CSVs and Markdown table are byte-identical to Python 3.11.
This verifies reporting, **not reproducibility of wall time**. The original
correctness CLI still reproduces its frozen values through the tested bridge.
The cause of the river weakness and any strength improvement remain unmeasured.
