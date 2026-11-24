# Residual exact-turn diagnosis on the known medium/wet game

**Issue #4; November 24, 2026 (PST).** This is the one read-only replay
specified in the [prospective protocol](known-wet-residual-diagnosis.md).
Its input, `Qs Kd As 3c` at the turn, was already used and outcome-inspected
in [PR #110](known-wet-turn-mechanism-result.md). No new policy was trained,
no new reference strategy was used, and this is not an unseen test or a
strength improvement. The [complete 12-policy report and raw row vectors](../results/known-wet-residual-diagnosis/diagnosis/manifest.json)
are the evidence for every number below.

## Fixed question and answer

The exact-acting-turn/exact-river candidate reduced the known game's
final linear-average restricted-game exploitability relative to the q8-turn
control at equal work, yet still failed PR #110's frozen absolute limits.
Where does its remaining gain for an optimal opponent sit? **On this
one game, the turn weakness is concentrated and the river weakness is
diffuse under the predeclared 50% rule.** The ten largest candidate-average
exact turn rows contribute `0.7661130692120555` of `0.8044784835351706`
chips (**95.2310%**); the ten largest exact river rows contribute
`0.013856407594872448` of `0.26850812174483196` chips (**5.1605%**).
The single largest turn row contributes `0.43046290373104545` chips,
53.5083% of turn gain; the first two contribute 71.3836%. These are
additive contributions to NashConv/2, half the sum of the two seats'
unilateral best-response gains in acting-seat chips. Smaller means less
gain is available to an optimized opponent in this restricted game.

The same 20 exact rows were selected **once** from the final candidate
linear average: ten turn and ten river, descending additive gain with
exact information index breaking ties. The [selection record](../results/known-wet-residual-diagnosis/diagnosis/selection.json)
was written before the control and other saved checkpoints were traced.
No zero-reach or unfavorable row was replaced. Every policy uses its
own fixed saved opponent when computing its best reply. Comparisons of
local action values therefore have different opponent and reach
assumptions across policies; they are not causal action-swap estimates
or universal poker advice.

## All fixed policies and accounting

The labels `100k`, `1m`, `10m` are the first complete charged-work
crossings, not identical to actual node counts. `cur` is the saved
current strategy and `avg` the saved linear average. `T10` and `R10`
are the **same candidate-selected** ten turn/river rows' shares of
each policy's full street gain; they are not independently selected
top-ten rows for the control. `Reach T/R` counts exact rows with
positive full saved-prefix reach. Values are chips except shares.

| Arm | Label | Readout | NashConv/2 | Turn | River | T10 | R10 | Reach T/R |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| q8 | 100k | cur | 55.994 | 55.978 | 0.016 | 90.3% | 0.0% | 16/88 |
| q8 | 100k | avg | 44.316 | 33.500 | 10.816 | 28.1% | 0.4% | 60/8280 |
| q8 | 1m | cur | 23.489 | 10.463 | 13.026 | 60.5% | 1.2% | 35/2059 |
| q8 | 1m | avg | 31.343 | 23.764 | 7.579 | 49.9% | 0.3% | 60/8280 |
| q8 | 10m | cur | 10.477 | 4.168 | 6.309 | 91.6% | 0.6% | 20/1367 |
| q8 | 10m | avg | 2.226 | 1.682 | 0.545 | 95.7% | 3.1% | 60/8280 |
| exact | 100k | cur | 56.139 | 56.123 | 0.016 | 90.2% | 0.0% | 16/88 |
| exact | 100k | avg | 44.316 | 33.500 | 10.816 | 28.1% | 0.4% | 60/8280 |
| exact | 1m | cur | 22.602 | 10.043 | 12.559 | 58.0% | 1.4% | 35/1983 |
| exact | 1m | avg | 31.246 | 23.509 | 7.737 | 48.6% | 0.3% | 60/8280 |
| exact | 10m | cur | 3.298 | 3.172 | 0.126 | 100.0% | 0.7% | 15/635 |
| exact | 10m | avg | 1.073 | 0.804 | 0.269 | 95.2% | 5.2% | 60/8280 |

The final path receipts record matched `10,117,956` charged nodes.
The table below gives the actual first-crossing counts, **saved
linear-average** whole/post-initial-river positive reach coverage,
peak worker RSS and whole-path training/scoring runtime. The current
policies have no corresponding positive-average coverage estimator in
those receipts; their positive saved-prefix row counts are above.

| Arm | Label | Actual nodes | Whole coverage | Post-river coverage | Peak RSS bytes | Whole path seconds |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| q8 | 100k | 266,262 | 1.000 | 0.000 | 758,923,264 | 47.22 |
| q8 | 1m | 1,065,048 | 1.000 | 0.808 | 758,923,264 | 47.22 |
| q8 | 10m | 10,117,956 | 1.000 | 0.904 | 758,923,264 | 47.22 |
| exact | 100k | 266,262 | 1.000 | 0.000 | 650,543,104 | 47.43 |
| exact | 1m | 1,065,048 | 1.000 | 0.776 | 650,543,104 | 47.43 |
| exact | 10m | 10,117,956 | 1.000 | 0.855 | 650,543,104 | 47.43 |

These memory and path times come from PR #110's saved receipts; this
diagnosis itself took **59.30096229200717 seconds** under its one
900-second whole-process cap. Its separate [admission](../results/known-wet-residual-diagnosis/admission/manifest.json)
used the parent report time `68.30351770902053` seconds to preregister
`2 × parent + 120 ≈ 256.607` seconds, below 900. The first failed
fictional-proof launcher found the wrong `uv` version before any proof;
the [proof archive](../results/known-wet-residual-diagnosis/proof/manifest.json)
retains that failure and the successful pinned `uv` 0.13.5 run.

## Representative exact decisions

The selected rows contain the board, private cards, legal concrete
actions, saved probabilities, **chance-times-opponent counterfactual
reach**, full saved-prefix reach, and alternative-action values. The
values below use the **final candidate linear average against its
fixed saved opponent**, with an optimized reply continuation. They
have the acting seat's payoff sign; a less negative value is better
for that responding seat under those assumptions. Local additive gain
is a reach-weighted contribution to the full exploitability, not the
value of changing one action in the deployed two-player policy.

| Exact row | Acting seat, cards and board | Legal actions, saved probabilities | Counterfactual / saved-prefix reach | Alternative values (chips) | Additive gain (chips) |
| --- | --- | --- | ---: | --- | ---: |
| turn 1611 | seat 1, `3d 5c`; `Qs Kd As 3c` | fold .76045, call .13414, raise to 144 .06483, raise to 182 .04057 | .20384252 / .20384252 | −18.000, −13.835, −21.763, −27.202 | .430463 |
| turn 4041 | seat 1, `2d 5d`; `Qs Kd As 3c` | fold .95024, call .03283, raise to 144 .01062, raise to 182 .00631 | .20384252 / .20384252 | −18.000, −16.601, −21.588, −21.081 | .143803 |
| river 1679 | seat 1, `3d 5c`; `Qs Kd As 3c 3h` | fold .55230, call .44770 | .000077299 / .000073316 | −18.000, −136.234 | .001940 |

In row 1611, call has the highest saved-opponent continuation value,
but the final average folds 76.05% at that exact decision. Its saved
**current** policy folds 100% there and contributes `1.861634` chips,
while the average contributes `0.430463`; both use their own policy
opponent. In row 4041, the average folds 95.02% and contributes
`0.143803`; the q8 control average contributes `0.962458` at the same
exact row. River row 1679 is a low-reach example: the current candidate
has zero counterfactual reach and zero additive gain there, but the
average reaches it and calls 44.77% against the saved opponent. Its
large local call loss does **not** make it a large part of total river
exploitability. The other 17 selected rows and all 12 observations for
each are in the machine report.

## What this distinguishes and what it cannot

- **Earlier-street information grouping:** this game starts at the turn;
  no flop decision is modeled. This explanation is untested here.
- **Remaining turn/river collisions:** the candidate's exact-to-abstract
  acting mapping was checked to be the identity on every exact row.
  There are no acting turn or river collisions in this finite game.
  That rules out the specified collision mechanism here, while saying
  nothing about other games.
- **Training and averaging:** the 100k averages coincide across arms,
  and the final candidate's current/average turn gains differ markedly
  (`3.171919` versus `0.804478` chips). The fixed rows also change
  probabilities and reach across checkpoints. This is consistent with
  a training/readout hypothesis, but each checkpoint and readout has a
  different saved opponent and reach. One deterministic seed and three
  checkpoints cannot establish convergence or that additional work
  would meet the old absolute gates.
- **Specified implementation faults:** each of the 12 full exact-row
  sums matches its saved exploitability within at most
  `7.105427357601002e−14` chips; the smallest numerical contribution
  is `−2.1160115934228425e−18` chips, inside the fixed `1e−12`
  slack. All previously audited own/native scalars differ by at most
  `1.9539925233402755e−14` chips versus the `1e−9` gate. The
  [source receipt](../results/known-wet-residual-diagnosis/source-checks/manifest.json)
  binds local/optional/hosted checks to isolated code and historical
  pins. These checks reject the specified accounting/source faults;
  they cannot rule out every possible software defect.

The most focused next **hypothesis** is that a change to how the
candidate's learning or averaging handles these high-gain exact turn
decisions could reduce its remaining exploitability at matched work.
That requires a separate prospective protocol with an unchanged
known-case development role, fixed control, seeds, work, admission and
independent evaluation boundaries. The diffuse river total also
deserves a separately bounded question; selecting one attractive
river row would not address most of its gain. Neither follow-up has
started here. PR #110 remains negative, with no default change.

To inspect the same exact decisions across all published checkpoints
from the repository root:

```sh
python3 - <<'PY'
import json

report = json.load(open('results/known-wet-residual-diagnosis/diagnosis/report.json'))
for info in (1611, 4041, 1679):
    row = next(row for row in report['diagnostics'] if row['exact_info'] == info)
    print(json.dumps(row, indent=2))
PY
```

This report used the one registered run and all retained checkpoints.
No unfavorable row was replaced, no cap or seed was changed, and no
scientific retry was made. Human hands-on time and personal learning
were not reported.
