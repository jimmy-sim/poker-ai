# Prospective clipped-regret test on two known river spots

**Issue #4; parent PR #99. Protocol status: prospective; no new proof,
profile or training outcome has been collected.** The frozen machine contract
is [medium-dry-clipped-regret.json](../configs/medium-dry-clipped-regret.json).
The experiment asks whether clipping negative accumulated regrets helps the
unchanged exact-river learner reduce remaining best-response gains at fixed
work. A best response chooses a legal reply against a fixed saved strategy;
exploitability here is half the two players' gains, divided by the initial pot.
Lower is better. Clipping prevents the regret ledger from carrying negative
values into the next update; it changes the learning rule, not the cards,
actions, representation, evaluator or work budget.

PR #98's medium/dry 10m linear-average candidate missed the frozen 1% median
and 2.5% worst exploitability gates. Its saved diagnosis found zero candidate
turn or river information collisions on this finite spot, with remaining
turn/river losses and a large current-versus-average gap. PR #99's unchanged
100m follow-up was stopped by its conservative 7,200-second compute admission.
Earlier clipped-regret work on another known game was mixed: one averaging
choice improved and another worsened exploitability. Thus clipping is a
distinct convergence hypothesis, not an established fix or a cheaper retry of
the rejected 100m design. Both selected spots and all three seeds were used
before; they are **known**, not unseen or held out.

## Frozen comparison and decision

Use `new_low_wet_ip` and `new_medium_dry_oop` with their byte-identical
published spot inputs and `q8_turn_exact_river` representation. Train the
signed/linear/linear control and clipped/linear/linear candidate independently
from seeds 20261371, 20261372 and 20261373, with IID B4 external sampling,
batch size four and target order 0 then 1. Match first complete charged node
work crossings 100k, 1m and 10m; preserve actual overshoot. The primary
endpoint is each final 10m linear-average restricted-game exploitability as a
fraction of initial pot. Report each seed and clipped-minus-signed paired
difference, median and worst for each spot. Also retain current and uniform
averages, coverage, recall, work, memory and runtime; do not select a favorable
readout after inspection.

**Positive:** the clipped final medium/dry median is at most 1%, worst at most
2.5%, and its paired median is at most -0.001 initial pots; low/wet also meets
the same absolute gates and has paired median at most +0.001. Coverage must be
at least 95% and recall violations zero. **Negative:** any absolute gate
fails, medium/dry paired median is at least +0.001, or low/wet paired median
exceeds +0.001. Other complete outcomes are inconclusive. These are local
known-spot gates, not default admission or population-level evidence. Preserve
the three preselected medium/dry turn rows 2443/1596/14 and aggregate turn/
river best-response-loss contributions as diagnostics, with opponent and
continuation assumptions stated. They do not alter classification.

## Qualification, compute and publication

Isolate new code in a new adapter; leave all historical source pins, protocols,
receipts and results unchanged. Qualify tested source with the applicable
correctness, exact-source local base/optional, hooks and hosted checks. First
run one capped fictional signal-game proof (<180 seconds). Publish and verify
its raw output before the fixed 36-path, three-repeat, 100k-work profile
(<900 seconds). For each of 12 game/seed/arm paths, use the slowest of its
three complete construction-through-replay times scaled to 10m/actual work.
Sum these 12 maxima in the fixed index-modulo-three worker partitions; let
`T` be the largest sum. Publish a separate data-only decision and admit the
one 12-path own run only if `2*(2*T+600)<7200` seconds. The whole own run has a
7,200-second cap; the comparison-only native scalar audit has 900 seconds
and tolerance 1e-9 chips. Retain peak RSS, fixed three spawned workers and
failure-save cap 120 seconds. A failed gate ends this experiment.

Publish and byte-verify complete or partial own raw policies and scores before
any pinned OpenSpiel 2.0.2 Apache-2.0 scalar audit. Reference outputs remain
comparison-only and cannot enter training. Recompute all readouts from saved
bytes and complete final exact-source checks. Do not search seeds, change
thresholds or budgets, retry an unfavorable scientific result, promote a
default or call these known spots unseen. Earlier PR #98 and #99 failures
remain visible regardless of this outcome.
