# Prospective exact-turn representation comparison

**Issue #4; November 23, 2026 (PST).** This protocol and its
[machine contract](../configs/turn-exact-transfer.json) must be published
before selecting new cards/ranges or measuring a new tree, policy or score.
The [PR #106 known-input diagnosis](river-turn-loss-diagnosis-result.md)
found 12 exact turn rows sharing six abstract keys and 92.8173% of the
unchanged full expected candidate's final turn best-response gain on those
rows. Its leading Jh 9h and Qd Qh decisions have opposing local action
values but share saved probabilities. This is a representation hypothesis,
not a strength gain. The parent [PR #105 comparison](river-full-broader-spots-result.md)
remains **negative**. The next question matters because a turn key that
separates genuinely different hands may remove that constraint without
changing the learner or asking it to spend more work.

## Definition of done and fixed question

At the same charged tree-node work, does **exact acting information on the
turn as well as the river** improve the final linear-average policy over
unchanged `q8_turn_exact_river` under the same full expected signed learner?
The new code must be an isolated adapter; historical source pins and the
published PR #105/#106 files stay untouched. One diagnosed PR #105
`full_new_medium_dry_oop` input is a **known mechanistic check**. Three
additional inputs are selected once by structure and then frozen before any
tree, policy or score inspection. Their public betting templates have been
used before; the newly drawn card/range combinations will be new to this
study but are **not unseen templates or a population sample**. Do not call
any previously inspected or evaluated input unseen.

Done means a published prospective contract, one frozen cohort, isolated
source and independent tiny-game correctness tests, exact-source local base
and optional Python 3.11/3.12 checks, all-file hooks and both hosted jobs;
one fictional proof; one fixed three-repeat profile and separate strict
conservative admission; at most one admitted own study; own publication
before a pinned comparison-only scalar audit; a fixed report, final exact
source checks and review. A failed source, numerical, compute or publication
gate stops this experiment with evidence retained. A failed scientific
criterion ends this experiment; no changed seed/case/cap or favorable retry.

## One-time cohort and paired paths

Use one PCG64 stream seeded **20261520**. In fixed order, draw:

1. `turn_exact_new_medium_dry_oop` from the known
   `configs/learning-spots/dev_medium_oop.json` template: dry flop,
   out-of-position actor.
2. `turn_exact_new_medium_wet_oop` from the same template: wet flop,
   out-of-position actor.
3. `turn_exact_new_low_wet_ip` from the known
   `configs/learning-spots/heldout_low_oop.json` template: wet flop,
   in-position actor.

For each stratum, draw an ordered four-card turn board without replacement
until all four ranks differ, the texture rule holds and its `(sorted flop
ranks, turn rank)` signature differs from every tracked spot in the six
closed prior directories listed in the machine contract (21 files), and
from earlier selections in this cohort, regardless of suits. Dry means
three flop suits and every pair of flop ranks at least three apart. Wet
means exactly two flop suits and flop-rank span at most four. Limit each
stratum to **10,000 attempts**; exhaustion is a retained failure. For each
accepted board, draw eight distinct remaining physical cards for two
private combos per seat and four independent integer range weights in
**{1,2,3}**. Keep the chosen template's pot, stacks, public action menu
and betting prefix; add exactly one legal check only when needed to make
the declared seat act next. Set actor and hero to that seat. Set maximum
tree nodes **200,000**. Validate only input syntax before freezing exact
spot bytes, attempt counts, signatures, source and SHA-256 hashes. A bad
frozen spot or oversized tree is retained as a failure, never replaced.
Selection must not use tree size, turn collision count, strategy,
exploitability, reference output or runtime. If the newly selected inputs
have **zero** turn collisions in total after source qualification, stop
before training as a structural non-test of the mechanism; report this
inconclusive strength outcome without drawing replacements.

Run four spots in this fixed order: known mechanistic medium/dry, then the
three frozen inputs above. For each run unchanged full expected
`q8_turn_exact_river` control first, then exact-turn/exact-river candidate.
Both use `PCG64(0)` with state unchanged: these are deterministic paths, so
there are **eight** total paths, not eight independent RNG samples. The
same cards, ranges, tree, legal actions, initialization, signed regret,
linear regret weight, linear average and target order zero then one apply
within each pair. Each full expected target pass charges all visited tree
nodes, including zero-reach nodes; charge exact uniform initialization in
both arms. Capture current and linear-average policies at the first
complete target-pair crossing **100,000, 1,000,000 and 10,000,000** charged
visits, recording actual work and overshoot. No warm start, alternate seed,
checkpoint selection or post-outcome tuning. Three spawned workers receive
path index modulo three.

The only representation difference is that acting turn rows use the same
existing `exact_information` observation key already used on the river.
The control retains the original q8 turn key. The new adapter must prove
identical exact game/chance/payoffs/owners/action menus and unchanged river
keys, verify that turn groups only split, and reject recall violations.
No global exact-tree or default-agent promotion is implied.

## Metrics and fixed decision

Primary lower-is-better metric: exact restricted-game NashConv/2 in chips
and as a fraction of the initial pot at final **linear average**. Report
all four paired candidate-minus-control spot differences at all three
work labels, separately for the known mechanistic spot and each new input.
There is one deterministic seed per arm; paired spots are dependent and
not a seed-based confidence interval. Report whole and post-initial-river
positive-average uniform-reach coverage, recall violations, exact and
abstract information rows, table bytes, actual charged work, wall time,
hardware and peak worker RSS. Rank each control final policy's top three
additive best-response gain rows on turn and river, tie-breaking by exact
information index, then display those **same rows** for both arms at all
checkpoints. Show board, private cards, legal actions, saved probabilities,
counterfactual and saved-prefix reach, alternative-action values and additive
contributions. Values assume each saved opponent policy and an optimized
reply continuation; local scores are not universal poker advice or a causal
estimate of retraining benefit. Report turn collision inventory for each
spot without selecting or dropping spots by it.

Apply historical absolute candidate gates **separately on each of the three
new spots**: final exploitability at most **0.01 initial pots** (the one
candidate is both median and worst and must also be at most **0.025**),
whole coverage at least **0.95**, zero recall violations. Report these gates
for all control paths too. **Positive** requires all three candidate new
spots pass their absolute gates, the known mechanistic candidate improve by
at least **0.001 initial pots**, at least one new medium candidate improve
by at least **0.001**, the other new medium not worsen by more than **0.001**,
and low/wet not worsen by more than **0.001**. **Negative** means any new
candidate absolute gate fails, or the known or any new spot worsens by more
than **0.001**. Other complete outcomes are **inconclusive**. A zero-
collision structural stop has no strength classification beyond
inconclusive. No acceptance here promotes a default: prior full-game,
solver and deployment gates remain separate. These are four restricted
finite games, three newly drawn inputs on known templates, not a
full-game strength or statistical-confidence claim.

## Compute, qualification and publication

The previous eight-path mixed B4/full study finished its 10m own run in
140.096 launcher seconds, with a conservative fixed-worker bound of
3,436.576 seconds. Its two full expected paths took 12.933 and 7.980
seconds, but these figures do **not** establish the cost of different
cards/ranges or the exact-turn adapter. Plan a cheaper 8-path full/full
grid, and let the measured profile decide admission. This work is flagged
as potentially taking hours including all qualification; do not buy
compute or exceed any existing cap.

Publish and verify the protocol first; then publish/verify selection source
before the one-time cohort freeze. Publish/verify the freeze before any
tree/collision/policy/score measurement. Test expected-pass arithmetic,
control identity, exact-turn key refinement and recall on independent toy
games, plus work crossings, RNG nonconsumption, snapshot/hash replay and
failure retention. Complete exact-source base/optional Python 3.11/3.12,
hooks and hosted CI before any real trajectory. Publish and GitHub-byte-
verify one fictional own proof under **180 seconds**.

Profile **all eight paths three times** under **900 seconds** total: each
path to first 1m crossing, including context, capture, own scoring and
replay. For each path take the maximum of its three complete
`whole_path_seconds × 10m / actual_final_node_work` estimates. Sum these
maxima in the fixed three-worker assignment and let `T` be the largest
worker sum. Publish all profile bytes before a separate data-only admission
requiring strictly **`2 × (2 × T + 600) < 7200` seconds**. Failure or
equality rejects the longer run. No repeat, alternate assignment, changed
formula or larger cap to gain admission.

At most one admitted eight-path own study has a **7,200-second** outer cap
and **120-second** failure-save reserve. Publish and GitHub-byte-verify
complete or partial own policies, scores and logs before reference work.
Audit the 48 saved current/linear-average policies' value, best-reply and
exploitability scalars against pinned OpenSpiel **2.0.2**, installed
Apache-2.0 license hash
`cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`,
within **1e−9 chips** under **900 seconds**. Open-source reference outputs
are comparison-only; never load their strategies into training. Build the
fixed report from published bytes, complete final exact-source local,
optional, hooks and hosted checks, solo review and history-preserving merge
if eligible. Retain every failure/partial run and preserve historical
source pins, licenses and attribution. Codex assisted; human hands-on time
and personal learning were not reported.
