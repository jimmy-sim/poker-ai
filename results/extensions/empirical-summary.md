### Measured-return risk and fee sensitivity

All five own scripted opponents are included; OpenSpiel and Slumbot outcomes are excluded. Each fitted law contains 1,000 original deck clusters, each retaining three frozen own policies × two seats. A simulated step is one **six-hand block**, not one independent hand.

| Own opponent | Gross mbb/hand | Five-opponent lower bound | Fitted fraction | Robust fraction |
| --- | ---: | ---: | ---: | ---: |
| random | +2,400.6 | -7,196.5 | 0.5361 | 0.0000 |
| always_call | +1,953.5 | -7,643.6 | 0.3607 | 0.0000 |
| always_raise | +4,051.6 | -5,545.5 | 0.5384 | 0.0000 |
| tight_aggressive | -2,508.6 | -12,105.6 | 0.0000 | 0.0000 |
| equity | -9,201.3 | -18,798.4 | 0.0000 | 0.0000 |

**5/5 confidence-robust fractions are zero before fees.** The positive fitted fractions in some matchups depend on the empirical return law being correct; resampling does not independently establish its mean. The study includes half/full fitted sizing and confidence-robust sizing across 45 cells, each with 10,000 paths of 1,000 blocks. Five-opponent one-sided Bonferroni–Hoeffding bounds cover the same fixed target as the original duplicate study, not a population of training seeds.

The 0/5/10 bb/100 fixed costs are illustrative, not a real site's pot-rake schedule. No positive edge was established by the primary match test even before fees; positive fee-adjusted point estimates cannot prove an edge survives realistic rake.

![Measured-return risk sensitivity](results/extensions/empirical-bankroll.png)
