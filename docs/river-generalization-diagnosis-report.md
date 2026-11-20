# Medium/dry saved-policy weakness diagnosis — November 19, 2026 (PST)

This is the one read-only diagnosis preregistered in the
[diagnostic plan](river-generalization-diagnosis.md) for issue #4 and draft
[PR #98](https://github.com/jimmy-sim/poker-ai/pull/98). The pinned source is
`f2533eab52b6910313e23ab69430865fb2fc90f3`; the whole process took
7.170 seconds against a 900-second cap. All 12 declared saved policies and
24 responding-seat traces completed. The [machine report and 12 compressed
raw traces](../results/river-generalization/diagnosis/manifest.json) bind
the plan, source, policy receipts, prior scores and independent scalar audit.
No policy was retrained, changed or selected after the fact.

**The parent comparison remains negative.** On medium/dry, final candidate
linear-average exploitability was 3.566%, 3.954% and 3.513% of the initial
pot for seeds 20261371–73. Its fixed 1% median and 2.5% worst acceptance
limits both failed. The previous final local base qualification also remains
incomplete because of retained spawned-fixture timeouts. This diagnostic
does not repair those checks. PR #98 stays draft; no merge or default
promotion is warranted.

## What the loss numbers mean

For each saved policy, seat 0 or seat 1 makes an **exact-information best
reply** against the other seat's fixed saved policy. An information row
combines hidden histories the acting seat cannot distinguish. At that row,
the action values below are in the acting seat's chips, using its own
optimized reply on later decisions and the fixed opponent throughout.
The listed *counterfactual reach* is chance times opponent reach before
maximizing; *saved-prefix reach* additionally includes the acting seat's
saved earlier actions. The row's additive exploitability contribution uses
the latter reach and divides the unilateral reply gain by two, matching the
published NashConv/2 convention. Contributions across exact rows and both
seats sum to each saved exploitability. A separate saved-continuation value
answers a local one-action question and is **not additive exploitability**.
These conditional restricted-game values are not universal poker advice or
an estimate of the effect of changing a representation or training rule.

## Largest measured weaknesses

The fixed ranking averages each exact row's additive contribution over all
three final candidate linear-average seeds. The board starts
`2s 6h Jc 3c`; the fifth card appears for river rows. The ten rows below
sum to 0.378049 chips, or 28.55% of the 1.323959-chip final candidate mean.

| Rank | Exact row | Acting seat and cards | Street / river card | Mean contribution (chips) |
| ---: | ---: | --- | --- | ---: |
| 1 | 2443 | 0, `3s 7h` | Turn | 0.119344 |
| 2 | 1596 | 1, `8c 9h` | Turn | 0.092138 |
| 3 | 14 | 0, `2c 8d` | Turn | 0.090236 |
| 4 | 1806 | 1, `8c 9h` | River `5h` | 0.012641 |
| 5 | 640 | 0, `2c 8d` | River `7h` | 0.011841 |
| 6 | 1 | 1, `6c Kc` | Turn | 0.011094 |
| 7 | 2166 | 1, `8c 9h` | River `Jh` | 0.010556 |
| 8 | 424 | 0, `2c 8d` | River `5h` | 0.010321 |
| 9 | 1468 | 0, `2c 8d` | River `Ac` | 0.010004 |
| 10 | 1036 | 0, `2c 8d` | River `Th` | 0.009874 |

The top three turn rows contribute 0.301718 chips, 22.79% of all remaining
mean exploitability and 93.05% of turn contribution. Yet **river decisions
as a street contribute more in total**: 0.999712 of 1.323959 chips (75.51%)
versus 0.324247 (24.49%) on the turn. River weakness is spread across many
smaller rows; the seven river rows in the top ten sum to 0.076331 chips.
All six final seed/seat traces had zero unsupported saved-prefix rows. The
[raw report](../results/river-generalization/diagnosis/report.json) retains
each seed/seat's fixed top five indices and every top-ten row's three-seed
values and checkpoint trajectory.

Representative **seed 20261371** rows show the actual scale and assumptions:

| Exact row; seat, cards, board, pot | Legal actions; saved probabilities in order | Counterfactual / saved-prefix reach | Best-reply-suffix action values (acting-seat chips) | Additive contribution (chips) |
| --- | --- | ---: | --- | ---: |
| 2443; 0, `3s 7h`, `2s 6h Jc 3c`, 72 | fold/call/raise to 144/raise to 182; `.651971/.348022/.00000550/.00000125` | `.381703/.381513` | `-18.000/-17.270/-54.325/-55.145` | `.090857` |
| 1596; 1, `8c 9h`, `2s 6h Jc 3c`, 36 | check/raise to 36/raise to 182; `.522950/.475695/.001355` | `.666286/.666286` | `-14.503/-14.098/-19.933` | `.073230` |
| 14; 0, `2c 8d`, `2s 6h Jc 3c`, 72 | fold/call/raise to 144/raise to 182; `.214446/.785547/.00000723/.00000069` | `.254469/.254295` | `-18.000/-15.003/-54.325/-55.145` | `.081750` |
| 1806; 1, `8c 9h`, `2s 6h Jc 3c 5h`, 108 | check/raise to 108/raise to 146; `.348440/.043740/.607820` | `.007919/.003767` | `-54.000/-50.784/-67.981` | `.021797` |
| 640; 0, `2c 8d`, `2s 6h Jc 3c 7h`, 254 | fold/call; `.557482/.442518` | `.003167/.002486` | `-54.000/-80.212` | `.014417` |

The row 2443 saved-continuation call value is `-18.909`, below folding at
`-18.000`, while its best-reply-suffix call value is `-17.270`, above folding.
Row 1596 similarly prefers check under saved continuation (`-15.117` versus
`-15.546` for the 36 raise), but the reply-continuation values favor the
36 raise. Thus a local one-action score would misdescribe these larger
**continuation-dependent** losses. On river row 1806, the best option differs
among seeds; the table is one saved policy, not a universal action rule.

## Cause tests and limits

| Explanation | Saved-evidence test | Conclusion for this finite spot |
| --- | --- | --- |
| Earlier-street information grouping | Candidate has 3,336 abstract rows for 3,336 exact rows; no turn exact row shares an abstract row. | No grouping collision is present here, so it cannot account for these measured losses. |
| Remaining river collisions | Zero collided river exact rows and zero collided river abstract groups. | No river collision is present here. The label “exact river” does not imply a collision on this spot. |
| Training/convergence differences | Candidate mean exploitability falls from 33.4855 chips at 100k work to 4.8448 at 1m and 1.3240 at 10m; the final control is 4.4636. Existing final candidate current/uniform/linear readouts average 19.0372/1.1761/1.3240 chips. | Continued improvement and divergent readouts are consistent with unfinished or oscillatory convergence. Three saved checkpoints do not establish an asymptotic rate, explain every river error, or prove more work reaches the failed gate. |
| Implementation defect | All 12 snapshot hashes and metadata match, both-seat contributions reconcile to saved exploitability within `1.16e-14` chips, native scalar discrepancies are at most `1.43e-14` (<`1e-9`), recall is zero, and parent/source/plan pins verify. | No defect in these checked bindings or value identities was detected. Unchecked defects remain possible; the earlier final local timeouts are unresolved. |

The control has larger final turn and river mean contributions (1.408207
and 3.055376 chips) than the candidate (0.324247 and 0.999712). This is a
matched-work description, not a causal decomposition of the representation
change. The finite spot has only two weighted private holdings per seat,
one fixed turn board and a restricted action menu. Findings cannot be
generalized to unseen games or unrestricted poker. There is no evidence in
this run that another representation change should be tuned to these rows.

**Recommended next bounded experiment, subject to a separate prospective
protocol and user authorization:** test whether the *unchanged exact
representation* continues to reduce the same medium/dry loss with a fixed
longer-work training cap and prespecified seeds, intermediate checkpoints,
stop rule, resource forecast and absolute acceptance criteria. Retain the
current 10m policies as comparison-only evidence. A plateau would require a
different hypothesis; the present snapshots cannot distinguish a convergence
plateau from later improvement. No such experiment was started here.

From the repository root, inspect the highest ranked saved decision with:

```sh
python3 scripts/inspect_river_generalization_diagnosis.py --rank 1
```

Use `--rank 4` for a river example; ranks 1–10 are available. The command
prints all three seeds' probabilities, reaches and both action-value types.
Codex assisted; human hands-on time was not recorded.
