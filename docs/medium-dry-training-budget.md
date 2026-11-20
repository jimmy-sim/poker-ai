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

## Tested source and retained qualification failure

The isolated runner and decision report were committed at `1c3004d`. Before
the first full local role finished, source review found that the report
imported a decision-row helper from the earlier diagnosis without binding
that helper in this study's new fingerprint. The first base 3.11 run was
interrupted at 22%; its partial log and interruption receipt are retained,
not counted as a pass. Commit `7fe07e7` moved the observable-row decoder
into the new isolated module and added a focused equality check for all
three preselected turn rows. The historical 384-file river fingerprint is
unchanged.

On corrected source `7fe07e7`, exact-head serial local base Python 3.11
and 3.12 each passed 5,724 tests, with 73 skips and 150 deselections, plus
Ruff, formatting and strict mypy. Optional 3.11 passed 2,589 and optional
3.12 passed 2,587 with two expected skips; installed OpenSpiel/Numba/license
guards and all-file hooks passed. The first hosted source run passed 3.12,
but 3.11 was cancelled by the **unchanged 35-minute CI job limit** during
pytest at 98%. Its official log is retained. Relative to the preceding
passing hosted run, progress to 50% and 80% was about 1.5 times slower
throughout the suite; no assertion failure was reported. One documented
same-source rerun of only that cancelled software job completed within the
unchanged limit: [hosted CI 44713065490](https://github.com/jimmy-sim/poker-ai/actions/runs/44713065490)
now passes both Python jobs and hooks, each with 5,724 tests. The cancelled
attempt remains failed. The [source qualification archive](../results/medium-dry-training-budget/source-checks/manifest.json)
binds both hosted attempts, all local roles, the first interrupted local
attempt, guards and hook results. No scientific proof or policy measurement
preceded this source qualification. Next: publish and byte-verify that
archive, then run the fixed capped synthetic own proof.

## Synthetic own proof

The one fictional signal-game proof on published source fingerprint
`60ee266a...` captured and replayed all nine fixed policy readouts at work
labels 80, 240 and 720. It reached 720 charged node work and exited zero.
The locked command wall time was 0.312 seconds, below the 180-second cap.
The [proof archive](../results/medium-dry-training-budget/own-proof/manifest.json)
contains the 21 raw and receipt members with hashes, including the runtime
and command measurement method. This is a software proof, not medium/dry
poker-strength evidence. Next: publish and GitHub-byte-verify every proof
member before the fixed 18-path 1m profile.

## Fixed profile: compute admission rejected

The one preregistered 18-path profile completed all six arm/seed paths three
times at the first complete 1m-work crossing. All 54 own captures and
replays finished; three workers exited zero. The whole profile took
`66.369365708` seconds (<900), with actual final path work from 1,000,012
to 1,000,092 and recorded maximum worker high-water RSS 239,075,328 bytes
on this Mac. The [complete raw and failed-gate archive](../results/medium-dry-training-budget/profile-failure/manifest.json)
retains the snapshots, mass, events, worker messages, per-path timing,
forecast, launch traceback and decision.

The fixed rule took the slowest of each path's three whole-time
extrapolations to 100m work. The fixed worker sums were `2213.34556`,
`2212.45011` and `2213.98349` seconds, so `T=2213.98349`. The prescribed
strict bound was `2*(2*T+600)=10055.93398` seconds, **above 7,200**.
An independent data-only recomputation matched the archived forecast.
Thus the compute admission is **rejected** even though the 1m profile
itself completed well within its 900-second cap. The actual 100m runtime
is unknown; the conservative rule is the gate, not an estimate to waive.

This experiment ends here. No separate admission receipt, 100m own study,
native comparison or final paired poker-strength endpoint was run. The
result is **inconclusive for poker strength because a required compute gate
failed**, while the compute admission itself is a clear negative result.
PR #98's historical 10m medium/dry strength result remains negative under
its own frozen 1%/2.5% gates. No profile rerun, budget extension, looser
forecast, changed seed or representation follows from this outcome. The
profile contains fixed 1m software/compute readouts; they are not promoted
as a post hoc strength comparison.
