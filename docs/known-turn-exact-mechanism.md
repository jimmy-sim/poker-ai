# Prospective known-case exact-turn mechanism test

**Issue #4; November 23, 2026 (PST).** This protocol and its [machine
contract](../configs/known-turn-exact-mechanism.json) precede any new tree,
policy, profile or score measurement. The [PR #106 saved-policy diagnosis](river-turn-loss-diagnosis-result.md)
found 12 exact acting turn rows sharing six q8 keys on the already evaluated
`full_new_medium_dry_oop` game. Those rows carried 92.8173% of the saved
candidate's final turn best-response gain. This is a plausible grouping
constraint, not evidence that finer keys improve play. [PR #107](turn-exact-transfer-result.md)
then stopped structurally before training: three separately selected inputs
had zero turn collisions. This distinct experiment tests the diagnosed
**known** input only; it cannot establish unseen-case transfer or full-game
strength. No default changes.

## Definition of done and fixed question

At identical complete expected charged node work, does splitting only the
acting turn q8 keys into exact acting information improve the final
linear-average restricted-game policy against the unchanged
`q8_turn_exact_river` control? Retain the same exact game, board, private
ranges, evaluator, chance/payoff/owner/action arrays, public action menu,
exact river key, signed regrets, linear regret weight, linear average and
frozen target order. The [PR #107 isolated adapter](../scripts/turn_exact_transfer/representation.py)
is the candidate implementation; its source and historical dependencies must
remain byte-identical. New orchestration, guards, tests and reporting live
only in isolated new modules.

Done means a published protocol; independent tiny-game correctness tests;
exact-source base and optional Python 3.11/3.12 qualification, all-file hooks
and both hosted jobs; one published fictional own proof; one fixed profile
and separate strict conservative admission; at most one admitted own pair;
own publication before a pinned comparison-only reference scalar audit;
fixed decision report, final exact-source checks, solo review and
history-preserving merge if eligible. A failed correctness, numerical,
source, publication or compute gate stops with evidence. An unfavorable
scientific result ends this experiment, without changed inputs, seeds, work
or thresholds.

## Frozen pair and measurements

Use exactly the **previously evaluated**
`configs/river-full-broader-spots/full_new_medium_dry_oop.json` input,
SHA-256 `b7c74e0de96e9949f8eb0e359d085b4e3281ea3172b9979f8a23f394bb642dea`:
turn board **As Jc 5d 3h**, out-of-position acting seat, initial pot **36
chips**. It was chosen before this protocol because the published diagnosis
identified collisions and opposing local action preferences. There is no
new spot draw, substitution, holdout or unseen claim. The source-qualified
PR #107 fingerprint is
`fb9006517142ee23076f2c0b6d581475dfdaed8127cb2c146a60731af901b09c`;
its source-archive manifest SHA-256 is
`af541362cdea019e33bca2385b83b79ebbed40b52fc926ba287243ccf2dc4071`.
Require those pins and the PR #107 ancestry, without changing the old files.

Run exactly **two** paths in order: unchanged signed full expected
`q8_turn_exact_river` control, then the PR #107 exact-turn/exact-river
candidate. Each path gets its own explicit **PCG64(0)**; complete passes
must consume no random draws. The paths are deterministic, so one path per
arm gives no seed-based confidence interval. Both begin from identical
exact uniform initialization, charge its complete tree traversals and
all later visited nodes including zero-reach nodes, and run target zero
then one as a complete pair. Save current and primary linear-average policy
at the first complete target-pair crossing **100,000, 1,000,000 and
10,000,000** charged visits. Record actual work and overshoot. No warm
start, alternate seed or checkpoint selection.

Primary lower-is-better metric: exact restricted-game NashConv/2 in chips
and divided by the 36-chip initial pot, at final linear average. At every
checkpoint report both arms, candidate-minus-control paired difference,
both-seat/turn/river additive best-response gains, whole and post-initial-
river positive-average uniform-reach coverage, recall violations, exact
and abstract information rows, strategy table bytes, actual charged work,
wall time, hardware and peak worker RSS. Both paths share one game and are
not independent samples. Compute no cross-game uncertainty interval.

Display diagnosed exact information rows **2445, 30 and 1** and the control's
final top **three** additive best-response-gain rows on each of turn and
river (ties by exact information index). Show the *same* resulting rows for
both arms at all checkpoints, without selecting favorable candidate rows.
For each row show acting seat, private cards, board, pot, legal actions,
saved action probabilities, counterfactual and saved-prefix reach,
alternative-action values and additive contribution. Values assume the
fixed saved opponent policy and an optimized best-reply continuation. A
local score is distinct from additive exploitability and is not universal
poker advice or a causal estimate of retraining benefit.

## Frozen classification

Apply the historical absolute candidate gates on this one finite game:
final exploitability at most **0.01 initial pots** (the single deterministic
path is both its median and worst, also at most **0.025**), whole coverage
at least **0.95**, and **zero** recall violations. Report the same gates
for the control. **Positive** requires all candidate absolute gates and
candidate-minus-control final exploitability at most **−0.001 initial
pots**. **Negative** means any candidate absolute gate fails, or the
candidate worsens by more than **+0.001 initial pots**. Other complete
outcomes are **inconclusive**. Report the measured paired difference even
if an absolute gate fails; a partial improvement does not change the
classification. No outcome here promotes a default or establishes
population-level performance.

## Qualification, compute and publication

Before a real trajectory, independently enumerate rational fictional
expected passes for both targets; check turn-key refinement, exact-river
identity, same exact game/actions/owners/payoffs, recall, unchanged RNG,
work crossings, snapshots, replay and retained failure behavior. Include
a no-collision fictional fixture where both representations agree. Pin
historical source and PR #107 source/archive hashes before and after each
base/optional role. Run the complete prescribed local suites, all-file
hooks and both hosted CI jobs on the exact tested source. Publish and
GitHub-byte-verify the qualified source receipt before proof.

The previous q8 full expected path on this exact known game reached 10m
work in **12.933 seconds** with **231,718,912 bytes** peak RSS; its earlier
1m path profile repeats were about **3.8–4.3 seconds** including context,
capture, own scoring and replay. These are planning context, not a bound
for exact-turn keys or two simultaneous workers. The next qualification
and profile may take hours; no paid compute or larger cap is authorized.

Publish and verify one fictional own proof under **180 seconds**. Then
profile both fixed paths to the first complete **1m** crossing **three
times each**, six complete paths under **900 seconds** overall, including
context construction, capture, own scoring and replay. Use **two fixed
workers**, path index modulo two, retaining every repeat, failure, timing
and RSS; do not choose a favorable repeat. For each path take the maximum
of its three complete `whole_path_seconds × 10m / actual_final_work`
estimates. Let `T` be the larger of the two fixed worker sums. Publish and
GitHub-byte-verify all profile bytes before a separate data-only admission
that recomputes strictly **`2 × (2 × T + 600) < 7200 seconds`**. Failure or
equality rejects the longer run; no changed assignment, formula or cap.

At most one admitted two-path own study has a **7,200-second** whole-process
cap and **120-second** failure-save reserve. Keep every partial/failing
output and publish/GitHub-byte-verify complete or partial own policies,
scores and logs **before** any reference work. Audit the **12** saved
current/linear-average policies' values, best replies and exploitability
against pinned OpenSpiel **2.0.2**, installed **Apache-2.0** license hash
`cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`,
within **1e−9 chips** and **900 seconds**. Reference output is scalar
comparison only; never load a reference strategy into training. Build the
fixed report from published bytes, complete final exact-source local,
optional, hooks and hosted checks, and retain failed qualification evidence.
No scientific retry, seed search, budget extension or default promotion.
Codex assisted with the prospective plan; human hands-on time and personal
learning were not reported. **No new policy or score measurement existed at
publication.**
