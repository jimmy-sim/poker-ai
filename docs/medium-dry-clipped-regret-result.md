# Clipped regret at matched river work: negative result

**Issue #4, PR #100, November 20, 2026.** This is the result of the
[prospective protocol](medium-dry-clipped-regret.md) at `3ad6004`, tested
isolated source `c996c0a`, published own evidence `ef3ac5d`, and pinned
comparison-only audit `804f35d`. Both evaluated spots were already known.
The representation, deal/range inputs, seeds, work labels, readout and gates
were fixed before outcomes. Neither arm is promoted as a default.

## Fixed 10m-work comparison

Exploitability is half the sum of the two players' exact restricted-game
best-response gains, divided by the initial pot. Lower is better. The signed
control and clipped candidate trained independently at matched charged node
work with seeds 20261371–73. Values below are final linear averages; delta
is clipped minus signed, in fractions of the initial pot.

| Known spot | Seed | Signed | Clipped | Paired delta |
| --- | ---: | ---: | ---: | ---: |
| Low/wet IP | 20261371 | 0.000946 | 0.002512 | +0.001567 |
| Low/wet IP | 20261372 | 0.000909 | 0.002470 | +0.001560 |
| Low/wet IP | 20261373 | 0.001146 | 0.002447 | +0.001301 |
| Medium/dry OOP | 20261371 | 0.035656 | 0.072249 | +0.036593 |
| Medium/dry OOP | 20261372 | 0.039542 | 0.075562 | +0.036021 |
| Medium/dry OOP | 20261373 | 0.035132 | 0.074594 | +0.039461 |

Clipped medium/dry median is **0.074594** and worst is **0.075562**,
exceeding the frozen 0.01 median and 0.025 worst limits. Its paired median is
**+0.036593**, versus the positive criterion of at most -0.001 and negative
criterion of at least +0.001. Low/wet clipped median/worst are
0.002470/0.002512, within their absolute limits, but its paired median is
**+0.001560**, above the allowed +0.001. The predeclared classification is
therefore **negative**. All six pairs worsened; no seed was discarded.

The one own run completed all 12 paths and 108 saved/replayed policy readouts
at 100k, 1m and 10m crossings. Final actual charged work was
10,000,014–10,000,169; three workers exited zero. Internal run time was
287.779 seconds and launcher wall 288.118 seconds, below the 7200-second cap.
Each final candidate had 100% whole positive-average coverage, zero
structural recall violations, and no information-key change. The final
four-float64 table estimate is 523,776 bytes for low/wet and 4,697,088
bytes for medium/dry for either rule. Whole-path times were 66.0–66.5
seconds on low/wet and 76.4–78.5 seconds on medium/dry; maximum recorded
worker high-water RSS was 239,288,320 bytes. See the
[raw own archive](../results/medium-dry-clipped-regret/own/manifest.json) for
all paths, readouts, support, memory, timing and exact scores. The pinned
OpenSpiel 2.0.2 comparison-only audit checked all 108 saved policies with
maximum scalar error `7.105427357601002e-14` chips, below `1e-9`; its
[raw rows](../results/medium-dry-clipped-regret/native/manifest.json) are
separate from training. The [complete report](../results/medium-dry-clipped-regret/report/report.json)
replays the own bytes and holds every paired seed, checkpoint and diagnostic.

Final exact-report-head qualification at `16171aa` passed base Python
3.11/3.12 (5,731 passed, 73 skipped, 150 deselected each, plus Ruff,
format and strict mypy), optional 3.11 (2,589 passed) and optional 3.12
(2,587 passed, two expected skips). Pre/post source, runtime, lock,
OpenSpiel/Numba and installed-license guards passed, as did all-file hooks.
Hosted CI run 44757177743 passed both Python jobs and hooks. The
[final check receipt](../results/medium-dry-clipped-regret/final-checks/manifest.json)
retains the role logs and official hosted log.

## What the saved decisions show

At medium/dry seed 20261371 and final work, signed turn and river
contributions were 0.264670 and 1.018938 chips; clipped contributions were
0.829936 and 1.771019 chips. Both streets worsened. The three preselected
turn rows 2443/1596/14 are in the report at every checkpoint and seed.
For example, row 2443 is seat 0 with `3s 7h` on `2s 6h Jc 3c`, facing
`fold`, `call`, `raise_to 144`, `raise_to 182`. At final work, the clipped
saved probabilities were 0.607544/0.379883/0.006054/0.006519, versus signed
0.651971/0.348022/0.000006/0.000001. Clipped's additive half-gain at this
row was 0.240843 chips, versus signed 0.090857. Its clipped counterfactual
and saved-prefix reaches were 0.306605 and 0.303299; the alternative-action
values with the saved opponent and optimal reply continuation were -18.000,
-16.093, -49.539,
-50.941 chips for the listed actions. These are diagnostic values against
the **saved opponent policy**, with an optimal exact-partition reply suffix
for the acting seat and saved-policy prefix reach. Their additive
contributions sum to fixed-profile exploitability; a local action value is
not a universal poker recommendation or a causal estimate of retraining.
The lower signed and clipped scores at later work show learning in both
arms, but clipping remained worse at the frozen final budget.

Inspect the same row across all three work checkpoints and both rules:

```sh
jq '.cases[] | select(.game=="new_medium_dry_oop" and .seed==20261371 and .readout=="linear_average") | {arm,work_label,exploitability_fraction_initial_pot,turn_contribution_chips,river_contribution_chips,row_2443:.fixed_turn_rows["2443"]}' results/medium-dry-clipped-regret/report/report.json
```

## Interpretation and limits

The data reject this clipped-update candidate **at these two known spots,
three paired seeds and the fixed 10m work budget**. The saved-policy scores
do not establish a population-level win-rate effect, unseen-spot behavior,
or why clipping worsened; the turn/river decomposition identifies where a
fixed opponent can gain, not the learning mechanism that caused it. The
clipped rule improved post-initial river coverage on medium/dry relative to
the signed control, yet its final exploitability worsened, so coverage alone
is not evidence of stronger play. No reference strategy entered training.
PR #98's negative medium/dry gate and PR #99's rejected 100m compute gate
remain unchanged. A distinct follow-up needs a new prospective contract;
this study will not be rerun with new seeds, thresholds, representation or
budget to seek a favorable result.

## Review questions

1. **Why compare at matched node work?** It charges both learners for the
   same number of visited decision nodes, so the result concerns the update
   rule rather than simply giving one arm more training.
2. **Why can coverage improve while play worsens?** Coverage says the saved
   average reached information rows; it does not say the action probabilities
   at those rows resist a best response. Medium/dry clipped coverage rose
   after initialization while exploitability also rose.
3. **What does the independent audit establish?** The pinned reference
   reproduced scalar scores for the exact saved policies within `1e-9`
   chips. It does not supply training strategy or generalize beyond these
   finite games.
