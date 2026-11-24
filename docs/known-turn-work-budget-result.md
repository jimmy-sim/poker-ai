# Result: unchanged exact-turn learner at longer matched work

**Issue #4; November 24, 2026 (PST). Classification: negative on the two already known games.** This is the single run under the [prospective protocol](known-turn-work-budget.md) and [machine contract](../configs/known-turn-work-budget.json), with source fingerprint `2a64f9e0e5cc620d50d43e595ab3e4e1e4b3414a729b5d487048f7a33e410d7a`. The [complete fixed report](../results/known-turn-work-budget/report/manifest.json), [own policies](../results/known-turn-work-budget/own/manifest.json), [independent audit](../results/known-turn-work-budget/native/manifest.json), [profile](../results/known-turn-work-budget/profile/manifest.json) and [admission](../results/known-turn-work-budget/admission/manifest.json) give the exact rerunnable evidence. Neither game was unseen. No policy or protocol was tuned to these outcomes; no default is promoted.

## Decision under the frozen rule

At the final 40m first complete crossing, the wet exact-turn **linear average** is `0.01004401976136313` initial pots (`0.36158471140907267` chips), above the required `0.01` pots (`0.36` chips) by `0.00004401976136313` pots (`0.00158471140907267` chips). This is a strict miss without rounding or tolerance. The dry candidate is `0.0013657276180571503` pots and passes. Both candidate-control improvements exceed the required `0.001` pots, both whole coverages are 1.0, and recall violations are zero. The worst candidate is below the separate 0.025 limit. Because the wet absolute gate fails while all required correctness and independent scalar checks pass, the two-known-game conclusion is **negative**.

The wet candidate does show the prospectively defined descriptive **continuing decline**: its 40m-minus-10m and 40m-minus-20m average changes are `−0.019761163718636936` and `−0.012256005719024087` pots, exceeding the required declines of `0.005` and `0.001`. This shows a bounded budget response, not eventual convergence or accepted strength. The candidate and control each ran one deterministic full expected path from fresh uniform current/average policies with PCG64 seed 0; changing the nominal seed would not create independent replicates.

## All saved readouts and matched work

NashConv/2 is half the sum of the two seats’ unilateral best-response gains against the saved policy, in chips; smaller is better. Fraction is chips divided by the loaded 36-chip initial pot. `Current` is the last learner policy, while `average` is its linear-time average. All values below come from the same four continuous paths; actual charged work matches arms within each game.

| Game | Arm | Target / actual work | Current chips | Average chips | Average / pot | Average turn chips | Average river chips | Whole / post-initial-river coverage |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| wet | q8 control | 10m / 10,117,956 | 10.476637195 | 2.226491892 | 0.061846997 | 1.681913965 | 0.544577926 | 1.000000 / 0.903896 |
| wet | q8 control | 20m / 20,235,912 | 7.565149172 | 1.420787090 | 0.039466308 | 1.257502484 | 0.163284606 | 1.000000 / 0.903896 |
| wet | q8 control | 40m / 40,205,562 | 9.350569005 | 1.056714198 | 0.029353172 | 0.955010790 | 0.101703408 | 1.000000 / 0.904104 |
| wet | exact-turn candidate | 10m / 10,117,956 | 3.298219874 | 1.072986605 | 0.029805183 | 0.804478484 | 0.268508122 | 1.000000 / 0.855456 |
| wet | exact-turn candidate | 20m / 20,235,912 | 12.995174086 | 0.802800917 | 0.022300025 | 0.588758804 | 0.214042113 | 1.000000 / 0.855508 |
| wet | exact-turn candidate | 40m / 40,205,562 | 4.072383598 | 0.361584711 | 0.010044020 | 0.294875604 | 0.066709107 | 1.000000 / 0.855508 |
| dry | q8 control | 10m / 10,012,410 | 8.799599862 | 0.904253779 | 0.025118161 | 0.861096265 | 0.043157515 | 1.000000 / 0.994179 |
| dry | q8 control | 20m / 20,024,820 | 1.729647780 | 0.521076500 | 0.014474347 | 0.515087992 | 0.005988508 | 1.000000 / 0.994179 |
| dry | q8 control | 40m / 40,007,034 | 9.401427246 | 0.312482826 | 0.008680078 | 0.277576499 | 0.034906327 | 1.000000 / 0.994179 |
| dry | exact-turn candidate | 10m / 10,012,410 | 10.691960402 | 0.231219476 | 0.006422763 | 0.151365932 | 0.079853544 | 1.000000 / 0.969010 |
| dry | exact-turn candidate | 20m / 20,024,820 | 2.523150525 | 0.089299250 | 0.002480535 | 0.066298535 | 0.023000716 | 1.000000 / 0.990817 |
| dry | exact-turn candidate | 40m / 40,007,034 | 10.913703612 | 0.049166194 | 0.001365728 | 0.034115126 | 0.015051069 | 1.000000 / 0.990817 |

At 40m, paired candidate-minus-control average exploitability is `−0.019309152409872323` pots wet and `−0.007314350880664468` dry. The [raw report](../results/known-turn-work-budget/report/report.json) also retains all twelve paired work/readout contrasts, exact contribution vectors for all 24 policies, memory/table bytes, zero-recall checks and zero-reach decision rows. Current policies can be much worse than their averages; the 40m exact-turn current values are 4.072384 chips wet and 10.913704 chips dry. This is one reason not to infer convergence from the averages alone.

## Representative decisions and assumptions

The largest remaining wet candidate turn contribution at 40m is exact row `1611`: seat 1 with `3d 5c` on `Qs Kd As 3c`, facing a 72-chip pot and legal `fold`, `call`, `raise_to 144`, `raise_to 182`. The saved exact-turn average chooses these with probabilities `[0.91641, 0.07672, 0.00425, 0.00262]`; its chance-times-opponent counterfactual reach and full saved-prefix reach are both `0.202644`, optimized-continuation alternative values are about `[-18.00000, -15.50002, -21.96314, -30.57310]` chips, and this row contributes `0.23891168` chips to NashConv/2. At 10m and 20m its candidate contributions were `0.43046290` and `0.46979094` chips. The remaining 40m wet candidate turn/river gains are `0.294875604`/`0.066709107` chips. The known dry row `2445` (`9h Jh` on `As Jc 5d 3h`, fold/call) contributes `0.00069091` chips to the final exact-turn average versus `0.00554276` for q8 control.

Each local alternative value assumes the **same saved opponent** for that policy and an **optimized best-response continuation**. The two arms therefore use different opponents, reaches and continuations. A row contribution measures exploitability accounting; it is neither a causal one-action swap nor universal poker advice. The complete report includes the prospectively fixed rows, the top ten candidate turn and river rows in each game, board/private cards, legal concrete actions, both arms’ saved probabilities, reaches and continuation values at all checkpoints. Whole average coverage is 1.0 for both final candidates; post-initial-river coverage is 0.855508 wet and 0.990817 dry, a descriptive support measure rather than the frozen whole-coverage acceptance gate.

## Checks, compute and limitations

- Prospective protocol, isolated source, exact-source receipt, fictional proof, complete 12-path profile, separate admission, own policies and comparison-only audit were published and remote-byte-verified at distinct checkpoints. Historical 10m policy hashes reproduced exactly. No training restart, seed search or budget extension occurred.
- Exact-source local base Python 3.11 and 3.12 each passed 5,841 fast tests, 73 skipped and 150 slow deselected; optional 3.11 passed 2,601, optional 3.12 passed 2,599 with two skips. Strict mypy, Ruff, formatting, all-file hooks and both source-head hosted jobs passed. Final exact-report checks remain to be completed at this report checkpoint.
- The profile completed all twelve 1m paths in 80.961 whole seconds, with maximum worker RSS 813,301,760 bytes. The separately published strict forecast was `5273.267051859777 < 7200` seconds. The one own run took 105.822 whole seconds, max worker RSS 786,169,856 bytes; the 24-case native audit took 99.306 whole seconds and had maximum error `6.750155989720952e-14` chips versus the `1e-9` tolerance. Installed OpenSpiel 2.0.2 Apache-2.0 license SHA-256 was `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`. Reference strategies remained comparison-only.
- These two previously inspected, dependent finite turn-start games and deterministic seed 0 provide no seed confidence interval, unseen-transfer evidence or full-game strength claim. The wet average still misses the absolute target. Earlier failed PR #113 attribution and all canceled intermediate CI logs remain retained. No default promotion or new experiment follows.

## Inspect the same saved decisions

From the repository root, this read-only Terminal command prints the same exact row for both arms at all three checkpoints, with saved probabilities, reach weights and alternative values:

```sh
python3 - <<'PY'
import json
from pathlib import Path
report = json.loads(Path("results/known-turn-work-budget/report/report.json").read_text())
for game, info in (("collision_medium_wet_oop-02", 1611), ("full_new_medium_dry_oop", 2445)):
    row = next(d for d in report["diagnostics"] if d["game"] == game and d["exact_info"] == info)
    print(game, row["hole"], row["board"], row["legal_actions"])
    for item in row["observations"]:
        if item["readout"] == "linear_average":
            print(item["arm"], item["work_label"], item["saved_probabilities"], item["counterfactual_reach"], item["saved_prefix_reach"], item["alternative_action_values_chips"], item["additive_contribution_chips"])
PY
```

The machine-readable report can be regenerated from the published source using `scripts/report_known_turn_work_budget.py` with the original published own and native archives, subject to its clean-checkout and exact-source guards. Human hands-on time and personal learning were not reported.
