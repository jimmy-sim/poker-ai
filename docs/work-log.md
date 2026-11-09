# Development work log

Use this log with [issues](https://github.com/jimmy-sim/poker-ai/issues),
[pull requests](https://github.com/jimmy-sim/poker-ai/pulls),
[commits](https://github.com/jimmy-sim/poker-ai/commits/main/) and
[hosted CI](https://github.com/jimmy-sim/poker-ai/actions). The
[contribution workflow](../CONTRIBUTING.md) defines how each new task becomes a
reviewable result.

Dates below use America/Los_Angeles unless marked UTC. Entries describe actual
work; elapsed agent/process time is not a record of personal hands-on hours.

For a guided explanation of the ideas and results, start with the
[plain-English learning journal](learning-journal.md).

## 2026-11-09 — Averaging-history runner and independent checks

- **Authorization:** One work window from midnight to 08:00 Pacific, continuing
  issue #4 and [PR #30](https://github.com/jimmy-sim/poker-ai/pull/30). This does not
  create another night of work. Codex-assisted; human hands-on time not recorded.
- **Change:** Complete own replay/report runner, source-bound toy correctness and
  historical forecast/admission, plus isolated native scalar comparison. Retain
  raw cumulative weights to reconstruct whole/suffix policies without training.
  Reports keep all seeds, duplicate current paths, support and fixed opponents.
- **Tests so far:** 193 focused fast checks pass. Complete three-process toy
  archive replay and four deliberately rehashed corruptions pass all 13 replay
  checks (8.99s). Altered scores, support, window timing and cumulative masses
  fail semantic validation despite recomputed file hashes. Fictional header/grid
  fixtures test schema only, explicitly not research outcomes.
- **Independent adapter:** Previously audited medium-game policies pass both
  target signs, all four own modes and fixed-reply cache reuse. Reference training
  and strategy export are blocked in this integration check. Partial own/native
  attempts are retained, overwrite refused, admission denied before any worker.
- **Remaining at this checkpoint:** Complete base/optional checks, hosted CI,
  clean source-bound toy correctness/forecast and published admission. No new
  Hold'em trajectory, new native study, selected snapshot or default admission.
- **Complete code checks:** Base `make check` passes 1439 tests with 24 optional
  skips on Python 3.11/3.12 (231.53/219.48s). All-extras suites pass 1472 each
  (262.02/251.12s); all ten relevant slow checks pass (31.88/32.62s). Strict typing
  covers 338 files in base and optional environments; lint/format/hooks pass.
  Both code CI jobs and source-bound correctness/forecast/admission still precede
  any new Hold'em replay. Local testing times are not experiment or human hours.

## 2026-11-08 — Current policies and averaging history, prospective

- **Request / issue:** Continue autonomous daytime #4 work after the fixed-opponent
  diagnosis. [Plan](averaging-history.md) and config fix all 64 original cases,
  192 original same-runtime prefix checks, 320 current /128 suffix /64 whole
  profiles and 2048 fixed-opponent target conditions before implementation/outcomes.
- **Question:** Does the current policy retain the weakness, or does the average
  retain weak earlier play? Replaying the same original 10m trajectories is needed
  because the old compact archive is not a resumable trainer. No new learning rule,
  extended work budget, selected snapshot/window or default/fresh/global admission.
- **Gates:** Read-only observer and exact prefix proof, frozen backend/rules/RNG,
  complete local/hosted checks and source-bound correctness/compute admission
  before poker replay. Three processes; forecast from the same 64 old durations,
  fixed formula/guard; own/native caps 7200/900s. Retain all outcomes/failures.
- **Status:** Protocol publication; implementation, admission and all new outcomes
  pending. Codex-assisted; personal hands-on time not recorded.
- **Before outcomes:** Retain 192 own cumulative-mass boundaries too, so suffix
  definitions reconstruct from the archive without retraining. Storage-only
  clarification; all cases/windows/metrics/seeds/caps/gates remain unchanged.
- **Foundation checks:** Own read-only current/sum observer, suffix mass arithmetic,
  compact raw-mass envelopes, original-prefix trajectory worker and complete-grid
  validation implemented. 119 focused checks pass on both Python versions; clean
  strict typing covers 322 files. Real archived loader passes with new learning
  and native construction blocked (4.48/4.23s). Eight toy worker combinations
  reconstruct windows and original prefixes; deliberate late prefix corruption
  retains partial files and fails completion. Full fictional ledgers test only
  schema/completeness, with invented values explicitly labeled non-research.
  Full foundation base make check passes 1365 tests /24 optional skips on both
  versions (235.52/225.48s); optional suites pass 1398 each (278.33/270.72s).
  Lint/format/clean strict typing pass. Complete runner/admission/study pending;
  no new poker learning. Journal step 33 explains the planned comparison.
- **Published foundation:** `f5c9b3b`, both hosted jobs 42534643024 pass. Complete
  runner/replay/report/admission and isolated native adapter subsequently drafted
  locally. Latest 146 fast checks pass (2.00s), strict typing 336 files, lint and
  format pass. Actual three-process toy archive integration passes Python 3.11/3.12
  (5.50/5.40s); six numerical files reproduce byte-for-byte and six explicitly toy
  figures render (20.86s), representative layouts inspected.
- **User returned:** Stop this autonomous block before new poker replay. Full
  runner changes remain isolated locally, beyond the published foundation. Native
  adapter integration/schema tests, final relevant full checks/CI, source-bound
  correctness/forecast and admission remain required before the fixed study.
  No new Hold'em trajectory outcomes, window choice or agent default change.

## 2026-11-08 — Saved controlled-policy reply diagnosis, prospective

- **Request / issue:** Continue authorized daytime #4 work after the complete
  controlled comparison. [Plan](controlled-reply-diagnosis.md), config fixes 64
  source policies / 128 within traces / 256 ordered crosses / 512 targets before
  diagnostic outcomes. Linear regret weights retain the original baseline context;
  all clipping/averaging modes, games/encodings/full controls/seeds retained.
- **Question:** Locate the within-partition gain increase and hold opponents fixed
  before blaming a street or changing a learner. No new postflop training, best-arm
  choice, new representation/default/fresh/global admission.
- **Gates:** Row/street/root/EV identities, complete grids, source/trace bindings,
  isolated native comparisons, separate 900s caps, tests and both code CI jobs
  before measurement. Implementation built; outcomes pending. Codex-assisted;
  personal hands-on time not recorded.
- **Initial software checks:** Asymmetric hidden-action toy and all ordered crosses
  check signs/root/EV identities; 16 raw-trajectory invariance cases cover both
  traversal/regret/weight/warm modes. 89 focused fast checks and four optional slow
  checks pass; base old-policy/inspector integrations need no optional reference
  runtime. Full base make check passes 1246 tests / 24 optional skips on each
  Python version (234.10/224.29s); full optional suites pass 1279 each
  (282.18/271.77s). Strict typing covers 310 files. Final-layout four slow checks
  pass 22.50/23.04s; base pair passes 7.22/5.85s. Lint/format/hooks pass.
  Final receipt-hardening targeted checks pass; hosted code CI/study gates pending.
- **Boundary correction before measurement:** The full suite catches a new
  read-only archived-reference import inside the postflop package. Move the new
  diagnosis into evaluation, preserving the existing no-reference-import training
  test. The focused regression passes; full checks rerun on the corrected layout.
- **Review:** Compact replies bind legal menus and every owned row; support/mass
  replay uses 1e-12 separately from chip values at 1e-9. All ordered crosses retain
  asymmetric seat signs and fixed-opponent identities. Failed/partial receipts
  remain inspectable; no reference strategy is exported. Four synthetic figures
  inspected for layout, clearly labeled as software fixtures. Journal step 32
  explains the question before outcomes. Execution-only reproduction clarification
  published before measurements; no seed/metric/tolerance/cap change.
  Native receipt validation also requires its complete 128-trace own replay with
  finite bounded error/time; deliberate corruptions fail closed.
- **Own evidence before native:** Both hosted code jobs 42531469249 pass on
  clean `4f34289`. All 64 sources / 128 traces / 256 crosses / 512 targets finish
  in 19.920551s (<900); parent/reaped-child CPU 10.704774/9.16s. Archive 3,065,110
  bytes, SHA 840dc20aa50a2933f85d60388f5e88a46f9ac340d9e1213b59e7810287ec0373.
  Base Python 3.12 replays all traces with zero error (8.797627s), regenerating
  all four numerical files byte-identically. Four actual plots visually checked.
  Independent comparison was pending at own-evidence publication `53d4fe9`.
- **Independent outcome:** All 256 crossed profiles /512 targets pass EV, root and
  achieved OWN reply comparison; max 2.415845e-13 chips (<1e-9). Native 17.525516s
  (<900), including zero-error own replay 8.868434s. Parent/reaped-child CPU
  17.475461/0.03s. License/version checked; no reference strategy exported.
  Audited base Python 3.12 replay zero (8.795223s); four numerical files byte-identical.
- **Finding:** Focal sampled medium candidate clipped/linear within gain 1.811454%
  pot splits turn 1.315782 /river 0.495672. Turn accounting is not training cause.
  With opponents fixed, seat-1 signed→clipped own linear-average gain increases
  2.446176–2.496141 points over all four opponent modes; exact encoding also shows
  2.473964–2.617986. Changed opponents/compression alone cannot explain this
  within weakness. All modes/seeds/seats retained; no winner/default/global stage.
- **Reporting / next:** Methods, four figures, three interview answers and journal
  step 32 explain units and limits. Both base CLI seat inspectors verify the audit.
  Standard frozen-writer CSV CRLF retained; CR-at-EOL-aware diff check passes.
  Final CI 42532418497 passes both Python jobs; PR #29 merged at `ca0b555`.
  Main .venv passes 90 focused tests (4.00s), own replay zero (8.894023s), archived
  native validation and all four byte-identical numerical reports. Seat-1 CLI
  succeeds; all ten unrelated modified output hashes unchanged. Next compare current
  policies and averaging history with checked replay before changing a learner.

## 2026-11-08 — Original controlled-learning comparison, prospective runner

- **Request / issue:** Continue autonomous daytime #4 work after the measured
  pipeline forecasts fit. [Plan](controlled-learning-comparison.md); original
  140 cells, seeds, work/iteration labels and scope remain frozen.
- **Before outcomes:** Publish this protocol before implementation and require a
  source-bound correctness receipt, complete local checks and both hosted CI jobs
  before new postflop learning. Three fixed workers, streaming legal snapshots,
  own replay, all-cell native comparison and separate hard caps.
- **Analysis fixed in advance:** All raw seeds, 32 conditional differences and 15
  averaged factorial differences; separate work and iteration axes, four-point
  bridge with common endpoint reused. No winner/default/global admission.
- **Implementation:** Frozen trainer/scorer wrappers, first-crossing/exact-iteration
  observations, source-bound CI/correctness admission, atomic compact strategies,
  streamed archive, own replay and isolated native roots/achieved-own-reply checks.
  Store own reply fingerprints and reconstruct them with the own scorer; no native
  strategies enter training. Typed finite-grid validation rejects partial results.
- **Checks so far:** 58 new fast checks pass Python 3.11/3.12. Real three-process
  toy orchestration covers all 140 identities / 840 labels. Two slow old-policy /
  synthetic-render checks pass Python 3.11/3.12 in 34.35/37.24s; reference strategy export and
  new poker learning tripwires pass. Strict typing 293 files, lint/format pass.
  Full base make check passes both versions: 1157 / 24 optional skips each.
  Final focused checks and clean non-incremental typing pass both base versions.
  Full optional suites pass 1190 each (265.87/255.54s); final-source slow pair
  passes 39.74/38.26s. Clean code `87fb4bc` yields 32 toy trajectories / 136
  snapshots in 0.539277s. Hosted CI 42522375101 passes both jobs on `87fb4bc`; source-bound
  admission recorded before learning; study had not started at that checkpoint.
- **Own evidence:** Clean published `70fe2f2` completes 140 cells / 840 checkpoints
  in 2161.351771s (<7200), batch 2148.667566s, parent/child CPU 3.489438/6446.21s.
  All prefix checks pass; own replay zero for all 282/282/276 worker snapshots,
  clean exits. Archive 8,725,389 bytes; all raw rows, 1536 means / 4512 contrasts /
  96 bridge rows / eight figures retained. Actual layout inspected; no strength
  or cause claim before separate native audit. Own outputs published first.
- **Native evidence:** Own outputs published `3bd6858` before comparison. All
  840 native EV/root/achieved-own-reply comparisons pass, max 1.705303e-13 chips
  (<1e-9). Native 92.193960s (<3600), parent/child CPU 0.222218/270.45s. License
  bytes/version checked; no reference strategies in training. Base Python 3.12 /
  NumPy 2.5.4 replays all 840 with zero error (64.920820s); all five numerical
  reports regenerate byte-identically. Timing/PNG bytes are not reproduced.
- **Finding:** In the focal medium candidate at 10m work, linear regret/average
  weights: clipping lowers sampled mean total 4.354032→2.501852% pot, but shifts
  within 0.243207→1.811454 while extra falls 4.110824→0.690398. With uniform
  strategy averaging it raises total 2.664089→3.525759. All three seed-pair signs
  agree in each contrast, without population inference. All eight common rule
  contexts retain a sampled-minus-full mean gap in this focal case. No unique
  cause, best-arm/default/fresh/global admission; follow up on saved own traces.
- **Reporting:** All outcomes, eight inspected/tested figures, raw contrasts,
  methodology/limitations, three interview answers, verified claim draft, README
  and journal step 31 updated. Final CI 42526808991 passes both jobs at `c45b463`;
  merged PR #28 at `4d4b69a`. User main .venv passes 246 focused checks (49.38s),
  all 840-policy replay zero (72.184812s) and archived native validation. First
  report output path was sandbox-denied after numerical replay; the same helper
  regenerates five byte-identical tables in /tmp. Ten unrelated output hashes
  unchanged. No source/gate change.
- **Admission CI:** Both code 42522375101 and receipt 42523042766 pass both Python
  jobs before this evidence publication; source/config hashes unchanged.
- **Correction / review:** Prefix lookup initially omitted 44 full controls because
  the node timing column contains only external cells. A test catches this; use
  the frozen combined endpoint lookup. No rule/seed/gate changes. Self-review adds
  typed metric/work/coverage guards, final endpoint checks and partial-file retention.
- **Assistance / time:** Codex-assisted; personal hands-on time not recorded.

## 2026-11-08 — Checkpoint/scoring and remaining pipeline cost

- **Request / issue:** Continue through-day #4 work after PR #26 puts three-process
  known cost below the cap. [PR #27](https://github.com/jimmy-sim/poker-ai/pull/27),
  [plan](controlled-pipeline-check.md); config published `561ed6d` before implementation/calibration.
- **Scope:** Checkpoint observers preserve arrays/RNG/keys/work; exact work crossings
  and iteration labels stay separate. Own EV/exact/restricted/river root accounting,
  explicit L2/coverage diagnostics, compact legal-weight archives and exact padded
  byte round trips. Separate native comparison-only module; no new postflop learning.
- **Fixed cost workload:** All 16 OLD own final profiles, three repeats and three
  workers: 48 own plus 48 native cases, separate 1200s caps. Synthetic 840-record
  IO/report fixture has eight figures and prominent labels, kept in ignored scratch.
  Forecasts retain 2× / 7200s own gate and separate 3600s native gate; no admission.
- **Unit findings / correction:** First padded full-size unit interrupted after six
  checks (local log `/tmp/pipeline-check-slow.log`, 116.65s). Payload was oversized;
  trace also showed a macOS font-discovery subprocess wait. No measured-RAM or
  sole-cause claim. Legal weights now stored with menus and exact byte restoration;
  fixture streams JSONL one profile at a time. No research gate/seed/formula changed.
- **Checks so far:** 56 fast tests pass; seven explicit slow integrations pass in
  60.58s, including all 16 old metrics, native roots/achieved own replies and render.
  Native strategy export/training tripwires pass. Rechecked installed Apache-2.0
  bytes against the previously read license. Strict typing (274 files), lint/format
  and hooks pass. Full local suites: 1132 fast each Python 3.11.17 / 3.12.15;
  base 1099 / 24 optional skips. Seven slow integrations pass each Python version
  (60.58 / 59.17s). Hosted CI and formal calibrations pending at this code checkpoint.
- **First own receipt / CI:** Clean published `f6ca5cb` completes 48 own cases and
  three full-size fixtures in 107.725027s. Raw receipt/bundle retained under
  `results/controlled-pipeline-check/attempts/f6ca5cb/`; no final forecast/native run.
  [CI 42517901699](https://github.com/jimmy-sim/poker-ai/actions/runs/42517901699)
  fails base-only typing before tests: direct optional Matplotlib import. Local
  base pytest had passed, but base-only typing was omitted. Fix the optional-import
  boundary, check base typing and repeat identical calibration from corrected
  published source; no scientific gates change. Native timing/learning stay off.
- **CI fix checks:** Renderer uses the existing dynamic optional-import pattern,
  without dependency/typing-gate changes. Base `make check` passes both Python
  3.11.17 / 3.12.15: each 1099 / 24 optional skips, plus clean non-incremental
  strict typing (274 files) both base versions, all-extras typing, 56 fast checks
  and a fresh full-size renderer integration (60.99s). Repeat the identical cost
  calibration from corrected published code; retain first source-bound artifacts.
- **Corrected own receipt:** Clean published `8843db1` completes all 48 cases /
  three full-size fixtures in 107.173776s. Full 16-profile replay, exact policy bits,
  metrics/replies/digests and timings pass. Root own receipt/profile bundle published
  before native timing. Group scoring maxima 0.034753 / 0.035043 / 0.505002 /
  0.470891s; IO fixtures 25.821397 / 16.939204 / 16.930429s, all retained. Forecast
  own 2337.248s, guarded 4674.496s < 7200. Still no learning admission; native/CI pending.
- **Native / final report:** Own receipt published at `9501ec4` before native run;
  all 48 comparisons complete in 31.318523s. Max scalar error 1.207923e-13 chips,
  fixed 1e-9 limit, no native actions/strategy export. Aggregate own/native CPU
  128.455632 / 49.144088s; final guarded forecasts 4674.496362 / 543.837789s below
  unchanged 7200 own / separate 3600 native caps. Native estimate includes serial
  own-input replay for 840 policies. [Table](../results/controlled-pipeline-check/report/tables.md).
  No new learning, strength, cause/default/global or automatic admission claim.
- **Merge / main:** Final CI 42520115258 passes both jobs; PR #27 merged at
  `a979d0a`. User .venv passes 188 focused fast checks (37.49s), final report and
  old correctness replay. All ten unrelated modified output hashes unchanged.
- **Next:** Journal step 30 completes old-policy correctness/cost calibration.
  Both report files regenerate byte-identically on base Python 3.12; saved timing
  validation, not wall-time reproduction. Final CI/main verification passed; next
  define the actual 140-cell runner without changing the preregistered comparison.
  No default, strength, river-cause or global admission.
- **Assistance / time:** Codex-assisted; personal hands-on hours not recorded.

## 2026-11-08 — Independent-cell process calibration

- **Request / issue:** Continue authorized through-day work on #4 after the serial
  node-cache forecast still exceeds the unchanged cap. [PR #26](https://github.com/jimmy-sim/poker-ai/pull/26),
  [plan](parallel-cell-calibration.md); config published `77460e2` before implementation/outcomes.
- **Fixed scope:** 1/2/3 spawned processes, three rotated-order repeats, all 140
  cells each (1260 endpoints), original modulo partitions; same frozen trainers,
  seeds/rules/work. Exact serial endpoint gate before forecasts. Charge startup,
  tree preparation, IPC/collection and separate parent/reaped-child CPU cost.
- **Implementation:** Isolated worker-local matrices/trainers/RNG, requested native
  thread environment recorded, streamed partial events, terminate/reap on failure.
  Source-bound replay/report, fixed-partition max-of-three forecast with measured
  overhead; same 1200s calibration / 10m / 2× / 7200s planning limit.
- **Checks so far:** 37 new tests pass, including real spawned toy parity and
  deliberate exception/exit/invalid-message/timeout cleanup. Initial test-module
  namespace was not importable in spawned children; explicit test source path fixes
  the fixture. 132 focused checks pass; strict typing (261 files), lint/format and hooks pass.
  Full local suites: 1076 all-extras each Python 3.11.17 / 3.12.15; base 1043 /
  24 optional skips. CPU accounting assertions pass in all three environments.
  Hosted CI and the fixed profile remain pending at this checked-code checkpoint.
- **Recorded evidence:** Clean published `0dd5af6` completes all nine batches in
  197.722051s; all 1260 serial state/RNG/work/cache endpoint checks pass. Median
  batch wall for 1/2/3 processes 33.163 / 18.691 / 13.827s; median serial ratio
  1 / 1.771 / 2.400×; aggregate CPU 33.175 / 37.213 / 40.795s. All observations
  retained. Guarded known-cost forecasts 12250.546 / 6299.036 / 4257.374s; latter
  two remain unresolved because scoring/checkpoint/audit/report costs are missing.
  [Receipt](../results/parallel-cell-profile/profile.json),
  [table](../results/parallel-cell-profile/report/tables.md); all three report files
  byte-identical on Python 3.12. Hosted CI separately pending at evidence publication.
- **Merge / user checkout:** Final CI both passes on `97eb96d`
  ([42514226815](https://github.com/jimmy-sim/poker-ai/actions/runs/42514226815));
  merged PR #26 as `75ef29d`. Earlier code-only CI superseded/cancelled by concurrency.
  User `.venv`: 132 focused checks pass (36.91s), process/node reports and correctness
  replay pass. All ten preexisting modified result files remain byte-identical.
- **Scope / next:** Journal step 29. No scoring, learning admission, default,
  playing-strength, global or river-cause claim. Remain on checked independent
  milestones while the user is away.
- **Assistance / time:** Codex-assisted; personal hands-on hours not recorded.

## 2026-11-08 — Immutable game-node interface cache

- **Request / issue:** Continue authorized through-day work on #4's measured
  menu/child-wrapper overhead after PR #24. [PR #25](https://github.com/jimmy-sim/poker-ai/pull/25),
  [plan](cached-node-graph.md), config published eaded32 before outcomes.
- **Implementation:** Opt-in immutable node graph, acyclic child pointers and
  cached static interface only. Frozen row math, sampler, updater, RNG/rules and
  evidence unchanged. Fresh graph construction charged to initialization;
  prepared-node records separate from unchanged CFR work. O(N) memory tradeoff.
- **Predeclared gates:** All nodes/edges of four matrices, exact 96-cell / six
  checkpoint trajectories, balanced 708 timing rows and six profiler cases;
  unchanged compute forecast/cap. Generic validator uses explicitly renamed
  reference/candidate schema roles without changing values or implementations.
- **Implementation checks:** 30 new + 65 prior focused tests pass (95 total),
  including 48,604 nodes / 48,600 edges, permuted node IDs, frozen metadata,
  per-iteration math/RNG/work/query counts and changed receipt rejection.
  Ruff/format, strict typing (256 files) and all-file hooks pass. Full local
  suites: 1039 all-extras each Python 3.11.17 / 3.12.15; base 1006 / 24 optional
  skips. Hosted CI and fixed profile remain pending at this code checkpoint.
- **Recorded evidence:** Clean published `1991026` completed all four interface
  matrices, 96 trajectories / 576 exact checkpoints, 708 timing rows and six
  instrumented cases in 213.256995s. Paired order 144/144; all ratios retained,
  min/median/max 1.040 / 1.356 / 1.668. Forecast parent/nodes 8168.894 / 6216.028s;
  2× guarded 16337.788 / 12432.056s both exceed 7200s before other costs.
  [Receipt](../results/cached-node-profile/profile.json),
  [table](../results/cached-node-profile/report/tables.md). All five report files
  regenerate byte-identically on Python 3.12. Hosted CI separately pending.
  First commit-hook attempt lacked uv on PATH; environment-loaded retry passed.
- **Merge / user checkout:** Both final CI jobs pass at `e7ed1be`
  ([42512474368](https://github.com/jimmy-sim/poker-ai/actions/runs/42512474368));
  merged PR #25 as `5db25f7`. Earlier code-only CI was superseded/cancelled by
  concurrency, not a math failure. Main `.venv` passes 95 focused checks (21.83s),
  new report and prior correctness/controlled/row reports; all ten unrelated
  modified output files are byte-identical after fast-forward and verification.
- **Scope / next:** Journal step 28. Interface/trajectory/performance only, no
  default, strength, river-cause or learning-run admission. Continue subsequent
  checked milestones under the user's through-day instruction.
- **Assistance / time:** Codex-assisted; personal hands-on hours not recorded.

## 2026-11-08 — Policy-row cache and exact paired profile

- **Request / issue:** Reduce #4's measured policy-table overhead, verify unchanged
  behavior and profile again. [PR #24](https://github.com/jimmy-sim/poker-ai/pull/24),
  [plan](row-policy-cache.md), config published fc27c56 before outcomes.
- **Implementation:** Opt-in external backend: padded row normalization once per
  visited row per frozen target pass, fresh cache before the next player. Existing
  sampler, updater, rules, initialization, menus, source and evidence unchanged.
  Skip the overwritten uniform fallback on positive rows; keep finite/legal row
  checks. Dense full-state exports remain inherited.
- **Fixed gates:** All 96 external cells / six checkpoints through iteration1001
  must match exact array bytes, policies, RNG, keys and charged work before timing.
  708 contemporaneous timing rows, balanced backend order, shared full cells,
  six profiler cases; unchanged 10m/max-of-three/2×/7200s forecast and 1200s cap.
- **Implementation checks:** 32 new + 33 prior focused tests pass (65 total),
  lint/format and strict typing (251 files) pass. Full local checks pass 1009
  all-extras each Python 3.11.17/3.12.15; base-only 976 passed/24 optional skips.
  Hooks and both [code CI jobs 42508619364](https://github.com/jimmy-sim/poker-ai/actions/runs/42508619364)
  pass. Code was checked/published before measurements; hosted CI overlapped them.
- **Recorded evidence:** All 96 trajectories / 576 exact checkpoints, 708 timing
  rows and six instrumented cases match state/RNG/work from clean 4cc0cc4928 in
  323.345249s. Median paired dense/cache loop ratio 1.695×; low range-mass median
  1.073× and slower individual repeats retained. Dense/cache training forecasts
  15,228.659 / 8,219.338s; guarded 30,457.318 / 16,438.675s both exceed 7200s.
  [Raw data](../results/row-policy-profile/profile.json),
  [table](../results/row-policy-profile/report/tables.md). All five report files
  regenerate byte-identically on Python 3.12; not a wall-time reproduction claim. Journal step 27.
- **Stop / next:** Verified opt-in parity/profile only; no default, strength,
  learning-cause or fresh/global admission, and no full learning sweep.
  User authorized autonomous continuation through the day; next is the measured
  state-adapter menu/child overhead, in a separate protocol/PR.
- **Assistance / time:** Codex-assisted; personal hands-on hours not recorded.

## 2026-11-08 — Controlled training compute gate

- **Request / issue:** Continue #4 after reproducing the correctness gate.
  [PR #23](https://github.com/jimmy-sim/poker-ai/pull/23),
  [prospective plan](controlled-training-profile.md), config published 58d8c62.
- **Fixed before timings:** All 140 common/unique bridge cells, three timing
  repetitions (420 rows), four separate profiler cases, fixed iteration counts,
  900s profiling cap, max-of-three forecast and 2× guard against the unchanged
  7200s learning cap. No EV/exploitability, arm selection or automatic learning run.
- **Implementation checkpoint:** Library orchestration and thin CLI, complete-grid
  timing validation/report, exact state/RNG repeat checks, legacy replay adapter.
  Baseline mathematical source/receipt unchanged; the old CLI import is bridged
  with explicitly pinned old/new hashes before outcomes. 13 new tests and all
  33 focused checks pass. Full local checks: 977 all-extras each Python
  3.11.17/3.12.15; base-only 944 passed/24 optional skips. Ruff lint/format,
  strict typing (246 files) and hooks pass. Hosted CI runs separately.
- **Recorded evidence:** All 420 rows/140 cells/four profiler cases complete from
  clean 44da3984 in 179.069551s; all repeat/instrumentation state and work match.
  Forecast 15,235.392s training-only; fixed 2× guard 30,470.783s versus 7200s cap.
  Decision `training_only_guarded_forecast_exceeds_cap`; full study not launched.
  External cells contribute 98.395% of forecast. Fixed medium sampled profiler
  case spends 49.43% of instrumented step cumulative time in current_policy;
  low case 20.26%. No universal bottleneck fraction or promised speedup.
  [Raw evidence](../results/controlled-training-profile/profile.json),
  [tables](../results/controlled-training-profile/report/tables.md); complete
  Python 3.12 regeneration matches all four report files byte-for-byte.
- **Stop / next:** Finish the verified compute gate before selecting a measured
  optimization or launching the controlled learning sweep. Next is opt-in
  overhead reduction with exact trajectory/RNG/work checks and a new profile.
  No optimizer or learning-cause result here. Journal step 26.
- **Assistance / time:** Codex-assisted; personal hands-on hours not recorded.

## 2026-11-08 — Controlled training definitions and correctness gate

- **Request / issue:** Continue #4 by isolating training differences behind the
  saved river weakness. [PR #22](https://github.com/jimmy-sim/poker-ai/pull/22).
- **Before outcomes:** Publish [protocol](training-isolation.md) and pinned
  config c6e39c8. Stop at common-updater correctness and historical work audit;
  later 16-cell learning grid/bridge is preregistered, not run.
- **Implemented:** Own full/external updater with independent regret/average
  weights, aggregate-then-clip, matched averaging and charged simultaneous start.
  Exact selector enumeration, all-control work audit, receipt replay and CLI.
  Historical code/policies unchanged; no reference actions involved.
- **Initial checks:** 20 focused tests pass, including old full/sampled modes,
  both real range-mass adapters, all 16 combinations, expectation/nonlinearity,
  averaging conventions, RNG/work and changed-receipt rejection. Full local
  checks: 964 all-extras each Python 3.11.17/3.12.15; base-only 931 passed/24
  optional skips. Ruff lint/format, strict mypy (243 files) and hooks pass. Both
  [code CI jobs 42466613135](https://github.com/jimmy-sim/poker-ai/actions/runs/42466613135)
  pass before receipt production from clean b8ed1d4.
- **Recorded evidence:** Four frozen-policy cases / 54 joint selector tapes pass;
  max raw regret/average discrepancies 8.32667e-17 / 5.55112e-17 fixture chips.
  Clipping nonlinearity demonstrated, not attributed as a poker-strength cause.
  All 30 historical work rows verified; medium range-mass old full endpoint
  174,514,176 visits versus about 10m sampled (17.4514×). Software audit 0.042211s;
  full offline replay passes both Python versions. [Receipt](../results/training-isolation/correctness.json).
- **Interpretation / next:** Definitions differ beyond sampling; do not claim
  a training cause before the controlled study. Journal step 25 explains this.
  No new postflop learning result, remedy or admission/default change.
- **Assistance / time:** Codex-assisted; personal hands-on hours not recorded.

## 2026-11-08 — Fixed-policy seat/street swaps

- **Request / issue:** Investigate #4's different full/sampled vulnerabilities
  while keeping the information groups fixed. [Plan](frozen-policy-swaps.md).
- **Before outcomes:** All controls/games/seeds; 160 crossed profiles and 120
  street hybrids. Opponent-specific roots, prior diagonals, signed two-street
  effects and interaction. No new training or remedy selection.
- **Checked code before outcomes:** Runner, native audit, report/inspector and
  30 new tests. All-extras 944 pass each Python 3.11.17/3.12.15; base-only 911
  passed/24 optional skips. Ruff lint/format, strict mypy and hooks pass.
- **Verified result:** All 160 crossed profiles/320 target rows, 120 street
  hybrids/240 response conditions complete in 60.218s from clean c2f14c1; nested
  replay zero. Medium range-mass mean extra gap FF/SF/FS/SS =
  0.271466/0.254886/3.361794/4.110824% pot. River contributes 3.473133 points
  of the 3.839358-point change; turn 0.366225, interaction 0.765610 already shared.
- **Independent evidence:** 160 crossed and 120 hybrid baseline EVs, 480 roots
  and 480 achieved own reply values pass native checks; max 1.27898e-13 chips.
  Audit 71.163s from clean acc98d8 after own evidence publication. Code CI
  42463711199 passes both jobs before measurements. Both plots visually checked.
- **Interpretation / stop:** [PR #21](https://github.com/jimmy-sim/poker-ai/pull/21),
  [method](frozen-policy-swaps.md), [tables/two plots](../results/policy-swaps/report/tables.md)
  and journal step 24. Saved river choices dominate this policy-substitution
  effect; training-algorithm causality remains untested. No new training, remedy,
  admission or default change; all failed gates remain and #4 stays open.
- **Assistance / time:** Codex-assisted; personal hands-on hours not recorded.

## 2026-11-07 — Saved range-mass reply diagnosis

- **Issue / request:** Continue #4 after the failed sampled gate; diagnose before
  selecting a remedy. [Prospective plan](range-mass-reply-diagnosis.md).
- **Fixed scope:** All 30 final sampled policies and ten full controls, both
  seats, exact/restricted replies, full loss accounting and all seeds retained.
  Arithmetic means for additive components. No new training or feature choice.
- **Implementation checks before outcomes:** Own diagnosis, nested replay, native
  root/achieved-value audit, report/inspector and 28 new tests. Local all-extras
  914 tests pass on Python 3.11.17/3.12.15; base-only 883 passed/22 optional skips.
  Ruff lint/format, strict mypy and hooks pass. No new research replies computed.
- **Measured diagnosis:** All 40 cases complete in 26.361s from clean 38fbe0f.
  Medium candidate sampled mean 4.354032% pot = 0.243207% within partition +
  4.110824% extra exact-information value; median remains 4.480481%. Same-key
  full control totals 0.271640%, so no universal abstraction floor/remedy claim.
- **Independent evidence:** All 160 exact/restricted roots and 160 achieved own
  reply values pass native checks; max 1.20792e-13 chips, own nested replay zero.
  Audit 49.321s from clean 5982ebb after own evidence publication. Full Python
  3.12 replay passes; both plots inspected; first-seed set-of-nines example retained.
- **Report / stop:** [PR #20](https://github.com/jimmy-sim/poker-ai/pull/20),
  [method](range-mass-reply-diagnosis.md), [tables/two figures](../results/range-mass-replies/report/tables.md)
  and journal step 23. No training, feature/remedy selection or admission change.
  All earlier failures remain; #4 stays open for the next controlled question.
- **Assistance / time:** Codex-assisted; personal hands-on time not recorded.

## 2026-11-07 — Range-mass fixed-work sampled comparison

- **Request / issue:** Continue #4's fixed-work sampled stage; stop at audited
  development results. [Plan](range-mass-sampled.md), unchanged protocol.
- **Before outcomes:** Five controls, two games, three fixed seeds and three work
  checkpoints: 90 policies. Count exact initialization and whole-iteration work.
  Replay the prior full-control admission before training; publish tested code.
- **Implemented / checked before outcomes:** Own runner, bundled checkpoint/visit
  replay, native audit, offline report and 39 new tests. `make check` passes
  884 all-extras tests on Python 3.11.17/3.12.15; base-only 855 passed/20 optional
  skips. Ruff lint/format, strict mypy and hooks pass. No sampled outcome yet.
- **CI finding / retained interruption:** Hosted run 42446227294 fails the real
  prior-admission replay on Linux at exact diagnostic equality. Local checks had
  passed. Stop the first run at 20/90 snapshots after 259.433 seconds; retain
  `results/range-mass-sampled-initial/` with original clean source acd3941 and
  KeyboardInterrupt/incomplete status. No performance admission from this run.
  Investigate portable numerical replay without editing frozen old source or
  changing the feature, seeds, work budgets or performance thresholds.
- **Corrected verification:** 886 all-extras tests each on Python 3.11/3.12,
  base-only 857 passed/20 skips, 41 new tests. Ruff/format/strict mypy/hooks pass.
  Hosted repair CI 42446699119 passes both jobs before the complete rerun.
- **Measured result:** All 90 snapshots complete from clean 64c0d9d in 1254.790s.
  Candidate medium median 4.480481% pot, worst 5.506634%, failing fixed 1%/2.5%
  limits; category 6.722857%/7.188975%, exact/raw 0.233819%/0.254711%.
  Low passes. Coverage 100%, recall zero. All 90 checkpoint/visit pairs replay
  with zero error; all 90 native value/BR checks pass, max 8.52651e-14 chips.
  Audit 15.461s. Raw evidence published as f8f4f67 before native comparison.
- **Evidence / stop:** [PR #19](https://github.com/jimmy-sim/poker-ai/pull/19),
  [method](range-mass-sampled.md), [tables/two plots](../results/range-mass-sampled/report/tables.md),
  journal step 22. A cumulative 3,008,036,864-byte peak RSS includes receipt
  serialization; no total-memory/competitive-strength claim. Stop before fresh,
  global or default changes; diagnose the saved failure next. No rescue run.
- **Assistance / time:** Codex-assisted; personal hands-on time not recorded.

## 2026-11-07 — Range-mass full-control admission

- **Issue / authorization:** User requested continuing #4 after the protocol gate.
- **Prospective scope:** One unchanged range-mass candidate; all five controls,
  two known games and six full-tree checkpoints. Publish checked code before
  measuring; preserve failed gates. [Plan](range-mass-admission.md).
- **Implementation checks:** 845 all-extras tests pass on Python 3.11.17 and
  3.12.15; base-only checks pass 818 with 18 optional skips. Includes 25 new
  runner/replay/audit/report tests. Ruff, strict mypy and hooks pass. These are
  software checks, separate from the research gate.
- **Measured result:** All 60 snapshots complete in 12.884 seconds. Both games
  pass unchanged limits. Medium candidate 0.271640% pot versus category
  2.593658% and exact 0.000182290% at 4,096 full iterations; 1,662/3,336 raw
  rows. Coverage 100%, recall violations zero. All 60 native value/BR checks
  pass, maximum error 1.27898e-13 chips; own replay zero. Audit 7.229 seconds.
- **Limit / evidence:** Longer medium keys increase key bytes despite fewer
  table rows; no total-memory or global-strength claim. [PR #18](https://github.com/jimmy-sim/poker-ai/pull/18),
  [method](range-mass-admission.md), [tables/figures](../results/range-mass-admission/report/tables.md)
  and journal step 21 retain source/config/context/work receipts.
- **Environment check:** A reused Python 3.12 environment later contained a
  duplicate editable path pointing to the previous worktree. A fresh environment
  is used for the final 3.12 replay/check; no research source/config is changed.
- **Stopping point:** Independently audited full-control evidence and journal
  step 21. No sampled learning, new feature search or global/default change.
- **Assistance / time:** Codex-assisted; personal hands-on time not recorded.

## 2026-11-07 — Range-mass candidate protocol and correctness

- **Request / issue:** Continue #4 by defining the next blocker/range-aware
  representation and acceptance tests, then stop at the protocol/correctness gate.
- **Prospective choice:** One `texture_range_q8_b8` candidate: existing private
  buckets/texture/category history plus river blocked/loss/tie/win masses against
  a fixed declared prior, pooled and quantized into eight intervals. Context-bound
  keys; no actual hidden hand, future card, betting posterior or solver output.
- **Before outcomes:** Publish [definition/limits](range-mass-representation.md)
  and pinned config before implementation/partition measurement. Keep prior full
  and sampled accuracy/compression/work limits. No learning/compression study,
  fresh/global stage, default change or deployable checkpoint in this block.
- **Completed implementation:** Optional context-bound encoder, finite adapter,
  inspector and pure full/sampled metric contracts. Exact rational mass bins;
  unsupported-view and serialization guards. Existing source/model/evidence
  bytes remain unchanged. No learning/compression result or deployable artifact.
- **Verification:** 820 all-extras tests pass on Python 3.11.17/3.12.15, including
  67 new feature/privacy/recall/context/metric-contract tests; base-only checks
  pass 795 with 16 optional skips. Ruff lint/format, strict typing and hooks pass.
  Synthetic metric fixtures are not performance evidence. The reused base/3.12
  environments initially imported older worktrees via duplicate editable `.pth`
  entries; remove only those verified stale paths, confirm the current package,
  and rerun checks. No code/threshold change resolves that environment issue.
- **Final review:** Add the explicit positive initialization-work requirement
  and its negative test; a true initialization flag with zero recorded work
  cannot pass. Rerun all three environments successfully before publication.
  No experiment or acceptance limit is changed by this contract correction.
- **Demonstration:** `inspect_range_feature.py 9h` versus `9d` separates the
  published full-house blocker using `(0,4,0,4)` versus `(4,0,0,4)` prior-mass
  bins. Current priors do not use betting-conditioned weights; the known static
  residual remains intentionally merged in a limitation test.
- **Evidence / stopping point:** [PR #17](https://github.com/jimmy-sim/poker-ai/pull/17),
  [definition/limits](range-mass-representation.md), journal step 20. Stop before
  candidate row-count/compression measurement or learning. Planned 60 full and
  90 sampled snapshots are unrun. Next block builds/runs full admission first;
  no fresh/global/default change. Hosted CI is recorded separately on the PR.
- **Assistance / time:** Codex implements/checks this block. Personal hands-on
  hours are unrecorded; no training wall time exists for this milestone.

## 2026-11-07 — Reachable river distinctions

- **Request / issue:** Continue #4 with missing river distinctions; GitHub and
  journal updates, then a bounded stopping point.
- **Before outcomes:** Fix pinned own inputs, both prefix panels, river-only
  F/G switches and loss accounting, strict reachable conflicts versus ties,
  and three static rank/range probes. See
  [river-distinction-diagnosis.md](river-distinction-diagnosis.md).
- **Definition of done:** Tested diagnosis, all eight prior controls/two seats/
  two panels, complete retained data, native own-profile root checks, concrete
  examples and journal step 19. No new feature, training or global/default change.
- **Implementation checks:** 753 all-extras tests pass on Python 3.11.17 and
  3.12.15, including 20 new river checks; base-only checks pass 728 with 16
  optional skips. Ruff lint/format, strict typing and hooks pass. Tiny fixtures
  cover prefix/sign/hidden-state accounting, probe invariance, receipt guards,
  native values, figures and inspector. Prior source/model/learner bytes unchanged.
- **Raw diagnosis retained:** Clean published `bb5f2cc` completes all eight
  cases in 8.670s. On medium category, responding seat 0's river-only gain is
  0.000006572 chips after the restricted prefix versus 2.717703 chips after the
  exact prefix. Preserve both panels; these are different conditional switches,
  not additive gains. Exact-prefix strict conflicts total 24 across seats;
  static range relations leave 4 original rows unresolved. Concrete examples
  include trips facing straight-making rivers and same-rank card removal.
- **Audit / completed finding:** All 64 own F/G root values pass native
  OpenSpiel expected returns (maximum error 9.94760e-14 chips); own replay zero.
  Audit including replay takes 10.630s. All 32 panel accounting identities pass.
  Medium category exact-prefix conflicts: 24 before probes, 11 after full rank,
  14 after compatibility, 4 after range relations. Restricted-prefix counts are
  19/10/8/4. These are structural counts, not trained-feature gains.
- **Concrete evidence:** Same tens-full-of-nines rank on `9h` versus `9d`, but
  `9d` blocks the declared `9c 9d` quads combo. Some remaining conflicts show
  different action-conditioned opponent weights despite identical static probes;
  causal belief/future-policy contributions were not separately ablated.
- **Evidence / stopping point:** [PR #16](https://github.com/jimmy-sim/poker-ai/pull/16),
  [tables/two figures](../results/river-distinctions/report/tables.md),
  [method/limits](river-distinction-diagnosis.md), journal step 19. Figures visually
  inspected. No feature selection/training/default or global admission change.
  Next proposed block declares one representation and admission design; dependence
  on the known tiny ranges must be explicit. Final hosted CI is reported on PR.
- **Assistance / time:** Codex implements/checks this block. Personal hands-on
  hours are unrecorded; process wall time will be recorded separately.

## 2026-11-07 — Best-response diagnosis of saved controls

- **Scope / issue:** Continue #4 with exact versus same-partition responses and
  additive decision-loss accounting on PR #14's eight saved final controls.
- **Before outcomes:** Publish pinned report/policy config, equations, tie/reach
  conventions, complete-grid and independent root requirements in
  [candidate-best-response.md](candidate-best-response.md). Diagnosis only;
  no feature selection, new training, fresh/global work or default change.
- **Implementation checks:** 733 all-extras tests pass on Python 3.11.17/3.12.15,
  with lint/format/strict mypy/hooks. Twenty-one new checks cover analytic hidden
  information/extra-value examples, random sequential accounting, brute-force
  Kuhn, exact equilibrium zero, recall/reach/ties, retained-input rejection and
  tiny native roots/plot/viewer fixtures. These are software checks, not evidence
  that the failed category candidate improves.
- **Fixture fixes before outcomes:** Retain the native Policy object through
  TabularBestResponse evaluation after a temporary-object lifetime crash; add the
  explicit provenance stub to the tiny native fixture. No retained-case results
  had been produced. Existing source/config/model bytes remain unchanged.
- **Raw diagnosis retained:** Clean published `6699f4c` completes all eight
  saved cases in 4.223s. Medium category epsilon is 2.593658% pot, decomposed
  into 0.000168654% within-partition response gain and 2.593489588% extra exact
  information value. Preserve raw diagnosis/all-info sidecar before native
  audit; interpretation is provisional. Largest additive row is an unmerged
  turn decision, illustrating that this attribution can include the value of
  later response choices, not locate the abstraction error causally.
- **Audit / result:** 32 native exact/restricted response roots and 32 own reply
  profile values pass. Maximum native error 9.94760e-14 chips; own replay zero.
  Audit including replay takes 8.773s. Decision-loss sums match unilateral gains
  and half-summed exploitability. Medium category is near equilibrium within its
  partition, but exact information adds 2.593489588% pot response value. This is
  a fixed-profile comparison, not an irreducible floor or retraining benefit.
- **Hosted optional-dependency failure:** CI run 42354820404 catches direct
  Matplotlib imports in the new renderer during base-only strict typing. Replace
  them with the existing project's lazy optional-import pattern. Preserve the
  initial raw diagnosis/sidecar/audit in `results/saved-replies-initial/`; their
  source freeze requires the historical revision. A fresh clean-source diagnosis
  and audit will be rerun, and a script will compare every nested case field.
  This is an import/typing correction, not a math, input, limit or feature change.
  Base checks pass: 709 tests, 15 optional skips, lint/format/strict typing/hooks.
  All-extras suites again pass 733 on both versions. Add a native-root receipt
  consistency guard and check its mutation fixture on both versions. Final clean
  reproduction/CI were pending at that checkpoint.
- **Final clean reproduction:** Source `e3ab000` completes all eight cases in
  4.163s and native audit including replay in 8.481s, both from clean source.
  All nested cases are numerically identical to the preserved initial run;
  full own-reply/all-info sidecar is byte-identical. All 32 native roots and
  32 own profile values pass again with the same maximum error; own replay zero.
  [Reproduction receipt](../results/saved-replies/reproduction.json). No feature,
  input, failed limit or training outcome was changed by the software fix.
- **Evidence / stopping point:** [PR #15](https://github.com/jimmy-sim/poker-ai/pull/15),
  [tables/two figures](../results/saved-replies/report/tables.md),
  [method/limitations](candidate-best-response.md), journal step 18. Both figures
  visually inspected. Stop before new features/training/global admission; next
  proposed work examines reachable river response disagreements and range/card
  removal distinctions. Final local/hosted checks are recorded separately on PR.
  Personal hands-on time remains unrecorded.
- **Assistance / time:** Codex implements/checks this block. Personal hands-on
  hours are not recorded; actual process time will be recorded separately.

## 2026-11-06 — Collision diagnosis and replacement admission

- **Request / issue:** Continue issue #4 after the texture accuracy failure.
  Diagnose concrete merges using frozen own controls, then define and test one
  replacement candidate before larger sampled/fresh/global work.
- **Before diagnosis outcomes:** Fix the two continuation panels, normalized
  decision weighting, hidden-history aggregation, support/tie handling and local
  sharing-score definition in
  [board-collision-diagnosis.md](board-collision-diagnosis.md). Input report and
  own-policy hashes are fixed in the config. No external solver outputs enter
  the diagnostic or learner.
- **Checks before diagnosis:** 686 tests pass with all extras on Python
  3.11.17/3.12.15, plus lint/format/strict typing/hooks. Ten new tests cover
  hidden-history aggregation, player signs/opponent reach, zero support,
  sharing-score math/self-zero, input retention and the terminal viewer.
- **Initial status:** Diagnostic code was published before retained-case
  results; diagnosis and candidate admission were pending at that checkpoint.
- **Diagnosis:** Clean published `9189c40` produces 7/115 conflicting low/medium
  rows under own exact continuation, versus 4/0 under uniform. Retain both panels.
  One row merges a full house and quads for pocket nines, with opposite preferred
  fold/call actions under the fixed own control. The local score is not game loss.
- **Before candidate outcomes:** Select only texture plus own made-hand-category
  history. Publish its input-bound config and unchanged full accuracy/compression
  targets before implementation/partition measurement. Scope is 48 full snapshots
  and native admission only; no fixed-work sampled/fresh/global comparison here.
- **Candidate implementation checks:** 712 all-extras tests pass on both Python
  versions, including 26 new candidate/admission tests. Optional encoder source
  and a bounded full-control runner/audit/report are published before the trial.
  Existing model/matrix/learner/report dependency bytes remain unchanged.
- **Raw admission retained:** Clean source `f3c28f0` completes all 48 full-control
  snapshots in 9.454s. The candidate passes low but fails medium full accuracy:
  2.593658% pot versus old texture 2.522516%, despite compression (1,428 vs raw
  3,336 rows). Preserve raw outcomes before native audit. No sampled comparison
  or second candidate is launched; confirmation was pending at raw publication.
- **Audit / completed result:** All 48 snapshots pass OpenSpiel 2.0.2 native
  value/BR checks (maximum error 1.27898e-13 chips); own replay error zero.
  Audit takes 5.630s. Medium candidate excess over exact is 2.593476 percentage
  points of pot versus a fixed 0.5 limit. Coverage/recall/compression pass;
  full-control admission fails. Figures/tables preserve the complete grid.
- **Interpretation / stopping point:** Category separates full-house/quads and
  straight/pair examples, but same-category conflicts remain in the retained
  diagnosis. The local proxy does not explain causal game EV loss. Compare
  2.593658% to the old **full-tree** 2.522516%, not the old sampled 7.369742%.
  Stop before sampled/fresh/global training; propose own best-response diagnosis
  of the actual failed policy next. No second candidate or default change.
- **Evidence:** [PR #14](https://github.com/jimmy-sim/poker-ai/pull/14),
  [tables/figures](../results/made-category-admission/report/tables.md),
  [method and limits](board-collision-diagnosis.md), journal step 17. Local
  checks: 712 tests on both Python versions, lint/format/strict typing/hooks;
  final hosted CI is recorded on the PR separately.
- **Assistance / time:** Codex implements and checks this block. Developer
  hands-on time is not recorded. Prior study outcomes/defaults remain unchanged.

## 2026-11-06 — Public-board fixed-work comparison

- **Request / scope:** Continue issue #4 with the unchanged fixed-work protocol,
  GitHub publication, journal updates and a bounded stopping point.
- **Before full outcomes:** Implement runner, collision/work/coverage checks,
  checkpoint replay, native frozen-policy/cross-play audit and offline figures.
  Clarify measurement conventions in
  [public-board-comparison.md](public-board-comparison.md) without changing the
  preregistered config. Tiny test fixtures are not development evidence.
- **Assistance / time:** Codex implements and executes this block. Developer
  hands-on time is not recorded; study runtime is recorded separately.
- **Checks before outcomes:** `make check` passes on Python 3.11.17/3.12.15
  with all optional extras: 676 tests each, lint/format and strict mypy. The 26
  new tests include native checks of a tiny fixture's 20 policies/100 profiles,
  coverage/work/receipt replay, missing-grid rejection and negative-gate retention.
  These fixture outcomes are software checks, not development results.
- **Initial status:** Runner code published before training; full-study results
  were pending at the entry's first publication. No fresh/global training.
- **Hosted fixture failure:** Initial CI on `48051de` fails because the timeout
  unit fixture inherits the optional JIT backend in a base-only environment.
  Correct the test to select NumPy; no learner/source/config/limit change. The
  all-extras local checks had hidden this fixture dependency. Retain the failed
  CI run and verify the base environment before advancing to result admission.
- **Raw grid retained:** Clean training source `48051de` completed all 150 own
  snapshots in 1205.044s, with all ten cells profiled three times. Source/input
  hashes match at completion. Exact controls pass; the texture candidate's raw
  learning gate fails on medium OOP despite meeting the compression requirement.
  Publish complete raw evidence before native audit; interpretation remains
  provisional until those independent checks finish. Test-only fix `3e1d374`
  changes no captured source/script/config; its hosted CI passes both jobs.
- **Audit / result:** All 150 policies, 800 ordered final cross-play profiles
  and 90 checkpoint/visit pairs pass. Native maximum error 1.63425e-13 chips;
  own replay error zero; audit wall time including replay 14.267s. Texture reduces
  raw-public rows 364→92 on low and 3,336→1,392 on medium. Medium sampled median
  7.369742% pot versus raw-public 0.233819%; worst 9.687537%. Full excess over exact
  2.522334 percentage points versus a 0.5 limit. Candidate fails unchanged accuracy
  gates despite passing compression. No result was dropped or retuned.
- **Evidence / limits:** [Tables/figures](../results/public-board/report/tables.md),
  [method and diagnosis](public-board-comparison.md), journal step 16,
  [PR #13](https://github.com/jimmy-sim/poker-ai/pull/13). Canonical keys add no
  row sharing here; all ten representations have zero abstract recall violations.
  Initialized coverage is separated from later sampled rows. Storage counters
  exclude shared tree/container costs; RSS is cumulative. Profiles precede their
  individual learning cells rather than one upfront batch; timings are descriptive.
- **Stopping point:** Bounded comparison and audit complete. Issue #4 stays open
  for a more informative representation; no fresh cases/global training/default
  changes. Final local/hosted quality checks are attached to the PR. Human hands-on
  time remains unrecorded; the study/audit times above are process wall time.

## 2026-11-06 — Public-board protocol and correctness

- **Scope / PR:** Resumed [issue #4](https://github.com/jimmy-sim/poker-ai/issues/4),
  [PR #12](https://github.com/jimmy-sim/poker-ai/pull/12). Stop at optional
  representation code/correctness; no new training or compression study.
- **Before outcomes:** Published protocol/config in `d120490`, fixing five
  controls, the texture candidate, three seeds, node-work thresholds, runtime
  cap and accuracy/compression limits. See
  [public-board-abstraction.md](public-board-abstraction.md).
- **Changes:** Added suit-canonical public boards and a coarse per-street texture
  history, plugged into the finite-game matrix as optional encodings. Kept
  existing keys/defaults. Added a read-only board inspector and journal step 15.
- **Actual verification:** `make check` passes with all optional extras on
  Python 3.11.17 and 3.12.15: 650 tests each, lint/format and strict types.
  Of these, 29 new tests cover board features, symmetry, hidden information,
  original-key compatibility, menus and recall on both development games.
  One additional historical-source regression confirms freeze rejection.
  Hosted CI is separate and attached to the PR.
- **Failure retained / resolved:** The first full run failed because its old
  positive admission test assumed current source matched historical evidence.
  Production rejection stays intact. Gate unit tests now explicitly use matching
  metadata in memory; the historical manifest/report/receipts remain unchanged.
  README/protocol identify the original revision for historical reproduction.
- **Limits / stopping point:** No measured learning benefit or memory reduction.
  Texture deliberately merges public information; canonical public suits do not
  preserve private blocker detail or guarantee equivalence under asymmetric
  ranges. Issue #4 stays open for the fixed-work runner and comparisons.
- **Assistance / time:** Codex implemented, checked and documented this block.
  Developer hands-on time is not recorded. No training experiment wall time.
  Unrelated user experiment outputs are excluded from the branch.

## 2026-11-05 — Fresh validation session

- **Start:** 10:03 Pacific (18:03 UTC), session clock. Resumed issue #3.
- **Prospective scope:** Freeze the ordinary procedure, select new cases by
  published card/position rules, verify the development gate, then retain a
  bounded fixed-work study and independent audit if admitted. Acceptance:
  [fresh-validation.md](fresh-validation.md). No fresh outcomes exist at publication.
- **Before outcomes:** Protocol published in `25e85cc`; runner/admission/selection
  code published in `1fbc9c8` after 26 new tests and 620 full local tests passed,
  plus lint/format/strict typing/hooks. The four structurally selected inputs and
  source/input freeze are published next, before admission or fresh training.
- **Admission:** Cohort/freeze published in `1a86d28`; real gate passes with
  16 final development/control policies replayed and zero own metric error.
  Input/source hashes, unchanged limits and linked native audit are verified.
  [Hosted cohort CI](https://github.com/jimmy-sim/poker-ai/actions/runs/42083487841)
  passed both Python jobs. The admission receipt is committed before fresh training.
- **Fresh result:** Clean `9442bca` completed all 44 sampled/control snapshots in
  499.560s. Raw outcomes/frozen own policies were published in `6e4d3d5` before
  native audit. All four cases pass the unchanged final procedure limits; the
  closest median is 0.9670% of pot against 1%, worst 0.9845% against 2.5%.
- **Independent checks:** All 44 native value/BR comparisons pass within
  8.53e-14 chips; audit wall time 2.450s. Own replay error is zero. All 36 original
  checkpoint/visit hash receipts and work counters were verified. Runtime
  provenance and a separate post-run hardware observation are retained.
- **Coverage/limits:** The medium wet case retains up to 1,545 initial-only rows
  and 94.6657% subsequent uniform-reach coverage, despite passing initialized
  average-row coverage. Four tiny per-case learners do not establish global
  strength or zero-shot play. The old failed hold-out stays failed.
- **Verification / PR:** [#11](https://github.com/jimmy-sim/poker-ai/pull/11);
  620 local all-extras tests passed on both Python versions, with quality checks
  and hooks. Cohort hosted CI passed; final evidence checks are attached to the
  PR. Figures and linked artifact hashes were inspected.
- **User learning:** The developer reports completing the suggested terminal
  commands and getting the expected results. No further mastery or hands-on
  duration is inferred; the report is added to the journal's personal notes.
- **Assistance / time:** Codex prepares and executes the research block.
  Developer hands-on time is not recorded; experiment time is recorded separately.
- **Stopping point:** Fresh procedure validation complete. Ordinary default
  retained. No global training/comparison, new abstraction or extra seed sweep
  was started; representation work remains issue #4.

## 2026-11-04 — Plain-English learning journal

- **Request / issue:** [#9](https://github.com/jimmy-sim/poker-ai/issues/9), create
  one guide to understand the project step by step and keep it current.
- **Change:** Added a retrospective 13-step walkthrough, labeled examples,
  evidence links, glossary, graph-reading help, local commands and optional
  personal-note prompts. It covers the work through the completed issue #2 study.
- **Maintenance:** README/work log link to the journal. Project instructions,
  contribution guidance and PR template require updates with substantive future
  milestones. This does not start experiments or schedule background work.
- **Assistance / time:** Codex drafted the guide from recorded project evidence.
  Developer hands-on time and personal learning progress are not recorded.
- **Verification:** Evidence/relative-link review and ordered-chapter/code-fence
  checks passed. Both suggested test commands passed together (116 tests; the
  sandbox reported an unwritable optional pytest cache). Full local checks passed
  lint/format/strict typing and 594 tests; hooks passed. Hosted CI is attached to
  the PR linked from issue #9. No new research run.

## 2026-11-04 — Issue #2 fixed-work experiment session

- **Start:** 00:17 Pacific (08:17 UTC), from the session clock.
- **Scope:** Resume the unchanged river-integration protocol with a bounded
  frozen-policy panel, fixed-work learning comparisons and a retained report.
  Acceptance is stated in [the experiment document](river-fixed-work.md).
- **Status at session publication:** Runner and experiments pending. No benefit
  of integration has been measured; all four earlier games are development data.
- **PR:** [#8](https://github.com/jimmy-sim/poker-ai/pull/8). The scope was published
  in `9400b71`, checked runner in `aebed7b`, audit/report pipeline in `fb4f04d`
  with optional-dependency/rerun fixes in `a781086`, and full raw outcomes in
  `80ed3f0` before native audit. Real commit dates are preserved.
- **Observed study:** All 80 learning/control policies and 96 frozen seed cells
  retained from clean `aebed7b`; 972.029s study wall time. Native audit took
  3.126s, passed all 80 policies within 9.95e-14 chips; own replay error was zero.
  All 72 original checkpoint/visit receipts and work counters were checked.
- **Finding:** Both variants pass final development limits. Integration has a
  lower final median in one game and higher in three; empirical frozen regret
  MSE times visits is higher in 14/16 cells. Keep the ordinary default. The
  [report](river-fixed-work.md) retains initial-only coverage and unstable
  panel-ratio limitations; no global strength/fresh hold-out claim follows.
- **Verification:** 594 all-extras local tests passed on each of Python 3.11 and
  3.12, with lint/format/strict typing/hooks. Hosted Python jobs passed on
  [pipeline CI](https://github.com/jimmy-sim/poker-ai/actions/runs/41799867893);
  final evidence checks are tracked on PR #8. Plots were visually inspected.
- **Assistance / time:** Codex implements and checks the runner and executes the
  study. Developer hands-on time is not recorded. Experiment and audit wall times
  are recorded separately from assistant session elapsed time.
- **Stopping point:** Bounded fixed-work investigation complete. No fresh games,
  abstraction study, global training or additional seed sweep was started.

## 2026-11-04 — Issue #2 estimator correctness

- **PR:** [#7](https://github.com/jimmy-sim/poker-ai/pull/7), partial progress on
  issue #2. The protocol was published first in `445adc2` on November 3 Pacific.
- **Implementation:** Selected hidden-river chance integration with probability
  weights on updates, deferred target passes, explicit node accounting and
  algorithm-bound checkpoint restoration. Existing ordinary behavior stays tested.
- **Checks observed:** 37 new tests passed. Full Python 3.11 checks passed lint,
  formatting, strict typing and 579 tests with optional extras. Full Python 3.12
  checks also passed 579 tests and strict typing. Targeted `make test-river-sampling`
  passed 44 checks; hooks passed. [Implementation CI](https://github.com/jimmy-sim/poker-ai/actions/runs/41797026396)
  passed both hosted Python jobs; final-head checks are tracked on PR #7.
- **Meaning:** Exact expected-update and continuation checks, not measured variance
  reduction or stronger play. No training/variance panel has run this session.
- **Assistance / time:** Codex implemented and checked the estimator/tests;
  developer hands-on time is not recorded. Session start is recorded below.
- **Stopping point:** Correctness foundation ready for review; fixed-work variance
  and learning experiments remain for the next block. No benchmark was run to
  fill the session, and no strength result is inferred from passing tests.

## 2026-11-03 — Issue #2 protocol and correctness session

- **Start:** 23:50 Pacific (07:50 UTC November 4), from the session clock.
- **Scope:** Resumed [issue #2](https://github.com/jimmy-sim/poker-ai/issues/2)
  for a bounded protocol/correctness block. Training and variance experiments
  remain deferred to the next block.
- **Prospective protocol:** [Study config](../configs/river-integration-study.json)
  and [derivation/acceptance](river-integration.md), committed before outcomes.
  All four previously inspected spots are known development games now.
- **Assistance / time:** Codex prepares the protocol, implementation and tests.
  Developer hands-on time is not recorded; session and process time are separate.
- **Status at protocol publication:** Implementation and correctness checks pending;
  no sampled-training or frozen-policy variance results have been collected.

## 2026-11-03 — Same-day publication preference

- **Request:** Make ongoing contributions visible across the days of actual work.
- **Change:** Recorded same-day publication of coherent checked increments,
  dated PR/work-log updates, and real commit dates in the project instructions.
- **Scope:** Documentation only. Issue #2 remains paused; no training or research
  experiment was started. A daily publishing cadence is not a recurring job.
- **Assistance / time:** Codex updated the instructions from the developer's
  request. Personal hands-on time was not recorded.
- **Verification:** Diff review and documentation formatting checks; hosted CI
  is attached to the PR containing this entry.

## 2026-11-03 — Public development workflow

- **Question:** How can progress be visible and reviewable on GitHub as work happens?
- **Decision:** Publish the existing history as a baseline, then use prospective
  issues, focused branches, PRs, CI and evidence-linked log entries.
- **Implementation:** Added issue forms, a PR template, contribution guidance and
  this log. README links point to live progress and CI.
- **Tracking:** [Publication/workflow issue #1](https://github.com/jimmy-sim/poker-ai/issues/1).
- **Assistance:** Codex prepared repository setup and workflow files. The developer
  selected the public repository and completed account sign-in. This entry does
  not claim personal implementation/review time that was not logged.
- **Hands-on time:** Not recorded.
- **Validation:** Local `make check` passed lint, formatting, strict typing and
  525 tests (8 optional skips). Issue-form YAML and local document links checked.
  Hosted Python 3.11/3.12 jobs passed for the
  [published baseline](https://github.com/jimmy-sim/poker-ai/actions/runs/41746694808)
  and the [initial PR head](https://github.com/jimmy-sim/poker-ai/actions/runs/41746822968).
- **PR:** [#5 — visible development workflow](https://github.com/jimmy-sim/poker-ai/pull/5).
  Later documentation commits receive their own CI; the links above identify
  the exact runs observed when this entry was written.
- **Next:** [Milestone: bounded strength-v3 validation](https://github.com/jimmy-sim/poker-ai/milestone/1)
  contains the prospective estimator, fresh hold-out and abstraction tasks.

## Retrospective baseline: November 2–3, 2026

This index was prepared on November 3. The 82 local commits through `932ea68`
already existed before GitHub publication. Their original history is preserved;
the rows below do not represent historical GitHub issues, reviews or PRs.

| Milestone | Recorded implementation/evidence | Review entry point |
|---|---|---|
| Fundamentals | Cards, five-to-seven-card evaluation, equity, immutable engine | [Phase 1 verification](phase1-verification.md) |
| Exact solvers | Kuhn/Leduc, CFR variants, exact best responses, OpenSpiel comparisons | [Phase 2](phase2-solvers.md) |
| Sampled training | MCCFR, abstraction, checkpoints, bounded limit/no-limit runs | [Phase 3](phase3-verification.md) |
| External comparison | Licensed comparison-only reference and retained strategy gaps | [Solver validation](solver_validation.md) |
| Evaluation | Duplicate deals, uncertainty, bounded public protocol pilot | [Phase 4](phase4-verification.md) |
| Quant extensions | Own Bayesian models and conditional risk analysis | [Phase 5](phase5-verification.md) |
| Learning diagnosis | Four controls, public-board comparison, retained held-out failure | [Hold'em diagnostic](holdem-strength-v2.md) |
| Research packaging | Technical brief, verified claims, actual checks | [Snapshot verification](phase6-verification.md) |

Most implementation and experiment execution was AI-assisted by Codex. Human
hands-on time for this baseline was not recorded. Commit counts and timestamp
spans must not be converted into hours worked.

One measured process interval is available: the full postflop reproduction took
**1668.27 seconds (27.8 minutes) of pipeline wall time**, including training,
independent checks and rendering. Source: the `seconds` field in
[reproduction.json](../results/holdem-learning/reproduction.json). This interval
is not human work time or a CPU-hours measurement and may overlap other activity.
Its actual outcome is `heldout_gate_failed`; passing numerical checks did not
change the preset performance target.

## Template for the next session

```text
Date / issue / PR:
Question or problem:
Decision and reason:
Changes and commit(s):
Commands, actual outcomes and artifact links:
Failure or remaining uncertainty:
AI assistance:
Developer's own review / experiment / learning note:
Hands-on time (recorded, otherwise unknown):
Experiment wall time (source; note overlaps):
Next step:
```
