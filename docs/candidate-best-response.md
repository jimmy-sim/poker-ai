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

Protocol published before new measurements. Implementation, tests and actual
results are pending. No candidate feature is selected by this block.


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
