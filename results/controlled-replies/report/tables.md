# Frozen controlled-policy within gains

Frozen controlled policies. All modes; linear regret weights.
Full controls once; sampled arithmetic means of three fixed seeds. Units: percent initial pot.

| Game / encoding | Traversal | Regret / average | Within | Turn loss | River loss |
|---|---|---|---:|---:|---:|
| dev_low_oop / exact | full | signed / uniform | 0.0106816903 | 0.0106800413 | 1.64903347e-06 |
| dev_low_oop / exact | full | signed / linear | 1.28001083e-05 | 1.28001059e-05 | 2.36797323e-12 |
| dev_low_oop / exact | full | clipped / uniform | 0.0106816903 | 0.0106800413 | 1.64903347e-06 |
| dev_low_oop / exact | full | clipped / linear | 1.28001083e-05 | 1.28001059e-05 | 2.36797323e-12 |
| dev_low_oop / exact | external | signed / uniform | 0.000696989985 | 0.000696203174 | 7.8681079e-07 |
| dev_low_oop / exact | external | signed / linear | 5.47631406e-07 | 5.47629005e-07 | 2.40148803e-12 |
| dev_low_oop / exact | external | clipped / uniform | 0.0639851439 | 0.0625326821 | 0.00145246184 |
| dev_low_oop / exact | external | clipped / linear | 0.0414792895 | 0.0407505455 | 0.000728744003 |
| dev_low_oop / texture_range_q8_b8 | full | signed / uniform | 0.0106816903 | 0.0106800413 | 1.64903347e-06 |
| dev_low_oop / texture_range_q8_b8 | full | signed / linear | 1.28001083e-05 | 1.28001059e-05 | 2.36797323e-12 |
| dev_low_oop / texture_range_q8_b8 | full | clipped / uniform | 0.0106816903 | 0.0106800413 | 1.64903347e-06 |
| dev_low_oop / texture_range_q8_b8 | full | clipped / linear | 1.28001083e-05 | 1.28001059e-05 | 2.36797323e-12 |
| dev_low_oop / texture_range_q8_b8 | external | signed / uniform | 0.000836530348 | 0.000538290254 | 0.000298240093 |
| dev_low_oop / texture_range_q8_b8 | external | signed / linear | 0.00012257492 | 0.000115251549 | 7.32337167e-06 |
| dev_low_oop / texture_range_q8_b8 | external | clipped / uniform | 0.0454058378 | 0.0449025011 | 0.000503336608 |
| dev_low_oop / texture_range_q8_b8 | external | clipped / linear | 0.0292050343 | 0.0289732298 | 0.000231804534 |
| dev_medium_oop / exact | full | signed / uniform | 1.17852656 | 0.871638062 | 0.306888497 |
| dev_medium_oop / exact | full | signed / linear | 0.28902188 | 0.155221865 | 0.133800015 |
| dev_medium_oop / exact | full | clipped / uniform | 1.22458586 | 0.985568259 | 0.239017604 |
| dev_medium_oop / exact | full | clipped / linear | 0.050212445 | 0.0381883911 | 0.012024054 |
| dev_medium_oop / exact | external | signed / uniform | 0.638878983 | 0.26364061 | 0.375238373 |
| dev_medium_oop / exact | external | signed / linear | 0.236525087 | 0.0934490914 | 0.143075996 |
| dev_medium_oop / exact | external | clipped / uniform | 3.66343305 | 2.14468696 | 1.51874609 |
| dev_medium_oop / exact | external | clipped / linear | 2.15525331 | 1.34652034 | 0.808732967 |
| dev_medium_oop / texture_range_q8_b8 | full | signed / uniform | 1.14971595 | 0.877141226 | 0.272574721 |
| dev_medium_oop / texture_range_q8_b8 | full | signed / linear | 0.370130705 | 0.2818046 | 0.0883261056 |
| dev_medium_oop / texture_range_q8_b8 | full | clipped / uniform | 1.21869686 | 0.965173391 | 0.253523465 |
| dev_medium_oop / texture_range_q8_b8 | full | clipped / linear | 0.0494715928 | 0.0363341131 | 0.0131374797 |
| dev_medium_oop / texture_range_q8_b8 | external | signed / uniform | 0.372604718 | 0.126476492 | 0.246128226 |
| dev_medium_oop / texture_range_q8_b8 | external | signed / linear | 0.243207295 | 0.14132957 | 0.101877725 |
| dev_medium_oop / texture_range_q8_b8 | external | clipped / uniform | 2.91843447 | 1.97577805 | 0.942656418 |
| dev_medium_oop / texture_range_q8_b8 | external | clipped / linear | 1.81145408 | 1.31578186 | 0.495672215 |

Street losses use saved-prefix reach and an optimal own reply suffix; they are not a causal feature attribution.
Fixed-opponent crossed EV/gain identities and every seed/target appear in crossed-targets.csv. No default or global admission.
