# One known wet game: exact-turn decision test

**Prospective issue #4 protocol, November 23, 2026 (PST).** PR #109
[stopped structurally](turn-collision-transfer-result.md) because its third,
low/wet in-position stratum had no candidate meeting the frozen collision
threshold. That **inconclusive** three-stratum result remains final. Its
first-eligible medium/wet out-of-position input was nevertheless saved
without any policy score. This distinct study asks a narrower poker-decision
question: **on that one now-known, structurally inspected wet game, does the
unchanged exact-acting-turn representation reduce exploitability at matched
learning work relative to the unchanged q8-turn control?** It cannot rescue
PR #109, estimate population transfer, isolate board texture from the changed
private ranges, or promote a default. No new policy trajectory or score exists
for this input at publication.

## Fixed input, arms and stopping rule

Use exactly
[`collision_medium_wet_oop-02.json`](../results/turn-collision-transfer/screen/attempts/collision_medium_wet_oop-02.json),
SHA-256 `cea60f6a69d07904078f6930238c7dcbbbb2dba6b36eceb215198b329564a616`,
from PR #109's [published one-time screen](../results/turn-collision-transfer/screen/manifest.json).
It is the second candidate and **first** to meet four collided rows in the
medium/wet OOP stratum, with 12 collided exact acting turn rows in six q8
groups. Its turn board is `Qs Kd As 3c`, it has five disjoint weighted private
combos per seat, 133,131 tree nodes, and unchanged exact river keys. All of
these structural facts were inspected before this plan. Do not redraw,
substitute, train on a second spot or call this held out/unseen.

Control: the qualified `signed_full_q8_turn_exact_river` from PR #108.
Candidate: the unchanged `signed_full_exact_turn_river` adapter from PR #108.
Both use the **same** exact game, chance, owners, payoffs, legal actions,
pot, stacks, range weights and exact river observations. Only the acting
turn information key differs. Start each path from exact uniform current
and average policies. Use signed full expected traversal, linear regret
and linear average weights, target order player zero then one, and charge
every visited node including zero-reach nodes plus initialization. Use one
`PCG64(0)` path per arm, control then candidate; full expected traversal
does not consume RNG, so this is one deterministic comparison, not seed
replication. Save both current and linear-average policies at the first
complete target-pair iteration crossing **100,000, 1,000,000 and 10,000,000**
charged node work; retain actual work and overshoot. No warm start, changed
representation, outcome-based tuning or rerun of an unfavorable scientific
result.

## Frozen readouts and classification

Primary lower-is-better metric: exact restricted-game NashConv/2 at final
linear average in chips and fraction of the **loaded game's initial pot**.
Report candidate-minus-control pairs at all work labels, whole and
post-initial-river positive-average uniform-reach coverage, recall
violations, turn collision inventory, exact/abstract information rows,
table bytes, wall time, hardware and peak RSS. Rank the control's final
top three additive best-response gain rows on each of turn and river,
plus the top three collided turn rows, ties by exact row index. Display
the **same rows** for both arms at all checkpoints with board, private
cards, legal actions, saved probabilities, counterfactual and saved-prefix
reach, alternative-action values and additive contributions. These assume
each saved opponent and optimized reply continuation; local values are not
universal poker advice or the causal effect of changing one action.

The historical candidate absolute gates apply to this one game: final
exploitability **≤0.01 initial pots**, worst **≤0.025** (one deterministic
path), whole coverage **≥0.95**, recall violations **zero**. Report the
control's gates too. **Positive on this known game** additionally requires
candidate-minus-control final exploitability **≤−0.001 initial pots**.
**Negative** means any candidate absolute gate fails or the final paired
difference is **>+0.001**. All other complete outcomes are **inconclusive**.
This one deterministic path yields no seed confidence interval. A software,
publication, numerical or conservative compute gate failure is retained
and ends this experiment; no cap extension, threshold change, new input
or favorable retry. No default promotion under any classification.

## Compute forecast and mandatory publication gates

Planning only: PR #108's two-path 10m known-game launcher took 14.516
seconds, and its slowest fixed 1m repeat scaled to 42.768 seconds per
10m path. Five private combos per seat allow up to `25/4 = 6.25` times
as many private pairings as its two-combo game, suggesting roughly
`2 × 6.25 × 42.768 ≈ 535` path-seconds and a two-worker safety expression
around `2 × (2 × 267.3 + 600) ≈ 2,269` seconds. This is a rough
**pre-run forecast**, not admission: tree size and scoring cost need not
scale with pair counts. The exact study remains capped at **7,200 seconds**
whole process; no paid compute or raised ceiling.

Keep new runner, guards and report isolated from all historical source pins.
Before a real trajectory, pass focused math/correctness tests and exact-source
base and optional Python 3.11/3.12, all-file hooks and both hosted jobs;
publish and GitHub-byte-verify the tested source. Then publish/verify one
fictional own proof under **180 seconds**. Profile both paths **three times
each** to the first complete 1m work crossing under **900 seconds**
including context, own scoring, capture and replay. For each path take
the **maximum** of three complete
`whole_path_seconds × 10m / actual_final_node_work` estimates. Assign one
path per worker, let `T` be the larger path maximum, and separately
publish a data-only admission requiring strictly
**`2 × (2 × T + 600) < 7,200 seconds`**. Failure or equality blocks
the long comparison. Do not choose a faster repeat or change workers.

At most one admitted two-path own study has a **7,200-second** whole cap
plus **120 seconds** reserved to save failures. Publish and verify every
complete or partial own policy, score, receipt and log **before** reference
work. Then audit all **12** saved scalar cases (two arms × three work
labels × current/linear average) against pinned OpenSpiel **2.0.2** with
installed **Apache-2.0** license SHA-256
`cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`,
within **1e−9 chips** and a **900-second** whole audit cap. Reference
strategies never enter training. Build the fixed report from published
bytes, complete final exact-source local/optional/hooks/hosted checks,
retain failures, review and history-merge only if eligible. Earlier
PR #109 and all negative/inconclusive results remain unchanged. Codex
assisted with this prospective plan; human hands-on time and personal
learning were not reported.
