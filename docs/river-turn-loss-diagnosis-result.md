# Result: saved medium/dry turn losses

**Issue #4; November 23, 2026 (PST).** The [prospective plan](river-turn-loss-diagnosis.md)
was published before any new decision ranking or collision count. This is a
read-only diagnosis of the **known, previously evaluated** new medium/dry OOP
input from [PR #105](river-full-broader-spots-result.md). The source passed
four exact-source local lanes, hooks and [both hosted jobs](https://github.com/jimmy-sim/poker-ai/actions/runs/45228243604);
its [qualified receipt](../results/river-turn-loss/source-checks/manifest.json)
and separate [fictional proof](../results/river-turn-loss/proof/manifest.json)
were published and GitHub-byte-verified before the saved policies were read.
The single fixed diagnostic completed in **24.886 launcher seconds** under
its **900-second** cap; its [complete raw archive](../results/river-turn-loss/diagnosis/manifest.json)
contains 12 compressed policy traces (24 responding-seat best replies), the
report, events, command, runtime and launcher state. There was no new
training, reference comparison, strategy change or default promotion.

## What the fixed rule found

The final full-expectation candidate has **0.904253779 chips** of exact
exploitability (NashConv/2) on this finite game: **0.861096265 chips on the
turn** and **0.043157515 on the river**. The turn partition has **six
collided abstract groups covering 12 exact rows**; the river has **zero
collisions**. Collided turn rows account for **0.799246390 chips, or 92.8173%**
of the candidate's final turn gain. At least one is in the preregistered top
ten, so the frozen interpretation rule returns **`grouping_test_candidate`**.
The top ten turn rows account for **99.9288%** of final turn gain. This
identifies a strong prospective representation hypothesis, not a causal
improvement from changing the key. The parent fixed strength comparison
remains **negative**.

The largest row is exact information index **2445**, seat 0 holding
**Jh 9h** on **As Jc 5d 3h**. Facing a call/fold choice at a 218-chip pot,
its saved final strategy folds **98.9432%** and calls **1.0568%**. Against the
*fixed saved opposing seat* and with an optimized best-reply continuation,
the alternative-action values are **−18.0000 chips for fold** and
**−14.1208 for call**. Counterfactual reach (chance times opponent) is
**0.388999**; saved-prefix reach is **0.388892**. The additive
exploitability contribution is **0.746330159 chips**, **86.6721%** of all
turn gain. This is a local diagnostic under those opponent and continuation
assumptions, not universal advice to call with this hand.

Index **30** is seat 0 holding **Qd Qh** on the same board, at the same
call/fold pot. It shares abstract row **30** and therefore the **same saved
probabilities** as index 2445, although its alternative-action values are
**−18.0000 fold** and **−27.3510 call**. Its final additive loss is only
**0.012810608 chips**. This opposing action preference within one row
explains why the shared key is a plausible limitation. It does not prove a
finer key will train well or improve a new card/range input.

The next-largest turn row, index **1**, is **2s 3d** on the same turn board,
seat 1 with legal check, raise to 36 and raise to 182 at a 36-chip pot. It is
**not collided**. Its final saved probabilities are **0.000391, 0.331969,
0.667640**; the corresponding alternative-action values are **11.4099,
16.8710, 16.5608 chips** under the same fixed-opponent and optimized-reply
assumptions. Counterfactual and saved-prefix reach are both **0.499862**,
and additive loss is **0.052290140 chips**. This residual shows that
collisions do not explain every measured turn mistake. The five highest
river rows are noncollided, each contributing **0.000378620 chips**; all 15
fixed rows, cards, legal actions, policies, reaches and action values for
all 12 saved policies are in `diagnosis/report.json`.

## Matched checkpoints and limits

| Saved arm and seed | Work label | Actual charged nodes | Exploitability, chips | Turn, chips | River, chips |
| --- | ---: | ---: | ---: | ---: | ---: |
| B4 20261511 | 100k | 100,106 | 28.336131 | 11.249753 | 17.086378 |
| B4 20261512 | 100k | 100,072 | 32.357150 | 9.144963 | 23.212188 |
| B4 20261513 | 100k | 100,018 | 33.815834 | 11.436961 | 22.378873 |
| Full 0 | 100k | 127,818 | 35.010790 | 25.683629 | 9.327161 |
| B4 20261511 | 1m | 1,000,056 | 3.419512 | 1.994482 | 1.425030 |
| B4 20261512 | 1m | 1,000,106 | 3.958276 | 2.182157 | 1.776118 |
| B4 20261513 | 1m | 1,000,012 | 3.649439 | 1.725731 | 1.923708 |
| Full 0 | 1m | 1,022,544 | 3.481626 | 2.910586 | 0.571040 |
| B4 20261511 | 10m | 10,000,109 | 1.126339 | 1.035954 | 0.090385 |
| B4 20261512 | 10m | 10,000,051 | 0.551042 | 0.522578 | 0.028464 |
| B4 20261513 | 10m | 10,000,091 | 0.617225 | 0.510033 | 0.107193 |
| Full 0 | 10m | 10,012,410 | 0.904254 | 0.861096 | 0.043158 |

At the final work label, candidate-minus-B4 turn contributions are
**−0.174858, +0.338518, +0.351064 chips**, paired by control seed order;
the median is **+0.338518**. River differences are **−0.047227,
+0.014693, −0.064035**, median **−0.047227**. These are three dependent
contrasts sharing one deterministic candidate; they are not independent
candidate-seed uncertainty or a confidence interval. Work labels mean first
complete crossing, so actual charged nodes differ, most visibly at 100k.
All 12 policies have 100% whole coverage and 3,336 positive-reach exact rows.
The diagnosis reuses the parent saved policies, so its training runtime and
memory are those in the [parent report](river-full-broader-spots-result.md);
this read-only launcher measured wall time but did not record its own peak RSS.

The two-seat additive accounting error is at most **5.68434e−14 chips**;
the pinned native scalar discrepancy is at most **4.26326e−14 chips**,
both below **1e−9**. Snapshot hashes, source and archive pins, report scores
and zero recall violations passed. The saved B4 controls also mostly fold at
index 2445 at 10m (**98.4280–99.2294%**), yet their row gains differ
(**0.089430–0.452431 chips**) because reach and reply values differ. Thus
this trace cannot isolate representation from training trajectory or policy
reach. Three checkpoints cannot establish asymptotic convergence or rule out
all untested implementation errors. The input was evaluated before this
analysis and cannot be called unseen.

**Next decision:** a separate prospective, fixed-work representation test can
ask whether splitting the identified turn collisions reduces exploitability
on both known and structurally selected new inputs without worsening river
behavior. Its selection, control, seeds, metrics, budget and gates must be
published before new outcomes. This diagnosis alone does not authorize a
representation change or default promotion. Codex assisted; human hands-on
time and personal learning were not reported.

## Reproduce and inspect

From the project root, with the committed lockfile and the matching source
history available:

```sh
source ../poker-env.sh
UV_PYTHON=3.11.17 UV_PROJECT_ENVIRONMENT=results/runs/guarded-skip-requalification-20261118/envs/base311 \
  uv run --locked python scripts/diagnose_river_turn_loss.py diagnose \
  --output results/runs/my-unique-turn-loss-diagnosis
```

The command refuses an existing output directory and requires a clean tree,
the published prospective plan and pinned parent archives. This is a
reproduction command; it is not a request to repeat the frozen scientific
run for a different outcome. To inspect the *published* decisions without
recomputing anything:

```sh
python3 - <<'PY'
import json
from pathlib import Path
p = Path('results/river-turn-loss/diagnosis/report.json')
r = json.loads(p.read_text())
for row in r['candidate_ranked_decisions'][:3]:
    print(row['exact_info'], row['hole'], row['board'], row['legal_actions'])
    for obs in row['observations']:
        if obs['work_label'] == 10000000:
            print(obs['arm'], obs['seed'], obs['saved_probabilities'],
                  obs['counterfactual_reach'], obs['alternative_action_values_chips'])
PY
```
