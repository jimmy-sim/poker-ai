| Fixed function | Calls | Self seconds | Inclusive seconds |
| --- | ---: | ---: | ---: |
| `reduced_study_run.read_saved` | 2 | 0.000158625 | 125.551543 |
| `reduced_study_protocol.require_admission` | 2 | 0.000514667 | 107.961533 |
| `reduced_study_protocol.expected_admission` | 2 | 0.000803625 | 107.960776 |
| `frozen_batch_inputs.prerequisites` | 14 | 0.004032626 | 121.853417 |
| `averaging_history_inputs.load` | 14 | 0.193814472 | 121.683246 |
| `frozen_batch_validation.gather` | 4 | 0.001370075 | 0.001725667 |
| `frozen_batch_validation.grid` | 2 | 0.0004573 | 0.041549542 |

| Caller of prerequisites | Calls | Direct edge inclusive seconds |
| --- | ---: | ---: |
| `reduced_study_run.read_saved` | 2 | 17.3613196 |
| `frozen_batch_protocol.read_profile` | 12 | 104.492098 |

Largest absolute child/self residual: 1.42108547e-14 seconds.
