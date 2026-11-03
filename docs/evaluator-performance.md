# Evaluator performance

## Baseline profile

Measured with `scripts/profile_evaluator.py` and `configs/evaluator-profile.json`
from clean source revision `c33e3f4d523292027a002b3743e18908d537dd34`.
The [raw report](../results/evaluator-baseline-profile.json) retains every timing,
input digest, source/config hash, and cProfile cumulative top-20 listing.

| Cards | Median seconds/hand |
| --- | ---: |
| 5 | 0.000011966 |
| 6 | 0.000063109 |
| 7 | 0.000229086 |

Inputs are generated before timing. Unprofiled batches are repeated, with warmup;
cProfile is a separate pass and its inflated times are not used as benchmark
medians. These are local measurements, not general hardware performance claims.

The seven-card profile reports 210,000 five-card evaluator calls for 10,000 inputs.
Repeated counting, sorting, and validation dominate that subset-based path.
The next optimization retains this reference and classifies six/seven-card inputs
directly using rank counts and suit masks. It must preserve all ranking and input
validation behavior and pass independent checks before equity work uses it.
