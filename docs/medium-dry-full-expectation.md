# Full expected updates at matched work on two known river spots: prospective

**Issue #4; November 23, 2026 (PST).** This protocol and its [machine
contract](../configs/medium-dry-full-expectation.json) precede all new full-pass
proof, profile, training or score measurements. The two spots, cards, ranges,
actions and three B4 control seeds have been inspected repeatedly. Neither is
unseen. No default agent changes from this experiment.

## Definition of done and question

The [saved-policy diagnosis](river-generalization-diagnosis-report.md) found no
information-key collision on the finite medium/dry candidate, while its river
decisions carried most remaining best-reply gain. The [B1](medium-dry-b1-updates-result.md)
and [B8](medium-dry-b8-updates-result.md) signed-update comparisons changed
stochastic batch size and both missed the same 1% medium/dry target at 10m
charged work. B8's three medium/dry final seeds were mixed; this does not
prove sampling noise is the cause. Earlier [full-tree CFR+ controls](river-fixed-work.md)
passed on different known games but were diagnostic controls, with a different
regret rule and no matched-work treatment here.

**One distinct question:** at the same charged node work, does replacing IID
batch-four external-sampling passes with their complete expected passes improve
the two known river-spot policies under the **same signed regret, linear regret
weight and linear average**? Full expectation removes trajectory sampling noise
but spends more work per policy update. This compares traversal mechanisms;
it is not a favorable B8 retry, a batch-size sweep, or evidence of scalable
full-game play.

Done means an isolated adapter with independently checked pass arithmetic and
capture/replay, full exact-source local/optional/hooks/hosted qualification, one
fictional proof, a fixed three-repeat compute profile and separate strict
admission, at most one admitted two-path own study, own-before-reference
publication, all fixed metrics/decision rows, final checks and an honest
positive, negative or inconclusive classification. Any failed source, compute,
numerical or publication gate stops this experiment with partial evidence.

## Fixed cases, control, candidate and work

Use exactly `new_low_wet_ip` and `new_medium_dry_oop` from the published
[PR #98 spot freeze](../configs/river-generalization-freeze.json), in that
order. Medium/dry is the known strength failure; low/wet is the known
nondegradation check. Both use unchanged `q8_turn_exact_river`, game trees,
private ranges, boards, chance probabilities, action menus, evaluator and
card model. Do not select, replace or label a case unseen after looking at new
candidate outcomes.

The immutable B4 control has seed labels **20261371, 20261372, 20261373**,
own commit `ef3ac5d03b87659fefc84206521412a289821786`, manifest SHA-256
`82ec824335129f41316d88103c8d07ce5bf8d496ad42e2b98e44daf84fe9333d`,
native-audit commit `804f35dd57c7b01f9d517ef2cf2ee90c957e4b81` and
manifest SHA-256
`4a2d2e5b143872e2c168a7dd8f5c327227faab7b5f1ca175327417fedf375f0a`.
Read those three control paths per spot without retraining. Their pinned
OpenSpiel audit is comparison-only evidence, never a training input.

Run **one deterministic candidate path per spot**, not three false seed
replicates. An explicit `PCG64(0)` object satisfies the existing
`ControlledTrainer` interface; complete passes must consume zero random draws,
with the generator state checked unchanged. Set traversal `full`,
`average_phase=opponent_pass`, `average_mass=chance_own_reach`, and
`Rules("signed", "linear", "linear")`. This is the existing batch-four
estimator's full expected pass under the same averaging convention, not the
historical CFR+ clipped update. Use the same simultaneous exact uniform
initialization; charge its **two complete tree traversals**. Every subsequent
iteration makes target 0 then target 1 full passes, freezing the policy for
each pass and charging **all tree nodes**, including chance, terminal and
zero-reach nodes. Capture at the first complete target-pair crossing of
**100k, 1m and 10m** charged visits, retaining actual work and overshoot.
No saved policy supplies a warm start.

The primary policy is the **linear average**; also save current policy. The
primary metric is exact restricted-game NashConv/2 divided by initial pot,
lower better. At every checkpoint report the one deterministic candidate score,
all three immutable B4 seed scores, all three candidate-minus-B4 contrasts,
and their median. The contrasts share the **same candidate policy**, so they
are dependent and provide no three-seed uncertainty estimate for the
candidate. Report coverage, initial-only and post-initial river coverage,
recall violations, information rows, actual table bytes, peak resident memory,
runtime and hardware. Previously used cases support only known-game claims.

## Scientific decision and poker diagnostics

Apply the unchanged absolute limits to each candidate spot: final
exploitability at most **0.01** initial pots (the single deterministic result
is both its median and worst, which also must be at most **0.025**), whole
positive-average uniform-reach coverage at least **0.95**, and **zero** recall
violations. **Positive** requires both spots to pass those absolute gates,
medium/dry candidate minus B4 **control median at most −0.001** initial pots,
and low/wet candidate minus control median at most **+0.001**. **Negative**
means any absolute gate fails, medium/dry candidate minus control median at
least **+0.001**, or low/wet candidate minus control median above **+0.001**.
Other complete results are **inconclusive**. These are descriptive known-game
criteria, not population inference or a default-promotion gate.

Prespecified medium/dry exact turn rows **2443, 1596, 14** and river rows
**1806, 640** come from the diagnosis before this candidate. For each arm,
checkpoint and available control seed, show aggregate turn/river additive
best-reply gains, and each fixed row's acting seat, hole, board, pot, legal
actions, saved probabilities, counterfactual and saved-prefix reach,
conditional alternative-action values and additive contribution. Values use
the **fixed saved opponent policy** and the acting seat's **optimal reply
continuation**. Local action values are not additive exploitability, causal
estimates of retraining, or universal poker advice. No selected row may
change the registered classification.

## Qualification, compute and publication gates

Keep all new adapters, runners, captures, guards and reports under a new
`scripts/` module so historical source pins and receipts remain unchanged.
Before full-game trajectories, independently enumerate rational tiny-game
expected passes for both targets; check the existing full pass equals the
conditional mean of raw external updates, including chance weights, opponent
reach, row aggregation and zero-reach histories. Check target ordering,
simultaneous warm start, signed linear update, opponent-pass average,
full-node work counts, exact first crossings, frozen policy snapshots, RNG
nonconsumption, replay and source binding. Tests must catch action-menu and
ownership errors. Complete exact-source base and optional Python 3.11/3.12
checks, all-file hooks and both hosted jobs before real candidate trajectories.

Publish and GitHub-byte-verify one fictional own proof under **180 seconds**.
Then profile the two candidate spot paths at first **1m** work crossing
**three times each**, six complete paths under **900 seconds**, one worker
serially, including context construction, capture, own scoring and replay.
Retain every repeat, timing, memory and any failure; do not choose a favorable
repeat. For each complete repeat compute
`whole path seconds × 10m / actual final charged work`; take the **maximum**
of the three estimates for each spot. Let `T` be the **sum** of the two maxima
for the serial 10m study. Publish every profile
byte before a separate data-only admission recomputes the strict bound
**`2 × (2 × T + 600) < 7200` seconds**. A failure or equality rejects the
10m run; do not change the formula, profile label or cohort to admit it.
Earlier B4/B8 times are planning context only, not this candidate's forecast.

At most one admitted two-path own run has a **7,200-second** outer cap and
**120-second** failure-save reserve. Publish and GitHub-byte-verify complete
or partial own policies, scores, counters, RNG state and logs **before** any
reference comparison. Then audit every candidate saved value, best-reply and
exploitability scalar with pinned OpenSpiel **2.0.2**, installed
**Apache-2.0** license hash
`cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`,
under **900 seconds** and **1e-9 chips** maximum error. Use OpenSpiel only to
check saved outputs; no reference strategy or value enters training. Rebuild
the fixed report from published own/control/audit bytes, complete final
exact-source local, optional, hook and hosted checks, conduct a solo review,
and history-merge if eligible.

Stop and retain failures or unfavorable results. Do not add candidate paths,
new seeds, new spots, retries to seek acceptance, larger budgets, weaker
thresholds, an altered representation or a default promotion. A future
question needs a separate prospective protocol supported by this outcome.
Codex assisted with this prospective plan; human hands-on time was not
reported. **No new full-expectation measurement exists at publication.**
