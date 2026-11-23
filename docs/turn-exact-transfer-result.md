# Exact-turn transfer: structural stop, strength inconclusive

**Issue #4, PR #107; November 23, 2026 (PST).** The [prospective
protocol](turn-exact-transfer.md) fixed a one-time cohort and required a
stop before training if all three newly selected inputs had zero turn-key
collisions. The published [source receipt](../results/turn-exact-transfer/source-checks/manifest.json)
passed all four exact-source local lanes, all-file hooks, and both hosted
Python jobs. The single frozen [inventory](../results/turn-exact-transfer/inventory/manifest.json)
then found exactly that stop condition. **Poker-strength result:
inconclusive.** No fictional proof, profile, compute admission, training,
saved policy, independent reference audit, or default promotion followed.

## Fixed question and observation

The planned control grouped acting turn hands through the original q8
description while keeping exact river hands. The candidate used exact
acting observations on both turn and river, at identical full expected
charged training work. A *collision* here is two distinct exact acting
turn information rows mapped to one q8 strategy row. A split can matter
only where that grouping exists. The registered three new card/range
inputs were drawn on known public betting templates without looking at
tree size or collisions, then frozen at `a779abf` before this inventory.

| Frozen input | Turn board | Tree nodes | Exact / q8 information rows | Collided turn rows / groups | Collided river rows |
| --- | --- | ---: | ---: | ---: | ---: |
| Known mechanistic medium/dry OOP | As Jc 5d 3h | 21,303 | 3,336 / 3,330 | 12 / 6 | 0 |
| New medium/dry OOP | 6s Kc 2h Jd | 21,303 | 3,336 / 3,336 | 0 / 0 | 0 |
| New medium/wet OOP | Qd Ad Jh Kh | 21,303 | 3,336 / 3,336 | 0 / 0 | 0 |
| New low/wet IP | 5h 6c 7h 3d | 2,295 | 372 / 372 | 0 / 0 | 0 |

All frozen trees fit the 200,000-node maximum. The three new inputs have
zero collided turn rows in total; the known mechanistic case retains its
12 rows in six groups. The registered `structural_stop` condition therefore
ended PR #107's training comparison. No spot was replaced and the candidate
was not tuned. This observation says the proposed split has no collision
opportunity on these three exact input trees. It does not estimate collision
prevalence over poker situations, show whether the candidate improves the
known case, or establish strength on other boards/ranges.

## Reproduction and safeguards

The one inventory ran once under the 900-second cap, from clean published
source/receipt HEAD `8e2e792d60a3ca5cf8b29ac6e9eeff4789aff249`,
source fingerprint `fb9006517142ee23076f2c0b6d581475dfdaed8127cb2c146a60731af901b09c`,
Python 3.11.17, NumPy 2.4.6, Apple M4/macOS arm64, and committed `uv.lock`
SHA-256 `db5529861ae56225daaf8a18513013e52bee88ef667227855b719a7e1364250c`.
Its launcher elapsed about 7.06 seconds, exited zero, and retained the
raw started/result JSON, command, environment, PIDs and logs in the
inventory archive. The preceding one-time selector used PCG64 seed
20261520. The planned training seed PCG64(0) was never used.

From a clean checkout containing the published receipt, the read-only
structural inventory can be rerun to a **new** output directory:

```sh
source ../poker-env.sh
UV_PYTHON=3.11.17 UV_PROJECT_ENVIRONMENT=results/runs/guarded-skip-requalification-20261118/envs/base311 \
  uv run --locked python scripts/study_turn_exact_transfer.py inventory \
  --output results/runs/manual-turn-exact-inventory
```

The raw archived result is at
`results/turn-exact-transfer/inventory/result.json`. There are no trained
PR #107 river decisions to inspect because the prospective stop occurred
before learning. The earlier [known-input decision report](river-turn-loss-diagnosis-result.md)
remains diagnostic evidence, not an exact-turn strength result.

The failed source-qualification launcher and copied-guard preflight, plus
earlier source iteration failures, remain in the source receipt; neither
reached this inventory. Historical source fingerprints and the PR #105
negative strength result remain unchanged. A separate prospective question
is needed to test poker decisions after this structural non-test. One
justified next question is whether the **known** medium/dry collisions can
be relieved by exact turn keys at matched work; it would support a causal
mechanistic claim on that known finite input only, with no new-input
generalization claim or favorable cohort redraw. Its controls, compute
admission and outcome gates must be published separately before training.

Codex assisted in implementation and reporting. Human hands-on time or
personal learning was not reported.
