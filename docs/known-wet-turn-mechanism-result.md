# Exact acting-turn keys on one known medium/wet game

**Prospective protocol:** [one known wet game](known-wet-turn-mechanism.md). **Machine report:** [12 saved policies, six paired contrasts and fixed decision rows](../results/known-wet-turn-mechanism/report/report.json). This is PR #109's already structurally inspected first-eligible medium/wet out-of-position input, `Qs Kd As 3c`, with five private combos per seat and a 36-chip initial pot. It is a **known case**, not unseen validation or a board-texture-isolated comparison. The q8-turn/exact-river control and unchanged exact-acting-turn/exact-river candidate each used deterministic PCG64 seed zero, identical full expected charged work, and the same exact game and chance. No default changes.

## Fixed-work poker result

Exact restricted-game exploitability is NashConv/2: the optimized best-response gain in chips, divided by the initial pot for the table below. Lower is better. The first complete target-pair crossings reached 266,262, 1,065,048 and 10,117,956 charged nodes for **both** arms; nominal labels are shown here.

| Charged work label | Readout | Q8 control, initial pots | Exact-turn candidate | Candidate minus control |
| ---: | --- | ---: | ---: | ---: |
| 100,000 | Current | 1.555381 | 1.559413 | +0.004033 |
| 100,000 | Linear average | 1.231005 | 1.231005 | 0.000000 |
| 1,000,000 | Current | 0.652467 | 0.627828 | −0.024639 |
| 1,000,000 | Linear average | 0.870651 | 0.867957 | −0.002694 |
| 10,000,000 | Current | 0.291018 | 0.091617 | −0.199400 |
| 10,000,000 | Linear average | 0.061846997 | 0.029805183 | −0.032041814 |

The final linear averages are 2.2264918915312473 chips for control and 1.0729866052800023 chips for candidate, a candidate-minus-control difference of **−1.153505286251245 chips**. The paired gain clears the frozen −0.001-pot improvement margin. **Classification: negative under the prospective rule**, because the candidate's 0.02980518348 initial pots exceeds both the final ≤0.01-pot and one-path worst ≤0.025-pot absolute gates. The control also fails its absolute gates. Whole positive-average uniform-reach coverage is 1.0 for both, and recall violations are zero. Candidate post-initial-river coverage is 0.855456 versus control 0.903896, a readout without a new acceptance threshold. One deterministic path per arm yields no seed-based confidence interval or population transfer claim. The unchanged PR #109 three-stratum structural failure stays inconclusive; this study does not rescue it.

At the final average, the control's additive best-response gain is 1.681914 chips on turn and 0.544578 on river. The candidate has 0.804478 turn and 0.268508 river chips. Both streets improve, but enough residual gain remains to fail the absolute gates. The exact-turn partition uses 8,340 information rows versus 8,334 for control, and 5,871,360 versus 5,867,136 table bytes under the report's two-array padded-width convention. The two-path launcher took 48.3169 seconds under 7,200; path walls were 47.2166/47.4288 seconds, with peak worker RSS 758,923,264/650,543,104 bytes (control/candidate). Raw policies, scores, masses, timings and partial event logs are in the [own archive](../results/known-wet-turn-mechanism/own/manifest.json).

## What the saved decisions show

The [machine report](../results/known-wet-turn-mechanism/report/report.json) fixes the control's final top three additive gain rows on each of turn and river, plus its top three collided turn rows, with overlap leaving eight distinct rows. It displays those **same** exact rows for both arms, all three work labels and both readouts. Each observation includes board, private cards, legal actions, saved probabilities, counterfactual and saved-prefix reach, alternative-action values and additive gain. The values assume that row's saved opponent strategy and an optimized best-response continuation; they are neither universal poker advice nor the causal value of changing one action.

For example, final-average turn exact row 4041 is seat one's `2d 5d` on `Qs Kd As 3c`, pot 72 chips, with fold/call/raise-to-144/raise-to-182 legal. It is both the largest control turn gain and largest collided-turn row. The q8 control saves fold probability 0.973045, with conditional values −18.000 for fold and −7.949 for call, counterfactual and saved-prefix reaches 0.194841, and additive best-response gain 0.962458 chips. The exact-turn candidate saves fold 0.950242; against its **different saved opponent and continuation**, fold/call values are −18.000/−16.601, reaches 0.203843 and gain 0.143803 chips. Those local values explain a major control vulnerability and a smaller remaining candidate vulnerability under the declared continuations; they do not prescribe a live action.

A river example is seat one's `3d 5c` on `Qs Kd As 3c 3h`, pot 108 chips, exact row 1686, legal check/raise-to-108/raise-to-146. Its final-average additive gain is 0.007396 chips for control and 0.000172 for candidate. The archived report gives the full saved probabilities, reach weights and alternative values for this and the other fixed rows.

Inspect the same representative decisions across work labels and readouts from the repository root:

```sh
python3 - <<'PY'
import json
report = json.load(open('results/known-wet-turn-mechanism/report/report.json'))
for row in report['diagnostics']:
    if row['exact_info'] in (4041, 1686):
        print(json.dumps(row, indent=2))
PY
```

## Independent check and limits

The [comparison-only OpenSpiel 2.0.2 audit](../results/known-wet-turn-mechanism/native/manifest.json) checked all 12 already-published own-policy scalars in 85.1616 seconds under 900. Maximum own/reference error was `1.9539925233402755e−14` chips, below the fixed `1e−9` tolerance. The installed Apache-2.0 license SHA-256 was `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`; reference strategies never entered training. The corrected exact-source local base/optional lanes, hooks and both [source-head hosted jobs](https://github.com/jimmy-sim/poker-ai/actions/runs/45339987008) passed before the fictional proof. The [source](../results/known-wet-turn-mechanism/source-checks/manifest.json), [proof](../results/known-wet-turn-mechanism/own-proof/manifest.json), [profile](../results/known-wet-turn-mechanism/profile/manifest.json) and [admission](../results/known-wet-turn-mechanism/admission/manifest.json) receipts preserve the publication gates. The profile's worst-repeat 10m estimate yielded a separately published conservative bound of `2,036.2455<7,200` seconds. The first locally/hosted-qualified source is retained as superseded by a pre-outcome report readout correction. Final exact-report qualification and final hosted CI are pending; report software qualification must be reported separately from the negative scientific result.

The next research question should address the remaining turn and river best-response gains without relabeling this known game as unseen, extending this protocol's budgets, or adjusting a representation against its evaluation result. Any distinct follow-up needs its own prospective protocol and controls. This study supports a gain on one known finite game, while its registered acceptance claim is **negative**.

## Three checks on interpretation

1. **What does 0.029805 initial pots mean?** An exact best reply gains about 1.073 chips against the candidate's saved final average in this restricted 36-chip-pot game; it is above the preset 0.01-pot gate.
2. **Why is a 1.1535-chip paired improvement still negative?** The protocol requires both paired improvement and absolute strength/coverage/recall gates; the candidate misses both absolute exploitability bounds.
3. **Can row 4041 tell us to call in ordinary poker?** No. Its values use this fixed game's ranges, saved opponent policy and optimized continuation; the two arms also induce different opponent policies and reaches.
