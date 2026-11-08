# Diagnose the saved range-mass strategies

Issue [#4](https://github.com/jimmy-sim/poker-ai/issues/4), November 7, 2026.
Codex-assisted implementation/reporting; personal hands-on time not recorded.

## Question and stopping point

The [sampled comparison](range-mass-sampled.md) fails the deeper-game limits.
Before choosing a remedy, measure how much a best reply can gain using the
existing representation, and how much additional gain exact information allows.
Use the unchanged saved policies: all five representations, both known games,
all three final sampled seeds at 10m work, plus all final full controls at 4096
iterations. The pinned [config](../configs/range-mass-reply-diagnosis.json) binds
all raw input reports, own policy/checkpoint bundles and independent audits.
There are 40 profiles, 80 responding seats and 160 exact/restricted reply roots.

For each responding seat i, freeze the saved opponent. Let V_i be the saved value,
B_i the exact best-reply value and R_i the best-reply value within the saved
information partition. Record B_i - V_i = (R_i - V_i) + (B_i - R_i).
Half-sum over seats to reproduce exact exploitability (NashConv/2).
Require equal-depth perfect recall before response dynamic programming; maximize
after summing hidden histories, never separately inside each hidden world.
Use the first legal exact maximizer, with no approximate tie substitution.

Keep per-seat, per-street and per-information-row saved-prefix/reply-suffix losses.
Their sum must equal each unilateral gain. Retain all zero-loss rows too. Display
up to eight positive groups and four supported examples per group, in deterministic
loss/index order. These are own counterstrategy examples, not deployed-agent play
or universal poker advice. A turn loss can include later river opportunities;
street attribution is not causal feature localization.

Report all seeds separately. When summarizing additive components, use arithmetic
means so the components still add to the mean total. A median total is a separate
statistic; median components generally do not add. Full-tree versus sampled
results use different update/work conditions and are not a causal variance ablation.

Publish tested code before computing new responses. Cap the own stage at 1800
seconds including input replay. Retain all 40 cases, source/config/input/context
hashes and own exact/restricted reply profiles. Replay every nested summary/detail
and accounting identity. Independently check all 160 roots and the 160 achieved
own reply-profile values with OpenSpiel 2.0.2 (Apache-2.0), comparison-only, within
1e-9 chips. The [license/shared-mechanics limitations](solver_validation.md) remain.
No native actions enter the own learner or reply computation.

Definition of done: checked own diagnosis, complete native audit, reproducible
tables/two figures, a terminal inspector, local/hosted software checks and journal
step 23. Stop there. No training, new representation, budget rescue, remedy
selection, fresh/global admission or default change. A large within-partition
value shows available deviations against this frozen opponent, not guaranteed
self-play improvement. Extra-information value is specific to that opponent and
policy, not a universal irreducible abstraction floor.

## Status

Prospective config and methodology, before implementation and new diagnosis results.
