# Best responses to the failed category candidate

## Definition of done, fixed before diagnosis

Continue issue #4 using the same two known development games and the four saved
4,096-iteration full-control strategies from PR #14. Publish this config/method
before measurement. Implement and test own information-set-constrained response
policies, exact versus same-partition comparisons and additive loss accounting.
Retain all eight cases, independent native root checks, concrete observable
examples, tables/figures and journal step 18. Stop before another feature or any
training, sampled comparison, fresh cases or global/default change.

This is post-hoc diagnosis of known failures. There is no new strength acceptance
gate and no tuning of the previous failed limits. There are no random draws:
inputs are fixed saved own policies, with exact deterministic traversal.

## Two responses to each fixed strategy

For each player independently, keep the saved opponent fixed. Compute one best
response using exact observable cards and one limited to that representation's
information partition. Choose one action per information set after summing
chance times opponent reach across all hidden histories. Future responder
choices are optimized recursively. Ties choose the first legal maximizing action.
Never choose separately after seeing the opponent's actual hidden cards.

Let `v_i` be the saved profile payoff, `B_i` exact-response payoff, and `C_i`
the same-partition response payoff, all net chips for player i. Report:

- Full unilateral gain `B_i - v_i`.
- Gain still possible within the partition `C_i - v_i`.
- Extra response value from exact information `B_i - C_i`.

The last two sum to the first. Their half-sums across players decompose the
project's exact exploitability (NashConv/2). Perfect recall and equal-depth infos
are required and checked in both trees. Expanding a restricted reply back to
exact infos must reproduce its value. The exact/public controls remain visible.
This separates fixed-opponent response opportunities, not the causal effect of
retraining with a feature. Best-response ties/policy choice can affect attribution. A response labeled
seat i exploits the fixed strategy of seat 1-i. Its decision-loss rows belong
to the responding player; they are not a causal list of the defender's mistakes.

## Additive decision loss

For a saved profile p and an exact best reply b by player i, evaluate continuation
values `W(h)` under `(b_i, p_-i)` in player i's chips. At each i-decision history,
weight `W(h) - sum_a p(a|I(h)) W(ha)` by that history's full **saved-profile**
reach (chance times both players' saved reaches). Sum histories into exact infos
before interpreting them. Then sum all infos for i:

`sum_I loss_i(I) = B_i - v_i`.

This telescopes: at other/chance histories W already follows the saved edges;
terminal payoff terms cancel, leaving the root value difference. Perfect recall
makes own saved reach identical inside each exact info; best-response optimality
then makes its aggregate loss nonnegative up to the fixed numerical tolerance.
Individual hidden-history terms need not be nonnegative. Zero baseline reach
contributes zero, even if the counterfactual response is defined there.

These are additive losses of the fixed strategy under this continuation
convention, unlike the preceding local collision proxy. They are still **not**
a causal decomposition of abstraction error. Group exact losses by the deployed
abstract row and by street/player. Rank all groups by summed chips, keep the top
eight and up to four deterministic examples with positive saved reach
(distinct best actions first). Unsupported rows remain in the full sidecar;
their arbitrary legal response and zero Q placeholders are not action advice.
Examples show own cards, observed board, saved probabilities, response actions,
conditional response-continuation values and support/reach. No hidden world is
used as a decision rule. Full exact-info contributions and own replies are
retained in a hash-bound compressed sidecar, including zero rows.

## Checks and independent comparison

Test hidden-history aggregation (including a clairvoyance counterexample),
player signs, zero support/reach, first-legal ties, sequential accounting, random
Kuhn/Leduc policies, equilibrium self-zero, restricted expansion and mutation
rejection. Test loss sums against root gains and halves against exploitability.
Code/config and checks must be published before retained-case measurement.

OpenSpiel 2.0.2, Apache-2.0, is the already selected reference; its
[license and comparison-only role](solver_validation.md) remain in force. A
separate validation module exports exact and abstract information partitions,
checks native response roots and evaluates only the own reply profiles. It never
exports native actions into this diagnosis or any learner. Both evaluators share
own exported mechanics/partition definitions, so this is not independent
full-engine/feature validation. Require root/accounting agreement within 1e-9
chips and complete grids; failure blocks interpretation rather than dropping rows.

## Status

At first publication, implementation/tests/results were pending. The completed
results follow below. No new candidate feature is selected by this block.


## Implementation checkpoint, before retained-case measurement

New own reply/accounting, diagnosis, replay, optional native audit and offline
renderer modules leave the old learner/encoder/model sources unchanged. The
terminal inspector reads saved examples and cannot train or play online.
Local `make check` passes on Python 3.11.17 and 3.12.15 with all extras:
733 tests, Ruff lint/format, strict mypy and hooks. The 21 new tests include analytic hidden-world and information-premium
examples, brute-force Kuhn replies, three random policies per toy game, a known
Kuhn equilibrium with zero loss, recall/zero-reach/tie guards and tiny end-to-end
fixtures with optional native/plot checks. Fixtures are not research outcomes.

The first native fixture exposed a temporary-policy lifetime error in the new
validation wrapper (process crash). Retaining the native Policy object through
the response evaluation fixes it; the tiny native root/profile checks then run.
A separate fixture metadata path needed its explicit test provenance stub.
Both issues were found before retained-case measurement; neither changes the
own response algorithm or earlier research evidence. The recorded OpenSpiel
2.0.2 license hash is rechecked against the installed distribution:
`cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`.

From clean published source:

```sh
make diagnose-saved-replies
```

The target diagnoses, audits, then renders into ignored
`results/runs/saved-replies/`. Set `SAVED_REPLY_OUTPUT` to a new directory to
preserve an earlier run; overwrites are refused. Once reviewed evidence is
published, `make report-saved-replies` replays it offline with the research extra.
Direct `.venv/bin/python scripts/inspect_saved_reply.py` reads the saved examples.
No new retained-case performance outcome exists at this implementation checkpoint.


## Completed diagnosis

Final clean source `e3ab00097b78c7ca76f526885cab1ff03789ddcb` completes all
eight saved cases in 4.163s. The native audit uses the same clean revision and
takes 8.481s including own replay. All **32 response roots and 32 own reply-profile values** pass; maximum
native disagreement is 9.94760e-14 chips. Full own numerical replay error is zero.
All per-seat decision-loss sums and the exploitability decomposition pass the
fixed 1e-9 chip tolerance. OpenSpiel is 2.0.2 / Apache-2.0; shared export and
partition limitations apply.

| Medium known game | Exact exploitability (% pot) | Within partition (% pot) | Extra exact information (% pot) |
| --- | ---: | ---: | ---: |
| Exact | 0.000182290 | 0.000182290 | 0 |
| Raw public | 0.000182290 | 0.000182290 | 0 |
| Old texture | 2.522516327 | 0.000185935 | 2.522330392 |
| Texture plus categories | 2.593658242 | 0.000168654 | 2.593489588 |

The category candidate is nearly an equilibrium when both responding players
are restricted to its information partition. Its large exact-game weakness is
almost entirely the extra response value available with exact information.
The low-game candidate has no measured information premium and remains near
zero exploitability. All eight cases and tiny near-zero residuals are retained
in the [generated table](../results/saved-replies/report/tables.md).

This favors investigating lost information before simply adding iterations.
It does **not** establish an irreducible exploitability floor for this partition,
a causal estimate of any feature's benefit, or the result of further training.
Another restricted equilibrium could differ; this study holds each saved
opponent fixed. No new strategy is deployed and the prior failed gate remains.

## Concrete response example and an attribution trap

Run `.venv/bin/python scripts/inspect_saved_reply.py`. The default displays
medium category row 1062: responding seat 0 holds `Tc Td` on `Ts 9s 4d 2h`.
The saved strategy checks about 0.000009 of the time, bets to 36 about 0.625078,
and bets all-in to 182 about 0.374912. Under an **exact best-reply continuation**,
check is worth 21.734972 net chips, versus 18.000366/18.000307 for the bets.
Saved reach is 0.5; this row contributes 1.867296 chips to seat 0's unilateral
gain of 1.867375 chips. Seat 0 is responding to the fixed seat 1 strategy.

This turn row has only **one exact member**. The loss therefore cannot be blamed
on merging distinct turn states in that row. Choosing check can unlock valuable
later decisions under an exact-card reply; the saved-prefix/optimal-suffix
identity attributes that opportunity at the earlier decision. The street plot
is an accounting convention, not a map of where to add features. A static
instruction to check trips would not reproduce the counterstrategy.

Use the first graph to compare response value: on the medium panel the orange
information component dominates the two texture bars. The low panel uses a
separate scale around millionths of a percent of pot; compare its numeric table
before inferring large losses from similarly tall bars. The second graph's
seat labels identify the **responder**, and every bar is divided by two so its
sum equals the project's exploitability convention. It is not a street-by-street
causal decomposition of the defender's errors.

## Stopping point and next question

Diagnosis, complete receipts, independent checks and offline figures are done.
There is no new training, sampled grid, fresh case, feature selection or global
agent change. The next proposed block is to identify reachable river decisions
where exact and restricted replies differ and define a small representation
that preserves relevant card-removal/range distinctions. Declare that design
and its admission limits before testing any replacement. This result alone does
not prescribe which feature or prove it will improve performance.

[PR #15](https://github.com/jimmy-sim/poker-ai/pull/15),
[raw diagnosis](../results/saved-replies/diagnosis.json),
[native audit](../results/saved-replies/independent.json),
[CSV tables and two figures](../results/saved-replies/report/tables.md).

## Questions to practice

1. **What does the exact/restricted gap measure?** Extra best-response value from
   exact information against one fixed opponent policy. It is not the EV gain
   promised by retraining with a feature.
2. **Why do losses add up here?** Saved-prefix reaches and optimal-reply suffix
   values form a telescoping identity. Hidden histories are summed per info,
   and the result matches the unilateral root gain and NashConv/2 convention.
3. **Why is a large turn loss not proof of a turn abstraction bug?** Its value
   includes later reply decisions. The largest row has no turn merge at all;
   the continuation can benefit from exact river information.


## Optional-dependency CI correction

Hosted CI on the initial implementation catches direct Matplotlib imports in
this new renderer when only base dependencies are installed. Use the same lazy
optional imports as existing reporters. Preserve the first raw diagnosis,
sidecar and native audit in `results/saved-replies-initial/`. Their captured
source hashes require historical revision `6699f4c` (diagnosis) / `6a03e14`
(audit); they are receipts, not inputs to training or the final diagnosis.
After the checked import fix, the clean-source run and native audit both pass.
`scripts/check_saved_reply_reproduction.py` confirms all eight nested cases,
including examples, are numerically identical; the full own-reply/all-info
sidecar is byte-identical. [Reproduction receipt](../results/saved-replies/reproduction.json).
The native-root receipt guard also rejects a changed root even when a stored
error field still claims zero. The 21 focused tests pass on both versions after
that guard; full all-extras checks pass 733 each, and a separate base install
passes 709 with 15 optional skips. Ruff, strict typing and hooks pass. Hosted CI
for the final head is recorded separately on PR #15.

To repeat the comparison of the retained receipts:

```sh
.venv/bin/python scripts/check_saved_reply_reproduction.py --output /tmp/saved-reply-reproduction.json
```

The source/environment/timing receipts differ as expected; they are excluded
from the numerical equality claim. The original run took 4.223s and its audit
8.773s; these are process wall times, not personal hours.
