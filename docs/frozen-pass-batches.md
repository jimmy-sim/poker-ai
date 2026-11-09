# Frozen-pass batches: prospective issue #4 diagnostic

November 9, 2026. This plan and [config](../configs/frozen-pass-batches.json)
precede implementation and all new measurements. It follows the completed
[fallback diagnosis](window-fallback.md): one fixed fill changes little, so the
large sampled-training weakness remains unresolved. Codex-assisted; human
hands-on time is not recorded. No stronger agent has been established.

## Question and definition of done

Would averaging several independent sampled traversals before changing the
policy help at the same ten-million-node work limit? A traversal follows one
sampled part of the game tree. A batch holds the current policy fixed across B
traversals, averages their increments, then makes one learning update.

At a fixed policy, independent averages have less random variation. At fixed
total work, however, larger batches make fewer updates. Linear iteration weights
also advance less often. This comparison measures that combined tradeoff, not
the isolated causal effect of variance and not general poker playing strength.

Done means the math and behavior checks, complete fixed timing gate, published
admission, complete own study if admitted, independent scalar checks, reproducible
tables/figures and honest interpretation. A failed compute gate is a valid
stopping result; it does not authorize a smaller grid or changed scientific cap.

## Frozen design

Use both original known games, exact and range-mass q8 information groups, all
three original seeds, signed/clipped regrets and linear regret weighting. Batch
sizes are 1, 4 and 16. B4 with signed regrets and a linear average on q8 is the
primary diagnostic; B1 is its matched baseline and B16 a dose control. All other
predeclared contexts remain visible. No result becomes an agent/default or a
fresh/global admission in this diagnostic protocol, regardless of its ranking.

There are 72 unique external learning paths. Each stores uniform and linear
average ledgers because average readout weights do not influence learning.
Those are 144 dependent readout streams, not 144 independent learners. Three
work labels (100k, 1m, 10m) give 432 fresh saved profiles. Reuse the 48 original
full-tree work profiles once for controls: 480 scored and native-checked profiles.
Do not repeat deterministic full controls as seed replicates.

Retain 432 raw cumulative average ledgers and 216 raw current-policy observations
for read-only support/normalization/movement replay. Reconstruct the common warm
origin from its two frozen simultaneous uniform expected passes, without a
trainer or random draws. This storage clarification precedes measurements; it
adds no trajectories, scores or selection opportunities.

Keep the original simultaneous uniform exact warm start: iteration one, 2N
charged visits. Each later iteration runs target 0, then target 1. For each
target, freeze its policy across B independent external traversals; aggregate
sparse increments left to right, divide by B once, apply the original iteration
time weights and clip only after the mean when clipping is enabled. Charge
every visited node. Target 1 sees target 0's committed update. RNG objects remain
explicit; independent traversals use successive draws, not repeated seeds.

B1 calls the unchanged cached-node step. Both readout books must reproduce the
original state/policy/work/iteration/initialization prefixes bit for bit on
Python 3.11.17 / NumPy 2.4.6. The 24 baseline paths must pass all 144 original
readout prefix checks before any B4/B16 long path begins. Their time shares the
same 7200-second own deadline; the second phase does not reset it.

## Mathematical and software gates

- Exhaust the nonuniform Kuhn adaptive selector tapes for both players and
  positive/zero-support policies; compare raw update expectations to full passes.
- Exhaust B2 Cartesian products. Verify half the single-sample conditional
  component variance and unchanged mean. Demonstrate the clipping nonlinearity:
  clipping a mean is not averaging separately clipped samples.
- Compare independent dense frozen-batch trajectories with the cached backend,
  including both regret signs, weights, seeds, targets and zero support.
- Check both B1 average books against two original trainers without aliasing or
  observer mutation. Test exact crossing/charged work, serialization, partial
  grids, source-bound receipts, native schema/failures and barrier enforcement.
- Complete relevant local base/optional checks and both hosted code CI jobs
  before timing or any new postflop learning. Tiny toy fixtures are labeled as
  software checks, never Hold'em performance evidence.

## Compute gate, fixed before timing

Measure every 72 path three times (216 rows), with three spawned workers in
sorted identity index-mod-three partitions. Time construction plus exact warm
initialization, then at least 100,000 **additional** visited nodes at a whole
iteration crossing. Record work overshoots, CPU, runtime, raw state and ledger
hashes. Repetitions must have identical final states. Baseline timing also checks
the original total-work 100k prefix in both books: 144 repeated checks of 48
distinct readout identities, not independent confirmations.

For each path use the maximum of three extrapolated times:
`setup_and_warm + loop_seconds * (10m - initialization_visits) / actual_loop_visits`.
Compute the maximum partition sum for B1 and for B4/B16 separately, then add
them because the baseline barrier makes the phases sequential. The guarded
forecast is `2 * (2 * training_barrier_forecast + 600)` and must be **strictly
below 7200 seconds**. The timing stage has its own 900-second cap, includes input
validation, and produces no EV/strength scores. These prefixes are new learning;
they must not be described as a no-training check.

Publish correctness, every timing row and a checked source-bound admission
before the long study. Stop on a failed gate. Preserve incomplete/failing output.
Do not shorten the grid, alter seeds, reduce ten-million work, or relax allowances.
Profile a measured bottleneck and verify behavior before any later optimization.

## Evidence and limits

Record actual work, update count, selector traversal count, current movement,
average mass coverage (separating warm-only and newly visited rows), exact
exploitability, within-partition gain, extra information value, river weakness,
units and source/archive/runtime/CPU identity. Use every seed and arithmetic
means with seed points; three fixed seeds do not justify population confidence
intervals. Original failed gates and source/data remain byte-frozen.

Publish all own results before the independent audit. OpenSpiel 2.0.2's pinned
Apache-2.0 license is recorded in [solver validation](solver_validation.md);
recheck its bytes before use. Native EV/BR/achieved-own-reply scalars are
comparison-only. No reference strategy or probability enters learning. Its
separate 900-second cap includes required own replay and all 480 profiles.

## Tested software foundation — November 9

The opt-in updater, both average ledgers, guarded work observer, fixed timing and
admission readers, full own runner, raw archives, report and scalar-only native
adapter are implemented. Historical trainers, inputs and scientific limits stay
unchanged. No Hold'em prefix timing or new long trajectories have run yet.

101 focused fast checks pass. Both optional environments pass all 23 relevant
slow checks (37.05/36.96 seconds while base checks also ran). The complete
three-process nonuniform-Kuhn exercise saves/replays 480 profiles, 432 raw
cumulative ledgers and 216 current observations with zero numerical error.
Its 144 original baseline readout checks pass before larger batches begin.
Rehashed metric/mass/coverage corruption, missing/duplicate grids and a failed
baseline barrier are rejected. Fictional native/CI receipts test metadata
contracts only; they are not independent solver or hosted-CI evidence.

Four exact frozen-policy/target cases enumerate 54 single adaptive tapes and
972 within-case independent B2 tape pairs. Means and variance halving agree
within 2.8e-16 fixture units at the fixed 1e-12 tolerance. Clipping nonlinearity
is demonstrated. 120 toy checkpoints match the independent dense batch updater;
40 B1 checkpoints also reproduce both original average books exactly. These
are mathematical/software checks, not a poker strength result. Two existing own
Hold'em profiles separately pass the real native scalar adapter; no new learning
is involved in that adapter test.

Complete base checks pass 1647 tests plus 24 optional skips each
(230.21/230.30s); all-extras fast checks pass 1680 each (258.63/248.43s).
Lint/format, strict typing (381 files) and hooks pass. Both complete-code
[CI jobs](https://github.com/jimmy-sim/poker-ai/actions/runs/42606554182) pass on
`48c0960579db72a419835c1087a0e06440f7b897`; source inventory SHA
`62bbea13782a0d4468000fc01cbf34a83810fdc42c738098f1ec0a3f1dbb18cd`.
Base Python 3.12 loads every archived control/prefix with all learner and native
constructors blocked (4.568871s). Four software-only figures are inspected.

The formal [correctness receipt](../results/frozen-pass-batches/correctness.json)
passes in **6.3355535s** on that clean checked source, with all grids and zero
own replay error. This is source-bound software evidence, with no new Hold'em
prefixes or strength scores. Publish it and the observed code-check receipt
before the fixed timing stage. The 216-row timing/forecast and checked admission
still remain before long learning.

Safe read-only commands after the corresponding receipts exist:

```sh
.venv/bin/python scripts/check_frozen_batches.py --replay results/frozen-pass-batches/correctness.json
.venv/bin/python scripts/profile_frozen_batches.py --replay results/frozen-pass-batches/profile.json
.venv/bin/python scripts/report_frozen_batches.py --no-plots
```

The second command returns nonzero if the retained forecast fails; that is the
expected behavior for a failed gate. It never reruns training in replay mode.
The report command requires complete admitted own evidence; it does not convert
a partial grid into a result. Formal recording/reproduction commands and measured
outcomes will be added only after their gates are actually observed.

## Reading the figures

The curve figures use blue for B1, orange for B4, green for B16, and gray for the
reused full-tree control. Each large colored point is the mean of all three
fixed seeds. The faint points show each seed, including unfavorable ones. Moving
right spends more node work; moving down means less exact exploitability in that
small game. A downward curve is encouraging, but these known games and three
seeds do not establish a general playing edge. Actual work overshoots and update
counts are retained in `profiles.csv`; the x-axis shows the declared work labels.

The stacked-bar figures use colors differently: blue is gain available to a best
response using the learner's own information groups; orange is the additional
value available with finer allowed own-card/public-board distinctions. Together
they equal exact exploitability. Read the legend for each figure. These are
strategy/opponent-specific gaps, not a universal representation floor and not a
street-by-street causal diagnosis.

Rows show the two fixed games. Columns keep signed/clipped regret and
uniform/linear averaging separate. Exact and q8 encodings have separate figures.
Each panel has its own vertical scale, so compare its tick values as well as
bar heights. The raw seed table is the numerical record; the plots are summaries.
The uniform and linear readouts share a learning path and are not independent
learners. Matching a seed across B1/B4/B16 does not align the sampled histories
once their policies and number of updates differ.

Three questions to explain this investigation:

1. **Why might a larger batch help?** At one frozen policy it averages independent
   raw updates, reducing component variance by 1/B without changing their mean.
   The exact tiny-game enumeration checks this. It does not prove convergence.
2. **Why might it hurt at the same work?** Larger batches make fewer updates.
   Clipping and linear iteration weights interact with that change. The study
   measures the combined tradeoff; it cannot attribute an outcome purely to less
   sampling noise.
3. **What does the external check prove?** OpenSpiel independently computes
   values/best-response roots for the same bounded compiled game and evaluates
   our own replies. Agreement checks the algorithms and stored evidence. It
   does not establish a strong global Hold'em agent or independently validate
   every underlying engine payoff. Reference outputs never train the agent.
