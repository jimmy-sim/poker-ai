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

## Implementation checkpoint before calibration

Own scorer checks exact/restricted roots with separate own response calculations,
value ordering and both frozen river-prefix accounting panels. Context validation
requires unchanged game arrays, legal menus, owners, information mapping, streets
and perfect recall. Native code is separate; it compares scalar roots and achieved
OWN replies only. Tests block reference training/policy-export methods.

The observer checks raw arrays/policies/RNG/key/work fingerprints around callbacks,
coalesces labels without pooling axes, and exports read-only copies. Diagnostic
cost uses explicit same-shape copies of old policy arrays as storage fixtures and
half the keys for lookup work; their returned norms/coverage are not learning
results. No training update or random draw occurs in cost calibration.

The first full-size IO unit was interrupted after six checks. Its padded payload
was unnecessarily large; the interrupt traceback also showed a macOS font-discovery
subprocess wait. No RAM usage was measured, so this is not a causal memory/timing
claim. Artifact storage now packs only legal decision weights (two or three here),
with explicit menus and exact padded-byte restoration; noncanonical negative-zero
padding is rejected. The strategy math/arrays stay unchanged, including chance
width 44. The synthetic 840-profile stress archive streams compressed JSONL and
reads one record at a time, rather than decoding all copies simultaneously.
The old local unit log/scratch is retained; no calibration receipt was produced.

All 56 new fast tests pass. All seven explicit slower integration checks pass in
60.58s, including all 16 old published metric profiles, native comparisons and the
full-size archive plus eight rendered figures. Native error bounds are 1e-9 chips.
The installed OpenSpiel license bytes match the previously read Apache-2.0 record.
Strict typing (274 files), lint/format and hooks pass. Full local suites pass:
1132 fast tests each Python 3.11.17 / 3.12.15; base 1099 / 24 optional skips.
Seven explicit slow integrations pass each Python version (60.58 / 59.17s).
Hosted CI and both formal calibrations remain pending. Figures were inspected for prominent synthetic
labels; they stay in ignored scratch space, never a strength report.

The eight IO figures fix four primary metrics × two separate checkpoint axes,
each with four game/representation panels and individual cell curves. Future own
scoring/replay uses the fixed worker partitions. The native forecast additionally
charges serial own-input replay over all 840 policies, conservatively, before the
parallel native phase. These accounting details are fixed before measurements;
all declared caps, cases, seeds and tolerances stay unchanged.

### Three questions to explain this step

1. **Why can average coverage be one before sampling visits the river?** The warm
   exact uniform update supplies positive average mass to all possible rows.
   Sampled visit coverage counts later sampled passes only. Neither is convergence.
2. **What does the river number measure?** A saved opponent is fixed while only
   the responder's river choices switch, keeping its exact-reply turn prefix.
   It is a frozen-policy comparison, not predicted improvement after retraining.
3. **Does packing the file change the strategy?** Only legal action weights are
   stored, then restored into the same padded matrix with identical bytes. Menu,
   shape, metadata and hashes are checked. Training update equations do not change.

Self-review: observation fingerprints include raw learning arrays, both exports,
RNG, keys and charged work. Scoring checks unchanged game structure, perfect
recall, signs and additive identities. Packing preserves legal weights and exact
padded bytes; 840-record JSONL decoding is streamed. Native functions supply
comparison scalars only; old own profiles remain the sole calibration inputs.
This is Codex-assisted solo self-review, not independent human review.

## First own-cost receipt and CI correction

Published source `f6ca5cb` completed all 48 own cases and all three 840-record IO
fixtures in 107.725027s, with no new learning. The unmodified receipt and 16-profile
bundle are retained in `results/controlled-pipeline-check/attempts/f6ca5cb/`.
They are historical source-bound evidence, not the final admission forecast.

Hosted [CI 42517901699](https://github.com/jimmy-sim/poker-ai/actions/runs/42517901699)
failed base-only typing before tests on both Python jobs: the renderer directly
imported optional `matplotlib`. Local all-extras typing and base pytest had passed;
base-only typing had been omitted. Use the existing dynamic optional-import
pattern, verify typing in base environments too, then repeat the same fixed
calibration under the corrected published source. No cap, seed, case, metric or
acceptance tolerance changes. Native timing and learning remain off until then.

The optional renderer now follows the existing `importlib.import_module` pattern;
no dependency or mypy-ignore configuration changes. Corrected-source checks pass:
full base `make check` on Python 3.11.17 / 3.12.15, each 1099 tests / 24 optional
skips; clean non-incremental strict typing on both base versions (274 files),
all-extras typing, 56 fast focused tests and another full-size rendering integration
(60.99s). The same calibration will be repeated from the corrected published
source; the first receipt remains archived unchanged.

## Corrected own-cost receipt, before native timing

Clean checked published source `8843db19e4312d48e99ad882b39e7fb9888f10db`
completes all 48 old-own cases and three full-size reporting fixtures in
**107.173776s**. Full replay verifies all 16 unique source policies, exact policy
bits, root/response/river metrics, repeat archive/metadata digests and cost records.
The [own receipt](../results/controlled-pipeline-check/own.json) and
[own profile bundle](../results/controlled-pipeline-check/own-profiles.json.gz)
are published before native timing. The first-source attempt remains unchanged.

Largest observed own scoring/round-trip cost across all four source policies and
three repeats per group: low exact 0.034753s, low range 0.035043s, medium
exact 0.505002s, medium range 0.470891s. Full-size fixture repeats take
25.821397 / 16.939204 / 16.930429s; all retained, including font-discovery startup.
Worker training + two scoring/replay passes project 2270.864 / 2239.840 / 2223.470s.
Including measured overhead and the largest full-size fixture gives 2337.248s,
**4674.496s with the unchanged 2× margin**, below 7200s. This is a planning estimate,
not a timing guarantee or learning admission. Native costs/checks and final CI
remain pending; no new postflop training or strength result.
