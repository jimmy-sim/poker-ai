# Bounded additional-spot river representation comparison

The [prospective issue #4 contract](https://github.com/jimmy-sim/poker-ai/issues/4#issuecomment-7027108691)
and [fixed config](../configs/river-generalization-fixed-spots.json) were
published before generating new card/range inputs or collecting outcomes.
PR #97 established a positive descriptive result on two known games, with one
unfavorable seed and a failed control gate. This comparison asks whether the
same candidate improves independently retrained local policies on two
additional inputs. It does not test zero-shot play or a global agent.

## Definition of done and prior use

The earlier `dev_*`, `heldout_*`, four `fresh_*` validation cases and solver
spots have already been inspected or used. They are known evidence, not unseen
cases. This study reuses two known **public betting templates** but draws new
four-card turn boards and weighted physical-card ranges without inspecting
strategy outcomes. Call them newly selected card/range inputs, not unseen
templates or an unbiased sample of all Hold'em.

Before selection, the config fixes one low/wet/in-position case using the
`heldout_low_oop` public pot, stack and action template (with one deterministic
legal check to put the button next), and one medium/dry/out-of-position case
using the `dev_medium_oop` public template. One PCG64 stream seeded 20261370
draws ordered boards without replacement. Wet requires three distinct flop
ranks within span four and exactly two flop suits; dry requires pairwise flop
rank gaps of at least three and three distinct flop suits. All four board
ranks must differ. Reject any rank signature `(sorted flop ranks, turn rank)`
already present in tracked `configs/learning-spots`, `configs/fresh-spots`,
or `configs/spots`, or selected for the other case. Stop after 10,000 failed
structural attempts; never choose on tree size, policy, score or reference
value. For each accepted board draw eight distinct remaining cards for two
combos per seat and four independent integer weights 1..3. A failed legal or
node-budget check retains the cohort and stops; no replacement case.

Commit the exact cases, structural attempt counts and source/input hashes in
the cohort freeze before any profile or training. The already used templates
and previous outcome cases remain identified in that freeze.

## Fixed matched-work protocol

Use unchanged q8 control `texture_range_q8_b8` and unchanged PR #97 candidate
`q8_turn_exact_river`. The candidate retains the q8 key through the turn and
uses only the acting player's own two cards, observed board, seat and public
history on the river. No opponent private card, future card, saved policy or
reference solver enters the key or trainer. Both arms independently train
with IID B4 external sampling, signed regrets, linear regret/average weights,
one exact uniform initialization charged in node work, and target order 0 then
1. The fixed seeds are 20261371–73. Two spots × three seeds × two arms give
12 paths. Save first complete 100k/1m/10m node-work crossings and current,
uniform-average and linear-average readouts: 108 logical profiles. Three
spawned workers take fixed path indices modulo three. Do not extend or rerun
an unfavorable path.

Exploitability is exact restricted-game NashConv/2, in chips and fraction of
initial pot (lower is better). The primary descriptive contrast is the final
10m linear-average candidate-minus-control difference for each paired seed,
the median per spot and the pooled six-pair median. Report all other readouts,
within-partition and extra-information gains, exact-prefix river-only gain,
positive-average uniform-reach coverage, post-initial river coverage,
initial-only rows, information rows, four-float64-table bytes, actual node
work/overshoot and whole-path wall time. Pairing seed labels does not make
sampled hands identical after strategies diverge.

The predeclared **positive** two-spot result requires medium/dry paired
median ≤−0.001 initial pots, low/wet paired median ≤+0.001, pooled six-pair
median <0, and candidate final median exploitability ≤1%, worst ≤2.5%,
uniform-reach average coverage ≥95% and zero recall violations in both
spots. Apply and report the same absolute gates separately to the control.
The result is **negative** if the medium/dry paired median ≥+0.001 or the
candidate fails an absolute quality gate. Every other complete result is
**inconclusive**. These are bounded descriptive decisions, not confidence
intervals or global admission; no outcome promotes a default.

## Compute, publication and stopping gates

All new code stays in an isolated adapter package, preserving historical
`src` and PR #97 source pins. Complete focused correctness tests, exact-source
base Python 3.11/3.12, fixed optional suites, hooks and both hosted jobs
before real trajectories. Publish and GitHub-byte-verify a small synthetic
own proof under 180 seconds. Then profile all 12 paths at 100k work three
times, 36 complete paths under 900 seconds. For each path, take the **maximum**
of its three complete construction-through-replay times scaled by
`10m/actual_final_work`. Sum those maxima in the fixed worker partitions and
let `T` be the largest sum. The separate admission must require
`2*(2*T+600)<7200` seconds, strictly; publish profile and admission before
one whole-own study capped at 7,200 seconds. The cheaper profile is the
budget filter for this potentially hours-long workflow.

Publish and GitHub-byte-verify complete or failed own raw policies and scores
before any comparison-only pinned OpenSpiel 2.0.2 audit. Its installed
Apache-2.0 license is checked, every one of 108 own value/reply/exploitability
scalars must match within 1e-9 chips, and its whole audit cap is 900 seconds.
Reference actions, policies and values never enter own training. Reproduce
the report from published data, complete final local/optional/hosted checks,
record failures and partial paths, update the work log and learning journal,
and stop at the declared classification. A failed source, compute, numerical
or scientific gate stops this investigation; no favorable retry, case swap,
threshold change, larger budget or next experiment.

At this prospective publication there are no selected new cases, trained
policies, profile times or outcome metrics. Codex assisted; human hands-on
time was not recorded.

## Exact-source qualification

Isolated study source `d78b5253d687e8e929e47ee20b6c416200e54b47`
(fingerprint `152b357b6942d065e402c84abc14ca3631b29d54551ead71bb668729ccbc81d3`)
passed clean pre/post guards and all required local roles. Base 3.11 and 3.12
each passed 5,717 fast tests (73 skipped, 150 deselected) plus lint,
formatting and strict typing. Optional 3.11 passed 2,589 tests; optional 3.12
passed 2,587 with two expected skips. Both optional roles checked the pinned
OpenSpiel 2.0.2 license. Hooks passed. [Hosted CI run 44652668301](https://github.com/jimmy-sim/poker-ai/actions/runs/44652668301)
passed both Python jobs, including hooks. The
[qualification archive](../results/river-generalization/source-checks/manifest.json)
retains local logs, guards and official hosted metadata/logs. No real policy,
profile or outcome has been collected. Next: publish and byte verify this
receipt, then run the capped synthetic own proof.

## Synthetic own proof

The one fictional signal-game proof completed and replayed all nine fixed
capture/readout combinations at work labels 80, 240 and 720. It reached 720
node work in 0.270 seconds including runner startup, below the 180-second
stage cap. The [own proof archive](../results/river-generalization/own-proof/manifest.json)
retains policy, mass, events and replay evidence bound to the qualified source.
It is a software check, not a new-spot strength measurement. Next: publish
and GitHub-byte-verify all proof members before the real 100k profile.
