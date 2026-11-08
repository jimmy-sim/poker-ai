# Inspect current policies and the history of their averages

Issue [#4](https://github.com/jimmy-sim/poker-ai/issues/4), November 8, 2026.
Prospective follow-up to PR #29, before implementation or new trajectory outcomes.
Codex-assisted; human hands-on time is not recorded.

## Question and scope

The fixed-opponent diagnosis finds a larger clipped within-partition weakness,
especially for seat 1, even with exact information. Changing only average time
weights can alter the final average without changing raw regrets/current policies
in the software checks. Are the current policies also weak, or does the stored
average retain weak earlier play? Check this before changing a learner.

This is diagnostic replay of the original known trajectories, not a new learning
rule or a proposal to deploy the best-looking snapshot. It does not extend the
10m work budget, revise the old failed gate or admit fresh/global training. There
are no reference strategies, hand-tuned targets, selected seeds or new features.
The configuration fixes selection, outputs and tests before outcomes.

## Complete trajectory and observation set

Retain the same 64 final source cases as PR #29: both games, exact/range-mass,
full controls once and every external seed (20261301/2/3), signed/clipped regrets
and uniform/linear average weights. Regret time weights stay linear, bridge stays
common, and exact simultaneous warm initialization is charged to work. The
existing node/full backends, random generator, update sequence and all rules
remain frozen. Three spawned workers use sorted source identity modulo three.

Replay from initialization because the old archive stores average policies, not
resumable regrets. At original work labels 100k/1m/10m, require all **192 original
average/state fingerprints**, exact iterations and work to match the archived
source case. The recorded Python 3.11.17 / NumPy 2.4.6 runtime is required for this
bit-level prefix gate. No mismatch is repaired by loosening tolerances or dropping
a case. Base Python 3.12 numerical report replay is a separate check, not proof of
bit-identical training on every platform.

Read current policies at first complete-iteration crossings of work labels
100k/1m/5m/9m/10m: **320 current profiles**. The two average-weight cases otherwise
share a raw learning path; verify their current policies match at every label and
label duplicated currents explicitly. They are not independent samples.

At 5m and 9m, copy cumulative `strategy_sum` without changing the solver. At 10m,
subtract each copy from the final cumulative sum, then normalize legal rows using
the unchanged uniform fallback for zero-mass rows. This gives **128 suffix
profiles** across windows (5m,10m] and (9m,10m]. Original iteration time weights
are retained; their clock is not reset. Boundaries mean actual first complete
iterations and their actual work, including overshoots. Warm initialization is
excluded by subtraction. Report zero-window-mass row fractions and uniform-reach
coverage overall and on the river; original warm average coverage is a different
quantity. No epsilon, negative clipping or reference-derived fallback is allowed.

Retain each recaptured whole final average as a control: **64 profiles**. Together
there are **512 self profiles**, all scored and archived with legal menus, exact
identities and raw seeds. Store own response fingerprints, never native strategy
outputs. Observations must preserve raw arrays, policies, RNG, keys and charged
work. Test against an unobserved toy path and frozen indexed implementations.

## Scores and fixed opponents

For every self profile, retain own exact exploitability, within-partition gain,
extra exact-information value, root values and achieved OWN reply fingerprints.
All use the existing own scorer, with source-bound replay. Values are player-zero
chips; unilateral replies use the target's sign. Half-summed self exploitability
and unilateral fixed-opponent gains must be labeled separately; percentages use
each game's initial pot. Extra information plus within gain equals exact total.

At the final work label, compare four own variants: whole average, current,
5m–10m suffix and 9m–10m suffix. For each of the four original source modes, hold
each of the four original saved opponent modes fixed, in each game/encoding/
traversal/seed group, for both seats. Keep **2,048 target conditions**. An own
variant replaces only its responding seat; the opponent always stays frozen.
Require constant within-BR root for a fixed opponent, achieved own reply/root
agreement, and gain differences equal negative target-EV differences. Reuse and
verify the archived OWN response to the fixed opponent, not a native strategy.

Every self profile and fixed-opponent target requires independent scalar checks
with pinned OpenSpiel 2.0.2 / Apache-2.0, license bytes rechecked against the existing
record. Native games use own exports, so agreement does not independently verify
every engine rule. The reference is comparison only: no native training, strategy
export or target enters any agent. All 512 self profiles and 2,048 fixed-opponent
targets must pass; partial grids cannot complete the study.

## Admission, budget and reproducibility

Before new poker trajectory replay: publish this plan/config, implement meaningful
observer/window/loader/accounting/failure tests, complete relevant local base and
optional checks and both hosted code CI jobs, then publish source-bound toy
correctness and compute admission. The correctness receipt must demonstrate that
observing current/sums and extracting suffixes does not change training. No new
poker learning is permitted in the correctness or forecast stage.

Forecast from the original complete `phase=trained` cell durations for the exact
64 selected identities. Partition them in the same fixed three-worker order.
The predetermined planning formula is:

`2 × (2 × maximum partition sum of original cell wall seconds + 600 seconds)`.

The inner factor allows more observations, the fixed allowance covers new parent
IO/report/replay/setup, and the outer factor is a planning guard. This must be
strictly below the unchanged **7,200s own cap** or stop before replaying poker.
This is a forecast, not a measured runtime, confidence bound or personal work time.
It can be wrong; the actual deadline remains binding and partial runs are retained.

The separate **900s native cap** includes own input replay and IO. Chip comparisons
use 1e-9; unitless support reductions use 1e-12. Counts, identities, source bindings,
same-runtime prefixes and target inventories remain exact. Record clean published
source/config/lock hashes, environment/hardware, wall and parent/reaped-child CPU.
Publish own outcomes before independent comparison for the recorded study.
Fresh one-command reproduction may retain immutable ignored own staging. Refuse
overwrites and retain failure reasons, partial snapshots and worker outcomes.

## Reporting and decision rule

Keep all raw cases, checkpoints, windows, original prefix checks, controls and
target matches. Full controls run once; sampled reports show individual fixed
seeds and arithmetic means without confidence intervals. Six fixed figures:

1. Current exact-exploitability curves, full controls.
2. Current curves, sampled means and raw seed points.
3. Final whole/current/suffix within-plus-extra bars, full controls.
4. Final bars, sampled means and raw seed points.
5. Fixed-opponent gain differences against whole averages, full, both seats.
6. The same fixed-opponent differences, sampled means, both seats.

Current/window behavior can distinguish weak endpoints from weak stored history
in these finite trajectories. Neither a favorable current snapshot nor a suffix
score proves convergence, a better general averaging rule or a repair. A noisy
current path and its average can have different vulnerabilities. Keep unfavorable
outcomes and do not select an arm, checkpoint, window or seed after inspection.
Any later proposed method and performance admission need a separate protocol.

Done means all original-prefix/observer/current-pair/accounting checks, complete
own/native receipts and replay, all six inspected plots and raw tables, methodology
and limitations, three interview answers, work log, README/journal updates and
green final CI. Implementation and every new outcome are pending at publication.
