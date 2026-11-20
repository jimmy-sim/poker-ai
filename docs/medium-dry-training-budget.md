# Prospective medium/dry training-budget study

## Definition of done

Classify one bounded longer-work study of the **unchanged** river candidate
on the already inspected `new_medium_dry_oop` spot. Complete the published
source, compute, own and comparison-only gates; retain all six paired paths,
checkpoints, failures and decision examples. Report whether additional work
gets the candidate below the historical 1% median and 2.5% worst
exploitability limits, and whether it still beats the unchanged q8 control
at matched work. This finite, previously used spot is not unseen poker and
cannot establish global strength. No outcome promotes a default.

PR #98's fixed 10m comparison was **negative** under those absolute gates:
candidate median/worst were 3.566%/3.954%. Its retained diagnosis showed no
turn or river information collision in this spot. The three largest turn
rows were exact indices 2443, 1596 and 14, while the river supplied 75.51%
of remaining candidate loss in aggregate. Falling saved exploitability
through 100k/1m/10m suggests possible incomplete convergence, but does not
prove more work helps. This study answers that specific question. It does
not erase PR #98's failed result or repurpose its 10m evidence as a fresh
sample.

## Fixed inputs and readouts

The machine contract is
[`configs/medium-dry-training-budget.json`](../configs/medium-dry-training-budget.json).
Use the frozen medium/dry board/ranges from PR #98, control
`texture_range_q8_b8`, candidate `q8_turn_exact_river`, and seeds
20261371–73. Independently restart each arm and seed using the same IID B4
external sampler, signed regrets, linear regret and average weights, batch
size four, target order 0 then 1 and one charged exact-uniform iteration.
No saved-policy warm start or training-rule change. Three spawned workers
receive six paths by index modulo three. Capture the first complete crossing
of 10m, 30m and 100m node work, including overshoot, with current, uniform
and linear-average readouts. The original saved 10m policies are historical
context, not a substituted checkpoint. Pairing seed labels controls the
setup but does not make sampled trajectories identical after policies differ.

The primary endpoint is 100m **linear-average exact restricted-game
exploitability**, NashConv/2 divided by initial pot, where lower is better.
Report all six values and three signed candidate-minus-control seed pairs
at every checkpoint. At the endpoint, also report median and worst candidate
and control scores, reach coverage, recall, information rows, four-float64
table bytes, actual work/overshoot, path time and peak resident memory.
For each checkpoint and seed, decompose both responding seats' saved-prefix
best-response gains by exact information row: rows 2443, 1596 and 14
individually, and all turn versus all river rows. Divide unilateral gains by
two so their sum is NashConv/2, checking the accounting within 1e-9 chips.
The opponent stays at the fixed saved policy while the responding seat may
optimize its own later decisions. These contributions diagnose the finite
game; they are not universal action advice or a causal attribution to the
representation.

The **positive** decision requires candidate endpoint median ≤1%, worst
≤2.5%, positive-average reach coverage ≥95%, zero recall violations, and
median of the three signed paired seed differences ≤−0.001 initial pots.
It is **negative** if the candidate fails any absolute gate or the paired
median is ≥+0.001. All other complete results are **inconclusive**. Apply
and report the same absolute gates separately to the control. Report the
three fixed turn rows and aggregate river trend regardless of classification;
do not turn them into post hoc acceptance criteria or select favorable
decisions. These descriptive thresholds do not establish a confidence
interval from three dependent seeds.

## Compute and publication gates

Existing 10m whole paths took about 76–77 seconds on this spot, so a linear
100m extrapolation suggests roughly 26 minutes for three workers with two
paths each;
that is planning context only, not compute admission. Before the long run,
publish tested isolated source and pass the exact-source local Python
3.11/3.12 base and optional checks, installed license guards, all-file hooks
and hosted CI. Publish and byte-verify one synthetic own proof under 180
seconds. Then profile all six paths at 1m work three times each: 18 complete
paths under 900 seconds, including context construction, capture, scoring
and replay. For each path take the **maximum** of three whole times scaled
by 100m/actual work. Sum those maxima in the fixed worker partitions and
set `T` to the largest sum. A separately published admission must require
strict `2*(2*T+600)<7200` seconds. A failed forecast ends this study; do not
rerun the profile for a better estimate. The one own long run has a 7,200
second whole cap and 120 seconds for failure saving.

Publish and GitHub-byte-verify all complete or partial own raw policies and
scores **before** constructing pinned OpenSpiel 2.0.2 comparison-only
references. Verify its installed Apache-2.0 license and independently audit
every planned own value/reply/exploitability scalar within 1e-9 chips under
900 seconds. Reference policies, actions and values cannot enter own
training. Reproduce the final report from published data, complete final
local/optional/hosted checks and retain all errors. No extra seed, path,
budget, threshold, representation adjustment or scientific retry follows an
unfavorable outcome. A software defect may be corrected only with retained
failure evidence and full requalification. The exact decision-inspection
command will be published with the measured report.

At this prospective checkpoint, no new training, profile, proof or outcome
has been collected. Codex assisted; human hands-on time is unrecorded.
