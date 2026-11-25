# Collision-conditioned medium-input turn transfer: negative

**Issue #4; PR #116; November 24, 2026 (PST).** This is the fixed report for the [prospective protocol](known-turn-collision-medium-transfer.md). The one score-free screen selected the first eligible dry A, wet A, dry B and wet B inputs at attempts 3, 15, 1 and 15. All 49 previously inspected physical inputs and their flop-rank/turn-rank signatures were excluded. Selection required at least four collided exact acting-turn rows, so this conclusion applies only to collision-containing medium out-of-position games on the known public betting template. These four dependent, deterministic games do not support a seed confidence interval, collision-prevalence estimate, unseen-template claim or general poker-strength claim.

## Fixed 40m decision

The metric is exact restricted-game NashConv/2, divided by the **36-chip initial pot**; lower is better. Both representations used the unchanged full expected trainer, identical game/action/chance/payoff arrays, and exactly matched charged work per pair. The final linear-average readout is fixed in advance.

| Input and turn board | q8 control | Exact-turn candidate | Candidate minus control | Candidate turn / river gain (chips) |
| --- | ---: | ---: | ---: | ---: |
| dry A: `4c Ks 9d Ts` | 0.018245221 | 0.013575482 | −0.004669739 | 0.263292 / 0.225425 |
| wet A: `7s 9h 6s 2s` | 0.017125132 | 0.017677381 | +0.000552249 | 0.356273 / 0.280113 |
| dry B: `5c 8s Jh 9c` | 0.030011787 | 0.020656811 | −0.009354976 | 0.594281 / 0.149364 |
| wet B: `Ad Kc Jd 9s` | 0.017896174 | 0.016751887 | −0.001144286 | 0.329937 / 0.273131 |

**Classification: negative.** Every candidate exceeds the unchanged `≤0.01`-pot absolute gate, despite relative gains in three pairs; wet A regresses. The candidate's worst deterministic value on each input is its sole final value and also passes the redundant `≤0.025` worst gate. Whole positive-average uniform-reach coverage is `1.0` for all eight final policies, and recall violations are zero. Candidate post-initial-river coverage is 0.971726, 0.940138, 0.932466 and 0.957779 in table order. The candidate policy table uses 5,871,360 bytes per input versus control 5,862,912–5,867,136 bytes. Dry paired median is −0.007012358 pots (range −0.009354976 to −0.004669739); wet median is −0.000296019 (range −0.001144286 to +0.000552249), with only two dependent inputs per texture. These are descriptive, not uncertainty estimates.

The [complete fixed report](../results/known-turn-collision-medium-transfer/report/report.json) includes all **24 paired current/average contrasts** at 10m, 20m and 40m, all 48 policies/scores, turn/river additive accounting, and the same selected decision rows at each checkpoint. At 40m the average contrasts for dry A/dry B improved from −0.000252/−0.009012 at 10m to −0.004670/−0.009355; wet A changed from −0.006207 at 10m to +0.000552 at 40m. This is a checkpoint description, not permission to select a more favorable budget. Final actual paired charged work was 40,205,562 per input. The sole eight-path own run took 287.409 seconds internally/289.327 seconds end to end under the 7,200-second cap, with 1,100,218,368-byte maximum worker RSS under the 1.5-billion-byte cap on an Apple M4. The one fixed report took 284.163 seconds end to end. The [published proof](../results/known-turn-collision-medium-transfer/own-proof/manifest.json), [profile](../results/known-turn-collision-medium-transfer/profile/manifest.json), [admission](../results/known-turn-collision-medium-transfer/admission/manifest.json) and [own archive](../results/known-turn-collision-medium-transfer/own/manifest.json) preserve the qualified path and raw evidence, including failures.

## Representative saved decisions

Rows below were selected by the frozen rule: highest additive turn gain in the **control final-average** policy for each of two inputs, then replayed at the same exact row for the candidate. Actions and probabilities are in the displayed order. The values are chips for the acting seat, using each arm's saved opponent and optimized best-reply continuation. Counterfactual reach multiplies chance and opponent probabilities; saved-prefix reach also includes the saved acting policy. Contribution is additive best-response gain across the exact-game tree, not a causal one-action swap or universal poker advice.

| Input; private cards; legal actions | Control probabilities; reach; values; gain | Candidate probabilities; reach; values; gain |
| --- | --- | --- |
| dry A `2s 9s`; `check`, `raise_to 36`, `raise_to 182` | 0.029241 / 0.967571 / 0.003188; reach 0.099907; values 22.811 / 19.143 / 9.935; gain 0.179374 | 0.055657 / 0.928994 / 0.015349; reach 0.099771; values 19.495 / 19.194 / 18.196; gain 0.014943 |
| dry B `4c Ts`; `check`, `raise_to 36`, `raise_to 182` | 0.074988 / 0.923560 / 0.001452; reach 0.200000; values −3.728 / −6.137 / −8.365; gain 0.223186 | 0.067516 / 0.929763 / 0.002720; reach 0.200000; values −5.079 / −5.792 / −8.386; gain 0.067240 |

The wet A candidate's turn and river aggregate gains both rise, from control 0.340981/0.275523 chips to 0.356273/0.280113. At its top control turn row (`3d 7h` on `7s 9h 6s 2s`, actions fold/call/raise to 144/182), the candidate's local gain *falls* from 0.054468 to 0.052907 chips. Thus that single local improvement does not explain the aggregate wet regression; the complete additive rows in the raw report are required for attribution. The unchanged representation does not resolve all remaining turn and river weaknesses. No new experiment or default promotion follows from this result.

Inspect those same saved rows across all three checkpoints with:

```sh
python3 - <<'PY'
import json
from pathlib import Path
r = json.loads(Path('results/known-turn-collision-medium-transfer/report/report.json').read_text())
for d in r['diagnostics']:
    if d['game'] == 'collision_medium_dry_oop_a' and d['street'] == 'TURN' and d['control_final_rank_within_street'] == 1:
        print(d['game'], d['hole'], d['board'], d['legal_actions'])
        for o in d['observations']:
            if o['readout'] == 'linear_average':
                print(o['arm'], o['work_label'], o['saved_probabilities'], o['counterfactual_reach'], o['saved_prefix_reach'], o['alternative_action_values_chips'], o['additive_contribution_chips'])
PY
```

The [pinned OpenSpiel 2.0.2 comparison-only audit](../results/known-turn-collision-medium-transfer/native/manifest.json) checked all 48 own scalar scores; maximum difference was `1.2434497875801753e-14` chips against the fixed `1e-9` tolerance. Reference outputs were never used for training or selection. Its installed Apache-2.0 license SHA-256 is `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`. The exact report reconciles turn/river row gains. The final report-head local, optional and hosted qualification remains to be completed and is recorded separately from this scientific conclusion.
