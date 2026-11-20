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

## Complete compute profile

The one fixed 36-path profile completed all three 100k-work repeats for each
of the 12 paths, including capture, own scoring and replay, in 36.669 seconds
including startup (<900). All 108 fixed profile readouts were retained in the
[raw archive](../results/river-generalization/profile/manifest.json). The
predeclared maximum-of-three extrapolation gives worker sums 1209.651,
1211.170 and 1221.884 seconds; `T=1221.884` and
`2*(2*T+600)=6087.536<7200` seconds. This is a prospective compute budget
filter, not a strength comparison. Next: publish and verify every profile
member, then independently recompute and publish the separate admission.

## Separate compute admission

After all 294 raw profile blobs were published and GitHub-byte-verified, the
data-only admission reader recomputed the same complete-profile forecast:
`T=1221.8841232260268` and strict bound
`6087.536492904107<7200` seconds. The
[admission receipt](../results/river-generalization/admission/manifest.json)
binds this decision to the published source and profile. Next: publish and
verify this separate receipt before one fixed 12-path 10m own study.

## Fixed own learning checkpoint

The single admitted 12-path study completed all 108 fixed readouts in
287.150 seconds including startup (<7200). Each path reached 10m node work;
final actual work ranged from 10,000,010 to 10,000,164, with zero saved
structural-recall violations. The [own raw archive](../results/river-generalization/own/manifest.json)
retains every policy snapshot, mass history, event, own score and whole-path
time. Own scores have not entered a final comparison; no reference was
constructed. Next: publish and GitHub-byte-verify all own raw blobs before
the comparison-only pinned native scalar audit.

## Independent scalar checkpoint

After all 221 own raw blobs were GitHub-byte-verified, pinned OpenSpiel 2.0.2
compared all 108 saved own scalars. The maximum absolute discrepancy was
`5.684341886080802e-14` chips, below the fixed `1e-9` tolerance; whole audit
time was 55.588 seconds including startup (<900). Installed Apache-2.0 license
bytes matched the pinned hash. The [native archive](../results/river-generalization/native/manifest.json)
retains all rows and fsynced events. No reference policy or action entered
training. Next: publish and verify this independent audit, then reproduce the
all-readout report from published own and native evidence.

## Fixed two-input result: negative

The [data-only report](../results/river-generalization/report/report.json) reproduced
all 108 readouts from published own and native evidence. At the declared
final 10m linear-average endpoint, the candidate-minus-control exact
restricted-game exploitability differences, as fractions of initial pot,
were:

| New card/range input | Seed 20261371 | Seed 20261372 | Seed 20261373 | Paired median |
| --- | ---: | ---: | ---: | ---: |
| Low/wet/IP | -0.005613362 | -0.005148597 | -0.003895194 | -0.005148597 |
| Medium/dry/OOP | -0.094993262 | -0.074216391 | -0.092425654 | -0.092425654 |

The pooled six-pair median was `-0.039914876`. All six paired seed contrasts
favored the candidate descriptively. **The preregistered classification is
negative** because the candidate failed the unchanged absolute quality gates
on the new medium/dry input: median exploitability was `0.035655787`
(3.566%) against ≤1%, and the worst seed was `0.039541661` (3.954%)
against ≤2.5%. The medium/dry control also failed, with median/worst
`0.127558135`/`0.130649050` (12.756%/13.065%). On low/wet/IP, candidate
median/worst were `0.000945518`/`0.001146135` and control
`0.006057871`/`0.006558881`, all within the absolute gates. Every final
linear-average row had 100% positive-average uniform-reach coverage; saved
structural-recall violations were zero. All 108 independent scalar checks
agreed within 1e-9 chips (maximum `5.684e-14`).

The report retains exact exploitability in chips, all within-partition and
extra-information gains, exact-prefix river-only gain, post-initial river
coverage and initial-only rows, each overshoot and path time. At final work,
low/wet/IP persistent four-table cost was 368,896 bytes for control and
523,776 for candidate; medium/dry/OOP was 3,252,480 versus 4,697,088
bytes. Own whole-path times ranged about 65.976–67.266 seconds on low/wet/IP
and 75.516–77.173 seconds on medium/dry/OOP. This fixed panel has two new
card/range inputs on known betting templates, only three dependent training
seeds, and no zero-shot or population inference. The favorable paired
contrasts do not override failed absolute gates; no default is promoted and
no case, budget, threshold or arm is changed.

For a reproducible decision illustration, the first exact river information
row in tree order was chosen for each spot, before inspecting its policy
probabilities. Seed 20261371 at 10m linear average checks with `Qc Qd` on
`9s 7d Jd 5d 2c` about 99.999945% (control) and 99.999991% (candidate).
With `2c 8d` on `2s 6h Jc 3c 2d`, the saved control checks 82.693%, raises
to 36 17.303% and raises to 182 0.0036%; the candidate checks 71.774%,
raises to 36 5.105% and raises to 182 23.120%. These examples illustrate
actual saved actions, not a favorable selection or evidence of stronger
play. Inspect them from a normal clone after `make setup` with:

```sh
PYTHONPATH=src:scripts uv run --locked python - <<'PY'
import json
from pathlib import Path
from poker_ai.cards import format_card
from poker_ai.postflop.controlled_checkpoints import read_snapshot
from poker_ai.training.no_limit import NoLimitState
from river_generalization.gate import ARMS, GAMES
from river_generalization.learning import context
root = Path.cwd()
for game_offset, game in enumerate(GAMES):
    contexts = {arm: context(root, game, arm) for arm in ARMS}
    source = contexts[ARMS[0]].exact.source
    info, node = next((i, n) for i, n in enumerate(source.representatives)
                      if source.states[n].dealer is not None
                      and len(source.states[n].dealer.board) == 5)
    state = source.states[node]
    assert state.dealer is not None
    obs = state.dealer.observe(state.actor)
    print(game, info, obs.seat,
          ' '.join(map(format_card, obs.hole_cards)),
          ' '.join(map(format_card, obs.board)))
    for arm_offset, arm in enumerate(ARMS):
        scoring = contexts[arm]
        folder = root / 'results/river-generalization/own/study' / f'path{6*game_offset+arm_offset:02d}'
        summary = json.loads((folder / 'summary.json').read_bytes())
        row = next(r for r in summary['captures']
                   if r['metadata']['work_label'] == 10_000_000
                   and r['metadata']['readout'] == 'linear_average')
        policy = read_snapshot(folder / row['file'], scoring.partition,
                               row['receipt'], row['metadata'])
        abstract = int(scoring.exact_to_partition[info])
        menu = scoring.partition.actions[abstract]
        actions = [str(NoLimitState(state.dealer, source.spot.rules).decode(a))
                   for a in menu]
        print(arm, abstract, list(zip(actions, policy[abstract, :len(menu)].tolist())))
PY
```

Next: publish and verify this negative report, then complete the required
final exact-source local, optional and hosted reproducibility checks. A failed
scientific quality gate ends this investigation; no next experiment follows.

## Final reproducibility gate and stop

The [final check archive](../results/river-generalization/final-checks/manifest.json)
binds report SHA-256
`e1a5793d1fa9e1ce666c4fba71f0bbd986d13dfd03faaece7de5d84814f245b0`
to exact report commit `d7b317953b6d340550c7bd9e1b77c128b557eb88` and the
unchanged 384-file source fingerprint. **Final local base checks failed.**
Python 3.11 had 1 failed, 5,716 passed, 73 skipped and 150 deselected;
Python 3.12 had 2 failed, 5,715 passed, 73 skipped and 150 deselected. The
first direct failures were the two parameterizations of an existing spawned
fixture test exceeding its unchanged 20-second `Deadline` during the
concurrent local full-suite runs (only the `False` case failed on 3.11; both
failed on 3.12). Ruff, formatting and strict mypy passed before pytest in
both base roles. The final optional 3.11 and 3.12 scopes passed 2,589 and
2,587 tests (two expected 3.12 skips), with clean pre/post source guards;
local hooks passed. [Hosted CI run 44657786167](https://github.com/jimmy-sim/poker-ai/actions/runs/44657786167)
passed both Python jobs and hooks. The earlier required premeasurement local
and hosted qualification on the same source fingerprint passed in full.
Retain the failed final local logs as failures; neither hosted success nor
the earlier qualification relabels them. No retry, deadline adjustment,
scientific rerun or new investigation was started. The fixed measured result
is negative, and final local reproducibility is incomplete.

Three review questions close this bounded research milestone:

1. **Why is the classification negative when all six paired seeds favored the
   candidate?** The prospective rule also required candidate median ≤1% and
   worst ≤2.5% exploitability on each spot. Medium/dry was 3.566% and
   3.954%, so those gates fail.
2. **What does the independent native audit establish?** It reproduces the
   108 saved own scalars within 1e-9 chips after own policies were published.
   It does not make the failed absolute quality gates pass or prove global
   poker strength.
3. **What is learned from the final local failure?** An existing spawned
   fixture exceeded its fixed 20-second wall cap in concurrent local suites.
   The failure is retained; the separately successful hosted and
   premeasurement checks do not turn that local final run into a pass.

Stop at this negative, fully retained milestone. Do not promote a new default
or start another experiment.

## Later software requalification — November 20, 2026

The preceding failed final local receipt remains **failed** and unchanged.
The [separate serial requalification archive](../results/river-generalization/requalification/manifest.json)
binds its SHA-256 and the same frozen 384-file source fingerprint. On exact
head `3e77a50195372fca00868dcdbeb773c7afc75d14`, the two parameterizations
of the previously failing spawned fixture passed in isolation on each Python
minor with the original 20-second deadline. Both full base roles then passed
serially: 5,720 passed, 73 skipped, 150 deselected each, with Ruff,
formatting, strict mypy, and clean pre/post source/runtime/lock guards.
The fixed optional 3.11 role passed 2,589 tests; optional 3.12 passed
2,587 with two expected skips. Both optional license guards and all-file
hooks passed. [Hosted CI 44694112687](https://github.com/jimmy-sim/poker-ai/actions/runs/44694112687)
passed both Python jobs and hooks on a PR merge checkout whose tree matched
the source head. The retained local logs support contention as the cause
of the earlier fixture timeouts, but do not erase those failures or prove
that scheduling was the only possible cause.

This resolves the software qualification on the new exact head, subject to
the final evidence-commit hosted check and review before PR merge. It does
**not** alter the preregistered negative poker-strength result: medium/dry
candidate median/worst 3.566%/3.954% still fail 1%/2.5%. No policy was
retrained, no threshold or timeout changed, and no default was promoted.
