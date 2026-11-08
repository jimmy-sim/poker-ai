# Independent-cell process calibration

All 1260 short-workload endpoints exactly match the pinned serial profile.
CPU seconds include parent plus reaped children; elapsed seconds differ.

| Workers | Median batch wall (s) | Median serial / batch | Median CPU (s) | 2x known-cost forecast (s) | Decision |
|---|---:|---:|---:|---:|---|
| 1 | 33.163 | 1.000 | 33.175 | 12250.546 | known_cost_exceeds_cap |
| 2 | 18.691 | 1.771 | 37.213 | 6299.036 | unresolved_unmeasured_pipeline_cost |
| 3 | 13.827 | 2.400 | 40.795 | 4257.374 | unresolved_unmeasured_pipeline_cost |

Fixed partitions and max-of-three cell forecasts include measured launch/tree/export/collection overhead, then the unchanged 2x margin.
Future scoring/checkpoint/audit costs remain unmeasured. No automatic learning admission, default or playing-strength claim.
