# Verify checkpoint scoring and remaining pipeline cost

Issue [#4](https://github.com/jimmy-sim/poker-ai/issues/4), November 8, 2026.
Depends on PR #26. Codex-assisted; personal hands-on time not recorded.

## Fixed milestone and definition of done before outcomes

The three-process known-cost forecast is 4257.374s under the unchanged 7200s cap,
but scoring/checkpoint/report work is missing. This milestone implements and tests
those functions and measures OLD OWN policies only. It does not start the 140-cell
learning comparison or pick an agent/default. Keep all earlier source and receipts
frozen. Publish checked code before calibration and own receipts before native
comparison. Complete tests, typing/lint/hooks/hosted CI, rerunnable evidence/tables,
learning journal/work log and three explanatory interview Q&As.

## Checkpoint and metric contract

Follow the unchanged preregistered work thresholds 100k/1m/10m and exact iteration
labels 16/64/128. Observe each first COMPLETE work-crossing iteration; record its
previous count, final count and overshoot. Stop at the latest required condition.
Coalesce labels met together into one policy snapshot while retaining both axes.
Export/scoring must not modify training arrays, RNG, visited keys or counters.
Test uninterrupted versus observed trajectories, warm/cold starts and all rule
variants on finite toy fixtures. Round-trip finite policies through canonical
JSON/gzip (mtime=0), verify hash, metadata/shape/menus and exact policy bytes.

For a saved profile value v in player-zero chips, let B_i be the own exact reply
value and R_i the own partition-constrained reply value in target-i chips. Let
s_0=+1, s_1=-1. Report exact exploitability = sum_i(B_i-s_i*v)/2,
within-partition gain = sum_i(R_i-s_i*v)/2, and extra-information gap =
sum_i(B_i-R_i)/2. Check their additive identity, ordering and finiteness at 1e-9
chips; do not clip a negative result into a pass. Exact encoding must have zero
extra-information gap. Deterministic ties choose the first legal maximizer.

For each target, use its exact-reply turn rows and replace only its river rows
with its restricted reply, holding the saved opponent fixed. River-only gain with
exact prefix is half the sum of B_i minus that hybrid target value. This isolates
a frozen-policy river switch, not expected EV improvement after retraining. Use
existing own reply/river accounting, including perfect-recall guards; test an
independently hand-computed hidden-world example and existing saved metrics.

Secondary diagnostics: L2 norm of all stored regrets; fraction of partition rows
with positive average mass; river-key visit fraction from external target passes
EXCLUDING exact initialization (full traversal visits all rows). No river rows
gives null coverage, not a fabricated zero/one. Explain that warm initialization
can give full positive-average coverage immediately, without convergence.

## Fixed calibration workload and resources

Use all 16 existing final own profiles: two pinned known games, exact/range-mass,
one full control and each of three sampled seeds. Reuse source-bound old loaders
and diagnosis/audit receipts, select no favorable cases. Three repeats on three
spawned processes; fixed sorted profile order and index modulo three. This is
48 own cases. Each times scoring plus atomic compressed policy/metric write,
hash/read/byte-exact round trip. Include fresh worker trees/metadata, initialization,
source/input validation, IPC/collection, setup and parent/reaped-child CPU costs.
Own calibration cap 1200s; retain incomplete/failure evidence.

After committing own results, independently audit all 16 profiles in three repeats
(48 native cases), again with three fixed processes and a separate 1200s cap.
Use pinned OpenSpiel 2.0.2 Apache-2.0, reuse and hash-check the license record in
`docs/solver_validation.md`. Native values, exact/restricted best-response roots,
and achieved OWN exact/restricted/hybrid reply profiles must agree at 1e-9 chips.
No reference action or policy export, solver training, commercial output or
reference input to own agent training. Native output is comparison-only. Test
this optional stage separately from base dependency checks.

## Conservative forecasts and admission boundary

Use the pinned three-worker per-partition training sums. For each future cell,
charge SIX snapshots, with maximum measured score/round-trip time across ALL four
source profiles and all three repeats for its game/representation. Charge that
cost twice: in-run scoring plus post-run own replay. Sum each fixed 140-cell worker
partition, take the maximum, add measured setup/launch/collection and report costs,
then apply the same 2x margin. Benchmark serialization/table/plot rendering for an
840-row duplicate-data fixture from old policies. Label it SYNTHETIC IO CALIBRATION,
never present duplicated rows as learning outcomes, and retain generated fixtures
in ignored scratch space. Record that extrapolations remain timing estimates.

Forecast native audit separately for the same 840 policies, using per-game/encoding
maxima over all saved cases/repeats, fixed partitions and measured overhead, then
2x; compare with a separately declared 3600s native-audit planning cap. This does
not relax the unchanged 7200s OWN-stage limit. Report aggregate CPU separately.
Missing costs, failures or an exceeded cap keep the large study off. Even when
both estimates fit, this milestone only establishes tested machinery and a
resource estimate. A subsequent checked runner/protocol must explicitly admit
and enforce the complete fixed-work experiment. No strength/river-cause/default
or fresh/global claim follows old-policy cost calibration.
