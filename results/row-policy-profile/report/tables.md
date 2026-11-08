# Policy-row paired profile

Exact valid-state parity; timing estimates only.

Parity: 96 cells / 576 checkpoints; 708 timing rows.
Median paired dense / row-cache loop time: 1.695×.

| Backend | Training forecast (s) | 2× guard (s) | Decision |
|---|---:|---:|---|
| dense | 15228.659 | 30457.318 | training_only_guarded_forecast_exceeds_cap |
| rows | 8219.338 | 16438.675 | training_only_guarded_forecast_exceeds_cap |

Full cells are shared. Setup/scoring/checkpoint/audit remain unestimated.
No learning sweep, default change or playing-strength claim.
