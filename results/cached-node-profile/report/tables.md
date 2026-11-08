# Immutable-node paired profile

Exact interface/trajectory checks; timing estimates only.

Interface: 48604 nodes / 48600 edges.
Parity: 96 cells / 576 checkpoints.
Timing rows: 708; median paired parent / nodes: 1.356×.

| Backend | Training forecast (s) | 2× guard (s) | Decision |
|---|---:|---:|---|
| parent | 8168.894 | 16337.788 | training_only_guarded_forecast_exceeds_cap |
| nodes | 6216.028 | 12432.056 | training_only_guarded_forecast_exceeds_cap |

Fresh graph construction is charged to initialization; static-node records are separate from unchanged CFR visits.
Full cells are shared. Other pipeline costs remain unestimated; no strength/default/admission claim.
