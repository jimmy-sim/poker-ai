# Full expected river updates at matched work: fixed result

**Issue #4, November 23, 2026 (PST). Classification: positive under the
predeclared two-known-spot criteria.** This is not evidence of stronger
general Hold'em play or a default-promotion decision. The [prospective
protocol](medium-dry-full-expectation.md) and [machine contract](../configs/medium-dry-full-expectation.json)
were published at `8770e3243356aad82d6cc07fac70320f04cdfc34` before any
new candidate measurement. The isolated tested source was
`fdcc438029752ec8e5183bce9146b73fa3894d05`.

## Definition of done and fixed comparison

The question was whether replacing B4 IID external-sampling passes with
complete expected passes improves the unchanged `q8_turn_exact_river`
representation under the **same signed regret update, linear regret weight,
linear average and 10m charged node work**. The candidate has one
deterministic path per already inspected spot; immutable B4 has seeds
20261371, 20261372 and 20261373. A complete target pass evaluates every
branch under the current opponent policy, rather than one sampled
trajectory. It costs more nodes per update. Both spots are **known**, never
unseen or held out for this question.

The [source receipt](../results/medium-dry-full-expectation/source-checks/manifest.json)
binds tested source `fdcc438029752ec8e5183bce9146b73fa3894d05`,
fingerprint `a549976f0811872dcc9057e112f40def8af5d2f3e16b81d1a678fdcf8bc62aab`,
both local base/optional Python 3.11/3.12 suites, hooks and passing
[tested-source CI](https://github.com/jimmy-sim/poker-ai/actions/runs/45166698139).
The [fictional proof](../results/medium-dry-full-expectation/own-proof/manifest.json)
passed in 0.366 seconds (<180), then all six fixed
[profile paths](../results/medium-dry-full-expectation/profile/manifest.json)
completed in 13.863 seconds (<900). The slowest scaled low/wet and
medium/dry repeats were 10.979192 and 34.345882 seconds; the separately
published [admission](../results/medium-dry-full-expectation/admission/manifest.json)
recomputed `T=45.325074` and strict `2*(2*T+600)=1381.300294<7200`.
All source/proof/profile/admission archive files matched their GitHub
commits before the next stage.

The one [own run](../results/medium-dry-full-expectation/own/manifest.json)
completed both 10m paths in 19.435177 outer seconds (<7200; 120-second
failure-save reserve unused) and was published and byte-verified **before**
the pinned OpenSpiel 2.0.2 Apache-2.0
[comparison-only audit](../results/medium-dry-full-expectation/native/manifest.json).
All 12 saved candidate policies' value, best-reply and exploitability
scalars agreed within `5.684342e-14` chips, below `1e-9`. No reference
strategy entered training. The one fixed [raw report](../results/medium-dry-full-expectation/report/manifest.json)
replays those archives and all immutable B4 own/native evidence into 48
spot/arm/work/readout cases; an independent data-only grid and arithmetic
check is retained alongside it. Exact report-head final local and hosted
qualification remains a separate merge gate.

## Primary 10m result

Exploitability here is exact restricted-game NashConv/2 divided by the
initial pot; **lower is better**. The fixed primary readout is the linear
average. The candidate's single deterministic value is both its median and
worst for the absolute 0.01/0.025 initial-pot gates. Each row below uses
the same charged-work label, with actual first-crossing overshoot retained.

| Known spot | B4 seed 20261371 | B4 seed 20261372 | B4 seed 20261373 | Full candidate | Candidate minus B4 seeds, in order |
| --- | ---: | ---: | ---: | ---: | --- |
| Low/wet IP | 0.000945518 | 0.000909274 | 0.001146135 | **0.000059952** | −0.000885566, −0.000849322, −0.001086183 |
| Medium/dry OOP | 0.035655787 | 0.039541661 | 0.035132481 | **0.006700181** | −0.028955606, −0.032841480, −0.028432300 |

Both candidate absolute gates pass: whole positive-average coverage is
1.0 and structural recall violations are zero on both spots. The medium/dry
median candidate-minus-control contrast is **−0.028955606** initial pots,
below the required −0.001; low/wet is **−0.000885566**, below the permitted
+0.001. Thus the frozen rule classifies the complete result **positive**.
The three contrasts share one deterministic candidate policy; they are
dependent descriptions of three historical control seeds, not three
candidate replicates or a confidence interval.

At the earlier medium/dry work labels, the candidate was **worse** than
the B4 control median: 1.216833 versus 0.938752 at 100k, and 0.212676
versus 0.138278 at 1m initial pots. It became better by the fixed 10m
endpoint. The other `current` readout and all earlier seed-level values are
in the raw report; they did not choose the endpoint or classification.

## Coverage, cost and remaining decisions

At 10m, medium/dry post-initial positive-average river coverage is
0.980975 for the candidate versus 0.955475/0.934115/0.947548 for the
three B4 controls; whole coverage is 1.0 for all. The candidate has 244
initial-only river rows versus 484/590/494 for B4.
The candidate's trainable table is 2,348,544 bytes on medium/dry and
261,888 bytes on low/wet; B4 control tables are 4,697,088 and 523,776
bytes. Candidate whole-path times were 11.619 and 7.350 seconds, with
maximum recorded cumulative worker RSS of 181,649,408 and 58,359,808
bytes. B4 saved whole-path times span 76.393–76.763 and
66.007–66.263 seconds on medium/dry and low/wet respectively; its
cumulative worker RSS spans 196,837,376–238,043,136 and
62,898,176–65,880,064 bytes. These historical paths ran separately;
runtime/RSS differences are descriptive, not a controlled speed claim.

For medium/dry at 10m, the candidate's additive best-response gains are
0.161258 chips on turn and 0.079949 on river, summing to its 0.241207-chip
exploitability. The B4 seeds have turn gains 0.264670/0.395755/0.312316
and river gains 1.018938/1.027745/0.952454 chips. Remaining candidate
gain is now mostly on the turn in this exact finite game. These gains use
each saved policy's **fixed opponent** and the acting seat's optimal reply
continuation. They cannot isolate the causal effect of changing a single
action, and local values are not universal poker advice.

One preregistered river example is exact row 1806: seat 1 holds `8c 9h`
on `2s 6h Jc 3c 5h`, pot 108 chips, with legal `check`, `raise_to 108`,
`raise_to 146`. B4 seed 20261371 saves probabilities
`[0.348440, 0.043740, 0.607820]`, counterfactual reach 0.007919,
saved-prefix reach 0.003767, conditional alternative values
`[-54.000, -50.784, -67.981]` chips and 0.021797-chip additive gain.
The candidate saves `[0.442735, 0.007477, 0.549787]`, reaches
0.007695/0.003849, has conditional values
`[-54.000, -68.322, -53.994]` and 0.000211-chip additive gain.
The opponent policies and continuation values differ across arms, so this
is a diagnostic of saved policies, not a direct action-swap experiment.
All prespecified turn rows 2443/1596/14 and river rows 1806/640, with
cards, boards, legal actions, probabilities, both reach measures and
alternative values at every checkpoint, are in `report.json`.

From the repository root, inspect the same representative river decision
across checkpoints and the B4 seed 20261371 with:

```sh
python3 - <<'PY'
import json
from pathlib import Path
rows = json.loads(Path('results/medium-dry-full-expectation/report/report.json').read_text())['cases']
for row in rows:
    if row['game'] == 'new_medium_dry_oop' and row['readout'] == 'linear_average' and (row['arm'] == 'signed_full_expectation' or row['seed'] == 20261371):
        spot = row['fixed_river_rows']['1806']
        print(row['arm'], row['seed'], row['work_label'], spot['identity'], spot['saved_probabilities'], spot['seats'])
PY
```

## Limits and next decision

Both spots and their B4 controls were inspected before this protocol. One
deterministic full-pass candidate cannot quantify variation across unseen
boards, ranges, stacks, action menus or training seeds. Restricted-game
exploitability is not full-game win rate. The favorable 10m endpoint does
not erase the worse 100k/1m medium/dry checkpoints. No default was
promoted. The next distinct question should test a structurally selected,
prospectively frozen broader spot cohort under matched work and the same
software/publication gates; previously inspected cases must remain labeled
known. Do not tune this candidate on those evaluation outcomes.

**Interview questions.** (1) *Why is this a matched-work comparison?* Both
arms stop at first complete crossings of the same charged tree-node labels;
the numbers of updates can differ. (2) *Why do three favorable contrasts
not establish a population confidence interval?* All reuse one deterministic
candidate and three fixed, previously known control seeds on two known
games. (3) *What does the independent audit establish?* It checks saved
value, best reply and exploitability scalars against pinned OpenSpiel within
the frozen tolerance; it does not validate generalization or promote an
agent default.

Codex assisted with implementation, execution and this report. Human
hands-on time and personal learning were not reported.
