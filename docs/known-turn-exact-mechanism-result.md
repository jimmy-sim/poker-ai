# Exact-turn representation on one known medium/dry river game

**Prospective protocol:** [known-turn exact mechanism](known-turn-exact-mechanism.md). **Complete machine report:** [12 policies and fixed decision rows](../results/known-turn-exact-mechanism/report/report.json). This is one previously evaluated As Jc 5d 3h board/range game, not an unseen test. The work-matched q8-turn/exact-river control and exact-turn/exact-river candidate each used PCG64 seed 0 from uniform initialization. Initial pot is 36 chips; exploitability is exact NashConv/2, where smaller is better.

| Charged work checkpoint | Control, initial pots | Candidate, initial pots | Candidate minus control |
| ---: | ---: | ---: | ---: |
| 100,000 | 0.972522 | 0.969442 | −0.003080 |
| 1,000,000 | 0.096712 | 0.070316 | −0.026396 |
| 10,000,000 | 0.025118 | 0.006423 | −0.018695 |

Both actually reached 10,012,410 charged work. Final candidate exploitability is 0.231219 chips; control is 0.904254 chips. The candidate passes the frozen 0.01-pot final and 0.025-pot worst gates, 0.95 whole-coverage gate (actual 1.000), and zero recall violations. Its matched-work difference also clears the frozen −0.001-pot improvement threshold. **Classification: positive on this known game under the registered rule.** The control fails its own absolute 0.01-pot gate; this is reported, not changed. One deterministic path per arm gives no seed-based uncertainty estimate or claim of generalization. No default is promoted.

The control's final additive best-response gains are 0.861096 chips on turn and 0.043158 on river; the candidate's are 0.151366 and 0.079854. Thus the measured benefit is primarily turn-side, while the river contribution is higher for the candidate. These sums use the fixed saved policy and an optimized best reply; a local alternative-action value assumes that opponent and continuation, and is not universal poker advice. The report retains all fixed infos 2445, 30 and 1 and the control-ranked top three turn and river rows, with cards, board, legal actions, saved probabilities, reach, local action values and additive contributions at all three work checkpoints. In particular, turn info 2445 is Jh 9h on As Jc 5d 3h facing fold/call, the largest control turn contribution at 0.746330 chips. Read the full row before interpreting any action.

The one comparison-only pinned OpenSpiel 2.0.2 audit checked all 12 saved policy scalars after own publication. Maximum error was 4.263256414560601e−14 chips, below 1e−9; the installed Apache-2.0 license hash and every row are in the [native archive](../results/known-turn-exact-mechanism/native/manifest.json). Reference strategies never entered training. The 10m pair took 14.516 launcher seconds under the 7,200-second cap; control/candidate peak worker RSS was 173,735,936/156,663,808 bytes. Final post-initial-river coverage was 0.994179/0.969010. Full raw policies, scores and timings are in the [own archive](../results/known-turn-exact-mechanism/own/manifest.json).

Inspect a representative saved decision in Terminal from the repository root:

```sh
python3 - <<'PY'
import json
report = json.load(open('results/known-turn-exact-mechanism/report/report.json'))
for row in report['diagnostics']:
    if row['exact_info'] == 2445:
        print(json.dumps(row, indent=2))
PY
```

The only supported next inference is that resolving these known turn collisions helped this finite game at the fixed budget. Whether it helps new boards and ranges remains unresolved; previously inspected inputs remain known cases. No new experiment or policy tuning was part of this result.
