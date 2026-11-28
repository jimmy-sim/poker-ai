# Uniform-regret transfer on four known medium games: negative

**Issue #4, [PR #120](https://github.com/jimmy-sim/poker-ai/pull/120), November 28, 2026 (PST).** The [prospective protocol](known-turn-uniform-regret-transfer.md) fixed all four already inspected, collision-containing PR #116 medium OOP games before any candidate measurement. The candidate changed only the signed regret increment time multiplier from iteration `t` to `1`; exact acting-turn and river information, legal actions, chance/range/payoffs, full expected target passes, linear strategy averaging and work crossings stayed fixed. This was one deterministic path per game, not seed replication or unseen validation.

## Fixed primary result

The primary score is exact restricted-game NashConv/2 divided by the 36-chip initial pot, at 40m nominal charged work using the linear-average policy; lower means less gain available to a best response. The immutable PR #116 exact-turn snapshots are the matched-work control. Both arms reached **40,205,562 actual visits** for each game. The [complete own archive](../results/known-turn-uniform-regret-transfer/own/manifest.json), [candidate-only independent scalar audit](../results/known-turn-uniform-regret-transfer/native/manifest.json) and [fixed report](../results/known-turn-uniform-regret-transfer/report/manifest.json) retain all 10m/20m/40m current and average policies, 24 paired contrasts and 42 preregistered decision rows.

| Already known game | Control | Uniform-regret candidate | Candidate minus control | Candidate turn / river gain, chips |
| --- | ---: | ---: | ---: | ---: |
| Dry A | 0.013575482 | 0.034279639 | +0.020704157 | 0.557011 / 0.677056 |
| Wet A | 0.017677381 | 0.046310471 | +0.028633090 | 0.797108 / 0.870069 |
| Dry B | 0.020656811 | 0.049307808 | +0.028650997 | 1.189667 / 0.585414 |
| Wet B | 0.016751887 | 0.052628450 | +0.035876563 | 1.072491 / 0.822133 |

**Negative under the frozen gates.** All four candidate scores exceed the `0.01`-pot absolute limit, and every paired change exceeds the `+0.001` regression limit. The paired changes range from `+0.020704157` to `+0.035876563`, median `+0.028642043`; the worst candidate is `0.052628450` pot, above the `0.025` worst limit. All candidate whole-tree coverage values are `1.000`, with zero recall violations; post-initial-river coverage is `0.949352`, `0.901559`, `0.929325`, `0.923212` in table order. Each policy table is 5,871,360 bytes. The own run finished in **134.396 whole seconds** (<7,200), with maximum per-worker high-water RSS **977,076,224 bytes** (<strict 1.5 GB); its four individual path times were 66.068, 66.181, 67.030 and 67.000 seconds in dry A, wet A, dry B, wet B order. No run was retried, no budget or threshold changed, and no default was promoted.

## What the decision rows show

The fixed row set came from [PR #119's published diagnostic](known-mixture-residual-map-result.md), before this candidate was trained. For example, on dry B's `5c 8s Jh 9c` turn with `Kd Ks` at exact row 7506, the legal actions are check, raise to 36, raise to 182. The old control saved probabilities are `[0.049527, 0.948127, 0.002345]`; the candidate's are `[0.049928, 0.941780, 0.008292]`. Their additive best-response contributions are **0.049351** and **0.356839** chips, respectively. The candidate row has counterfactual reach `0.300000`, and its alternative-action values under its own saved opponent and optimized continuation are `[29.021138, 26.575616, 19.881144]` chips. The much larger diagnostic contribution despite similar local probabilities shows why a row's contribution cannot be interpreted as the causal value of changing just that action: the opponent policy and reply continuation also differ.

On wet B's `Ad Kc Jd 9s` turn with `2c 3s` at exact row 1, the same three actions are available. Control probabilities are `[0.114850, 0.882902, 0.002248]` and candidate probabilities `[0.077380, 0.922117, 0.000503]`; additive contributions are **0.019526** and **0.225780** chips. Candidate counterfactual reach is `0.249619`, with alternative values `[-3.474307, -5.435068, -5.368079]` chips under that saved opponent and optimized continuation. These are restricted-game best-response diagnostics, **not universal poker advice**. The report includes each selected row's board, private cards, legal actions, saved probabilities, counterfactual and saved-prefix reaches, alternative values and additive gain for every checkpoint/readout in both arms.

From the repository root, inspect these same decisions across checkpoints:

```sh
python3 - <<'PY'
import json
from pathlib import Path

report = json.loads(Path('results/known-turn-uniform-regret-transfer/report/report.json').read_text())
for row in report['diagnostics']:
    if (row['game'], row['exact_info']) not in {
        ('collision_medium_dry_oop_b', 7506),
        ('collision_medium_wet_oop_b', 1),
    }:
        continue
    print(row['game'], row['street'], row['board'], row['hole'], row['legal_actions'])
    for item in row['observations']:
        print(item['arm'], item['work_label'], item['readout'],
              'probabilities=', item['saved_probabilities'],
              'reach=', item['counterfactual_reach'],
              'gain_chips=', item['additive_contribution_chips'])
PY
```

## Qualification, scope and next decision

Final exact-report qualification subsequently passed on `de1a992f`: base Python 3.11 and 3.12 each had 5,888 passed, 73 skipped and 150 slow tests deselected, with Ruff, format, strict mypy and pre/post source guards. Optional 3.11 had 2,601 passed; optional 3.12 had 2,599 passed and two skipped. Pinned all-file hooks and all four [hosted CI46148293429](https://github.com/jimmy-sim/poker-ai/actions/runs/46148293429) jobs passed. The [final receipt](../results/known-turn-uniform-regret-transfer/final-checks/manifest.json) retains the source-bound local and hosted logs. Receipt publication, receipt-head CI and solo review remain separate before merge.

The exact-source gate at `bcd43332` passed base Python 3.11/3.12 (5,888 tests each, 73 skipped, 150 slow deselected), optional 3.11 (2,601 passed), optional 3.12 (2,599 passed/two skipped), Ruff, format, strict mypy, pinned hooks and all four hosted source jobs. Its [receipt](../results/known-turn-uniform-regret-transfer/source-checks/manifest.json) preserves an earlier runner-only historical-status precheck failure. Fictional `1`-versus-`t` proof passed in 0.963 seconds without real policy access. The complete twelve-path 5m profile ran in 147.941 seconds; slowest-repeat conservative bound was **2,771.724 < 7,200**, separately admitted before the own run. All own bytes were published and GitHub-byte-verified before the comparison-only OpenSpiel 2.0.2 audit. Its 24 scalar cases finished in 171.926 seconds (<900), maximum difference **1.066e-14 chips** (<`1e-9`); the installed Apache-2.0 license SHA-256 matched the frozen pin. [Admission](../results/known-turn-uniform-regret-transfer/admission/manifest.json) and [audit admission](../results/known-turn-uniform-regret-transfer/audit-admission/manifest.json) are separate published decisions. At report publication, final report-head local/optional/hosted qualification and PR review were pending; the subsequent check result is recorded above.

The four games are structurally selected, dependent, and previously inspected; one deterministic path per arm gives no seed-based confidence interval. This result is a clear regression **for these known restricted games at matched 40m work**, not a population claim about new boards, full-game Hold'em, or the merit of uniform regret weighting in every setting. The earlier favorable 10m controlled-learning row was on a different known game and does not transfer here. The next research decision should use this negative transfer and the retained turn/river contributions to choose a distinct, prospectively registered question; no more training of this candidate or favorable seed/spot search is warranted.
