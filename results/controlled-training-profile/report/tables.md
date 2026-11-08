# Controlled-training cost forecast

Timing extrapolation only; no strength comparison.

Decision: `training_only_guarded_forecast_exceeds_cap`.
Training only: 15235.392s; with 2× guard: 30470.783s; cap: 7200s.

Setup, scoring, checkpoint and audit costs are unestimated; this is not a bound.

| Game | Groups | Traversal | Bridge | Cells | Forecast seconds |
|---|---|---|---|---:|---:|
| dev_low_oop | exact | external | common | 24 | 2924.241 |
| dev_low_oop | exact | full | cold_target_history_mass | 1 | 6.446 |
| dev_low_oop | exact | full | common | 8 | 50.598 |
| dev_low_oop | exact | full | warm_target_chance_mass | 1 | 6.541 |
| dev_low_oop | exact | full | warm_target_history_mass | 1 | 6.495 |
| dev_low_oop | texture_range_q8_b8 | external | common | 24 | 2161.519 |
| dev_low_oop | texture_range_q8_b8 | full | cold_target_history_mass | 1 | 4.000 |
| dev_low_oop | texture_range_q8_b8 | full | common | 8 | 31.846 |
| dev_low_oop | texture_range_q8_b8 | full | warm_target_chance_mass | 1 | 4.041 |
| dev_low_oop | texture_range_q8_b8 | full | warm_target_history_mass | 1 | 4.013 |
| dev_medium_oop | exact | external | common | 24 | 6048.546 |
| dev_medium_oop | exact | full | cold_target_history_mass | 1 | 7.283 |
| dev_medium_oop | exact | full | common | 8 | 56.096 |
| dev_medium_oop | exact | full | warm_target_chance_mass | 1 | 7.263 |
| dev_medium_oop | exact | full | warm_target_history_mass | 1 | 7.205 |
| dev_medium_oop | texture_range_q8_b8 | external | common | 24 | 3856.615 |
| dev_medium_oop | texture_range_q8_b8 | full | cold_target_history_mass | 1 | 4.787 |
| dev_medium_oop | texture_range_q8_b8 | full | common | 8 | 38.184 |
| dev_medium_oop | texture_range_q8_b8 | full | warm_target_chance_mass | 1 | 4.840 |
| dev_medium_oop | texture_range_q8_b8 | full | warm_target_history_mass | 1 | 4.833 |
