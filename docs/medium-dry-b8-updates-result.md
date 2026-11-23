# B8 signed updates on two known river spots: negative

**Issue #4, November 23, 2026 (PST).** This is the one result under the
[published prospective protocol](medium-dry-b8-updates.md) and
[machine contract](../configs/medium-dry-b8-updates.json). Both river spots,
their cards and ranges, and the three seed labels were already known. This is
not a held-out or unseen-game result. No default agent changed.

## Decision

The candidate averaged eight IID samples per signed-regret update (B8) against
the immutable published four-sample control (B4), at the same charged node
work. The final **linear-average** B8 policy on medium/dry has median
exploitability **0.036102** and worst **0.042155** initial pots. Both miss the
unchanged absolute gates of **0.01** median and **0.025** worst. Its three
paired B8-minus-B4 seed differences are **+0.000447, −0.004799, +0.007022**
initial pots (median **+0.000447**). One seed improved and two worsened.
The prospectively fixed classification is therefore **negative** because the
medium/dry absolute gate fails; the paired median alone does not reach the
separate +0.001 regression threshold.

Low/wet B8 passes its absolute gates (median **0.001053**, worst **0.001083**),
with paired median **+0.000107** within the +0.001 nondegradation allowance.
Both arms have 1.0 whole positive-average uniform-reach coverage and zero
recall violations on both known spots. The B4 medium/dry control also fails
its absolute gate (median 0.035656, worst 0.039542). These are restricted-game
NashConv/2 exploitabilities divided by the initial pot, not win rates or
full-game exploitability. Lower is better. The initial pots are 324 chips
(low/wet) and 36 chips (medium/dry).

## Fixed work comparisons

Every row below is one predeclared spot, seed and first complete target-pair
work crossing. Entries are exploitability fractions of the initial pot;
`Δ = B8 − B4`. Shared seed labels pair the paths, but different batch sizes
consume different random draws. All three seeds are shown at every checkpoint.
The complete [report JSON](../results/medium-dry-b8-updates/report/report.json)
also retains current and uniform-average readouts.

| Known spot | Charged work label | Seed | B4 | B8 | Δ |
| --- | ---: | ---: | ---: | ---: | ---: |
| low/wet | 100,000 | 20261371 | 0.013594 | 0.010205 | −0.003389 |
| low/wet | 100,000 | 20261372 | 0.011311 | 0.012255 | +0.000944 |
| low/wet | 100,000 | 20261373 | 0.011568 | 0.010715 | −0.000853 |
| low/wet | 1,000,000 | 20261371 | 0.003170 | 0.003275 | +0.000104 |
| low/wet | 1,000,000 | 20261372 | 0.003218 | 0.003293 | +0.000075 |
| low/wet | 1,000,000 | 20261373 | 0.003523 | 0.003204 | −0.000319 |
| low/wet | 10,000,000 | 20261371 | 0.000946 | 0.001053 | +0.000107 |
| low/wet | 10,000,000 | 20261372 | 0.000909 | 0.001038 | +0.000129 |
| low/wet | 10,000,000 | 20261373 | 0.001146 | 0.001083 | −0.000063 |
| medium/dry | 100,000 | 20261371 | 0.895404 | 0.973034 | +0.077630 |
| medium/dry | 100,000 | 20261372 | 0.938752 | 0.910948 | −0.027805 |
| medium/dry | 100,000 | 20261373 | 0.956300 | 0.894305 | −0.061995 |
| medium/dry | 1,000,000 | 20261371 | 0.138278 | 0.145856 | +0.007578 |
| medium/dry | 1,000,000 | 20261372 | 0.123157 | 0.135891 | +0.012734 |
| medium/dry | 1,000,000 | 20261373 | 0.142300 | 0.144228 | +0.001928 |
| medium/dry | 10,000,000 | 20261371 | 0.035656 | 0.036102 | +0.000447 |
| medium/dry | 10,000,000 | 20261372 | 0.039542 | 0.034743 | −0.004799 |
| medium/dry | 10,000,000 | 20261373 | 0.035132 | 0.042155 | +0.007022 |

The three paired observations are descriptive, not a confidence interval or
population claim. Seeds share the same two game trees and evaluator, so their
errors and game-specific biases can be dependent. Neither the candidate nor
any threshold was adjusted after seeing them.

## Where the medium/dry best replies gain

The fixed saved-opponent best-reply decomposition adds to exact restricted-game
exploitability. The entries below are **chips** of NashConv/2, summed over both
seats; the medium/dry initial pot is 36 chips. Each row uses the final linear
average at that work label. The full report retains each selected turn and
river row for every arm, seed and checkpoint.

| Work | Seed | B4 turn | B4 river | B8 turn | B8 river |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 100,000 | 20261371 | 11.1614 | 21.0732 | 13.3404 | 21.6888 |
| 100,000 | 20261372 | 9.6176 | 24.1775 | 12.0406 | 20.7536 |
| 100,000 | 20261373 | 12.5536 | 21.8732 | 11.3640 | 20.8310 |
| 1,000,000 | 20261371 | 1.2338 | 3.7443 | 1.5267 | 3.7241 |
| 1,000,000 | 20261372 | 0.8317 | 3.6020 | 1.2185 | 3.6736 |
| 1,000,000 | 20261373 | 1.0527 | 4.0701 | 1.5098 | 3.6824 |
| 10,000,000 | 20261371 | 0.2647 | 1.0189 | 0.3800 | 0.9197 |
| 10,000,000 | 20261372 | 0.3958 | 1.0277 | 0.3040 | 0.9468 |
| 10,000,000 | 20261373 | 0.3123 | 0.9525 | 0.4521 | 1.0655 |

At B8's final checkpoint, river accounts for 70.2–75.7% of remaining
medium/dry exploitability. The three turn rows fixed from the earlier diagnosis
(14, 1596, 2443) account for 93.5–97.6% of the **turn** contribution across
the three B8 seeds. The two fixed river rows (640, 1806) account for only
0.6–1.5% of the **river** contribution: the river weakness remains dispersed.
This decomposition describes a fixed saved profile against each seat's best
reply; it does not show that changing one row would produce that global gain.

For a concrete river example, final B8 seed 20261371 at exact row **1806**
has hole `8c 9h` on `2s 6h Jc 3c 5h`, pot 108 chips, and legal actions
`check`, `raise_to 108`, `raise_to 146`. Saved probabilities are
`[0.5002, 0.0641, 0.4357]`. Against **this saved opponent policy** with the
acting seat's **optimal reply continuation**, the conditional action values
are `[-54.000, -66.570, -45.517]` acting-seat chips. Counterfactual reach is
0.007852; saved full-prefix reach is 0.003800; its additive NashConv/2 loss
is 0.010624 chips. At exact row **640**, hole `2c 8d` on
`2s 6h Jc 3c 7h`, pot 254, the actions `fold` and `call` have probabilities
`[0.5704, 0.4296]` and conditional values `[-54.000, -58.602]` chips under
the same assumptions; counterfactual/saved reaches are 0.003331/0.002500,
with 0.002472 chips additive loss. These one-action values are local
diagnostics, not universal poker advice. B4 has a different saved opponent
policy, so its local action values cannot be compared as if the opponent were
held constant across arms.

## Coverage, memory and time

At 10m work, every row has whole positive-average uniform-reach coverage
**1.0000** and **zero** structural recall violations. The table shows the
separate post-initial river coverage and initial-only river rows, which are
diagnostic rather than the registered 0.95 whole-coverage gate. RSS is peak
worker resident memory in MiB; seconds are complete construction-to-replay
path times. Each arm keeps 372 information rows and 523,776 four-table bytes
on low/wet, or 3,336 rows and 4,697,088 bytes on medium/dry.

| Spot | Seed | Arm | Post-initial river coverage | Initial-only river rows | Peak MiB | Path seconds |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| low/wet | 20261371 | B4 | 0.9984 | 4 | 60.0 | 66.01 |
| low/wet | 20261371 | B8 | 0.9984 | 4 | 63.8 | 63.36 |
| low/wet | 20261372 | B4 | 0.9981 | 4 | 60.1 | 66.26 |
| low/wet | 20261372 | B8 | 0.9967 | 4 | 63.8 | 63.35 |
| low/wet | 20261373 | B4 | 1.0000 | 0 | 62.8 | 66.14 |
| low/wet | 20261373 | B8 | 0.9991 | 3 | 63.7 | 63.43 |
| medium/dry | 20261371 | B4 | 0.9555 | 484 | 187.7 | 76.76 |
| medium/dry | 20261371 | B8 | 0.9497 | 476 | 188.0 | 72.84 |
| medium/dry | 20261372 | B4 | 0.9341 | 590 | 189.6 | 76.39 |
| medium/dry | 20261372 | B8 | 0.9482 | 479 | 189.2 | 73.49 |
| medium/dry | 20261373 | B4 | 0.9475 | 494 | 227.0 | 76.63 |
| medium/dry | 20261373 | B8 | 0.9426 | 444 | 193.5 | 73.31 |

The B8 six-path parent study ran 136.942 seconds; its outer guarded driver
ran 137.430 seconds with a 7,080-second learning cutoff and 120-second save
reserve inside the 7,200-second cap. Control path times are from its earlier
published own study on the same Apple M4. These wall times are observations,
not a speed guarantee. The B8 fixed 18-path profile completed in 19.408
seconds (<900), giving conservative `T=657.976753` and strict whole-study
bound `3,831.907011<7,200`; a **separate** published admission reproduced
the bound before training. Peak observed B8 study worker RSS was 202,883,072
bytes. Actual final work and overshoot for every path are in report JSON.

## Provenance, checks and limits

The B4 control own and native manifests are pinned in the protocol; neither
was retrained. The B8 source at `81ef11a` has fingerprint
`666ac9e4322ca84f93ad43acf972e8a758125f1aa1276da2847a6025049b40ad`.
Checkpoint commits, in order, are protocol `24103f9`, source `81ef11a`,
[source receipt](../results/medium-dry-b8-updates/source-checks/manifest.json)
`2ba208e`, [fictional proof](../results/medium-dry-b8-updates/own-proof/manifest.json)
`2005302`, [fixed profile](../results/medium-dry-b8-updates/profile/manifest.json)
`026d89e`, [admission](../results/medium-dry-b8-updates/admission/manifest.json)
`a4aad88`, [own policies](../results/medium-dry-b8-updates/own/manifest.json)
`05db73c`, and [native audit](../results/medium-dry-b8-updates/native/manifest.json)
`738104b`. Raw ignored job directories under `results/runs/medium-dry-b8-*`
retain launch state and logs; reviewed small evidence is in `results/`.
The locked `uv.lock` SHA-256 is
`db5529861ae56225daaf8a18513013e52bee88ef667227855b719a7e1364250c`.
Own snapshots and scores were published and GitHub-byte-verified **before**
the OpenSpiel 2.0.2 Apache-2.0 comparison-only audit. All 54 B8 native scalar
comparisons passed the 1e-9 chip tolerance (maximum `6.395e-14`); the
combined B4/B8 maximum in the report is `7.105e-14` chips. No reference
strategy entered training.

At the tested source, base Python 3.11/3.12 each passed 5,755 tests with 73
skips and 150 slow deselections, Ruff, formatting, strict mypy and exact
pre/post guards. Optional 3.11 passed 2,597 tests; optional 3.12 passed 2,595
with two skips, with pinned runtime/license checks. The new B8 focused tests
passed eight each under both optional runtimes, all-file hooks passed, and
[source-head CI](https://github.com/jimmy-sim/poker-ai/actions/runs/45135404030)
passed both Python jobs. The first commit-hook PATH failure and a later
shell-wrapper failure after passing hooks remain in the source archive.
**Final report-head local, optional, hook and hosted checks remain pending**
at this report publication checkpoint.

The experiment isolates only batch size on two known restricted games. It
cannot establish full-game quality, unseen-spot generalization, or a general
statistical benefit of B8. The medium/dry failure is a scientific negative
under frozen gates; no budget extension, new seed, B16 follow-on, candidate
tuning or default promotion follows from this experiment.

To inspect the same saved river decision at every checkpoint and seed from
the repository root:

```sh
python3 -c 'import json; r=json.load(open("results/medium-dry-b8-updates/report/report.json")); [(print(x["seed"], x["work_label"], x["arm"], x["fixed_river_rows"]["1806"])) for x in r["cases"] if x["game"]=="new_medium_dry_oop" and x["arm"]=="signed_b8" and x["readout"]=="linear_average"]'
```

The [fixed report command](../scripts/study_medium_dry_b8.py) rebuilds
`report.json` from committed own and native archives in a clean normal clone.
