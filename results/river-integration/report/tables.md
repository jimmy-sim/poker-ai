# Fixed-work river results

Known development games. Lower exploitability is better. Ranges span three seeds, not confidence intervals.

| Spot | Work threshold | Variant | Median epsilon/pot | Min–max | Iterations | Median seconds | Initial-only rows (max) |
| --- | ---: | --- | ---: | --- | --- | ---: | ---: |
| dev_low_oop | 100,000 | external | 2.34929e-07 | 1.64588e-07–8.01291e-07 | 5,531–5,531 | 0.369 | 368 |
| dev_low_oop | 100,000 | river_integrated | 9.59357e-06 | 9.35958e-06–1.00739e-05 | 193–193 | 0.324 | 368 |
| dev_low_oop | 1,000,000 | external | 2.10243e-09 | 1.47275e-09–7.20023e-09 | 58,472–58,472 | 3.883 | 368 |
| dev_low_oop | 1,000,000 | river_integrated | 8.59109e-08 | 8.58866e-08–8.71798e-08 | 2,030–2,030 | 3.388 | 368 |
| dev_low_oop | 10,000,000 | external | 2.0796e-11 | 1.45715e-11–7.0762e-11 | 587,884–587,884 | 39.197 | 368 |
| dev_low_oop | 10,000,000 | river_integrated | 8.57631e-10 | 8.57158e-10–8.58749e-10 | 20,397–20,397 | 34.120 | 368 |
| dev_medium_oop | 100,000 | external | 0.767079 | 0.733541–0.776732 | 1,461–1,499 | 0.258 | 1119 |
| dev_medium_oop | 100,000 | river_integrated | 0.635118 | 0.604401–0.738049 | 42–47 | 0.256 | 1089 |
| dev_medium_oop | 1,000,000 | external | 0.0713837 | 0.0382278–0.0733779 | 26,971–30,267 | 3.998 | 828 |
| dev_medium_oop | 1,000,000 | river_integrated | 0.0966135 | 0.0508314–0.100869 | 711–797 | 4.032 | 481 |
| dev_medium_oop | 10,000,000 | external | 0.00246273 | 0.00185006–0.00287179 | 307,038–314,609 | 41.157 | 827 |
| dev_medium_oop | 10,000,000 | river_integrated | 0.00761239 | 0.0036789–0.00936826 | 8,207–8,964 | 39.810 | 463 |
| heldout_low_oop | 100,000 | external | 3.56157e-05 | 2.89097e-05–0.000120552 | 5,174–5,468 | 0.380 | 107 |
| heldout_low_oop | 100,000 | river_integrated | 0.00181925 | 0.000828291–0.00589302 | 172–181 | 0.338 | 9 |
| heldout_low_oop | 1,000,000 | external | 3.12883e-07 | 2.5592e-07–1.05694e-06 | 55,001–58,409 | 4.136 | 106 |
| heldout_low_oop | 1,000,000 | river_integrated | 1.52741e-05 | 6.37538e-06–5.17682e-05 | 1,817–1,919 | 3.771 | 9 |
| heldout_low_oop | 10,000,000 | external | 3.09139e-09 | 2.53668e-09–1.0439e-08 | 553,747–587,821 | 40.677 | 105 |
| heldout_low_oop | 10,000,000 | river_integrated | 1.4982e-07 | 6.09021e-08–5.19033e-07 | 18,283–19,292 | 36.392 | 9 |
| heldout_medium_ip | 100,000 | external | 0.110913 | 0.105636–0.116945 | 3,000–3,111 | 0.361 | 182 |
| heldout_medium_ip | 100,000 | river_integrated | 0.0962955 | 0.0804674–0.115125 | 87–93 | 0.349 | 81 |
| heldout_medium_ip | 1,000,000 | external | 0.0294586 | 0.0283444–0.0315056 | 35,649–37,573 | 4.376 | 167 |
| heldout_medium_ip | 1,000,000 | river_integrated | 0.0259317 | 0.021758–0.0369933 | 1,044–1,107 | 4.192 | 81 |
| heldout_medium_ip | 10,000,000 | external | 0.00943331 | 0.00806819–0.00968536 | 365,301–386,401 | 42.995 | 167 |
| heldout_medium_ip | 10,000,000 | river_integrated | 0.00710928 | 0.00640402–0.00729615 | 10,712–11,401 | 40.178 | 80 |

## Frozen-policy ratios

Integrated / ordinary: below 1 favors integration. Means pool the equal-sized seed batches before division. Zero denominators remain unavailable.

| Spot | Policy | Target | Regret MSE | Visits | Regret MSE × visits | Turn regret MSE × visits | Average MSE × visits |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| dev_low_oop | own_full_cfr_plus_256 | 0 | 0.5469 | 31.1 | 17.01 | 17.01 | 31.1 |
| dev_low_oop | own_full_cfr_plus_256 | 1 | 0.1575 | 28.21 | 4.443 | 6.089 | 14.18 |
| dev_low_oop | uniform | 0 | 0.1526 | 32.88 | 5.019 | 7.489 | 17.22 |
| dev_low_oop | uniform | 1 | 0.1539 | 30.23 | 4.653 | 6.475 | 12.24 |
| dev_medium_oop | own_full_cfr_plus_256 | 0 | 0.02464 | 35.97 | 0.8863 | 7.671 | 12.49 |
| dev_medium_oop | own_full_cfr_plus_256 | 1 | 0.3012 | 33.43 | 10.07 | 13.52 | 10.89 |
| dev_medium_oop | uniform | 0 | 0.05773 | 38.13 | 2.201 | 4.145 | 9.523 |
| dev_medium_oop | uniform | 1 | 0.05321 | 34.83 | 1.853 | 2.951 | 6.74 |
| heldout_low_oop | own_full_cfr_plus_256 | 0 | 0.6616 | 31.1 | 20.58 | 20.58 | 31.1 |
| heldout_low_oop | own_full_cfr_plus_256 | 1 | 0.2446 | 28.35 | 6.936 | 11.39 | 15.35 |
| heldout_low_oop | uniform | 0 | 0.17 | 32.88 | 5.59 | 8.523 | 17.21 |
| heldout_low_oop | uniform | 1 | 0.1951 | 30.23 | 5.899 | 8.403 | 12.24 |
| heldout_medium_ip | own_full_cfr_plus_256 | 0 | 0.02393 | 33.26 | 0.7957 | 2.231e+04 | 6.462 |
| heldout_medium_ip | own_full_cfr_plus_256 | 1 | 0.1791 | 35.96 | 6.442 | 18.57 | 12.03 |
| heldout_medium_ip | uniform | 0 | 0.06184 | 31.93 | 1.975 | 4.086 | 5.903 |
| heldout_medium_ip | uniform | 1 | 0.05481 | 35.49 | 1.945 | 3.488 | 10.59 |

Candidate development gate: **True**.
Study 972.029s; native audit 3.126s; 80 frozen policies checked.

All per-seed, per-budget rows, coverage, overshoot and costs remain in study.json and learning.csv.
