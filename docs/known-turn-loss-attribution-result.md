# Saved-policy loss attribution stopped at a binding guard

**Issue #4; November 24, 2026 (PST); [prospective protocol](known-turn-loss-attribution.md). Classification: inconclusive for the fixed two-game question.** The one admitted read-only run ended after 43.258 seconds with an `ArithmeticError` while opening the fourth saved policy. The [complete failed raw archive](../results/known-turn-loss-attribution/diagnosis/manifest.json) was published at `577a6b78` before this interpretation. Three of four policies and the full wet-game row report survived. No training, new reference run, budget extension or scientific retry occurred.

## Earliest cause and scope

The isolated tracer's `FOLDERS` mapping points the dry candidate to `results/known-turn-regret-recency/own/study/path00`. That published path's `summary.json` identifies the **wet** candidate. The published dry candidate is `path01`. The existing `replay_path`/`decode_mass` binding guard rejected the mismatched dry mass with `cumulative mass schema/menu/source binding changed`. This is an input-path software defect in PR #113, not evidence of a dry poker regression or a defect in the immutable saved policies. The wrong path was not used for any reported dry candidate outcome. The protocol permits one real diagnostic and says a failed binding/archive gate ends this milestone; this run is retained and is not restarted under PR #113. A corrected future measurement needs its own authorized prospective plan and full source qualification, without revising this receipt or calling it a fresh test.

## Valid partial wet-game readout

The completed wet pair is the **known, outcome-inspected** `collision_medium_wet_oop-02` game, seed PCG64(0), 10,117,956 charged visits in each saved arm, 36-chip initial pot. Its prior fixed report already established a candidate-minus-control exploitability increase of **0.635010281274127 chips** (1.7079968865541293 versus 1.0729866052800023). This new partial trace reconciled all 8,340 exact rows and the prior native scalar, with 100% whole coverage, zero published recall violations, and post-initial-river coverage 0.986902 candidate versus 0.855456 control. The two saved path runtimes were 44.120/47.429 seconds and worker peak RSS 650.379/650.543 MB (candidate/control); these are historical training-path records, not this diagnostic's 43.258-second runtime.

| Street | Net worsening, chips | Positive worsening mass | Negative offset | Top ten share of positive mass | Previously inspected rows' share | Fixed descriptive class |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Turn, 60 rows | 0.411577261568 | 0.525203965733 | 0.113626704164 | 83.056% | 62.285% | Concentrated; known rows dominant |
| River, 8,280 rows | 0.223433019706 | 0.286262528784 | 0.062829509078 | 3.919% | 0.137% | Distributed; known rows nondominant |

These are additive **best-response gain contributions** against each arm's own fixed opponent policy and optimized continuation. They are not a causal estimate of swapping one local action and are not universal poker advice. The different reaches and opponent policies across arms matter. The dry candidate, its street comparison and any two-game classification are missing; no uncertainty interval follows from one deterministic seed and two related known cases.

For one representative turn row, exact index 1611 has seat 1 holding `3d 5c` on `Qs Kd As 3c`, with legal `fold`, `call`, `raise_to 144`, `raise_to 182`. The saved control probabilities are `[0.760453, 0.134142, 0.064830, 0.040574]`; candidate probabilities are `[0.485760, 0.213480, 0.196258, 0.104502]`. Candidate-minus-control additive worsening is **0.090101305471 chips** at this row. The chance-times-opponent counterfactual reaches differ (0.203843 control, 0.185712 candidate). The [raw wet report](../results/known-turn-loss-attribution/diagnosis/partial/collision_medium_wet_oop-02-report.json) contains both full saved-prefix reaches and optimized-continuation alternative-action values. Its fixed top-ten rankings and complete row contribution vectors are retained. Inspect the same row without training:

```sh
python3 - <<'PY'
import json
from pathlib import Path
p = Path('results/known-turn-loss-attribution/diagnosis/partial/collision_medium_wet_oop-02-report.json')
d = json.loads(p.read_text())
print(next(row for row in d['diagnostics'] if row['exact_info'] == 1611))
PY
```

The wet partial suggests that the recency rule's turn worsening is concentrated while its river worsening is diffuse on this one known game. It cannot establish why that rule worsened play, whether a different training budget would help, or whether the same pattern holds on the dry game. The immediate technical lesson is to validate every fixed saved path's game and arm **before** the one-run trace in any future protocol. Historical source pins, negative PR #112 acceptance, and all saved results remain intact. Codex assisted; human hands-on time and personal learning were not reported.
