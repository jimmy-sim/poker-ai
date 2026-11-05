# Fresh procedure validation

Each case receives its own training. Lower epsilon/pot is better.

| Case | Node threshold | Median epsilon/pot | Min–max | Iterations | Median seconds | Initial-only rows (max) | Subsequent coverage (min) |
| --- | ---: | ---: | --- | --- | ---: | ---: | ---: |
| fresh_low_dry_oop | 100,000 | 0.0003055 | 3.47823e-05–0.000763479 | 4,495–4,732 | 0.389 | 4 | 99.96% |
| fresh_low_dry_oop | 1,000,000 | 2.70197e-06 | 3.11209e-07–6.82791e-06 | 47,511–50,248 | 4.090 | 4 | 99.96% |
| fresh_low_dry_oop | 10,000,000 | 2.66788e-08 | 3.08576e-09–6.73091e-08 | 477,579–505,650 | 41.035 | 4 | 99.96% |
| fresh_medium_wet_oop | 100,000 | 0.178778 | 0.170316–0.216148 | 1,744–1,833 | 0.266 | 1819 | 93.57% |
| fresh_medium_wet_oop | 1,000,000 | 0.00944438 | 0.00426341–0.0108721 | 30,001–30,780 | 4.073 | 1545 | 94.61% |
| fresh_medium_wet_oop | 10,000,000 | 0.000489874 | 3.74902e-05–0.000597768 | 303,041–328,377 | 41.506 | 1545 | 94.67% |
| fresh_low_wet_ip | 100,000 | 0.00809943 | 0.00677474–0.00911051 | 5,171–5,246 | 0.396 | 0 | 100.00% |
| fresh_low_wet_ip | 1,000,000 | 0.000893511 | 0.000819674–0.00121441 | 56,454–56,646 | 4.120 | 0 | 100.00% |
| fresh_low_wet_ip | 10,000,000 | 7.02137e-05 | 5.87815e-05–0.000126404 | 576,600–576,913 | 40.402 | 0 | 100.00% |
| fresh_medium_dry_ip | 100,000 | 0.140414 | 0.128759–0.142614 | 2,921–2,981 | 0.363 | 39 | 99.36% |
| fresh_medium_dry_ip | 1,000,000 | 0.0358478 | 0.0340445–0.0359093 | 35,604–36,170 | 4.140 | 8 | 99.96% |
| fresh_medium_dry_ip | 10,000,000 | 0.00966995 | 0.00924263–0.0098446 | 364,078–379,964 | 41.205 | 8 | 99.96% |

## Final limits

| Case | Full epsilon/pot | Sampled median | Sampled worst | Average coverage | Passed |
| --- | ---: | ---: | ---: | ---: | --- |
| fresh_low_dry_oop | 1.52403e-08 | 2.66788e-08 | 6.73091e-08 | 100.00% | True |
| fresh_medium_wet_oop | 6.98912e-07 | 0.000489874 | 0.000597768 | 100.00% | True |
| fresh_low_wet_ip | 3.75631e-08 | 7.02137e-05 | 0.000126404 | 100.00% | True |
| fresh_medium_dry_ip | 4.16776e-05 | 0.00966995 | 0.0098446 | 100.00% | True |

Fresh procedure gate: **True**. No thresholds or cases were replaced.
Average coverage includes initialization; see initial-only rows and subsequent coverage separately.
Bands/ranges span three fixed seeds and are not confidence intervals. No global or zero-shot claim.
