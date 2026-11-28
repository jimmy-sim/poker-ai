# Saved-mixture residual map: known-game diagnostic

Issue #4, [PR #119](https://github.com/jimmy-sim/poker-ai/pull/119), November 28, 2026 (PST). This is the one read-only analysis registered in the [prospective protocol](known-mixture-residual-map.md). The four policies, games, ranking rule and work caps were fixed before any mixed-policy row trace. All four games had already been inspected. The result is **informative about these saved restricted-game policies**, not a new poker-strength improvement or unseen transfer. [PR #118's negative acceptance result](known-turn-half-policy-mixture-result.md) remains negative.

## What the exact row map shows

The single own trace finished in 84.088 whole seconds under the 900-second cap, with 979,533,824-byte peak RSS below the strict 1.5-billion-byte cap. Each of the four policies yielded all 8,340 additive best-response gain rows. The fixed report ran once after a separately qualified report-source correction, in 1.100 whole seconds. Its largest turn-plus-river scalar reconciliation error is `8.33e-17` chips, below the frozen `1e-9`-chip tolerance. The [own archive](../results/known-mixture-residual-map/own/manifest.json) retains every gain vector and ranked decision; the [report archive](../results/known-mixture-residual-map/report/manifest.json) binds the fixed parent comparison and launcher. Report source `1a505951` passed full local base and optional Python 3.11/3.12, hooks and all four hosted jobs; its [separate receipt](../results/known-mixture-residual-map/report-source-checks/manifest.json) preserves both prior report-code failures.

Exploitability here is **NashConv/2 in chips** for the exact two-player restricted game: half the sum of each seat's payoff gain from a best response against the *saved opponent policy*. Turn and river contributions are additive parts of that same best-response calculation. Lower is better. Q8 and exact-turn parents come from PR #116's already published final vectors; their own opponents, reaches and best-response continuations differ from the mixture's. Parent differences below are descriptive, not the effect of swapping one local action.

| Known game | Q8 total | Exact-turn total | Mixed total | Mixed turn | Mixed river | Mixed turn share | Top 10 positive turn rows' share |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Dry A | 0.656828 | 0.488717 | 0.538034 | 0.315913 | 0.222120 | 58.7% | 94.6% |
| Wet A | 0.616505 | 0.636386 | 0.556914 | 0.316184 | 0.240730 | 56.8% | 78.9% |
| Dry B | 1.080424 | 0.743645 | **0.864300** | **0.708274** | 0.156025 | **82.0%** | 93.0% |
| Wet B | 0.644262 | 0.603068 | 0.564683 | 0.313047 | 0.251636 | 55.4% | 98.0% |

All values are chips, before rounding in this table; the 36-chip initial pot is fixed. Dry B has the largest remaining mixed-policy gain and meets the protocol's turn-dominant rule (at least 60%). The other three are split. On dry B, the mixture's turn gain is 0.210002 chips below Q8's but 0.113993 above exact-turn's; its river gain differs by only -0.006123 and +0.006661 chips respectively. The mixture therefore retains a substantial dry-B turn weakness relative to the already saved exact-turn parent. The top-ten turn rows account for 79–98% of positive turn gain across these games, while the top-ten river shares are only 3.8–8.7%. This concentrates the *diagnostic* turn gain; it does not establish that editing those ten local actions would recover the same amount.

## Representative saved decisions

The ranking is the fixed descending mixed additive gain with exact row index as tie-breaker; the report also retains PR #116's fixed control-ranked rows. For dry B's highest-ranked turn row, seat 1 holds `7h Kc` on `5c 8s Jh 9c`, facing `fold`, `call`, `raise_to 144`, `raise_to 182`. The mixed probabilities are `[0.515153, 0.235005, 0.098919, 0.150923]`; Q8's are `[0.508571, 0.238417, 0.104006, 0.149005]` and exact-turn's `[0.521734, 0.231594, 0.093831, 0.152841]`. The mixed chance-times-opponent counterfactual reach and saved-prefix reach are both 0.269486. Against that saved mixed opponent and its optimized best-response continuation, alternative-action values are `[-18.000000, -16.575338, -18.182742, -18.469191]` chips and the row adds 0.158828 chips to the aggregate gain. These values depend on the restricted range, action menu and continuation; they are **not universal advice** to call with these cards.

For dry B's highest-ranked river row, seat 1 holds `5d Kh` on `5c 8s Jh 9c Tc`, with `check`, `raise_to 108`, `raise_to 146`. The mixed probabilities are `[0.071110, 0.026303, 0.902586]`; Q8's are `[0.059802, 0.019494, 0.920704]` and exact-turn's `[0.082418, 0.033113, 0.884469]`. Mixed counterfactual reach is 0.002041, saved-prefix reach 0.002025, optimized-continuation alternative values are `[-2.609046, 0.670633, 5.504121]` chips, and the additive row gain is 0.000713 chips. The much smaller row reach helps explain why this particular river decision contributes less than the selected turn decision. The values do not isolate a causal local swap.

To inspect every fixed selected decision in dry B, from the repository root:

```sh
python3 -c 'import json; from pathlib import Path; p=Path("results/known-mixture-residual-map/report/report.json"); c=next(x for x in json.loads(p.read_text())["cases"] if x["game"]=="collision_medium_dry_oop_b"); [print(x["street"],x["seat"],x["hole"],x["board"],x["legal_actions"],x["mixed_probabilities"],x["mixed_counterfactual_reach"],x["mixed_alternative_action_values_chips"],x["mixed_additive_gain_chips"]) for x in c["selected_decisions"]]'
```

## Conclusion and limits

This diagnostic is **informative**, with no new acceptance of the mixture. It identifies dry B's turn as the largest residual and shows many high-reach turn rows where both saved parents already assign similar probabilities. That pattern makes simple 50:50 policy blending an unlikely complete remedy on these known games; it does **not** prove whether the cause is earlier information grouping, training dynamics, or a specific action abstraction. The four games share a template and are statistically dependent. The trainer is deterministic, so there is no seed replication or confidence interval. The former PR #117 parent-row source gate failed without a row outcome; it is not reinterpreted here. No new OpenSpiel output was calculated: PR #118's pinned OpenSpiel 2.0.2 Apache-2.0 scalar audit remains comparison-only, and no reference strategy entered training.

The next justified question is whether a prospectively fixed turn-information or learning change can lower dry B's broad turn best-response gain **at matched work** without regressing the other declared games. It needs a separate protocol, independent qualification and fresh evaluation inputs before any new outcomes; this report does not choose an action edit, board, seed or mixture weight from the ranked rows.

## Review questions

1. **Why does a high turn-row gain not identify a safe action patch?** The gain is computed against the saved mixed opponent with an optimized best-reply continuation and its own reach. Changing one action changes the two-player policy and may change the opponent's best reply, so the row number is diagnostic rather than a causal estimate.
2. **Did 50:50 mixing solve the dry-B turn weakness?** No. It lowered dry-B turn best-response gain from the Q8 parent's 0.918277 chips to 0.708274, but the exact-turn parent was lower still at 0.594281. The mixture also failed PR #118's unchanged absolute strength gate on every game.
3. **What did the independent reference establish here?** PR #118's pinned OpenSpiel 2.0.2 audit checked the four saved mixture scalars before this diagnostic. This report reused those published scalars and computed no new reference output; the reference supplied neither training policy nor row choices.
