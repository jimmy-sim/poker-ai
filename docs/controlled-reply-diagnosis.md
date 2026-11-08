# Explain the clipping/averaging tradeoff with saved policies

Issue [#4](https://github.com/jimmy-sim/poker-ai/issues/4), November 8, 2026.
Depends on the completed original comparison in PR #28. Codex-assisted; personal
hands-on time not recorded. This document fixes selection and tests before new
diagnostic outcomes. It selects no strongest recipe and runs no new Hold'em training.

## Question, complete selection and units

The previously failing medium range-mass game motivates this follow-up. Changing
clipping under linear regret weights lowered total exploitability with linear
strategy averaging, while raising it with uniform averaging. Extra-information
value fell but within-partition response gain could rise. Diagnose that tradeoff
before changing the agent. All source policies were already independently audited.

Fix the original 10m work label and linear regret weights, matching the motivating
old sampled baseline. Keep signed/clipped regrets × uniform/linear averages, both
original games × exact/range-mass representations × full once/external all three
fixed seeds. This is **64 saved policies**, not newly trained agents. Select every
identity in this grid; do not select by metric, rank, seed or current strength.
Inputs include the entire immutable own archive and native receipt by SHA-256.
Game values are player-zero chips; responder values and gains use the target's
sign (+ for seat 0, - for seat 1). Display pot-normalized scores separately.

## Part 1: trace the within-partition gain

For each source profile and both seats (128 traces), compute an own best response
inside the same information partition. Keep the opponent fixed at that saved
profile. Use the checked `trace_losses`: saved full prefix reach multiplied by
local deviation with optimal own reply continuation. Aggregate hidden histories
within an information group before maximizing; retain every owned row, including
zero-support/zero-loss rows. Pure ties choose the first legal maximizer, no epsilon
substitution. Store own reply fingerprints, root values, row losses, saved reach,
counterfactual support and legal conditional action values in a compact streamed
archive with schema/menus/source bindings. No reference strategy is stored.

Require additive rows = unilateral response gain, and half-sum over both seats =
the source's within-partition metric, all at 1e-9 chips. Sum by turn and river only
when street is publicly constant inside each group. These are fixed-profile loss
accounting numbers; they are not a retraining intervention or unique attribution
of cause to one street or feature. An unmerged turn row can depend on future reply
choices. Never add these restricted response losses to exact response losses as
if they were disjoint. No action-conditioned beliefs are newly trained.

## Part 2: hold the opponent fixed

Within each game/encoding/traversal/seed group, cross every ordered pair of the
four modes: player 0 uses A, player 1 uses B. This yields **256 crossed profiles**
and **512 target conditions**. For each target, report baseline target EV, own
within-partition BR root, achieved own reply EV, and unilateral gain. Rows label
which mode belongs to the responding agent and which to its opponent. Retain all
opponents, both seats and all seeds. Do not assume the matrix is antisymmetric:
position, ranges and stacks can make the fixed game asymmetric. Each profile is
zero-sum, with target signs explicit.

The BR root depends on the fixed opponent, not on the responding agent's original
probabilities. Verify that root is constant across own modes for each opponent
and target, and that a difference in unilateral gains equals the negative target
EV difference. These identities distinguish changed opponent behavior from own
policy EV changes; they do not establish globally stronger play. Diagonal crossed
profiles must match the audited source values and within gains. Reuse source own
reply profiles where appropriate, but independently re-evaluate them and verify
hashes. New crossed EVs/roots/achieved own replies require native comparison too.

## Software tests, measurement and reporting gates

Before measuring: publish this config, then implementation with meaningful tests,
complete relevant base/optional local checks and both code CI jobs. Tests cover
selection/pins, compact trace loader, hidden-information aggregation, seat signs,
row/street/root accounting, all crossed identities, deliberate partial/altered
inputs and an asymmetric hand-computed toy game. A separate toy regression checks
that changing only average time weights leaves regrets, current policies, RNG,
visits and sampled keys unchanged. It formalizes an updater property; it is not
new postflop learning or a claim of cross-runtime bit equality for the whole agent.

Own and native stages each have a separate **900s hard cap**, including their
input checks and IO; retain partial outcomes on failure, no silent budget reset.
Publish complete own results before native comparison. OpenSpiel 2.0.2 uses the
previously read Apache-2.0 license; recheck installed bytes/version. Native results
are scalar comparisons only; reference training and strategy export are forbidden.
Every target/row/profile must pass fixed 1e-9 chip accounting/comparison, with
unitless support reductions checked at 1e-12. Both stages require clean published
source, fixed source/archive hashes, environment and actual CPU/wall receipts.

Done means complete own/native receipts, source-bound replay, all raw rows and
crossed conditions, two street-contribution figures and two fixed-opponent gain
heatmaps, methodology/limitations, three interview Q&As, journal/work log, checked
CLI and green final CI. Sampled figures show arithmetic means and raw seed points
where applicable, without confidence intervals. The inspector defaults to the
motivating clipped/linear-average first-seed medium range-mass case, but can show
any retained source row. It labels merged-row Q values and illustrative own-card /
board examples clearly. It does not read hidden opponent cards to choose actions,
run a live client, train an agent, or present universal poker advice.

The original comparison's code and receipts stay frozen. Fresh reproduction of
that earlier study belongs at its recorded revision; later read-only modules do
not silently extend its learning admission. No new representation, seed, budget
or accuracy gate is chosen in this follow-up.
