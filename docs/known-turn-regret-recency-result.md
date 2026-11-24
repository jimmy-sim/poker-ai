# Fixed known-turn signed-regret recency result

**Classification: negative on two known development games.** The [prospective protocol](known-turn-regret-recency.md) fixed the signed-regret discount, PCG64(0), work, controls, thresholds and decision rows before outcomes. The [complete report](../results/known-turn-regret-recency/report/report.json) retains 24 policy scores, 12 paired contrasts and 23 fixed decision rows with 12 observations each. These boards and ranges were previously outcome-inspected. Exploitability is exact restricted-game NashConv/2 divided by the 36-chip initial pot; smaller is better.

| Game | Charged work | Readout | Control, pots | Candidate, pots | Difference, pots |
| --- | ---: | --- | ---: | ---: | ---: |
| Wet | 266,262 | current | 1.559413 | 1.559413 | +0.000000 |
| Wet | 266,262 | linear average | 1.231005 | 1.231005 | +0.000000 |
| Wet | 1,065,048 | current | 0.627828 | 0.719009 | +0.091181 |
| Wet | 1,065,048 | linear average | 0.867957 | 0.881585 | +0.013628 |
| Wet | 10,117,956 | current | 0.091617 | 0.152559 | +0.060942 |
| Wet | 10,117,956 | linear average | 0.029805 | 0.047444 | +0.017639 |
| Dry | 127,818 | current | 1.628291 | 1.583586 | −0.044705 |
| Dry | 127,818 | linear average | 0.969442 | 0.876148 | −0.093294 |
| Dry | 1,022,544 | current | 0.339973 | 0.189501 | −0.150472 |
| Dry | 1,022,544 | linear average | 0.070316 | 0.081579 | +0.011262 |
| Dry | 10,012,410 | current | 0.296999 | 0.000000 | −0.296999 |
| Dry | 10,012,410 | linear average | 0.006423 | 0.002055 | −0.004368 |

Both arms matched charged work at every checkpoint. Wet final candidate exploitability is **1.707996887 chips / 0.047444358 pots**, versus immutable control **1.072986605 chips / 0.029805183 pots**: **+0.017639174 pots**. It fails the preregistered 0.01 final and 0.025 worst absolute limits and worsens by more than the fixed +0.001 paired limit. Dry candidate improves to **0.073980859 chips / 0.002055024 pots**, versus control **0.231219476 chips / 0.006422763 pots**, a **−0.004367739-pot** difference. Both final candidates have whole positive-average reach coverage 1.000 and zero recall violations. This mixed outcome is **negative** under the frozen rule; there was no retry, budget extension or default promotion.

Wet control/candidate final additive turn best-response gains are 0.804478/1.216056 chips and river gains 0.268508/0.491941. The two previously ranked turn rows together contribute 0.574266/0.590830 chips. Dry control/candidate turn gains are 0.151366/0.050075 and river gains 0.079854/0.023906 chips. The fixed discount helped the known dry game but increased both turn and river weaknesses in the known wet game. These are exploitability contributions against each arm's own saved opponent; they do not isolate a causal action swap.

**Representative wet turn decision:** seat one holds `3d 5c` on `Qs Kd As 3c`, pot 72 chips, with legal fold/call/raise-to-144/raise-to-182. At final average, control probabilities are 0.760453/0.134142/0.064830/0.040574; candidate probabilities are 0.485760/0.213480/0.196258/0.104502. This row's additive best-response contribution rises from 0.430463 to 0.520564 chips. Counterfactual reaches are 0.203843/0.185712. Local alternative-action values assume each arm's saved opponent and optimized reply continuation; they are not universal poker advice. The full report retains wet river row 1679 and dry turn row 2445 at all checkpoints and readouts.

The one comparison-only OpenSpiel 2.0.2 Apache-2.0 audit passed on all 12 candidate policies after own bytes were published; maximum own-versus-native scalar error was `4.263256414560601e−14` chips versus the frozen `1e−9` gate. The [native record](../results/known-turn-regret-recency/native/manifest.json) retains the license pin; no reference strategy entered training. The admitted own study took 45.139/7,200 launcher seconds, after a published conservative forecast of 1,972.992/7,200. Final wet control/candidate worker paths took 47.429/44.120 seconds and peaked at 650,543,104/650,379,264 RSS bytes; dry paths took 13.644/12.938 seconds and peaked at 156,663,808/157,155,328 bytes. Final policy tables use 5,871,360 wet and 2,348,544 dry bytes. Post-initial-river coverage is wet 0.855456/0.986902 and dry 0.969010/0.997295 (control/candidate). The [own archive](../results/known-turn-regret-recency/own/manifest.json) retains policies, guards and timings.

Inspect fixed decisions across work checkpoints and readouts from the repository root:

```sh
python3 - <<'PY'
import json
report = json.load(open('results/known-turn-regret-recency/report/report.json'))
for row in report['diagnostics']:
    if (row['game'], row['exact_info']) in {
        ('collision_medium_wet_oop-02', 1611),
        ('collision_medium_wet_oop-02', 1679),
        ('full_new_medium_dry_oop', 2445),
    }:
        print(json.dumps(row, indent=2))
PY
```

One deterministic path per known related game offers no seed-based confidence interval or transfer evidence. The discount changes current and average policy dynamics; the wet increase does not alone establish an implementation defect or a single causal action. The independent scalar audit supports this bounded negative conclusion. A distinct next question needs a new prospective protocol.

## Qualification

Corrected isolated source passed exact-source local base/optional Python 3.11/3.12, hooks and both hosted jobs. Old failed source evidence is retained in the [source receipt](../results/known-turn-regret-recency/source-checks/manifest.json). Final exact-report local, optional and hosted checks remain pending at report publication; this section does not claim them early. Human time and personal learning were not reported.
