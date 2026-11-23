# Full expected river updates on two new inputs: prospective protocol

**Issue #4; November 23, 2026 (PST).** This protocol and its
[machine contract](../configs/river-full-broader-spots.json) precede case
selection, candidate measurements and training. PR #104 improved two repeatedly
inspected games at 10m charged node work; it was worse at earlier checkpoints.
The [PR #102 four-spot readout study](river-uniform-readout-result.md) stopped
at an 8,885-second conservative forecast, so this is a smaller, distinct test
of whether the **unchanged full expected updater** transfers to new card/range
inputs under the existing 7,200-second cap. Neither public betting template is
unseen; newly selected inputs are not a population sample or a default-agent
promotion gate.

## Definition of done and fixed question

Does the `q8_turn_exact_river` full expected, signed-regret, linear-weight
learner from PR #104 improve final **linear-average** restricted-game poker
decisions over independent batch-four signed external-sampling controls at the
same charged node work on one medium/dry OOP and one low/wet IP input? Done
means one frozen cohort, isolated source, independent tiny-game correctness
tests, exact-source local/optional/hooks/hosted qualification, one fictional
proof, one fixed profile and separate conservative admission, at most one
admitted own study, own-before-reference publication, pinned scalar audit,
fixed report and final requalification. A failed gate ends this experiment with
its evidence retained.

## One-time selection and training

Use a single PCG64 stream seeded **20261510**, in this order: medium/dry/OOP
using the known `dev_medium_oop` public template, then low/wet/IP using the
known `heldout_low_oop` public template. For each, draw ordered four-card turn
boards without replacement. Require four distinct ranks. Dry requires three
flop suits and pairwise flop-rank gaps at least three. Wet requires exactly two
flop suits and flop-rank span at most four. Exclude every `(sorted flop ranks,
turn rank)` signature in all 19 tracked earlier spot inputs across the five
declared directories, regardless of suits, and any signature already selected
here. At most 10,000 attempts per stratum; exhaustion stops selection. After
each accepted board draw eight distinct remaining physical cards for two
private combos per seat, then four integer range weights from 1 through 3.
Retain the template pot, stacks, actions and betting prefix; add one legal
check only if needed to put the declared seat next. Freeze attempt counts,
exact bytes, source, input hashes and legal spot files before building a tree,
policy or score. A selected invalid spot or tree over 200,000 nodes is retained
as a failure; never replace it. Selection cannot use exploitability, strategy,
reference output or tree size.

For each frozen spot use three independent B4 control RNG seeds **20261511,
20261512, 20261513**, and exactly one deterministic full expected candidate
with `PCG64(0)` whose state must remain unchanged. Both arms use the unchanged
`q8_turn_exact_river` representation, same action menu, signed regret, linear
regret weight, linear average and simultaneous exact uniform initialization.
B4 uses IID batch four external sampling, target order zero then one. Full
expected passes enumerate every node for target zero then one under frozen
opponent policies and charge all visits, including zero-reach nodes. Count
initialization work in both arms. Capture current and linear-average policies
at the first complete iteration crossing **100,000, 1,000,000 and 10,000,000**
charged tree-node visits; retain actual work and overshoot. Never warm-start,
change seeds or choose favorable checkpoints. Fixed path order is stratum
order, then B4 seeds in order, then the one candidate per stratum; three
spawned workers receive path index modulo three.

## Metrics and decision

Primary lower-is-better metric: exact restricted-game NashConv/2 in chips and
as a fraction of the initial pot, for the final linear average. At every
checkpoint report the deterministic candidate, each B4 seed, all three
candidate-minus-B4 contrasts and their median. Those contrasts share one
candidate and are dependent; they do not estimate candidate seed uncertainty.
Report whole and post-initial-river positive-average uniform-reach coverage,
recall violations, information rows, table bytes, actual work, wall time,
hardware and peak RSS. Rank the control median seed's top three additive
best-response gain nodes on each street using only control saved policies,
breaking ties by information index, then display those same nodes for every
arm at every checkpoint. Show cards, board, legal actions, saved action
probabilities, counterfactual and saved-prefix reach, conditional alternative
values, and street contributions. Values assume the saved opponent policy and
an optimal reply continuation; local values are not universal poker advice.

Apply the historical absolute gates **separately to each final candidate
spot**: exploitability at most 0.01 initial pots (the one candidate result is
both median and worst, also at most 0.025), whole positive-average coverage
at least 0.95, zero recall violations. Report the same gates separately for
every control seed. **Positive** requires both candidate spots to pass, the
medium/dry candidate-minus-control median at most −0.001 initial pots and
the low/wet median at most +0.001. **Negative** means any candidate absolute
gate fails, medium/dry median at least +0.001, or low/wet median above +0.001.
Other complete outcomes are **inconclusive**. A failed source, compute,
publication or numerical gate stops without a strength classification.
These are two selected finite games, with no claim for unseen templates,
full-game strength, statistical confidence or a default promotion.

## Qualification, compute and publication

Isolate selection, adapters, runner, guards and report in new modules; do not
modify historical source dependencies, protocols, receipts or lock. Test both
targets' expected-pass arithmetic against independent tiny-game enumeration,
plus B4/control identity, work crossings, RNG nonconsumption, snapshots,
source binding, replay, ownership and action menus. Complete exact-source base
and optional Python 3.11/3.12 suites, all-file hooks and both hosted jobs
before any real trajectory. Publish and GitHub-byte-verify a fictional own
proof under **180 seconds**.

Planning context only: PR #104's two full paths took 19.435 seconds total at
10m, while PR #102's 12 B4-path forecast failed at 8,885.117 seconds. This
smaller eight-path grid may fit; the measured profile alone decides. Profile
all eight paths **three times each** under **900 seconds**: B4 at first 100k
work crossing and full expected at first 1m crossing, each timing context,
capture, own scoring and replay. For each path take the maximum of its three
complete `whole_path_seconds × 10m / actual_final_node_work` estimates. Sum
these maxima in the fixed three-worker assignment and let `T` be the largest
worker sum. Publish every profile byte before a separate data-only admission
requiring strictly **`2 × (2 × T + 600) < 7200` seconds**. Failure or equality
rejects the 10m run. No repeat, alternate worker partition, altered formula or
larger cap may seek admission.

At most one admitted eight-path own run has a **7,200-second** outer cap and
**120-second** failure-save reserve. Publish and GitHub-byte-verify all
complete or partial own policies, scores and logs **before** the OpenSpiel
comparison. Audit all 48 saved policy value, best-reply and exploitability
scalars against pinned OpenSpiel **2.0.2**, installed Apache-2.0 license hash
`cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`,
within **1e-9 chips** under **900 seconds**. Reference strategies and values
never enter training. Build the fixed report from published bytes; complete
final exact-source local, optional, hooks and hosted checks, review and
history-preserving merge if eligible. Keep all failures and partials. No
scientific retry, budget extension, source-pin rewrite or default promotion.

At prospective publication no cohort was drawn and no new measurement exists.
Codex assisted; human hands-on time was not reported.
