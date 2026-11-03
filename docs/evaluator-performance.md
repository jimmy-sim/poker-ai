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


## Direct classifier

The subset baseline is preserved as `evaluate_best_reference`. Public
`evaluate_best` delegates five-card inputs to the unchanged validated classifier;
six/seven-card inputs are classified directly from rank counts and per-suit rank
masks. Straight detection intersects shifted rank masks, with an explicit wheel
check. Quads, two trips, three pairs, long flushes, and kicker removal follow the
same comparison-key rules. No external table, native extension, or Numba is used.

`configs/evaluator-comparison.json` compares both implementations on identical
pre-generated hands. Six repeats rotate implementation order, balancing which
runs first. All outputs are checked before timing. Speed ratios will be reported
only after measurement, alongside all raw timings and validation evidence.

Local checks pass on Python 3.11 and 3.12, including 274 tests and strict typing.
The direct classifier must also pass the declared two-million-hand Treys stream
before equity calculations use it. Profile/validation timings describe different
workloads and must not be mixed into a speedup claim.
