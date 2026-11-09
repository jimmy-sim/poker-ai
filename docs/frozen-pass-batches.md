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

No outcomes, compute admission, plots or stronger-agent claim exist at this
prospective checkpoint. Completion will add exact results, commands, limitations
and three interview questions with answers.
