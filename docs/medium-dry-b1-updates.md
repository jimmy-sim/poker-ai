# Prospective batch-one update-frequency test on two known river spots

**Issue #4; parent PR #100. Status: prospective, before new candidate proof,
profile or training outcomes.** The frozen machine contract is
[medium-dry-b1-updates.json](../configs/medium-dry-b1-updates.json).
This distinct question asks whether applying signed-regret updates after
one external sample rather than a batch of four improves saved poker
policies at the **same charged node work**. Smaller batches give more
updates at that work budget, but each update is noisier. The representation,
card/range inputs, regret rule, averaging, evaluator and work counter stay
fixed. Both spots and all three seeds are **known**, not unseen or held out.

PR #98's exact-river medium/dry 10m candidate failed the frozen 1%/2.5%
exploitability limits. Its saved diagnosis found no information collisions
on this finite spot, but large turn/river best-response gains and a very
weak latest policy relative to the average. PR #99's 100m study failed its
conservative compute admission without a poker-strength result. PR #100's
clipped update worsened every matched seed on both known spots. An earlier
*different* exact known game had lower mean 10m signed exploitability with
B1 than B4, while its abstract games were mixed; that is hypothesis
motivation, not evidence that B1 helps this medium/dry spot. This experiment
changes update frequency and sampling variance, not the rejected clipping
rule or the disallowed 100m budget.

## Frozen comparison and decision

Train one B1 signed/linear-regret/linear-average candidate for each of
`new_low_wet_ip` and `new_medium_dry_oop` at seeds 20261371, 20261372 and
20261373, with IID external sampling, exact uniform initialization, and
target order 0 then 1. The control is the already published B4 signed path
for the same spot/seed from PR #100, bound by own commit `ef3ac5d`,
`results/medium-dry-clipped-regret/own/manifest.json` SHA-256
`82ec824335129f41316d88103c8d07ce5bf8d496ad42e2b98e44daf84fe9333d`,
and comparison-only native audit commit `804f35d`. Reuse those six immutable
control policies once; do not retrain or select them. Both arms use the
unchanged `q8_turn_exact_river` key. The same seed labels the pair, but B1
and B4 consume different sequences of random draws, so paired-seed
variation is not a common-random-number confidence interval.

Stop at the first complete charged-node-work crossing of 100k, 1m and 10m;
retain overshoot. Save current, uniform-average and linear-average policies,
but preselect the **final 10m linear average** as primary. Exploitability is
restricted-game NashConv/2 divided by the initial pot, lower being better.
Report each final seed and B1-minus-B4 paired difference, medians and worst
per spot, coverage, recall, work, memory and runtime. Keep the previously
selected medium/dry turn rows 2443/1596/14 plus aggregate turn/river
best-response-loss contributions as diagnostics; state fixed opponent,
reply continuation and reach assumptions. They cannot change classification.

**Positive:** B1 medium/dry and low/wet each meet the unchanged 1% median,
2.5% worst, 95% positive-average coverage and zero recall-violation gates;
medium/dry paired median is at most -0.001 initial pots and low/wet paired
median at most +0.001. **Negative:** any absolute gate fails, medium/dry
paired median is at least +0.001, or low/wet paired median exceeds +0.001.
Other complete outcomes are inconclusive. These known finite games do not
justify a default promotion or a population-level claim, even if positive.

## Qualification, compute and publication

Keep new B1 code in isolated modules/adapters. Do not change historical
source pins, PR #100 source/receipts/results or frozen protocols. Test B1
work/seed identity, exact signed-rule behavior, capture/replay, completeness,
forecast and fixed decision logic. Complete exact-source local base 3.11/3.12,
optional 3.11/3.12, hooks and hosted checks before science. Run one fictional
B1 software proof under 180 seconds and publish/byte-verify its raw output.
Then run the fixed 18-path, three-repeat, 100k-work profile under 900
seconds. For each of six candidate paths, use the slowest of its three
complete construction-through-replay times scaled to 10m/actual work. Sum
these six maxima in fixed index-modulo-three partitions of three workers;
`T` is the largest partition sum. Publish a separate data-only admission
receipt, and train only if strict `2*(2*T+600)<7200` seconds. The whole six-path
own run has a 7200-second cap; the pinned OpenSpiel 2.0.2 Apache-2.0
comparison-only scalar audit has a 900-second cap and `1e-9`-chip tolerance.
Retain partial/failing results and 120 seconds for failure-save containment.

Publish and GitHub-byte-verify complete or partial B1 own raw policies and
scores before constructing any new reference comparison. The old B4 control
and its independent audit remain read-only. Recompute all candidate and
control scores from their saved bytes and complete final exact-source local,
optional and hosted checks. A failed source, compute or numerical gate ends
this experiment with evidence retained; a negative poker outcome will not be
retried with new seeds, work, representation or criteria to seek a positive
result. Do not promote a default or describe these cases as unseen.
