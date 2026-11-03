# Phase 4 — frozen-policy match evaluation (implementation)

Definition of done: fixed random/always-call/always-raise/TAG/equity opponents and
an OpenSpiel baseline; duplicate deals with seats exchanged; win rates in mbb/hand,
cluster-aware confidence intervals and a predeclared significance test; measured
variance reduction (a documented alternative to AIVAT); independent reference-rule
checks; reproducible configs/reports and three interview answers. Slumbot is a
separate conditional public-benchmark step, with permission/protocol checked first.
The timing pilot is now complete; its small-sample scores are retained for
transparency and are not playing-strength claims. Main results are pending.

## Predeclared local experiment

`configs/match-evaluation.json` fixes the experiment before match outcomes. Primary
is the frozen own potential-8 external-sampling agent at 1,000 iterations for the
three existing seeds, without choosing favorable seeds or retraining on results.
This agent was weak in Phase 3.5's restricted games; the benchmark will measure its
actual behavior rather than assume it is strong. Both policies use full-pot/all-in
sizes with legal passive/fold choices, 200-chip equal stacks and 1/2 blinds (100bb).

Each independently sampled deck is replayed with the own agent in seat 0 and then
seat 1, fixed button 1 and reset stacks. Hole cards and public chance tape stay in
the same physical seats, so each policy receives both card/position roles. This is
simulation, with no real-money client or real-time assistance integration.

The timing pilot uses 32 duplicate decks on its own seed. The main budget is 1,000
fresh decks per opponent, three fixed agent policies and both seats. Pilot results
will estimate runtime before launching main compute; no favorable-outcome stopping
or seed replacement is allowed. Six opponent definitions are retained, including
any losses or wide intervals. Own uniform fallbacks are counted explicitly.

Baselines: uniform over matched concrete actions; check/call; largest legal raise
(all-in) then passive; a transparent tight preflop value chart plus postflop equity
heuristic; and a uniform-opponent equity/pot-odds heuristic. Equity sample budgets,
thresholds and seeds are fixed. Deterministic canonical-card equity estimates are
part of each frozen heuristic; they do not learn from match histories.

## Inference and variance

For each deal average the two exchanged-seat profits, then average the three fixed
agent policies within that deal. The independent statistical unit is the **deal**,
not each seat or training seed. The target is the equally weighted set of these
three fixed policies, not the population of possible trained agents. Per-seed
results are descriptive. Units: mean net chips/hand divided by big blind times
1,000 = milli-big-blinds/hand.

Report an approximate paired CLT 95% interval and a conservative bounded Hoeffding
interval. The predeclared primary test is two-sided mean-zero Hoeffding, corrected
with Bonferroni over six opponents. A positive estimate or narrow empirical CLT
interval alone is not the significance rule. Known payoff support is [-200,200]
chips/hand. Log tail bounds avoid reporting underflow as an exact zero probability.
These finite-sample guarantees require independent sampled deals and fixed N;
matching both seats/three agents does not multiply the independent sample count.

Duplicate pairing is the variance-reduction alternative to AIVAT here; no AIVAT
estimator is claimed. Compare empirical paired variance to the estimate obtained
by omitting cross-seat covariance. Pairing need not reduce variance. Tests include
exact cancellation for deterministic callbot self-matches, positive covariance
that increases variance, manual SE/unit conversions and familywise tail checks.

## OpenSpiel reference baseline and independence

Use OpenSpiel 2.0.2 **Python ISMCTS** with native `universal_poker` ACPC mechanics,
32 simulations, 16 world samples, one random rollout, UCT constant 200 chip units
and normalized visit counts. It is a small search baseline, not a GTO solver or a
claim of strong poker. The acting observation contains only own cards/public data;
a synthetic opponent hand constructs the native root. Search resamples compatible
opponent hands uniformly. It does not infer opponent ranges from action likelihood.

All search, rollout and world-sampling streams are explicit separate seeds. Early
prototype replay tests found native one-shot action ordering sensitivity and an
unseeded default world sampler in the Python wrapper. The chosen wrapper uses
OpenSpiel's public `set_resampler` hook with a seeded callback. Tests verify
fixed-input repeatability and invariance to the synthetic opponent hand; a failure
blocks scoring. No upstream or own C++ code is added or modified.

Native private-card dealing is grouped per player, versus the own interleaved
deal. Known cards are mapped explicitly. Native pot/all-in methods return
**total-hand raise targets**, converted to own street targets by subtracting prior
street commitments. Native has no explicit hidden burns, which does not change
the marginal conditional distribution of unseen board cards. Concrete legal menus,
nonterminal paid ledgers and net terminal payouts are checked on fixed-seed shared
full-world traces before scoring. These rules cover fully funded heads-up play
with equal stacks and this grid, not all 2–6-seat engine edge cases.

OpenSpiel's complete pinned Apache 2.0 license was read in
[Phase 3.5](solver_validation.md). The full additional ACPC license was read from
[upstream commit 6ae3e6e](https://github.com/jblespiau/project_acpc_server/blob/6ae3e6ec59b66139a9bd444ff7ba3c40271a565a/LICENSE):
CPRG/University of Alberta 2011 permission notice with a nonendorsement clause,
plus the RNG's 1997–2002 BSD three-clause notice. Preserve copyright/permission/
disclaimer and applicable nonendorsement notices; this is not labeled plain MIT.
License SHA256: `1d5b4504d396cec59bb5c9153c3725ae8eb80522bd3ddee76c26919eec09b56d`.
The inspected upstream commit is from 2020; OpenSpiel's install script clones that
dependency's master branch without exposing the wheel's exact bundled commit.
The OpenSpiel version/locked wheel is known; exact bundled ACPC source identity
is a provenance limitation, not an invented verified revision. The
[pinned upstream README](https://github.com/google-deepmind/open_spiel/blob/v2.0.2/open_spiel/games/universal_poker/README.md)
also cautions that this game has not been extensively reviewed by its team.

Reference search is an opponent inside evaluation only. It is never imported by
own agent/training/abstraction modules or used as own training data/strategy.

## Slumbot preparation — no game requests sent yet

The [official public API example](https://slumbot.com/sample_api.py) documents
anonymous sessions, `/slumbot/api/new_hand` and `/slumbot/api/act`, street raise-to
amounts and 50/100 blinds with 20,000 chips (200bb). The
[maintainer's October 12, 2026 reply](https://github.com/ericgjackson/slumbot2019/issues/49)
approves paced anonymous research with sequential requests and backoff on errors.
A small separately declared pilot can follow local validation; no large/multi-hour
session will start without flagging compute/sample tradeoffs. No account messages
or credentials are needed. The unrelated `slumbot.lol` terms are not this service.

A matched-depth own 200bb checkpoint must be trained from own self-play only before
this benchmark. Public protocol parsing/settlement and error handling must be
verified first. Do not copy/import the example implementation, disable TLS checks,
retry ambiguous non-idempotent actions blindly, hide incomplete hands or report a
small connectivity pilot as a competitive win-rate result. External server deals
are not client-seeded; retain sanitized raw responses and label live rerun limits.

## Local commands

Own checkpoints must exist (`make validate-solvers` recreates them from own
self-play). The pilot/main commands install the pinned optional reference/plot
extras and independently verify the configured 1,000 native-mechanics traces.

```sh
make check
make pilot-evaluation  # 32 decks/opponent, separate chance seed; ignored outputs
make evaluate-agents  # 1,000 fresh decks/opponent, all three fixed own policies
```

A failed rule/action/fingerprint check aborts scoring. A technical time-budget
abort keeps raw completed hands for diagnosis, does not infer from a partial
prefix and does not replace reviewed results. Worker processes are fresh, with
fixed RNG streams and no shared learning. Main data retain all per-hand profits,
counts and deck hashes so interval calculations can be audited separately.


## Timing pilot gate

The separately seeded pilot completed all six opponents and its 1,000-hand native
mechanics gate with zero payout disagreement. A second fresh-process run exactly
replayed all raw hand records, inference outputs and own lookup counts. See the
[retained pilot](../results/evaluation/pilot/pilot.json) and
[replay audit](../results/evaluation/pilot/reproducibility.json). The pilot projects
about seven minutes of serial worker time for the main budget; parallel wall time
and cache/startup costs differ. This is below the few-hour compute warning gate.
No pilot scores were used to change seeds, agents, sizes, thresholds or N.

The two displayed 95% intervals are pointwise, not simultaneous family intervals.
The predeclared family-adjusted test determines significance. Pilot intervals
have particularly low power; only the fresh fixed-N main study will be summarized
as evaluation evidence.
