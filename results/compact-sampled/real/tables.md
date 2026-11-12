# Fixed-work compact sampled comparison

Known restricted games; final LINEAR averages. Lower exploitability is better.
Three fixed seeds; ranges are descriptive, not confidence intervals.

| Game | Representation | Median % pot | Worst % pot | All three seeds % pot |
|---|---|---:|---:|---|
| dev_low_oop | exact | 2.02482311e-09 | 2.07116553e-07 | 2.07116553e-07, 1.65007761e-09, 2.02482311e-09 |
| dev_low_oop | public_b8 | 1.65003594e-09 | 1.86390996e-08 | 1.86390996e-08, 1.65003594e-09, 1.64920478e-09 |
| dev_low_oop | texture_b8 | 1.65003594e-09 | 2.23571208e-08 | 2.23571208e-08, 1.65003594e-09, 1.64920478e-09 |
| dev_low_oop | texture_made_b8 | 1.65003594e-09 | 2.25363421e-08 | 2.25363421e-08, 1.65003594e-09, 1.64920478e-09 |
| dev_low_oop | texture_range_q8_b8 | 1.65003594e-09 | 2.25363421e-08 | 2.25363421e-08, 1.65003594e-09, 1.64920478e-09 |
| dev_low_oop | texture_range_q8_own_q8_b8 | 1.65003594e-09 | 2.2648928e-08 | 2.2648928e-08, 1.65003594e-09, 1.64920478e-09 |
| dev_medium_oop | exact | 0.292419682 | 0.660690263 | 0.292419682, 0.660690263, 0.194613427 |
| dev_medium_oop | public_b8 | 0.292419682 | 0.660690263 | 0.292419682, 0.660690263, 0.194613427 |
| dev_medium_oop | texture_b8 | 5.40857833 | 7.7946812 | 5.40857833, 7.7946812, 5.23811949 |
| dev_medium_oop | texture_made_b8 | 4.31913151 | 4.46315286 | 4.31913151, 4.46315286, 4.29838416 |
| dev_medium_oop | texture_range_q8_b8 | 2.7932918 | 3.3494722 | 2.7932918, 0.37528661, 3.3494722 |
| dev_medium_oop | texture_range_q8_own_q8_b8 | 2.38991201 | 2.4945677 | 2.4945677, 1.22545973, 2.38991201 |

Exact AND candidate must meet median <=1% and worst <=2.5% in BOTH games.
Other readouts cannot replace this declared primary.
All324 readouts and30 signed paired baseline effects are in the CSV files.
Negative candidate-minus-baseline favors candidate; every seed is retained.
Whole average coverage includes exact warm mass; see result.json support rows
for post-warm/all/river support. No default/fresh/global strength claim.
