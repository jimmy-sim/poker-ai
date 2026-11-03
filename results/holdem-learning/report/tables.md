# Own postflop learning diagnostic

Audit: **passed**. Held-out learning gate: **FAILED**.

Exploitability is exact restricted-game NashConv/2, divided by the initial pot.
Each range has only two physical combos per seat. Each game receives its own training.

| Experiment | Spot | Encoding | Median ε/pot | Worst seed | Min average coverage | Initial-only rows (max) |
|---|---|---|---:|---:|---:|---:|
| uniform | dev_low_oop | exact | 5.75111273e-06 | 6.48616902e-05 | 76.88% | 0 |
| uniform | dev_medium_oop | exact | 0.00943260236 | 0.0160028281 | 97.54% | 0 |
| warm | dev_low_oop | exact | 2.24058355e-06 | 4.22381447e-06 | 100.00% | 368 |
| warm | dev_medium_oop | exact | 0.00852745724 | 0.0105118037 | 100.00% | 1144 |
| linear | dev_low_oop | exact | 4.43152029e-09 | 5.06777557e-07 | 82.44% | 0 |
| linear | dev_medium_oop | exact | 0.00232078113 | 0.00273002229 | 97.71% | 0 |
| linear-warm | dev_low_oop | exact | 7.98508365e-11 | 2.72253309e-10 | 100.00% | 368 |
| linear-warm | dev_medium_oop | exact | 0.00300824098 | 0.00351348633 | 100.00% | 827 |
| representations | dev_low_oop | legacy_b8 | 5.58172877e-11 | 0.00252892169 | 100.00% | 26 |
| representations | dev_low_oop | public_b8 | 5.58172877e-11 | 3.90401414e-09 | 100.00% | 358 |
| representations | dev_medium_oop | legacy_b8 | 0.164301142 | 0.221189749 | 100.00% | 50 |
| representations | dev_medium_oop | public_b8 | 0.00300824098 | 0.00351348633 | 100.00% | 827 |
| heldout | heldout_low_oop | exact | 1.05191682e-08 | 4.002031e-08 | 100.00% | 106 |
| heldout | heldout_low_oop | legacy_b8 | 6.93479148e-09 | 1.70696896e-08 | 100.00% | 5 |
| heldout | heldout_low_oop | public_b8 | 1.05191682e-08 | 4.002031e-08 | 100.00% | 106 |
| heldout | heldout_medium_ip | exact | 0.0101528588 | 0.0106645246 | 100.00% | 167 |
| heldout | heldout_medium_ip | legacy_b8 | 0.18719347 | 0.193698314 | 100.00% | 5 |
| heldout | heldout_medium_ip | public_b8 | 0.0101528588 | 0.0106645246 | 100.00% | 167 |

The preset median target is ≤0.01 pots; worst seed ≤0.025; coverage ≥95%.
Initialization calculates every row once; 100% average-row coverage does not mean every row was subsequently sampled.

## Cross-play against own full-tree CFR+ control

Positive EV favors the tested strategy; averaged over its two seats. This is not a best-response metric.
The row L1 gap uses uniform-policy decision reach; range 0–2. Different equilibria can have different actions.

| Experiment | Spot | Encoding | Seed | EV/pot | Weighted row L1 |
|---|---|---|---:|---:|---:|
| uniform | dev_low_oop | exact | 20261208 | -1.88333459e-05 | 0.24073 |
| uniform | dev_low_oop | exact | 20261209 | -3.05370279e-06 | 0.437508 |
| uniform | dev_low_oop | exact | 20261210 | -4.43299549e-06 | 0.448601 |
| uniform | dev_medium_oop | exact | 20261208 | -0.00410272566 | 0.352447 |
| uniform | dev_medium_oop | exact | 20261209 | -0.00415171293 | 0.385439 |
| uniform | dev_medium_oop | exact | 20261210 | -0.00384772301 | 0.361005 |
| warm | dev_low_oop | exact | 20261208 | -2.09187757e-06 | 0.407888 |
| warm | dev_low_oop | exact | 20261209 | -1.18997005e-06 | 0.407885 |
| warm | dev_low_oop | exact | 20261210 | -9.96044259e-07 | 0.407884 |
| warm | dev_medium_oop | exact | 20261208 | -0.00310310539 | 0.369648 |
| warm | dev_medium_oop | exact | 20261209 | -0.00298476942 | 0.357187 |
| warm | dev_medium_oop | exact | 20261210 | -0.00323541686 | 0.357339 |
| linear | dev_low_oop | exact | 20261208 | 1.92776362e-08 | 0.365928 |
| linear | dev_low_oop | exact | 20261209 | 2.00050711e-08 | 0.444523 |
| linear | dev_low_oop | exact | 20261210 | -1.12489348e-07 | 0.225567 |
| linear | dev_medium_oop | exact | 20261208 | -0.000907804314 | 0.259927 |
| linear | dev_medium_oop | exact | 20261209 | -0.00101255193 | 0.259083 |
| linear | dev_medium_oop | exact | 20261210 | -0.00108334466 | 0.194154 |
| linear-warm | dev_low_oop | exact | 20261208 | 2.10717204e-08 | 0.407883 |
| linear-warm | dev_low_oop | exact | 20261209 | 2.11592038e-08 | 0.407883 |
| linear-warm | dev_low_oop | exact | 20261210 | 2.11700683e-08 | 0.407883 |
| linear-warm | dev_medium_oop | exact | 20261208 | -0.00123296298 | 0.263768 |
| linear-warm | dev_medium_oop | exact | 20261209 | -0.00120910353 | 0.271187 |
| linear-warm | dev_medium_oop | exact | 20261210 | -0.000936013782 | 0.254643 |
| representations | dev_low_oop | legacy_b8 | 20261208 | 2.11901593e-08 | 0.407883 |
| representations | dev_low_oop | legacy_b8 | 20261209 | -4.5910557e-08 | 0.256702 |
| representations | dev_low_oop | legacy_b8 | 20261210 | 2.11701304e-08 | 0.407883 |
| representations | dev_low_oop | public_b8 | 20261208 | 2.11901593e-08 | 0.407883 |
| representations | dev_low_oop | public_b8 | 20261209 | 1.92358417e-08 | 0.391029 |
| representations | dev_low_oop | public_b8 | 20261210 | 2.11701304e-08 | 0.407883 |
| representations | dev_medium_oop | legacy_b8 | 20261208 | -0.000116660051 | 0.245586 |
| representations | dev_medium_oop | legacy_b8 | 20261209 | -0.000102704457 | 0.383164 |
| representations | dev_medium_oop | legacy_b8 | 20261210 | -0.000106473369 | 0.369877 |
| representations | dev_medium_oop | public_b8 | 20261208 | -0.00123296298 | 0.263768 |
| representations | dev_medium_oop | public_b8 | 20261209 | -0.00120910353 | 0.271187 |
| representations | dev_medium_oop | public_b8 | 20261210 | -0.000936013782 | 0.254643 |
| heldout | heldout_low_oop | exact | 20261208 | 1.71236427e-08 | 0.181363 |
| heldout | heldout_low_oop | exact | 20261209 | 2.73094688e-11 | 0.431923 |
| heldout | heldout_low_oop | exact | 20261210 | 1.98130018e-08 | 0.134017 |
| heldout | heldout_low_oop | legacy_b8 | 20261208 | 1.59444386e-08 | 0.443922 |
| heldout | heldout_low_oop | legacy_b8 | 20261209 | 1.893125e-08 | 0.442718 |
| heldout | heldout_low_oop | legacy_b8 | 20261210 | 1.01281994e-08 | 0.358153 |
| heldout | heldout_low_oop | public_b8 | 20261208 | 1.71236427e-08 | 0.181363 |
| heldout | heldout_low_oop | public_b8 | 20261209 | 2.73094688e-11 | 0.431923 |
| heldout | heldout_low_oop | public_b8 | 20261210 | 1.98130018e-08 | 0.134017 |
| heldout | heldout_medium_ip | exact | 20261208 | -0.00144700961 | 0.287087 |
| heldout | heldout_medium_ip | exact | 20261209 | -0.00140306265 | 0.274007 |
| heldout | heldout_medium_ip | exact | 20261210 | -0.00153398084 | 0.227599 |
| heldout | heldout_medium_ip | legacy_b8 | 20261208 | -0.0343388006 | 0.372106 |
| heldout | heldout_medium_ip | legacy_b8 | 20261209 | -0.0306704118 | 0.465662 |
| heldout | heldout_medium_ip | legacy_b8 | 20261210 | -0.0300666735 | 0.301947 |
| heldout | heldout_medium_ip | public_b8 | 20261208 | -0.00144700961 | 0.287087 |
| heldout | heldout_medium_ip | public_b8 | 20261209 | -0.00140306265 | 0.274007 |
| heldout | heldout_medium_ip | public_b8 | 20261210 | -0.00153398084 | 0.227599 |

Replayed 378 independently checked frozen policies; maximum own replay error 0 chips.
Reference comparison hashes are linked in summary.json; reference strategies never enter training.
Public-board collision counts, actual sampled node counts and initialization work are in summary.json.

A failed learning gate blocks the preregistered global comparison. These numbers do not establish full-game strength or profitability.
