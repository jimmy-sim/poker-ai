### Selected quantitative extensions

Own finite-type Bayesian models: **72,000 censored toy hands**, **360 exact checkpoint profiles**. Each table cell is the final-checkpoint mean over both seats and three training histories. Positive NLL improvement means better held-out public-transcript prediction under a fixed blueprint logging policy. EV gains are exact **ante chips/hand versus the same own scripted opponent**, relative to the own CFR+ blueprint. Those gains include exploitation already available from the prior; they do not isolate the benefit of learning.

| Game | Opponent scenario | NLL improvement (nats) | Guarded EV gain | Unrestricted EV gain |
| --- | --- | ---: | ---: | ---: |
| kuhn | uniform | +0.0441 | +0.0738 | +0.3101 |
| kuhn | calling_station | +0.4407 | +0.1103 | +0.1517 |
| kuhn | aggressive | +0.4961 | +0.1479 | +0.2185 |
| kuhn | value | +0.0979 | +0.0456 | +0.1398 |
| kuhn | misspecified | +0.0622 | +0.0438 | +0.1352 |
| kuhn | switching | -0.0040 | +0.0161 | +0.0697 |
| leduc | uniform | +0.2628 | +0.0493 | +1.6662 |
| leduc | calling_station | +0.7489 | +0.0895 | +0.8345 |
| leduc | aggressive | +0.7410 | +0.2128 | +1.9847 |
| leduc | value | +0.1930 | +0.0514 | +1.0290 |
| leduc | misspecified | -0.0808 | +0.0333 | +0.6661 |
| leduc | switching | -0.5055 | +0.0600 | +1.2003 |

The model improves predictions on included stationary types but can worsen them under misspecification or drift. A root-level exploitation mixture is certified to lose at most **0.1 chip/hand of blueprint worst-case security in these exact games. This permits some degradation; it is not a Hold'em guarantee or a game-value safety claim.

![Bayesian learning and security](results/extensions/bayesian-leduc.png)

Conditional bankroll study: **120 cells**, 10,000 independent paths per cell, 1,000 steps/path. In the synthetic binary p=.55 model with sizing chosen at that assumed edge, persistence 0: threshold crossing 18.1%; persistence 0.8: threshold crossing 72.5%. The specified uncertainty set gives a robust fraction of **0**. All fixed-stake Monte Carlo controls match finite-horizon exact ruin probabilities within the predeclared reported tolerance. Fractional threshold crossing is not literal bankruptcy. Return laws, fees, stationarity and stake scaling are model assumptions; no positive real-world edge or bankroll recommendation follows.

![Conditional bankroll sensitivity](results/extensions/bankroll-risk.png)

`make analyze-extensions` reproduces both studies, posterior audit, tables and figures offline. No external solver or public benchmark outputs enter learning. See [methods, limitations and interview answers](docs/phase5-extensions.md).

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
