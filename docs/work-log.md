# Development work log

The dated record of changes, experiments, and checks. For the reasoning in plain
English, read the [learning journal](learning-journal.md); for the current
question, see [issue #4](https://github.com/jimmy-sim/poker-ai/issues/4).
[PRs](https://github.com/jimmy-sim/poker-ai/pulls),
[commits](https://github.com/jimmy-sim/poker-ai/commits/main/), and
[CI](https://github.com/jimmy-sim/poker-ai/actions) contain the associated history.

Dates use America/Los_Angeles unless marked UTC. Entries include AI-assisted
implementation, execution, checks, and writing. Personal hands-on time is recorded
only when reported, separately from experiment runtime. Entries retain their
original context and attribution; an earlier next step may already be complete.
The [contribution workflow](../CONTRIBUTING.md) describes publication.

## 2026-11-28 — Qualify the corrected saved-mixture residual reader

- Review found that first correction `2a49fd46` still called the old source-receipt guard with its new fingerprint. That would make the report fail after qualification because the old measurement receipt must not be rewritten. The active base Python 3.11 suite completed **5,874 passed, 73 skipped, 150 slow deselected** with clean pre/post pins; the next base 3.12 role was intentionally interrupted after 18.659 seconds. Both receipts and logs remain in ignored `results/runs/known-mixture-residual-map-reportfix-source-20261128/`, and no worker survived. The new report-only source uses a separate `report-source-checks` archive while validating every original measurement archive against its published fingerprint. Full requalification and a new hosted check are required before interpretation; the four policy traces will not be rerun. Codex assisted; human time and personal learning were not reported.
- After every own raw file and all 14 own commit blobs were published and byte-verified, the committed own gate passed. The first fixed report launcher stopped in 1.105 seconds **before writing any comparison**: the report reader incorrectly compared PR #118's nested `classification` object to the string `"negative"` and raised `ArithmeticError("fixed published input grid incomplete")`. Its failed job-state/exit/log are retained at ignored `results/runs/known-mixture-residual-map-report-20261128/`. A read-only check confirmed the published nested decision is negative, all eight final parent cases reconcile within `1e-9` chips, and all four published mixed rows are present. This is a report-code schema defect, not a failed poker gate or changed prior evidence. A report-only correction now reads the nested field, adds focused regression tests, and explicitly pins the already published **old measurement-source fingerprint** when verifying source/proof/admission/own archives. The four scientific traces will not run again. Focused tests passed 10, Ruff/format/strict targeted mypy passed; full exact-source local/optional/hosted qualification of this correction is next before any report rerun. Codex assisted; human time and personal learning were not reported.
- After the strict admission was published and all 10 changed blobs matched GitHub bytes, its committed guard passed. The **single** admitted [own read-only trace](../results/known-mixture-residual-map/own/manifest.json) completed all four fixed mixed policies in **84.088 whole seconds** (<900), with maximum process RSS **979,533,824 bytes** (<1.5 billion). Each exact policy produced all 8,340 additive row gains and fixed decision records; each row/street sum matched the already published own exploitability scalar within `1e-9` chips. Mixed turn/river gains in chips are dry A `0.315913/0.222120`, wet A `0.316184/0.240730`, dry B `0.708274/0.156025`, wet B `0.313047/0.251636`. Dry B has the largest total residual (`0.864300` chips) and the frozen turn-dominant label; the other three are split. These are **own-only descriptive traces** against each saved mixed opponent and optimized continuation, not a new strength improvement or causal action swap. No new reference output was used. Next: publish/verify every raw vector, then compute the fixed parent comparisons from already published PR #116 data and issue the one report. Codex assisted; human time and personal learning were not reported.
- After all nine fictional-proof commit blobs were published and matched GitHub bytes, the committed proof gate passed. A **separate data-only** [compute admission](../results/known-mixture-residual-map/admission/manifest.json) rehashed the prior published report clock, rounded 284.162649 seconds upward to 284.163, and recomputed the frozen conservative `2 × 284.163 + 120 = 688.326 < 900`-second bound in 1.039 whole launcher seconds. The 120-second reserve is within the unchanged 900-second own cap; the strict 1.5 GB RSS limit also remains. No real mixed policy or row was opened. Next: publish and byte-verify the admission before the single four-game own trace. Codex assisted; human time and personal learning were not reported.
- After the source receipt at `38acff2e` was published and all 34 changed blobs matched GitHub bytes, its committed publication guard passed. One [fictional-only proof](../results/known-mixture-residual-map/proof/manifest.json) then ran at that exact clean head in 1.086 whole seconds under its 180-second cap. It checked invented row ordering, additive scalar reconciliation, and rejection of a mismatched scalar; `real_policy_opened=false`. The receipt-head hosted CI46126193613 was still running at proof time and is tracked separately. This proof is a software check, not a poker-strength result. Next: publish/verify the proof, then run a separate data-only conservative compute admission before any real mixed row trace. Codex assisted; human time and personal learning were not reported.
- Corrected PR #119 source `3bb3366e` passed full exact-source local base Python 3.11 and 3.12: **5,872 passed, 73 skipped, 150 slow deselected each**, plus Ruff, format, strict mypy and clean pre/post source, prior-evidence, runtime, lock and installed-package guards. Optional 3.11 passed 2,601 tests; optional 3.12 passed 2,599 with two skips, each on the fixed 82-file suite with pre/post guards and pinned OpenSpiel 2.0.2/Apache-2.0 license and Numba checks. All-file hooks passed. [Source-head CI46122565044](https://github.com/jimmy-sim/poker-ai/actions/runs/46122565044) passed both 3.11 shards, full 3.12 and aggregate. The old `8bf2c666` source-head CI was canceled by the correction and remains separately recorded. The complete [source receipt](../results/known-mixture-residual-map/source-checks/manifest.json) retains the first detached runner interruption, old-source passed base311/partially interrupted base312, fictional JSON TypeError, canceled hosted run, two pre-receipt packager import errors, and all corrected passing logs. No real mixed row trace, fictional proof or admission has run. Next: publish and GitHub-byte-verify this source receipt before the one fictional proof. Codex assisted; human time and personal learning were not reported.

## 2026-11-27 — Merge the negative half mixture and register its residual map

- [PR #118](https://github.com/jimmy-sim/poker-ai/pull/118) history-merged as `8145b661` after the final receipt was published and GitHub-byte-verified, receipt-head [CI46117574930](https://github.com/jimmy-sim/poker-ai/actions/runs/46117574930) passed both 3.11 shards, full 3.12 and aggregate, and a solo self-review was posted. The separate [post-merge main CI46119545333](https://github.com/jimmy-sim/poker-ai/actions/runs/46119545333) was still running at this entry; its outcome is not counted as a passed PR check. The scientific classification stays **negative**: all four known mixed policies improved on q8 but failed the fixed `0.01`-pot absolute gate. The old hourly LaunchAgent remains disabled/unloaded, its denial and logs retained, and no research worker was present. Next: save post-merge CI when complete, then follow the separately [preregistered mixed-policy residual map](known-mixture-residual-map.md). Codex assisted; human time and personal learning were not reported.
- The next bounded diagnostic pins PR #118's four newly published mixed policies and PR #116's already published parent row vectors. It fixes a four-trace, 900-second/strict 1.5 GB read-only analysis, exact additive accounting, turn/river and concentration labels, deterministic row ranking, source/proof/admission and publication gates **before any mixed row trace**. PR #117's failed parent diagnosis remains closed with no row result. This protocol can identify a later strength question but cannot itself improve play or claim unseen transfer. Next: publish and verify the protocol, implement isolated adapters, then qualify exact source. Codex assisted; human time and personal learning were not reported.
- The protocol was published on draft [PR #119](https://github.com/jimmy-sim/poker-ai/pull/119) at `0edb30a2` and all five changed blobs were fetched and matched byte for byte. Isolated `scripts/known_mixture_residual_map` adapters now bind those published bytes and prior archives, compute fictional-testable additive summaries, prepare four read-only saved-policy traces and fixed parent comparisons, and retain each completed game or failure. Focused synthetic/pin-only tests passed seven cases before the final added row-selection test; Ruff/format/strict mypy passed the then-current isolated code. **No real mixed-policy row trace, proof or admission has run.** Next: rerun focused checks on the complete source, publish the tested source, then complete all exact-source qualification before any fictional proof or real trace. Codex assisted; human time and personal learning were not reported.
- Protocol-head [CI46120038098](https://github.com/jimmy-sim/poker-ai/actions/runs/46120038098) passed all four hosted jobs; official logs were retained. The first source `8bf2c666` passed eight focused tests, targeted Ruff/format/strict mypy, and pinned commit hooks; all 13 changed blobs were verified after publication. An initial detached full-check runner exited during mypy without a receipt; its partial log remains. A foreground same-source runner then passed base3.11 (5,872 tests, 73 skips, 150 slow deselected, pre/post guards). During base3.12, a separate fictional JSON serialization probe found that `positive_rows` was a NumPy integer and could not be written. The base3.12 pytest child was interrupted at 47%, yielding 2,806 passes/35 skips/150 slow deselected before a **failed role receipt**; no optional role or poker trace started. The exact-source qualification is therefore incomplete, not passed. The synthetic failure log and both interrupted role logs remain in ignored run directories. A small correction converts the count to a Python integer and adds a serialization regression assertion; the corrected source requires complete requalification. PR #118's separate post-merge [main CI46119545333](https://github.com/jimmy-sim/poker-ai/actions/runs/46119545333) passed all four jobs and official JSON/log were retained separately. Codex assisted; human time and personal learning were not reported.

## 2026-11-27 — Prove the fixed half mixture without opening poker policies

- Exact negative-report-head `71b0c62b` [final qualification](../results/known-turn-half-policy-mixture/final-checks/manifest.json) passed serial local base Python 3.11 and 3.12 (5,864 pass/73 skip/150 slow deselected each), optional 3.11 (2,601 pass), optional 3.12 (2,599 pass/two skip), pre/post clean-source/report/runtime/license guards, all-file hooks and hosted [CI46112526107](https://github.com/jimmy-sim/poker-ai/actions/runs/46112526107) on both 3.11 shards, full 3.12 and aggregate. The receipt retains two pre-test launcher failures: an initial background process never started, and a second guard rejected ambient uv 0.13.9 before tests; the pinned 0.13.5 run passed without source or scientific change. The report remains **negative**. Next: publish/verify final receipt, verify receipt-head hosted CI, solo review and history-preserving merge if eligible. Codex assisted; human time and personal learning were not reported.
- The [fixed four-game report](known-turn-half-policy-mixture-result.md) reconciled all published own and independent-audit rows at clean head `06572cdd` in 1.211 whole launcher seconds. The preregistered classification is **negative**: all four mixtures improved relative to q8 by 0.001655–0.006003 initial pots, yet all four exceed the unchanged `0.01`-pot absolute target; dry B is 0.024008. The redundant `0.025` worst check passes and the all-four paired improvement rule passes. This is a known, deterministic, collision-containing restricted-game result with no seed interval or unseen transfer claim. The report provides a rerunnable saved-row command for dry A `2s 9s` on `4c Ks 9d Ts`; that row was already selected in PR #116. Next: publish/verify the report, then final exact-source local/optional/hooks/hosted checks, solo review and history-preserving merge if eligible. No default promotion or scientific retry. Codex assisted; human time and personal learning were not reported.
- After all 17 own-policy/score blobs were published and GitHub-byte-verified, the one pinned OpenSpiel 2.0.2 [comparison-only audit](../results/known-turn-half-policy-mixture/native/manifest.json) checked all four mixed-policy scalars. Maximum independent difference was `7.105427357601002e-15` chips, below the frozen `1e-9` tolerance; the installed Apache-2.0 license SHA-256 matched `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`. Audit internal/whole time was 63.707/103.162 seconds (<900), peak RSS 1,247,379,456 bytes (<1.5 billion). No reference strategy entered training or mixture construction. The own negative signal is independently supported but final classification still awaits the fixed report. Next: publish/verify native evidence, then run that report without changing any gate. Codex assisted; human time and personal learning were not reported.
- The single admitted four-game [own mixture evaluation](../results/known-turn-half-policy-mixture/own/manifest.json) completed once at exact head `b7932de7`, 99.004 whole seconds (<900), peak RSS 1,436,631,040 bytes (<1.5 billion), all 8,340 exact rows per game validated and zero perfect-recall violations. Mixed exploitability fractions of the 36-chip initial pot were dry A `0.014945375951`, wet A `0.015469824468`, dry B `0.024008319616`, wet B `0.015685627214`. All four exceed the frozen `0.01` absolute gate; paired differences from the fixed q8 control are `-0.003299845179`, `-0.001655307608`, `-0.006003467577`, `-0.002210546494` pots. Thus the own-only strength signal is **negative despite four relative improvements**. All four saved mixed policies, scores, event log, source/runtime and partial-safety records are retained; do not treat this as an independently audited final classification. Next: publish and GitHub-byte-verify every own result before the pinned OpenSpiel comparison-only scalar audit. No retry, cap extension or default promotion. Codex assisted; human time and personal learning were not reported.
- After the fictional proof was published and all 12 changed GitHub blobs byte-verified, the separate data-only [compute admission](../results/known-turn-half-policy-mixture/admission/manifest.json) rehashed both pinned PR #116 timing records and recomputed the frozen conservative bounds: own `688.326 < 900` seconds, pinned-reference `886.088 < 900` seconds. It passed in 1.486 whole launcher seconds without opening or scoring a policy. This admits one fixed four-game own evaluation under the unchanged 900-second and strict 1.5 GB caps; it does not imply poker improvement. Next: publish and byte-verify admission before the own run. Codex assisted; human time and personal learning were not reported.
- Jimmy superseded the old November 27 work cutoffs for this active session; the expired hourly LaunchAgent was disabled and unloaded, with its denial and partial closeout logs retained. On PR #118's clean, qualified source receipt at `18d62b17`, the first proof launcher stopped before Python started because the sandbox denied access to the pinned uv cache; its 0.08-second failure remains at `results/runs/known-turn-half-policy-mixture-proof-20261127/`. The unchanged proof then passed with cache access in 4.056 whole seconds, below the fixed 180-second cap. Its [fictional receipt](../results/known-turn-half-policy-mixture/own-proof/manifest.json) checks all 8,340 synthetic rows, the exact 0.5/0.5 arithmetic, and rejection of an invalid parent; `real_policy_opened=false`. This is an implementation proof, not a poker-strength result. Next: publish and byte-verify the proof before the separate data-only compute admission. The issue #4 comment remains pending because no verified issue-targeting write endpoint is available; the rejected PR-number endpoint was not retried. Codex assisted; human time and personal learning were not reported.

## 2026-11-27 — Implement the preregistered half mixture without scoring parents

- Resumed [PR #118](https://github.com/jimmy-sim/poker-ai/pull/118) from its clean prospective commit after verifying remote HEAD and all four protocol-head CI jobs passed. The old GitHub-comment auto-review rejection remains preserved; the available add-comment tool identifies a pull-request number, so issue #4's prospective comment remains pending. Isolated `scripts/` code now pins all eight saved parent hashes, lifts q8 probabilities to exact rows, forms the fixed 50:50 behavior-policy mixture, applies the four-game gates, retains partial failures and separates synthetic proof, data-only compute admission, own scoring, comparison-only OpenSpiel audit and final report. Ten fictional/pin-only focused tests, Ruff, formatting and strict targeted mypy passed; no real mixed policy or score was calculated. Next: publish the tested source, finish exact-source base/optional local and hosted qualification, then follow the frozen proof/admission/own/reference checkpoints only if time and gates permit. Codex assisted; human hands-on time and personal learning were not reported.
- A source review after publication found that own receipts should explicitly include the zero perfect-recall violation count, and the independent audit should enforce the fixed 1.5 GB peak RSS cap. The first exact-source local run was deliberately interrupted during base Python 3.11; its partial log and source identity are retained in ignored `results/runs/known-turn-half-policy-mixture-source-20261127/`. A corrective source checkpoint adds those guards without changing the protocol or calculating an outcome; its full qualification is required anew. The first hosted run is tracked separately and cannot qualify the correction.
- Corrected exact source `73b5e117` passed [source qualification](../results/known-turn-half-policy-mixture/source-checks/manifest.json): base Python 3.11/3.12 each 5,864 passed/73 skipped/150 slow deselected with clean pre/post guards; optional 3.11 passed 2,601; optional 3.12 passed 2,599/two skipped with its pre/post guards on one same-SHA full requalification; all-file hooks and hosted [CI46103378029](https://github.com/jimmy-sim/poker-ai/actions/runs/46103378029) passed both 3.11 shards, full 3.12 and aggregate. The **first full optional3.12 attempt failed** one historical saved-data export test at its unchanged 120-second child watchdog (2,598 other passes/two skips); the isolated same-source test then passed in 5.11 seconds. The failed full log, an initial standalone collection error, stack samples and passing requalification are all retained in the receipt. No test timeout, historical pin, source protocol or poker candidate changed. Source qualification does not supply a poker-strength result. The original 20:00 PST target to stop starting scientific jobs passed before source qualification finished, so proof, admission, own scoring and reference audit were not started in this window; PR #118 remains draft. Next authorized session: verify this receipt and CI, then apply the frozen proof/admission/own-before-reference gates within its own authorized time window. Codex assisted; human time and personal learning were not reported.

## 2026-11-25 — Preregister a known-policy strength mixture

- [PR #117](https://github.com/jimmy-sim/poker-ai/pull/117) closed unmerged after exact-source qualification failed; no row distribution was computed. The new [prospective 50:50 saved-policy mixture protocol](known-turn-half-policy-mixture.md) fixes eight fully published PR #116 final-average snapshots, four already known medium OOP games, exact q8-to-exact lifting, no training or RNG, the q8 comparator, all-four `<=0.01`-pot absolute gate, three-of-four paired rule, 900-second/1.5 GB own cap, separate conservative own/reference forecasts, source/proof/admission gates and own-before-OpenSpiel publication. It tests a genuinely new mixed policy; no mixture or score has been computed. Next: publish/verify this protocol before implementation and any mixture measurement. Codex assisted; human time and personal learning were not reported.

## 2026-11-25 — Qualify the negative conditional-input report

- Receipt-head [CI45583412257](https://github.com/jimmy-sim/poker-ai/actions/runs/45583412257) could not complete its full Python 3.11 job within the unchanged 35-minute limit on two attempts: first stopped at 93% of tests, one targeted same-commit operational requalification stopped at 88%, both before hooks and with no assertion failure visible. Python 3.12 passed first time and was carried forward. Both official logs/metadata are retained in the [CI-layout evidence](../results/known-turn-collision-medium-transfer/ci-layout/manifest.json); the earlier report-head CI passed both jobs. The concrete hosted qualification blocker warrants a CI-only split of the unchanged 302 fast-test files into deterministic, disjoint 151-file Python 3.11 shards. A collection-only check found **3,096 and 2,828 selected nodes** with no overlap and exactly the same 5,924 selected nodes as directory-based `make test` discovery; the 150 marked slow tests remain deselected. Each shard keeps its 35-minute cap, Ruff/format/strict mypy and all-file hooks; an aggregate `Python 3.11` gate requires every shard plus the unchanged full Python 3.12 job. No source, scientific measurement, threshold or budget changed. PR #116 stays draft until all new hosted checks pass. Codex assisted; human hands-on time and personal learning were not reported.
- Exact report-head `8095d0c1` [final qualification](../results/known-turn-collision-medium-transfer/final-checks/manifest.json) passed serial local base Python 3.11/3.12 (5,854 passed, 73 skipped, 150 slow deselected each; Ruff, format, strict mypy) and optional 3.11 (2,601 passed)/3.12 (2,599 passed, 2 skipped), all with pre/post clean-source, archive, lock, runtime, report and optional OpenSpiel-license guards. All-file hooks and hosted [CI45572326397](https://github.com/jimmy-sim/poker-ai/actions/runs/45572326397) passed both versions. The complete receipt retains official hosted logs and two **pre-test operational** launcher failures: sandbox denial of the uv cache write and a short/full HEAD pin mismatch. Both were corrected without changing source, protocol or scientific data; neither reached a test. The report remains **negative** under all four unchanged absolute strength gates. Next: publish/byte-verify the receipt, then receipt-head CI, solo review and history-preserving merge if eligible. Codex assisted; human hands-on time and personal learning were not reported.

## 2026-11-24 — Preregister conditional medium-input turn transfer

- The one fixed [decision report](known-turn-collision-medium-transfer-result.md) completed at clean `9e67420e` in 284.163 launcher seconds. Its [raw archive](../results/known-turn-collision-medium-transfer/report/manifest.json) retains 48 cases, 24 matched checkpoint contrasts and 32 selected exact decision rows. Independent maximum error remains `1.2434497875801753e-14` chips; turn/river row accounting passed. At final 40m average, control/candidate exploitability in initial pots is dry A `0.018245221/0.013575482`, wet A `0.017125132/0.017677381`, dry B `0.030011787/0.020656811`, wet B `0.017896174/0.016751887`. All four candidate absolute `≤0.01` gates fail, so the fixed classification is **negative**, although three relative pairs improve. No retry or default promotion. Next: publish/byte-verify report evidence, then finish exact report-head local/optional/hosted checks and PR review. Codex assisted; human time and personal learning were not reported.
- After every own byte was published and all 107 own checkpoint blobs GitHub-byte-verified, the single pinned [comparison-only OpenSpiel audit](../results/known-turn-collision-medium-transfer/native/manifest.json) checked all 48 saved policy scalars in 381.316 internal/383.043 whole seconds (<900). Maximum own/reference difference was `1.2434497875801753e-14` chips (<`1e-9`); the installed OpenSpiel 2.0.2 Apache-2.0 license SHA-256 was `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`. Its seven-member archive retains every row, installed runtime/license, partial-event log and launcher evidence. No reference output entered training or the score-free selector. Next: publish/verify the audit, then compute the fixed paired, per-street and decision report and classify the still-negative own signal. No retry or default promotion. Codex assisted; human time and personal learning were not reported.
- The one admitted [eight-path own study](../results/known-turn-collision-medium-transfer/own/manifest.json) completed once in 287.409 internal/289.327 launcher seconds (<7,200), with maximum worker RSS 1,100,218,368 bytes (<1.5 billion), no failure, exact paired actual work 40,205,562 at 40m, all 48 registered current/linear-average readouts, policies, masses and event logs saved. **Provisional own-only 40m linear-average** candidate/control exploitability as fractions of the 36-chip initial pot: dry A `0.01357548189783807/0.01824522113017414`, wet A `0.017677380854054372/0.017125132075186154`, dry B `0.02065681123082638/0.030011787192958432`, wet B `0.016751887322440054/0.017896173708394494`. All four candidate absolute values exceed the unchanged `0.01` target; wet A also worsens by `+0.0005522487788682182`. Final average whole coverage is 1.0 for each candidate; post-initial-river coverage is 0.971726/0.940138/0.932466/0.957779 respectively. This is a **negative own-only signal**, not an independently audited final classification. Next: publish and GitHub-byte-verify **all own bytes before** the pinned comparison-only OpenSpiel scalar audit and fixed report. No policy/seed/spot retry, cap extension or default promotion. Codex assisted; human time and personal learning were not reported.
- After all 156 profile checkpoint blobs were published and GitHub-byte-verified, the separate [data-only compute admission](../results/known-turn-collision-medium-transfer/admission/manifest.json) recomputed all 24 saved path timings and the frozen two-worker partition. It recorded `T=800.8661611182278` seconds and strict `2*(2*T+600)=4403.4646444729115 <7200` seconds, status **admitted** in 1.647 whole launcher seconds. This permits exactly one eight-path matched 10m/20m/40m own comparison under the unchanged 7,200-second cap; it says nothing about whether decisions improve. Next: publish/verify admission before starting that single run. Codex assisted; human time and personal learning were not reported.
- The fixed two-worker [24-path profile](../results/known-turn-collision-medium-transfer/profile/manifest.json) completed all eight control/candidate paths three times each at first complete 5m charged-work crossing. Whole launcher time was 301.757 seconds (<900), internal 300.430, maximum worker high-water RSS 1,105,739,776 bytes (<1.5 billion), minimum actual path work 5,058,978. The slowest of three whole-path extrapolations per path yields worker sums 800.866/800.184 seconds and provisional `T=800.866`, strict `2*(2*T+600)=4403.465 <7200` seconds. The 152-member archive retains all 24 paths, snapshots, scores, masses, events, resource/timing records and forecast; no choice among faster repeats. This is a compute measurement, **not the separately published admission or a 40m strength conclusion**. Next: publish/byte-verify every profile member, then run one data-only admission; no longer work before that checkpoint. Codex assisted; human time and personal learning were not reported.
- After the frozen inputs were published and all eight changed blobs verified on GitHub, the one registered [fictional capture/replay proof](../results/known-turn-collision-medium-transfer/own-proof/manifest.json) passed once in 1.372 whole seconds (<180). The two fictional arms reached identical charged work 726 and matching six-policy own readouts each; the 31-member archive retains every policy, score, event, replay and launcher record. It provides no new real-game policy or strength result. Next: publish/byte-verify proof before the 24-path 5m compute profile. Codex assisted; human time and personal learning were not reported.
- After the entire 34-attempt screen archive and all 46 changed blobs were GitHub-byte-verified, the [immutable four-input freeze](../configs/known-turn-collision-medium-transfer-freeze.json) copied only the published first-eligible raw inputs. Fixed dry A/wet A/dry B/wet B boards are `4c Ks 9d Ts`, `7s 9h 6s 2s`, `5c 8s Jh 9c`, `Ad Kc Jd 9s`; private five-combo ranges and weights are in the four linked spot files. Each frozen file SHA-256 equals its selected raw attempt, with no new draw, policy or score. Next: publish/verify the freeze before the fictional proof and measured profile. Codex assisted; human time and personal learning were not reported.
- The one registered [score-free structural screen](../results/known-turn-collision-medium-transfer/screen/manifest.json) completed once from qualified source under its 900-second whole cap: 333.265 internal/334.579 launcher seconds, peak process RSS 847,577,088 bytes (<1.5 billion). All 34 drawn inputs, hashes, board signatures, textures, tree/row/collision counts, events, source/runtime and launcher logs are retained. The first eligible attempts in fixed dry A/wet A/dry B/wet B order were 3/15/1/15, with 18/12/12/24 collided exact acting-turn rows, six/six/six/twelve collided abstract groups, zero river collisions and 133,131 tree nodes each. First-eligible, 49 prior-input exclusions and no-policy/no-score guard replay passed; no policy or strength outcome exists. Next: publish and GitHub-byte-verify every screen record, then freeze only the four selected physical inputs before fictional proof. Codex assisted; human time and personal learning were not reported.
- [PR #116](https://github.com/jimmy-sim/poker-ai/pull/116) published the prospective protocol as `682b5431` before any new board/range draw; [protocol-head CI](https://github.com/jimmy-sim/poker-ai/actions/runs/45554232043) passed both Python jobs. The isolated selection, training, forecast, audit and reporting source at `a96e37fd` passed 31 focused tests, Ruff, strict mypy, all-file hooks and exact-source local base Python 3.11/3.12 (each 5,854 passed, 73 skipped, 150 slow deselected), optional 3.11 (2,601 passed) and optional 3.12 (2,599 passed, two skipped). All 14 changed source/test blobs were verified on GitHub. [Source-head CI](https://github.com/jimmy-sim/poker-ai/actions/runs/45558165765) Python 3.12 passed; Python 3.11 first canceled at its unchanged 35-minute cap at 97% of tests, with the official failure log retained, then a targeted same-SHA requalification passed all 5,854 tests and hooks. The [source receipt](../results/known-turn-collision-medium-transfer/source-checks/manifest.json) retains all local/hosted logs, the canceled attempt and an earlier safely interrupted local source iteration. No selection, proof, profile, training or reference output has been collected. Next: publish/verify this receipt before the one-time score-free structural screen. Codex assisted; human time and personal learning were not reported.
- The [prospective protocol](known-turn-collision-medium-transfer.md) and [machine contract](../configs/known-turn-collision-medium-transfer.json) fix four new medium OOP inputs (two dry, two wet), a score-free first-eligible collision screen, all 49 already inspected config/screened physical inputs as exclusions, unchanged q8 control/exact-turn candidate, deterministic full expected 10m/20m/40m matched work, per-spot historical absolute gates, paired thresholds, 900-second selection/profile/audit caps, 7,200-second own cap, fixed two-worker profile forecast and strict separate admission. PR #107 had zero collisions on its new two-combo inputs and PR #109 stopped at its low/wet structural gate; those failures are retained and no prior screened input is reused. A collision-conditioned cohort can answer only for that selected class, not general board prevalence. No new board, collision, policy or strength result exists at this protocol checkpoint. Next: publish/verify the protocol, then qualify isolated source before any screen. Codex assisted; human time and personal learning were not reported.

## 2026-11-24 — Stop deterministic seed replication before training

- [PR #114](https://github.com/jimmy-sim/poker-ai/pull/114) history-merged as `1f1d4895`; receipt-head and post-merge main CI both passed Python 3.11/3.12 and hooks. No issue #4 worker remained. A read-only [seed preflight](known-turn-seed-replication-preflight.md) traced the unchanged capture path to `medium_dry_full.learning.train`, which fixes `PCG64(0)` and uses full expected traversal. Its only random draw belongs to unused external sampling. All 24 saved checkpoint RNG states equal the unconsumed initial state. Therefore seed labels cannot change the policies; no replication protocol, 40m training or new poker outcome was started. PR #114 remains **negative** because its wet candidate exceeds the frozen 0.01-pot absolute limit. Next: stop; a distinct input-diversity question would require its own prospective protocol and compute gate. Codex assisted; human time and personal learning were not reported.

## 2026-11-24 — Prospective matched-work exact-turn budget

- Final exact-negative-report-head qualification at `73f11326` passed: base Python 3.11/3.12 each 5,841 passed/73 skipped/150 deselected with Ruff, format, strict mypy and pre/post guards; optional 3.11 passed 2,601, optional 3.12 passed 2,599/two skipped with installed reference-license guards. All-file hooks and both [hosted report-head jobs](https://github.com/jimmy-sim/poker-ai/actions/runs/45490979968) passed. The [final receipt](../results/known-turn-work-budget/final-checks/manifest.json) retains all four local logs, hosted log, pins and canceled intermediate CI logs. This qualifies the software and preserves the **negative** wet absolute strength gate; no default promotion or scientific retry. Next: publish/verify this receipt, review PR #114, and history-merge if eligible, then stop. Codex assisted; human time and personal learning were not reported.
- The fixed 24-case/12-pair/42-decision [negative report](known-turn-work-budget-result.md) replayed published own policies and independent scalar audit, then reconciled every exact turn/river row within `1e-9` chips and enforced `−1e-12` nonnegative slack. At 40m wet exact-turn/q8 averages are `0.01004401976136313/0.029353172171235453` pots, dry `0.0013657276180571503/0.008680078498721619`; paired improvements pass, wet descriptive decline passes, but the wet candidate fails the strict `0.01` absolute gate by `0.00004401976136313` pots. The [raw report archive](../results/known-turn-work-budget/report/manifest.json) retains all rows, reaches, alternative values and fixed decisions. Next: publish/verify report, complete final exact-report local/optional/hooks/hosted checks and review; no retry, new experiment or default promotion. Codex assisted; human time and personal learning were not reported.
- After all own blobs were published and remote-byte-verified, the one pinned OpenSpiel 2.0.2 comparison-only audit checked all 24 saved scalar scores in 99.306 whole seconds (<900). Maximum own/reference error was `6.750155989720952e-14` chips (<`1e-9`), with installed Apache-2.0 license SHA-256 `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`. The [native audit](../results/known-turn-work-budget/native/manifest.json) retains all rows, runtime and process evidence. No reference strategy entered training. Next: publish/byte-verify the audit, then build the fixed exact-row/street report and apply the preregistered classification. The own wet candidate remains just above 0.01 pots; no retry or default promotion. Codex assisted; human time and personal learning were not reported.
- The one admitted four-path own study completed once in 105.822 whole seconds (104.127 internal), below the 7200-second cap; max worker RSS 786,169,856 bytes. All 24 current/linear-average policies and their 10m/20m/40m scores, complete masses and event logs are in the [own archive](../results/known-turn-work-budget/own/manifest.json). Historical 10m policy hashes and actual work reproduced exactly, paired work matched, coverage is 1.0 at each final average, and recall violations are zero. Own final 40m linear averages: wet candidate/control `0.01004401976136313/0.029353172171235453` initial pots (paired `−0.019309152409872323`), dry `0.0013657276180571503/0.008680078498721619` (paired `−0.007314350880664468`). The wet own candidate is **above** the fixed 0.01 absolute limit by `0.00004401976136313` pots despite a large decline; this is a provisional own-only negative signal, not a final independently audited classification. Next: publish/byte-verify every own blob before the pinned OpenSpiel comparison-only audit. No retry or default promotion. Codex assisted; human time and personal learning were not reported.
- After all 85 profile/docs blobs were published and GitHub byte-verified, the separate data-only [admission](../results/known-turn-work-budget/admission/manifest.json) recomputed all twelve profile repeats and the fixed worker partition: `T=1018.3167629649444s`, strict `2*(2*T+600)=5273.267051859777s <7200s`, status **admitted** in 1.287 whole-process seconds. This permits exactly one fixed four-path 10m/20m/40m own run under its existing 7200-second cap; it is no poker-strength outcome. Next: publish/byte-verify admission before starting that run. Codex assisted; human time and personal learning were not reported.
- The one fixed 12-path PR #114 profile completed under its 900-second whole cap in 80.961 seconds (79.686 internal), with two workers, three complete first-1m repeats per wet/dry control/candidate path, no failure and peak worker RSS 813,301,760 bytes (<1.5 billion). The [raw profile](../results/known-turn-work-budget/profile/manifest.json) retains every path, work count, snapshot, score and runtime. The slowest-repeat per-path extrapolations produce worker sums 1016.535/1018.317 seconds and provisional strict bound `2*(2*T+600)=5273.267 < 7200`; this is not yet the separate admission. Next: publish/byte-verify all profile bytes, then recompute and publish the data-only admission before any 40m study. Codex assisted; human time and personal learning were not reported.
- After the source receipt was published and its normal-clone guard passed, PR #114's one fictional-only capture/replay proof completed once in 1.275611 whole-process seconds (<180), with two matching synthetic arms and six saved readouts per arm. The [proof archive](../results/known-turn-work-budget/own-proof/manifest.json) retains launcher state, raw readouts, events and logs. It contains no real-game profile or strength measurement. Next: publish/byte-verify proof before the fixed twelve-path 1m profile. Codex assisted; human time and personal learning were not reported.
- [PR #114](https://github.com/jimmy-sim/poker-ai/pull/114) published prospective commit `01b50a3e` with both [protocol-head CI](https://github.com/jimmy-sim/poker-ai/actions/runs/45477168284) jobs passing, then isolated source `674d7836` with all 11 changed blobs byte-verified. Exact-source local base Python 3.11/3.12 each passed 5,841 tests/73 skipped/150 deselected; optional 3.11 passed 2,601, optional 3.12 passed 2,599/two skipped. Full strict mypy (1,061 files), all-file hooks and both [source-head hosted jobs](https://github.com/jimmy-sim/poker-ai/actions/runs/45481961337) passed. The [source receipt](../results/known-turn-work-budget/source-checks/manifest.json) retains the exact logs, pins and an initial ambient-uv commit-hook failure corrected with pinned uv 0.13.5. No profile, trained policy, score or reference output has been collected. Next: publish/verify the source receipt, then run the one fictional proof before any real profile. Codex assisted; human time and personal learning were not reported.
- [PR #113](https://github.com/jimmy-sim/poker-ai/pull/113) history-merged as `91260be0` after both final-receipt hosted jobs passed and solo review; all eight evidence commits remain on main. Its one-shot result remains **inconclusive** and the dry saved-path defect is retained. Post-merge main CI is separately pending. The next [prospective protocol](known-turn-work-budget.md) fixes the original q8 and exact-turn learner, two already known games, PCG64(0) deterministic paths, 10m/20m/40m matched work, frozen known-game gates, source qualification, profile/admission caps and own-before-reference boundaries. No new policy or profile outcome exists at this planning checkpoint. Next: publish/verify the protocol after main CI, then implement isolated source. Codex assisted; human time and personal learning were not reported.

## 2026-11-24 — Prospective saved-policy loss attribution

- Exact report-head `5d9f972b` final qualification passed: local base Python 3.11/3.12 each 5,832 pass/73 skip/150 deselected; optional 3.11 2,601 pass; optional 3.12 2,599 pass/2 skip, with pre/post source/archive/report/runtime/lock/license guards. All-file hooks and [hosted CI45459055154](https://github.com/jimmy-sim/poker-ai/actions/runs/45459055154) passed both versions. One zsh wrapper tried to assign the read-only `status` parameter *after* hooks passed; its failed invocation is retained and the same-head `hook_code` capture exited zero. Intermediate source/proof/admission/raw-head CI was canceled by subsequent mandatory pushes, with official logs retained in the [final receipt](../results/known-turn-loss-attribution/final-checks/manifest.json). Next: publish/verify final receipt, solo review and history-preserving merge if eligible. The scientific classification stays inconclusive. Codex assisted; human time and personal learning were not reported.
- The one admitted read-only PR #113 trace stopped in 43.258 seconds after three of four saved policies. Its immutable [failed raw archive](../results/known-turn-loss-attribution/diagnosis/manifest.json) was published and all 14 GitHub blobs byte-verified before interpretation. The dry candidate was incorrectly mapped to the wet candidate `path00`; the existing mass/source guard rejected it. The [inconclusive report](known-turn-loss-attribution-result.md) retains the complete wet-pair row decomposition and the missing dry result. The protocol stops after this one failed binding gate; no retry or poker-strength conclusion. Next: qualify the failure report, review and close PR #113, then choose a distinct prospective question. Codex assisted; human time and personal learning were not reported.
- A separate data-only [admission](../results/known-turn-loss-attribution/admission/manifest.json) recomputed the pinned conservative bound `2*(59.30096229200717+57.46654349999153)+120 = 353.5350115839974 < 900` seconds and passed in 0.381 whole-process seconds. It read no saved policy and changed no cap. Next: publish/verify its bytes, then run one capped four-policy read-only trace with partial/failure retention. Codex assisted; human time and personal learning were not reported.
- After the published `9dc61036` source archive passed its normal-clone guard and all 27 archive members matched GitHub bytes, the one fictional-only proof passed in 0.385 whole-process seconds (<180) on that clean head. It saved/reloaded an eleven-row synthetic NPZ and checked exact decomposition, positive mass and stable ranking; no poker policy was loaded. The [proof archive](../results/known-turn-loss-attribution/proof/manifest.json) retains inputs, output, process record and log. Next: publish/verify this proof before the separate data-only compute admission. Codex assisted; human time and personal learning were not reported.
- The exact PR #113 source `5aa76bcd` passed all four guarded local lanes: base 3.11/3.12 each 5,832 pass/73 skip/150 deselected; optional 3.11 2,601 pass; optional 3.12 2,599 pass/2 skip, plus all-file hooks. Hosted protocol and source-head Python 3.11 first attempts each reached 96% then hit the unchanged 35-minute limit; each passed one targeted same-SHA rerun, while Python 3.12 passed first attempts. Full failed and successful logs are in the [source receipt](../results/known-turn-loss-attribution/source-checks/manifest.json); no timeout or source pin changed. Next: publish/verify that receipt before the fictional proof, then perform separate admission. No real saved-policy trace has run. Codex assisted; human time and personal learning were not reported.
- The isolated PR #113 source now implements read-only replay of four
  pinned final-average policies, complete exact-row contribution vectors,
  fixed row rankings, partial/failure saves, old-source/archive guards,
  fictional proof and separate data-only admission. Focused Ruff,
  formatting and strict mypy passed; the two new test modules passed
  independently (four/two tests) and together (six), all fictional or
  pin-only. Initial formatting errors, a direct mypy invocation without
  the repository source path, a synthetic floating-point tie failure,
  and one mis-scoped environment invocation are retained in ignored
  iteration logs; no saved-policy trace was run. PR #112's separate
  post-merge main CI was canceled by the next workflow; its official
  logs are retained, while PR #112's report/receipt-head gates passed.
  Protocol-head CI for PR #113 is in progress. Next: complete full
  exact-source local/optional/hooks/hosted qualification before proof.
  Codex assisted; human time and personal learning were not reported.
- [PR #112](https://github.com/jimmy-sim/poker-ai/pull/112) history-merged
  as `4c26fbea` after both receipt-head hosted jobs passed and solo
  review; all evidence commits remain on main. Post-merge main CI is
  running separately. The frozen negative wet/dry result is unchanged.
  The next [prospective diagnostic protocol](known-turn-loss-attribution.md)
  fixes four already published final-average policies at matched work,
  complete exact-row attribution/ranking, a 900-second cap and separate
  data-only admission. It asks whether the wet loss shifted beyond the
  previously diagnosed rows; it starts no training or new outcome at
  protocol publication. Next: publish/verify protocol and hosted CI,
  then isolate source and qualify it. Codex assisted; human time and
  personal learning were not reported.

## 2026-11-24 — Prospective known-turn regret-recency question

- Final exact-report local qualification at `19fb8e49` passed four
  serial lanes with pre/post source/archive/runtime/lock and optional
  OpenSpiel license guards: base Python 3.11/3.12 each 5,826 passed,
  73 skipped, 150 slow deselected; optional 3.11 2,601 passed;
  optional 3.12 2,599 passed and two expected skipped. All-file hooks,
  independent 24-case/12-contrast/23-row report audit and both
  [hosted report-head jobs](https://github.com/jimmy-sim/poker-ai/actions/runs/45414979807)
  passed. The [37-member final receipt](../results/known-turn-regret-recency/final-checks/manifest.json)
  retains official logs and two failed preflight wrappers (wrong new
  proof status, then an overbroad wrapper edit of an unchanged historical
  proof status) before tests; neither changed source or scientific
  results. Next: publish and byte-verify receipt, then solo review and
  history-preserving merge if eligible. Negative classification remains.
  Codex assisted; human time and personal learning were not reported.
- The fixed 24-policy/12-contrast/23-row report completed once in
  57.467/3,600 launcher seconds from published own and native bytes. Its
  [negative report](known-turn-regret-recency-result.md) and
  [raw archive](../results/known-turn-regret-recency/report/manifest.json)
  show wet final candidate 0.047444358 pots versus 0.029805183 control
  (paired +0.017639174), failing both absolute limits and paired
  worsening tolerance. Dry improves to 0.002055024 versus 0.006422763
  (paired −0.004367739). All fixed decisions/readouts are retained.
  Final exact-report qualification remains. No retry or default promotion.
  Codex assisted; human time and personal learning were not reported.
- The complete own archive was published at `b956d838`; all 37 changed
  GitHub blobs and the publication guard passed **before** any reference
  work. The one comparison-only OpenSpiel 2.0.2 scalar audit then checked
  all 12 candidate saved policies in 49.102/900 whole seconds. Maximum
  independent difference was `4.263256414560601e−14` chips versus the
  fixed `1e−9` gate; installed Apache-2.0 license SHA-256 matched the
  pin. The [eight-member native archive](../results/known-turn-regret-recency/native/manifest.json)
  has SHA-256 `2843cb7c32fa1d8a0c753b7a35e2e1567804bb7b1002e0ff743b3368e6341abf`.
  This validates the unfavorable wet own score numerically, without
  changing the frozen negative criterion. Next: publish/byte-verify
  native evidence, then build the fixed 24-policy/card-action report.
  Codex assisted; human time and personal learning were not reported.
- The one admitted two-path own study completed in 45.139/7,200 whole
  seconds on the fixed seed zero. Both paths matched the archived
  controls' final charged work (wet 10,117,956; dry 10,012,410), saved
  all six policies each, replayed, had full whole-average coverage and
  zero recall violations. Wet final linear-average exploitability is
  1.707996887 chips / 0.047444358 initial pots, versus the immutable
  0.029805183 control: paired **+0.017639174 pots** and both frozen
  absolute limits fail. Dry is 0.073980859 chips / 0.002055024 pots
  versus 0.006422763 control, paired −0.004367739 pots. Thus the own
  outcome is **preliminarily negative** despite dry improvement; the
  required pinned scalar audit and fixed report remain. The
  [33-member own archive](../results/known-turn-regret-recency/own/manifest.json)
  SHA-256 is `8b7d3a327d67f5b1c6b2b78e9b819676d86bfb9ec7613477450170caa482c7a9`.
  Next: publish/byte-verify all own bytes **before** comparison-only
  reference work. No retry, new representation or default promotion.
  Codex assisted; human time and personal learning were not reported.
- The [profile archive](../results/known-turn-regret-recency/profile/manifest.json)
  was committed and all 50 changed GitHub blobs and the publication
  guard passed. A **separate data-only admission** recomputed the same
  six-repeat maximum from published bytes in 0.796/180 operational
  seconds: `T = 193.248009`, strict bound `1,972.992036 < 7,200`.
  The [eight-member admission archive](../results/known-turn-regret-recency/admission/manifest.json)
  has manifest SHA-256 `b3bdbd6d1694501c439230fa942577085a6b240c5cbe482e9eb86264d240d3a8`.
  Next: publish and byte-verify admission before the single fixed
  two-path 10m own study. No reference comparison or default decision
  exists. Codex assisted; human time and personal learning were not
  reported.
- The single fixed six-path 1m-work profile completed in 62.400/900
  whole launcher seconds (worker record 61.579 seconds), with wet/dry
  charged crossings 1,065,048/1,022,544 on every repeat. All six saved
  paths replayed and the [46-member archive](../results/known-turn-regret-recency/profile/manifest.json)
  contains their policies, events, state guards, timings and forecast.
  The wet repeat maximum extrapolates to `T = 193.248009` seconds; the
  registered conservative bound is `1,972.992036 < 7,200` seconds.
  This is not admission until the separate data-only step recomputes it
  from published bytes. Manifest SHA-256 is
  `a231a6d8910ead53df36ca7176ccdffd8113bec0c014dac11022ade4c208f282`.
  Next: publish and byte-verify every repeat, then apply the unchanged
  admission rule. Codex assisted; human time and personal learning were
  not reported.
- After the source receipt was committed and all 30 changed GitHub blobs
  verified, its archive publication guard passed. The one registered
  fictional proof then saved six current/linear-average policies at
  80/240/720 visits, final work 726, and replayed every snapshot. Its
  whole launcher used 0.790/180 seconds on the recorded Apple M4.
  The [20-member proof archive](../results/known-turn-regret-recency/own-proof/manifest.json)
  has manifest SHA-256 `3dcb79da6acd30cab61d3d72f8053eb753a44a66dc6b1485c7beba964dd1fc5b`.
  No known-game candidate score exists. Next: publish and byte-verify the
  proof before the six fixed 1m-work profile paths. Codex assisted;
  human time and personal learning were not reported.
- The corrected `3ff86f18` source passed exact-head base Python
  3.11/3.12 (each 5,826 passed, 73 skipped, 150 slow deselected),
  optional 3.11 (2,601 passed), optional 3.12 (2,599 passed, two
  expected skips), pre/post source/archive/runtime/lock/license guards,
  all-file hooks and both [hosted jobs](https://github.com/jimmy-sim/poker-ai/actions/runs/45402269115).
  The [26-member source receipt](../results/known-turn-regret-recency/source-checks/manifest.json)
  retains old-source interrupted/canceled evidence and has manifest
  SHA-256 `b5a54226afda37018a4ee18f7b35e064e6b8e2900d7ded252cd7126cc120e6b8`.
  Its prepublication archive reader correctly refused to count untracked
  files as published; the raw members were verified separately. Next:
  commit, push and byte-verify the receipt, then rerun the publication
  guard before the fictional proof. No candidate poker policy or score
  exists. Codex assisted; human time and personal learning were not
  reported.
- The isolated PR #112 source now implements the fixed signed-regret
  discount, full-work capture/replay, historical-control guards, strict
  profile forecast, comparison-only scalar audit and 24-policy report.
  Fictional/synthetic focused checks passed: Ruff, format, strict mypy and
  ten tests. The report preserves the fixed wet/dry rows, both saved
  readouts and every matched-work contrast. These checks establish code
  behavior, not poker strength; no new known-game candidate was trained
  or scored. Protocol-head hosted CI and full exact-source qualification
  remain separate gates. An independent report-test invocation then exposed
  an import-order defect masked by the ten-test bundle. The exact-source
  base 3.11 lane was interrupted with its partial log retained. The test
  now imports the isolated script path itself; all three new test modules
  pass independently and together. Full source qualification must restart
  on the corrected commit. Codex assisted; human time and personal
  learning were not reported.
- [PR #111](https://github.com/jimmy-sim/poker-ai/pull/111) history-merged as
  `ec9c0d2f` after its diagnostic checks and solo review. Receipt-head
  hosted Python 3.11 first timed out at the unchanged 35-minute limit
  after 96% of tests; its official log is retained, and one targeted
  same-SHA rerun passed. Python 3.12 passed. Separate post-merge main
  [CI](https://github.com/jimmy-sim/poker-ai/actions/runs/45395070401)
  passed both Python versions. The diagnostic gives no strength gain.
- The next [prospective protocol](known-turn-regret-recency.md) fixes one
  asymmetric signed-regret discount on the unchanged exact-turn learner.
  It reuses PR #108/#110's already published controls, trains only one
  new candidate path on each of two **known** games, and fixes work,
  readouts, absolute and paired gates, source qualification, profile,
  strict admission, and own-before-reference order before outcomes.
  No new candidate policy or score exists at this checkpoint. Next:
  publish and byte-verify the protocol, then implement the isolated
  adapter and fictional tests. Codex assisted; human time and personal
  learning were not reported.

## 2026-11-24 — PR #111 final diagnostic qualification

- The [final 30-file receipt](../results/known-wet-residual-diagnosis/final-checks/manifest.json)
  binds the unchanged published diagnostic report to exact commit `70fc7db0`.
  Serial base Python 3.11/3.12 each passed 5,816 tests, 73 skipped and
  150 slow deselected; optional 3.11 passed 2,601 and optional 3.12 passed
  2,599 with two expected skips. All pre/post source, archive, runtime,
  lock and optional license guards, all-file hooks, and both
  [hosted jobs](https://github.com/jimmy-sim/poker-ai/actions/runs/45377664083)
  passed. The receipt includes the independent 12-case/8,340-row audit
  and retained intermediate CI cancellations and check iterations.
  Manifest SHA-256 is `8ceca76ac92bc02e481cac7564d92ab04e4328573d0569590229324fee13ecee`.
  Next: publish and byte-verify this receipt, require receipt-head CI,
  then solo review and history merge. The one known-game result is
  diagnostic only; PR #110's absolute acceptance remains negative.
  Codex assisted; human time and personal learning were not reported.

## 2026-11-24 — PR #111 one saved-policy residual diagnosis

- The single admitted read-only replay completed all 12 fixed policies
  and selected 20 exact decision rows in 59.30/900 seconds at clean
  admission HEAD `b55dce91`; its [raw archive](../results/known-wet-residual-diagnosis/diagnosis/manifest.json)
  and [report](known-wet-residual-diagnosis-result.md) retain every case,
  event and contribution vector. Candidate final-average top-ten turn
  rows account for 0.766113/0.804478 chips (95.23%) of turn gain:
  **concentrated** under the fixed 50% rule. Top-ten river rows account
  for 0.013856/0.268508 chips (5.16%): **diffuse**. Two seat-one turn
  hands, `3d 5c` and `2d 5d` on `Qs Kd As 3c`, account for 71.38% of
  candidate turn gain; their local action values assume their saved
  opponent and optimized continuation. All 12 exact sums agree with
  saved scores within 7.11e−14 chips; prior native scalar difference
  is at most 1.95e−14 versus the 1e−9 gate. This is a diagnosis on one
  already known game, not a stronger policy or unseen result. PR #110
  remains negative. Next: publish/byte-verify raw and report, then full
  exact-report local/optional/hooks/hosted qualification, review and
  history merge. Codex assisted; human time and personal learning were
  not reported.

## 2026-11-24 — PR #111 separate read-only compute admission

- After the fictional proof was published and its 15 changed GitHub
  blobs verified, the [six-member admission archive](../results/known-wet-residual-diagnosis/admission/manifest.json)
  recomputed `2 × 68.30351770902053 + 120 ≈ 256.607` seconds from the
  pinned parent report job state, strictly below the unchanged 900-second
  whole-diagnostic cap. The data-only run took 1.25 seconds under its
  own 180-second launcher cap, used pinned `uv` 0.13.5 and read no
  saved policy decision. Its manifest SHA-256 is
  `36df155246d35043e4427a05c9a308a8a0f23fe7b07f37d61e9d05e1d6e2b071`.
  The intermediate source-receipt-head CI was canceled by proof
  publication; its official metadata/logs are retained separately, while
  both required exact-source-head hosted jobs passed. Next: publish and
  byte-verify admission before the one 900-second read-only diagnosis.
  Codex assisted; human time and personal learning were not reported.

## 2026-11-24 — PR #111 fictional proof before diagnosis

- The [11-member fictional proof archive](../results/known-wet-residual-diagnosis/proof/manifest.json)
  contains a synthetic 24-row ranking/additivity result, the guarded
  1.13-second run under its 180-second cap, and the first retained
  preflight failure. That first launcher exited before the proof because
  it found `uv` 0.13.9 rather than required 0.13.5. The corrected
  launcher used the pinned toolchain; neither attempt read saved poker
  policy outcomes. The proof manifest SHA-256 is
  `b5b054f554eaa5277231761aa68c5dcda028681af968dec198875aab5c8fe401`.
  Next: publish and byte-verify the proof archive, then separately
  compute and publish the fixed conservative admission before any real
  candidate-ranked trace. Codex assisted; human time and personal
  learning were not reported.

## 2026-11-24 — PR #111 exact-source qualification

- The [20-member source receipt](../results/known-wet-residual-diagnosis/source-checks/manifest.json)
  binds isolated tracer commit `b86a992e`, fingerprint
  `4901950e9b49d2f8e383152e67dba06f82b70a486db19905b9e810fdd67ff2d3`,
  four complete local lanes, exact-head all-file hooks and both passing
  [source-head hosted jobs](https://github.com/jimmy-sim/poker-ai/actions/runs/45370824410).
  Base Python 3.11/3.12 each passed 5,816 tests, skipped 73 and deselected
  150 slow tests; optional 3.11 passed 2,601 and optional 3.12 passed 2,599
  with two skips. Pre/post historical archive, source, lock, runtime and
  installed license guards passed. The manifest SHA-256 is
  `b3c9618f1a959fd3c756f9a18ba8798d09bfd4bd60fc6c2c5ede00df29ef0920`.
  Source and all ten changed GitHub blobs were verified before the hosted
  check. No real saved-policy trace or proof was run. Next: publish and
  byte-verify this receipt, then run the single fictional proof and
  separate data-only admission before any real diagnosis. Codex assisted;
  human time and personal learning were not reported.

## 2026-11-24 — PR #111 isolated residual tracer under qualification

- The new `known_wet_residual` adapters replay only the 12 pinned
  [PR #110 policies](../results/known-wet-turn-mechanism/own/manifest.json).
  They select candidate-final-average top-ten exact rows per street
  before loading the control trace, retain each case and event, and
  reconcile full additive gains to the published scalar and street
  totals. A separate fictional proof and data-only admission precede
  any real saved-policy diagnosis. Four focused Python 3.11 tests,
  Ruff and strict mypy pass. The first lint/type iteration and a
  synthetic-fixture test failure are retained in ignored
  `results/runs/known-wet-residual-source-20261124/iteration-failures.md`;
  neither involved a policy outcome. Full exact-source local/optional,
  hooks and hosted qualification remain pending. Codex assisted;
  human time and personal learning were not reported.

## 2026-11-24 — Prospective known-wet residual diagnosis

- After [PR #110](https://github.com/jimmy-sim/poker-ai/pull/110)
  history-merged with negative absolute acceptance and both receipt-head
  hosted jobs passing, the next [prospective protocol](known-wet-residual-diagnosis.md)
  fixes one read-only question before any new candidate-ranked trace.
  It binds all 12 published known-game policies, both readouts, all three
  work labels, candidate-final-average top-ten turn and top-ten river row
  rules, exact trace identities, a separate conservative forecast and
  one 900-second cap. The candidate has exact acting turn and river keys
  on a turn-start game, so this cannot test flop grouping or unseen
  transfer. No new ranking, training or reference work has occurred at
  publication. Post-merge main CI for PR #110 is tracked separately.
  Codex assisted; human time and personal learning were not reported.

## 2026-11-24 — PR #110 exact-report qualification

- The [final check receipt](../results/known-wet-turn-mechanism/final-checks/manifest.json)
  binds report HEAD `690723db`, unchanged source fingerprint, seven prior
  evidence stages, four exact-head local lanes, all-file hooks and both
  [report-head hosted jobs](https://github.com/jimmy-sim/poker-ai/actions/runs/45345593711).
  Base Python 3.11/3.12 each passed 5,812 tests, skipped 73 and deselected
  150 slow tests; optional Python 3.11 passed 2,597, and optional Python
  3.12 passed 2,595 with two skips. All pre/post source, archive, runtime,
  lock and license guards passed. The final receipt has 19 hashed files;
  its manifest SHA-256 is
  `d95cba42bfc9ee90974572b31e450bcdac6f8f8229b205ad20de6fb57c7b3aca`.
  The independent scientific classification remains **negative** because
  the candidate missed both frozen absolute exploitability gates despite
  its paired improvement. Next: publish and byte-verify this receipt,
  require receipt-head hosted CI, then solo review and history-preserving
  merge if eligible. Codex assisted; human time and personal learning were
  not reported.

## 2026-11-23 — PR #110 fixed report: negative acceptance

- The [fixed report](known-wet-turn-mechanism-result.md) and
  [machine evidence](../results/known-wet-turn-mechanism/report/report.json)
  classify the one known medium/wet game **negative** under the frozen
  absolute gates. The candidate's final average is 1.0729866053 chips
  (0.0298051835 initial pots) versus control 2.2264918915 chips
  (0.061846997 pots); the −1.1535052863-chip paired gain is real within
  this restricted game, but candidate misses ≤0.01 final and ≤0.025
  worst gates. Final additive turn/river gains fall from
  1.681914/0.544578 control to 0.804478/0.268508 candidate chips.
  The report retains six both-readout paired contrasts and eight fixed
  exact decision rows, including turn `2d 5d` on `Qs Kd As 3c` and
  river `3d 5c` on `Qs Kd As 3c 3h`. Each local action value uses its
  saved opponent and optimized continuation; it is not general advice.
  Native scalar error was ≤1.9539925233402755e−14 chips. One known
  input/seed gives no transfer or confidence claim; no default change.
  The report archive is built; final exact-report local/optional/hosted
  qualification remains pending before review/merge. Codex assisted;
  human time and personal learning were not reported.

## 2026-11-23 — PR #110 pinned scalar audit

- After own policies/scores were published and all 35 changed GitHub
  blobs verified, the single comparison-only OpenSpiel 2.0.2 audit
  checked all 12 saved scalar cases in 85.16/900 seconds. Its maximum
  absolute own/reference error was `1.9539925233402755e−14` chips,
  below the fixed `1e−9` tolerance. Installed Apache-2.0 license SHA
  `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`
  matched the pin. The [eight-file native archive](../results/known-wet-turn-mechanism/native/manifest.json)
  retains every scalar and runtime record; reference policies never
  entered training. This validates the saved own scores but does not
  reverse the candidate's negative absolute gate. Next: publish/verify
  native evidence, then build the fixed report and representative
  decisions from published bytes. Codex assisted; human time and
  personal learning were not reported.

## 2026-11-23 — PR #110 one fixed own policy pair

- The sole admitted two-worker control/candidate run completed in
  48.32/7,200 seconds from published admission `a3974b40`, deterministic
  seed zero, both paths at 10,117,956 charged nodes with all six
  captures/path and zero recall violations. The complete
  [own archive](../results/known-wet-turn-mechanism/own/manifest.json)
  retains policies, own scores, positive-average reach masses, events,
  timing and worker peak RSS. Final linear-average exact restricted-game
  exploitability was 2.2264918915 chips (0.061846997 initial pots) for
  q8 control and 1.0729866053 chips (0.0298051835 pots) for exact-turn
  candidate, a paired candidate-minus-control difference of
  −1.1535052863 chips (−0.0320418135 pots). Both paths have whole
  positive-average coverage 1.0; candidate post-initial-river coverage
  is 0.8554558 versus control 0.9038961. The candidate **fails** its
  frozen final ≤0.01-pot and worst ≤0.025-pot absolute gates despite
  the paired gain: provisional classification **negative**, pending
  independent scalar audit of all 12 saved policies. This one known
  game/seed does not establish generalization or confidence. No reference
  output has been read or loaded. Next: publish and GitHub-byte-verify
  all own bytes before comparison-only OpenSpiel. Codex assisted; human
  time and personal learning were not reported.

## 2026-11-23 — PR #110 strict compute admission

- The separate data-only gate recomputed the published profile exactly,
  using the larger of both three-repeat maxima `T=209.06137525266`
  seconds. Its strict bound `2*(2*T+600)=2,036.24550101064<7,200`
  seconds **admitted** one fixed two-path 10m-work own comparison;
  the [eight-file admission receipt](../results/known-wet-turn-mechanism/admission/manifest.json)
  binds the published profile, source and 0.73-second launcher. This is
  compute admission, not a strength claim. No own long policy or reference
  comparison has started. Next: publish and GitHub-byte-verify the
  admission before one capped own pair. Codex assisted; human time and
  personal learning were not reported.

## 2026-11-23 — PR #110 fixed six-path profile

- The one published-proof profile ran both fixed arms three times each to
  first complete 1m-work crossing: every path reached 1,065,048 charged
  work, and the whole launcher took 66.32/900 seconds. The six complete
  own captures/replays and raw worker logs are in the
  [45-file profile archive](../results/known-wet-turn-mechanism/profile/manifest.json).
  Worst per-arm `whole_path_seconds × 10m / actual_work` estimates were
  209.06 seconds (q8 control) and 207.41 seconds (exact-turn candidate),
  with worker peak RSS up to 1,079,164,928 bytes. The recorded formula
  computes `2*(2*T+600)=2,036.25<7,200` seconds; **separate data-only
  admission remains pending**. The profile's 1m policies are prescribed
  partial evidence, not final acceptance or a seed replication. Next:
  publish/verify the profile and run the independent strict admission.
  Codex assisted; human time and personal learning were not reported.

## 2026-11-23 — PR #110 corrected exact source qualified

- Corrected source `c137d828` passed exact-source local base Python
  3.11/3.12 (each 5,812 passed, 73 skipped, 150 slow deselected), optional
  3.11 (2,597 passed), optional 3.12 (2,595 passed, two expected skips),
  all pre/post historical source/archive/runtime/lock/license guards and
  all-file hooks. Both corrected source-head
  [hosted jobs](https://github.com/jimmy-sim/poker-ai/actions/runs/45339987008)
  passed. The [20-file source receipt](../results/known-wet-turn-mechanism/source-checks/manifest.json)
  binds tested HEAD, fingerprint, local and hosted evidence. The first
  source-head [CI run](https://github.com/jimmy-sim/poker-ai/actions/runs/45333730045)
  also passed but is retained separately as superseded by the report
  correction. No proof, profile, training, score or reference comparison
  has run. Next: publish and byte-verify the source receipt, then run the
  frozen fictional proof. The one published-source fictional proof then
  passed at HEAD `1b719048`: 0.80 seconds under the 180-second cap,
  six readouts per arm, identical paired scores and final charged work
  726. Its [32-file archive](../results/known-wet-turn-mechanism/own-proof/manifest.json)
  is a software/math check, not a poker-strength result; profile and
  compute admission remain pending. Codex assisted; human time and
  personal learning were not reported.

## 2026-11-23 — PR #110 report readout correction before policies

- The first tested source `2b937eaa` passed all four exact-source local
  base/optional lanes and hooks; its hosted source-head run was still active.
  A read-only source review then found that the copied decision report
  displayed ranked rows only for linear-average policies, although the
  protocol saves both current and average readouts at every crossing.
  Before any proof, profile or policy run, the isolated report now computes
  street contributions, matched-work contrasts and the same ranked decision
  rows for **both** readouts. A focused duplicate/missing pair regression
  was added. Six focused tests and targeted Ruff, formatting and strict
  mypy passed. The first source check is retained as superseded; the
  corrected source requires all local/optional/hosted checks again before
  admission. No scientific outcome has been collected. Codex assisted;
  human time and personal learning were not reported.

## 2026-11-23 — PR #110 isolated known-wet source under qualification

- Added an isolated one-game runner, source guard, compute forecast, comparison-only
  audit, report and regression tests for the published
  [known-wet protocol](known-wet-turn-mechanism.md). Historical source modules,
  pins, policies and results are unchanged. The first focused test run exposed an
  incorrect copied parent receipt hash in the new adapter; that implementation
  defect was corrected using the published source receipt. A second focused run
  exposed a test-only street parser error; it was corrected without measuring
  a policy outcome. Focused five tests now pass, including exact game/chance
  identity and six collided q8 turn groups covering 12 exact rows; targeted
  Ruff and strict mypy pass. Full exact-source local/optional/hosted
  qualification remains pending. No PR #110 proof, profile, admission or
  policy trajectory has started. Codex assisted; human time and personal
  learning were not reported.

## 2026-11-23 — PR #109 merged; one known wet-game question registered

- [PR #109](https://github.com/jimmy-sim/poker-ai/pull/109) was
  history-merged at `66ec5a9d` after both receipt-head hosted jobs passed
  and the solo diff/evidence review. All six research checkpoint commits
  remain ancestors of main; post-merge main CI is tracked separately.
  Its three-stratum collision-conditioned comparison remains
  **inconclusive by structural stop**, with no policy or default change.
- The distinct [prospective known-wet protocol](known-wet-turn-mechanism.md)
  fixes PR #109's already structurally inspected first-eligible
  `Qs Kd As 3c` medium/wet OOP input, unchanged q8/exact-turn arms,
  deterministic seed zero, 100k/1m/10m matched charged work, historical
  absolute and paired gates, proof/profile/separate strict compute
  admission, own-before-reference publication and hard caps. The question
  is whether this one known wet game's decisions improve; it does not
  replace the failed third stratum or establish population transfer. No
  policy outcome for this input exists at protocol publication. Next:
  publish/verify the plan before isolated implementation or any training.
  Codex assisted; human time/personal learning were not reported.

## 2026-11-23 — PR #109 final exact-report qualification

- On the published structural-stop report HEAD `cc8a310f`, exact-source
  local base Python 3.11/3.12 each passed 5,806 tests (73 skipped, 150
  slow deselected) with lint, format, strict typing and pre/post historical
  source/archive/runtime/lock guards. Optional 3.11 passed 2,597;
  optional 3.12 passed 2,595 with two expected skips and pinned
  OpenSpiel/Numba/license guards. Exact-head all-file hooks and both
  [hosted jobs](https://github.com/jimmy-sim/poker-ai/actions/runs/45317245286)
  passed. The earlier intermediate receipt-head CI was canceled by the
  report push and its official logs are retained separately. The
  [21-file final receipt](../results/turn-collision-transfer/final-checks/manifest.json)
  binds the unchanged source, full raw structural stop, report and exact
  check logs. No policy or score was collected. Next: publish/verify the
  final receipt, await receipt-head hosted CI, finish solo review and
  history-preserving merge if eligible. Codex assisted; human time or
  personal learning were not reported.

## 2026-11-23 — PR #109 one-time structural stop

- On published qualified selector HEAD `5019cf1e`, the one permitted
  PCG64(20261624) score-free screen saved all 25 candidate inputs and 50
  ordered draw/screen events. Medium/dry OOP first qualified at attempt 3
  with 12 collided exact turn rows; medium/wet OOP at attempt 2 with 12.
  Low/wet IP exhausted all 20 attempts, maximum two collided rows versus
  the frozen minimum four. The [audited raw archive](../results/turn-collision-transfer/screen/manifest.json)
  binds the clean source, every input and event, predeclared caps, and
  launcher. Internal selection took 78.6751 seconds; whole launcher
  123.2653/900 seconds on Apple M4. The first unpublished archive verifier
  had a relative-root path mistake; its partial package and correction are
  retained ignored under `results/runs/turn-collision-transfer-screen-launch-20261123/`.
  The [result report](turn-collision-transfer-result.md) classifies poker
  strength **inconclusive by structural stop**: no freeze, training,
  exploitability score, reference comparison or default change. Next:
  publish/verify the complete raw stop, finish applicable final checks and
  review, then design a distinct prospective question without changing this
  failed three-stratum rule. Codex assisted; human time/personal learning
  were not reported.

## 2026-11-23 — PR #109 corrected selector source qualified

- Corrected selector HEAD `6d43f62a` passed exact-source base Python 3.11/3.12
  (5,806 tests each, 73 skipped, 150 slow deselected), optional 3.11
  (2,597 passed), and [hosted Python 3.11/3.12](https://github.com/jimmy-sim/poker-ai/actions/runs/45306928141).
  Optional 3.12 first failed one **existing** saved-profile regression's
  unchanged 120-second child watchdog after 2,594 passed/two skipped. Its
  focused same-environment test passed in 5.35 seconds; one full same-source
  operational recheck passed 2,595/two skipped with pre/post guards. The first
  failure, collection-only diagnostic, and complete recheck remain separately
  in the [source receipt](../results/turn-collision-transfer/selection-source-checks/manifest.json).
  All-file hooks passed. A first receipt packager attempt stopped on a
  misnamed ignored diagnostic script before manifest creation; that partial
  attempt is retained under ignored `results/runs/turn-collision-transfer-source-requal-20261123/`.
  No cohort board, tree, collision, policy or score has been measured. Next:
  publish and byte-verify the source receipt, then run the one registered
  structural screen within its cap. Codex assisted; human time or personal
  learning was not reported.

## 2026-11-23 — PR #109 source qualification correction

- First published selector source `437190f` failed hosted Python 3.12
  strict mypy on a **synthetic test-only** NumPy `~turn` expression; no
  selector, tree, policy or score ran. The existing local base311 role was
  stopped early and its partial log/driver state retained. A new test-only
  explicit Boolean array plus `np.logical_not` passes all seven focused
  tests and strict mypy under pinned Python 3.11/3.12. The failed hosted
  log and partial local check remain in ignored persistent
  `results/runs/turn-collision-transfer-source-20261123/` for the source
  receipt. Next: publish the corrected tested source, run all required
  exact-source roles and hosted jobs again, and do not screen a cohort
  until they pass. Codex assisted; human time/learning not reported.

## 2026-11-23 — PR #109 isolated one-time selector source

- An isolated score-free selector now binds the published protocol, all 24
  prior spot hashes, parent source and one-time output paths. It draws five
  private combos per seat, counts only structural turn-key collisions,
  flushes each raw candidate before inspecting its tree, and retains every
  screened attempt. Its freeze reader checks every saved candidate and
  first-eligible order; source pin, timeout and no-replacement guards
  remain. Seven synthetic/contract tests, focused Ruff/format and strict
  mypy passed. Initial test import and style/type iteration failures are
  retained under ignored `results/runs/turn-collision-transfer-source-20261123/`.
  No registered board, tree, collision, policy or score has been measured.
  Next: publish/byte-verify tested selector source, then complete exact-source
  qualification before the one-time screen. Codex assisted; human time or
  learning was not reported.

## 2026-11-23 — PR #108 merge and next prospective question

- [PR #108](https://github.com/jimmy-sim/poker-ai/pull/108) was
  history-merged at `71ab64fa` after both exact receipt-head hosted jobs
  passed, solo review and clean merge status. All research checkpoint
  commits remain ancestors of main; post-merge main CI is tracked
  separately. The positive result is restricted to one known finite game,
  with no default promotion. The next [prospective protocol](turn-collision-transfer.md)
  asks whether the unchanged exact-turn representation improves new
  collision-conditioned card/range inputs under matched work. It fixes a
  first-eligible, bounded structural screen across three varied strata and
  excludes 24 prior inputs; screening uses no policy score. The protocol
  and machine contract were written before any new board, tree, collision,
  policy or score measurement. Next: publish/verify the plan, then build
  and check isolated selection source before its one-time screen. Codex
  assisted; human time/learning not reported.

## 2026-11-23 — PR #108 final exact-report qualification

- On report commit `d9df778a`, serial local base 3.11/3.12 each passed
  5,799 tests, 73 skipped and 150 slow deselected with lint, format,
  strict mypy and pre/post source/archive/runtime/lock guards. Optional
  3.11 passed 2,597 and optional 3.12 passed 2,595 with two expected
  skips; both pinned OpenSpiel, Numba and license guards passed.
  All-file hooks and both [hosted jobs](https://github.com/jimmy-sim/poker-ai/actions/runs/45294831863)
  passed. The first local wrapper failed before tests on a mistaken proof
  status string; its failed log/receipt/wrapper are retained with the
  corrected full run in the [final check receipt](../results/known-turn-exact-mechanism/final-checks/manifest.json).
  No scientific code, protocol or outcome changed. Next: publish/verify
  this receipt, solo review and history merge if eligible. Codex assisted;
  human time or learning was not reported.

## 2026-11-23 — PR #108 fixed known-game report

- The fixed [decision report](known-turn-exact-mechanism-result.md) replayed
  all 12 published own policies and the published independent scalar audit.
  The frozen rule classifies the one known As Jc 5d 3h seed-zero pair
  **positive**: candidate 0.006422763 versus control 0.025118161 initial
  pots at matched 10,012,410 charged work, paired −0.018695397 pots;
  candidate passes both absolute gates, whole coverage 1.000 and recall
  zero. Final additive turn loss is 0.151366 versus control 0.861096 chips;
  candidate river loss is 0.079854 versus control 0.043158 chips. Seven
  fixed/control-ranked decision rows retain cards, actions, probabilities,
  reach and local values. One known input/seed has no transfer or seed
  uncertainty claim. The first report invocation stopped at shell
  redirection before Python started; its preflight correction is retained.
  Next: publish/verify report, run final exact-source local/optional/hooks
  and hosted checks, then review PR #108. No default promotion. Codex
  assisted; human time/learning not reported.

## 2026-11-23 — PR #108 pinned scalar audit

- After the complete own archive was published and byte-verified, the one
  registered comparison-only OpenSpiel 2.0.2 audit checked all 12 saved
  policies at 100k/1m/10m work, current and linear average. Maximum
  independent scalar error was `4.263256414560601e-14` chips versus the
  `1e-9` gate. Internal time was 12.185 seconds; the launcher took 12.902
  seconds under the 900-second cap. Installed Apache-2.0 license hash and
  every row, PID and log are retained in the [native archive](../results/known-turn-exact-mechanism/native/manifest.json).
  A prelaunch expected-HEAD typo was corrected before any audit worker or
  output existed and is recorded there. Reference strategies did not enter
  training. Next: publish/verify this audit, then run the fixed decision
  report from published bytes. Codex assisted; human time or learning was
  not reported.

## 2026-11-23 — PR #107 closure and known-case turn protocol

- [PR #107](https://github.com/jimmy-sim/poker-ai/pull/107) was history-merged
  as `e147802c8c2ecefbe7722a793d0c34169c118f6b` after solo review,
  four exact-source local lanes, hooks and both receipt-head hosted jobs.
  The first Python 3.11 job canceled at the unchanged 35-minute cap after
  96% of pytest, without a preceding test failure. The failed metadata/log
  remain under ignored persistent
  `results/runs/turn-exact-transfer-receipt-ci-20261123/`; one targeted
  same-SHA Python 3.11 operational requalification passed 5,795 tests,
  73 skipped, 150 deselected and hooks in 24m24s. Python 3.12 passed.
  [Post-merge main CI 45283536151](https://github.com/jimmy-sim/poker-ai/actions/runs/45283536151)
  is separately pending at this entry. The one structural inventory ended
  the scientific comparison **inconclusive for poker strength** before
  training because all three selected new inputs had zero turn collisions.
  No outcome, seed, input or cap was changed and no default promoted.
  Codex assisted; human time or personal learning was not reported.

- The distinct [known-case prospective protocol](known-turn-exact-mechanism.md)
  fixes the already evaluated As Jc 5d 3h medium/dry input with 12 turn
  collisions, a same-work q8 control and exact-turn candidate, deterministic
  seed zero, 100k/1m/10m checkpoints, historical absolute and paired gates,
  six-path profile, strict conservative admission, 7,200-second own cap and
  own-before-reference boundary. It is a mechanism test on **one known
  game**, not a new holdout or generalization test. The PR #107 source and
  old result files remain pinned. No new game-tree, policy, profile or
  score measurement existed at this protocol checkpoint. Codex assisted;
  human time or personal learning was not reported.

- PR #108's isolated runner, source/archive guards, strict two-worker
  forecast, comparison-only scalar audit, fixed report and synthetic
  no-collision regression were implemented without changing PR #107 or
  historical pinned files. Four new focused tests and 24 inherited full-pass
  and exact-turn tests passed together (28 total); Ruff lint/format passed
  all project files and strict mypy passed 1,004 source files. The first
  unformatted source and missing test import/explicit export failures are
  retained under ignored `results/runs/known-turn-source-20261123/` and were
  corrected before source qualification. No new game-tree, profile, policy
  or score measurement occurred. Next: publish tested source, then run all
  four exact-source local/optional roles, hooks and both hosted jobs before
  any real trajectory. Codex assisted; human time/learning not reported.

- Exact-source PR #108 qualification on tested commit `0b899554` passed
  base Python 3.11/3.12 with 5,799 passed, 73 skipped, 150 slow
  deselected each; optional 3.11 passed 2,597 and optional 3.12 passed
  2,595 with two expected skips across the fixed 81 suites. Pre/post
  guards bound the new source fingerprint
  `6e09c02673ca596e6082ea8d0a57ba12cd2533acfaf2c777991c4d29f395e0f4`,
  historical sources, lock, installed runtimes and OpenSpiel/Numba/license.
  All-file hooks and both [source-head hosted jobs](https://github.com/jimmy-sim/poker-ai/actions/runs/45285559652)
  passed. The first detached local wrapper stopped after writing a passing
  base 3.11 receipt but before updating its driver state; no worker
  survived, and a supervised continuation accepted that receipt and ran
  only the three remaining roles. The interruption and prior software
  iteration failures remain in the [source receipt](../results/known-turn-exact-mechanism/source-checks/manifest.json),
  32 hashed members. No real-game path, profile or score has run. Next:
  publish and GitHub-byte-verify this receipt before the one capped
  fictional proof. Codex assisted; human time/learning not reported.

- After the source receipt was published and GitHub-byte-verified,
  PR #108's single [fictional own proof](../results/known-turn-exact-mechanism/own-proof/manifest.json)
  ran from clean receipt HEAD `b227e4de` with the pinned base 3.11
  environment. Both representation labels saved and replayed six fixed
  readouts each at 80/240/720 work crossings, final charged work 726.
  The whole launcher exited zero in 0.783 seconds under the 180-second
  cap. The 32-member archive retains raw policies, mass, scores, events,
  launcher PIDs, environment and logs. This is a software proof, not a
  known medium/dry strength result. Next: publish/byte-verify proof, then
  one fixed six-path, three-repeat 1m-work profile. Codex assisted;
  human time/learning not reported.

- The one fixed PR #108 six-path, three-repeat [profile](../results/known-turn-exact-mechanism/profile/manifest.json)
  completed on clean proof HEAD `11a12d80` in 13.029 internal/13.771
  launcher seconds (<900). Every path reached 1,022,544 charged visits,
  saved/replayed current and linear-average policies, and retained all
  timings; peak worker RSS was 223,363,072 bytes. Worst-repeat 10m
  extrapolations are 42.752851 seconds for q8 control and 42.767612
  seconds for exact-turn candidate. Fixed two-worker `T=42.767612`, giving
  strict `2*(2*T+600)=1,371.070446 < 7,200` seconds. This is a forecast,
  **not** admission or strength. All 45 raw/launcher members are sealed;
  next: publish/byte-verify profile, then one separate data-only admission.
  Codex assisted; human time/learning not reported.

- After all 45 profile members and 49 changed blobs were published and
  verified, PR #108's separate data-only
  [admission](../results/known-turn-exact-mechanism/admission/manifest.json)
  recomputed the six unselected profile repeats from clean `4ce972d2`.
  Fixed two-worker `T=42.7676115453` seconds gives strict bound
  `1,371.0704461813 < 7,200` seconds, so status **admitted**. The
  launcher exited zero in 0.722 seconds; eight raw/launcher members are
  retained. No 10m policy has started. Next: publish/byte-verify admission,
  then run the single fixed two-path own study within 7,200 seconds with
  120 seconds reserved for failure save. Codex assisted; human time/
  learning not reported.

- The one admitted PR #108 matched-work [own pair](../results/known-turn-exact-mechanism/own/manifest.json)
  completed once from clean admission HEAD `a5f1bb5d` under its 7,200-
  second cap: 13.740 internal/14.516 launcher seconds, both arms at
  10,012,410 charged visits, six saved current/linear-average policies
  each, whole coverage 1.000 and zero recall violations. Final own-only
  exact exploitability is 0.904254 chips (0.025118 initial pots) for the
  q8 control and 0.231219 chips (0.006423 pots) for the exact-turn
  candidate, paired difference −0.018695 pots. At 100k/1m the paired
  differences are −0.003080/−0.026396 pots. Final post-initial-river
  coverage is 0.994179/0.969010 respectively; peak worker RSS
  173,735,936/156,663,808 bytes. All 32 raw/launcher members are sealed.
  These are preliminary own calculations on one **known** game, not an
  accepted strength claim or seed-based uncertainty estimate. Next:
  publish/GitHub-byte-verify every own policy/score before the one pinned
  comparison-only OpenSpiel audit. Codex assisted; human time/learning
  not reported.

## 2026-11-23 — PR #106 closure and prospective exact-turn test

- [PR #106](https://github.com/jimmy-sim/poker-ai/pull/106) was history-merged
  as `fe8ffb7021ee4a39f77de22aaf81990a1aeff047` after all exact
  source/report local and hosted gates, the retained final receipt, and
  solo review. Its receipt-head [CI 45244998632](https://github.com/jimmy-sim/poker-ai/actions/runs/45244998632)
  passed both versions; official full logs are retained under ignored
  `results/runs/river-turn-loss-final-20261123/`. Prospective, source,
  proof, raw report and final receipt commits are all ancestors of main.
  Post-merge main CI 45251041211 was still running at this entry. The
  [known-input result](river-turn-loss-diagnosis-result.md) is a
  **turn-grouping hypothesis**, not a poker-strength success: 92.8173%
  of the candidate's final turn gain falls on collided rows. Parent
  PR #105 remains negative, and no default was promoted. Codex assisted;
  human time was not reported.

- The distinct [prospective exact-turn comparison](turn-exact-transfer.md)
  asks whether using exact acting turn information with unchanged exact
  river information reduces exploitability under identical full expected
  charged work. The diagnosed medium/dry case is labeled known; three
  additional card/range inputs will be selected once by fixed structural
  rules on known public templates. Control, candidate, deterministic seed,
  checkpoints, absolute/paired gates, conservative forecast, caps and
  publication boundaries are fixed in the machine contract before any new
  selection or outcome. No new spot, training, profile or score exists at
  this protocol checkpoint. Codex assisted; human time or personal learning
  was not reported.

- The isolated PR #107 one-time selection source checks the published
  contract and 21 tracked known spots, pins the prior mechanistic input,
  rejects duplicate output, and draws only by board/range structure.
  Three focused tests use a separate fictional RNG stream and read-only
  contract checks; no registered cohort was drawn. The first Ruff failure
  (imports/line length) is retained in ignored
  `results/runs/turn-exact-transfer-20261123/`; formatting, focused tests,
  strict mypy and lint then passed. Source publication/verification precedes
  the one real selection. Codex assisted; human time was not reported.

- The one registered PR #107 structural cohort was drawn once at clean,
  published selector head `c036dd920dacd82a80e87d8886586e5f9d807d63`
  with PCG64 seed 20261520. The [freeze](../configs/turn-exact-transfer-freeze.json)
  records medium/dry OOP, medium/wet OOP and low/wet IP new card/range
  inputs after 66, 31 and 2 board attempts respectively. All 21 prior
  input hashes, three new input hashes, distinct rank signatures, fixed
  texture/position rules and selected source hashes were checked without
  building a game tree or reading a policy or score. No case was replaced;
  no turn collision or strength outcome is known at freeze publication.
  Codex assisted; human time was not reported.

- PR #107's isolated exact-turn adapter, fixed full-work capture/replay,
  inventory, conservative forecast, admission, comparison-only audit and
  report source were implemented after the freeze. Historical source files
  and pinned inputs were not edited. Fictional and already known fixture
  tests cover turn-key refinement, policy replay, strict forecast equality
  and the fixed strength decision: 11 focused tests passed. Ruff and format
  passed; strict mypy passed 994 project source files. Early style/typing
  failures and an initial pytest import failure from the default environment
  remain in ignored `results/runs/turn-exact-transfer-20261123/`; the test
  rerun used the pinned Python 3.11 environment. The frozen selected trees,
  collision counts and poker outcomes have not been read. Exact-source
  base/optional/hosted qualification remains before real inventory. Codex
  assisted; human time or personal learning was not reported.

- Exact-source PR #107 qualification passed at published commit `99dff04`,
  fingerprint `fb9006517142ee23076f2c0b6d581475dfdaed8127cb2c146a60731af901b09c`.
  Base Python 3.11 and 3.12 each recorded 5,795 passed, 73 skipped and
  150 slow deselected with source guards before and after. The 81-file
  optional suites recorded 2,597 passed on 3.11 and 2,595 passed with two
  expected skips on 3.12; pinned Numba/OpenSpiel versions and license hash
  matched. All-file hooks and both [hosted jobs](https://github.com/jimmy-sim/poker-ai/actions/runs/45256396875)
  passed, and all 24 closed source/input blobs matched GitHub. The first
  two local launcher/preflight attempts failed before any selected tree and
  remain in the source-check archive alongside software iteration failures.
  No collision or strength outcome is known. Next: publish and verify the
  [source receipt](../results/turn-exact-transfer/source-checks/manifest.json)
  before the frozen inventory. Codex assisted; human time or personal
  learning was not reported.

- The single source-qualified frozen [inventory](turn-exact-transfer-result.md)
  ran from clean `8e2e792` and exited zero in about 7.06 launcher seconds,
  below its 900-second cap. The known mechanistic input has 12 collided
  exact turn rows in six q8 groups, but all three new card/range inputs
  have zero turn collisions. Their trees have 21,303, 21,303 and 2,295
  nodes, all below the 200,000-node limit. The registered
  `structural_stop` ended the comparison **inconclusive for poker strength**.
  No fictional proof, profile, admission, training, reference audit,
  default change, redraw or retry occurred. Raw JSON, PIDs, command and
  logs are preserved in the [inventory archive](../results/turn-exact-transfer/inventory/manifest.json).
  Next: publish/verify the structural-stop evidence, finish final
  documentation/source checks and PR review, then register a distinct
  known-case mechanistic question if justified. Codex assisted; human
  time or personal learning was not reported.

- PR #107's published `d41baac` structural-stop report and raw archive
  passed final exact-result local requalification: base Python 3.11 and
  3.12 each 5,795 passed, 73 skipped, 150 slow deselected; optional
  Python 3.11 2,597 passed; optional 3.12 2,595 passed and two expected
  skips. Each role checked the historical/source fingerprint and published
  receipt, inventory and report hashes before and after; all-file hooks
  passed. Both [result-head hosted jobs](https://github.com/jimmy-sim/poker-ai/actions/runs/45265519612)
  passed. The [final receipt](../results/turn-exact-transfer/final-checks/manifest.json)
  retains complete local/hosted logs, PIDs and exact pinned bytes; publish
  and verify it before solo review and history-preserving merge. The
  scientific result remains inconclusive and no training occurred. Codex
  assisted; human time or personal learning was not reported.

## 2026-11-23 — PR #105 negative result and next diagnostic

- [PR #105](https://github.com/jimmy-sim/poker-ai/pull/105) history-merged as
  `c84302b58c8ee18220d39a2d8130abae803a779a`; protocol, source,
  admission, own-before-reference and final receipt commits are ancestors
  of main. The [fixed two-input result](river-full-broader-spots-result.md)
  is **negative** on the newly selected medium/dry card/range input on a
  known public template. No default changed. Receipt-head
  [CI 45213999919](https://github.com/jimmy-sim/poker-ai/actions/runs/45213999919)
  first canceled Python 3.11 at the unchanged 35-minute limit at 97% of
  `make check`; Python 3.12 passed. The complete canceled log is retained
  under ignored `results/runs/river-full-broader-receipt-ci-20261123/`.
  One same-SHA operational requalification of only the canceled 3.11 job
  passed in 1,488 seconds; no scientific work, timeout or test selection was
  changed. The post-merge main CI 45226018829 was pending at this entry.
  Codex assisted; human hands-on time was not reported.

- The [next prospective read-only diagnostic](river-turn-loss-diagnosis.md)
  fixes the published PR #105 policies, seed/work grid, candidate-ranked
  turn-node rule, collision accounting, numerical gates and 900-second cap
  **before** any new node ranking or collision count. It uses the evaluated
  medium/dry input as a known case and collects no training or new reference
  output. The prior PR #98 known spot had zero turn collisions, so the new
  turn-heavy loss alone is insufficient to choose a representation change.
  Diagnostic source and measurements remain pending. Codex assisted; human
  hands-on time and personal learning were not reported.

- Isolated PR #106 read-only trace/selection code and five focused tests
  were implemented after protocol publication. The code checks exact
  published plan and archive bytes, the unchanged parent source fingerprint,
  snapshot/native/report identities, additive both-seat best-reply accounting,
  recall and duplicate-output refusal. A fictional signal-game test verifies
  additive gain against an independently computed own score. Ruff,
  formatting and strict mypy passed on the new files; five focused tests
  passed. Exact-source full local/optional/hosted qualification, fictional
  proof and real saved-policy diagnosis remain pending. No new candidate node
  ranking or collision count has been measured. Codex assisted; human time
  was not reported.

- Exact tested-source PR #106 `4400b52a87659ec543fa3c3eaf0f8785487d80c4`
  passed local base Python 3.11/3.12 (5,784 passed, 73 skipped, 150 slow
  deselected each; Ruff, format, strict mypy and source guards), optional
  3.11 (2,597 passed) and optional 3.12 (2,595 passed, two expected skips).
  Both optional roles checked the pinned OpenSpiel 2.0.2 license and Numba
  0.68.1. All-file hooks and [hosted CI 45228243604](https://github.com/jimmy-sim/poker-ai/actions/runs/45228243604)
  passed on the same head. The [source-check receipt](../results/river-turn-loss/source-checks/manifest.json)
  retains exact local and hosted logs and the earlier system-Python import
  failure. No real saved-policy diagnosis or fictional proof had run at this
  publication checkpoint. Main post-PR #105 CI also passed both jobs.
  Codex assisted; human time was not reported.

- The separately capped fictional PR #106 proof passed at source-receipt
  head `49aa13b66773adb4617ffdefa122bfec0623f2c1` in 0.495 launcher
  seconds against 180. Its four toy exact rows all collide under the coarse
  key; both-seat additive gain/2 equals 0.25 toy chips of independent
  exploitability, with zero accounting error. The [proof archive](../results/river-turn-loss/proof/manifest.json)
  retains the exact command, environment, launcher state and raw proof. This
  is a fictional math check, not a medium/dry poker result. The single saved
  real-policy diagnosis remains pending. Codex assisted; human time unknown.

- The one fixed, read-only PR #106 saved-policy diagnosis completed all 12
  cases and 24 best-reply traces in 24.886 launcher seconds under 900. The
  [raw archive](../results/river-turn-loss/diagnosis/manifest.json) and
  [interpretation](river-turn-loss-diagnosis-result.md) show 12 collided
  turn exact rows in six groups, zero river collisions, and 92.8173% of
  final candidate turn gain on collided rows. The leading Jh 9h turn row
  contributes 0.746330 chips, 86.6721% of turn gain; it shares its saved
  probabilities with Qd Qh despite opposite local call/fold values. Two-seat
  accounting and native scalar errors remain far below 1e−9 chips. This
  flags a future representation test under the frozen rule; it does not
  overturn PR #105's negative strength classification or establish a
  causal gain. Codex assisted; human time and personal learning unknown.

- Final exact PR #106 negative-parent diagnosis-report head `abef90e4fc532f20484ad7522f789942ca819eb9`
  passed serial local base Python 3.11 and 3.12, each with 5,784 passed,
  73 skipped and 150 slow deselected, plus Ruff, formatting, strict mypy,
  pre/post historical/current source, archive, lock and runtime guards.
  Optional 3.11 passed 2,597; optional 3.12 passed 2,595 with two expected
  skips, both across 81 pinned suites and license guards. All-file hooks
  and [report-head hosted CI 45237203341](https://github.com/jimmy-sim/poker-ai/actions/runs/45237203341)
  passed both Python jobs. The [final receipt](../results/river-turn-loss/final-checks/manifest.json)
  retains complete local/hosted logs and archive hashes. The diagnostic
  signal remains a hypothesis, with no new poker-strength acceptance.
  Codex assisted; human time was not reported.

## 2026-11-23 — PR #104 merge and next prospective question

- [PR #104](https://github.com/jimmy-sim/poker-ai/pull/104) history-merged as
  `804c4ed258416083e8c704febfe84c9077b38bae` after both receipt-head
  Python CI jobs passed. Its source, admission and own-before-reference commits
  remain ancestors. The fixed two-known-spot result is positive only in that
  scope; no default promotion. [Main CI 45186501720](https://github.com/jimmy-sim/poker-ai/actions/runs/45186501720)
  was pending at this entry. The next
  [prospective issue #4 protocol](river-full-broader-spots.md) fixes a
  two-input matched-work full-versus-B4 comparison before case selection or
  outcomes. The earlier four-input B4 forecast failure motivated the bounded
  cohort; it is not a strength result. Codex assisted; human hands-on time was
  not reported.

- The isolated PR #105 selector and B4/full adapters were implemented without
  changing historical files, source pins or the lock. Before cohort selection,
  seven focused tests passed for deterministic exclusion/refusal to replace,
  toy B4 capture/replay, a fictional two-learner runner check, fixed path order,
  conservative slowest-repeat forecast and the frozen strength rule. Ruff
  lint/format and strict mypy passed on the
  new source. The PR #104 historical source fingerprint still equals
  `a549976f0811872dcc9057e112f40def8af5d2f3e16b81d1a678fdcf8bc62aab`.
  Full exact-source qualification, cohort freeze and all scientific stages are
  pending; these focused checks make no poker-strength claim.
  The first source commit hook attempt failed before Ruff ran because its shell
  could not find `uv`; the retained ignored local log at
  `results/runs/river-full-broader-source-20261123/first-hook-failure.log`
  records it. The code was unchanged and the hooks will be rerun with the
  repository's environment sourced, without bypassing them.

- The one preregistered structural selection ran once from clean published
  selector source `f40551562ed4b37204174f7e6a5e3dc7213524aa`.
  `full_new_medium_dry_oop` took 41 attempts and rank signature
  `((5, 11, 14), 3)`; `full_new_low_wet_ip` took 10 attempts and signature
  `((12, 13, 14), 11)`. Both exact legal spot bytes and all 19 prior known
  input hashes are in the [cohort freeze](../configs/river-full-broader-freeze.json).
  Selection used no tree, policy, score or reference output. The known public
  templates remain known; no strength measurement exists yet.

- The PR #105 protocol-head [CI 45187285433](https://github.com/jimmy-sim/poker-ai/actions/runs/45187285433)
  passed Python 3.11 and 3.12 before source publication. The frozen cohort
  commit `190fde4ee2768857f4a24bda2170d0ec1ec14555` was pushed, and its
  three GitHub blobs matched local bytes. The new source guard now pins that
  exact freeze; full exact-source qualification is still pending. Separately,
  PR #104's [post-merge main CI 45186501720](https://github.com/jimmy-sim/poker-ai/actions/runs/45186501720)
  was canceled at its unchanged 35-minute limit with Python 3.11 around 97%
  of `make check`; Python 3.12 passed. The canceled 3.11 log is retained locally
  under `results/runs/river-full-broader-source-20261123/`. PR #104's earlier
  receipt-head CI passed both versions and remains a distinct gate.

- Exact PR #105 source `6ccf3a367ec06fe7f3ac4ca807a5d1d9111f75dd`
  completed serial four-role local qualification: base Python 3.11 and 3.12
  each passed 5,779 tests, 73 skipped and 150 slow deselected, plus Ruff,
  formatting, strict mypy and pre/post source/lock/runtime guards. Optional
  3.11 passed 2,597; optional 3.12 passed 2,595 with two expected skips,
  both with pinned OpenSpiel 2.0.2, Numba 0.68.1 and installed Apache-2.0
  license guards. All-file hooks and exact tested-source
  [hosted CI 45193945715](https://github.com/jimmy-sim/poker-ai/actions/runs/45193945715)
  passed both versions. All 17 source-bound files matched GitHub blobs. The
  [source receipt](../results/river-full-broader/source-checks/manifest.json)
  retains role/hosted logs, eight focused tests and the corrected first hook
  failure; its publication and GitHub verification precede the fictional
  proof. No poker trajectory or strength measurement has run.

- After the complete source receipt was published and all 24 GitHub blobs
  verified, one [fictional proof](../results/river-full-broader/own-proof/manifest.json)
  ran on clean source-receipt head `5e964607716b4257c41578b45b99abd2bd42c0d5`.
  The 180-second launcher finished in 0.510 seconds, exiting zero. B4 and full
  expected arms each saved/replayed six fixed readouts; their final charged
  work was 720 and 726 toy nodes. The archive retains the launcher, source,
  events, policies and logs. This is software proof on a fictional signal
  game, not poker evidence. Next: publish/verify every proof byte, then run
  the fixed real-game 24-path compute profile once.

- The single preregistered PR #105 profile completed all 24 paths (three
  repeats of eight) from clean proof-receipt head `b8155e3` in 20.667 seconds
  internally and 21.170 seconds at the launcher, below its 900-second cap.
  Its [complete raw archive](../results/river-full-broader/profile/manifest.json)
  retains every path, timing, score, event and launcher log. The fixed worker
  sums are 559.144, 529.325 and 513.456 seconds, giving `T=559.144` and the
  preregistered strict bound `2*(2*T+600)=3436.576<7200` seconds. Profile
  scores were not used to select cases or change the candidate. The separate
  data-only admission remains pending; no 10m trajectory or strength result
  exists. Codex assisted; human hands-on time was not reported.

- After the profile archive was published at `05ed5e8` and all 153 GitHub
  blobs matched, the separate data-only admission recomputed the identical
  `T=559.1438954659656` and strict bound `3436.575581863862<7200` seconds.
  The [admission receipt](../results/river-full-broader/admission/manifest.json)
  records the published profile and source head. No source, seed, work budget
  or spot changed. Next: publish and byte-verify admission before the single
  fixed eight-path own study. Codex assisted; human time was not reported.

- With admission published and all three receipt blobs verified on GitHub,
  the one fixed eight-path 10m own study ran from clean `78f5ded`. All eight
  paths completed with 48 saved policy readouts and their own scores at the
  three charged-work crossings. Internal runtime was 139.545 seconds and
  launcher runtime 140.096 seconds under the 7,200-second cap. The
  [own archive](../results/river-full-broader/own/manifest.json) retains
  policies, score events, work counts, launcher state and logs. Its publication
  and GitHub byte verification are required before the pinned OpenSpiel
  scalar audit; no reference comparison or final strength classification
  exists at this checkpoint. Codex assisted; human time was not reported.

- After all 104 own archive blobs matched GitHub at `da58637`, the one
  pinned OpenSpiel 2.0.2 comparison-only audit checked all 48 published
  policy readouts. It passed the unchanged `1e-9`-chip scalar gate with
  maximum error `1.1368683772161603e-13` chips; internal runtime was
  26.930 seconds and launcher runtime 27.497 seconds under the 900-second cap.
  The [native archive](../results/river-full-broader/native/manifest.json)
  retains all row values, license/runtime evidence, launcher and logs. No
  reference strategy entered training. Next: publish and byte-verify the
  audit before the frozen report. Codex assisted; human time was not reported.

- The frozen PR #105 report rebuilt all 48 published policies and 12
  control-ranked representative nodes from verified own/native bytes. The
  [negative result](river-full-broader-spots-result.md) has medium/dry final
  candidate 0.025118161 initial pots, above its 0.01 absolute gate and
  +0.007973008 worse than the B4 median at matched 10m work. Low/wet passes
  its absolute and +0.001 nondegradation gates, but does not reverse the
  medium/dry failure. All whole-coverage values are 1.0 and recall errors
  zero; native maximum error is `1.1368683772161603e-13` chips. This is a
  **negative** two-input test, with no scientific retry or default change.
  Next: publish/verify the report, complete required final exact-source
  local/optional/hosted checks and review PR #105. Codex assisted; human
  hands-on time was not reported.

- Final exact PR #105 negative-report-head `f62373f` qualification passed:
  serial local base Python 3.11/3.12 each passed 5,779 tests, 73 skipped,
  150 slow deselected plus Ruff, format, strict mypy and pre/post guards;
  optional 3.11 passed 2,597, optional 3.12 passed 2,595 with two expected
  skips, both with pinned OpenSpiel/Numba/license and archive guards.
  All-file hooks and [hosted CI 45205774174](https://github.com/jimmy-sim/poker-ai/actions/runs/45205774174)
  passed both jobs. The [final receipt](../results/river-full-broader/final-checks/manifest.json)
  retains exact logs and the negative classification. Next: publish/verify
  this receipt and finish solo review before merge. Codex assisted; human
  hands-on time was not reported.

## 2026-11-23 — PR #103 merge and next prospective question

- [PR #103](https://github.com/jimmy-sim/poker-ai/pull/103) history-merged as
  `79db2fb59f7357f1042d395b9f05f8e5d89ae7c2` after final receipt-head
  [CI 45152979600](https://github.com/jimmy-sim/poker-ai/actions/runs/45152979600)
  passed Python 3.11/3.12 and the solo review found no material source or
  evidence issue. The **negative** B8 scientific result and all checkpoint
  commits remain intact; no default changed. Post-merge main CI
  [45156767169](https://github.com/jimmy-sim/poker-ai/actions/runs/45156767169)
  is pending at this entry. The [new prospective full-expectation question](medium-dry-full-expectation.md)
  asks whether removing trajectory sampling, with signed linear rules and
  matched charged work, improves the same two known spots against immutable
  B4 control. It fixes one deterministic path per spot, three control seeds,
  work, gates, profile, strict forecast and stop rule before new outcomes.
  No candidate policy or score has been measured. Codex assisted; human
  hands-on time was not recorded.
- **Isolated full-pass implementation, local focused checks:** new
  `scripts/medium_dry_full/` and thin study command use the existing
  `ControlledTrainer` full expectation under unchanged signed/linear rules.
  Capture/replay, strict source/archive guards, six-path forecast, staged
  publication checks, comparison-only native scalar audit and fixed
  candidate/control decision report are isolated from historical sources.
  Sixteen focused tests passed, including enumerated tiny-game conditional
  means for both players, adaptive signed-linear update, RNG nonconsumption,
  first work crossings, replay, failure retention, fixed grid/forecast/
  classification and known-game information-key identity. Ruff lint/format
  and strict mypy passed on all 10 new source/test files. The first focused
  lint/format iterations failed and their logs remain under ignored
  `results/runs/medium-dry-full-source-20261123/`; corrected checks passed.
  Full exact-source local/optional/hooks/hosted qualification is pending,
  as are all scientific stages. No candidate real-game policy or score exists.
  Codex assisted; human hands-on time was not recorded.
- **Exact-source qualification and tested-source publication:** prospective
  protocol-head [CI](https://github.com/jimmy-sim/poker-ai/actions/runs/45157713793)
  passed both Python jobs. The isolated tested source `fdcc438` with
  fingerprint `a549976f0811872dcc9057e112f40def8af5d2f3e16b81d1a678fdcf8bc62aab`
  passed base Python 3.11 and 3.12, each with 5,771 tests, 73 skips and
  150 slow deselections, plus Ruff, format, strict mypy and exact pre/post
  source, historical-pin, runtime and lock guards. Optional 3.11 passed
  2,597 tests; optional 3.12 passed 2,595 with two expected skips; both
  checked pinned OpenSpiel 2.0.2 and its license. Sixteen focused new tests
  passed on base and both optional runtimes. All-file hooks and tested-source
  [hosted CI](https://github.com/jimmy-sim/poker-ai/actions/runs/45166698139)
  passed both Python jobs. The [source-check archive](../results/medium-dry-full-expectation/source-checks/manifest.json)
  keeps exact logs, receipts and initial corrected focused-check and hook
  PATH failures. Post-merge PR #103 main
  [CI](https://github.com/jimmy-sim/poker-ai/actions/runs/45156767169)
  passed both jobs. No full-expectation proof, real policy, score or reference
  audit has run. Next: publish and byte-verify the source receipt before the
  one fictional proof. Codex assisted; human hands-on time was not recorded.
- **One fictional full-pass proof:** all 41 published source-check blobs
  matched GitHub's committed tree, and the offline source archive guard passed.
  At clean receipt head `bcc932e`, one capped proof on the fictional signal
  game saved and replayed six current/linear-average snapshots across three
  first work crossings, finishing at 726 charged node visits in 0.366 outer
  seconds under the fixed 180-second cap. The [proof archive](../results/medium-dry-full-expectation/own-proof/manifest.json)
  retains snapshots, cumulative masses, events, source verification, launch
  command, environment, PID and logs. This is a software proof, not a poker
  result. Next: publish and GitHub-byte-verify the proof before the one fixed
  six-path real-game profile. Codex assisted; human hands-on time was not
  recorded.
- **Fixed six-path full-expectation profile:** all 22 published fictional-proof
  blobs matched GitHub and both offline source/proof gates passed. One serial
  worker completed the preregistered two known spots × three repeats at first
  1m charged-work crossings in 13.862620 seconds (<900); all paths, policies,
  scores and work counts are retained in the [raw profile](../results/medium-dry-full-expectation/profile/manifest.json).
  Low/wet finished at 1,000,620 work and medium/dry at 1,022,544 work in each
  repeat. Maximum observed worker RSS was 181,911,552 bytes (cumulative
  process peak). The required maximum scaled whole-path estimates were
  10.979192 seconds for low/wet and 34.345882 for medium/dry, so
  `T=45.325074` and `2*(2*T+600)=1381.300294<7200` seconds. This is a
  profile-derived forecast, **not** separate admission or a 10m poker result.
  Next: publish and byte-verify the complete profile, then recompute the
  data-only gate. Codex assisted; human hands-on time was not recorded.
- **Separate conservative admission:** all 47 published profile blobs matched
  GitHub, and the offline source/proof/profile guards passed. A data-only
  [decision](../results/medium-dry-full-expectation/admission/manifest.json)
  recomputed the frozen profile's `T=45.325073510810725` seconds and strict
  `2*(2*T+600)=1381.300294043243<7200`, so the one two-path 10m own run is
  **admitted**. No new policy was trained and no reference output used in this
  step. Next: publish and GitHub-byte-verify the admission before launching
  the one capped own study. Codex assisted; human hands-on time was not
  recorded.

- **One admitted own full-pass study:** after all 10 admission files matched
  GitHub and the offline source/proof/profile/admission guards passed, the
  single fixed two-path 10m study completed from clean admission head
  `1507453`. The outer driver took 19.435177 seconds (<7200) and did not
  need its 120-second failure-save reserve. Low/wet crossed 10m at
  10,001,610 charged nodes and medium/dry at 10,012,410. Each path saved
  six current/linear-average policies across three work labels, cumulative
  mass, exact own scores and RNG state; both have zero structural recall
  violations and whole positive-average coverage 1.0. The final own linear
  average exploitability is 0.0194244965 chips (low/wet) and 0.2412065218
  chips (medium/dry). Maximum recorded worker RSS was 181,649,408 bytes.
  The [own archive](../results/medium-dry-full-expectation/own/manifest.json)
  retains complete/partial markers, source/environment/worker logs and all
  policies. No OpenSpiel reference or B4 comparison entered training or this
  publication. These own scores require the pinned independent audit and
  fixed report before a strength classification. Next: publish and
  GitHub-byte-verify every own byte before the comparison-only audit. Codex
  assisted; human hands-on time was not recorded.
- **Pinned comparison-only scalar audit:** all 34 published own-policy files
  matched GitHub and the offline source/own guards passed before OpenSpiel was
  loaded. The fixed OpenSpiel 2.0.2 Apache-2.0
  [audit](../results/medium-dry-full-expectation/native/manifest.json)
  checked every candidate saved value, best reply and exploitability scalar
  across 12 policies in 6.548546 seconds (<900); maximum error was
  `5.684341886080802e-14` chips (<`1e-9`). Installed license hash matched
  `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`.
  No reference strategy entered training. Next: publish and byte-verify this
  audit, then replay the fixed candidate/B4 control report and prespecified
  river decisions. Codex assisted; human hands-on time was not recorded.
- **Fixed full-expectation strength report:** after all 10 published native
  files matched GitHub, the one frozen report replayed 48 candidate/control
  work/readout cases and an independent data-only grid/arithmetic check
  passed. The [report](medium-dry-full-expectation-result.md) and
  [raw evidence](../results/medium-dry-full-expectation/report/manifest.json)
  classify the two-known-spot result **positive** under the registered rule:
  medium/dry candidate 0.006700181 initial pots versus B4 seed scores
  0.035655787/0.039541661/0.035132481, with candidate-minus-control
  differences −0.028955606/−0.032841480/−0.028432300; low/wet candidate
  0.000059952 versus 0.000945518/0.000909274/0.001146135, with differences
  −0.000885566/−0.000849322/−0.001086183. Whole coverage 1.0, zero
  recall violations, and pinned scalar audit error below tolerance. At
  medium/dry 100k and 1m, the candidate was worse than the B4 median;
  only the fixed 10m endpoint passes. The three contrasts share one
  deterministic candidate, and both games are known; no population or
  full-game claim or default promotion follows. Fixed turn/river rows and
  a Terminal inspection command are in the report. Next: publish/verify
  the report, complete exact report-head local/optional/hooks and hosted
  qualification, then solo review and history-preserving merge if eligible.
  Codex assisted; human hands-on time was not recorded.

- **Final report-head qualification:** exact positive-report head `715637b`
  passed clean pre/post historical/new-source, protocol, published-report,
  lock/runtime and optional reference-license guards. Base Python 3.11 and
  3.12 each passed 5,771 tests, with 73 skips and 150 slow deselections,
  plus Ruff, formatting and strict mypy. Optional 3.11 passed 2,597;
  optional 3.12 passed 2,595 with two expected skips. All-file hooks and
  [hosted report-head CI](https://github.com/jimmy-sim/poker-ai/actions/runs/45174852553)
  passed on both versions. The [final receipt](../results/medium-dry-full-expectation/final-checks/manifest.json)
  binds the exact logs and metadata; earlier corrected source-check failures
  remain in their separate archive. Scientific classification remains
  **positive on two known games**, with no default change. Next: publish
  and byte-verify the receipt, check receipt-head hosted CI, complete solo
  review and history-preserving merge if eligible. Codex assisted; human
  hands-on time was not recorded.

## 2026-11-23 — PR #103 fixed B8 result

- The one preregistered [paired report](medium-dry-b8-updates-result.md) replayed
  both published cohorts once and retained all 108 spot/arm/seed/work/readout
  cases in the [raw report](../results/medium-dry-b8-updates/report/manifest.json).
  Its classification is **negative**: medium/dry B8 final median/worst
  0.036102/0.042155 initial pots exceeds the frozen 0.01/0.025 gates.
  B8-minus-B4 paired differences are +0.000447, −0.004799, +0.007022
  (median +0.000447); low/wet passes its absolute gate. Whole coverage is 1.0
  with zero recall violations. Fixed river decomposition and representative
  saved decisions are in the report. The combined native comparison maximum
  difference is `7.105e-14` chips. No training was repeated, protocol changed,
  budget extended or default promoted. Next: publish/verify the report, then
  complete final report-head local/hosted checks and PR review. Codex assisted;
  human hands-on time was not recorded.
- **Final qualification:** on exact report head `9bcc83b`, base Python
  3.11/3.12 each passed 5,755 tests, 73 skips and 150 slow deselections, plus
  Ruff, formatting, strict mypy and pre/post guards. Optional 3.11 passed
  2,597; optional 3.12 passed 2,595 with two skips, with pinned runtime and
  license guards. All-file hooks passed. Hosted
  [CI 45146235586](https://github.com/jimmy-sim/poker-ai/actions/runs/45146235586)
  passed both Python jobs and hooks. The [final receipt](../results/medium-dry-b8-updates/final-checks/manifest.json)
  retains exact logs and metadata. Scientific classification remains negative;
  next: publish receipt, solo review and history-preserving merge if eligible.
  Codex assisted; human hands-on time was not recorded.

## 2026-11-23 — PR #103 exact-source B8 qualification

- **Tested source:** `81ef11afffd2067e94b3c576e5d2cb3e76f733cc`,
  B8 fingerprint `666ac9e4322ca84f93ad43acf972e8a758125f1aa1276da2847a6025049b40ad`.
  Base Python 3.11 and 3.12 each passed 5,755 tests, with 73 skips and 150
  slow deselections, plus Ruff, format, strict mypy and exact pre/post guards.
  Optional 3.11 passed 2,597 tests; optional 3.12 passed 2,595 with two skips;
  both checked OpenSpiel 2.0.2, its license, historical pins and the exact
  B8 source. The new B8 focused tests passed eight times on each optional
  runtime. All-file hooks passed; an earlier shell wrapper failed only while
  trying to save its exit code after the hooks printed passes. The original
  commit-hook PATH setup failure also remains retained. Source-head
  [hosted CI](https://github.com/jimmy-sim/poker-ai/actions/runs/45135404030)
  passed Python 3.11/3.12. The [source archive](../results/medium-dry-b8-updates/source-checks/manifest.json)
  retains logs, receipts and failures. No B8 scientific stage has run. Next:
  publish and GitHub-byte-verify this receipt before fictional proof. Codex
  assisted; human hands-on time was not recorded.
- **Fictional own proof after source publication:** all 26 source archive
  GitHub blobs matched the local commit, and the offline publication guard
  passed. The one capped B8 proof on the fictional signal game completed nine
  captures and 784 charged node work with replay at receipt head `2ba208e`.
  Its observed external command wall time was 0.2001 seconds, below the
  180-second cap; the [proof archive](../results/medium-dry-b8-updates/own-proof/manifest.json)
  retains snapshots, masses, events, command and exit evidence. This is a
  software proof, not a poker result. Next: publish/verify proof before the
  one fixed 18-path 100k profile. Codex assisted; human hands-on time was not
  recorded.
- **One fixed B8 profile:** all 18 predeclared 100k-work paths across three
  repeats completed in 19.407502 seconds, below the 900-second cap; no path
  failure. Maximum observed worker RSS was 191,774,720 bytes. The prescribed
  maximum-per-path, fixed-partition calculation gave
  `T=657.9767527444723` seconds and strict bound
  `3831.907010977889<7200`. The [complete raw profile](../results/medium-dry-b8-updates/profile/manifest.json)
  has 150 members with all snapshots, scores, events, work counts and timing.
  This is a forecast from the profile, not the separate published compute
  admission or a 10m strength result. Next: publish/verify every profile byte,
  then recompute the separate gate. Codex assisted; human hands-on time was not
  recorded.
- **Separate compute admission:** all 151 published profile blobs matched the
  local tree, and the offline source/proof/profile gates passed. The data-only
  [admission decision](../results/medium-dry-b8-updates/admission/manifest.json)
  recomputed the same `T=657.9767527444723` and strict
  `3831.907010977889<7200` bound from the complete published profile, so
  the fixed B8 10m study is **admitted**. No training or reference comparison
  began during admission. Next: publish/verify this receipt before one capped
  six-path own run. Codex assisted; human hands-on time was not recorded.
- **One admitted own run:** six fixed B8 spot/seed paths each crossed 10m
  charged node work once, with final work 10,000,007–10,000,313. The spawned
  learner finished in 136.941730 seconds; the outer driver, including setup
  and save, exited0 in 137.430354 seconds below the 7,200-second cap with
  its 120-second failure-save reserve unused. Maximum worker RSS was
  202,883,072 bytes. All six path summaries, nine captures per path, saved
  policies, masses, RNG states, work counts and own scores are in the
  [complete own archive](../results/medium-dry-b8-updates/own/manifest.json)
  (114 members). No OpenSpiel output or comparison-only audit was used.
  Next: publish/GitHub-byte-verify the own raw bytes before any reference
  audit or strength classification. Codex assisted; human hands-on time was
  not recorded.
- **Pinned comparison-only audit:** after all 115 own-policy GitHub blobs
  matched and the offline publication guard passed, the fixed OpenSpiel 2.0.2
  scalar audit completed all 54 B8 saved policies in 28.124776 seconds under
  its 900-second cap. Maximum own/reference value, best-reply and
  exploitability error was `6.394884621840902e-14` chips, below `1e-9`.
  The [native archive](../results/medium-dry-b8-updates/native/manifest.json)
  retains raw comparison rows, events, runtime and Apache-2.0 license hash.
  It was run after own publication and did not feed reference strategies into
  training. Next: publish/verify the native archive, then replay the paired
  report and fixed decision rows. Codex assisted; human hands-on time was not
  recorded.

## 2026-11-22 — PR #103 isolated B8 source

- **Resume and source implementation:** local/tracking/GitHub PR head `24103f9`
  matched with a clean worktree; no local research worker or B8 outcome existed.
  Protocol [CI](https://github.com/jimmy-sim/poker-ai/actions/runs/44902543538)
  passed Python 3.11 and 3.12. Added an isolated B8 runner, capture/replay,
  source and stage guards, conservative forecast, comparison-only audit and
  paired report against the immutable published B4 controls. The candidate
  uses the existing signed batch-mean updater with `batch_size=8`; each saved
  checkpoint records RNG state. The report covers the prespecified turn and
  river rows. No historical pinned source or frozen protocol changed.
  Eight focused tests passed; Ruff lint and strict mypy passed after one
  formatting correction. Full exact-source qualification remains pending;
  no fictional proof, profile or poker outcome has run. Codex assisted; human
  hands-on time was not recorded.

## 2026-11-21 — PR #102 exact-source qualification

- **Merge and next prospective question:** [PR #102](https://github.com/jimmy-sim/poker-ai/pull/102)
  history-merged as `3bece9c19d99e68c3797fd4383679b8de6f012a5`;
  [post-merge main CI](https://github.com/jimmy-sim/poker-ai/actions/runs/44900095409)
  passed both Python jobs. Its conservative compute gate remains rejected and
  its poker-strength result inconclusive. The separate
  [B8 protocol](medium-dry-b8-updates.md) fixes one matched-work signed-update
  question against published B4 on two known spots. No B8 source, profile,
  training or outcome exists at this prospective checkpoint. Codex assisted;
  human hands-on time was not recorded.

- **Tested source:** `3e837b7e56c238d522de33bff0cacd8abcd16cf9`,
  source fingerprint `a982d8c3537f9d50aa721001a0436766f34e862732b8e1b514fdc79355a963f6`.
  Base Python 3.11 and 3.12 each passed 5,747 tests, with 73 skips and 150
  slow deselections, plus Ruff, format, strict mypy and exact pre/post guards.
  Optional Python 3.11 passed 2,597 tests with pinned OpenSpiel 2.0.2 and
  license checks. Tested-source [hosted CI](https://github.com/jimmy-sim/poker-ai/actions/runs/44882130314)
  passed both Python jobs.
- **Retained qualification failure:** the first optional Python 3.12 suite
  passed 2,594 tests and skipped two, but its unchanged historical
  saved-profile child exceeded the 120-second watchdog. The full failed log
  and receipt remain in the [source-check archive](../results/river-uniform-readout/source-checks/manifest.json).
  The same historical test then passed in focused checks. One bounded full
  software requalification at the identical source, suite and watchdog passed
  2,595 tests/two skips in 704.45 seconds. The first timeout's exact cause is
  unproven; no scientific work was retried or changed.
- **Hooks and source receipt:** the first hook launch was denied an external
  uv-cache lock by the sandbox; the second used an unavailable Python 3.11.14
  in offline mode. Both setup failures are retained. With the installed
  Python 3.11.17 and cache access, both all-file Ruff hooks passed in 326.38
  seconds. The archive keeps all three attempts and exact local/hosted logs.
  No poker proof, profile, training, reference audit or strength result has
  started. Next: publish/verify this source receipt before the fictional proof.
  Codex assisted; human hands-on time was not recorded.
- **Fictional proof after source publication:** the first launch was blocked
  by sandbox access to the uv cache before any output. Its log remains in the
  [proof archive](../results/river-uniform-readout/own-proof/manifest.json).
  With cache access, the prescribed same-path capture/replay on the fictional
  signal game completed nine captures and 732 final node work in 9.28 seconds,
  below its 180-second cap. This is a software proof, not poker evidence.
  Next: publish and GitHub-byte-verify the proof before the fixed profile.
  Codex assisted; human hands-on time was not recorded.
- **Fixed profile and stop:** [proof archive](../results/river-uniform-readout/own-proof/manifest.json)
  was pushed and all 28 GitHub files byte-verified. One profile completed all
  36 fixed 100k-work paths/three repeats in 54.230126 seconds, below its
  900-second cap. The predeclared conservative calculation gave
  `T=1921.279151` and `2*(2*T+600)=8885.116605` seconds, above the strict
  7200-second own-run cap by 1685.116605 seconds. The unchanged forecast was
  reproduced from the complete raw record. The
  [retained result](river-uniform-readout-result.md) is a **rejected compute
  admission and inconclusive poker-strength comparison**. No separate
  admission, 10m study, reference audit or default change; no scientific
  retry. Next: publish raw failure and report, then complete appropriate
  final qualification/review. Codex assisted; human hands-on time was not
  recorded.
- **Final publication qualification:** at report head `440b9a4`, both full
  local Python bases passed 5,747 tests/73 skips/150 slow deselections plus
  Ruff, format, strict mypy and pre/post exact-source, historical pin,
  published-archive and rejected-forecast guards. Optional Python 3.11
  passed 2,597 tests; optional 3.12 passed 2,595 with two skips. Both optional
  roles rechecked pinned OpenSpiel 2.0.2 and its license. All-file hooks
  passed. [Hosted CI](https://github.com/jimmy-sim/poker-ai/actions/runs/44893486953)
  passed Python 3.11 and 3.12. The [final check receipt](../results/river-uniform-readout/final-checks/manifest.json)
  preserves the exact logs. This qualifies the rejected report; it does not
  admit the 10m study or change the inconclusive poker-strength result.
  Codex assisted; human hands-on time was not recorded.

## 2026-11-20 — PR #101 merge and prospective average-readout panel

- **Completed prior milestone:** [PR #101](https://github.com/jimmy-sim/poker-ai/pull/101)
  history-merged as `0154696903dc50b97e137ffc552e44391ddfb7f6` after
  final local/hosted qualification and solo review. Its fixed B1 result is
  **negative**; [report](medium-dry-b1-updates-result.md) and failed gates
  remain. Post-merge main CI 44802207887 is separately pending at this entry.
- **Next question:** saved B4 policies show input-dependent uniform-versus-
  linear average direction. The [prospective four-stratum contract](river-uniform-readout-spots.md)
  fixes structural selection, same-path control/candidate, seeds, work,
  thresholds, source checks, compute caps and publication order before any
  new input or score. Earlier templates and outcomes remain known evidence.
- **State:** protocol drafting only; no selection, profile or training job.
  Codex assisted; human hands-on time not recorded.
- **Isolated source before selection:** added structural selector, same-path
  B4 runner/capture, source/publication gates, conservative forecast,
  comparison-only audit, fixed reporter and control-ranked decision trace.
  The [prospective diagnostic addendum](river-uniform-readout-diagnostic-addendum.md)
  fixes the pooled control ranking and 900-second trace cap without changing
  the original protocol. Nine focused new/historical tests pass; Ruff,
  formatting and strict mypy pass on 14 new source/test files. An initial
  test fixture directory error was corrected; no scientific job ran.
  Full exact-source qualification remains pending. Codex assisted; human
  hands-on time not recorded.
- **One frozen cohort, still before outcomes:** source checkpoint `984ba8a`
  and its hosted Python 3.11/3.12 CI passed; full pre-cohort local base3.11
  passed 5,746 tests/73 skips/150 deselections, Ruff, format and strict
  mypy. The one fixed PCG64 selector wrote four legal
  [spot inputs and hash freeze](../configs/river-uniform-readout-freeze.json)
  with structural attempts 13/5/1/11. A read-only independent check passed
  all file hashes, disjoint cards, weighted ranges, positions and exclusion
  of all 15 prior rank signatures. No game tree, policy, score or profile was
  built. Next: publish/verify this cohort, pin its commit and qualify exact
  source. Codex assisted; human hands-on time not recorded.

- **Post-freeze source guard and legality:** the first read of the frozen
  cohort failed because the new guard compared sorted file keys with unsorted
  stratum order. The ignored failure receipt at
  `results/runs/river-uniform-readout-source-20261120/cohort-pin-first-failure.json`
  preceded an isolated guard fix and regression test. Cohort and protocol
  bytes did not change. The fixed guard checked four hashes and source
  fingerprint. Frozen tree construction passed without training or scoring:
  each medium input has 21,303 exact nodes/3,336 candidate rows; low/wet has
  2,295/372; recall violations zero. The local log at
  `results/runs/river-uniform-readout-source-20261120/cohort-tree-check.log`
  is ignored. Next: publish tested source pin and complete all exact-source
  checks before proof. Codex assisted; human hands-on time not recorded.

## 2026-11-17 — Close allowance correction; plan nested archive measurement

- **Issue:** #4. [PR #84](https://github.com/jimmy-sim/poker-ai/pull/84) merged at
  b852436 after all six final roles passed on 49cb951. Local bases: 5,081 tests
  each (900.69 / 880.55 seconds); optional: 1,987 each (745.01 / 527.81 seconds).
  Hosted bases: 5,081 each (1187.64 / 1170.17 seconds), actual runtimes and full
  checkout trees verified. Both retain 68 skips / 150 deselections; the hosted
  historical warning remains. Earlier failures are preserved.
- **Main:** 419 focused tests in 95.63 seconds; complete saved pair authenticates;
  all three numerical exports match, 27 raw files and ten unrelated local changes
  remain unchanged. [Closing receipts](../results/source-phase-cpu-v2/final-ci/manifest.json).
- **Next question:** separate context building, sampled-state decoding/scoring,
  direct full decoding and prior full verification inside archive validation.
  [Prospective plan](parent-archive-cpu.md) published before implementation, with
  401 calls per cost read / 802 per complete pair. Existing source, inputs,
  seeds, scientific work and caps stay fixed. No optimizer or new training yet.
- **Implementation:** temporary nested caller aliases, strict saved-data tree
  reconstruction, complete runner and data-only report, previous numerical
  identity pinned separately from the original 128 scientific input pins.
  Both focused suites: 139 passed / one plotting skip, 24.99 / 23.86 seconds.
  Ruff/format pass; full strict typing passes 816 files. Initial stale 14-call
  assertion retained below, corrected to the prospective 802-call design.
  All six complete source qualification roles still precede formal collection.
- **Attribution:** AI-assisted implementation, execution and drafting. Human
  hands-on time not recorded; no personal learning outcome inferred.

## 2026-11-10 — Full matched-update pipeline, prospective

- **Issue:**#4; [detailed plan](matched-update-pipeline.md) and config published
  before code/outcomes. Complete the unchanged24-context/48-target design,
  full original-B1 barrier and144new/144reused profiles,1152new/reused targets.
- **Compute:** all72 timing repeats; original2*(2*training+600)<7200, full added
  old-policy overhead<600, comparison-only native overhead2*elapsed<900.
  Real own/native7200/900 and shared tiny-proof180 caps unchanged.
- **Preservation:** freshly hashed all ten current unrelated main modifications;
  isolated research/matched-update-pipeline from latest GitHub main88ebfba.
- **Direction:** continuing model research and reported user learning, not
  contribution counts or inferred human hours. Codex-assisted; hands-on unknown.
- **State:** planning only. Full source checks/proof/forecast/published admission
  precede actual long trajectories; no native/reference output enters training.

## 2026-11-09 — Matched-prefix capture, prospective software only

- **Issue:**#4; [bounded plan](matched-prefix-capture.md) before implementation:
 24logical tiny cases/48targets/144own policies/96raw ledgers, complete immutable
 archive/replay and independent exact arithmetic. No actual Holdem score/path.
- **Implementation:**22focused checks pass each1.84/1.95s;144policy/96mass
  IO,384exact-boundary/72work checks, independent terminal/pure-response math;
  retained pre-input/dirty-source/partial/timeout/archive failures. Temporary
  clean-source fixtures preserve main's ten modified outputs. Counts/hashes
  exact; replay error uses existing1e-12fixture-chip tolerance. Ruff/format553/
  strict455. Final source/full checks running; no accepted published proof yet.
- **Published checked proof:**sourceCI42645030455bothgreen;218-fileSHA5f168559...
  sourcegatebf9024dpublished first. Fullbase1957+24skip each264.38/251.57s;
  extras1990each294.89/286.15s;73focused each2.45/2.46s. Clean toy proof
  0.707454291s<180,144policies/96masses/384boundaries/72work; independent
  error3.3306690738754696e-16fixturechips. Base312
  reader0.223499291s, constructorsblocked. Actualpublished regression
  added; finalartifactCI pending. No realHoldem/native/forecast/admission.
- **Parent merged:**PR38at6f22103afterfinalCI42644211540bothgreen; main51tests
  0.80s/metadataCLIpassed;tenuseroutputsintact. Source/data historicalbytes kept.
- **Gate:** fixed180s software stage, complete local/hosted source checks before
 published clean proof. Future7200/900 caps and own/native runner/forecast/
 admission remain; no future work schedule. Codex; personal hours unrecorded.

## 2026-11-09 — Matched-update batch foundation, prospective

- **Issue:**#4; [prospective design](matched-update-batches.md) and fixed config
  select ALL48 endpoint iteration targets by metadata, not strength.144new B1
  readouts/144reused batched readouts;1152new/1152reused fixed targets planned.
- **Implementation:**50focused checks pass each1.13/1.12s (28observer/22grid),
  six16-step independent tiny trajectories; original work-observer parity and
  both-book/RNG/current/work mutation guards. Actual source manifest validates
  nine hashes/complete native receipts without training/reference construction.
  Ruff/format547/strict450 pass; full local and hosted checks running.
- **Complete checks:**base1947+24skip each266.13/255.43s; extras1980each
  296.34/282.65s. Strengthened every16boundary assertion passes28observer tests
  each0.15/0.16s after those full suites; no production-code changes. Final
  hosted run remains required. Journal navigation added; no long admission.
- **Published grid:**sourceCI42641272661bothgreen ond37e610; clean-source
  plan.json records48targets(18,727–146,972updates), all within B1 sourceendpoints,
  144profilepairs/1152reusedfixed targets;9inputhashes verified. New published
  metadata regression recomputes all targets; final artifactCI pending.
- **Viewer merged:**PR37at0e8b422 afterfinalCI42638459644bothgreen. Main24tests
  0.26s and actualn/p/qCLI pass;10originalmodifiedoutputs untouched.
- **Bounded scope:** grid validation and mutation-guarded mixed work/iteration
  observation tests only. No actual Holdem replay/score or long admission.
  Full7200+900 caps plus verification cannot fit tonight; no shortened run or
  future schedule. All source/data preserved. Codex; personal hours unknown.

## 2026-11-09 — Offline saved-strategy viewer, prospective

- **Issue:**#4; [prospective acceptance](batch-strategy-viewer.md) fixes a
  read-only saved-policy comparison and optional n/p/q terminal browser before
  implementation. Distribution L1 is not EV loss or playing strength.
- **Actual verification:**24fast+3actual-archive checks; fullbase1897+24skip
  each270.11/257.66s, extras1930each298.10/285.85s;3actualsource checks each
  65.71/62.01s, constructors blocked. Default3.11 and n/p/q3.12CLI pass.
  Ruff/format541/strict445. No source/data edits; final hosted CI pending.
- **Dependency merged:**PR36de4755d, finalCI42635166354bothgreen; main2checks
  0.32s/full216+1728replay0in47.488662458s/6filesbyteequal;10userhashes intact.
- **Scope:** verified own archives/complete published audit chain; only acting
  player's own cards and public board; preserve all old scientific source/data.
  New focused tests, actual CLI and full relevant checks/hosted CI required.
- **Assistance:** Codex; hands-on time unrecorded. No training or new schedule.

## 2026-11-09 — Saved batch current policies, independently audited

- **Issue:**#4; [plan](batch-current-diagnosis.md)/config fixed before batch
  outcomes, code or diagnosis. All216 saved currents; final72currents+144averages
  versus all4 original same-context full controls, both seats:1728 fixed targets.
  No training/policy edits or favorable subsets. Source study/audit still running.
- **Independent audit:** all216+1728targets pass164.198028083s<900, maximum
  2.0605739337042905e-13 chips; included own replay0in41.213945417s. Own10df9be
  published first. OpenSpiel2.0.2Apache2 comparison-only; no actions exported.
  Two actual-evidence metadata/byte checks pass each0.21/0.22s; source216 intact.
  Complete writeup/3interviewanswers/verifiedclaimdrafts/license/README/journal39
  updated; final artifact CI pending. Hands-on time unknown; Codex-assisted.
- **Own result, published before reference:**216currents/1728fixed targets complete
  in156.781172375s<3600. Own replay0chips40.945068375s; base3.12 full replay0
  40.166751417s; all6numeric files byte-identical and3actualfigures inspected.
  Latest policies remain much more self-exploitable in the medium game, while
  fixed-original-opponent gains often favor them. All cases retained; no pure
  variance/default/fresh/global claim. Independent216+1728audit pending.
- **Admission:** source gate5e9937apublished first; full source own/native
  input chain and seven hashes bound in a new saved-data admission. At06:16
  full3600own+900native plus verification fit this one-time window. Publish
  admission before diagnosis; no training or strategy changes permitted.
- **Source gate:** both CIjobs42630704951passed on2aa8f39;216-fileSHA
  9968baff2397ac3ea4b297700b4392ece2b94f38a9b0fa2800bd5af0b9330337.
  Base1871+24skipeach299.91/294.70s; extras1904each331.87/320.05s;65focused
  each57.20/67.49s including18slow; strict440/format534/Ruff. Final3toyfigs
  inspected. Publish source record before admission/anyactualdiagnosis.
- **Implementation:**47 focused fast checks pass, independent exact path/reply
  math, self-zero signs, real Git-tree checks, source/native schema/failure gates.
  Analytic-only216/1728process/archive exercise16checks pass15.68s; three toy
  figures inspected, legends moved off data. Full checks running; Ruff/format534/
  strict440 pass. No actual diagnosis or source admission yet.
- **Gate:** complete published own+native first; new source checks/admission before
  scoring, own evidence before native;3600own/900native, only if full caps and
  verification fit authorization. Preserve all failures/source/data. No default/
  fresh/global claim. Codex-assisted; hands-on time unknown.

## 2026-11-09 — Reduced-backend fixed-work study, complete

- **Issue:** #4; [plan](reduced-batch-study.md) and config precede code. The
  reduction72-prefix/216-timing outcomes remain pending; absent/failed evidence
  blocks admission. Prepare an explicit backend adapter and complete tiny-game
  archive gates without changing old source, design, seeds, work or caps.
- **Published-evidence regression:**2tests pass on each base runtime33.99/31.86s,
  constructors blocked;480own/nativechain/3archivehashes/4numericfiles checked.
  Strict419/format512; finalartifactCIpending, scientificsource205unchanged.
- **Independent audit:**169.194451625s under900; all480profiles pass,maximum
  scalar/root error1.5631940186722204e-13 chips. Ownpublished67c5894before native.
  Nativeincludesownreplay115.699832292s; base312ownreplay0/113.263148750s,
  four numerical files byte-identical and native receipt validates data-only.
  Three interview answers/verified claim drafts/limits recorded; no global/default
  admission. Source205files unchanged throughout.
- **Complete own calculation:**1502.599063166s under7200;480profiles
  (432new+48reused),432mass/216current,144baselinechecks; ownreplay0chips/0unitless
  in86.302381583s. Four figures inspected. PrimaryB4signedlinearq8 mean total
  4.354031565→2.172683537%pot, one seed worsens; clippedmode remains mixed.
  Publish allown evidence/3archives before any new-policy native. Base312/native
  checks pending at this publication; no default/fresh/global admission.
- **Admission:** software proof11c5758 and observed code receipt90f3a9e
  published first; new checked admission binds all8 prerequisites/current205
  source files and unchanged6953.920827419guard. Published before long learning;
  at05:15Pacific full7200own+900native plus verification fit this window.
- **Source/software gate:** both jobs42622026217passed on d568f1f;205-file
  SHA3c4cda2030ed59748b94a51ef071fe84533c22d8ee9f5e843383f05a79665212.
  Base1822+24skip each265.07/254.26s; extras1855each295.38/285.34s;62focused
  each37.61/50.97s including24slows; Ruff/strict418/format510. Formal9.008274959s
  tiny-game proof480/432/216/144identities/replay0, base312readerpassed.
  Publish proof/code/admission in order before new long trajectories.
- **Implementation:** explicit new factory/own format/native adapter;62 focused
  optional checks pass37.39s, Ruff/format510/strict418. Complete tiny-game archive
  and source/admission gates tested; full suites/hosted checks pending.
- **Acceptance:** full local/hosted source checks, published software proof and
  checked admission before long learning; all144 B1 prefixes before B4/B16;
  own7200/native900, complete inventories, own publication before native.
  No long run unless full caps and safe verification fit this authorized window.
- **Assistance/time:** Codex-assisted; hands-on time unknown. No outcome or
  stronger/default/fresh/global claim at this prospective checkpoint.

## 2026-11-09 — Batch reduction dispatch, prospective

- **Issue:** #4; [plan](batch-reduction.md) and fixed config precede code.
  Published raw cost evidence motivates the same array reductions through methods,
  preserving all validation/arithmetic. New optional backend; frozen old source/data.
- **Complete forecast:**216 rows/72 paths,144 repeatedB1checks, all old
  state/work identities exact;65.922444291s under900. Same guarded
  formula6953.920827419<7200; base3.12 two reportfiles byte-identical.
  Old7201.492438542failure retained. Historical timings are unpaired, no causal
  speedup or strength claim. No long admission yet.
- **Own correctness:**72 endpoints/48B1readout checks all exact; 27.067313916s
  under900, base3.12 offline replay passed; published before216timings.
- **Source gate:**3a1a3c9; both CIjobs42619839287passed. Base1784+24skip
  each,extras1817each,3slowintegrations each; strict405/format496/Ruff. Formal
  source receipt published before actual72prefixes and216timings.
- **Implementation:**84 focused checks pass; Ruff/format496/strict405. Full
  base/optional, tiny-game process and hosted checks pending. Explicit new factory,
  all72 exact endpoint controls before216timings, no patch to frozen old code.
- **Acceptance:** independent math/invalid/alias checks, exact tiny trajectories,
  full local and hosted source checks before all72 realprefixes/216timingrows.
  Same formula/grid/seeds/7200own/900native; retain old failure and all new outcomes.
  No optimizer result, long admission or stronger/default/fresh/global claim yet.
- **Main cost merge verification:** PR33 merged9895452,51 focused tests pass
  in0.18s; all4 offline numerical files identical;10 useroutput hashes unchanged.
- **Assistance/time:** Codex-assisted; hands-on time not recorded.

## 2026-11-09 — Batch function costs, checked source

- **Complete own cost evidence:** 21.733298041s under900; all48 archived
  endpoints exact,32 repeatedB1checks,24 completeprofiles/3,456frames/5,896edges.
  Base3.12 offline replay reproduces all four numerical files byte for byte;
  both real figures inspected. Raw costs published before any optimizer.
  Mean directall/any callee totals1.121222/1.097186s forB4/B16 include reduction
  work; mean inclusive time includes traversal. No strength/forecast/admission.
- **Checked source:** `0a86ca8`; both hosted code jobs passed in run
  [42616172811](https://github.com/jimmy-sim/poker-ai/actions/runs/42616172811).
  Corrected base1,700+24skip each; extras1,733 each; five slow integrations each;
  strict394 and format483. Formal cost-only source receipt published before
  actual short prefixes. No Hold'em cost outcome at this checkpoint.
- **Issue / question:** #4, after the retained 7201.492439s forecast failure.
  Profile actual function costs before optimizing; [plan](batch-overhead.md) and
  config precede code/outcomes. No unchanged timing retries or relaxed caps.
- **Fixed scope:** All 24 first-seed paths across both games/encodings/regret
  rules and B1/B4/B16; plain plus instrumented copies (48 endpoints), three
  workers, separate900s cap. Exact archived state/work/readout/prefix identities,
  complete function/caller ledgers and independent call/work accounting. Whole
  measure instrumentation; inclusive mean time includes traversal and is not
  validation-only cost. No optimizer, EV scores or long admission in this step.
- **Prior verification:** PR #32 adds two actual published-data replay tests,
  base3.11/3.12 pass5.69/5.73s. Actual clean-source admission rejects the failed
  forecast. Final artifact CI42609429095 pending at97234bb; no new-policy native
  audit or long study claimed. All historical source/data/failures remain intact.
- **Status:** Prospective only. Codex-assisted; human hands-on time not recorded.
- **Tested implementation:** 49 focused fast checks pass; all five new relevant
  integrations pass each optional runtime (57.30/67.82s while full checks ran).
  Actual three-process software exercise retains all 48 endpoints/24 cProfiles,
  exact old states/counters and independent visit/sample/mean call identities.
  Full runner/report serialization and offline reader pass; four numerical files
  recreate byte-identically and two explicitly software-only plots render. Real
  recursion verifies different function/caller count tuple orders. Failure
  receipts distinguish requested, attempted and completed training. Synthetic
  CI/call ledgers test schema only. Full base/optional and hosted checks remain
  before any actual Hold'em cost prefix; no optimizer or new forecast/admission.

- **Pre-measurement correction:** Review finds standard pstats labels can merge
  generated constructors with the same file/line/name. Raw cProfile extraction
  now retains every code entry and caller edge, using portable structural code
  identities plus distinct entry IDs. Two regression cases cover different and
  identical generated code sharing a label. 51 focused fast checks pass; complete
  local/hosted checks are required on the corrected collector before any actual
  Hold'em cost measurements. No learner, seed, work or scientific gate changes.

## 2026-11-09 — Frozen-pass batches, complete failed compute gate

- **Issue / question:** #4; does averaging independent frozen-policy traversals
  help at the same work, despite fewer updates? [Plan](frozen-pass-batches.md)
  and fixed config precede implementation and outcomes.
- **Design:** B1/B4/B16, 72 paths with two dependent average books; 432 new
  profiles plus 48 reused full controls. Exact baseline prefix barrier, complete
  conditional-variance proof and fixed 216-row timing forecast precede a possible
  7200s own study. Separate timing/native 900s caps. No selected/default/fresh or
  global admission, and no modified historical data, seeds, caps or gates.
- **Status:** Plan only; no new training, timing or results. Codex-assisted;
  developer hands-on time not recorded. The previous fallback result is complete
  and awaits final artifact CI/merge on PR #31.
- **Prospective clarification:** Replace the copied previous-stage native role
  wording with this plan's already-declared 480 self profiles and river hybrids;
  no fixed-opponent grid is part of this new batch plan. No cases or gates change,
  and no timing/training outcomes have run. PR #31 is now merged after both final
  hosted jobs passed at `b6d1076`.
- **Before measurements:** Retain all 432 cumulative ledgers and 216 current
  observations so coverage and movement can be independently replayed offline.
  Warm mass is reconstructible from the unchanged two uniform expected passes.
  Storage adds no training paths, selection, scores or changed compute gates.
- **Tested implementation:** 101 focused fast checks pass; all 23 new relevant
  slow checks pass in both optional environments (37.05/36.96s while base suites
  also ran). Complete three-process tiny-game IO replays 480 profiles, 432 masses,
  216 currents and 144 baseline prefixes with zero error. Rehashed corruption,
  source/work/grid failures and baseline barrier rejection pass. Four exact
  conditional-moment cases (54 tapes/972 independent B2 products) agree within
  2.8e-16 fixture units; 120 dense batch parity checkpoints include 40 B1
  dual-book original matches. Two old own Hold'em profiles pass the real native
  adapter, without new training. Fictional CI/native receipts are schema checks,
  not external evidence. Full base/optional fast suites and hosted code CI remain
  pending before actual timing or long learning.

- **Complete checked source:** Code `48c0960`, inventory SHA
  `62bbea13782a0d4468000fc01cbf34a83810fdc42c738098f1ec0a3f1dbb18cd`.
  Base 1647 passed /24 skipped each (230.21/230.30s); optional 1680 each
  (258.63/248.43s); strict typing 381, format 469, hooks pass. Both hosted jobs
  [42606554182](https://github.com/jimmy-sim/poker-ai/actions/runs/42606554182)
  pass before measurement. Base Python 3.12 archived loader with all learner/native
  constructors blocked passes 4.568871s. All four toy figures inspected.
- **Source-bound correctness:** Formal receipt passes 6.3355535s at the checked
  code revision, complete four moment/120 parity/480 profile/432 mass/216 current
  software grids and 144 baseline prefixes; replay errors zero. No new Hold'em
  timing or long learning yet. Publish correctness and observed code checks
  before the unchanged 216-row timing gate. Method adds the chart guide and
  three interview answers; no stronger/default/fresh/global claim.

- **Retained timing gate:** All 216 rows/72 paths complete in 55.257181459s
  (900s cap); repeated states and 144 repeated B1 source readouts match. Raw
  [profile](../results/frozen-pass-batches/profile.json) retains every seed/repeat.
  Training-only phase-max sum 1500.373109635s; fixed
  guarded forecast 7201.492438542s exceeds 7200 by
  1.492438542s. Stop before long learning; no new strength
  scores, admission or default. This is planning sensitivity, not actual full
  runtime. Parent/child CPU 4.679161/151.14s.
  Preserve failure; profile real costs before optimizing rather than rerunning
  unchanged timings to find a pass.

## 2026-11-09 — Saved-window fallback, prospective

- **Issue / question:** Continue #4 after the completed averaging-history study.
  Does the uniform fallback at zero-window-mass rows affect its saved late
  policies? Missing mass alone is not proof of weakness; full controls can have
  unreachable rows. [Plan](window-fallback.md) and config precede implementation
  and intervention outcomes. No new Hold'em training or selected agent.
- **Fixed design:** All 128 original suffixes; raw/seat0/seat1/both fill from the
  same own whole average, only exact-zero rows. 512 self profiles, 2048 fixed
  opponent conditions, full-control realization equivalence and complete 2×2
  BR accounting. Original source/data/caps/gates remain frozen; this saved-policy
  stage has separate 900s own/native caps. Tests/local/hosted checks precede
  measurement; own publication precedes reference comparison.
- **Status:** Prospective only. Codex-assisted; human hands-on time not recorded.
- **Software progress:** 107 focused fast checks pass. Complete tiny-game checks
  exercise all 512 self profiles/2048 fixed targets with training/reference
  construction blocked during the offline stage (four checks, 11.26s). Complete
  toy archive replay and rehashed corruption tests pass all 19 checks (13.73s).
  The real old-window loader passes on base Python 3.12 with new learning/native
  construction blocked (100.72s), retaining every 128 original window.
  Own/native receipt failure tests and four explicitly toy figures pass (22
  run/report checks, 25.58s); layouts inspected. Fictional byte/native ledgers
  test schema only and are explicitly not independent solver evidence.
- **Before outcomes:** Retain eligible/changed row counts and uniform/own reach
  measures separately for all rows and river rows, by seat. This makes the
  declared reach question inspectable; no masks, cases, gates, caps or metrics
  selection are changed. Complete source/reader/report/native code drafted;
  full base/optional checks and hosted code CI remain before intervention outcomes.
- **Complete local code checks:** Base `make check`: 1546 passed /24 optional
  skips on both Python versions (242.25/232.58s). All-extras fast suites: 1579
  passed each (274.70/268.50s). All 27 relevant slow checks pass (169.41/166.45s),
  including 26 new checks plus the earlier real-policy native adapter. Base-only
  Python 3.12 toy replay/report: 20 passed /one plotting skip (30.11s). Strict
  typing covers 358 files; lint/format/hooks pass. No intervention outcomes yet;
  both hosted complete-code CI jobs remain required before measurement.
- **Checked code before measurement:** Both
  [42596478622](https://github.com/jimmy-sim/poker-ai/actions/runs/42596478622)
  jobs pass on `815d4700800248a9ec70fc295f8c34f64ec101f8`. The complete source
  inventory SHA is `c6f6761915cb106c6117bc233b76afd3d0659aad69c69ba051556b4243956f31`.
  Publish these observed checks and the plot-reading guide before the clean
  saved-policy run. No Hold'em intervention outcomes have been measured yet.
- **Complete own evidence, native pending:** All 128 original windows produce
  the planned 512 profiles and 2048 fixed target conditions. All 128 raw controls
  and additive panels pass; all 32 full windows preserve realization and required
  values exactly (maximum changes zero). Own archive replay has zero chip and
  unitless error in 94.142837s. Own stage 285.478070s under 900s, including
  94.552135s upstream replay; parent CPU 285.363828s, reaped child CPU 0.07s.
  Seven numerical files and four figures retained. Publish complete own outputs
  before independent comparison; no complete native claim at this checkpoint.
- **Independent comparison:** After own publication `3fa97c4`, every 512 self
  profile /2048 fixed target /128 accounting panel passes the pinned native
  audit. Stage 332.709628s under 900s, including 193.038860s complete own/upstream
  replay with zero error; parent CPU 332.593217s, reaped child CPU 0.07s.
  Maximum scalar discrepancy 1.6342482922482304e-13 chips; fixed-difference
  discrepancy at most 2.842170943040401e-14, both below 1e-9. All 128 cached
  opponent/target identities verified. All four final figures inspected.
- **Cross-version reproduction:** Base Python 3.12 replays the complete old/new
  chain with zero error in 187.900927s, validates the independent receipt and
  regenerates all seven numerical files byte-for-byte.
- **Finding / limits:** Medium range-mass clipped/linear sampled means change
  half-window 2.531900→2.531738% pot; short-window 4.888556→4.869954%. Two
  half-window raw seeds worsen. Across all 96 sampled both-fill windows, total
  differences span -0.073002 to +0.000529 percentage points. This one declared
  completion makes a small change; it is not a bound on all alternatives or a
  training-cause proof. Full controls show why missing uniform coverage can be
  harmless under actual own reach. README, full method/limits, three interview
  answers and journal step34 updated. Original failed limits/defaults preserved.
- **Next:** Separately preregister within-pass sampling batches and their
  correctness/compute tests before new learning. No batch method or stronger
  agent is admitted by this saved-policy diagnosis. Final artifact CI pending.

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
- **Checked source / forecast:** Both hosted jobs
  [42584867420](https://github.com/jimmy-sim/poker-ai/actions/runs/42584867420)
  pass on `432908e`. Clean source-bound correctness completes in 9.559915s,
  with 192 toy prefixes, 512 profiles, 192 mass boundaries, 160 current pairs,
  2048 fixed targets and zero replay errors. This is explicitly toy software proof.
  The complete 64-case historical forecast is 5328.971368s, below the unchanged
  7200s own cap. Historical partition sums: 1032.242842/1031.129947/1021.501461s.
  Forecast is a planning guard, not measured new runtime or human hours. Publish
  correctness before recording and publishing checked admission; poker still pending.
- **Admission:** `results/averaging-history/admission.json` binds clean checked
  code `432908e`, actual CI run 42584867420 and complete local checks to the
  published correctness receipt. Scope is only the same original trajectories.
  This admission is published before starting the replay; all 64 cases, original
  prefixes, fixed seeds and caps remain required. Native study follows own publication.
- **Complete own evidence, native pending:** All 64 original trajectories and
  192 exact original prefixes pass. Retain 512 profiles, 192 raw boundaries and
  2048 fixed target conditions; all 160 current-weight pairs match. Full own
  archive replay takes 88.728334s with zero chip, unitless and identity errors.
  Own stage 1136.768864s, parent CPU 100.041639s, reaped child CPU 3099.32s,
  below 7200s. Six figures and all six numerical files generated. Publish these
  own outputs before independent audit; they do not yet complete native validation.
- **Independent audit:** After own publication `c0df957`, all 512 self profiles
  and 2048 fixed target conditions pass OpenSpiel 2.0.2 scalar comparison.
  Maximum discrepancy 2.4158453015843406e-13 chips, below 1e-9. Native stage
  237.653849s under 900s, including 99.214009s complete own input replay with zero
  error; parent CPU 237.495094s, reaped child CPU 0.07s. All 128 fixed-opponent/
  target reply identities checked before reuse. Reference output never trains
  an agent. All six figures inspected; raw numerical and seed results retained.
- **Read-only cross-version check:** Base Python 3.12 replays all profiles,
  boundaries and fixed matches with zero error (95.666413s), validates the archived
  native receipt, and regenerates all six numerical files byte-for-byte.
- **Finding:** In the motivating medium range-mass clipped/linear sampled context,
  mean total is whole 2.501852 / current 9.519793 / half-window 2.531900 /
  short-window 4.888556% initial pot. Current within weakness persists in every
  seed; late windows do not provide a general repair. Old fixed-opponent mean EV
  can improve while self exploitability worsens. All modes/seeds and unfavorable
  raw conditions retained. Warm whole coverage does not establish late support.
  README, method/limits, three interview answers and journal step 33 updated.
- **Next decision:** Prospectively test only zero-window-mass fallback on saved
  policies, distinguishing harmless unreachable rows from a missing-update effect
  before another learning rule. No new default, selected suffix, stronger-agent,
  fresh/global admission or relaxed failed limit. Final artifact CI pending.
- **Merged / main verification:** Both final CI 42589812391 jobs pass at
  `0035658`; PR #30 merged at `687d9bf`. User main passes 193 focused checks
  (2.70s), all profile/boundary/fixed-target replay with zero error (97.326688s),
  archived native audit and all six byte-identical numerical files. Ten original
  modified output hashes are unchanged. Next protocol is isolated in PR #31.

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

### November 10 — real factories and unscored capture barrier (PR #40)

Added new modules, preserving historical source/data. The real factory validates
all pinned receipts and produces all24 contexts,48 targets and72 old B1
work-crossing expectations (both readouts, current, both raw ledgers and full
state). Actual constructor-blocked source load passed in30.006725459s without
training or constructing a reference. This is setup evidence, not a forecast.

Capture writes immutable unscored policies and raw masses; no profile is scored
until the complete cross-context barrier passes. Tests compare separate
uninterrupted tiny trajectories, duplicate numeric target identities, signed/
clipped rules, corruption of each state component and partial disk failure.
Full source suites, native integration and admission remain pending.

### November10 — full-shape own IO and native scalar adapter (PR #40, draft)

Implemented the new scoring/archive/replay and comparison primitives. The full
explicit tiny fixture exercises144 captures,144 scored versions of those same
policies,96 raw ledgers and1,152 fixed targets. Its independently generated right
profiles intentionally equal the left policies: every paired gap is zero.
Twelve own integration/corruption/failure tests passed in22.54s.

The native adapter exports the actual array game to OpenSpiel2.0.2 and requests
only values and best-response roots. Its first tests caught nonconsecutive
per-player information numbering; fixing the exporter made all6 scalar tests
pass. Eighteen full-shape native/schema/failure tests passed in2.82s, checking
all144 self profiles and1,152 fixed targets, missing/duplicate rows, wrong policy/
reply hashes, nonfinite values and cap/flag/count corruption. These are local
software tests, not the separately source-bound published proof or poker data.

Re-read the installed Apache2.0 license before optional native tests: pinned
SHA256 cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30.
The real-run admission entry currently fails closed; complete checks, source-bound
software proof and the prospective compute gate remain required.

### November10 — fixed forecasts, timing aliases and admission implementation

Added72-row max-per-context/fixed-partition forecasting with the unchanged
2*(2*training+600)<7200 rule; all17 synthetic timing tests pass (0.05s), including
strict failure at7200. New old-policy overhead corpus keeps the actual original
B1 final work/iteration and exact saved policy/mass hashes while duplicating only
logical timing labels;2 metadata tests passed in0.42s. It does not claim new
prefix outcomes or a new B1 barrier replay. The separate source and runtime gates
remain mandatory. New command entry points expose source checks, tiny proof,
profiling, admission, study, independent audit and offline replay/report.

Added raw worker completion/partition checks, shared-clock expiry and native
constructor failure retention. Four pre-input/shared-source/fake-admission tests
passed in0.07s. The latest combined optional focused run passed140 tests with5
slow tests deselected in26.17s; subsequent gate/corpus additions have their own
results above and final broad checks remain pending. Four actual MatrixTree
exporter/value/root/own-reply correctness checks passed in3.32s using uniform
policies on both original spots and both representations, without poker training.

The earlier fail-closed admission placeholder has been replaced by a checked
reader that requires the full source-bound tiny proof, all72 real short timings,
complete old-policy own/native overhead and published exact-source admission.
No such admission exists yet; no new real prefix or long trajectory has run.

### November10 — production event ordering regression found during review

Review of the production collector found that fixed-target rows were ordered by
opponent before policy, while the offline reader expects policy/opponent/seat.
The explicit regression failed on d02492a (1failed in0.22s), even though the
earlier synthetic pipeline bypassed that collector. Corrected the collector's
canonical fixed-row order and added the regression alongside worker checks.
No actual profile or new poker trajectory had run. Current full base checks
started before this correction are baseline information only; the corrected
source needs new complete local/hosted validation before any admission.

The full tiny exercise now routes its records through the actual production
collector instead of maintaining a separate list order. It explicitly labels
sequential fixture event routes; it does not pretend to have spawned workers.
The added full-shape regression fails if the old bad order is restored. Targeted
own/native/worker checks passed45 tests in28.41s; the added full-shape bad-order
test passed in2.72s. Training initialization is recorded separately from a request
so a failure before actual initialization does not claim completed training.

The tiny archive reader also previously regenerated fixture learners. It now
loads saved OWN fixture inputs/controls/replies and validates their bytes and
achieved values without learner construction. The full archived-input replay
with the learner factory blocked passed in3.51s. Baseline d02492a base suites
reported2033 passed/44skipped/143deselected each (292.24s and291.61s), but these
precede the correction and are not used to admit the final source.

### November10 — historical replay versus fresh-source admission

Review found that the current-source inventory check also blocked historical
data-only readers after any future SRC addition. A regression reproduced that
rejection (1failed in1.08s). Read-only mode now checks every original byte and
the original complete checked commit, while permitting added modules. Fresh
proofs/profiling/native audits/admission still require the entire current source
to match the tested cohort; explicit fresh-proof/native source checks were added.
Twelve source-gate/pre-input/fresh-proof tests passed in0.09s. No original-file
hash, cap, seed, tolerance or performance gate was weakened. a5fffa4 full base
checks passed2036 tests on each Python version (305.69/305.45s), but the new
source-gate correction requires a new complete source validation before use.

### November10 — final complete source gate passed at06a3402

Source06a34023ae13127018346d5e888b0c50abe304b9,242 mapped files, SHA256
a516f6c59105c701d91d5d9d2c802dc8cba5cf4cb00037064d50dd3319999887.
Both hosted jobs passed in [run42792838522](https://github.com/jimmy-sim/poker-ai/actions/runs/42792838522).
Final local base:2044 passed/44optional skips/143slow deselected on each version
(311.26/312.28s); optional:2097 passed/143slow deselected (372.20/360.08s);
relevant slow integrations:59 passed/8deselected (266.72/256.99s). Ruff lint,
590-file formatting and491-file strict typing passed. Python3.11.17 optional
checks used original NumPy2.4.6; Python3.12.15 used NumPy2.5.4. Base environments
used2.5.4 and are software/data evidence.

[Source receipt](../results/matched-update-pipeline/code-checks.json) and six
byte-hashed test logs retain actual commands/results. This admits the next
source-bound tiny software proof, not real poker trajectories. Full tiny
own/native proof, fixed forecast/overhead and checked published admission
remain prerequisites for the long matched-update study.

### November10 — published complete source-bound tiny own/native proof

Generated from clean3d4ec03 with the checked06a3402 source cohort. Own proof
completed in4.531098915991606s:144 unscored captures,144 scored versions of the
SAME policies,96 raw ledgers,72 source crossings and1,152 fixed targets/paired
conditions. Offline own replay error0. Own evidence and all three archives were
pushed at [9fb1cf1](https://github.com/jimmy-sim/poker-ai/commit/9fb1cf1e85f5910d1ac27d4a211ac1cd14f8d8c8)
and its GitHub workflow was observed before native construction.

The full independent native144/1152 scalar audit and final OWN replay completed
in34.524477458006004s on the ONEshared180s clock, including the publication
interval. Maximum native error2.220446049250313e-16fixture chips. No native
action/strategy was exported. Both learner/reference constructors blocked, the
base Python3.12/NumPy2.5.4 archived-data reader also passed. This is not real
trajectory replay and does not admit the long study.

[Own proof](../results/matched-update-pipeline/software-own.json),
[native proof](../results/matched-update-pipeline/software-native.json),
[data-only reader](../results/matched-update-pipeline/software-replay-312.json).
The24 logical labels share one tiny tree/six seed-rule paths, with identical
right-strategy controls; not24 independent poker games. Next: all72 original-
runtime short timings and complete old-policy overhead, then checked admission.

### November10 — correction: local runtime labels were wrong; gate closed

The assistant discovered that `uv run` respected the project's `.python-version`
3.11 and recreated both named base environments asPython3.11.17/NumPy2.4.6.
The earlier base312 check and the file named software-replay-312 were therefore
mislabeled. The optional312 command genuinely usedPython3.12.15/NumPy2.5.4, and
the hosted312 job passed, but these do not replace the missing local base312
check. Base311 NumPy was also incorrectly described as2.5.4; actual2.4.6.

The first tiny own/native arithmetic proof passed, including its shared34.52s
clock, but its prerequisite record is NOT eligible for real study admission.
All13 original receipt/log/proof/archive files are preserved byte-for-byte at
[superseded-environment-labels](../results/matched-update-pipeline/superseded-environment-labels/retention.json)
with SHA256s and original publication commits. The root code gate is explicitly
closed. No real prefix timing or new long trajectory has run. An explicitly
selectedPython3.12 local base check is running with machine-reported runtime
before/after; corrected receipts and a fresh eligible tiny proof must follow.
Earlier journal/log claims of local base312 and reader312 are superseded by
this correction; their numeric data have not been hand-tuned or discarded.

Both explicitly selected base runs now passed with runtime asserted before and
after:Python3.11.17/NumPy2.4.6 (2044passed,300.64s) andPython3.12.15/NumPy2.5.4
(2044passed,287.24s);44optional skips/143slow deselections each. The original
invalid-chain proof files are retained in the superseded folder and original
commits. Their root latest-attempt aliases are cleared for a new eligible proof.
Corrected source receipts will use parsed machine runtime headers, not directory
names. No real timing or new trajectory has run.

### November10 — corrected machine-identified source receipt published

Re-recorded the same checked06a3402 source cohort after both explicit base runs
passed. Runtime headers before/after match:3.11.17/NumPy2.4.6 and3.12.15/2.5.4.
Base counts2044each (300.64/287.24s), optional2097each (372.20/360.08s), relevant
slow59each (266.72/256.99s); hosted42792838522bothgreen. Metadata now comes
from actual header output; original invalid labels/bytes stay retained. The new
source receipt enables a fresh eligible tiny proof only. First attempt arithmetic
results remain historical, ineligible prerequisite evidence; no real timing yet.

### November10 — eligible tiny proof after corrected prerequisites

The fresh own proof completed in4.489952458011s after the corrected
actual-runtime source receipt was published. Its144captures/144scored/96ledgers/
72crossings/1152fixed conditions replayed with0 own error. OWN evidence was
pushed45929b9ef8f6adab81c10582625f632028f694ec and GitHub workflow42798325998
was observed before native construction. Native144/1152 plus finalownreplay
completed the ONEshared180s clock in30.472155417025s, maximumerror
2.2204460492503131e-16fixture chips.

The archived-data read now genuinely ranPython3.12.15/
NumPy2.5.4, asserted before and after, with learner
and reference constructors blocked. The first ineligible-chain proof and all
original bytes remain retained separately. This corrected eligible software
proof permits the first real short-prefix timing/old-overhead gate only; it
still does not admit a long trajectory, stronger default or global agent.

### November10 — first real original-runtime compute forecast, own stage passed

All72 short B1 timing rows completed, with exact original100k checkpoint checks
and repeated endpoint bits/work unchanged. Runtime3.11.17/NumPy2.4.6 was
asserted. Max-per-context/fixed-partition training forecast535.8363967065269s;
unchanged guarded formula gives3343.3455868261076s <7200.

The complete OLD-policy overhead corpus144captures/144scored/96ledgers/1152fixed
targets replayed in151.010662000044s <600. Full own profiling stage including
source/setup/72timings/overhead/archive/replay/report took238.368770834000s <900.
[Timing receipt](../results/matched-update-pipeline/profile.json) and
[old-policy corpus](../results/matched-update-pipeline/overhead/own.json).
All actual old iteration/work/policy/mass identities remain explicit; this is
not a new prefix strength result or an unpaired causal speedup claim. Publishing
complete own evidence now precedes comparison-only native overhead. The native
900s cap and strict2*elapsed<900 gate, then checked published admission, still
block the long study. No scientific cap, seed or tolerance changed.

### November10 — native overhead blocked by volatile manifest provenance

The first native old-policy overhead attempt FAILED before reference construction
or any scalar target. It retained0profiles/0fixed targets, no reference setup,
and `old-policy corpus/inputs changed`. Complete command wall30.607491416973062s;
this is a software-input failure, not an unfavorable poker score. No long study
was admitted. The successful own72-row forecast/151.01s overhead remains intact.

A metadata-only diagnosis recomputed the full timing corpus: every stable target,
readout, coordinate, policy identity and input hash matched. The ONLY differences
were `/source/git_commit` and `/source/git_status:length`: publishing own evidence
necessarily changes those fields. The reader incorrectly compared the entire
manifest, including that volatile provenance.

[Failed native receipt](../results/matched-update-pipeline/overhead/native.json),
[diagnosis](https://github.com/jimmy-sim/poker-ai/blob/95e8c8d6f89e4d05bdd526a455180f9e770bbc9e/results/matched-update-pipeline/overhead/reader-failure-diagnosis.json).
Next: a versioned parent IO adapter that preserves all existing scientific source
and data, validates original code/config bytes separately and compares every
stable corpus identity. Add lifecycle/failure tests, then recheck the expanded
source cohort and its proof/compute gates before any real trajectory. This is a
source repair, not permission for an unchanged favorable timing retry. Caps,
seeds, grids and tolerances stay fixed; retain all first-attempt outcomes.

### November10 — additive parent IO adapter, frozen reader reused

Added `matched_update_parent_io` and a pinned implementation contract, preserving
every existing scientific source byte. The explicit parent service delegates all
original receipt, worker, hash, archive and numerical checks. It validates every
stable corpus field and all original nested code/config bytes, then supplies the
saved provenance view to the frozen reader. Only publication HEAD/status may
differ; targets, coordinates, hashes and metrics remain strict. Bindings restore
on every exit; spawned numerical workers remain unchanged. This is a serialized
parent CLI boundary, not a concurrent threaded API.

The actual first old-policy corpus now replays144profiles/96ledgers/1152targets
with learner/reference constructors blocked;9 checks including that integration
passed in59.62s. Added restoration/error tests then10fast checks passed in0.50s.
[Source-cohort06 retention](../results/matched-update-pipeline/source-cohort-06a3402/retention.json)
preserves all25 original cohort files and the native pre-input failure exactly.
The expanded source needs complete checks, fresh tiny proof and a complete
prospectively fixed72-row/old-overhead compute gate before admission. Repeating
that full gate is required by the new source cohort, not selecting favorable
unchanged timings. All old observations remain visible and no cap/seed/tolerance
changes. Use the new versioned module entry point for current operations.

### November10 — fresh source cohort starts with old evidence retained

Verified every byte/hash of all25 cohort06 files against their retention receipt,
then cleared only the latest aliases. The first successful own forecast and
failed native attempt remain under `source-cohort-06a3402/`, with original Git
history intact. The new243-file source inventory is
`cc43405e521329890b42cd29709f53ca60ed9504ac8eb13a8b11fa744df158b5`;
its admission remains closed while complete checks run. No old favorable timing
is reused as admission for changed source. Original scientific modules, source
policies, seed/grid/cap contracts and user checkout results are unchanged.

### November 10 — repaired parent IO source passes all current checks

The expanded 243-file source passed both hosted jobs in run
[42803996539](https://github.com/jimmy-sim/poker-ai/actions/runs/42803996539),
checked commit a2b1604. Local machine-asserted Python 3.11.17 / NumPy 2.4.6
and Python 3.12.15 / NumPy 2.5.4 each passed 2,054 base tests (44 skips,
144 slow deselections), 2,107 optional tests and 60 relevant slow integrations.
Base timings: 380.98 / 369.94 s; optional: 387.33 / 374.84 s; slow: 373.35 /
358.91 s. Ruff checked 592 formatted files; strict typing passed 493 files.
The [source-bound receipt](../results/matched-update-pipeline/code-checks.json)
binds the exact source inventory and all six log hashes. Both base checks
selected an absolute interpreter and asserted runtime before and after.
This permits a fresh full tiny software proof, not real study admission.

### November 10 — repaired-cohort full tiny proof passes

Own evidence completed in 4.42767816700507 s and was pushed at 92dacbd,
observed on GitHub (workflow 42806194225) before native reference construction.
The complete native comparison and final own replay finished on the same
34.34460362500977 s clock, below the unchanged 180 s cap including publication.
All 144 captures / 144 scored policies / 96 ledgers / 72 work crossings /
1,152 fixed targets passed; maximum independent scalar error
2.220446049250313e-16 fixture chips. The Python 3.12.15 / NumPy 2.5.4 base reader
replayed the archive with fixture building, learner and reference constructors
blocked; runtime asserted before and after. Exact source cohort: cc43405e….
This is tiny-game software evidence only. It permits the complete short-prefix
forecast/old-policy overhead gate; it does not admit a long real trajectory.

### November 10 — report destination failure retained, admission stays closed

The repaired-cohort own profile failed after all 72 timing rows and complete
144-policy / 96-ledger / 1,152-target own replay. The assistant removed old
latest files but left their empty `overhead/report` directory. The report writer
correctly refused any existing destination. Full profile235.7591332080192 s;
overhead149.15557816601358 s; guarded forecast3361.849243913491 s. These are
retained partial observations, NOT a passing compute/admission receipt.
No native overhead was attempted and no long real trajectory was admitted.
All current files are byte-retained under `source-cohort-7bd650d/` with a hash
receipt and the empty-directory diagnosis. This was an avoidable setup mistake.
Next: prospective destination preflight before child computation, and a complete
CLI clock receipt including preflight/startup/final-write. Keep all scientific
source, caps, seeds and outcomes unchanged; the added IO source needs its full
checks and new cohort gates rather than rewriting the failed receipt.

### November 10 — additive destination preflight and full child-command clocks

Added a launcher that rejects existing receipts, child copies, temporary archives
and any report directory before child computation. A unique rejection receipt
retains the reason; the launcher never removes old data. Complete child receipts
remain byte-exact beside the measured receipt. Clock checks reject nonfinite,
boolean, boundary, failed-child, changed-file, changed-host and expired shared
proof observations. Subsequent stages and admission validate complete clocks in
addition to the frozen original gates. No numerical worker or scientific cap
changed. Focused lifecycle plus parent IO:39 passed,1 slow deselected in0.09s;
strict typing passed both new files. All20 failed-cohort aliases were verified
against retained bytes before clearing files AND empty directories.
The expanded source now needs complete base/optional/slow checks on both
versions, both hosted jobs, a new proof and the full fixed compute gate.

### November 10 — complete lifecycle source checks

Both hosted jobs in [42808276656](https://github.com/jimmy-sim/poker-ai/actions/runs/42808276656)
passed on 36dbd45, matching every byte of the complete 244-file source inventory
84143f4e…. All six local runtime-asserted checks passed: base311: 2083 passed, 44 skipped, 144 deselected, 431.4 s; base312: 2083 passed, 44 skipped, 144 deselected, 419.88 s; focused_slow311: 60 passed, 0 skipped, 18 deselected, 414.39 s; focused_slow312: 60 passed, 0 skipped, 18 deselected, 398.2 s; optional311: 2136 passed, 0 skipped, 144 deselected, 472.66 s; optional312: 2136 passed, 0 skipped, 144 deselected, 464.38 s.
Ruff/format checked 594 files; strict typing passed 495 files. Python/NumPy
runtimes were asserted before and after: 3.11.17/2.4.6 and 3.12.15/2.5.4.
The receipt binds all six log hashes. The source remains frozen for the next
full tiny proof and fixed compute gate. No long study is admitted by software
checks; the two retained IO failures and runtime-label correction remain visible.

### November 10 — complete-launcher tiny proof passes

Own tiny proof: inner4.438767125015 s, complete command
4.632313500042 s. Exact child plus measured own receipt
and all three archives were published at a30ed05 and observed through GitHub's
commit API BEFORE native construction (workflow listing lagged). Complete native
command5.920270000002 s; outer shared clock including
publication and final replay52.012633042003 s
<180. Inner shared clock51.890885124973 s also passes. All144 captures /
144 scored /96 ledgers /72 crossings /1152 fixed targets replay; maximum
independent scalar error2.2204460492503131e-16 fixture chips.
Actual3.12.15/NumPy2.5.4 constructor-blocked reader also passes.
This source-bound software proof permits full original-runtime short profiling
only; no long trajectory or strength/default/fresh/global admission.

### November 10 — complete lifecycle own compute gate passes

The244-file source completed the entire prospective72-row original-runtime
forecast and complete OLD-policy overhead, including archives, zero-error own
replay and reports. Training forecast535.5877299844701 s; unchanged guarded
formula3342.3509199378805 s <7200. Complete overhead148.712823249982 s <600.
Inner own profile234.590419542044 s; full launcher/child command
234.750478875008 s <900. Exact child receipt is preserved beside the measured
profile. Original100k checks pass for all72 timing rows.
This is a new-source full gate, not substitution of an earlier favorable
partial timing. Both earlier cohorts/failures remain byte-retained. The OLD
corpus's144 policies/96 ledgers/1152 targets are timing aliases, not new-prefix
strength results. Publish all own evidence now before the comparison-only
900-second native overhead; strict2*complete elapsed <900 and published
checked admission still block the real long study.

### November 10 — independent complete overhead passes

Complete own evidence was pushed at5ad3aec and observed at its canonical GitHub
commit before any native construction. Comparison-only OpenSpiel2.0.2
(Apache2, pinned license already read/recorded) audited all144 profiles and
1152 fixed targets; maximum scalar discrepancy1.3500311979441904e-13
chips <1e-9. Inner complete audit111.469186791976 s; full launcher/child
command111.674510959012 s; unchanged strict twice-complete guard
223.349021918024 s <900. Exact native child bytes remain beside the measured
receipt. Reference actions/strategies were not exported or used in training.
The source-bound proof and complete own/native compute gates now pass.
Next: generate, check and publish admission before any new real trajectory.
This is bounded scalar/calculator agreement, not agent/solver strategy agreement
or a stronger/default/fresh/global claim. All earlier failures remain retained.

### November 10 — checked compute admission recorded before trajectories

The frozen admission routine recomputed the complete source/proof/72-row
forecast/old-overhead/native chain and produced
[admission.json](../results/matched-update-pipeline/admission.json). It binds
all source inputs, proof/corpus archives and measured own/native receipt bytes.
New launcher prerequisites additionally checked the complete command clocks
(own234.7505 s <900, native2×111.6745=223.3490 s <900) before recording.
Original inner native guard222.9384 s also passes. Source244/checked36dbd45,
both source CI jobs42808276656. This is compute admission for the complete
24-context/48-target known-game study only, not a performance/default/fresh/
global gate. Publish this receipt and check its pushed exact bytes before any
new learner starts. At04:01Pacific the full7200 own +900 native caps plus
verification fit comfortably before the one-time noon deadline. No cap, seed,
source target or acceptance tolerance changed. All earlier failures remain.

### November 10 — complete real matched-update own evidence, before native

Published admission3ec1b8b was independently observed on GitHub and its exact
pushed-byte chain recomputed with learner/reference constructors blocked, before
the first new real trajectory. At04:04Pacific all full caps plus verification
fit before noon; source244 remained frozen.

The complete real own stage now passes:24 initialized B1 paths through their
original10m endpoints,72 original work crossings with144 average readouts,
72 currents,144 raw masses and72 full-state/work guards exact. The global
barrier passed before new scoring. Saved144 captures and separately scored
versions of those SAME144 policies, plus96 raw ledgers. All144 matched self
pairs and1152 fixed-opponent target contrasts remain; own replay error0.
Inner full own stage756.632723374991 s; complete launcher/child
756.886853375006 s <7200.24 paths attempted/initialized, both3-worker phases
complete. Exact child receipt, all archives, reports and partial/failure history
are retained. Original3.11.17/NumPy2.4.6 runtime verified.

Publish this entire OWN evidence now before any new-policy native construction.
The900-second complete native audit is still pending; no stronger/default/
fresh/global or pure-variance claim follows. Reports are own-only snapshots;
the later native receipt supplies the independent comparison without modifying
the originally published own evidence.

### November 10 — complete independent real matched-update audit

All own results were published atd3bd9cf and observed through GitHub's canonical
commit API before independent construction. OpenSpiel2.0.2 / Apache2 completed
all144 new-policy self profiles and1152 fixed target conditions, including own
input/admission replay and all required setup. Inner218.955465457984 s;
complete launcher/child219.216563750000 s <900; maximum scalar discrepancy
1.9895196601282805e-13 chips <1e-9. Exact native child receipt and
complete measurements remain separate from the immutable own publication.
No reference actions/strategies were exported or used in training.

This completes the prescribed actual24-context/48-target comparison, with all
144 new policies/96 ledgers and all seeds/readouts retained. The two compute
axes differ: equal updates costs unequal node work. In the original motivating
medium/q8/signed/linear context, the six raw target deltas in the report show
mixed B4 seed directions, while the earlier B1 prefixes are more exploitable
than B16 in all three declared seeds. These are bounded known-game comparisons,
not a pure-variance effect, default selection, fresh/global admission or general
win-rate claim. Next: complete artifact CI and make all paired results easier
to read/browse before defining another method. Earlier IO/runtime mistakes and
failed/partial cohorts remain retained rather than rewritten.

### November 10 — artifact CI hosting limit, not a scientific gate change

Final artifact run42815549217 passed Python3.12. Python3.11 was canceled at
exactly the15-minute job limit while pytest had reached91%, with no reported
test failure; its stdout showed continuing progress. Retained the cancellation
log and raised the GitHub Actions hosting timeout to25 minutes so all checks
and commit hooks can finish on the hosted runner. No tests, scientific source,
seed, acceptance threshold or7200/900/180/600-second experiment limit changed.
The observed pre-study source CI42808276656 remains valid; this final artifact
CI cancellation is retained separately. Both new hosted jobs must pass before
merging PR40. Local actual archive replays on3.11.17/NumPy2.4.6 and
3.12.15/NumPy2.5.4 pass with learner/reference constructors blocked and zero
error; original SVG/JSON reproduce byte-for-byte, CSV values match with column
order differences from JSON-sorted keys. The separate presentation milestone
will make CSV column order canonical without rewriting historical results.

### November 10 — matched-update study merged and local bytes preserved

Both final artifact CI jobs42818361425 passed on7ecb3b9 after the documented
hosting-timeout correction. PR40 merged at
[e4df336](https://github.com/jimmy-sim/poker-ai/pull/40), completing the actual
24-context matched-update experiment. The user checkout fast-forwarded from
88ebfba to that merge. Before updating, all10 current modified result files
were copied byte-for-byte to a timestamped local backup with hashes and binary
diff; after updating every hash and the same10 modified paths remained intact.
No user result was staged, reset or overwritten.

### November 10 — read-only two-axis tables and policy browser implementation

The prospective issue4 comment6767326534, pinned input config and new reading
guide fix the complete presentation scope before new summary publication.
Added data-only joins for288 self and2304 fixed contrasts (both axes),96/768
three-seed groups, canonical CSV columns and three all-context heatmaps. The
browser validates saved own/native chains, loads one same-update pair once,
then displays unweighted L1-ranked own decisions with actual work/update counts
and bounded n/p/q navigation. It labels global self vulnerability separately
from the representative action differences. No strategy changes or training.

29 independent unit checks pass(0.07 s); Ruff and strict typing pass all7 new
Python files. Initial actual integration failed on both runtimes at a tuple-key
join assumption before producing a new report; exact failure logs are retained.
The explicit-ID rekey fix has its own regression. Corrected actual integration
passes both base runtimes with learner/reference constructors blocked:1 pass,
10 deselected,206.54/198.42 s. All144/96/1152 replay with zero error; full288/2304
contrasts and six report files validate, plus averaged/current viewer paths on
both seats. Separate original-script replays retain CSV column-order mismatch
while confirming all numeric rows and byte-identical SVG/JSON. Complete current
base/optional/hosted checks are next before publishing official presentation
outputs. AI-assisted implementation/checking; no new user practice or human
hands-on time is inferred. Original244-file scientific inventory stays unchanged.

### November 10 — optional plot boundary corrected before publication

Initial full reader-source67edaed checks passed2165 optional tests on each
runtime(347.48/334.69 s), but both base strict type checks and hosted
run42822352177 failed on three unresolved Matplotlib imports. No base pytest
result is claimed. The direct imports were inside the plotting function but
still required optional stubs during base typing. The corrected boundary uses
the existing renderer pattern: dynamic optional imports and headless Agg only
when plotting is requested. Added an explicitly fictional rendering smoke
test; no plot data, model or scientific result changed. All four original
check logs and their failure notice are retained. Complete current checks
will rerun for the corrected source before official report publication.


### November 10 — complete data-only report and browser

Corrected source070e75a: base2112pass45skip145deselect(373.56/359.01 s), optional
2166pass145deselect(414.37/401.80 s), actual constructor-blocked integration
1pass10deselect(243.07/235.42 s), on actual3.11.17/NumPy2.4.6 and3.12.15/2.5.4.
Ruff602files and strict typing502files pass; both hosted jobs42823793710 pass.
All logs/runtime assertions and source inventory retained separately from the
historical scientific admission. Generated complete288self/2304fixed raw
contrasts,96/768three-seed groups and three visually inspected heatmaps in
144.749310s. All six numeric/text exports reproduce byte-for-byte on both
runtimes. Actual terminal n/p/q checked through ranks1→2→1, then clean quit after
one load. Original science code/data unchanged; prior join/import failures
retained. PR41 reports existing results, not new learning or a default selection.
AI-assisted work; no additional user practice, mastery or human minutes inferred.


### November 10 — preregistered private-prefix kernel foundation

Prospective protocol/config740f8fa was pushed and observed on GitHub before new
algorithm implementation. Issue4 comment6768900466 and draftPR42 declare the
complete48-changed-path/432-profile/288-ledger/1152-fixed-target design and
unchanged caps/seeds/gates. Added optional two-level joint private-deal plan,
stratified selector and B>1 frozen-batch subclass; B1 delegates original code.
All original scientific modules/data are preserved. Plans use only chance
metadata and are included in the observation guard; both chance nodes stay
charged. Tiny kernel check/replay is explicitly insufficient for real admission.

71 focused tests pass in4.53s.12 fixed-policy raw-moment cases check unbiased
means and variance decomposition against full expectations, plus independent
rational covariance tests.120 adaptive dense-oracle endpoints match with zero
array error, including40 B1 bit checks. The oracle has its own warm expectation,
traversal, CDF and updater; tests forbid production arithmetic inside it.
Boundary/zero support, invalid laws, post-warm books/work/RNG, last-callback plan
and old-state mutations, stale/partial receipts and overwrite refusal are
covered. Ruff/strict typing pass all9 new Python files. Complete base/optional
and hosted checks are next; no new real trajectory or reference comparison,
full-shape proof, forecast or admission is claimed. AI-assisted work, no inferred
user time/practice/mastery. The reader branch is integrated to keep step68 and
its immutable data available; its final hosted artifact checks remain separate.


### November 10 — kernel foundation source and replay gates pass

Sourcead160906f3c891817fbdb93a1b473846ee46dfec passes both hosted CI jobs in
42828991764. Actual3.11.17/NumPy2.4.6 and3.12.15/2.5.4 base suites each pass2183
tests/45skips/145deselections(332.01/319.19s); optional suites each pass2237/
145deselections(378.30/365.45s). Ruff613files and strict typing511files pass.
All four complete logs include actual runtime assertions before and after checks.
Clean-source kernel.json records12 moment cases/120 adaptive endpoints/40 B1
bit checks,zero maximum array error; a separate3.12 replay matches every row.
No native reference or real poker learner is constructed. Kernel source map,
CI/local receipts and logs are retained in results/private-prefix. This completes
PR42's sampler foundation only: full pipeline proof/forecast/admission remain
false. PR43 continues source/context/grid/archive/native integration; its earlier
published accounting adds48 previously unscored B1 current evaluations inside
the same caps, with no altered scientific gates. AI-assisted work.


### November 10 — complete source/capture/archive components and corrected inventory

PR42 merged ate26656c after BOTH final artifact CI42831549444 jobs passed.
Before updating the user checkout, a fresh backup of the actual10 changed files
was made; all hashes/status stayed identical afterward. Kernel replay on that
checkout passes12 moments/120 endpoints/40 B1 bit checks with zero array error.

PR43's first accounting note contained an assistant reading error: the old216
current records were treated as final-only. Actual own.json and its source loop
show72 at each of100k/1m/10m and24 B1 currents per label, all independently
audited. Corrective driver-v2/c49109e preserves the superseded draft before any
new real profiling/training/native candidate comparison. It removes only the
unnecessary48 extra evaluations proposed from that false assumption; original
432/288/1152 core workload, case grid, seeds, work, formula, quality gates and
scientific caps stay unchanged. The earlier step69 wording is historical and
superseded by this correction, not evidence of missing scores.

Implemented strict complete48-path/432-policy/288-ledger grids, typed work and
shared-state/capture lineage, source/context factories and whole used-archive
checks; generic own capture/score/archive/replay, partial retention, complete
B1/IID paired functions, optional standard Matplotlib heatmaps and separate
native432/1152 schema/scalar adapter. The explicit tiny fixture also retains
648 old IID baseline profiles/1728 fixed conditions, yielding864 self and2304
fixed contrasts; those are dependent software fixtures on one nonuniform Kuhn
game. Real sources are loaded without any learner/reference constructor.

Focused base133pass1skip2deselect4.87s. Full toy archive/paired/report integration
1pass7deselect11.50s; all own/new/baseline metrics and raw masses replay with
constructors blocked,zero discrepancy; numeric reports reproduce byte-identically.
Actual original-data source-loader test1pass1deselect31.32s, including regression
for all72 already scored B1 currents and exact72 original crossing records.
Native schema tests are fictional and do not assert actual solver construction
or agreement. Ruff/strict typing pass the new component files. These are checked
components, not the source-bound full command/software proof, compute forecast,
admission or real learning study. Command-level whole clocks/gates remain next.
AI-assisted implementation/tests; no user practice/hours/mastery inferred.


### November 10 — whole private-prefix command and failure retention

Added separate complete-command source gates, original-runtime144-prefix fixed
forecast, full OLD432/288/1152 cost corpus, own study/native controllers,
source-bound admission recomputation and read-only replay. Append/fsync journals
retain each worker message before final JSON; readers check exact journal/source
bindings. Fresh-destination preflight includes the nested old report, and the
parent kills the complete child process group on timeout. Partial baseline
records/archive errors and failed/over-budget stages remain visible. Reference
construction follows observed own publication; no reference policy is exported.

Focused execution/source integration passes23 tests in55.99s, including a complete
toy command/read-only replay, real archive copying with constructors blocked,
spawn success/failure, journal tampering, fixed forecast arithmetic and failures,
publication rejection before reference construction, and destination/timeout
rejections. Initial journal tests exposed list-subclass equality/fixture-copy
issues; corrected by comparing plain persisted lists, with no numerical change.
Whole source base/optional and hosted checks are next. This implementation
commit is not a passed full software proof, forecast, admission or real study.
Scientific configs/seeds/caps and historical source/data are unchanged.
AI-assisted work; no human minutes, practice or mastery inferred.


### November 10 — retain and fix console-only spawn fixture failure

Source63a6209 full base suites each finish2263pass/46skip/148deselect with2
failures: console pytest omits the repository root from sys.path under importlib
mode, so spawned synthetic test functions cannot import `tests`. The same
module passes under python-m pytest. A console reproduction confirms the cause;
explicit pytest monkeypatch of the test import path fixes it, matching the
existing spawn tests. Corrected console run20pass1deselect0.85s. Both failing
full logs and before/after diagnostics remain in
results/private-prefix/development-failures/console-spawn. No scientific source,
seed, cap, gate or result changed; fresh full checks are required before proof.


### November 10 — close the parent-scoring interruption gap before proof

The corrected f391c95 cohort passes both hosted source jobs42847940174 and all
six local checks (base2265each, optional2320each, slow3each). Full source-bound
logs/runtime assertions and observed CI are retained in pipeline-checks-f391c95.
Review found that the real runner journaled worker messages but replaced its
event list with a plain list before parent scoring; a hard timeout could lose
completed scoring event metadata until final JSON. OLD calibration had the same
parent-only gap. No actual proof, profiling, native comparison or real candidate
trajectory had begun.

The combined event list now preserves the existing worker stream once, then
fsyncs parent scoring in its own slot. OLD copy/scoring has a checked durable
journal too, included in admission inputs and unchanged whole-clock overhead.
Tests check durability before exception handling or final JSON; focused console
execution22pass1deselect2.61s, full Ruff/format/strict typing pass. No numerical
operation, RNG, seed, grid or scientific cap changed. Repeat complete source
checks before any proof/admission; the prior passing cohort is not reused as
current admission. AI-assisted review/implementation, no inferred human time.


### November 10 — isolate a synthetic test from shallow hosted history

Source1989b52 passes all local checks:2267base/2322optional/3slow on each runtime.
Hosted3.12 job129951572681 in42851073282 instead fails1 test (2266pass/46skip/
148deselect,597.28s): the new synthetic OLD interruption test accidentally calls
real historical kernel_evidence, but the shallow checkout lacks ad160906. The
full hosted log and local packet are retained. Isolated the synthetic failure
test's kernel evidence; separate slow real-source/archive validation remains
unchanged. Corrected console22pass1deselect1.67s. No scientific source, seed,
cap, gate or data changed (274-file sourceSHAa5a2e28 remains unchanged). New
complete local/hosted checks precede proof; no reference/profiling/real candidate
trajectory has run. AI-assisted work; no inferred human time or understanding.


### November 10 — final complete pipeline source checks pass

Sourcee96e07e, scientific274-file SHAa5a2e28de289d719efe51e639f1a30bb9df8573377b406b823e0216d57154070,
passes both hosted jobs129963379794/129963379924 in run42854406375. This is the
existing ci.yml workflow dispatched on exacte96 after GitHub reported PR
mergeability unknown and did not list a synchronize run; no gate or workflow
was weakened. All6 latest local logs have before/after runtime assertions:
base2267each(354.74/341.16s;46skips148deselect), optional2322each(387.88/374.38s;
148deselect), slow3each(98.91/95.25s;112deselect), actual3.11.17/NumPy2.4.6 and
3.12.15/2.5.4. Complete packet is results/private-prefix/pipeline-checks. Both
previous shallow-history hosted failures remain retained, including311's
1failed/2266pass/46skip/148deselect841.74s. These are source software checks
only; actual shared-clock tiny proof, real forecast and checked published
admission remain required before long study. AI-assisted work.


### November 10 — complete source-bound tiny proof passes

Own full-shape rehearsal432policies/288ledgers/1152fixed plus648baseline
profiles/1728baseline fixed conditions completes whole22.93704875s. Own replay
errors are exactly0; all864self/2304fixed contrasts and three inspected labeled
Matplotlib heatmaps are retained. The15 own files match committed bytes at
f684a319c5d48d25d5ae709c75820e4e0e0c82de; GitHub's canonical commit/tree
79d72b074fe8898b4f677d562799cc75561e5758 was observed before reference construction.
OpenSpiel independently checks1080profiles/2880fixed, maximum error
5.551115123125783e-16chips. Complete native command11.838831416s; shared own
command/publication/native/final-replay116.913814416s<180. Raw journals and exact
child receipts remain published. This repeats ONE nonuniform Kuhn game under
logical labels; it is software evidence, not Hold'em strength. Sourcee96e07e
and both source CI42854406375 jobs bind the unchanged274-file sourceSHAa5a2e28.
Next: original-runtime144-prefix complete conservative forecast and OLD workload
inside900/600, then own publication before native timing and checked admission.
No real candidate profiling or long trajectory has been admitted yet.


### November 10 — complete real-prefix own forecast passes

On original3.11.17/NumPy2.4.6, all144 prescribed timing prefixes (48changed paths
repeated3times, additional100k node work each) complete with identical repeated
state/work guards. The whole profile, including all setup/input checks and full
OLD432-policy/288-ledger/1152-fixed serialization/scoring/replay/report workload,
takes288.370542167s<900. Subtracting only the longest worker's actual setup+
incremental-training intervals27.634824962s leaves260.735717205s<600 for ALL
nontraining/setup/old workload. Complete fixed-partition max-of-three forecast
T862.476172223s gives2*(2*T+600)=4649.904688890s<7200. The three OLD heatmaps
were inspected; IID-self contrasts are zero and all figures say OLD/no new
trajectories. No new candidate utility was scored from timing prefixes.

Own forecast and old workload are being published before the independent native
cost comparison. This is not long-study admission: strict2*whole-native<900,
source/inputs/CI-bound checked published admission and constructor-blocked
recomputation remain required. No seed, cap, formula, grid or gate changed.
AI-assisted execution/documentation; no human time or stronger-agent claim.


### November 10 — independent complete native cost gate passes

After canonical GitHub observation of own profile commit6e245f628fee0e799d7b527e3d9ccd6e84fe9f91
and tree0b7073a607e8b0db2847b9a8d47d1870229a0a87, all17 referenced own profiling
files match committed bytes. The separate OpenSpiel audit checks every OLD
432profile/1152fixed condition, maximum2.0605739337042905e-13 chips disagreement.
Whole native command341.493552959s; strict2*whole=682.987105918s<900 passes,
including source/input setup, all independent work and final full own replay.
No reference strategy is exported or loaded into learning. Own evidence was
published first. Next: recompute and publish exact source/config/input/CI/whole-
clock admission, then constructor-blocked verification of those published bytes.
This cost gate permits no stronger/default/fresh/global claim and has not yet
started a long new candidate trajectory. Source/seeds/caps/gates unchanged.


### November 10 — checked known-game admission before long training

The admission command recomputes the complete source274-file inventory, exact
config, both source CI jobs, all6 local logs, published tiny proof,144timing
rows/fixed forecast, full OLD replay/native validation, whole clocks and every
used input hash. It produces checked_known_game_trajectory_admission_not_agent_strength
with long_run_admitted=true while new_agent_default/fresh_global_admission=false
and candidate_strength_still_unmeasured=true. These flags describe permission
to run the prescribed known-game experiment, not a measured improvement. The
record is published before constructor-blocked recomputation and any new long
trajectory. Original7200/900 caps, complete grid, seeds and gates remain fixed.
The actual window must still fit full caps plus final verification before launch.


### November 10 — complete own private-prefix study, main accuracy gate fails

Before any new long trajectory, published admission39144dc was canonically
observed on GitHub and recomputed with5learner/reference constructors blocked
in126.528608083s (all36 bound inputs). The17:08UTC window check left10320s,
covering full7200+900caps plus1800verification seconds before20:00UTC.
The original-runtime study completes all48paths/432readouts/288ledgers/1152fixed
conditions,864self/2304fixed contrasts in whole1201.279549125s<7200. Own archive
replay chip/unitless discrepancy0; all3 new heatmaps inspected. No case, seed,
readout, cap or threshold changed.

Primary medium/q8/B4/signed/linear final10m exploitability percentages by seeds
20261301/02/03 are2.311742130540,4.494857881670,3.245725163721. Existing IID-B4
controls are2.793291801246,0.375286609858,3.349472198669. The new mean is
3.350775058644%, versus2.172683536591%; paired baseline-minus-new mean
-1.178091522053percentage points. Two small positive seed differences and one
large negative are all retained. New median3.245725163721>1% and worst
4.494857881670>2.5% fail the unchanged primary accuracy limits. It is not rescued
by a different readout, B16, or the exact control. Low-game accuracy passes;
medium exact control also passes (median0.183407419724%, worst0.229841014432%).
Whole warm-inclusive coverage is100%, while primary medium post-warm row
coverage is0.652226/0.593261/0.613718; warm support is not learned coverage.
These are own known-game quantities pending independent comparison. Publish all
complete evidence first; keep default/fresh/global admission false. Next is
the independent900-second audit, then diagnosis using saved policies, not an
unchanged favorable training retry. AI-assisted execution/reporting.


### November 10 — complete real independent audit verifies the negative result

Own studyccbffb91064c82df6de503033932c6e90f789968/tree55bc8e106c41e9a18d76f06b85a9bac1d100dfdc
was canonically observed, with all16 study files hash-matched to committed bytes,
BEFORE real-native construction17:38UTC. All 432 profiles/1152fixed conditions
pass independent OpenSpiel checks, maximum2.0605739337042905e-13 chips. Whole
native639.711564250s<900 includes all required setup/admission checks, own
archive/baseline reads, reference work and final full replay. Raw1596-message
journal and exact child retained. A data-only replay with constructors blocked
checks source, whole-clock/child bytes, raw journal and complete native schema.

The numerical audit passes; the main accuracy target still fails. Keep every
negative seed/control/readout and the default/fresh/global flags false. README
now reports B14.354032%, IID-B42.172684%, stratifiedB43.350775% on the declared
primary, with scope and failed limits. No extra training study starts this
window. Next bounded step is the prospectively specified saved-policy gap
diagnosis (issue4 comment6774698163), with all3seeds/readouts/work labels and
both encodings/games; no causal/floor claim or favorable unchanged retry.
Final artifact CI is required before merge. AI-assisted work, no inferred human
minutes or mastery.


### November10 — prospective bounded saved-policy diagnosis

After the complete independently checked negative primary, register the fixed
post-hoc panel before generating decomposition tables: B4/signed, both games
and encodings, all3seeds/readouts/work labels, B1 and IID controls. Expected
324method points/216paired points/108method groups/72paired groups. Stack only
within-partition+extra-information gain; keep exact-prefix river switch separate
from total/actual EV loss. Include actual work/updates and whole/post-warm support.
The config binds published own SHA and unchanged model sourcea5a2e28. No new
trajectory, cap, seed, threshold or default change. Acceptance requires complete
source/own/native/journal/whole-clock checks, constructor-blocked read-only
replay, tests and reproducible tables/figure. Post-hoc evidence is descriptive,
not causal proof or an irreducible-floor claim. No diagnostic result yet.


### November10 — checked saved-policy projection entrypoint

Implemented the prospective diagnostic as experiment-specific CLI orchestration
over the frozen replay/metric/native/schema/source libraries. No src/model
module changes. Complete108coordinate selection produces324method/216paired
points and108/72three-seed groups; stack only within+extra. The fixed figure
keeps all medium-game seeds/readouts and both encodings. Replays run with
learner/reference constructors blocked; fresh outputs, config/own/model source
hashes and complete native journal/clock are checked first.

Fictional base11pass1skip2.31s, optional12pass10.37s, Ruff/format/strict typing
pass. Tests independently assert known signed gaps, zero-self, separate river
metric, missing/duplicate/type/nonfinite/identity failures, missing seeds and
no-overwrite-before-expensive-replay. Actual diagnosis and final base/optional/
hosted checks follow; no diagnosis result or causal claim yet. AI-assisted work.

### November 10 — complete saved-policy component diagnosis

PR #43 merged at d83de6d after final artifact CI 42869639853 passed both jobs.
Its negative performance gate remains failed; independent numerical validation
does not change that outcome. PR #44 is retargeted to main.

The constructor-blocked saved-policy diagnosis completed in 352.852207541s:
324 method points / 216 paired points / 108 method groups / 72 paired groups,
all fixed seeds/readouts/checkpoints/encodings/games retained. Frozen model
a5a2e28 and own/native input hashes validated. No training/reference constructed.

Primary compressed linear-average means (percent initial pot) are candidate
3.350775 = 0.150998 within + 3.199777 extra, IID 2.172684 = 0.094215 + 2.078469.
The candidate-minus-IID excess is concentrated in extra-information value;
this locates a vulnerability, not a causal representation-only conclusion or
irreducible floor. Exact-control and all current/uniform/linear readouts remain
visible. River-switch values stay separate. Whole warm support does not imply
learned coverage; updates differ at equal work.

All four local suites pass: base 2,278 / 47 skipped / 148 deselected in
379.79s (311) and 369.38s (312); optional 2,334 / 148 deselected in 414.01s
and 402.83s. Runtime before/after assertions retained with exact logs.
Actual diagnosis figure visually inspected. Cross-runtime numeric reproduction
and final hosted CI remain to be recorded. Main was fast-forwarded to PR #43
only after a fresh byte snapshot; all ten unrelated modified files and exact
status were preserved. AI-assisted execution; no inferred human minutes.

Numeric reproduction on Python 3.12.15 / NumPy 2.5.4 completed in 255.965582s; all four CSV files are byte-identical to the original-runtime diagnosis. Constructors remained blocked and no training or reference construction occurred. This is saved-data reproduction, not real trajectory parity. Exact receipt and manifest are retained in results/private-prefix/diagnosis/checks/.

### November 10 — register complete saved-decision follow-up

Before generating local row tables, issue #4 comment 6775611715 fixes the
medium/q8/signed/B4/final10m/linear panel: all three seeds × B1/IID/stratified,
nine profiles and both responding seats. Existing own trace, full owned-row
archive, deterministic top-five groups/four examples, TURN/RIVER accounting to
total unilateral gain, source/native/policy checks and unchanged inputs.
This is not an attribution of extra-information value alone or a causal
retraining gain. No new training or default/gate/seed/cap changes. Prospective
config/document only; implementation and outcomes remain pending.

### November 10 — implement saved-decision tracing and cached browser

Experiment-specific CLI restores the nine policies from source-bound original
archives, reuses existing own reply analysis, checks audited root/row/street
identities, and fingerprints arrays before/after. Full owned-row detail and own
reply profiles remain in deterministic gzip; partial progress is retained.
No model source or scientific contract changes.

Added a cached hash-checked browser with n/p/s/o/t/q controls, explicit target
seat/action/value conventions and total-vs-extra/retraining distinctions.
Sixteen fictional tests pass in 0.58s; Ruff/format/strict typing (547 files) pass.
No actual decision result yet. Full local checks, constructor-blocked actual
replay and both hosted jobs follow. AI-assisted implementation.

### November 10 — retain first complete nine-profile trace before review fixes

Published source 57f11cb restores and traces all nine saved profiles / eighteen
responses in 358.294261833s, with constructors blocked. Root comparisons pass,
arrays are unchanged, and every seed/control is retained. Base suites each
2,294 passed / 47 skipped / 148 deselected (381.84s / 369.55s); optional each
2,350 passed / 148 deselected (415.93s / 404.14s). Exact logs and the complete
initial archive are retained in results/private-prefix/decisions-initial57f.

Actual TTY n/p/s/o/t/q and a captured command-input reproduction work. Source
review identifies report safeguards to strengthen: explicit per-seat gain
identities to reject canceling seat errors; full owned-row inventory checks;
retain each completed profile's details before advancing, rather than retaining
only a count until the final write. This is reporting validation/retention work,
not a changed learner or a favorable training retry. Preserve the first outcome
and rerun only saved-data analysis after the fix. No new poker training.

### November 10 — strengthen report accounting and interruption retention

Retained the complete initial diagnostic/source before review fixes. Added each
seat's gain-to-root identity, complete owned-row/menu/support validation, and
per-profile finite detail persistence before advancing. Canceling seat errors,
missing/duplicate rows, changed sums/menus/support and later nonfinite detail
failure are rejected; earlier completed detail bytes remain unchanged. Browser
zero-loss fixture initially failed from indexing before the empty-list check;
moved indexing after that check. Focused 26 pass0.48s; Ruff/format/typing pass.
No scientific model/data change. Final full suites and saved-data replay follow.

PR #44 final artifact CI42874878787 passed both jobs and merged8b303fdd.
PR #45 retargeted to main; integrate the merged data-only reproduction receipts
before final checks. Human minutes not recorded; AI-assisted execution.

### November 10 — complete safeguarded saved-decision replay

All9profiles/18responses/30,024owned exact rows complete in357.455548917s,
constructors blocked, audited roots/accounting and unchanged arrays checked.
Summary and full detail gzip are BYTEIDENTICAL to retained initial57f outcome;
per-profile partial details now survive interruption. Both final base suites
2304pass47skip148deselect380.77/368.58s; optional2360pass148deselect413.90/402.76s.

Every seat-1 profile's top group819 is the singleton turn99 case. Most total
gain is attributed at turn, but the best-reply suffix includes river choices;
this is not evidence of missing turn information or extra-only row loss.
All seed/control street totals and example values are in the report, with
learning-journal step79 and an interactive cached browser. Native original
432/1152 evidence remains comparison-only. Cross-runtime data-only replay and
final hosted CI remain next; no new training or default/gate change.

Python 3.12.15 / NumPy 2.5.4 saved-data reproduction finishes in 257.833441s with constructors blocked. The full summary, full detail archive and all nine per-profile detail archives are byte-identical to the original-runtime report. This is data-only reproduction, not bit-exact training replay. Exact manifest and output hashes are retained in results/private-prefix/decisions/checks/.

### November 10 — register fixed saved-continuation contrast

Issue #4 comment 6776137714 predeclares exact/restricted/hybrid action values
for all nine primary profiles and both seats, every previously ranked group
and every exact member. The hybrid changes only own river rows; opponent and
pre-river rows are checked, as are audited roots, finite values, support and
complete inventory. Pin the final decision report to the initial summary bytes;
do not change the hash if reproduction fails. No new training or solver.
No contrast values measured yet. This diagnoses a frozen continuation, not
causal training improvement or extra-information-only attribution.

### November 10 — implement controlled saved-continuation values

Report-only CLI reuses the frozen own scoring/conditional-action functions and
the fixed decision archive loader. Exact/restricted/hybrid roots match audited
source values; opponent rows are fixed; hybrid is checked to change only own
river rows. Retain all90groups/415members, including unsupported rows with None
choice, first-legal supported ties, finite values, separate1e-9chip/1e-12support
tolerances and unchanged input arrays.

Thirteen fictional arithmetic/control tests pass0.52s; Ruff/format/mypy549files
pass. A hand-computed two-decision payoff fixture checks both target signs and
own-past-reach exclusion, not poker strength. No actual continuation contrast
yet. Integrate the published safeguarded input report, run full local checks,
then constructor-blocked saved-data contrast and both hosted jobs. No training.

### November 10 — retain and correct continuation support-scope failure

Initial source e92d0cc saved-data attempt fails at the first contrast before any
completed derived output. Keep raw stderr, independent Kuhn reproduction,
failure notice and all four initial passing suites: base2317/47skip/148deselect
380.89/369.72s; optional2373/148deselect415.69/403.50s. Those tests missed a
valid two-player support change. Exact failure wall time was not retained;
do not infer it from polling.

Independent fixture: responding CF mass change0, other-actor change1/6.
Only responding infos' chance*opponent mass is invariant when own strategy
changes. Restrict that comparison to target-owned infos at the SAME1e-12
threshold; opponent POLICY equality remains universal. Add valid two-player
regression; focused14pass0.45s, Ruff/format/typing pass. AllSRC/modela5, config
SHA, seeds,9/18/90/415panel, chip tolerances and scientific caps unchanged.
No new training/reference. Publish corrected source before fresh saved-data
analysis; preserve failure in results/private-prefix/continuations-initial-e92-failure.

### November 10 — complete fixed saved-continuation contrast

Corrected source7f68380 completes18responses/90groups/415members in356.912652750s.
Root discrepancy0chips; responding support discrepancy0; all415CFsupported,
31TURN/384RIVER. Exact vs hybrid preferred actions differ in10of31selected
TURNrecords. These are dependent post-hoc selected records, not hand frequencies.
Allarraysunchanged; learner/referenceconstructorsblocked; no newtraining.

Largestseat1singleton99turngroup:7of9snapshotsfold->call whenonly ownriver
continuationchanges. B1seed02 andnewseed03alreadycall, retained. Newseed02fold-18,
callhybrid-19.8539257466, exactcall-12.7212238082chips; different snapshots use
their respective saved opponents, fixed onlyWITHIN eachcontrast. Full415rows
retainalllegalQs; newper-rowQs are OWNmath, not anewnativeaudit ortrainingbenefit.

Finalbase2318pass47skip148deselect384.99/371.81s; optional2374pass148deselect
416.41/404.64s.14focusedchecks, Ruff/format/mypy pass. Separate renderer projects
all9examples toCSV/PNG, visualinspectionfixedoverlappingfootercaption; unreviewed
layoutdrafts stayignored. No source/strategy/scientific gate change. Journal81
and plainreport explain the failure, mechanism, limitations and next decision.

PR45finalCI42879966452bothPASS mergedb861c4bc. UsermainFFafterfresh19:08snapshot;
all10modified bytes/index/statuspreserved. Main38focusedtestspass15.04s andactual
cachedexampleworks; postcheck10hashes/statusunchanged. PR46retargetmain; integrate
the last PR45data-only reproductionreceipt before final branch checks.
Cross-runtime continuation reproduction and final hostedCI remain pending.

### November 10 — reproduce all saved-continuation records across runtimes

Python3.12.15/NumPy2.5.4 saved-data reproduction completes in253.189350s,
constructorsblocked. Fullsummary, all415Qrecords gzip and cumulativepartialJSON
are BYTEIDENTICAL to original311; exactreceipt/manifest/log retained. No real
trajectory replay or newnativeaudit claimed. Clarifiedhybridprefixremainsfixed:
the figure compares conditionalactionvalues, notactualhybridactionfrequencies.
Model/source/seeds/thresholds/caps/default unchanged. Finalbothhostedjobs required
beforemerge; no newlongstudy thiswindow.

### November 10 — project success governs publishing cadence

The user explicitly reaffirmed that project success and efficiency take priority
over the appearance or number of GitHub contributions. Record the accepted
approach in AGENTS.md, CONTRIBUTING.md and the continuing roadmap: one coherent
research question/milestone per PR when useful, related work grouped at logical
commit boundaries, and routine status updates in PRs/issues.

All separately required protocol, tested-source, admission and own-before-
reference publication gates remain. Preserve exact-commit research history;
consider squashing only unreferenced housekeeping. No daily activity quota,
artificial dates or delayed completed work. Use appropriate local checks for
documentation-only changes and retain required hosted CI before merge.

Scope is process documentation only: no model, scientific config, seed, cap,
result, validation threshold, CI workflow or schedule change. No new scientific
milestone or personal learning claim is inferred. Local diff/content checks pass,
three local guideline/roadmap links resolve, and the scientific source inventory
remains the same 274-file SHA a5a2e28. Only the
four intended Markdown files differ; source/config/results/workflow diffs are
empty. No numerical tests were added or run for these documentation edits.
Required hosted CI follows before merge.

### November 10 — resume issue #4 with static river refinement controls

The user deleted the next scheduled window and authorized autonomous work now
until stopped. Automation poker-ai-nov-11-midnight-to-noon was deleted through
the app. Issue #4 comment 6788998129 prospectively registers the complete nine-
snapshot, both-seat, all-river-row diagnostic before new feature measurements.

The experiment-specific runner preserves frozen model source and compares the
original groups, exact rational static masses, ordered combo relations and exact
singletons under both fixed own reply suffixes. Local sharing cost is normalized
by responding chance-times-opponent support; it is not root EV/exploitability or
a training improvement. No new trajectory, native construction or default change.

Thirty focused tests pass in 0.12s; Ruff/format and strict typing pass. Tests cover
hand-computed cost, ties/unsupported rows, refinement, independent equal-prior
bin arithmetic, observable-card invariance, malformed/duplicate/owner/menu data,
deterministic archive and partial/timeout/input-change retention. Journal step82
explains the question with a fictional example. Full base/optional checks,
hosted CI and actual saved-data/cross-runtime results remain pending. Preserve
all ten unrelated user result changes; work stays in an isolated checkout.

### November 10 — static refinement adds no distinctions in the known game

Source410faef published and fully checked before execution. Base suites each
2348pass47skip148deselect357.35/344.48s; optional each2404pass148deselect
404.50/389.09s. Hosted42974764735 both PASS. Diagnostic311 completes294.563466s;
312 data-only reproduction266.377378s, both<900. All12 numeric files BYTEIDENTICAL;
no trajectory replay. Exact receipts, complete/partial per-profile data and logs
retained in results/river-refinement/. Frozen274-file scientific SHAa5a2e28 stays.

All9profiles/18responses retain29,808ownriver memberrecords, everyrowCFsupported,
not played/training coverage. Respondingseat0 has864originalgroups, seat1 has774;
both have1656exactriverinfos. Exact rational static masses and ordered combo
relations add ZEROgroups and leave every local cost/conflict count unchanged
under BOTH own suffixes. Singleton costs0 byconstruction. Roots/support errors0.
Local sharing cost is not rootEV/exploitability or a strength ranking across
different opponents. OldprimaryFAIL remains; no agent/default/fresh/global change.

Report reader reconstructs all row summaries and144conditiontable; bothnumeric
reportfiles reproduce byteforbyte on312. Figure visually checked; label explicitly
marks singletoncontrol. Report render source records its working-tree hashes,
while the scientific saved-data run used clean published410faef. Focused base
44pass1skip2.10s; optional45pass2.19s, including actual complete-receipt regression
and changed/failure/source/hash/inventory rejection. Lint/format/stricttypingpass.
Final base2362pass48skip148deselect353.39/338.86s and optional2419pass148deselect
400.67/386.97s, runtimeassertedbefore/after. Final hostedCI pending beforemerge. README,
method/limits/3QAs and plain-English journal83 record the complete negative result.
Next question: own coarse learner against own exact-information training opponent,
with new prospective mixed-view correctness/work controls before any admission.

### November 10 — retain Linux report-reader failure and narrow roundoff fix

FinalCI42979804961 on dd196a5: Python312 fails the actual complete-row replay
because its summary comparison requires byte-exact floating arithmetic. Raw log
retained. Independent Fraction arithmetic on all36saved local costs has maximum
error8.881784197001252e-16 relative to saved scores; rerunnable script/JSON retained.
The correction permits1e-12absolute roundoff ONLY for recomputed local costs;
archived hashes, all structure/support/counts and singletonzero stay EXACT.
No scientific config/source/data, root/support tolerance, cap or strength-gate
change. Seven regression cases cover small/large errors and forbidden field drift.
Focused corrected base51pass1skip2.48s; Ruff/format/stricttyping pass. New full
local suites/hostedCI required beforemerge; no new research trajectory begins.
Own-exact-opponent software prospect registeredcomment6790000490, separate empty
worktree exists; its implementation waits until this mismatch is resolved.

### November 11 — close PR #48 and build the own-opponent information controls

PR #48 merges at 078433b after corrected CI 42981595850 passes both jobs.
Linux measures 8.881784197001252e-16 local replay roundoff, with all structure,
support and counts exact. Corrected local base suites each pass 2,369 tests
(48 skipped, 148 deselected; 337.78/326.02s); optional suites each pass 2,426
(148 deselected; 382.04/367.52s). Raw corrected logs and SHA receipts are in
PR comment 6790343848. User main passes 52 focused checks in 12.25s; its actual
renderer reproduces both numeric tables byte for byte. Fresh pre-FF snapshot
and post-test checks preserve all ten modified bytes, index, status and diff.

Only then implement prospective comment 6790000490 in a separate worktree.
The new factory creates the two own coarse/fine-opponent information views;
the composer projects each coarse seat from its own view and discards the fine
opponent rows. Read-only copies, source/view/role/policy fingerprints, legal-menu
checks and perfect recall protect the construction. No historical source file,
policy data, updater, dependency lock or agent default changes.

Thirty-two focused checks pass in 3.24s, with Ruff/format/strict typing passing.
Independent terminal sums and pure replies validate a fictional signal-game
counterexample for both target signs. Both known poker games pass all-node
observability/hidden/future invariance and policy-edge/value/own-reply checks.
The cached original browser still loads. Interrupted/incomplete software evidence
retains failure and denies training admission. Journal step 84 and the versioned
protocol explain this software-only milestone. Full base/optional/hosted checks
and a published software receipt are pending; no new real trajectory or stronger/
default/fresh/global claim. Added modules create a new source cohort, not an
inheritance of the old admission. User authorization continues until stopped;
the deleted automation is not recreated. No human hours or mastery inferred.

### November 11 — freeze matched own-opponent learning controls and raw captures

PR #49 foundation source05a00d6 passes full local base2401/optional2458 tests on
both runtimes; 48 base skips and148 deselections, base363.61/350.74s and optional
415.10/409.54s. Hosted42986614874 BOTH SUCCESS: 2401pass48skip148deselect1 retained
historical roundoff warning; 591.72/791.28s. Clean311/312 software proofs agree on
all analytic/structural/input/source fields, completing2.456548/2.388334s. Raw logs,
proofs and source/hash receipt retained in results/opponent-information/software-views/.
This checks source05a only, not the new learning pipeline or real admission.

Prospective issue4comment6791111602 fixes the next coherent comparison before
new real trajectories. Four logical arms separate fine own-opponent information
from the cost of two learning games. Five actual paths per known game/seed reuse
one explicitly charged coarse prefix. Fixed30paths/108boundaries/324rawpolicies/
216ledgers/30warmorigins/108compositions/432uniqueprofiles, all3seeds/readouts,
36originalB4barriers and1152fixed conditions. All8frozenowncontrols pergame are
verified by saved policy hash; no strength-based opponent choice. Historical
caps7200/900, runtime311.17/NumPy2.4.6, accuracy/coverage/recall gates preserved.
New source cohort; historical admission is not inherited. Native output stays
comparison-only. No new real-poker timing or learning trajectory.

Implement fixed typed design, unchanged IIDB4 capture, warm/book/policy replay,
explicit paired work and own seat composition/replay. Tiny fixtures cover all
30paths and every raw/derived policy, normalization, legal-view/source bindings,
observer state-bit identity, both warm starts/overshoots, repacked bad warm and
average values, altered compositions, unsafe paths and interruption retention.
Overwrite preflight rejects before initialization. Sixty-six focused tests pass
at the implementation checkpoint; Ruff/format/strict typing pass. Full pipeline
score/archive/fixed/native/report integration, source checks, conservative fixed
forecast and published admission remain pending. Journal85 explains reuse and
why two coarse paths are necessary. PR stays draft; no stronger/default/fresh/
global claim and no personal hours or mastery inferred.

### November11 — complete the own-opponent command and cost/permit implementation

Continue the coherent issue4 investigation in draftPR49. New shared three-worker
training and independent-scalar paths retain complete raw messages and partial
failures. Own432-profile/1152-fixed-condition scoring, five archives, book/seat/
scalar replay,216-point tables and three figures are connected. Whole-command
clocks include startup/preflight/source/work/replay/report; interrupted temporary
bytes are retained. Git publication is required before reference construction.

Prospective comment6792824092 and a versioned COST supplement specify old OWN
stand-ins before cost measurements. Every old coordinate/source/hash/work is
retained; mixed tables were not learned together. New training work is0 and
iteration/guard/learning RNG areNone. Cost data cannot enter the actual collector
or satisfy36 original B4 barriers. Fixed24-path historical timing maxima and all
three complete own/native cost repetitions feed the unchanged conservative
forecast. Source checks, complete published software/cost evidence and a checked
published permit gate real workers; original runtime/caps/seeds remain fixed.

175 focused base tests pass18.04s;10 optional skipped,1slow deselected. Relevant
slow original archive decoding passes1test34.42s. Ruff/format/strict typing pass
on the new source/tests. Optional focused checks185pass18.24s. Actual spawned
fictional integration checks the entire
own path. Independent terminal arithmetic checks toy values; mocked native
schema/worker numbers are explicitly not an audit. An old-book work-field test
failed before linking books to their original saved checkpoint work records;
the corrected all180-member reader passes. All3 draft figures visually checked;
3numeric files byte-identical through layout-only fixes. Journal86 explains the
distinctions. Full source-bound local/optional/hosted checks and formal proof/
forecast/admission are pending. No new real trajectory, improved agent/default,
fresh/global claim, personal hours or invented user learning.

### November11 — repair unitless replay tolerance before proof/admission

Source627427b completes full local base2576/optional2643 each,58base skips and
149deselections; pytest430.35/417.08s base,480.83/464.79s optional. Relevant
slow archive1pass each51.48/49.62s. Both hosted43004096870 jobs pass2576 with
58skips/149deselections/1historical warning,906.60/887.49s. All raw logs and
source/checkout/hash receipts are retained in source-627427b-checks. GitHub PR
checkout9a535dae source inventory exactly equals tested627427b.

Final review finds coverage replay using the chip1e-9 tolerance instead of the
frozen unitless1e-12. Two consistently repacked whole/post-warm5e-10 defects
reproduce as wrongly accepted; one within-tolerance5e-13 control passes. Preserve
before-fix2failed/1passed8.95s and after-fix3passed6.62s logs. Correct coverage
guard and receipt comparison, retaining separate unitless/chip maxima. Journal87
explains why readable/hash-consistent archives still need mathematical replay.
Fresh complete corrected-source checks are required. No formal new proof/cost
forecast/admission/real trajectory occurred on the superseded source. Seeds,
learning rules, scientific caps and original thresholds remain unchanged.

Corrected focused178base23.51s/188optional23.45s,1slow deselected and10base optional
skips. Full repository Ruff/format/strict typing pass. Corrected full source-bound
local/optional/hosted and relevant slow checks remain pending.

### November11 — preserve truthful uncertainty when workers are interrupted

Coverage source7f191d4 passes complete base2579/optional2646 each,58base skips/
149deselections:434.84/421.63s base,487.04/470.06s optional; relevant slow1pass
50.76/48.89s. Both hosted43006909815 jobs pass2579/58skip/149deselect/1historical
warning638.31/866.85s. Full PR checkoutec6bb135 source inventory equals7f191d4.
All raw logs/hash receipts retained in source-7f191d4-checks.

Interruption review catches initialFalse poker-work reporting surviving partial
worker execution. Two synthetic REAL-label cases reproduce before repair;
4training/native cases pass afterward. Source/permit/events are mocked: no actual
real game, learner or solver runs. Persist attempted/unknown state before worker
startup, infer only witnessed progress, retain per-path cumulative-work lower
bounds and keep missing progress unknown. Hard-timeout receipt test verifies this
without a child exception handler. Confirm compute permit separately from run
completion. Complete real controls/thresholds/Native publication gates unchanged.
Journal88 explains the distinction. Focused182base21.54s/192optional20.85s and
repository lint/format/typing pass. Fresh full source-cohort checks are required
before the still-unrun formal proof/cost forecasts/permit/real trajectory.

### November11 — final own-opponent source checks complete

Source4878eb99de8ab021261576249e43c1edce3e0c78, complete sourceSHA
2fdf2e2844cce31d1c25fc4bc23b5088a46efa53c74f03b07c720cd2c48c5a4a:
both local base2583pass58skip149deselect437.38/420.75s; optional2650pass149deselect
485.58/473.14s; relevant slow1pass10deselect50.83/49.00s. Both hosted43009320593
jobs pass2583/58skip149deselect1historical roundoff warning506.05/911.71s.
Checkout5f4f19f04aa7aaa0ef5e3be694ecea7be2b44d8e complete source inventory equals
4878eb9. Raw logs/hash receipts retained in results/opponent-information/software-checks/.
These are software checks, not a real training admission. The next required stage
is the full fictional own/publication/native rehearsal under its shared180s.

### November11 — complete published own/native software rehearsal

C3source4878eb9 passes the formal complete30path/324raw/216book/30warm/108compose/
432profile/216logical/1152fixed fictional pipeline. Own14.940791666s published
f969a04 BEFORE actual native construction. Native7.353254167s; full shared clock
25.260755625s<180 includes own publication and final own replay. Both own error
maxima0; policy/book bits exact. Independent OpenSpiel2.0.2 all432/1152 scalar
checks pass max1.1102230246251565e-16<1e-9; publishedf84d698. Checked software
gate accepts; base312 published-own replay passes. Journal89 distinguishes this
software evidence from poker strength/admission.

Next: actual three complete old-OWN cost repetitions under unchanged900s each,
all own published before three native repetitions, then fixed conservative
forecast and checked published compute permit before any new real trajectory.
Prospective routine output/publication choice: fresh ignored output folders keep
source clean between repetitions; exact byte-identical administrative copies go
to canonical cost/{i} publication paths, retaining originals/args/scratch. All
required child work is inside the measured command; later publication copying
is separate. No scientific inventory, tolerance, seed, formula or cap changes.

### November11 — publish all three complete own cost repetitions

Source4878eb9 complete old-OWN cost runs0/1/2:230.234677291/232.654408792/
233.219642833s<900 each; D=233.219642833s, using the required maximum. Each
retains324raw/216books/30warm/108composed/432profiles/216logical/1152fixed and
complete zero-error chip/unitless replay with exact policy/book bits. New poker/
toy training work0 and no reference construction. All three report figures
visually inspected in the first repetition; clearly labeled old stand-ins.

Original ignored outputs/args/scratch retained. Canonical publication copies
under cost/{0,1,2} are verified byte-identical, with SHA manifest in
cost/own-publication.json. Publish ALL own cost evidence before first native
cost construction. Native repetitions, full forecast and compute permit remain
pending; no real trajectory or strength/default/fresh/global admission.

### November11 — complete and publish all native cost repetitions

After own publication6c9c200, source4878eb9 native cost0/1/2 completes
368.528307792/371.195141500/371.648972542s<900 each. Every repetition verifies
all 432 profiles/1152fixed, maxerror1.8474111129762605e-13 chips<1e-9, no exported
actions or training. N=max371.648972542s. End-to-end clocks include own/source/
publication checks, all reference construction/scalars and final own replay.
Byte-identical canonical copies and SHA manifest retained at cost/native-publication.json;
original ignored output/args/rawjournals/logs remain. All outcomes included.
The actual full forecast command must still verify every receipt/input and the
fixed T/D/N rules before a checked published permit. No real trajectory yet.

### November11 — complete checked forecast passes unchanged limits

Actual full forecast408.798313416s<900 verifies all3own costs, all3native audits,
published source/proof/checks,87input seals and all24 original B4 timing paths.
T610.943356249918,D233.21964283299894,N371.6489725419997s; no half-budget discount.
Fixed guarded own4110.21271066567<7200 and native863.2979450839994<900 both pass.
All source/seed/label/iteration/cap/acceptance rules unchanged. Full receipts,
child, journal and command log retained; journal90 explains forecast versus
strength. Publish this result, then create and publish the checked compute permit
before actual new real trajectories. Forecast is not an actual-runtime guarantee
or stronger/default/fresh/global admission.

### November11 — checked compute permit before real initialization

The actual admit command completes8.905501334s and accepts source4878eb9/SHA2fdf...
against the complete checked/published proof, all cost receipts and forecast
seals. Statusown_opponent_learning_admitted; own/native7200/900 caps retained;
new_agent_default/fresh_global_admissionFalse. Publish permit/child/journal/log
BEFORE any worker initialization. This grants the bounded known-game computation,
not successful completion or policy quality. All30paths/36original B4 barriers,
all seeds/readouts, own replay, source checks and independent comparison remain
required. No actual new real trajectory has started at this permit checkpoint.

### November11 — actual study rejects a malformed permit before training

The first actual study command fails preflight in8.845484625s with
`complete checked published study permit changed`. No worker initialization,
poker training or reference construction occurred. Exact failed parent/child
receipts, command log and SHA manifest are retained in
results/opponent-information/failed-admission-4878eb9/.

Diagnosis: permit() builds89 sealed inputs (87 forecast inputs plus forecast and
source-check receipts), but the common CLI write path overwrites input_sha256
with19 routine input pins. The fail-closed reader detects the lost inventory.
Earlier unit tests covered permit construction but did not round-trip it through
CLI persistence. Add that missing integration/failure coverage and separate the
permit seals from routine command pins; preserve all scientific rules. Fresh
corrected-source checks, proof, cost measurements, forecast and published permit
are required before another real attempt. No model-strength claim follows.

The synthetic CLI-to-persisted-reader regression fails before the fix and all39
related admission/CLI tests pass afterward (4.58s). Mutations cover missing/
changed seals, legacy overwritten inventory, cap/source changes and edited input
bytes. Complete repository Ruff/format/strict typing pass697files/587typedfiles.
Keep permit_input_sha256 separate from routine input_sha256; no scientific gate
is weakened. Exact prior proof/check/cost/forecast/permit files are retained under
source-4878eb9-pipeline with original-path hashes and historical checkout guidance.
Journal91 explains this missed integration path; full corrected checks pending.

### November11 — complete corrected permit-source checks

Source5cbb87e2899d214059c3748cc6c53dd39ba4b1f1, scientific sourceSHA
b0bc9c37e55fa65e14fc5e44548064b54d548e7ac19605e4b3d8528b3d37d038:
base2590pass58skip149deselect467.10/452.45s; optional2657pass149deselect
518.75/501.64s; relevant slow1pass10deselect56.33/54.42s. Full lint/format/
strict typing/hooks and before/after runtime/module/source guards pass.
Hosted43019692776 both2590pass58skip149deselect1historical warning898.91/908.68s.
Actual PR checkout e9d7ec0f4abfd3dde00dc45cc90c5553d42bdbfc matches all291
scientific source/config/entrypoint/lock files. Raw local/hosted logs and hashes
are retained in software-checks. These checks validate software; the corrected
formal proof/cost forecast/published compute permit are still required.

The first corrected-source fictional launch refuses an existing default scratch
folder left by the prior source. This is a launch-path error, before worker
initialization/toy or poker training/reference; full failed own evidence was
published at a7c4fb1 and is retained in failed-software-scratch-5cbb87e. The
external launcher now supplies an explicit fresh scratch folder for a new full
rehearsal. Source, configs, seeds, complete inventories, caps and gates remain
unchanged; no partial run is resumed or favorable subset selected. Retain both
attempts and require the complete new own/publication/native shared-clock proof.

### November11 — corrected-source full fictional proof passes

Source5cbb87e own6.453446791s publishesbc76e54 BEFORE native construction;
native7.619018167s, full shared16.982763458s<180 including own publication and
final replay. All30fictional paths/324raw policies/216books/30warm/108composed/
432unique/216logical/1152fixed retained. Own chip/unitless replay maxima0 and
exact policy/book bits. Independent OpenSpiel2.0.2 scalar maxerror
1.1102230246251565e-16<1e-9, no exported actions/training. Native published1b4130e;
actual software gate accepts tiny-only evidence. Read-only base312 replay also
passes and its exact JSON/child/journal/log copies retain filenames in
software/base312-replay. All3fictional report plots visually inspected.

Next: all3complete old-OWN costs, own publication, all3native costs, full fixed
forecast and published persisted permit round-trip before real training.
Fresh ignored output/scratch folders distinguish this source from prior runs;
canonical publication copies remain byte-identical. No caps/seeds/gates changed.

### November11 — all corrected-source own cost repetitions pass

Source5cbb87e complete own cost0/1/2 times231.491571875/233.828099000/
233.752731375s<900 each. D=max233.82809899999847s. All three complete inventories
retain324raw/216books/30warm/108composed/432unique/216logical/1152fixed, exact bits
and zero chip/unitless replay errors. New poker/toy work0; no reference created.
First cost's CSVs and all three PNGs match prior old-data reports byte-for-byte.
Original ignored outputs/scratch/args retained; canonical files/logs copied
byte-identically with SHA manifest cost/own-publication.json. Publish ALL own
cost evidence before first corrected-source native cost construction. Full
native costs/forecast/persisted permit/real study remain pending.

### November11 — all corrected-source native cost repetitions pass

After own publicationc7930ad, complete native costs0/1/2 take356.133935375/
357.755006833/358.878548334s<900 each. N=max358.8785483339998s. Each verifies
all 432 profiles/1152fixed, maxerror1.8474111129762605e-13 chips<1e-9, no exported
reference actions or training. Full command times include published-own/source
preflight, reference construction/scalars and final own replay. Exact canonical
copies/logs and SHA manifest retained in cost/native-publication.json; original
ignored output paths/arguments remain. Publish all native evidence, then run the
full fixed forecast command; no corrected-source permit or real trajectory yet.

### November11 — corrected full forecast passes fixed limits

Actual complete forecast407.786650958s<900 verifies all3own/all3native costs,
software proof/source checks,87input seals and all24 original B4 timing paths.
T610.943356249918,D233.82809899999847,N358.8785483339998s. Guarded own
4111.429622999669<7200 and native837.7570966679996<900 both pass unchanged
strict formulas; no half-budget discount. Source/config/seeds/caps/gates unchanged.
Parent/child/journal/full command log retained. An outer zsh launch used a
reserved variable and stopped BEFORE Python; its diagnostic log is retained
separately. It created no scientific receipt or run. Corrected wrapper uses
forecast_rc. Publish forecast, then checked permit and actual persisted reader
verification before real worker initialization. This is not a strength result.

### November11 — corrected persisted permit retains both input inventories

Actual admit8.952586750s completes source5cbb87e/SHA b0bc... with status
own_opponent_learning_admitted. Saved permit_input_sha256 retains89 seals;
routine input_sha256 separately retains19 pins, fixing the reproduced overwrite.
Own/native caps7200/900, new_agent_default/fresh_global_admissionFalse.
Publish complete permit/child/journal/log before the independent actual
require_admission read-back and study entry. The real entry repeats all its
prerequisites inside its unchanged whole-command cap and binds each worker to
this exact permit/original3.11.17/NumPy2.4.6 runtime. No worker initialized at this
publication checkpoint; completion, all36old B4 barriers, all30paths/432profiles/
1152fixed and independent audit/quality gates remain ahead.

### November11 — real own comparison complete; primary superiority gate fails

Published permit9fe8083 passes the actual require_admission read-back (89sealed
inputs/19routine pins) before real entry. Complete own command635.308768500s<7200
trains30paths with210001434actual charged node visits, all seeds/readouts retained.
All36original B4 boundaries match108policy/72ledger/36work-guard checks before
scoring; full raw/archive/reply/support/fixed replay has0chip/unitless error and
exact policy/book bits. All324raw/216books/30warm/108compose/432unique/216logical/
1152fixed are retained. All3actual figures visually inspected.

Final linear-average medium mean exploitability falls from ordinary coarse
2.1726835365908252% to mixed0.597027911089941% initial pot. Mixed median
0.5531623046246893%, worst1.0355187414374256%; paired-coarse minus mixed median
improvement2.8049282275745457percentage points. Two seeds improve, one worsens.
Low mixed median6.609080361175546e-9%, worst9.258394215892083e-8%; median paired
improvement0. BOTH games pass absolute median<=1%/worst<=2.5% and whole-average
coverage100%, BUT the preset strictly-positive paired improvement in BOTH games
FAILS on low. Preserve failure; no new threshold, readout rescue or promotion.
Post-warm reach support low71.11–80.78%, medium97.24–97.56%, reported separately.

These are own-calculated known-game results pending the independent numerical
audit. Publish complete own JSON/child/journal/5archives/6reports/command log/
permit-read-back evidence before real native construction. No default/fresh/
global admission. Issue4 remains open; source/seeds/caps/gates unchanged.

### November11 — real independent audit validates complete own measurements

After own publication691a7074af105b77eebbfc84b6debb2589d43217, the actual native
audit completes358.570928584s<900. All432policies/1152fixed targets validate with
maxerror1.8474111129762605e-13 chips<1e-9; no exported reference actions/training.
Own/source/permit/publication preflight, three native workers and closing own
replay count inside the command. Pinned OpenSpiel2.0.2 Apache2 license verified;
source SHA b0bc.../original runtime retained. Publish full native JSON/child/
journal/command log. The numerical gate passes; the overall two-game positive-
improvement gate FAILS and no default/fresh/global promotion occurs.

Read-only digest diagnosis: low final linear paired/mixed probability hashes
are identical for seeds20261302/20261303. Their exact tied scores are not decimal
display rounding. The other seed is slightly worse at an already tiny scale.
Low means lowSPR (38behind324pot); medium has182behind36pot. Consistent with
little improvement headroom in low; not a post-hoc exception or proof of broader
strength. README reports the independently checked medium result and overall
failure. Cross-runtime data-only replay/report and final artifact CI remain.

### November11 — real archive portability and complete report

Python3.12.15/NumPy2.5.4 BASE readonly replay passes140.020708584s; OPTIONAL
readonly report passes151.335751459s. No training/reference construction. All3
numeric files and all3PNGs are BYTEIDENTICAL to original report; original311
figures already visually inspected. Exact original-output copies preserve
replay/report receipt/child/journal basenames in portability312 with logs/SHA
manifest. These validate data/math within fixed1e-9chip/1e-12unitless tolerances,
not bit-exact new trajectory execution eligibility. CLI read-back retains the
original own-replay maxima in its emitted metadata; do not label those as fresh
312 error measurements. Actual311own0/native1.847e-13 errors remain separate.

Method now states the known-game result, all-seed failure, failed low superiority
diagnosis, remaining medium seed2 extra-information gap, limitations and3practice
interview answers. No original gate is changed and no quality promotion occurs.
Final artifact hosted CI BOTH jobs must pass before a history-preserving merge.

### November11 — prospective saved-decision and common-opponent diagnosis

Issue4comment6797629916 registers the next bounded read-only investigation.
Frozen own/native/config hashes select both known games, all3seeds/all4arms,
final10m linear averages:24profiles/48responding-seat traces. The192condition
common-opponent cross panel separates changed target from changed opponent.
Full row/street/root accounting, diagonal source agreement, zero-sum hybrid-EV
identities, cached-viewer tamper tests and constructor blocks define acceptance.
Top10groups/4examples are display only; full owned rows remain. Fixed900s data-
only bound includes source-own replay and all work; original learning/audit caps
and failed superiority gate unchanged. No new training/reference/default/fresh/
global admission. Implementation and actual results are pending in isolated
research/opponent-gap-inspection; PR49's final artifact CI runs unchanged.

### November11 — merge verified experiment; implement read-only inspection

PR49finalCI43032413121 passes both2590/58skip/149deselect/1historical warning,
525.95/913.56s. Exact decoded logs/hashes retained in opponent-information/final-ci
and explicitly scoped to the previous source, not this new diagnostic. Self-review
records no independent human review. History-preserving merge07a39623960b615e65336bfcd13ac05869e63db2.
Main fast-forwards only after a fresh complete snapshot; all10unrelated user
file bytes, index entries, status and staged/unstaged diffs remain identical.
Main package path checked;7permit regressions pass0.12s, with a non-failing
pytest-cache write warning from the filesystem permissions. No user files reset.

The new isolated branch implements frozen24/48trace and192common-opponent
accounting, source/native-root verification, complete partial retention and a
cached browser. Both ordered seats, every owned row, street/group sums, reply
fingerprints, cross diagonal/zero-sum/common-opponent identities and no mutation
are checked. Existing output and failed/interrupted caches are refused.
Focused35tests pass on311; earlier33on312 before two additional browser cases.
Complete Ruff/format/strict typing pass. Full relevant local/hosted checks and
actual full diagnostic reproduction are still pending; no new learning or
reference is constructed. The diagnostic clock starts at thin-script entry before
numerical imports; interpreter startup is not measured or claimed. Original
learning/audit caps unchanged. Journal95 remains prospective until actual output.

### November11 — complete saved-decision and common-opponent diagnosis

PR50 source9bfe45c/fingerprint0927e4b runs the frozen complete read-only command
in139.8018285s<900:24profiles/48responding traces/192cross conditions. Every owned
row, street/group/root sum, reply fingerprint and diagonal source value checks;
maximum trace discrepancy1.2273010890382813e-13 chips<1e-9. Cross zero-sum/common-
opponent identities pass; no training/reference/default/fresh/global admission.
All new off-diagonals remain own calculations, not a new native audit.

Both full local bases2625pass58skip149deselect, lint/format/types/hooks/source/
runtime guards pass; relevant optional35pass1.00/.97s. SourceCI43036606438 BOTH
jobs2625pass58skip149deselect1historical warning896.51/540.86s. Exact logs/receipts
retained in results/opponent-decisions-checks. Agent-run actual-cache CLI smoke
covers all48game/seed/arm/seat selections in one load, navigation, invalid key/
rank and quit; no personal learning/time inferred. Final artifact CI remains.

Unfavorable mediumseed20261302/mixed responding-seat1 gain.6782093457chips is
concentrated in turn groups819/31 (.3988370387/.2216959014;91.50%combined).
Their fine best reply calls using optimal later continuations. Saved prefix
mass.4005350448vs paired.1546846116; not a conditional action frequency or causal
local-error proof. With paired opponent fixed, paired->mixed target gap slightly
improves.3309940111->.3279387575; switching that mixed target's opposite seat to
mixed raises gap to.6782093457. Full both-game/all-seed/arm inventories retained;
method/journal95 explain common-opponent scope, turn/river dependence and next
controlled continuation question. Original superiority gate still FAILS; issue4
open. These read-only results do not admit another learning study.

Publication hooks first caught a missing tool path, then treated the exact
external launcher record as repository Python. The path was restored and the
unchanged launcher bytes retained as run_checks.py.txt (a historical execution
record). No source, test, config, output or scientific gate changed.

### November11 — prospective fixed-turn continuation diagnostic

Issue4comment6798673089 registers the next question before implementation/output.
Frozen turn-continuations config binds PR50's complete manifest/summary/config.
Both known games/all3seeds/all4arms/final10mLINEAR,24profiles/48responding seats,
four continuation panels give192root values plus every owned TURN row/menu.
Saved/restricted-river/fine-river preserve ownTURN and all opponent probabilities;
full fine reply explicitly may change ownTURN. Exact information-set masked DP,
analytic/enumerated controls, original reply slices/roots, root ordering/stage
telescoping, support/inventory/source checks, retained partial failures, constructor
blocks and cached browser define acceptance. Separate900s data-only bound does
not admit learning or change historical caps/seeds/gates/default. Implementation
and measurements pending; PR50 final artifact CI continues unchanged.

### November11 — implement the fixed-turn continuation controls

New modules only; historical scientific/diagnostic source bytes remain unchanged.
Masked own DP freezes unselected rows and aggregates hidden histories before
maximizing. Complete runner replays original evidence, checks prior full-reply
fingerprints/river slices and every owned turn menu/support, then writes complete-
profile partials before advancing. Cached browser shows saved/restricted-river/
fine-river/full-reply values, fixed-opponent signs and public history; no hidden
opponent cards or universal advice. Existing/failed/temporary outputs refused.

Focused62tests PASS0.82s; full lint/format/strict typing pass. Independent analytic/
pure-enumeration fixtures check both target signs, nonclairvoyant sharing,
generic masked-vs-sliced full response, nonmonotone finer-row Q with improving
root, exact ties and zero support. Genuine uniform-own-engine/source corruption/
interruption tests and complete UNIT-only cache/schema/browser cases pass.
Initial integration fixture failures came from passing unserialized tuples to
the list-only archive decoder; fixture now performs the actual JSON round trip.
An additional complete prior-reply fingerprint guard is included. No actual full
continuation measurement/new training yet. Complete relevant local/optional/
hosted checks pending before the registered full diagnostic and merge.

### November11 — merge saved-decision diagnosis and preserve main changes

PR50 finalCI43039703564 passes BOTH2625/58skip/149deselect/1historical warning,
916.61/519.27s, before history-preserving merge967990bccd044623150a0a6a1e1f44764ded99ae.
Self-review6798971799 explicitly Codex-assisted solo review. PR51 retargetedmain;
scientific source/head8e347e2 unchanged. Fresh actual main snapshot before FF:
all10unrelated file bytes/status/staged+unstaged diffs/userpath index entries
preserved. Main editable package path and actual seat1 cached browser checked;
35focusedtests PASS0.94s with cache writes disabled; all10remain exact afterward.
Exact PR50 finalCI logs retained with old-source scope in the next publication.

### November11 — complete fixed-turn continuation measurement

Source8e347e23fc6e3d149d61e3311c3f7bbecd4bc2b1/fingerprint45bb7d825589a22a71151620e5efd84f8854ae6938052a0e8128723239c7a0dc.
Both full local bases2687pass58skip149deselect (476.86/469.51s), all lint/format/
types/hooks/before-after source/runtime guards pass. Relevant optional62pass
.96/.92s. Hosted sourceCI43041865392 BOTH2687pass58skip149deselect1historical
roundoff warning889.03/467.53s. Scientific source/config/seeds/caps/gates unchanged.

ACTUAL complete data-only command137.917452209s<900 retains24profiles/48conditions/
192root values/384owned TURNrows. All baseline/fullreply fingerprint/river slice/
Q/support/source comparisons have0chip error on311.17/NumPy2.4.6. Root ordering,
stage telescoping, complete turn menus and immutable policies/games/inputs pass.
No trainer/reference constructed; new calculations have NO new native audit.
Actual cached-browser agent smoke coversall48 selections in one load, constructors
blocked, n/p/s/o/g/t/q, invalidkey/rank and quit; not personal practice/time.

Mediumseed20261302/mixed/seat1/nines call: saved-25.8949808893, bestrestricted
river-18.8080607860, fine river/fullreply-16.9943146228 vsfold-18. QhKhcall
-29.023136/-18.439778/-17.446327, also flips onlywithfine river. Rootstages
.0325374242/.00743365886/.63823826267 sumoriginal.67820934573gain. Saved turn
folds suppress realization of the fine river opportunity; root-only small fine
increment does not rule out missing river information. Not a universalfloor,
causal training conclusion, newstrength/default/fresh/global admission or change
to originaloverallFAIL. All games/seeds/methods/seats retained. Method and plain-
English journal96 explain result/units/limits and next conditional-range question.
Final artifact CI and evidence publication remain before merge.

### November11 — prospective local river range-weight mechanism test

Issue4comment6799471551 registers the next question before code/output. New
frozen config binds complete PR50/PR51 evidence. Same24profiles/48responses,
two own river suffixes/actual-vs-compatible-prior weights give96suffix conditions/
192LOCALpanels, all owned RIVER rows/menus/compatible combos. Source conditional-Q
mixture reconstruction, blocker/history/support normalization and singleton/
identical/refinement convexity controls define math acceptance. Fixed per-game/
seat uniform-decision weights normalize BEFORE shared actual-support filtering;
no favorable subset or post-filter normalization. Original and full-static-probe
groups retain separate denominators and signed changes. No effect-size gate,
root-EV/retraining interpretation, new native audit/training/feature/default/
fresh/global admission. Separate900s data-only clock and partial/failure retention;
full relevant checks before measurement/merge. Implementation and outcomes pending;
PR51 final artifact CI43044961257 runs unchanged.

### November11 — prior continuation result merged; range math checkpoint

PR51 finalCI43044961257 BOTH2687/58skip149deselect1historical warning,
800.26/902.83s, before history-preserving merge01f91df39ba25ea6c53ba7f81a257c1f49b67476.
Self-review6799767883 explicitly Codex-assisted solo review. Exact decoded final
logs/length/hash receipt retained as old-source evidence, not checks of this new
range calculation. Fresh main snapshot before FF preserves all10actual user
file bytes/status/staged+unstaged diffs/userpath index entries. Main package path,
new default four-column viewer and62focusedtests PASS1.89s; preservation verified
again afterward. No personal practice/time inferred.

New range core25tests and own-engine integration/group controls15tests pass:
40PASS5.76s, relevant lint/format/strict typing pass. Independent terminal sums
and both target signs check actual/prior mixtures, no hidden-world maximization,
own-prefix exclusion, fixed pre-filter weights/zero support, wrong combo/weight
order, blockers, aliases, nonfinite inputs, singleton/refinement/identical controls.
Genuine uniform UNIT policies on both own games reconstruct every river menu,
sourceQ/support and frozen suffix without training. Initial tamper-test reversal
left a palindromic policy row unchanged; the fixture now changes the maximizer
explicitly. Test config typing corrected. No actual saved-profile range study
or new feature/learning. Complete command/cache/schema/failure/browser integration
and full relevant source checks remain before measurement.

### November11 — complete local range command/cache/browser implementation

New-source integration now retains every river row and both own suffixes,
builds192local panels/two group controls (384CSVrows), replays bound C5/C6/own/
native receipts and original own math, and checks original reply roots/Q/support.
Own prefix reach is excluded from range inference; declared priors match the
chance-only compatible range, including wrong-order guards. Source weights update
only actions inside the declared spot, not its fixed historical preflop prefix.
Every complete profile is written before the next starts; complete/partial/
failure destinations cannot be overwritten. Cached reader checks all artifact
hashes and lazily rechecks detail bytes, full local mixture/group arithmetic,
typed24/48/96/192inventories and fixed-support weighting. Browser adds r to
n/p/s/o/g/t/q for own suffixes, showing hypothetical range order and both weights.

Focused72tests PASS8.44s; full Ruff/728format/strict typing612files pass. Includes
independent terminal sums, hidden-state/weighting/source guards, real uniform UNIT
engine fixtures, source corruption, complete synthetic-cache schema/tamper,
constructor blocks and genuine completed-profile interruption retention.
All historical source/config/test/lock bytes remain unchanged; no actual saved-
policy range comparison, training, feature or default change yet. Full relevant
local runtime/optional/hosted checks precede measurement; final CI before merge.

### November 11 — range source checks pass locally; hosted account block retained

Published source42cd59f31324566b3286fc112e496438f5c484f4, scientific fingerprint
987c636e258c4f866d22b23cbc6bc4349493bc0874b994ac5d0cbc8e258512bd, checked from
a clean immutable detached checkout. Both full bases pass 2,759 tests, 58 skipped,
149 deselected (Python3.11.17/NumPy2.4.6:484.87s; Python3.12.15/NumPy2.5.4:472.25s).
Full lint/728-file format/strict typing612files/hooks/source/runtime/package-path
guards pass before and after. Focused all-extras checks pass72tests10.36/9.65s;
not the entire optional historical suite. Exact raw logs/receipts/launcher and
hash index retained in results/river-range-checks/source-local.

Hosted source run43050870261 fails both jobs before ANY steps. GitHub's exact
annotation cites failed account payments or a spending limit; no actual billing
dashboard inspected or payment/limit changed. This is not a code/test failure.
Retained job metadata/annotations; no fabricated job logs for unstarted jobs.
Required hosted source checks have NOT passed. Actual range comparison unrun,
measurement admission false, PR52 draft. User notified; continue only independent
work while Actions availability is unresolved. Scientific caps/seeds/gates stay.

Added a plain-English four-column terminal exercise using completed C6 evidence.
Actual-cache agent smoke passes default/rank2 plus n/p/s/o/g/t/q; separately
retained logs/receipt. Journal97/navigation/current status explain local success,
external block and unchanged pending comparison. No user completion, personal
time or mastery inferred. No main update or unrelated-file mutation in this step.

### November 11 — complete the local river range-weight comparison

After explicit public-visibility authorization and CI retry/resume, source run
43052779450 attempt2 passes BOTH jobs on unchanged published a682d91c605bdfe19b5d1153ffc47a59dd5b5000:
2,759passed/58skip/149deselect/1historical roundoff warning, 675.02/944.82s.
All lint/format/types/hooks steps pass; exact source/job metadata and decoded
logs retained in results/river-range-checks/complete. Prior account-blocked
attempts stay intact. No actual billing dashboard or spending settings changed.
Expired temporary environments restored to persistent work paths from the same
lock; original311.17/NumPy2.4.6/active module/clean source/config verified, 72
focused tests PASS8.87s. Scientific fingerprint remains987c636e258c4f866d22b23cbc6bc4349493bc0874b994ac5d0cbc8e258512bd.

Only then ACTUAL complete data-only command passes in168.794338750s<900:
24profiles/48responses/96suffixes/192LOCALpanels/384CSVcontrol rows, 44,160
profile-seat river-row records (88,320 across both suffixes, not independent
hands). Largest source mixture/root/Q error8.526512829121202e-14chips<1e-9;
unitless support/normalization error2.220446049250313e-16<1e-12. Complete raw
rows/groups/unsupported cases/partials retained, trees/policies/source inputs
unchanged and constructors blocked. No new native audit/training/feature/
default/fresh/global admission; original overall learning FAIL remains.

Both runtimes validate every cached detail and render all96 selections plus
n/p/s/o/g/t/r/q/invalid-key/rank (11.1189/8.4191s); agent activity, not personal
practice. A retained one-off analysis execution record formats all384 raw rows
into192paired control rows, all-case tables and both visually inspected plots.
Both runtimes reproduce all three numeric/text files and both PNGs byte for
byte; raw inputs unchanged. Cached postprocessing time is separate from the
900s original command, not new learning or original full replay. Its first
Matplotlib import used a temporary font cache; the warning is retained, and
subsequent checks use an explicit writable cache. Initial reporting-record
lint/line wrapping was fixed before execution; no scientific source changed.

In unfavorable mediumseed20261302/mixed/seat1/fine suffix, actual→prior local
cost is1.026045948→0.635127679 in the saved partition (34→19conflicts/774groups),
and0.386738718→0.164204558 with full static refinement (23→11/1,386). Same
static-signature nines5d/5h have identical comboQ but different posteriors and
call/fold preferences; common50/50prior removes that conflict. QhKh9d/9h still
prefer fold/raise under commonprior because frozen later responses differ.
Prior substitution also creates a small seat0 static conflict (0→.0002828928).
All192paired control rows retained:66lower local cost,10higher,116within1e-9;
dependent descriptive counts, not a success rate or learning gate. These local
costs are NOT rootEV/retraining gains or additive to the prior.678209root gap.

Method/README/plain-English journal97 and a dated note of the user's actual
negative-continuation question updated. Added two publication tests checking
the real full cache and every reported pair/plot digest; initial2PASS9.12s.
Combined focused publication suite74PASS20.62/16.94s on both runtimes; whole
Ruff/732-file format/strict typing613files pass. Scientific source bytes remain
unchanged; the new publication test validates measured artifacts rather than
altering their calculations.
Complete relevant artifact checks and BOTH final hosted jobs required before
merge; those final results are reported separately. Main and unrelated user
results remain untouched at this checkpoint. Next question concerns residual
later responses and their stability, not immediate range-only feature adoption.

### November 11 — final local range publication checks

Immutable result commit be6f91dd63ad041f5fac6f0d9179af449dba4de4 passes both full
local bases: 2,761passed/58skip/149deselect, 504.91/488.55s. All lint/format/strict
typing/hooks and before/after clean HEAD/runtime/module/scientific-source guards
pass. Focused ALL-EXTRAS suites74PASS20.49/16.84s, not the entire optional
historical suite. Exact logs/receipts/launcher retained in final-local; wrappers
521.5702/506.9642s base and25.9293/21.9643s optional, setup excluded. Original
scientific fingerprint987c636e... unchanged. Subsequent edits are documentation/
evidence only, including clarification that a posterior feature might also proxy
future responses; this local control does not prove a particular feature fails.
Both final hosted artifact jobs remain required before history-preserving merge.

### November 11 — prospective two-sided public range-blocker diagnosis

Issue4comment6814712059 registers the next question before code/output. PR52
post-merge mainCI43086132574 passes both jobs. Fresh actual user-main snapshot
before isolated branch creation captures all ten current unrelated result edits;
no main files changed. Frozen config binds the complete C7 manifest/summary/CSV.
Same24profiles/48responses/96suffixes/192source range panels and all44,160
profile-seat river records (88,320acrosssuffixes); five nested controls produce
960grouped panels. Source static / own public range availability / both public
masks / both masks+joint matrix / exact singleton. No new Q/posterior/policy or
training; source reconstruction, physical-card oracle, private-input exclusion,
refinement/singleton and joint redundancy controls define acceptance. Retain
all unsupported rows/common weights/denominators and no positive-effect gate.
Separate900s cache-only full-validation/feature/regroup/write clock; original
caps/seeds/gates unchanged. Full local/optional/hosted source checks precede
measurement; both final artifact jobs before merge. Implementation/results
pending; a future feature-learning test needs its own contract/admission.

### November 11 — two-sided blocker implementation checkpoint

PR53 adds new modules only: public two-range availability/joint features,
independent scalar reconstruction and nested grouping, pinned cache schema,
guarded runner with per-profile partial/failure retention, and offline inspector.
Historical source/data remain unchanged. Fifty-three focused tests pass in2.35s;
whole-repository Ruff lint/format and strict mypy622files pass. Synthetic runner
tests use explicitly fictional UNIT_ONLY parents, never scientific receipts.
Physical-card oracle/private-input exclusion/unchanged-feature/matrix redundancy,
same support/weights, all960 panel slots, corrupt cache and interruption/cap
tests pass. Full local bases/focused all-extras/both hosted SOURCE checks are
pending and must precede the actual C8 comparison. No measurements/training/
feature deployment or performance admission at this checkpoint.

### November 11 — complete two-sided public blocker comparison

Both full immutable source bases on21d3420 pass2,814/58skip/149deselect,
512.17/497.50s; all lint/format/mypy622/hooks/source-runtime guards pass.
Focused ALL-EXTRAS53pass3.05/2.90s, not all historical optional tests. Hosted
SOURCE43159009130 both pass BEFOREmeasurement (2,814/58/149/one old roundoff
warning each;935.75/670.86s). Original optional launcher filename errors exit4
remain with corrected successful logs; inherited receipt scope wording is
clarified as synthetic units only. No scientific source changes for that fix.

Published clean21d3420/fingerprint519887a... completes unchanged900s cache-only
command in11.832719541s. All24/48/96/192/960inventory and44,160/88,320rows,
96publicboards retained; max source reconstruction5.330805e-15chips and
2.220446e-16unitless. New manifest4559326c...; no new Q/policy/trajectory/native
audit or original full-game mathematical replay. Original data/source frozen.

Focal harder/mixed/seed2/seat1/fine actualcost0.386738718→0.046621048,
23/1,386→4/1,440conflicting groups;19originalconflictsresolved. Priorcontrol
0.164204558→0,11→0. Own-public masks separate recordedQhKh9d/9h observations.
All192panels:36costdecreases,156unchangedwithin1e-9,69positive residuals. Both
public masks addnothing beyondown in THESE inputs because every cross-seat
private-hand pair is disjoint and oldcompatibility already gives opponent
publicmask; overlap UNITfixture explicitly demonstrates general extra split.
Joint given BOTH masks is alwaysredundant forfixedranges. These two facts differ.
No causal response attribution, rootEV/exploitability/learning-gain or global
compression claim. Original overall learningFAIL/default/gates remain.

All24cached details/96browser selections+navigation/rank/EOF pass both runtimes
with blockedconstructors,20.441678459/18.489029166s. All5numeric/text/plot outputs
byte-identical; both figures visually inspected. Firstformat15.613303416s is
separate postprocessing; original font-cache warning retained. Exact sourceCI,
local bases/optional failures+correction, command/cache/report records committed
with plain-English journal98 and terminal exercise. Two actual-publication
regressions added; final relevant checks and both artifactCI jobs remain before
merge. Ten user main result modifications remain untouched in the isolated work.

### November 11 — final blocker publication verification

Immutable result88178f5 passes both full bases:2,816passed/58skip/149deselect,
514.55/493.73s. Whole lint/format/mypy623files/hooks and before/after clean
HEAD/module/runtime/scientific-source guards pass. Focused ALL-EXTRAS55pass
17.89/16.43s, including actual-cache/report checks; not the entire historical
optional suite. Exact logs/receipts/launcher retained in final-local. Check
wrappers528.460657125/508.836396458s base,22.758831667/21.682086709s optional;
setup excluded. Only docs/evidence change at this checkpoint. Scientific
fingerprint519887a... and all measured raw outputs unchanged. Raw sourceCI
timestamp spaces/BOM preserved verbatim, documented in complete/README.md;
code/docs diff check excluding only those two raw logs passes. Both final
hosted artifact jobs on the final PR head remain a merge gate; PR53 records
their conclusions without manufacturing an independent human review.

### November 11 — prospective compact public-range candidate

Issue4 comment6816637695 fixes ONE texture_range_q8_own_q8_b8 candidate before
code/measurement: old parent plus river public-own-prior blocked/nine-category
unconditional exact masses, q8 bins packed30bits. No actual-own filtering of
alternatives, hidden opponent/future/policy/posterior input or joint vector.
Config binds model/spots/C8 evidence and canonical contexts. Same six-control
full72 and later324sampled-readout inventories/gates fixed prospectively; old
thresholds/caps/seeds/failure/default untouched. This milestone ONLY definition,
encoder/structural/privacy tests and SYNTHETIC metric assessors; no actual row/
compression/savedQ/learning measurement. Actual admission alwaysfalse.
Main repeatCI43164682908 BOTHpassed; fresh snapshot063713UTC captures allten
current unrelated user edits before isolatedbranch. PriorPR53finalhostedlogs
retained as OLD source evidence. Journal99 explains plannedscope in plain English.

### November 11 — compact candidate implementation and focused checks

Protocol7ace4a3 precedes new code. PublicOwnRangeAbstraction only adds river
public-own-prior blocked/category q8 packed30bits to complete oldrange parent.
New source modules only; no historical scientific source edits. Fixed config/
context/input binding, finite adapter, serialization denial and public inspector
implemented. Scalar/set/exhaustive5card oracle, allcategory/bin/packing/privacy/
context/collision/structural tests and pure72full/324sampled SYNTHETIC threshold
grids total98PASS4.10s. Both known structural games preserve parent refinement/
concrete menus and zero recall; motivating observations split, pooled collision
retained. Lint/format/mypy629 PASS. Initial two typing/format defects corrected
before advancement; config/feature/gates unchanged. Full local bases/relevant
optional/hosted checks follow. No row-count/compression/savedQ/learning/native
measurement, actual admission or default change. Plain-English journal99 updated.

### November 11 — complete local compact-definition checks

Immutable source02b7c9b passes full bases BOTH2,914/58skip/149deselect,528.28/
509.72s; lint/format/mypy629/hooks and before/after clean HEAD/runtime/module/
source guards pass. Relevant ALL-EXTRAS(candidate plus old parent feature/gates)
BOTH165PASS9.17/8.44s, not the entire optional historical suite. Exact local
logs/receipts/launcher and public-only9h/9d encoding examples retained. Wrappers
549.335451667/533.413609875s base and18.340652083/17.522130625s optional exclude
setup. Sourcefingerprintf1f91bc0... unchanged by subsequent docs/evidence.
Config/gates/seeds untouched; original scientific source/data immutable. No
actual compression, candidate policy, exploitability, runtime forecast, native
audit or learning admission. Current milestone is tested definition ONLY.
Both hosted final jobs remain required before history-preserving merge; PR54
records actual conclusions. Journal99 includes current checks/plain-Englishscope.

### November 11 — compact full-control pipeline foundation

User authorized full-control admission for the one frozen candidate. Protocol
bb98b68 and issue4 comment6817542727 preceded code/measurement. PR55 adds new
source modules only: real/same-path tiny factories; immutable hashed snapshots
of policies, CFR+ regrets and linear average masses; complete 72-profile replay;
OpenSpiel scalar value/BOTH-BR audit and failure retention; stdlib process-group
clocks; source-bound check receipts; no-training structural cost, fixed forecast
and published-admission gates; complete report path. Six controls, both spot/model
pins, checkpoints, scientific caps and all scalar gates unchanged. No sampled
stage/default change. Original scientific source/data and allten main edits
preserved; latest snapshot072721UTC. Full installed pinned Apache license read
and recorded before reference unit fixtures. New78 focused tests pass; repository
lint/format/strict typing640 files pass after correcting a test adapter and
annotation/formatting defects. Full immutable local bases/relevant optional and
both hosted source checks are next. No measured proof, forecast/admission or new
real Hold'em trajectory yet. Journal100 explains what the new records establish.

### November 11 — full-control source gate catches a reference boundary violation

Both complete immutable1a9 base suites fail unchanged
test_postflop_training_has_no_reference_imports: 2,989pass/60skip/149deselect,
onefailure,533.09/516.60s. Initial optional suites278pass36.62/35.72s; they do not
override the base failure. SourceCI43177397488 also reports a failing311 job;
312 conclusion retained when observed. No measured proof, forecast/admission or
compact scientific trajectory. Native dispatch moved to evaluation; pure native
scalar receipt/schema arithmetic extracted into its own postflop module. This
removes the forbidden dependency instead of weakening/bypassing the guard.
Focused suite INCLUDING that unchanged guard now279pass32.24s; lint/format and
mypy641 pass. Failed source/logs/receipts retained under compact-full-control.
A corrected immutable cohort and both hosted jobs are required before advancement.

### November 12 — complete corrected compact source checks

Source02234c7/fingerprint9db8dab passes both immutable full bases2,990/60skip/
149deselect551.59/532.46s. All lint/format/mypy641/hooks and clean before/after
HEAD/runtime/module/source guards pass. Both relevant ALL-EXTRAS279pass37.58/
35.98s; not every optional historical suite. Both sourceCI43179157842 jobs pass
2,990/60/149/one oldroundoffwarning1019.59/976.81s, exact head metadata/logs
retained. Six-role receipt validator accepts all6. Rejected1a9 hosted attempt
retained311failure/312canceled (superseded); both local failures remain. Scientific
source fingerprint unchanged by this evidence/docs publication. No measured
tiny proof, forecast/admission or compact scientific trajectory yet. Existing
bounded kernel correctness fixtures are software checks. Publish checked-source
evidence now before the tiny own rehearsal; publish own archive before reference.

### November 12 — tiny own full-control rehearsal published before reference

Same corrected9db8 source, checked-source publicationa482067. The real full runner
on two dependent ordinary/negated Kuhn software contexts and six logical control
labels captures all72 profiles/12layouts and replays all72 with zero metric
change. Complete command1.8403986659996008s, cap180; own snapshot/manifest/child
clock hashes verified. No Hold'em study and no reference constructed in this
operation. Publish this own evidence before comparison-only OpenSpiel audit.
These duplicate fixture labels are software coverage, not12 poker treatments.

### November 12 — independent tiny proof and fixed nontraining costs

Own tiny evidence7a07560 was public before constructing the reference. Same
9db8 source/OpenSpiel2.0.2 Apache scalar adapter checks all72 values and BOTH
BR roots; maximumerror1.5265566588595902e-16chips. Complete native command
2.1196606250014156s under180. Three fixed nontraining real-layout repetitions
0/1/2 complete and replay all12 layouts plus their disk archives:6.20355091700003,
6.194329124999058,6.218683040999167s. Process lifetime high-water RSS191299584/
190709760/191676416bytes; not isolated per-representation memory. Uniform policies
and zero training weights only; no compact scientific trajectory or strength
claim. Publish proof/cost evidence before fixed conservative forecast/admission.

### November 12 — fixed compact full-control forecast

Published proof/cost27642b8 precedes forecast. Source9db8 replays the72 tiny own
policies/native comparisons, allthree12-layout cost archives and historical
60-profile range-mass own/native evidence. Fixed formula gives own94.07949982799036s,
native68.05050486082328s; each below unchanged900s. HistoricalH12.88399437499902,
A7.2285687910043634; S6.218683040999167; T1.8403986659996008; N2.1196606250014156.
Factor1.2 and margin4 unchanged. Complete forecast command23.047677708000265s.
This is a conservative engineering forecast, not a statistical guarantee.
Publish forecast now, then recompute/check published admission before any compact
scientific trajectory. No sampled/default/fresh/global promotion.

### November 12 — checked published permission for the compact full study

Forecast0f3cc57 is public before admission. Admission recomputes all prerequisite
proof/cost/history arithmetic and checks exact published input bytes. Complete
command24.040744333000475s; full_trajectory_admitted=True, actual_admission=False,
fresh_global_admission=False. Publish this permit before the real own run.
It authorizes only the frozen72-policy full-control study, not accuracy, sampled
learning, a new default or a stronger/general agent. Own runner rechecks the
published permit and dependencies under its unchanged900s complete-command cap.

### November 12 — complete compact own full-control grid, audit pending

Published permit5483c42 precedes real own command. Source9db8/original3.11.17/
NumPy2.4.6 completes all72 profiles/12layouts,1/16/64/256/1024/4096, allsix
controls/two games. Raw policy/regret/linear-mass snapshots replay72 with zero
metric change. Complete command50.698962332999145s, cap900; source/data intact.
Final own candidate exploitability2.577133407089394e-6%pot low and
0.00017718448559713964%pot medium, versus exact2.4545130526156374e-6% and
0.0001822898460278487%. Candidate130/364 rawpublicrows low;1770/3336 medium.
Allcontrol final uniform coverage1.0. These are OWN figures pending independent
audit; actual_admission staysFalse. Key UTF8bytes150986/1985885 exceed rawpublic
125226/1079292; fewer rows are not whole-memory savings. Publish allown evidence
before constructing the real comparison reference; retain allcontrols/checkpoints.

### November 12 — compact full-control admission passes

All72real own policies were publicbb73102 before real OpenSpiel construction.
Native72value/BOTH-BR comparisons pass, max1.3500311979441904e-13 chips, complete
25.00606195799992s. Authenticated result/report passes all11 frozen full checks
onboth known turn games. Candidate epsilon%pot2.5771334e-6/0.00017718449 and
rows130/364 (35.7143%),1770/3336 (53.0576%). Allcontrols uniform coverage1.0;
recall0/menus/context/work/source good. Report45.7460s includes temporaryfontcache;
allcontrol/checkpoint/layout/signed-difference CSVs/tables and both plots retained
and visually checked. OwnpeakRSS394985472bytes lifetimeonly; largerUTF8keys mean
no whole-memory savings claim. No sampled/fresh/global/default/superiority
promotion. Oldfailuresretained. README/method/journal100updated; finalhostedCI
onfinalpublicationhead remainsmergegate. Stopafterverifiedpublication/mainchecks.

### November 12 — fixed-work compact sampled pipeline, source checkpoint

Issue4 / [PR56](https://github.com/jimmy-sim/poker-ai/pull/56). Published
prospective protocol72755ed before implementation. Preserve the frozen six
representations, two games, seeds20261301–3, B4 signed/linear method and first
complete-iteration100k/1m/10m work crossings; no gate/cap changes. New own runner
captures36warm origins,108states and324current/uniform/linear readouts. Raw signed
regrets, both books, PCG64 states, counters and fsynced worker journals support
algebra/receipt replay and honest partial outcomes. Current support, exact-warm
mass and post-warm support stay distinct. Cost stand-ins are pinned OWN full
policies only and never construct a sampled learner. Native adapter requests
only independent own-policy value and BOTH best-response scalars after own
publication. Complete-command clocks, exact-source checks, conservative forecast
and checked published admission remain mandatory before real sampled training.

Initial relevant all-extras check:373passed in47.09s on3.11.17/NumPy2.4.6;
Ruff lint/format pass and strict typing658files passes. Includes new tiny
capture/original-B4 bit equivalence, complete archive, raw/worker/journal/clock/
native failure tests and old candidate/parent/archive/JIT integration. The prior
full-control72policies replay under unchanged historical dependency/Git blobs
in10.8452s. This is software/prerequisite evidence, not a sampled accuracy result.
New source-bound complete base checks, focused optional checks on both supported
versions and BOTH hosted jobs are next. No new Hold'em trajectory has run.
Learning journal101 explains the question and limits. Codex assisted; human
minutes not recorded. Ten unrelated main result edits were snapshotted with
their actual bytes and remain untouched. User cutoff10a.m.Pacific November12;
full downstream reserves apply before starting any real study.

### November 12 — repair the optional plotting import before admission

The first exact-source base311/base312 checks and hosted run43191822549 both
fail strict typing: Matplotlib was imported directly in the optional plotting
function while absent from the base environment. Relevant all-extras tests had
passed; they did not establish base compatibility. Retain the exact failed
logs/receipts in results/compact-sampled/failed-source-f8ded44. Replace only the
optional plotting import with the repository's runtime optional-import pattern;
no training/scientific fields change. Base-environment strict typing now passes
658files; the95new focused/architecture tests pass in13.61s. Repeat the full
source-bound base/optional/hosted cohort on the corrected revision. No real
Hold'em trajectory or source-bound rehearsal started before these gates.

### November 12 — distinguish collection from read-only replay

Before experiments, self-review found that gather's replay-only no-training flag
would be copied into an own training manifest. Separate replay-only metadata
from actual collection. Completed collection records sampled training; tiny
scope explicitly records no Hold'em training. A started/interrupted collection
records unknown progress, with journal receipts, instead of asserting no training.
Two regression tests exercise completed archive orchestration and interrupted
real-scope orchestration with mocked workers/permits; they authorize no study.
Focused new/architecture97tests pass14.40s; base strict typing658files and Ruff
lint/format pass. Export all324 numeric readouts and30 signed final LINEAR
candidate-baseline seed effects to CSV plus a primary-final Markdown table.
Superiority admission requires the full accuracy gates and each baseline's
two-game paired sign; storage/key/lifetime-RSS quantities remain distinct.
Scientific seeds/configs/caps/method unchanged. Repeat the mandatory exact-source
cohort on this corrected metadata/report revision before the first rehearsal.

### November 12 — complete sampled source gate, before rehearsal

Exact8da3c2c/source41b6f34d passes immutable base3.11/3.12:3082passed,
61optional skips/149slow deselected each (536.16/517.75s). Lint/format/strict
typing658files/hooks and before/after head/module/runtime/source guards pass.
Relevant locked ALL-EXTRAS375each52.47/52.45s. Hosted43193724153 BOTH pass at
the exact source head:3082/61/149/one historical warning each;1035.94/598.58s.
Archive exact observed raw logs, metadata, execution wrapper and digest receipts
in results/compact-sampled/checks*. The source gate validator authenticates all
six roles. Preserve initial failures and superseded local cohorts outside the
canonical successful receipt. Clarify that36separately initialized paths reuse
paired seeds and are not36independent random replicates; no design field changes.
Publish this checked-source checkpoint BEFORE the first source-bound tiny own
collection. No real sampled trajectory, forecast or admission yet.

### November 12 — source-bound tiny own rehearsal published before reference

Checked-source checkpoint4b30519 precedes the first formal own collection.
Software-only36B4 paths complete:36warm origins/108raw checkpoint states/
216cumulative books/324current-uniform-linear readouts. All raw work, RNG,
normalization, journal/pipe and exact-warm checks replay; no trajectory retraining
during replay. Complete command2.554832042s<180, exit0, no interruption/temporary.
Collection reports sampled trainingTrue and new Hold'em trainingFalse; replay
reports no sampled training. These are dependent ordinary/negated Kuhn aliases,
not36independent poker experiments or playing-strength admission. Publish ALLown
manifests/child/journals/warms/states before constructing the native reference.

### November 12 — complete tiny native rehearsal, cost stage next

Alltiny own evidence1edc652 was public before new reference construction.
OpenSpiel2.0.2 scalar-only audit checks all324values/BOTH-BR roots; maximum
error2.0816681711721685e-16chips<1e-9. Installed Apache2LICENSE SHA matches.
Complete native command5.027906125s<180, no failure/interruption/temporary.
Actual/fresh/global admission remainFalse; these dependent tiny aliases establish
software only. Next run the fixed three NONTRAINING own cost repetitions, publish
all own fixtures, then their three native costs. No new poker prefix or learner
is permitted in COST scope; conservative forecasts/caps remain unchanged.

### November 12 — all three no-training own costs complete

All three declared own cost repetitions finish under900s each, including startup,
source/full-prerequisite checks,108archive slots/324scores, raw replay and writes.
Complete clocks65.935652250/66.580811209/67.018426166s (exact raw receipts retained).
Each explicitly records sampled_training_performed=False/learner_constructed=False;
no new real prefix or initialization. Only pinned OWN full64/1024/4096policies
are repeated across the IO readout labels as declared stand-ins. Their labels
are not newly learned current/average strategies. Publish ALLthree own fixtures
and archives BEFORE any corresponding native cost reference. The forecast must
use the maximum WHOLE-command time, not an interim pre-replay manifest timer.

### November 12 — complete three native cost comparisons

Allthree own fixtures d2efbdc were public before native cost construction. Each
comparison checks324stand-in own values/BOTH-BR roots; complete clocks50.020953959/50.368202500/50.438742208s<900each.
Maximum error across all repetitions 1.35003119794419e-13 chips<1e-9. No reference
strategy enters learning; no learner was constructed in any cost run. The source-
bound software proof and ALLthree own/native costs are complete. Publish native
cost evidence before the fixed deep forecast and checked admission; real sampled
training remains unrun/unadmitted until those published gates pass.

### November 12 — unchanged conservative sampled forecast passes

Deep source-bound forecast authenticates/replays the full-stage prerequisite,
tiny proof, ALLthree own/native costs and ALL24historical complete B4 paths.
T=733.132027500s is the maximum fixed-worker sum of per-game maximum old10m
path times for all36new paths. O/N/P are the declared maximum complete costs.
Fixed4*(T+O+P)=3220.713439164s<7200 and4*(N+O+P)=489.940297996s<900.
Forecast complete command107.862500125s; no real trajectory was run. Publish
this forecast BEFORE checked admission. No changed factors/caps/seeds, no accuracy/
default/fresh/global admission. Full11100s user-deadline reserve still applies.

### November 12 — checked sampled study permission, publish before trajectory

Published forecast06e099e precedes admission. The admission command recomputes
source/proof/cost/history arithmetic and authenticates909sealed prerequisite files
and exact fetched-origin publication bytes. Complete command26.335615209s;
sampled_trajectory_admitted=True, actual_admission=False, fresh_global=False.
This permits only the frozen36-path known-game research study, not accuracy, a
stronger agent or default/fresh/global promotion. Publish the permit before
starting. The full11100s study/audit/report/final-CI/save reserve fits before
the user's10a.m.Pacific cutoff; parent/worker recheck permit/source before learning.

### November 12 — complete real sampled own grid; audit pending

Published permit486d29e precedes first new real trajectory. All36paths/36warm
origins/108raw states/216average books/324readouts complete, original3.11.17/
NumPy2.4.6/Numba0.68.1/source41b6. Complete command735.623852375s<7200;
raw-state/work/RNG/normalization/journal/pipe replay324 with zero metric change,
no retraining during replay. ALLcontrols/seeds/crossings retained. Initial OWN
primary-final values below are pending independent audit, not admission.
dev_low_oop/exact:median 2.02482310754e-09%pot,worst 2.07116552715e-07%pot; seeds 2.07116552715e-07,1.65007760542e-09,2.02482310754e-09.
dev_low_oop/public_b8:median 1.65003593779e-09%pot,worst 1.86390995916e-08%pot; seeds 1.86390995916e-08,1.65003593779e-09,1.64920477823e-09.
dev_low_oop/texture_b8:median 1.65003593779e-09%pot,worst 2.23571208186e-08%pot; seeds 2.23571208186e-08,1.65003593779e-09,1.64920477823e-09.
dev_low_oop/texture_made_b8:median 1.65003593779e-09%pot,worst 2.25363420655e-08%pot; seeds 2.25363420655e-08,1.65003593779e-09,1.64920477823e-09.
dev_low_oop/texture_range_q8_b8:median 1.65003593779e-09%pot,worst 2.25363420655e-08%pot; seeds 2.25363420655e-08,1.65003593779e-09,1.64920477823e-09.
dev_low_oop/texture_range_q8_own_q8_b8:median 1.65003593779e-09%pot,worst 2.26489280006e-08%pot; seeds 2.26489280006e-08,1.65003593779e-09,1.64920477823e-09.
dev_medium_oop/exact:median 0.292419682341%pot,worst 0.660690262712%pot; seeds 0.292419682341,0.660690262712,0.194613427468.
dev_medium_oop/public_b8:median 0.292419682341%pot,worst 0.660690262712%pot; seeds 0.292419682341,0.660690262712,0.194613427468.
dev_medium_oop/texture_b8:median 5.4085783262%pot,worst 7.79468119515%pot; seeds 5.4085783262,7.79468119515,5.23811949182.
dev_medium_oop/texture_made_b8:median 4.31913150937%pot,worst 4.46315286224%pot; seeds 4.31913150937,4.46315286224,4.29838415609.
dev_medium_oop/texture_range_q8_b8:median 2.79329180125%pot,worst 3.34947219867%pot; seeds 2.79329180125,0.375286609858,3.34947219867.
dev_medium_oop/texture_range_q8_own_q8_b8:median 2.38991200503%pot,worst 2.49456769971%pot; seeds 2.49456769971,1.22545973317,2.38991200503.
Candidate fails fixed medium median<=1%pot despite worst<=2.5%; do not change
limits/readout/seed grid. Exact passes. No default/fresh/global promotion. Publish
ALLown evidence before constructing the actual native reference. All-control
whole average coverage includes warm mass; report post-warm support separately.

### November 12 — actual sampled scalar audit passes; quality failure retained

ALLown9177081 was public before actual OpenSpiel construction. Native checks
all324policy values/BOTH-BR roots, maximum error 1.27897692436818e-13 chips<1e-9. Complete
command41.155461709s<900, pinned OpenSpiel2.0.2/Apache2 license verified; no
reference policy used in training. Numerical verification passes; the candidate
medium LINEAR median2.389912005%pot still misses the preset1%limit. Do not
change limits or select a different readout/seed. Publish audit before authenticated
report; full result tables/plot and failure explanation are next. Default/fresh/
global admission remain unchanged.

### November 12 — complete failed sampled report and readable figures

Authenticated report completes64.070273584s<900. All13 checks are evaluated:
accuracyFalse alone, allother12True. Compact medium LINEAR median2.389912005%
exceeds fixed1%; worst2.494567700%<2.5%cannot rescue it. Exact/rawpublic
median0.292419682%/worst0.660690263%; previous range-aware2.793291801%/
3.349472199%. Two paired candidate seeds improve and one worsens. All324readouts,
30signed baseline effects,12final primary rows, support/storage/work metadata and
all five false superiority-admission flags are retained. No reseed/readout switch,
more work, changed gate, default/fresh/global promotion or issue4closure.

Visually inspected original learning.png; its symlog view wastes negative-axis
space. Preserve original figure/result hashes. Add a separate data-only positive-
log renderer and learning-log.png/receipt using unchanged scalar input hashes,
all six descriptions and all three primary seeds. Original scientific source
fingerprint41b6f34d is unchanged; the new display script authenticates every named
historical dependency/Git blob without weakening the old aggregate checker.
Actual3.11/3.12data-only rendering produces identical PNG SHA
ff8df8887919b36d4b2853710a1da8851a6411c8c1e109ae31cb997d4837af9e;
this is NOT bit-exact real trajectory admission on3.12. Lint/format pass;
strict typing659files passes both versions. New method/README/journal101 clearly
state failure, seed dependence, warm-versus-postwarm coverage, exported-engine
limits and no whole-memory claim. Three interview Q&As and read-only terminal
commands included. Artifact digest/failure-flag/relative method-link checks pass.
Final publication base/hosted checks and solo self-review remain merge gates.
Next justified issue4 question: separate within-group learning weakness from
finer-information vulnerability with each saved opponent held fixed, before
choosing another training/representation remedy. Human minutes not recorded.

### November 12 — prospective compact fixed-opponent diagnosis

After complete PR56 failed accuracy, preregister a separate diagnostic before
new crossed/decomposition outcomes. All36saved final LINEAR S policies and12
same-representation full4096 F policies, allsix/two games/three seeds. Four
owner-row mixes SS/SF/FS/FF perpair:144logical profiles/288target conditions.
No new learning/RNG draws/default/feature/fresh/global stage. Test E=W+I and
fixed-opponent root/I invariance; retain all signed own EV effects and source
failures. Full archive/source/Git-blob compatibility without editing old checkers;
complete local/optional/hosted source checks and tiny same-pipeline software proof
before actual900s own/native diagnostic. Publish own before reference, preserve
partials, use pinned scalar-only Apache2reference. Full4800s downstream reserve
must fit the user's10a.m.Pacific cutoff. Method/config/journal102 published first;
no outcomes or remedy choice claimed. PR56 final publication checks still run.

### November 12 — fixed-opponent implementation and first correctness checks

Prospective62aa441/PR57 precedes implementation. Added original-source compatible
readers, ownership-bit-preserving SS/SF/FS/FF mixtures, immutable own reply/detail
archives, E=W+I and fixed-opponent root/information/EV identities, complete clocks/
cutoff guard, scalar-only native schema/replay and all-case reports. No training
entry point or fresh RNG draws. Current focused new/architecture69tests pass
20.92s; lint/format pass and strict typing672files passes. Includes literal
seven-node hidden-world nonzero-information/within gains and actual native check,
two-player Kuhn zero-support root invariance, complete mocked144details/288target
IO, corrupted/re-signed policies, missing/duplicate rows, partial retention,
fake native error/source/license fields and clock/source-check failure paths.
The published tiny-source adapter replays324sampled readouts/72full policies and
selects48sources with sampled/full/reference constructors blocked. These are
software tests, not new real diagnostic outcomes or a formal rehearsal count.
Selected OpenSpiel2.0.2 Apache2license was read earlier November12; its new pinned
environment copy matches cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30.
Original full/sampled source maps are verified as unchanged subsets/Git blobs;
no strict historical checker was edited. Complete exact-source base/optional/
hosted cohort and published-own144-profile software proof remain required before
real diagnosis. All original scientific caps/seeds and failed sampled gate stay.

PR56 final publication BOTHCI43202520424 and both immutable bases pass atccb0c82
before history mergea53bda02840bcb78c4027408fa3e91c3a69f21cf. Main guarded FF,
3.11.17/NumPy2.4.6/Numba0.68.1/module/fingerprint guard,97focused tests14.44s,
full108-state/36-warm/324-readout replay0 in17.648811s all pass. Fresh snapshot
and post-test checks preserve allten unrelated user bytes/status/index entries/
patches. Raw finalCI/head/log/local proofs retained outside repo; no CI-only
commit. Main-push repeat43204968981 is separately in progress. PR57 retargeted
from dependent branch to main. No stronger/default/fresh/global admission.


### November 12 — reject malformed native player identifiers before diagnosis

Self-review after implementation2852bef found that Python equality allowed
False/0.0 and True/1.0 as native player identifiers. Four explicit regression
cases failed as expected before the fix; their raw log is retained under
results/compact-fixed-opponents/implementation-regressions. Require actual int
IDs0/1 before accepting scalar receipts. This tightens the new diagnostic only;
no historical dependency/config/seed/cap/gate changed and no diagnostic outcomes
were collected. Corrected focused suite73passes24.53s; Ruff/format/type672pass.
Initial optional443passes77.40s (3.11),442passes/1runtime-specificskip75.79s
(3.12) belong to the superseded source, not permission for corrected code.
A new complete source-bound local/optional/hosted cohort is required next.
Method prose spacing and journal status are clarified without changing design.
Installed OpenSpiel2.0.2 Apache2license reread in full; pinned digest unchanged.


### November 12 — corrected fixed-opponent source checks pass before rehearsal

Immutable sourcec6c384b, fingerprint2670f3f6, passes all six required roles.
Full local bases3152passed/63skipped/149deselected each,604.24s (3.11) and585.21s
(3.12); Ruff/802formattedfiles/strict typing672files/hooks pass. Focused locked
ALL-EXTRAS447passes94.81s on3.11;446passes/1recorded-runtime-specificskip94.02s
on3.12. BOTH exact-head hosted43207761909 jobs131147296682/131147296281 pass.
Raw decoded logs, full GitHub head/job metadata, install logs, local receipts and
wrapper retained with the six-role bound checks.json; gate validates its digest.
The superseded initial bases3148passeseach and443/442optional remain locally
retained, not substituted for the corrected cohort. One failed worktree setup
attempt (missing sandbox write access to shared Git metadata) ran no tests or
experiment and was retained separately before successful isolated setup.

Prospective seeds/complete caps/144logical/288target grid and failed sampled
accuracy gate stay unchanged. No new poker diagnostic outcomes have been
collected. Next is the actual checked-source tiny own rehearsal, publication,
then scalar comparison; only its published complete proof admits real diagnosis.


### November 12 — tiny own fixed-opponent rehearsal before reference

Checked-source no-training tiny run completes all144joint profiles/288target
responses and144fixed-opponent identities using48published own final inputs.
All original324sampled readouts/72full policies replay before selection; every
new detail/reply profile replays exactly. Complete own clock 2.4802082079986576s <180s.
No native constructed, no new training or poker strength claim; all144details
and parent/child receipts are published here BEFORE native construction.
Raw hosted logs retain original trailing whitespace/BOM; code/docs diff checks
exclude those authenticated verbatim receipts rather than editing their bytes.


### November 12 — complete tiny scalar proof before real frozen diagnosis

Tiny own144profiles/288responses were public atdb348c9 BEFORE scalar-reference
construction. Native144comparisons/all288responses pass with maximum error
2.0816681711721685e-16chips; complete native command5.406218207997881s <180s.
Own complete2.4802082079986576s. No new training or poker admission; positive
information-gap branch is additionally covered by the actual independent seven-
node fixture test, not inferred from one-to-one Kuhn aliases. Published complete
source-bound software proof now permits only the frozen real diagnostic, within
its original900/900/900s caps and full4800s cutoff reserve. Prior sampled accuracy
failure stays failed. This is no new Holdem trajectory study.


### November 12 — publish all real frozen-own diagnosis before reference

Complete no-training real own command 123.74255779099985s <900s; all144joint
profiles/288responses and144fixed-opponent identities replay. Maximum identity
error 0.0chips. SS/FF reproduce the original
primary source metrics; original108sampled states/324readouts and72full snapshots
replayed before selecting48sources. All raw144mixture/reply details plus own/child
manifest are public in this checkpoint BEFORE reference construction. No new
learning/RNG draws/default/admission. Original sampled accuracy remains failed.
Independent scalar validation/report are pending; no remedy selected yet.


### November 12 — all frozen-opponent scalar comparisons pass

All144real joint profiles/288player responses independently checked after own
publicationcc53a93. Complete native clock 105.58452487500108s <900s; maximum
raw scalar/root/achieved-reply/metric agreement error 1.0658141036401503e-13 chips <1e-9.
Both exact/restricted roots and achieved OWN exact/restricted/river-before replies
are covered, not aggregate exploitability alone. Pinned OpenSpiel2.0.2 license
verified; no reference policies returned/used for training. Fixed source2670f3f6
and all historical source maps remain unchanged. Report is next; no new training,
remedy choice, default/fresh/global or failed-gate change.


### November 12 — complete frozen-opponent diagnosis, retained negative result

Authenticated report completes88.63809604199923s <900s, all144profile CSV rows,
288target rows,144fixed-opponent EV conditions and both visually inspected
figures. Original accuracy gate stays FAILED. Harder compact SS mean E2.036646479%
pot =W0.117109360% +I1.919537119%; I/E94.24989258%. This is descriptive mean,
not the prior median2.389912005% acceptance statistic. Responding seat1 versus
sampled seat0 has I[1.6890740885925197,.8186241819688647,1.6260200483283072]
chips by fixed seed; versus full seat0 it has I[0,0,0]. Every I/root stays exactly
invariant to changing only the target's S/F policy. Full-control self play hides
a weakness exposed by sampled own opponents; no universal abstraction floor or
pure causal sampling/training remedy follows. Within-group gain is small in all
three compact medium seeds. No feature selected/trained/default promoted.

Every signed own-S-to-F EV effect retained:74 below-1e-9chips,72 in near-zero low
game and two medium texture/category cases. All six representations, both games,
all three seeds and four mixtures remain. Figures distinguish their legends,
show panel scales and retain negative effects; min/max is not confidence.
README/method/three interview Q&As and rewritten plain-English journal102 explain
the result, source/runtime, dependent full aliases and shared exported-engine
limits. Artifact hashes,144/288/144CSV counts, unchanged scientific source2670,
and all relative README/method/journal file links pass. Codex-assisted solo review
notes retained outside repo. Final local base/hosted publication checks remain
before history merge; no new trace/probe outcomes or new trajectory study started.
Next justified separate step: identify the concrete merged decisions behind the
large information benefit while holding frozen opponents fixed.

### November 12 — prospective trace of the audited information benefit

Before new row/conflict outcomes, pin PR57's complete 48-input/144-profile/288-
response archives and define 144 unique fixed-opponent traces with all288alias
provenance. Unchanged own trace_losses starts at the saved partition-best reply,
so all additive rows must sum to already-audited B-R. Prefix is restricted-reply
reach, not original sampled reach; turn contributions do not causally identify
a river feature. All six/two games/three seeds/both players/S-F opponents retained.
No new learner/RNG/reference constructor, feature probe/selection/admission.
Prospective software180s and realown/report900s complete caps, full3900s cutoff
reserve, own-before-rendering checkpoints and complete source/test/hosted gates.
Historical source/checkers stay unchanged; new sealed-source reader authenticates
named old dependencies/Git blobs and raw own policies. No new trace outcomes yet.
PR57 final publication local/hosted checks are still running; branch is stacked
on its published4c5ba3c, to retarget main after checked history merge.

### November 12 — information-trace implementation and first correctness checks

Prospectiveca983341/PR58 precedes all new row outcomes. Implemented a sealed
parent reader that authenticates unchanged source2670named files/Git blobs and
replays all parent mixtures; old strict aggregate checkers are not edited or
patched. Added restricted-best-reply-prefix trace panels, 288alias binding,
all-row/group/street accounting, exact tie-set conflict rules, complete clocks,
immutable/partial retention and all-case tables/terminal browser. Reusable
receipt and no-training execution helpers reduce duplicated experiment plumbing.
A fresh-process import blocker refuses every reference backend and patches all
learner factories; there is no new native construction. Parent B/R scalar
comparisons remain comparison-only, and new individual-row values are labeled
own calculations rather than independently audited new values.

Current67focused tests pass13.34s, including positive hand-calculated hidden-
world sums for BOTHplayers, zero-support retention, overlapping action ties,
wrong aliases/context/root identifiers, complete mocked144panel/288alias IO,
corrupt/re-signed details, partial/report timeouts, cache/terminal navigation,
clock failures and six-role receipt failures. Recorded tiny parent144profiles/
288responses also replay with learner/reference constructors blocked; this is
parent replay, not the new source-bound trace proof. Initial fixture-sharing
import-path error was caught/fixed before this passing suite, with logs retained
outside the repo. Ruff/817formattedfiles/strict typing686files pass. No new real
trace outcome, probe, learned feature, training/default/admission exists yet.
Next: full exact-source local/optional/hosted cohort, then published tiny trace
proof before any900s real trace under unchanged3900s cutoff reserve.

PR57 final local bases3152/63skip/149deselect pass576.41/562.89s; BOTH exact-head
hosted43211159496 pass before history merge9737b7acbde53f1fdbc48b46850fcd7d6760020c.
Hosted311894.65s and3121113.89s, same3152/63/149/one historical warning. Full
head/log/digest/local proof retained outside repo to avoid a CI-only commit.
Fresh main snapshot/guardedFF preserve allten unrelated bytes/status/changed-index
entries/patches; main source/runtime guard and73focused tests21.01s pass. Complete
main archive replay is running separately. PR58 retargeted main after the merge.

### November 12 — complete exact-source trace checks before rehearsal

Source219f338/fingerprint3b5b9878 passes all six roles. BOTH complete localbases
3217passed/64skipped/149deselected in581.29s311/564.74s312; Ruff817format/strict
mypy686/hooks pass. Relevant locked optional513passed90.58s311;511passed with
2recorded-runtime adapter skips86.94s312. BOTH exact-head source-hosted43214557237
pass:311job131170497572808.46s,312job1311704978961138.64s, same3217/64/149 plus
one historical warning. Raw decoded logs/head/job metadata/install receipts and
wrapper retained; six-rolechecks.jsonsha0f5214fa7157c3ec6f5d7d93dff020832c42196804904441939c7110715b7530
validates before publication. Authenticated raw logs retain their whitespace/BOM.
Scientific source/caps/seeds/config unchanged. Prose clarifies target=attacker,
fixed opponent=defender; largeI does not itself select a card-feature remedy.
No new row outcomes yet. Actual tiny trace proof is next, before real tracing.

PR57 main full144/288 archive replay completes75.40927466599896s with zero
fixed-opponent identity error; allten unrelated main bytes/status/changed-index
entries and patches remain exact after checks/replay. Receipt/post-preservation
proof retained outside repo. New trace code does not alter any historical SRC.


### November 12 — complete tiny information-trace proof before real rows

Actual checked-source same-pipeline tiny run completes144panels/288aliases/864
ownedrows, all raw details and summaries replayed, maximum accounting/root error
3.469446951953614e-17chips. Complete command 2.169484458001534s <180s.
Learner factories and every reference import blocked; no new toy training,
reference construction or poker-strength result. One-to-one aliases are zero-
information software cases; separate literal hidden-world tests cover positiveI
for both players and overlapping ties. Full own/child/144details are published
here before real tracing. No scientific caps/seeds/gates/admission changed.


### November 12 — publish complete real information trace before report

No-training own trace completes 117.1815822919998s <900s. All144fixed-opponent
panels/288sourcealiases/133632owned decision rows replay, maximum accounting/
root error 1.0658141036401503e-13 chips <1e-9. All raw row/menu/R-prefix
reach/conditional-value/group/street/alias detail files plus own/child manifests
are published here BEFORE report rendering. Complete source/prospective/tiny
proof gates precede this collection; old B/R scalar audit is reused only as
a comparison receipt. No new learner/RNG/reference construction, independent
row-value audit, feature selection or model/default/accuracy admission. Report
and concrete interpretation are next; original sampled gate remains failed.


### November 12 — complete decision trace and actual terminal inspection

Authenticated report98.93773416600015s <900s follows published ownf4824b2; all
144panels/288aliases/133632ownedrows/84600grouprows retained and replayed. Hashes,
CSV counts, source3b5b9878 and relative doc links pass. Actual browser n/p/j/k/q
navigation passes; allthree default compact target1-versus-S seeds, fullopponent,
rank2riverconflict and opposite-seat rivercase inspected. No new native solver
or training runs. Prior B/R comparison receipts remain comparison-only; new
individual conditional row values are own calculations.

Allthree medium compact seeds concentrate nearly all target1I at exactturnrow
1611/coarserow873, own9c9d onTs9s4d2h. This group hasONEexact member and no strict
current conflict. R folds, finer-suffix B calls: callvalues[-12.9751262,
-15.5716222,-13.3752332] versusfold-18; contributions[1.68900823229,
.818596892079,1.62600876064]chips versus totalI[1.68907408859,.818624181969,
1.62602004833]. Negativecall stillbeatsfold, but Q assumesfinerfutureplay R
cannotuse. ReachisRprefix,notoriginalsampled. R-prefixstrictreachable groups
3/4/7remain; riverlosses.000065856301/.0000272898904/.0000112876885chips are
smallbecauseearlierfoldssuppressreach. This is not causal turn-local feature
attribution or universal advice. Target1attacksfixedseat0S; itisnotnecessarily
theweakdefender. SamepanelsversusFhaveI0allseeds.

README/method/3interviewQ&As and rewritten plain-English journal103 explain all
roles/units and provide the actual browser commands. No personalpractice/hours
inferred from Codex's checks. No feature selected or agent promoted; original
compact sampled accuracy remains failed. Next justified separate test is finer
OWN opponents for the unchanged compact learner, with paired coarse/fixed-work
controls and all original seeds/caps/gates, not an assumed fix. Final applicable
local base/hosted checks and solo self-review remain before history merge.

### November 12 — prospective compact finer-own-opponent comparison

After the complete PR58 trace, register a matched-work training remedy before
new trajectories/outcomes. Keep the compact learner fixed; compare ordinary
compact, paired compact, mixed compact/fine own opponents and ordinary fine.
Preserve old five-path/30actual-path/108boundary/432profile/1152fixed-target design,
three seeds, scalar/role1PCG64 streams, 100k/1m/10m total-work labels, exact2N
initialization, both-player charges and ALLoriginal strict quality gates. In
particular low-game zero improvement stillfails strict superiority; no rescue.
All36 ordinary compact/exact B4 barriers bind the original compact-sampled raw
states; original8own full controls/game remain comparison-only and are expanded
from their original parent encoding, not loaded into the learner.

New pinned design/cost contracts require complete source/local/optional/hosted
checks, actual full432/1152tiny shared180s proof, all3own-cost publications before
ANYnativecost, all3nativecosts, unchanged conservative24path historical forecast,
and checked published admission before any7200s real study. Own/native/report
caps7200/900/900 unchanged; full11100s reserve means no current-window study start
after6:55Pacific. Costs are explicitly nontraining refinement/density projections,
not original-prefix or strength evidence. No new trajectory/feature/default/
fresh/global admission exists. PR58 final publication checks are still running;
this separate draft is stacked on its published9f2e122 before implementation.

### November 12 — merged trace, preserved main, compact training adapters

PR58 history-merged511ae2f after final local bases3217passed/64skipped/149deselected
each603.868004/591.673235s and both exact-head hosted43220163404 jobs passed on
9f2e122. Raw final logs/head metadata/digests retained outside the repo to avoid
a CI-only source cycle. Fresh snapshot20261112T130215Z, guarded main FF and
post-test checks preserve all10 unrelated result bytes/status/changed-index
entries/patches. Main3.11.17/NumPy2.4.6/module/source guard,138focused tests34.39s,
full144/288trace replay and both saved browser cases pass. No new learning.

PR59 is retargeted to main. New separately bound adapters reuse unchanged
capture/normalization/composition/scoring/archive/replay/reference-scalar math.
Compact contexts refine original coarse groups (130/1770rows; mixed254/252 and
2544/2562 versus fine376/3336). Training imports no saved-policy loader or
reference backend; exact structural payload schema rejects policy injection.
Read-only source/cost/replay parents block all learner and native constructors.
All36 original compact/exact raw checkpoints decode; literal old readout hashes
are reconstructed without a learner. Cost density projection preserves exact
new uniform warm origin and normalized old probabilities, records old/new
hashes/IDs/work and never claims new learned books.

Full tiny three-worker child/archive/replay tests cover432unique profiles and
1152fixed conditions; direct terminal equations/exhaustive pure choices check
all432values/BRs and positive information gaps. Command caps, shared software
clock, cutoff reserve, partial event/unknown-state retention, missing checks/
permit rejection and persisted seal/cap/input mutations are tested. Allthree
own cost publications are required before ANYnativecost; every recorded witness
field and raw scalar/derived error schema is checked. Native schema tests use
already-public old data or explicit unit fixtures, not a new reference run on
unpublished policies. Source/180projection integration passed89.01s with solver
constructors blocked; this is not a fixed cost repetition or timing forecast.
Full exact-source base/optional/hosted checks and formal software/cost/forecast/
admission still precede new real training. All old scientific source/data and
preregistered seeds/caps/strict gates remain unchanged. Codex-assisted work;
human practice/time not inferred.

Draft implementation verification:100new fast checks pass18.98s, one slow
source/180projection integration check passes separately89.01s; shared backend
integration group175passes/1slow deselected before the final seven witness-field
cases. Whole-repo Ruff/format840files and strict mypy708files pass. Earlier
iteration fixture naming/path mistakes were corrected before source publication;
no formal source-bound scientific collection has started. Full immutable base/
optional and both hosted checks remain next, not inferred from focused passes.

Before formal source checks, identified optional-test process contamination:
other native test modules import pyspiel at collection. Keep production fresh-
process guards unchanged. The real own-child and historical-source integration
tests now use fresh subprocesses; wholly mocked interruption fixtures isolate
only their fake parent boundary. The guarded three-worker child plus optional
native-module collection regression passes18checks3.93s; strict typing passes.
Scientific source fingerprintd6da7eeb is unchanged; corrected test head still
needs the complete exact-head check cohort before formal evidence collection.

The157bd40 optional311 cohort passes634tests; optional312 reports633passed/1failed.
Retained raw optional312 log/receipt, exact reproduction and executed check driver
under results/compact-own-opponent-learning/implementation-regressions/runtime-matrix-157bd40.
The test incorrectly expected real original-runtime source replay under3.12;
unchanged compact_full_run.check_runtime correctly raises own/native/replay
runtime changed. Correct only the test expectation: full36/180 integration on
recorded3.11.17/NumPy2.4.6; expected real-runtime rejection on3.12, whose structural/
software/raw-data checks remain. Targeted312guard regression passes39.82s.
No scientific source, seeds/caps/tolerances/quality gates changed, no formal new
collection/training yet. A complete corrected exact-head cohort is still required.

Reread the full installed OpenSpiel2.0.2 Apache2.0 license in the new active311
environment, SHA cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30;
comparison-only reference, no source copied into the own learning core.

Before any formal cost repetition, self-review found that independently lifting
old average probabilities and raw density books can disagree by one floating
bit, despite satisfying the1e-12 old-probability cost tolerance. Synthetic fixed
density fixtures on the two structural layouts reproduce30/185 probability-bit
differences, maximum1.1102230246251565e-16; these are NOT learned policy results.
Keep the old exact replay check unchanged. Lift each book once and derive its
cost average by exact normalization of that book; record both original members
and before/after hashes. Current/fine tables stay as declared. Two new real-layout
fixture checks pass with all18foundation tests18.25s; complete36boundary/180table
source integration, now also checking all36coarse book-average pairs exactly,
passes100.88s. No original scientific dependency or training rule was edited.
This draft-source correction requires a new full exact-source cohort before
formal software/cost/forecast/admission or real study. Earlier check cohorts
remain separate and cannot admit the corrected source.

### November 12 — complete source-bound compact opponent cohort

Source1b6ccc8ca928ddc1ce2a6abd6072ee48d54df152 / scientific fingerprint
2ace916f0812efd1d93d0f16f533a9ecab15deceda482e94553df9a158d6a989 passes ALL
six roles before formal software/cost/learning. Immutable full base311/312:
3319passed/64skipped/150 deselected each; complete checks669.730447/651.925671s,
including lint/format/strict types/tests/hooks and source/runtime/module guards.
Relevant all-extras636each, complete checks350.804740/288.604327s; original-runtime
full36/180 integration311, expected real-runtime rejection312 and structural/
raw-data/software checks both. Both exact-head hosted43228827703 jobs pass:
131218952181/131218954870, same3319/64/150 with one historical warning each,
pytest670.28/1190.68s. Raw decoded UTF8 logs, API head/job metadata, executeddriver
and typed six-role checks retained, receipt SHA
0a6e3bb645a2a3dff9a303a895cc0623c21c3a2e18b502e54a68fdc856cc233f verified.
This source-check publication is not compute or strength admission. Formal full
tiny own/public-before-native proof is next; no new real trajectory yet. Method's
three interview questions explain paired controls, future-suffix interpretation
and what a software/compute gate does and does not establish.

### November 12 — full new software proof; own cost repetition0

Formal software-own15.292187916005787s publishes37ca53d734a50386a37ea6d04a7c2e070e627aa1
BEFORE native5.612813625004492s publishes0ec17ef91f01a06169b1cd6d3378d7d654d66323.
Whole shared proof47.27623416600545s<180, source2ace916f; same3spawn learning path,
all30initializations/108boundaries/324raw policies/216ledgers/108compositions/
432unique scores/1152fixed conditions. All432/1152 independent scalar and derived
field checks pass, maximum1.1102230246251565e-16 FICTIONAL payoffunits; no native
actions exported or reference output used in learning. Checked published software
gate reports complete_tiny_software_only_not_poker_admission. Actual toy learning
ran; no new Hold'em trajectory. Raw reports/events/archives and both own/native
complete-command bodies retained. Raw hosted log whitespace is preserved so
the recorded hashes remain exact.

Fixed cost-own repetition0 completes308.32340462499997s<900 including full historical
source/context loading, all30data-only paths, raw/composed archives,432scorings,
1152fixed conditions, complete replay and all required reports. Cost scope is
explicit; no new poker/toy learning, initialization or native construction.
No code, seed, gate or environment tuning between fixed repetitions. Publish
this complete own outcome before the next own repetition; allthree own costs
must precede ANY nativecost. Remaining two own/three native repetitions, complete
maxima-based forecast and checked published permit are still required. A cost
curve is not a newly trained agent or a playing-strength result.

### November 12 — all three own costs complete before native costs

Own cost repetitions0/1/2 complete308.32340462499997/309.2752516670007/
305.3145045409983s, each<900. All432unique/324raw policies/216books/30warms/
108compositions/216logical/1152fixed conditions replay with maximumchip/unitless
error0 and policy/ledger bytes exact. All actual poker/toy work0, initialized
trainingpaths0, learner/native constructionFalse. D=max309.2752516670007s; the
remaining full forecast still needs all three independent cost commands.
Six report files (twoCSVs/summary/threePNGs) are byte-identical across allthree
repetitions. Allthree repetition0plots visually inspected; cost-only/zero-new-
learning titles readable, all seeds/readouts retained. Coincident paired/control
curves are a consequence of old table reuse, not a new training result.
Own0 published01517bf, own1 published7e8d493; this own2 publication completes the
required all-own checkpoint BEFORE ANY nativecost construction. No changed
code/seed/cap/gate/environment setting between repetitions; no favorable subset.
Native0/1/2 full432/1152 scalar audits, complete forecast and checked published
permit remain before a real study; full11100s reserve and10a.m.cutoff unchanged.


### November 12 — compact training remedy denied compute admission


**Compute admission fails; no new compact/finer-opponent trajectory was run.**
The complete fictional software proof passed all 432 profiles / 1,152 conditions
within 47.276234 seconds shared, and all required source checks passed before
collection. All three own costs were published before any independent cost.
Every fixed cost completed under its 900-second command cap, with exact own
policy/book replay and all 432 / 1,152 independent scalar checks passing.

| Fixed repetition | Complete own seconds | Complete independent seconds | Largest independent error (chips) |
|---|---:|---:|---:|
| 0 | 308.323405 | 533.671665 | 1.84741e-13 |
| 1 | 309.275252 | 545.105072 | 1.84741e-13 |
| 2 | 305.314505 | 544.434855 | 1.84741e-13 |

The complete [forecast](../results/compact-own-opponent-learning/forecast.json)
replays all three own archives and validates every independent raw worker,
publication witness, complete clock and source/input seal. It takes
655.200384 seconds under 900. From all 24 original timing
paths, T=610.943356249918; D=309.275251667001; N=545.105072250000 seconds. The unchanged
own forecast 2*(2*T+D+600)=4262.323928<7200 passes. The unchanged
independent forecast 2*(N+60)=1210.210145<900 is **false**.
A command fitting its individual cap is insufficient for the conservative
admission forecast. No favorable repetition is discarded and no gate/cap is
changed. These are wall times on the recorded workstation, with routine light
administrative work during collection, not exclusive-machine speed benchmarks.

No study permit is created, no new real learning starts, and the failed compact
sampled accuracy result remains. The paired/treatment cost curves reuse old
OWN tables by construction; they never measure the proposed training remedy.
The next separate [profiling milestone](https://github.com/jimmy-sim/poker-ai/pull/60)
measures a full replay before selecting any lossless optimization. An optimized
source must earn its own checks, fixed costs and admission; this result cannot
be rescued by profiler timings. No default/fresh/global or stronger-agent claim.

Final same-source review passes102focused fast checks (one slow integration deselected),20.70s. All362named scientific dependencies match the original fully checked source. The earlier complete local bases (3,319passes/64skips/150deselections each), optional636each and both source-bound hosted checks remain valid; the new complete archive/cost/forecast evidence is retained. Final PR-head hosted CI is required before merge.

## November 12, 2026 — prospect: complete compact replay profiling

The first published independent cost needs 533.671665 seconds; the fixed native admission formula requires the maximum of all three costs below390. Remaining repetitions and the original complete forecast remain required in PR#59. The separate [profiling protocol](compact-replay-profile.md) fixes plain then instrumented full replay of cost archive0, unchanged original source/guards,900s per child and complete raw function/caller evidence. No profile outcome or optimization exists yet. Codex-assisted planning; no personal time or understanding inferred. Refs#4.

The standalone profiling tool now passes56focused checks, including an actual full432-profile tiny replay with exact plain/profile identity, raw caller accounting, blocked construction, changed-source/input rejection, corrupt viewer evidence and retained hard timeouts/failures. Lint/format and strict typing pass. Both complete local bases and source-bound hosted checks remain required before a formal poker-archive profile. This is software evidence only; no new poker learning or runtime result.

Viewer self-review also binds every named historical scientific file and Git blob before presenting timings. It accepts unrelated source additions without weakening the original runner aggregate.57focused checks now pass (10.82s), including this provenance check; no formal profile has run.

GitHub then caught a checkout-history issue: Python3.11 reports3,350passes and two provenance-test failures because its default shallow checkout lacks the archived source commits. Both full local suites had3,352passes/64skips/150deselections; optional112each. We retain the failed hosted log, exact head/job metadata and local receipts. CI now fetches full history. A new local shallow-clone fixture proves the checker refuses missing history and passes after fetching it; no source checker is relaxed.58focused checks pass9.51s. A fresh same-head local/optional/hosted cohort is required before formal profiling. The original forecast and scientific source are unchanged.

Self-review before formal profiling caught a verification gap: the frozen reader checks recomputed values, then returns its stored input receipt. Comparing that object alone would compare stored diagnostics rather than directly compare both recomputations. The new observer records the return from exactly one call to the unchanged replay function. Both complete stored receipt and actual computed summary must match across modes; original arithmetic/guards remain. Synthetic tests reject missing/duplicate summaries and detect a1e-16 computed change despite identical stored inputs.61focused tests pass11.42s, including a real full432-profile tiny replay with actual summaries equal. Actual runtime/hardware and OS-reported reaped-child CPU are now recorded. Old full local3353/optional113 and successful hosted3.11 remain retained evidence for the earlier source, not admission for this changed entrypoint. Fresh required same-head checks follow; no formal poker profile or new learning has run.


### November 12 — complete observed-summary profiler source cohort

Frozen c349b4f2f86f8aefc88ccee5067f8f501bbed87d / fingerprint
ce6cf85ca3b2333a2f001406c737fc3f7cd9bb1548cb736e58bf51c9b71b9851
passes BOTH full local bases (3,356/64skip/150 deselected), BOTH relevant optional
suites (116each), and BOTH exact-head hosted43246354825 jobs BEFORE formal
profiling. All six raw logs, head/job metadata, guards and observed receipts
validate and are published with this checkpoint. Earlier source cohorts do not
admit this corrected observer. Late cancelled/superseded old logs and final
metadata are retained separately without overwriting initial snapshots.

PR59 history-merged d14a3ca after final hosted43243962216 both passed at9d2464d.
Actual main imports correct runtime/source,102fast checks pass18.92s, and a full
COST0 reader executes all original math gates; combined208.409087s. Ten unrelated
user modifications remain byte/status/index/patch identical. PR60 retargets main.
No formal profiler data yet, no new learning or admitted training remedy.


### November 12 — full replay profile, exact core identity and partial OS capture


**Core replay identity passes; expanded outer OS resource recording is partial.**
The complete plain and instrumented children return 0 in 188.008402s and
289.352565s, each under 900. Their exact pair identity passes in477.363457s
under 1,800. Both actual recomputed summaries and full stored receipt hashes
match: 324 raw policies,216 books,30 warm origins,108 compositions,216 logical profiles,
432 unique scored profiles and 1,152fixed conditions; zero chip/unitless error and
exact policy/book bytes. No learner/reference construction or new admission.

All 2,017 raw function entries and 4,722 caller edges are retained, alongside the
supplemental binary profile, actual runtime/hardware, per-child OS-reported
CPU and command/metadata/raw logs. [Manifest and limits](../results/compact-replay-profile/profile/manifest.json)
record every byte. The timed process uses Python3.11.17/NumPy2.4.6 on the recorded
arm64 macOS 27.2.1 workstation with 10 logical CPUs; exact CPU-model query is
unavailable and is recorded as such.

The outer `/usr/bin/time -lp` wrapper returns 1 because macOS denies
`sysctl kern.clockrate`. Both child return codes and the pair's numerical/cap
checks pass. The wrapper's raw failure is retained, with available wall/user/sys
values; expanded memory/resource counters are unavailable. No rerun replaces
this outcome. This is not a claim of successful full OS resource capture or
memory savings.

The largest exclusive Python cost is `require_recall`: 2,832 calls,
44.089108s exclusive and 75.244400 s inclusive.
The entire profiled reader takes 287.884152 s; exclusive recall
work is 15.31% of that profiled time.
Inclusive recall work is 26.14%,
but overlaps the source-loading/scoring paths below and must not be added again.

| Caller of the recall check | Calls | Inclusive recall seconds |
|---|---:|---:|
| `response_profile` | 1760 | 49.616282 |
| `river_switches` | 864 | 20.584490 |
| `ScoringContext.__post_init__` | 200 | 4.818562 |
| `build_view` | 8 | 0.225066 |

The source loader takes 159.793191inclusive seconds and the subsequent full
archive replay 124.663812. These component totals include other functions and
are not independent exclusive budgets. Scoring and nested replay calls also
overlap. All raw data remains available beyond the viewer's top 12 display rows.
The one ordered pair measures instrumentation under these conditions; it is
not a population speed estimate, a new fixed-cost repetition or new poker play.

The next question is whether an already proven equal-depth/perfect-recall
property can be reused when the exact fields that define it stay unchanged.
A candidate must detect structural mutations, preserve all rejection cases and
match the complete original replay. It must not remove validation, touch the
historical checker or claim that this profile rescues the failed 2ace forecast.
Any cache needs its own prospective protocol, source checks and controlled
comparison before a performance claim or production integration.

Browse the authenticated retained evidence:

```sh
.venv/bin/python scripts/profile_compact_replay.py --show results/compact-replay-profile/profile
```


### November12 — prospective recall-proof cache comparison

The full profile points to repeated recall checks. The [prospective cache plan](recall-proof-cache.md) tests a content-hash certificate: if the exact checked fields change, run the original checker again; never cache a failed check. A fixed uncached/cached whole-archive pair must preserve actual replay results and all policy/book bytes. No implementation or cache speed result exists yet. Required source checks come before timing; if the full caps/CI/save reserve do not fit by10a.m., stop at tested source. The current model and failed admission remain unchanged. Codex assists; personal time or mastery is not inferred.

The mutation-aware prototype now passes31focused checks, including every structural input, failed proofs not cached, mutation during validation, restored structures, unsupported-input fallback, hook restoration, late-start refusal and exact actual/stored results for all432tiny scored profiles. Lint/format and strict typing pass. Four explicit read-only hooks count every request and restore on exit. All original files/arithmetic remain unchanged; fresh full local/optional/hosted source checks are required before the fixed whole-cost pair. No cache timing result, production integration or new training yet.


### November 12 — checked recall-cache source before timing

PR61 frozen79354f8a665c1d137c58bf8974f7327ae92e9807,367-file fingerprint
cc9840128fe313a3a564131055d169d00f7cad079e7c8e7ca59890245c922352,
now has all six observed source-bound check roles. Both complete local bases
pass3,387/64skip/150deselect (478.56/456.30s), optional147each (16.28/15.55s),
and both hosted43257152055 jobs pass3,387/64/150 plus historical warning
(888.98/1,200.64s). Exact raw logs/head/job metadata/check drivers retained;
source-only receipts precede the one registered full-cost pair. PR retargeted
main after dependencyPR60merged and sourceCIcompleted. Journal106 now explains
content fingerprints, mutation limits and what software identity would prove.
Original362-file2ace and364-filece6 dependencies remain unchanged/public;
no timedcache outcome, integration, admission or poker learning yet.


### November 12 — complete recall-cache pair, exact results

After allsix source roles were public37dcf58, the single registered pair starts
8:41a.m.Pacific (before8:55latest). Uncached188.27628845899744s, cached
138.15393783400214s; both return0 under900each, shared326.43247416600207<1,800.
All432/1,152 actual AND stored summaries exact, numerical errors0, policy/book
bytes exact; full324raw/216books/30warms/108compositions retained. Both2,832
requests; original traversals2,832→18, successful reuses0→2,814, no fallback or
rejection on valid archive. Source367/config/inventory/source-publication and
whole-child CPU/wall/command/environment are bound in retained raw manifests;
original ignored bytes copied exactly before verification. No expanded macOS
resource query repeated; no memoryclaim. Conditional ordered-pair wall reduction
26.621701030563326%, not population or full-native-audit speed estimate. All
unfavorable historical outcomes including old1,210.21>900admission remain;
no production integration/permit/new poker training. README/method/3QAs/journal106
explain exact outcomes and limits. Final relevant checks and both final-head
hostedCI remain before merge. Stop10a.m.; no further automation/subagents.

Final same-source relevant suites pass147each:16.16s onPython3.11 and15.91s
onPython3.12. All367named scientific files unchanged; complete raw pair hashes
and recomputed/stored identity rechecked by the retained own reader.
Lint/format/hooks pass. Final publication hosted checks required before merge.

### November 13 — resume issue4; prospective cached pipeline

User authorizes this night's work through9a.m.Pacific. Actual main455e6e9 and
allten unrelated modified result files inspected and freshly snapshotted before
isolated research/compact-cached-pipeline. The prospective integration plan fixes
effective source/counters in every process, complete original proof/cost/audit/
forecast/admission and unchanged scientific gates before any new learning.
No prototype timing rescues old1,210.21>900failure. No implementation or new cost
outcomes yet. Latest real-study start5:55a.m. preserves original11,100s reserve;
no future automation/subagents. Codex-assisted, human time not recorded.


### November 13 — cached pipeline implementation/correctness foundation

New opt-in scripts/compact_cached family reuses original capture/replay/scoring/
context/projection/native math and preserves every historical src/entry/config
byte. Its380-file effective source includes every private module, entry and
registration plus all367historical cache dependencies. New own/native/worker
records require implementation config and strict actual cache counters; missing,
disabled, malformed and cross-family records/permits are rejected. Whole clocks,
original180/900/7200caps, fixed formulas and all-three-own-before-native gates
are preserved. Read-only new-family metadata uses actual COST/REAL/TOY scope and
actual recomputed summary, with stored summary separate; legacy entry unchanged.

Focused adapter47+original cache31 checks pass on the current source. Complete
new spawned30-path/432-score tiny unit data agree with direct terminal sums and
exhaustive pure replies; all324policy/216book/30warm vector contents match the
old uncached proof, while source-bearing metadata intentionally differs. These
are mocked-gate UNIT checks, not formal checked-source proof/admission. Lint,
format and full-project strict typing pass. Full fresh local bases/optional and
both exact-head hosted checks are next before formal collection.

Local setup found an inherited macOS UF_HIDDEN flag on the isolated editable
.pth file, which Python correctly skipped. Clearing ONLY that local environment
flag restored imports; interpreter/scientific source stayed unchanged. A draft
subprocess-test import indentation issue and missing explicit unit own-path were
fixed before formal collection; early private logs retained outside repo. No
scientific outcome or favorable timing retry involved. OpenSpiel2.0.2 full
installed Apache license reread/recorded Nov13 before any new reference use.
Codex-assisted; human time/mastery not inferred. Stop9a.m.Pacific, latest real
study5:55 under the unchanged11,100s reserve; no subagents/future automation.


Premeasurement review strengthened the baseline-equivalence requirement: the
first379-file implementation checked old vector agreement in UNIT tests, but
the formal software proof/admission must enforce it too. A new source-bound
parity module checks all324policy/216book/30warm contents against exact original
published commit37ca53d, including archive/header integrity, under the complete
stage clocks. Formal read/publication/native/permit paths now require its record
and replay its numerical check; source380binds that helper. Tests reject changed
vectors even when archive hashes are updated, missing inventory, wrong scope or
baseline, and absent parity evidence. Original source379check cohort is retained
as pre-correction evidence and cannot qualify the final380source. No formal
measurements were made on it, so this is not a cost retry or outcome selection.
All final source roles will be rerun at one unchanged final head before data.


### November 13 — final effective-source gate complete before collection

B52a9ef/E45source380 passes both full local bases3,443/64skip/150deselect
(785.65/764.62s), both broad ALL-EXTRAS784 (451.06/392.08s), and BOTH exact-head
hosted43407283257 (3,443/64/150 plus historical warning;1,207.10/1,223.59s).
Allsix raw roles/head/job metadata are retained atchecks.json. Superseded379
source's3434/775local passes and cancelled hosted43405881565 are retained
separately; no formal results existed on that source and none qualify380.
Original source/config/kernel bytes unchanged. Source/frame/runtime guards use
explicit checkout PYTHONPATH because this Mac skips hidden editable-path files.

Collection may use fresh ignored output directories, then publish exact original
receipt/child/journal/archive/report bytes at canonical versioned paths. Actual
producer paths/invocations stay retained; no data rewriting or timing changes.
The original complete-command scope excludes subsequent administrative copying
and publication. All source/loading/archive/mathematical replay/report work stays
inside measured clocks. This permits one coherent ALLthree-own publication
BEFOREany native cost, and ALLthree-native publication before forecast, without
weakening clean-source or publication gates. Runs remain serial. No formal proof,
new cost or real training outcome yet. Next: publish these source roles, then the
full shared180s tiny proof, own before native.


### November 13 — complete source-bound cached tiny proof

After six-role source evidence31db81a was public, fresh own software proof takes
15.0506875s, all324policies/216books/30warms/108compositions/432scores/1152fixed
conditions, replay0 and exact policy/book bytes. Formal old-vector guard matches
all570vector contents against original own-only commit37ca53d. Parent5244checks,
8original traversals/5236reuses; actual per-worker counters/journal retained.
Complete own evidence02be1af public BEFORE any new native constructor. New
independent command6.247079s; all432/1152compare within1.1102230246251565e-16
FICTIONALpayoffunits; no reference actions exported/training. Shared133.857476s
(includes own publication/administrative interval) fits180. Raw clocks, source,
worker/journal/schema and exact copies retained. This is software proof ONLY;
no new Hold'em trajectory or compute permit. Next allthree serial own cost
stand-ins, one coherent own publication BEFOREany native costs.


### November 13 — all three complete own costs retained before native

Fixed serial0/1/2 whole own commands take200.1095483750105,
200.82031762499537,201.19776920799632seconds; D=max201.19776920799632.
Each fits900, includes source/proof/loading/archive/full math replay/sixreports,
and records432scores/1152fixed, replay0, exactpolicy/bookbits and actualnew
pokerwork0. Parent8076requests/26original/8050reuse, nofallback/rejection each.
Every producer receipt/child/journal/archive/report is byte-identical at its
published canonical path; original ignored outputs and command paths retained.
Allsix reportfiles byte-identical across allthree runs; inspected allthree PNG
classes (representative0 covers identical1/2). Titles explicitly say oldOWN
stand-ins/zero newlearning/no strengthadmission, coincidentpairedgaps are not
an experimental treatment result. No native COST constructor yet. Publish this
ALLthree-own bundle before any new nativecost. These are new absolute pipeline
costs, not a causal speed estimate versus old unpaired timings. Native N and the
complete original guarded forecast remain unmeasured; no permit/new training.


### November 13 — all three complete independent costs retained

After ALLthree own costs were public atab02f25, fixed serial native0/1/2
commands take402.320211541999,406.53780845800065,406.9446965840034s.
Each compares432scores/1152fixed targets within1.8474111129762605e-13 chips;
reference scalar-only, no new training. Parent8316requests/26original/8290reuse
and each native worker1112/18/1094, no fallback/rejection. Whole clocks retain
pre-own rereplay, worker startup/loading/scalars, and required final own rereplay.
Raw receipts/children/journals/execution/publication witnesses are retained at
results/compact-cached-learning/cost/0..2. Original outputs remain unchanged.
N=max406.9446965840034 gives native guard933.8893931680068>900; the COMPLETE
forecast has not yet run and must seal/replay ALLinputs before final reporting.
Publish this ALLthree-native bundle first. No admission/new poker trajectory.
If full forecast fails, next step is complete-native-path profiling before any
new optimizer; retain this failed cost set without favorable retries.


### November 13 — complete cached forecast fails the independent budget

Whole forecast 450.751459332998s<900; ALLthree own
archives replayed, all native worker/journal/license/clock/publication evidence
validated, 101 inputs sealed and original ALL24 full B4 paths/kernel geometry
checked. No half discount. T=610.943356249918, D=201.19776920799632, N=406.9446965840034.
Own guard 4046.1689634156646<7200 passes; independent
933.8893931680068>900 FAILS. No admit command or new Hold'em
trajectory. All prior failed outcomes and defaults remain. Method retains all
six times and limitations; journal107 explains the practical decision.
Next complete-native-path profiling, separately registered/source-checked,
before any further optimization. Diagnostic times cannot rescue this cost set.

Final relevant same-source regression:87focused adapter/cache tests pass in17.00s;
all380scientific bytes still match B52/E45, complete forecast measurement valid,
no permit/real own trajectory file exists. This evidence/documentation-only
publication retains the earlier complete same-source local/optional gate. Both
final PR-head hosted checks remain required before history-preserving merge.


### November 13 — complete native-path profile registered before measurements

Issue4/step108: cached whole-native costs402.32–406.94s leave the guarded
forecast933.889>900failed. Fix repetition0, one plain/profile pair,900each/1800
pair plus60save reserve, full initial/final own math and all native workers.
Use parent CPU cProfile nanosecond timer, lossless functions/callers and raw
binary; retain separate worker wall/CPU and complete-read phase times. Allscalar
and computed replay summaries must be exact. Expanded source binds all380old
files plus standalone instrumentation; base-admission validator must reject
instrumented receipts. Source-bound six-role checks precede formal collection.
Private unmeasured scaffold drafted during prior forecast; protocol published
before outcomes. No optimization selected, new training, gate change, admission
or causal/population speed claim. Stop9a.m.Pacific; no subagents/future schedule.

Complete native profiler implemented in an explicitly separate standalone entry;
all380base bytes unchanged.35new+61existing focused checks pass96/16.12s,
full lint/format and strict730-file typing pass. Actual fixture profile retains
lossless stats and blocks base admission; hard timeout retains partial bytes.
No formal native profile outcome yet. Freeze/publish exact instrumentation
source, then all six same-head base/optional/hosted roles before collection.


### November 13 — all six complete-native-profile source roles pass

Immutable D4/0471/382 source: full local3478/64skip/150deselect each
(786.59/762.55s), optional819each(437.70/372.98s), BOTH exact-head hosted
43419209354 pass (3478/64/150 plus historical warning;1140.45/741.41s).
Raw role logs/run/jobhead/timing metadata/driver retained. Source unchanged;
all six roles published before any formal pair. Method/3QAs/journal108 updated.
Previous PR62 final hosted43418526498 BOTHpass at07c6dcd (3443/64/150 plus
historical warning;1093.35/1256.25s), ready for history merge; rawfinalCI logs
and metadata retained separately. Fresh main snapshot115945Z still matches all
ten original094024Z user changes exactly. Finish safe main integration before
the one fixed full native profile, with no competing local heavy checks.


### November13 — CPU-instrumented full audit hits fixed cap; raw partial retained

ONEpair: ordinary407.5098637080082s/0, profile900.0317477079952s/124
TimeoutExpired; overalldriver1, pairfailed_retained. Allthree native DONE records
survive144scores/384fixed each, but finalownmath/wrapperidentity unfinished.
No .prof/losslessfunctions/callers outputs; no detailed bottleneck or complete
pair agreement claimed. Exactwholepair/execution copies plusallfilehashes and
originalignoredbytes retained. Old CPUsource382/capsunchanged; no retryunderit.
Source/runtime/mainintegration and sixrole evidence stillvalid.

Separately register complete ELAPSED-stack measurement on samefixedcost0 with
builtin cProfile timer(no per-call Python CPU callback), same900/1800caps/all
mandatorymath/workers. Parent/read boundaryCPU and workerCPU remain separate;
per-framevaluesare elapsed/wait-inclusive. Newsource384 bindsold382+newentry/
config, allold380kernelsunchanged. New six-role checks before formaldata, old
partialpublished first. No diagnostic-time rescue/optimizerselection/newlearning.

New elapsed instrument implemented separately:35new+96related checks pass
131/21.31s; full lint/format/strict732files pass. Actual fixture verifies builtin
profiler factory has no Python CPUcallback. Prior382map+newentry/config yields
384effectivefiles; original380numeric and382CPUinstrumentation remain unchanged.
Freeze/publish source; six same-head roles before any new elapsed-profile data.


### November13 — actual hosted patch mismatch found before elapsed collection

C0local3513/64skip/150deselect each(763.62/743.98s), optional854each
(426.06/365.19s), both hosted43426080942 pass software. Reading actual uv lines
finds hosted312uses3.12.3, not receipt/schema's3.12.15. C0cohort savednonqualifying;
no elapsed pair collected. Earlier B52/D4hosted312logs show same mismatch.
Read-only fixedC0audit of tracked*checks*.json roles authenticates all log hashes:
9receipts/18hostedrows,9declared31117match,9declared31215actually3123. Sixparser
self-tests pass. Allrows/inputhashes/rerunnablescript retained; scope limitedto
theseformats, no automatic claim every numerical value invalid. Exact-patch
gate claims unsupported; no backfilled qualification or rewritten olddata.

Workflow now pins exact3.11.17/3.12.15 throughsetup-uv+UV_PYTHON and assertsactual
Python/NumPy beforetests. YAML parsed/pins/guard verified and uvinstalledhelp
confirmsUV_PYTHON selection. All384sciencefiles unchanged. README/methods/dated
correction/journal explicitly distinguish metadata error from numerical producer
outputs and retained budget/profilefailures. New six roles atONEcorrectedhead
must pass withactualguardmarkers before moredata. Originalcaps/seeds/quality
gates unchanged; no newrealtrajectory/default/global admission or humanhours.


### November13 — corrected actual-runtime source roles qualify new diagnostics

A672all6roles PASS: local3513/64skip/150deselect each796.09/771.16s;
optional854each448.17/387.33s; BOTHhost43430646265headA6723513/64/150plus
historicalwarning1290.36/962.81s. Raw uv lines ANDactualguardmarkers confirm
31117/NumPy246 and31215/NumPy254 beforetests. Newassembler requires those
markers/selectionlines/guardsteps, actualhead andrawuntrimmedloghashes. Receipt
bindsworkflow/correction, future-diagnostic-only andno-retroactive-admission flags.
All384sciencebytes/7fdfp unchanged. Journal109 explains labelsversusactualruntime.
Publish allsixroles BEFOREsinglefixedelapsedpair. No elapsed outcome/optimizer
selection/newtrajectory yet. No localheavychecks duringcollection.

### November13 — complete elapsed audit profile and exact pair identity

Correctactualrolespub331precede fixedpair. Ordinary406.4912895419984s/0,
profile573.8724571670027s/0; shared980.402532209002<1800, each<900. Complete
432scalars/1152fixed/threeactualreads/worker-cache-source identities EXACT.
All2354rawfunctions/5640callers+binary retained; exactwholepair/executioncopies,
allfilehashes/originalignoredbytes, readonlyverifierPASS. OldCPU900timeout and
old9runtime-label mismatches remainunchanged/flagged; no retroactiveadmission.

Callersshow184matrixbuilds114.6707inclusive,918104canonicalcalls32.0032inclusive,
4099136bestevaluatorcalls35.2272inclusive. Wait126.5368self includesnativework;
wallframesnotCPU andinclusiveregionsoverlap. Measurednextquestion: boundedpure
card normalization/ranking reuse preserving allvalues/RNG/typedinputbehavior,
notpolicy/referenceoutputcaching. No optimizationoutcome/newtrajectory yet.
Posthocreport source+10unit checks0.02s pass withlint/format/types; rawallframes/
callers exported andelapsed-versusCPU guard preventswrongunitlabels. Publish
source+rawsbeforeactualrender. Latest13:55real-study start nowpassed; remaining
work is boundedsoftware/diagnosis before9, never shrunkcaps/seeds/gates.


Posthoc385-source report generated from published8519562reportcode, rawdata and
source/unit guards; exact copies retained withallinput/outputhashes. ActualPNG
visually inspected: labels/legend/elapsed-versusCPU clear, no clipping/overlap.
ALL2354function/5640caller CSVrows pluselapsedparts/workers/summary saved.
Tenpure accounting/unit-source tests0.02s/lint/format/strict2newfiles pass.
README/method/limits/terminalcommands/journal110 updated. Final hostedCI required
before63historymerge. Next prospectivecard-only memoization (canonicalization
andranking), exactvalues/input/RNG andboundedmemory withactualperprocesscounters;
no agentperformance claim or fulltrajectory after13:55UTCunder11100reserve.

Posthoc base-only typing caught optionalMatplotlib import-not-found after the
all-extras check passed. Fixed ONLYreporter to defer optional imports through
importlib, matching optional rendering dependency boundaries. Both actual base
311/312strictnewfile checks and10report tests pass; no384measuredsource orraw
artifact changed. Original385render851source/outputs retained; final hostedCI
must include this reporter fix. This is a reporting packaging correction, not
an experiment rerun or changed numerical claim.

### November13 — prospective parent-only pure-card reuse diagnostic

Measured elapsed callers motivate bounded16,384canonical/65,536rank exact-tuple
LRUs, successful immutable original results only. Publish protocol/config before
implementation/outcomes. Same complete cost0audit uncached/cached, unchanged
spawned workers,900/1800caps and1800finalCI+120save reserve, six actual-runtime
source checks before pair. Exact432/1152/three computed reads/worker equality,
invalid/fallback/dependency/RNG/counter/bounds tests. No policy/reference cache,
production integration, admission or new learning; originalfailuresretained.

Parent-only cache scaffold now covers exact primitive tuple keys, bounded LRUs,
success-only insertions, dependency fallback including card validation/helpers,
full accounting, aliases/late imports/failure restoration and explicit original
worker scope.59new+101prior profile/recall tests pass160/19.73s; allprojectlint and
strict737files pass. Six fresh same-head actual-runtime roles precede formal
ONEcomplete pair. No timing outcome or changed policy/source gate claimed yet.

A separate posthoc reporter is drafted while387-source checks run, before any
pair outcome. Seven report scope/source and warmed-key type-boundary tests0.03s and strict checks on both
base-only interpreters pass; optional plotting uses importlib from the start.
It will display all mandatory wall stages and original card calls, retain either
timing sign and bind all measured inputs. No report generated or pair yet.

PR63history merged52619fa after BOTHfinalhost43439012871 pass3523/64skip/150
plus historicalwarning1270.80/1137.55s, actualuv+Python/NumPy verified. Rawfinal
logs/metadata saved inwork/native-profile-final-checks. Main actual31117/NP246,
all384source/historicalinput hashes/viewer and111regressions15.86s pass. Fresh
141842Zsnapshot matches originalnightly allten user bytes/status/index/patches;
allstillpreserved afterFF/viewer/tests. Historical exact-patch qualification
mistakes remain corrected, not backfilled.

Card source49ebd19/387files/b55a86 passes localfull3582/64skip/150deselect each
774.51/754.13s andoptional923each439.81/371.70s; allfouractualenv/sourceguards
pass andprocessesclosed0. BOTHhost43440514840stillpending. No timingpair yet.
Posthocreport explicitly discloses samewrapper/guard/counter overhead in BOTH
modes: a pair reduction cannot be called unwrappedproduction speedup or replace
freshthreecosts/maximumforecast. No originalboundsciencebyte altered.

BOTHsourcehost43440514840 nowPASS at49ebd19 withactualuv+Python/NumPy guards
verified; all6roles/rawmetadata/untrimmedlogs authenticated andretained. Source
387/b55a86 unchanged; retarget64main onlyafterthisruncompleted. Publishchecks+
posthocreporter/source beforeONEregistered completepair. No otherlocalheavyjob
runs duringmeasurement; full900/1800caps+1800finalCI+120save fit9a.m.cutoff.

### November13 — card reuse exact but registered whole-wall criterion FAILS

Bothcompletecommands0,481.8409937079996/595.6503214999975s; pairedtimingdriver2.
All432scalars/1152fixed/threeactualreads/worker-source-proof identities EXACT.
ParentCPU283.79782/261.253542s(7.94%lower), butwholecachedwall23.62%higher.
Canonical918104requests/917324hits/780originals; rank4099136/4068415/30721.
No errors/fallbacks/evictions; allentrybounds intact. UnchangedworkerCPUabout123s
each whilebatchwall134.1043→165.1282; tinyreadCPU1.91/2.03 versuswall2.06/9.61.
Evidence identifiesCPU-versus-elapsed discrepancy, notitscause. No arbitrarywall
exclusion, capchange, rerun, cachedproduction/forecast/admission or newlearning.
Exactwholepair/executioncopies+allhashes/originalignoredbytesretained; readonly
complete math verifierPASSwhiletimingFAILkept. RendererC806publishedbeforedata;
389-source report generated, exactcopied, actualPNG visuallychecked(no clipping/
labeloverlap), allinputs/outputs bound. Sevenreport/boundarytests/lint/format/strict
bothbase interpreterspass. Next separately registerboundedresources/clocktracing,
notintegration ofthefailedprototype. Final64hostCIbeforehistorymerge.

### November13 — prospectively trace the failed clock discrepancy

AfterPR64whole-wallFAIL, registerseparatecurrent-process/worker-resource trace
beforeimplementation/data. Unchangedcardcache/387source/limits/numerics; explicit
temporarypercommandcaffeinate-i controlforbothsides,binarypinned/localmanualread,
no display/persistentsettings/machine-widelogs. Boundaryperf/UTC/process/thread/
rusage+self/reapedchildren, threeseparateworkersidecarswithnewsourceguard and
unchangednumeric summary; RSSpeakunits/counterlimits explicit. Sixactual-runtime
rolespublicbeforeONE900/1800pair+1800finalCI+120save. Done=exactmath+complete
telemetry, BOTHtimingdirectionsdescriptive, NOperformanceadmission. Priorfailed
pairnotretried/reclassified; no productionintegration/newforecast/learning.

Resource observer implemented withown/reaped-child rusage andperf/UTC/process/
thread boundaries, raw/delta/unit guards, cumulativeRSSpeaklabeling andUTCadjustment
allowance. Parentreadstarts/workerstarts andnumericfinished-before-aftersource
are persisted onfailure. Threeworker sidecarsbindnewsource/runtime/module-root/
actualspawnedPID/partitions/unchangednumericsummary. Old387files/cardhelper/caps
unchanged. Utility-lifetimecaffeinate-i requestrecorded(notindependentlyaudited
assertionstate), exactsupervisorcommand/binary pin checked, restoredaliases/env,
no newtraining/policy/referencecache.34new+66cache/reporttests100pass2.36s;
fullprojectlint/strict742filespass. Publishsource thenall6same-head actual-runtime
rolesbeforeanyformaltrace. Supplemental profiletests included in finalfocusedset.

PR64historymergedb8ef006afterbothfinalhost43448389410pass3589/64skip/150plus
historicalwarning926.89/1198.07s, actualuv/Python/NumPyverified; rawlogs/metadata
retained. MainFFfresh152151Zsnapshot alltenbytes/status/index/patches preserved;
readonlydata/sourceviewer and66regressions3.77spass, aftertestpreservationpasses.
This closesnegativeinvestigation, nottimingadmission. New390-sourcecollection
stillwaitsforallsixroles. Posthocresourceexporter draftedbeforeoutcome:8unit
scope/raw-delta/CPU-wall/peak-unitchecks0.04s andbothbase-onlystrictchecks pass;
allresourcecounter/clock/peakrows retainedwithoutcausal/performanceclaim.

InstalledDarwingetrusage(2)manualchecked:ru_maxrssmaximumresidentsetisbytes;
LinuxKiBlabelsapplyonlytheir software fixtures. Temporarycaffeinate-i truefixture
returns0/no diagnostics; requestfieldexplicitlydoesnotclaimindependentassertion-
state audit. Originalfailedpairimmutable, newbothdirectiondescriptivetraceonly.

390-source7487afb/be647d36 ALL6rolesPASS: local3623/64skip/150deselect
798.44/772.94s; optional964each449.10/382.05s; bothhost43450790359actualuv+
Python/NumPyverifiedbeforetests. Untrimmedlogs/fullheadmetadata authenticated;
retarget65mainonlyafterruncompleted. Publishallsixandtestedposthocreporter
BEFOREoneformalresourcepair. Source390/old387 unchanged. Currentfullcaps plus
1800finalCI/120save reservefit9a.m.; no otherlocalheavyjobduringcollection.

### November13 — complete resource diagnostic, old timing FAIL preserved

ONEresourcepaircomplete0:551.6211327499914/527.1198560829944s, shared
1078.7796968330076<1800; each<900. All432scalars/1152fixed/threeactualreads/
cardcounts/unchangednumericworkers EXACT; all3read+3worker source/PID/runtime/
resource records validate. Canonical/rank countersmatcholdprototype(917324/
4068415hits,780/30721originals), zeroerrors/fallbacks/evictions. No production/
performanceadmission/newforecast/permit/learning; rawlowerwallisdescriptiveonly.
BodyCPU285.656045/260.792604. Resourceownreads report21.46–21.97childUSERCPU plus1.28–1.31childSYSTEMCPU
perfullread, alongside127–141parentCPU; workersreport124–125ownCPU plus
about39.5childUSERCPU/2.5childSYSTEMCPU. ParentCPUalonewasincompletecomputeaccounting. Extraobserver
sourcechecksareincluded; no causaldiagnosisofolderuntracedpair, no summedparallel
CPUaselapsed or assertion-state claim. Original481.84→595.65timingFAILunchanged.
Exactwholepair/executioncopies/allhashes+originalignoredbytes retained; readonly
source/raw/resources/completeidentityverifierPASS. Publishrawbeforeposthocrender.


Posthoc392-source report frompublished641reporter generated andexactcopied;
actualPNGinspected(noclip/overlap), all16clock/288counter/32peak rows/input/output
hashes retained. Tableusesrawreporteduser/systemchildCPUfields, notunmeasured
helperattribution; oldprofiledifferentcopy. No wallstackofCPU/parallel sums,
causalidleclaim, memorysaving or productionforecast. Documentednexttest=perhelper
accountingbeforeoptimization. AddedpostcollectiondirectchildCPUagreementfixture
(0.1saccountingtolerance, fixedintegerwork, no poker) passes311/312. 312alsofound
posthocfixtureexact2 versuscorrectfloatdelta1.9999999999999998; approximateassertion
fixONLYtest, no390measurementcode/data altered. All9report/accountingtestsPASS
bothversions0.04/0.07s andstrictbothbaseenvs pass. Journal112/README/methods current;
finalrelevantchecks+bothhostedjobsrequiredbefore65historymerge.

### November13 — prospective helper-accounting component only

Resourcecountertrace recordschildCPUbutnotpercommand. Registertransparent
subprocess.runobserver contractbeforeimplementation: Gitread-onlycategories/
argvhashes/outputtype+hashonly, no rawargs/env/input/outputcontents. Unsupported
calls executeunchanged withvisibleincompletecoverage. Rawresourceincrements
areovercallinterval, notexclusivePIDCPU; concurrentchildrenconfound. Return/error
identity, partialstarts/retentionfailures/restoration/privacy tests withtiny
softwarefixtures. No real-sourcecollector wired or formalmeasurement tonight;
futurecollector mustbesource-bound/all6rolespublicwithfixedcap/config. No new
pokertraining/reference/optimization/admission, originalfailuresremain.

Helperobservercomponent implemented withoutcollector: supportedGitcategories+
argument/outputfingerprints only, no rawargs/env/input/output, visibleunknown
coverage, before/afterOSsnapshotswithnonexclusiveintervalscope. Originalreturned
object/bytes andprimaryexceptionidentity preserved; startretentionfailureblocks
execution, secondaryobserverfailuredoesnotreplaceprimaryerror, hooksrestore.
Coverageisnotcommandsuccess/sourceadmission.19testsPASSboth311/3120.08/0.07s;
expandedpriorfixturegroup126/2.84s(17-testdraft) and31260/0.40s; strict746files+
alllintpass. Journal113current, no real-sourcepathrecorded, solverorlearnerrun,
optimization, measuredspeedup or admission. Publishtestedcode, thenfullbase and
relevantoptionalchecks+bothhostjobs. Futureformalcollectorstillunimplemented.

Final component review caught relative `git -C` classification ignoring child
`cwd`. Recognition now requires an absolute repository path; unsupported forms
still execute unchanged. Added regression test for return/argument identity and
visible coverage rejection. No old source/data changed. Previous19-test and
component full checks remain draft-head results, not qualification of this fix.

The corrected component now passes20 focused tests on both actual Python3.11.17
and3.12.15 (0.07/0.09s), plus full strict typing746files and lint/format. Full
base/optional and hosted checks are repeated for the corrected head before merge.

Further failure review found an initial snapshot could raise before appending the
attempt, allowing previous completed calls to masquerade as full coverage. Record
the attempt first, mark/count initial observer failures and preserve exception
identity without executing the original command. OSError/KeyboardInterrupt
regressions cover a completed prior call. Full checks at768b/ac4ec9b remain their
own-head software evidence; this correction requires fresh checks before merge.
No real-source collector or formal collection.

Latest initial-snapshot correction:22focused tests PASS311/312(1.89/0.10s),
166related tests PASSboth(9.16/8.34s), strict746files PASSboth and all lint/format
pass. Journal current-status updated. Remain DRAFT until fresh full local/hosted
checks of this correction pass; prior-head results are not transferable. With
under13minutes to9AM, do not launch another full local check whose safe finish
cannot be assured. Publish corrected source/CI and retain all partial/prior
checks; no formal collector, actual source-path measurement or poker trajectory.
PR65 is history-merged effa65c after verified3632pass hosted jobs on both actual
runtimes; main viewer/43tests0.20s and all390source hashes match, ten user result
edits/status/index entries/staged+unstaged patches remain exact.


### November 14 — finish PR #66 and register a publication-helper diagnostic

Corrected source3a94953 passes full local3,654/64skip/150deselect on both
versions(819.99/806.67s), relevant optional166each(10.19/8.88s), strict746files,
lint/format/hooks. Hosted43466368826 passes both actual3.11.17/NumPy2.4.6 and
3.12.15/2.5.4(918.26/1178.60s). Raw logs/exact heads/runtime guards authenticated.
History-merged PR66 as6c9d394; main22tests0.10s pass. Guarded FF preserves all
ten unrelated edits/status/index entries/patches. This completes the software
component, not measurement qualification for a future collector.

Register fixed publication-check diagnostic before implementation: one original
compact_cached.publication.publication call per control/observed arm, exact
returned dictionary and fourteen frozen input members; no replay/training/reference.
900s complete child/1800s shared separate diagnostic caps; seeds/work/study gates
unchanged. Add independent process-event census to detect run/Popen aliases;
ignore event arguments, retain partial failures. Extend command catalog only with
symbolic-ref used by the existing check. All390 historical scientific files stay
unchanged; exact collector source and six actual-runtime roles public BEFORE
collection. Both timing directions descriptive, no full-audit forecast rescue.
Journal114 explains the bounded question. Codex assisted; actual work dates.

Publication collector implemented after prospective557511c: existing validator
called unchanged, separate child per arm, exact returned witness, source394
(all historical390 unchanged), fixed inputs/caps and published six-role gate.
Helper catalog adds symbolic-ref only. CPython audit census discards arguments
and detects imported run/Popen aliases; marker detects suppressed registration.
Streaming starts/finals and partial ledgers persist, observer scope is interval
accounting rather than exclusive PID CPU. Read-only CSV reporter checks raw
inventory/command/status/PID/deltas/hash/qualification/witness before grouping.
Unit fixtures isolate audit hooks in separate processes. First fixture failure
was its own untracked output directory; ignored that directory in the fixture,
not in the real validator. No actual publication target or training run yet.

Prepublication software checks:37new +22component =59pass both311/312
(0.60/0.72s); full lint/format and strict748files pass. Fresh full local base,
relevant all-extras and both hosted checks now precede formal collection.

Premeasurement interface review caught a real relative-path mismatch: the
supervisor recorded the CLI's relative output argument while child provenance
stored an absolute path. Normalize the run destination before child commands;
add a regression for the public relative CLI form. Record runtime/hardware in
each child as well as administrative context, and validate saved Python/NumPy
markers in the reporter. No formal target pair had run. Earlier1f85d32 software
checks remain source-bound evidence for that superseded head; none qualify this
correction. Repeat all required source checks on the corrected head before data.
No protocol target/input/seed/cap changes and all390 historical sources unchanged.

Corrected prepublication tests:39new plus22component =61pass on actual311/312
(0.72/0.69s), all lint/format and strict748files pass. Old1f checks fully passed
but do not qualify this changed collector. Publish code and repeat all six.

Corrected394-source459fc0f/7da2c541 now passes ALL6roles before data: 3693 passed, 64 skipped, 150 deselected in 791.93s (0:13:11); 3693 passed, 64 skipped, 150 deselected in 769.40s (0:12:49); 205 passed in 11.04s; 205 passed in 9.71s; 132398692248; 132398692142.
Hosted43578743429 both actual runtime/uv/head/log hashes authenticated. Full
local3693/64skip/150deselect each, optional205each, exact source guards before/
after. Publish all raw role logs plus checks.json and operator launch record
BEFORE the one fixed pair. All390 historical files unchanged; no target yet.

ONEfixed publication-helper pair complete0 after5396c43six-role publication; raw
fbf5eb8 published BEFORE posthoc renderer. Completechildren 1.0604225000024599/1.064042709000205s; exact14input/witness
identity,21helpers/21audit events,1event/request,0unsupported/unassigned/nonzero.
All9raw files+executionexactcopied, originalignoredbytes retained, manifest binds
allraws; operator matches prepublished launch source. Child runtime/hardware
recorded(brandquery unavailable,arm/10CPU only). Reportgroups Gitshow14largest
observed interval0.236304623s, targetabout0.6s. No causaloldread explanation,
per-PIDCPU/wallstack, full-audit forecast rescue, memorysaving or stronger agent.
Nextquestion whole-reader helperfrequency; stop this milestone after final checks.
Journal114/methods complete; original390sources/caps/seeds/failures unchanged.


### November 14 — clearer project introduction and contribution wording

Editorial work requested in [issue #68](https://github.com/jimmy-sim/poker-ai/issues/68).
The README now introduces the project, components, representative results, setup,
and research navigation. Detailed reports remain linked; all four generated
summary blocks and their markers are retained unchanged in a collapsible section.
The [previous front page](https://github.com/jimmy-sim/poker-ai/blob/459fc0f98a6989ce4beb6646229ae03a87281c9f/README.md)
preserves the earlier running narrative without duplicating it in a new file.

Overview introductions and interview drafts distinguish project capabilities,
Codex assistance, supported intentions, and actual personal practice. Historical
journal chapters, specific credits, reports, protocols, raw results, and operational
requirements are preserved. The package description was reviewed and left intact:
it is already factual and is part of frozen source fingerprints. No code, tests,
dependencies, budgets, criteria, CI behavior, or autonomous permissions change.
Documentation/link/anchor/image/generator checks and hosted CI are required before
merge; actual verification results are recorded in the documentation PR.

Codex assisted with the editorial restructuring and verification. No new personal
practice, manual implementation, or hands-on time is inferred.

One pre-existing broken work-log artifact link now points to its original file
at immutable commit95e8c8d. The artifact, event description, dates, and results
are unchanged; no historical data were recreated.

Focused verification passes: diff whitespace, relative links and heading targets,
GitHub Markdown rendering, five unchanged linked figures, four byte-identical
generated blocks, and generator-update functions on a temporary README copy.
The original Mermaid diagram, historical journal/personal notes, interview
numbers, phase contracts, operational files, and package metadata are preserved.
The public-board example passes. The saved-decision browser needs a published
branch; its smoke check and required hosted CI follow publication.


### November 14 — complete-reader helper diagnostic, prospective

Continues [issue #4](https://github.com/jimmy-sim/poker-ai/issues/4) after PR #67.
The [protocol](reader-helper-trace.md) fixes one control/observed complete own
read, fresh existing recall cache, original real-archive runtime, complete
900/1800 diagnostic caps, exact returned/computed/cache identity, and full
helper/process-event coverage. All six exact-source qualification roles are
published before a real read; raw evidence precedes reporting. No training,
reference construction, optimization, failed-gate revision or new admission.
The ten unrelated local result changes were freshly snapshotted before work;
an isolated branch preserves their bytes/index/status/patches. Historical394
measurement files stay unchanged; new private entry/config are explicit.
Learning-journal116 explains the difference from the narrow publication check.
Codex assisted; personal hands-on time is unrecorded. Stop after this bounded
inventory or a retained explicit failure, before choosing an optimizer.

Implementation adds the private collector and55 software fixtures only; original
394files remain unchanged. New gzip streams preserve full dictionaries and
partial outcomes; exact reader/cache/deadline call shape, actual summary,
independent process coverage, raw/log hashes, caps, scopes, input mutation and
read-only report tests pass. Combined116fixtures pass3.11 in1.22s; initial312
fixtures passed116 in1.58s, before two typing-only corrections. All lint/format
and strict750files pass. Full exact-source base/optional/hosted checks and
published qualification are next; no real reader target has run. The connector's
PR-only comment route was rejected for issue4; verified issues/4 as an issue and
published the plan through the issue-specific interface, without changing scope.

Source0e46992/396filedb1fbed9 passes all6roles before collection: base3748/
64skip/150deselect each801.47/786.78s; optional260each12.15/10.62s; hosted
43618535981 both3748 with one historical warning (940.29/658.15s). Actual
3.11.17/NumPy2.4.6 and3.12.15/2.5.4, exact heads/uv/log hashes verified.
Direct312log redirect timed out; complete authenticated connector log retained,
companion311byte-identical to direct download. No CI/measurement retry.
Publish checks.json/raw six-role logs/runners and exact operator before the
one complete-reader pair. Clock boundary conventions are explicit; no source,
scientific cap or acceptance criterion changes. No actual target yet.

Original pair fails and is retained278fc04 before reporting: control37.860311792s,
return1/PackageNotFoundError; shared37.897130209s; no observed arm, complete
summary or helper count. Exact four raw files/execution copied with originals
retained. Launcher base environment lacked Numba and other extras; metadata-only
inventory proves missing requirements, not which package triggered first.
Static review identifies the reader's CPU-brand sysctl query, outside the first
Git-only catalog. Prospectively register ONE fresh runtime-complete pair with
new398-file collector/config preserving all396 measured files. Pin existing
optional versions and exact probe binary; keep old caps/data/reader/math/gates.
Fresh six-role checks and published qualification precede any corrected read.
No optimization or new training. Journal116 records failure and correction.

Follow-up implementation preserves old396files, adds private collector/config
and68fixtures. Combined184 pass both versions; strict752files passes. Required
locked versions and exact CPU-probe binary are checked before target; saved
requirements, probe success/alias/privacy and unknown-not-zero prior-failure
report covered. Fresh six-role398-source qualification still precedes a real
follow-up. No old source/data/caps/acceptance predicate changes.

Corrected398-sourceab69275/e1e5e879 passes ALL6roles before newdata: local3816/
64skip/150deselect each781.55/766.57s; optional328each15.32/14.09s; hosted
43622239051both3816/onehistoricalwarning736.56/656.41s. Actual3.11.17NP2.4.6
and3.12.15NP2.5.4, exactsource/uv/log hashes verified. Strict752/Ruff895pass.
Publish newchecks.json/allrawlogs/runners and exact full-optional311operator
before ONE correctedpair. Original396files/failed278fc04evidence preserved.
The old failure JSON reports unknown helpers and no completed replay; no new
reader measurement yet. No scientific cap/gate/strategy/default changes.

Corrected ONEpair completes0: wholechildren142.690953542/142.749746041s,
shared286.059276959s;398source and20input bindings unchanged. Raw507058a
public BEFOREreport. Nine rawfiles/execution exactcopied, originals retained,
operator==prepublishedcopy.49helpers/49process events(47Git+2sysctl), all0,
no unsupported/unassigned/observer/retention error; exact own/computed/cache
identity,432uniqueprofiles/1152fixed conditions, zero recorded errors.
Cache2832requests/18original/2814hits, no rejection/fallback. ReportCPUhelper
sums0.239208user/0.652311system match whole target increments; ownprocess
about141s. Historical21–22child-userCPU NOTreproduced, cause unresolved.
No helper-dominance/optimizer/933.89forecast rescue/strategy improvement claim.
Both numeric exports byte-identical in3.12DATA-ONLYparser with actualreader/
learner/reference blocked. Methods/table/limits/threeQAs/journal116 complete;
first278fc04failure retained. Final relevant/source/hosted checks precede merge;
stopafterthisinventory, before newoptimization or training. Codex-assisted;
personal hours/mastery/practice not inferred.

### November 14 — reconcile saved reader boundaries before another measurement

Prospective [issue #4 plan](https://github.com/jimmy-sim/poker-ai/issues/4#issuecomment-6886112990)
precedes this data-only checker. Six fixed input hashes bind both historical
three-read arms and both standalone reader receipts. Check all eight intervals,
process/scope/order, recorded source maps/current bytes and recorded real archive
summaries; do not execute the reader or infer a causal speedup. Tests deliberately
break these conditions. Initial28 pass; full applicable checks and hosted CI
still follow. Historical398 files and all raw results stay unchanged. The ten
unrelated main changes were freshly snapshotted; this isolated branch preserves
them. Journal117 explains the question. Codex-assisted; human time unrecorded.

Record the November14 request for modest contribution counts here and in the
publishing guidance: coherent batching/edit existing status descriptions, with
all mandatory publication boundaries and real dates intact. No separate PR or
commit for that preference, no contribution quota and no change to research gates.

Data-only result in [PR #71](https://github.com/jimmy-sim/poker-ai/pull/71): all8
raw intervals recompute exactly with matching parent IDs/platform/units. Six
recorded real-archive summaries and own hashes agree; old390source hashes are
unchanged within the newer398map, and all398current bytes match. Export
[summary.json](../results/reader-boundary-reconciliation/summary.json) binds all
six input hashes plus checker/config hashes. Actual3.11.17/NumPy2.4.6 and
3.12.15/2.5.4 produce identical JSON (SHA256593df042b166f618a20410c3da8b24c11322c038b4ecda7a9551da1ada819a06).
These are data-only checks, not new mathematical replay or runtime collection.

28new tests pass per version; related optional clock/checker suites71pass each
(0.69/0.90s). Ruff897files, strict754files, hooks, diff whitespace and allfive
changed Markdown files' relative links/anchors/fences pass with no old or new
link defects. Full local tests and hosted checks are still running at report
publication; their final results and exact-head CI links are recorded in the PR
before merge. No code changed after these checks began; the final increment
adds the saved-data export and explanation.

Cause remains unresolved. Frozen call paths differ in tiny-read/cache history,
card wrappers and nested observers. Later native workers cannot by themselves
explain the older initial read. Do not call this a speedup or choose a helper
optimizer from counts. Next separately registered measurement should restore
the intended original audit context and account for helper/resource boundaries
and dominant own-process work together. No further collection begins in this
milestone. Original933.89/900forecast and prior unfavorable cache timing remain
failed; no new training, stronger agent or default/admission claim.

### November 14 — original-audit-context measurement registered

Continue [issue #4](https://github.com/jimmy-sim/poker-ai/issues/4#issuecomment-6889171302)
with one fixed control/observed pair of the original complete uncached audit.
[Protocol](original-audit-helpers.md) preserves the warm-up, shared recall cache,
card wrappers, three mathematical reads and native workers. Only the observed
half adds per-read helper/resource coverage. Source map402 preserves all400prior
measurement/bookkeeping files;31input hashes, runtime/extras/binaries and900/1800
caps fixed. All six same-head source checks and published qualification/operator
precede data; raw evidence precedes reporting. First37fixtures pass, including
nested ledger/schema failures and original-child raw retention. No real target
has run. Codex-assisted; no personal hours/mastery inferred. Ten unrelated local
result changes freshly snapshotted and preserved in an isolated branch. One PR
will keep the required source, qualification, raw and report boundaries batched.


All six source roles pass at 9bd3593 / 402-file f0f19b08 before collection:
local bases 3,881 / 64 skipped / 150 deselected each (795.80 / 778.81s), optional
393 each (16.20 / 14.65s); hosted43677796759 both pass with actual runtimes/uv/head
verified and one existing roundoff warning. Ruff900/type756/hooks/relative links
pass. Publish checks.json, every full log and exact launch/retention operators
before the one pair. The 400 prior source bytes, caps, seeds and gates remain
unchanged. No real target yet; these checks do not admit training or a forecast.


ONE actual original-context pair completes at published qualification c4428ac,
source402/f0f19b08 unchanged. Raw79e2b9f is public BEFORE interpretation; 30 raw
files and exact execution copies retained, originals kept. Whole children
430.942727125/460.964389041s, shared893.187598875s, all within900/1800 caps.
Original432profiles/1152conditions/three actual replays/three workers/card
counters match historical control and both halves exactly. Observed110helpers/
110CPython events (12tiny,49initial,49final), all recognized/successful and no
unassigned/observer/retention error. Per-read helper user/system sums equal
outer child-counter increments exactly at saved precision; zero residuals.
Real read own-process CPU141.258–158.211s, child-user0.247–0.278s and combined
childCPU<1s each. Historical21–22child-userCPU does NOT reproduce even in control.
Cause remains unresolved; no causal factor isolation or old-result invalidation.

Report includes six read rows, all six worker clocks, a visually checked figure,
raw/code/render hashes and three byte-identical numeric exports in actual31215/
NP254 data-only replay with reader/child/learner/reference blocked. This does
not replay archived mathematics in a newer runtime. Journal118 explains scales
and limits. No optimizer, new training/default, stronger-agent or933.89/900
forecast rescue; prior unfavorable results remain. Final relevant checks and
both exact-head hosted jobs precede merge, then stop at this milestone.


### November 14 — coarse CPU boundaries, prospective

[PR #72](https://github.com/jimmy-sim/poker-ai/pull/72) closes the preceding
original-context measurement at 6d59531. Final exact-head CI43681028590 passes
3,881 tests per version, and main's saved-data command plus 37 fixtures pass;
all ten unrelated result edits remain exact. Its finding motivates this step,
without resolving the historical child-counter discrepancy or admitting training.

The [new issue #4 plan](https://github.com/jimmy-sim/poker-ai/issues/4#issuecomment-6890391633)
precedes this [coarse CPU instrument](coarse-reader-cpu.md). Time only matrix
builds, spot-tree builds and checkpoint replays inside the original three reads;
retain the original full audit in both halves. The selected call forest derives
non-overlapping process CPU without a global per-frame timer. Preserve all402
prior files in a404-file source map;37 inputs, original runtime/extras,900/1800
caps, one attempt and all failed outcomes stay fixed. Initial70software fixtures
pass on3.11 and3.12; full six-role qualification precedes any data.
No real target has run. Codex-assisted; personal time/mastery unrecorded.

Apply the latest publishing preference in this substantive change: finish local
implementation/review/checks before the first source push, then batch commits
at the required qualification, raw and report boundaries. No standalone preference
push, date manipulation, acceptance change or future work schedule is introduced.


Source stage in [PR #73](https://github.com/jimmy-sim/poker-ai/pull/73):8970bc5,
404-file fingerprint00a339915681bbb109d04c9ee15a90d245a8bd6672b5d01b4081b17d44d3e8db.
Both immutable local bases pass3,951tests/64skipped/150 deselected,814.15/801.25s;
optional463pass each,17.88/16.53s. Lint/format/strict typing/hooks and focused
Markdown links/anchors/fences pass. Source is published after local checks;
both same-source hosted jobs and qualification publication still precede data.


At the November14 check-in, the user chose to continue issue#4 validation and
training improvements before building a Chipzen practice adapter. This keeps
the current research sequence; no external connection or season entry is part
of this milestone. No personal practice, hours or strength claim is inferred.


All six source roles now pass at8970bc5: hostedCI43688723951 verifies actual
3.11.17/NumPy2.4.6 and3.12.15/NumPy2.5.4, all uv selections and exact checkout;
3,951tests/64skip/150deselect plus the old warning each. Complete decoded logs,
local/install receipts, exact check runner/assembler and prepublished launch/
retention operators are in[checks](../results/coarse-reader-cpu/checks.json).
This qualification checkpoint precedes the one pair; no real target has run.
The404-file map and37scientific pins remain unchanged. The same source and
qualification checks will run inside the registered clocks as well.


Recorded outcome, [PR #73](https://github.com/jimmy-sim/poker-ai/pull/73): one
control/profiled pair426.7636394160072/444.64136350000626s, shared872.5313877080043s,
all under900/1800. Full original432profiles/1,152conditions/three computed reads,
worker/card identity and base-admission rejection pass. The1532-call inventory
is184matrix/52spot-tree/1296checkpoint; all complete, no hook errors, restored
aliases/descriptors, all actual selected roots. Raw31files plus8execution files
published6e69bd2 after qualificationb1b3f98 and before posthoc rendering; original
ignored bytes and exact published operators preserved.

The [report](coarse-reader-cpu.md#recorded-result--november-14-2026) assigns
17.9292% matrix,10.5082% spot-tree,24.5342% checkpoint and47.0283% outside across
two real-read process CPU totals148.116763/146.597543s. Body/nearby-child/worker
and supervisor clocks remain separate; one order does not identify pure overhead.
The old21–22child-user discrepancy remains unresolved. All five numeric exports
match actual3.12.15/NumPy2.5.4 with reader/child/tree/snapshot/scoring/learner/native
execution blocked; source404 unchanged. Final figure inspected after correcting
a clipped label with numeric bytes unchanged. No optimizer, new training/default,
strength or933.89/900forecast rescue. Next separately registered question:
localize the47% remainder, rather than assume the matrix-depth hypothesis is
large enough. Final relevant local and exact-head hosted checks precede merge.


Final local regressions463each(16.28/16.26s), Ruff903files, strict mypy758,
hooks and focused Markdown paths/images/anchors/fences pass. Saved-data CLI
matches report; all39raw/admin bytes and ignored originals retained. Local
verification and complete final logs are in the report. Both final exact-head
hosted jobs must pass before history-preserving merge; routine CI/merge status
updates the existing PR description, avoiding a status-only commit.


### November 15 — close coarse profiling and locate input-loading CPU

[PR #73](https://github.com/jimmy-sim/poker-ai/pull/73) merged at 15546d8 after
both final jobs in [CI 43692243608](https://github.com/jimmy-sim/poker-ai/actions/runs/43692243608)
passed 3,951 tests / 64 skipped / 150 deselected plus the historical warning
per version, in 937.88 / 1176.29 test seconds. Actual Python, NumPy and all uv
versions are checked. GitHub's temporary source and final test-merge trees equal
the complete published PR-head trees; those are distinct commit IDs, not distinct
code. [Full closing evidence](../results/coarse-reader-cpu/final-ci/verified.json)
is retained with this substantive follow-up. Main's saved-data CLI equals the
report; 70 fixtures pass in 3.59 seconds under 3.11.17 / NumPy 2.4.6. All ten
unrelated result edits preserve bytes, status, changed-path index entries and
both patches. Their uncommitted file bytes are not part of this publication.

The [next prospective plan](https://github.com/jimmy-sim/poker-ai/issues/4#issuecomment-6891701494)
precedes implementation and data. [Protocol](reader-load-cpu.md) and sealed config
add three nested input-loader boundaries to the original three, to locate the
47.03% CPU remainder. Preserve all prior 404 source files; the new entry/config
are expected to form 406, to be verified after the source commit. There are 41
pinned inputs. Original 900/1800-second caps, 120-second saving reserve, 4096-call
ceiling, one attempt, runtime/extras and all scientific rules remain unchanged.
The original per-read selected counts must match the coarse capture exactly.

The private implementation reuses the coarse collector under a bounded registry,
target and owned-alias extension. It includes the private command package's
imported loader alias and restores original globals/aliases after success and
failure. The 56 fixtures pass on both versions, and strict focused typing passes;
full source qualification remains pending. No new real audit, optimizer,
policy, default or admission exists at this checkpoint. Journal 120 explains
nested accounting. Codex-assisted; human time and mastery are not inferred.

Source stage in [PR #74](https://github.com/jimmy-sim/poker-ai/pull/74):
8453abd1c5e84604fb19a802f5d2b7c0e232bc71, verified406-file fingerprint
07fd809ecd498154177624eedbf762b277225758f92a852dc5bed4f0499dc4d3.
The two initially interrupted base runs retain their partial logs; only those
incomplete roles were resumed into new files. Both complete local bases now pass
4,007tests/64skipped/150 deselected in815.00/793.63test seconds. The unchanged
optional roles pass519each in61.78/60.44seconds. Actual runtime, physical imports,
source cleanliness/fingerprint, lint, format, strict typing and hooks pass.
Source was pushed after all four local roles completed. Both same-source hosted
jobs, their actual runtimes/tested trees and published qualification/operators
still precede the one measurement. No timed audit has started.

All six source roles now pass at8453abd: [hosted CI43746058432](https://github.com/jimmy-sim/poker-ai/actions/runs/43746058432)
passes4,007tests/64skip/150deselect plus the historical warning each,
904.83/803.24test seconds. Actual3.11.17/NumPy2.4.6 and3.12.15/NumPy2.5.4,
all uv selections and runtime guards are verified. GitHub's actual temporary
checkout e068958 has the same complete tree as the source PR head, with the
distinct commit IDs recorded explicitly. [Qualification](../results/reader-load-cpu/checks.json)
retains untrimmed logs, raw metadata, exact initial/resumed runners and interrupted
logs, assembler and the launch/retention operators. This checkpoint is published
before the one fixed pair. No new audit or training has run.

The single pair completes: control409.6105099580018s,
profiled413.1019390830188s, shared823.8671735420066s, all under the original
900/1800caps. Both child commands return0; the original audit, selected-call
coverage and restoration checks pass. All31pair files and8administrative files
are copied exactly, with originals retained and39hashes verified in the
[raw manifest](../results/reader-load-cpu/raw-manifest.json). This raw publication
precedes posthoc analysis. No CPU attribution, optimization or admission is
claimed at this checkpoint.

Posthoc report: [full result](reader-load-cpu.md#recorded-result--november-15-2026).
The 1,538-call capture preserves all original per-read counts and adds one call
per loader per real read; all hooks restore with zero errors/remaining aliases.
Real-read CPU totals 277.177134 seconds: matrix 18.5299%, spot-tree 10.9012%,
checkpoint 23.9142%, comparison-loader remainder 2.6633%, older-loader remainder
12.5279%, sampled-source remainder 17.6531%, outside 13.8103%. Inclusive loader
times overlap descendants and are not added to these selected-exclusive shares.
The original 432/1,152/three-read/worker/card/scalar witnesses remain identical.
The raw publication `8d6d379` precedes rendering; all 39 raw/admin bytes and
original ignored copies remain exact.

The first Python 3.12 export check fails only `readers.csv`: built-in summation
changes one posthoc residual from 1.4210854715202004e-14 to 0 seconds. Retain its
exact renderer, failed outputs and drafts. Using `math.fsum` in that derived
column produces all five numeric exports byte-identically on actual 3.11.17 /
NumPy 2.4.6 and 3.12.15 / NumPy 2.5.4, with reader/child/tree/loader/scoring/
replay/learner/native execution blocked. Instrument/source, raw data and the
existing arithmetic allowance stay unchanged; no new pair or favorable retry.
Figure inspected. Final optional regressions pass 519 each (19.44/19.39 seconds).
The next candidate is a linear-work depth check in measured matrix construction;
that loop's cost/savings are not yet established. Complete final local and
exact-head hosted checks still precede merge. No training/default/stronger-agent
or failed-forecast admission follows from this measurement. Journal 120 explains
the result and retained export failure. Codex-assisted; personal time unknown.

### November 15 — close loader profiling and test grouped matrix depths

[PR #74](https://github.com/jimmy-sim/poker-ai/pull/74) merged at
efec4e2900b9722bb099f0bf64e1a93d3b8ce356 after both final jobs in
[CI 43749828795](https://github.com/jimmy-sim/poker-ai/actions/runs/43749828795)
passed 4,007 tests / 64 skipped / 150 deselected plus the historical warning
each: 1,181.03 / 760.90 test seconds. Actual Python/NumPy/uv and both source/final
temporary test-merge trees match their complete published PR-head trees.
[Closing evidence](../results/reader-load-cpu/final-ci/verified.json) includes the
untrimmed logs, metadata and verifier. Main's saved-data command equals the
report; 56 fixtures pass in 2.74 seconds under actual 3.11.17 / NumPy 2.4.6.
All ten unrelated result edits retain bytes, status, changed-path index entries
and both patches, rechecked after main verification. Their file bytes are not
published. Closure is archived with this substantive step to avoid a status push.

The [next prospective issue #4 plan](https://github.com/jimmy-sim/poker-ai/issues/4#issuecomment-6899625741)
precedes implementation. [Protocol](grouped-depth-check.md) and sealed config
pin 47 inputs, all prior 406 source files, the original 900/1800-second caps,
one attempt and unchanged scientific rules. A grouped integer depth predicate
replaces only the original constructor's repeated final masks, with an AST-body
guard and complete dataclass/array field witnesses. Expected effective source
count is 409, to be verified after the new entry is complete. Original/grouped
arms must have the same timers and ordered field fingerprints; both complete
wall time and matrix CPU must strictly decrease for the diagnostic cost pass.
Source qualification and a 180-second source-bound software proof precede any
comparison. No candidate timing, speedup or training admission is claimed.
Journal 121 explains groups, depths, exact equivalence and the remaining checks.
Codex-assisted; personal hours and mastery are not inferred.

Initial candidate/runner checks: 128 new fixtures pass; combined with the
existing reader/coarse fixtures, 254 pass under each actual Python version
(12.22 / 12.30 test seconds). Literal-constructor AST equivalence, independent
integer sets, all five encodings, full field fingerprints, aliases/subclasses,
primary exceptions, incomplete/corrupt records and comparison/source/clock/cap
failures are covered. A fictional-qualified software-proof fixture exercises
the retained shape without a reference or trajectory; it is not formal proof.
The saved-data pair fixture preserves a slower candidate's failed cost result.
Ruff lint/format passes 911 files; strict typing passes 764, hooks and 387 focused
relative destinations / five images / anchors / fences pass. CLI help works.
Complete immutable-source local and hosted qualification remains pending;
no real proof, reference comparison or candidate timing has run.

Source [PR #75](https://github.com/jimmy-sim/poker-ai/pull/75):
7311ab4d3c84a2df032f56cdd744e7572de425dd; verified 409-file fingerprint
01dfb1da8ac702c585744b997c77b19e0da1035e6b50c290d955d39766d05ef7.
Both immutable full local bases pass 4,135 / 64 skipped / 150 deselected,
825.92 / 805.02 test seconds; both optional suites pass 647, 56.19 / 54.67 seconds.
Actual runtime, physical imports, head/source cleanliness and fingerprint match
before/after. Initial source push waits for all four local roles. Both hosted
jobs and publication of complete qualification/operators still precede the
formal software proof and its required publication before the one pair.

All six roles pass at 7311ab4. Hosted [CI 43759887855](https://github.com/jimmy-sim/poker-ai/actions/runs/43759887855)
passes 4,135 / 64 skipped / 150 deselected plus the historical warning each,
871.60 / 760.88 test seconds. Actual Python/NumPy/uv and source test-merge
a218b773's complete tree equal the qualified source tree. [Qualification](../results/grouped-depth-check/checks.json)
retains exact untrimmed logs, raw metadata, local runner, assembler and generic
launch/save operators. No formal software proof or pair has run; publication
of this qualification precedes those stages. Source remains 409 files, all
47 pins and original scientific caps unchanged.

Formal software proof after qualification `e40d5e4`: outer command
4.258358540973859 seconds; registered shared 4.2042644579778425; supervised
child 2.367665457975818, all below 180. All 256 generated integer cases plus
eight edges match independent direct sets with unchanged inputs; all five
original/grouped constructor field vectors match. No learner, reference
constructor or new trajectory. [Raw proof](../results/grouped-depth-check/software/proof.json)
and 18-file raw/admin manifest retain exact original/administrative bytes and
published operators; manifest is the 19th file. Publish this evidence before
the single pair. This is not a speedup or a replacement full training-family
software proof; the pair and all later compute/admission requirements remain.

Single pair after proof publication `4915c76`: original 430.3515602090047,
grouped 431.91335204200004, registered shared 866.5069792499999, outer command
866.5707877919776 seconds, all under 900/1800. Both commands return zero;
original audit/field-fingerprint/capture/restoration verification passes.
Grouped wall time is longer, missing that predeclared diagnostic condition.
All 51 raw/admin files are copied exactly and hash-checked, with original
ignored bytes retained; [manifest](../results/grouped-depth-check/raw-pair-manifest.json)
is file 52. This raw publication precedes CPU analysis. No favorable retry,
new policy, optimizer admission or forecast rescue.

Posthoc decision: **diagnostic cost fail**. Grouped wall is +1.5617918329953682
seconds (+0.3629106938%); selected matrix CPU is −0.744592000000182 seconds
(−1.4122152201%). Correctness/coverage passes, but both lower wall AND lower
matrix CPU were required. All 184 whole-child field fingerprints match in order
per arm; both 1,538-call captures, original 432/1,152/three-read/worker/card/
source/scalar witnesses and restoration pass. [Full report](grouped-depth-check.md#recorded-cost-decision--november-15-2026)
includes real-read CPU 287.629979 / 289.543382 and all region/body/worker clocks.
One order is not pure causal savings, uncertainty or a forecast replacement.

First actual 3.12 export fails one grouped comparison-loader CPU remainder:
3.736865999999978 vs 3.7368659999999636 seconds. Retain exact failed renderer,
drafts and difference JSON. Posthoc explicit sequential sums restore 3.11's
association from raw selected rows, checked against the frozen parser's existing
1e-9 CPU-second allowance. All five initial 3.11 exports/figure stay byte-equal;
all five final exports match actual 3.12.15 / NumPy 2.5.4 with poker execution
blocked. No source/raw/tolerance/gate change or capture retry. Source stays409.
Final optional suites pass647each (29.02/28.97seconds). Next question: isolate
observation/key, array, depth-check and witness costs before another optimizer.
Final local report checks and both exact-head hosted jobs still precede merge.
The failed forecast and known-game quality result remain; no new training or
default admission. Journal121 explains the negative result. AI-assisted;
personal hours/mastery unknown.


PR #75 closing verification, November 15: merged `af764a7`. Final
[CI 43764600876](https://github.com/jimmy-sim/poker-ai/actions/runs/43764600876)
passes 4,135 / 64 skipped / 150 deselected each, 882.87 / 882.82 test seconds;
actual Python/NumPy/uv and complete test-merge tree equal report `095204e`.
Main saved CLI equals report; 128 focused tests pass 8.22 seconds. Fresh snapshot
and post-check proof preserve all ten unrelated user bytes/status/changed-path
index entries/both patches. [Closing receipts](../results/grouped-depth-check/final-ci/manifest.json)
are batched here. Negative cost outcome and all scientific failures remain.

### November 15, 2026 — locate phases inside original construction (issue #4)

Question: what fraction of the observed matrix CPU belongs to information/key
creation, array setup, original depth validation, object creation or complete
field witnessing? [Registered plan](https://github.com/jimmy-sim/poker-ai/issues/4#issuecomment-6901801110)
precedes implementation. [Protocol](matrix-phases.md) fixes one ORIGINAL-only
complete audit, unchanged scientific caps and all historical checks, five coarse
intervals per 184 constructors, 2,458 combined selected calls and matching pinned
original field fingerprints. It does not retest the failed original/grouped
cost condition or claim optimization/admission.

Private source-body/phase-boundary checked constructor, serial recorder and
source-bound runner are implemented alongside software/failure fixtures. Preserve
all 409 previous source files and 53 pinned inputs. Source qualification and a
published bounded own software proof still precede actual collection. Expected
synthetic depth rejection stays distinct from failed real data. No new trajectory,
reference training input or numerical outcome exists at this checkpoint.
Journal122 explains the question and an explicitly illustrative example;
AI-assisted, no inferred personal hours or mastery. Full local/hosted checks
and formal stages remain pending.

Implementation check: 93 new fixtures; combined 347 on both supported Python
versions (actual runtimes retained in subsequent qualification). A unit-test
name collision and nonfinite-clock failure handling were corrected before
source qualification, with failed local outputs retained in the workspace.
Ruff lint passes, 916 files formatted, strict mypy passes768source files;
385 focused relative destinations/4images/heading anchors/fences pass.
No formal collection or measurement was performed by these software tests.


Initial [hosted run43768513969](https://github.com/jimmy-sim/poker-ai/actions/runs/43768513969)
fails both runtimes:2failed/4226passed/64skipped/150 deselected plus historical
warning,895.58s311/787.44s312. Both failures are the two new expiry fixtures:
`perf_counter()-2000` can be negative on a recently booted VM. Actual runtime,
every uv selection and complete test-merge tree equal initial source `a459b06`.
[All initial receipts](../results/matrix-phases/qualification-history/initial-a459b06/manifest.json)
retain four local passes, both complete failed hosted logs and raw metadata;
no six-role pass or formal proof is claimed for that head.

Fix only the test clock:positive5000/3000 synthetic timestamps, with explicit
short/long host-uptime cases. Production instrument, original sources,412-file
fingerprint,53pins,caps,seeds,tolerances,gates unchanged. Nine initial targeted
checks pass; strengthened clock regression gives11passed/44deselected. Complete
corrected-head local and hosted qualification is required again before any
formal proof or actual audit. Journal122 records the portability failure.


Corrected source qualification at `f82ae1d0be8099b4c6bd70dd2e78668e8191ffed`
now has all six roles passing. Effective412-file fingerprint
f0b2bdf3bb793cd1645ea60055e37afff6e2e707f4fe7624ef31ce0d97419f6d,
all prior409 files and53pins unchanged. Corrected working-copy combined suites
pass349each27.35/27.13s,95newfixtures; lint916/type768/docs387dest4imagespass.
[Full qualification](../results/matrix-phases/checks.json) preserves all actual
source/role/runtime/uv/full-tree proof and exact generic launch/save operators.
Observed results:

- base311: 4230 passed, 64 skipped, 150 deselected in 874.36s (0:14:34)
- base312: 4230 passed, 64 skipped, 150 deselected in 860.61s (0:14:20)
- optional311: 742 passed in 78.69s (0:01:18)
- optional312: 742 passed in 76.42s (0:01:16)
- hosted311: 2026-11-15T23:08:25.4535929Z 4230 passed, 64 skipped, 150 deselected, 1 warning in 772.88s (0:12:52)
- hosted312: 2026-11-15T23:09:18.5579400Z 4230 passed, 64 skipped, 150 deselected, 1 warning in 811.23s (0:13:31)

The initial local-passing/hosted-failing a459 source remains explicitly
nonqualifying in its original history. This test-clock correction changes no
scientific instrument/config/source fingerprint/cap/seed/tolerance/gate. Full
software suites can exercise toy/fixture solvers; source status lines refer to
formal diagnostic collection, not a claim that no unit test constructs a learner.
Eight synthetic administrative retention fixtures pass without actual poker
collection. Qualification publication precedes the one bounded software proof;
its publication must precede the one actual audit. No formal attempt has run yet.
The933.89/900forecast and2.390%versus1% quality failures remain. Journal122 updated;
AI-assisted, no invented personal hours or mastery.

Formal own software proof after qualification publication `1bffc0f`: outer
4.598493875004351, registered 4.5392701660166495, whole child 2.5236837080155965
seconds, all below180. Five original/phased constructor field vectors match;
positive phase records are complete; both explicitly synthetic depth fixtures
retain the expected ValueError distinctly from actual collection failure.
No learner/reference/new trajectory. [Raw proof](../results/matrix-phases/software/proof.json)
SHA256990a85ca93eddaa367194bfa8ea5523f1eb23b58d5dca13cbbc66f54c73d17ba.
All25raw/admin files and originals retained/hash-checked; manifest is26th.
Publish this evidence before the one ORIGINAL-only audit. Scientific source412,
all53pins/caps/gates unchanged. This is not the separately required production
family end-to-end proof or training admission. Journal122 updated.

Single ORIGINAL-only audit after proof publication `ee4a639`: supervised whole
child 432.06430320898653, registered shared 436.83444570799475, complete outer
command 436.86079670800245seconds, below 900/1800. Outer exits0, uninterrupted.
All original432profiles/1152conditions/three computed reads, worker/card/source/
scalar witnesses, restored hooks and184 pinned ORIGINAL field fingerprints pass.
Five phases184each=920plus1538global=2458<4096. All32raw/admin files retained
and originals exact; [raw manifest](../results/matrix-phases/raw-pair-manifest.json)
is33rd. Publish this complete raw evidence BEFORE phase CPU analysis. Source412/
all53pins remain unchanged. No retry, new training, optimizer/default admission
or production933.89/900 forecast replacement. Journal122 explains capture scope.

Posthoc after raw publication `c4a9141`: information/key CPU44.433599 of
52.715310observed matrix seconds,84.289742%; original depth1.292698(2.452225%),
field witnessing1.403231(2.661904%). Two archived-policy reads total288.672415CPU;
matrix18.261291%,key15.392395%. Inclusive/exclusive global ledgers,920phase CSV
rows, two-read stacked plot and disjoint constructor/wrapper remainders retained.
No parent/child CPU double count. Whole original body/nearby-child and all three
parallel comparison-worker clocks/resources are in tables; workers not summed
into elapsed. [Results](matrix-phases.md#recorded-cpu-result--november-15-2026).

Posthoc constructor-encoding classification:exact68calls,key0.986307CPU;
public_b816calls,key4.966956;texture_b8100calls,key38.480336. These are constructor
fields with different inventories, not causal encoding-speed or strategy-count
comparisons. Separate rerunnable extraction and raw-bound manifest retained.
Actual3.12.15/NumPy2.5.4 reproduces all six numeric exports and encoding CSV
byte-for-byte with builder/reader/child/supervisor/scorer/replay/learner/native
execution blocked. Explicit legacy3.11 sequential CPU association stays within
frozen1e-9 arithmetic allowance; phase aggregation math.fsum; no changedraw,
tolerance,caps,seeds,gates or recapture. Figure visually inspected.

Final relevant suites742each pass; exact logs/timings retained in report. Source
remains412FPf0b2…/all53pins; original25software and32audit raw/admin files and
ignored outputs preserved. No full-game strength/new training/default/fresh/global
admission or933.89/900forecast rescue. Next prospective question:replace repeated
card-suit arithmetic with a fixed exact lookup, requiring independent equivalence
and complete cost proof before any production integration. Journal122 updated;
final local verification and exact-report-head hosted checks precede merge.

Final local verification passes:742relevant tests each40.53/39.27s, source/
raw/original-copy/initial-failed-CI retention proof, actual3.12portable exports,
CLI base fields equal report (report adds derived read/matrix aggregates),Ruff916,
strictmypy768,hooks and409focused destinations/5images/anchors/fences.
[Local receipt](../results/matrix-phases/report/local-verification.json) records
actual scope and remaining exact-report-head hosted requirement. No source or
scientific criterion changes; no new trajectory. Publish coherent report, then
both hosted jobs must pass before history-preserving merge.


PR #76 closing verification: both final hosted jobs in run43776395105 pass
4,230/64skip/150deselect, actual 3.11.17/2.4.6 and 3.12.15/2.5.4 runtimes and
complete tested tree verified. History-preserving merge26e0c8c; fresh snapshot,
guarded main FF and actual3.11 saved CLI base/report equality plus95fixtures
(14.29s) pass. All ten unrelated user paths' bytes/status/index/patches remain
exact after checks. [Closing receipts](../results/matrix-phases/final-ci/manifest.json)
are batched with this next substantive implementation; no status-only commit.

## 2026-11-15 — Exact suit translation lookup, prospective implementation

Issue #4 [plan](https://github.com/jimmy-sim/poker-ai/issues/4#issuecomment-6903489482)
precedes new code. [Protocol](suit-lookup.md) and60-pin sealed config: preserve412
prior sources, add3 for415. Fixed24x52 translations replace repeated arithmetic,
not card-result memoization. Both modes share eligibility/dependency/counter hooks,
original uncached card wrappers and full constructor-field observer; native workers
keep original code. No production algorithm, dependency, CI, seed or old gate change.

Focused163 software fixtures pass; Ruff/format and strict types pass on new files.
Coverage includes1248entries,1326preflop pairs, property boards, exceptions,
unsupported/dependency fallbacks, aliases/counters/PID/thread/primary interruption,
expired budgets, complete saved-data proof shape and rebound-kernel corruption.
Fictional fixture qualification is not actual formal qualification or a measurement.
Complete immutable-source local base/optional roles and both hosted roles come
before published exact operators/receipts, then one180s own proof publication,
then one original/lookup pair900each/1800shared/120failure-saving. No actual audit
or timing claim yet. Journal123 explains the question in plain English; Codex-
assisted work, human time not recorded. Preserve prior failed outcomes and all
unrelated user main bytes. Full cost and subsequent production/quality gates remain.


A final accounting review adds the exact lookup rule: every original evaluation
in lookup mode must be a fallback. Two new regression cases fail before the
parser correction; four additional fixtures then pass with the full 167-test
focused set. The four in-progress local source roles were interrupted and are
[retained as nonqualifying](../results/suit-lookup/qualification-history/superseded-d3e60b2/superseded.json).
No formal proof or actual audit had started. Qualification restarts on the revised
immutable source; the algorithm, config, scientific caps and seeds are unchanged.


Exact-source qualification now passes on published source53fbdf10: effective415
files, FPfc3d73cd6365bfc440230ad3b0596add01001731e72c04a38766ed117858058b;
all412 previous sources/all60 config pins unchanged. Full local bases each4397/
64skip/150deselect,885.69/867.35s; optional909each91.99/89.38s. Full lint/format,
strict types772, hooks and post-check source/runtime guards pass. GitHub source
run43783661537 both4397/64skip/150deselect+existing warning:311911.12s,
3121312.17s. Actual Python3.11.17/NumPy2.4.6 and3.12.15/2.5.4, all uv selections,
both actual checkout logs and complete temp-merge tree verified against53fbdf10.
CI durations are software checks, not actual child900-second measurements.

[All six receipts](../results/suit-lookup/checks.json), full untrimmed logs/raw
metadata, tested-tree record and exact launch/save operators are retained. Eight
fictional administrative routing fixtures pass; all4398 software-input hashes
match across actual311/312 with canonical/game/learner/native execution blocked.
These extra checks are not actual proof/audit evidence or bit-exact real-trajectory
admission. First publish qualification/operators, then the formal180-second own
software proof. No actual timing pair, retry or new training has occurred. Existing
production forecast and strategy-accuracy failures remain. Journal123 updated;
[PR #77](https://github.com/jimmy-sim/poker-ai/pull/77) keeps the coherent milestone.


One formal own software proof after qualification89be152: complete outer
5.307256125001004s, registered5.236114416999044, whole supervised child
3.0092819170095026; exits0/uninterrupted under180. All1248table entries,
4398valid cases each,17fixed behavior cases each and5complete constructor fields
match. Valid/builder scope10970requests each, original10970BASE vslookup10970LUT,
no fallback/error; fixed unsupported/error calls separate precise receipts.
No learner/reference/new trajectory. [Proof](../results/suit-lookup/software/proof.json)
SHA2560362d13b0bead0ec06685a09171652fbb282266b56a64d71857535d60f4b6259. All57raw/admin files+ignored originals exact, manifest58th.
Publish own proof BEFORE actual original/lookup pair. No timing retry, changed
source415FPfc3/all60pins/caps/seeds/gates or production/quality admission.
Journal123 updated; this is not the separately required production-family proof.


ONE complete original/lookup pair after ownproof0b4203c: outer850.8070003750036s,
registered850.7695943330182s, under1800; both whole children under900, exits0,
uninterrupted. No retry/seed/cap/gate/source change. Parent validation passes all
original432profiles/1152conditions/3reads/worker/card/source/scalar identities,
equal request/fallback counts and184pinned ORIGINAL constructor fingerprints each.
Global1538each/3076combined<4096; no920phasehooks. All53raw/admin files+ignored
originals retained exact, [manifest](../results/suit-lookup/raw-pair-manifest.json)
54th. Publish this raw evidence BEFORE posthoc cost/CPU analysis. No diagnostic
cost verdict or production/quality/default/fresh/global admission yet. No new
own policy/real trajectory trained; reference outputs comparison-only. Journal123
updated with observed scope and next decision.


Posthoc after raw59ff388: cost diagnostic PASS, original/lookup whole supervised
wall423.3883260829898/420.99904466600856s (observed0.5643238771%lower);
selected matrix CPU53.6667260000001/51.90405599999999s (3.2844746296%lower).
All correctness/counters/coverage/source/184FPs remain exact;918104requests each,
original918104BASE vslookup918104LUT,0fallback/errors. Native code unchanged.
Small one-point benefit, not stable causal/runtime/population/production admission:
unchanged parallel workers also ~1.65squicker, not added into wall. Both own read
CPU totals remain similar. [Report](suit-lookup.md#recorded-cost-result--november-15-2026)
retains full clocks/6numeric exports/2zero-based inspected figures and exact code.

First312export failed BEFORE numeric generation: generic work/data-only-render312.log
already existed. Unhandled FileExistsError retained with empty stdout; outer shell
last tail returned0, not a passed verifier. No separately captured Python exit
status invented. Original verifier/log/error and failure metadata/manifest retained.
Corrected verifier uses unique log, preserves old bytes, and all6numeric exports
match actual3.12.15/NP2.5.4 byte-for-byte with poker execution blocked. No actual
poker retry/raw/cap/seed/gate/source change. Matplotlib temp-cache notices retained.
Final relevant909eachPASS53.68/53.43s, source/runtime guards retained. Journal123
updated. Next prospective question: private-hole minimum/tied-suit candidate
factorization, independently proven before any new cost study. No production/
new-trajectory/default/quality admission;933.89/900and2.390vs1failures remain.


PR #77 closing verification: both final hosted jobs in43789578292 pass4397/
64skip/150deselect+existing warning (902.83/783.30s), actual Python/NumPy/alluv
and complete source/report test-merge trees verified. History merge63535047;
fresh snapshot+guarded main FF, saved CLI==report and167fixtures12.58s pass.
All ten user paths' bytes/status/changed-path index/bothpatches preserved AFTER
checks. [Closing11raw+manifest12](../results/suit-lookup/final-ci/manifest.json)
are batched with this substantive source. Issue4 remains open, no production or
strategy-quality admission from the small cost diagnostic.

## 2026-11-15 — Private-minimum suit factorization, implementation

[Prospective issue4 plan](https://github.com/jimmy-sim/poker-ai/issues/4#issuecomment-6905294880)
before code: exact lex minimum min(H_p,B_p)=(h*,min B_p over H_p=h*). Controlall24
LUT vs reduced tied maps, identical guards/fields. Static52x52 ordered-hole table,
52duplicate sentinels/2652valid slots, tie counts2:1872/4:156/6:624. Fresh private/
outer tuples, original validation/fallback and alias/primary-failure restoration.
All415 earlier scientific files preserved; add entry/support/config for418,68pins.
ConfigSHA593072acc4d94403378675dc7550131e75373a1f159c5f04a9337edbf007cb09,
geometrySHAf1cf3685244285e88220e82b5c274fd96b12f07acf4cd17a106bf079ce2cfc8d.

Focused189development fixtures pass33.61s on actual311/NP246; lint/format/strict
new-file types pass. Fictional qualification in own small-builder/data-parser
fixtures is not formal source qualification or a new actual audit. Tests cover
allorderedholes/ties/suit-inputproperties/invalidcalls/dependencies/counters/
restoration, source/caps/publication/preconditions/failures and original/all/reduced
software record parsing. Four rebound-schema regressions catch bool/int equality
before the fix, four other new cases already reject; canonical typed comparisons
then reject all and the full focused set passes. No algorithm/cap/seed/gate change.

[Protocol](suit-candidates.md) fixes full6-role qualification and operatorPUB,
one180s own proof (all2704geometry/1248translation entries,5724valid original/all/
reduced cases,17fixed outcomes each,5fullbuilder encodings each), proofPUB before
ONEall/reducedpair900each/1800shared/120save. Shared software-only seed20261502,
all historical poker RNG/caps/gates unchanged;1538timers each3076<4096, no phase/
dense profiling. Current code is a private experiment only; no actual proof/pair
or timing result yet. Journal124 explains the math and parser fix; AI-assisted,
human time not recorded. Full production/fresh/default/quality admission remains
separate; old933.89/900 and2.390vs1failures preserved.


Both actual31117/NP246 and31215/NP254 focused sets pass189 (33.61/31.94s).
Full-project Ruff lint/format926, strictmypy776 pass; focused relative links,
anchors/fences and images pass. All415prior sources/68pins/11PR77closing raw
receipts remain byte-exact. Implementation/config/data checked before source
freeze. Complete immutable-head local base/optional roles and both source-bound
hosted roles still required before any formal proof/capture. No actual new timing
or quality claim; source-only publication will wait for all four local roles.


All6exact-source roles pass at3a15a53/418FP8fd42fd8ae4f18461a5646b46e3ec8b7da4ff62352dfbf2e6878fed8e5deec1a.
Local full4586/64skip150deselect930.76/900.93s; optional1098each130.47/125.67s.
Hosted source43796168210both4586+existingwarning,3111002.91s/312856.88s. Actual
Python3.11.17/NP2.4.6 and3.12.15/NP2.5.4, alluvselections, actualsourcecheckout
91d9def5 andcompleteTREE1f0fc8d310444c70a206ca013a3a06718b6fc669==3a15 checked.
[Six-role record](../results/suit-candidates/checks.json) retainsfulluntrimmedlogs,
rawAPIobjects, guardsandEXACTlaunch/saveoperators. All415earlierfiles/68pinsunchanged.
EightfictionalroutingfixturesPASS;5724softwareinputhashesmatchbothactualruntimes,
noactualkernelrequests/game/learner/native/trajectory (staticgeometrymetadatamayinit).
Theseextrasnotformalproof/data; fullsuitescanexerciseTOY/fixturelearning,notactual
completereal-audittarget/newrealtrajectory. Publishqualification/operatorsBEFORE
ONE180sownproof. Noactualnewtiming/stronger/default/fresh/global/productionadmission;
alloldforecast/accuracyfailuresretained. Journal124updated.


ONEformal own proof afterqualificationd62b657passes: outer6.4555765409895685s,
registered6.42996020798455, supervised3.901490958989598, under180/exits0/nointerrupt.
All1248translation entries/2704geometryslots independentlymatch;5724valid+17fixed
peroriginal/all/reduced;all5fullMatrixfieldseach=15witnessesmatch. Variantvalid/builder
12296requests each,allwithdeclaredkernel,0fallback/errors. Originaldirectbaseline
recordsactualowncalls/owner/fields,notexternalref/nofakekernelcounts; expected
negativefixedcasesseparateprecisereceipts. No learner/reference/newtrajectory.
[Proof](../results/suit-candidates/software/proof.json)SHA256
1dee6b09d999df3b68c93c0e9b5e1ed07d8c08eef8ea02acc6a50da695c5e364.
62raw/adminfiles+manifest63andignoredoriginalsretainedexact. PublishBEFOREactual
ONEall/reducedpair. All418FP8fd/68pins/caps/seeds/gatesunchanged; noactualnewcost
verdict/production/fresh/default/qualityadmission. Journal124updated.


November 15, 2026 — The one registered suit-candidate audit pair completed:
outer command 829.4326407079934 seconds, both children successful within the
900-second child/1,800-second shared limits, no interruption or retry.
`verify_pair` validates original identities, fields, source, card/worker checks
and saved records. Both raw manifests remain exact. Retained 53 pair/admin
files plus manifest and their ignored originals. Publish this raw checkpoint
before cost analysis. Scientific source, seeds, budgets and admission rules
remain unchanged; no production or new trajectory admission. Journal step 124
records this stage.


November 15, 2026 — After raw publication da0dc24, the declared diagnostic cost
checks pass: complete supervised wall 413.8943964159989 -> 408.68608008301817 seconds
(1.258368% lower), selected exclusive matrix CPU 50.67445900000007 -> 43.54697200000005
(14.065245% lower). Both184 original constructor witnesses,432profiles,
1152conditions,3reads,918104 declared-kernel requests/zeroerrors/fallbacks each;
1538 timers each3076combined<4096. One ordered pair, identical instrumentation,
all-candidate LUT control, unchanged-worker variation disclosed. No stable causal
speedup/production forecast or strategy-quality claim. Both zero-based figures
visually inspected; actual31215/NP254 six numeric exports byte-identical with
execution blocked. Standalone illustrative suit-tie viewer added with the report,
not a scientific collector dependency. Journal124 updated. Separate production
qualification/full proof/all3own before freshnative/all3costs/forecast/admission
remain mandatory; historical failed gates are retained.


Final relevant regressions: 1098 pass on actual311/NP246 in92.44s and312/NP254
in90.54s; guarded commands including startup95.107988/94.013639s. Full Ruff
lint/format927, strictmypy777 andhooks pass;439relative destinations/7images/
anchors/fences pass. CLI equals report,418scientific files/68pins/raw manifests/
ignored originals exact. Eight illustrative viewer cases pass both runtimes.
Initial viewer E501 resolved by splitting one output string; failure log retained.
First posthoc verifier expected51hook restorations incorrectly; retained failure
and exact operator, then v2 verifies34variant restorations plus all51fixed
outcomes and truthful unhooked original baseline. No collection retry. Final
exact-report-head hosted jobs remain required before merge.


## 2026-11-15 — Exact normalization in complete validation, in progress

[Prospective issue4 registration](https://github.com/jimmy-sim/poker-ai/issues/4#issuecomment-6906832663)
precedes new compact_suit adapter code. Separate parent-only exact factorization
plus original recall caching; training/native workers retain original canonical
code. All418 predecessor sources remain unchanged; the current adapter inventory
extends this to433. New contract SHA443f6a78b7d58bdf9c758bc5f31de31dacd9022a6698b11b3cce64bebc4bf2b0.
Original science, seeds, work, caps, strict formulas and quality gates unchanged.
Source metadata is read from a pinned own proof anchor rather than importing the
diagnostic runner into a reference-free training worker. Fresh subprocess checks
validate the complete source with inactive worker normalization.

Initial38 focused tests pass1.03s: role isolation, live/final restoration,
unsupported/dependency fallback, counter typing, source coverage, worker imports,
unchanged forecast AST and old failed-admission refusal. Card-contract and full
pipeline integration/failure tests remain in progress. New own-only card dispatch
proof is required inside the same180s software command before reference use;
actual software/cost/forecast/admission collection has not started. No new real
trajectory or strength result. Journal125 explains why tiny games alone cannot
exercise the card optimization. AI-assisted; human time not recorded.

PR78 final CI43800671628 passes4586/64skip150deselect+existingwarning both,
978.25/696.45s; actual Python/NumPy/alluv and full source/report trees verified.
History mergee8018609, fresh guarded main update, CLI==report and189tests35.42s.
All10user bytes/status/changed-pathindex/bothpatches preserved AFTER verification.
[Closing11raw+manifest12](../results/suit-candidates/final-ci/manifest.json) retained
with this next source increment; issue4 remains open.


All75 focused tests pass actual311/NP24610.06s and312/NP25410.37s. This includes
fresh three-worker own tiny capture and original324/216/30 vector parity with
independent terminal/pure-choice oracles; optional unit native432/1152 matches
unchanged tolerance with original worker normalization. Mocked source/publication
fixtures remain nonqualifying; no formal own/reference/cost/study run yet.
Production card fixture5724/17/five complete builder encodings passes; rebound
schema corruptions/data-only parsing/partial and existing-output preservation
checks pass. Initial serializer-whitespace failure retained; fixed to preserve
original input bytes. Cleanup-overwrite risk found in review, fixed by early
refusal plus last-write ownership binding, covered by new regression tests.
Formal operators must register pre-Python origin; complete clocks bind observed
child PID, real archive costs/replay require original31117/NP246. Source433files,
all418 prior bytes unchanged. Ruff lint/format947 and strictmypy796 pass.
Installed OpenSpiel2.0.2 Apache2.0 license read before optional comparison; pinned
license and comparison-only scope preserved. All four immutable local roles plus
both exact-source hosted jobs remain required before formal evidence. Journal125
updated; source publication will wait for complete local checks as requested.


November 15 — Premeasurement boundary review: the initial local cohort at
`d6f0fa5` passes both full suites (4,660/65 skipped/150 deselected;
971.48/944.20 seconds) and both optional suites (1,563; 549.18/483.40 seconds).
It is retained as superseded local software evidence, without hosted checks or
formal collection. Final execution-counter, role and restoration validation is
now charged inside the child command before its final receipt write. A new
regression rejects inconsistent final accounting before completion is written.
Both focused revisions pass 76 tests (10.94/11.14 seconds); direct private-module
pytest imports are explicit. All four local roles and both hosted roles must be
repeated on the revised source before any formal proof or production cost.
No scientific cap, seed, mathematical result or acceptance criterion changes.


November 15, 2026 — All six source-check roles pass on `066f522` with the same
433-file fingerprint. Both full local suites pass 4,661 tests (65 skipped,
150 deselected; 988.95/963.24 seconds); optional suites pass 1,564 each
(565.55/499.07 seconds). Both GitHub source jobs in run `43809812112` pass 4,661
with the existing warning (1,284.07/866.26 seconds). Actual Python/NumPy, every uv
selection, checkout and whole tested tree are verified. The earlier cohort stays
superseded. The exact launch, retention and publication instructions and their
19 subprocess/file checks plus four mocked publication-order cases are retained.
Publish these receipts before the single fresh shared-180-second software proof.
No formal proof, production cost or new registered Hold’em study has run yet.


November 15, 2026 — software-own: complete raw capture. The complete command reports 6.797211083001457 seconds. Own evidence is published before the independent constructor. This is software evidence, not new Hold’em training or strength admission.


November 15, 2026 — software-audit: complete raw capture. The complete command reports 6.631517209025333 seconds. Independent output is comparison-only; complete proof verification still precedes costs. This is software evidence, not new Hold’em training or strength admission.


### Own proof and all three complete own costs — November 15, 2026

The fresh shared software proof passes in 24.288505792006617 seconds, including
own publication before the independent constructor. Own and native commands
take 6.797211083001457 and 6.631517209025333 seconds. All original toy histories
match; the native scalar comparison covers 432 profiles and 1,152 fixed conditions
with maximum error 1.1102230246251565e-16 fixture chips. The production card
contract passes all 5,724 inputs, 17 fixed cases and five full builder encodings,
with 12,296 reduced calls, no fallback/error and final restoration.
[Saved verification](../results/compact-suit-learning/software/verified-publication.json).

All three fresh own-cost repetitions complete: 182.12105958300526,
184.0667208750092 and 186.84964237501845 complete-command seconds, each below
900. Their supervised outer clocks are 182.54452658299124,184.4868316249922
and187.26981083399733 seconds. Each includes original stand-in creation, full
own math replay and all six report files; 432 profiles/1,152 conditions replay
with zero error and exact policy/ledger bits, 459,052 reduced calls, no
fallback/error and restored aliases. These are cost stand-ins with zero new
learning, not a measured improvement in strategy quality.

Publish all 66 raw/admin members and three manifests together before any fresh
native cost constructor. [Raw publication checks](../results/compact-suit-learning/own-cost-raw-verification.json)
verify bytes against ignored originals, saved replay/accounting, source and caps;
they do not perform another mathematical replay or a comparative cost analysis.
The first posthoc checker failed on an import before producing evidence; its
[history](../results/compact-suit-learning/checks/posthoc-own-verifier-history/failure.json)
and corrected operator remain available. No collection was repeated.

Next: all three complete independent costs, then publish them before the original
maximum-based forecast. The old budget and accuracy failures remain current.
Source, seeds, caps and acceptance criteria are unchanged. Codex-assisted; human
hands-on time not recorded.


### All three complete independent costs — November 15, 2026

The fixed native repetitions complete in 390.69778079201933,
393.7666274170042 and 396.27123320801184 seconds, below their 900-second caps.
Supervised outer clocks are 390.8178977500065,393.85517862500274 and
396.3754958329955 seconds. Each retains both complete own replays, original
worker loads, source/publication/license checks and final writes. All 432 profiles
and 1,152 fixed conditions agree with maximum error 1.8474111129762605e-13 chips.
Each parent records 918,104 reduced calls, zero fallback/error and final restoration;
all three spawned workers retain original normalization. Outputs are comparison
scalars only, with no training or exported reference actions.

All three own grids were published together at d8d514e before any native cost.
Their exact publication inventories pass again with a clean unchanged 433-file
source before retention. The 33 native raw/admin members, three manifests and
ignored originals match. [Raw validation](../results/compact-suit-learning/native-cost-raw-verification.json)
checks saved workers/scalars/journals/accounting/bytes and clocks; it is not an
additional full own mathematical replay. Publish this complete batch before
posthoc cost analysis or the fresh full forecast. No favorable retry, cap/seed
change, new poker trajectory or admission. The original failed budget and quality
results remain intact.


### Complete forecast: independent budget still fails — November 15, 2026

The full forecast command completes in 412.56740954099223 seconds (supervised
outer 412.6018629579921), below its 900-second command cap. It replays the tiny proof
and all three complete own archives, validates the independent records and all
127 sealed inputs, and rebuilds the original kernel-geometry check. Its 11 raw/admin
members and manifest match ignored originals; the 433-file source is unchanged.

The unchanged maximum-based calculation yields T=610.943356249918,
D=186.84964237501845 and N=396.27123320801184seconds. Own forecast
`2*(2*T+D+600)=4017.472709749709 < 7200` passes. Independent forecast
`2*(N+60)=912.5424664160237 < 900` **fails**. This is a completed calculation with
a failed budget criterion, not a failed replay. No admission or new real
trajectory is attempted. [Complete forecast](../results/compact-suit-learning/forecast.json)
and [raw manifest](../results/compact-suit-learning/raw-forecast-manifest.json)
retain the unfavorable result. The historical 933.889393168007/900 and
2.390%-versus-1% failures remain intact. Different runs/sources do not establish
a causal speedup or a playing-strength improvement.

Next: finish the saved-data terminal report/plots, portability and final local
and hosted checks, then investigate remaining validation cost using measured
evidence. No changed cap, safety margin, seed, accuracy criterion or default.


November 15 — Saved-data report added with four integrity/isolation tests passing
both actual runtimes (6.09/7.30s), lint/format and strict types. Complete six costs
and both strict forecast outcomes print without numerical execution. All three
numeric exports match byte-for-byte actual31117/NP246 vs31215/NP254 with execution
blocked; two zero-based plots visually inspected. Initial rendering in base
environments lacked Matplotlib; partials/operator retained, then existing locked
research environments render successfully to fresh folders. The first code commit
hook could not find uv before the project environment was sourced; hooks then
pass. No scientific collection repeated or source433byte changed. Final relevant
local/optional and exact-report-head hosted checks remain required before merge.


Final local report checks pass on immutable 31da1f8: both full bases 4,665 / 65 skipped /
150 deselected (1,088.97/1,075.45 seconds), relevant optional 1,568 each
(642.57/578.45 seconds). All runtime/root/source guards pass before/after;
lint/format 949, strict mypy 798 and hooks pass. [Exact four-role logs](../results/compact-suit-learning/final-regressions/manifest.json)
retain the operator and actual commands. The 433-file scientific source remains
unchanged. Both final exact-report-head hosted jobs still precede merge.

The saved-data audit additionally blocks actual MatrixTree/SpotTree constructors,
ScoringContext.score, defining canonical/lookup functions, internal replay and
reference audit, alongside the earlier entry-point guards. All three numeric
exports remain byte-identical in both actual environments and to the original
report. [Supplemental execution guards](../results/compact-suit-learning/report-execution-guard-v3-manifest.json)
retain this check without replacing the earlier report or its partial failures.


## 2026-11-15–16 — Shorter project introduction and reading paths

[Issue #80](https://github.com/jimmy-sim/poker-ai/issues/80) follows Jimmy's request
for clearer, shorter documentation with a personal project voice. The README
now leads with the research questions and a recorded river-decision example; its
handwritten overview is 719 words, down from 1,013. Journal navigation, roadmap
and work-log introductions, and interview wording were tightened. Intentions use
first person where supported; implementation history and AI-assistance credits
remain factual. No new personal practice, discoveries or hours are inferred.

Local checks pass: 456 relative destinations, 57 incoming anchors, eight image
references, Markdown fences, GitHub README rendering, and four existing generator
update functions exercised only on disposable copies. Generated README content,
historical journal/log entries, phase contracts and all 433 scientific source
hashes remain unchanged. Hooks and diff checks pass; required hosted CI still precedes merge. The existing About description already fits; package metadata remains
untouched. Research in issue #4 stays paused; this is an editorial change.


## 2026-11-16 — Checkpoint-replay observer and correctness tests

Issue #4 resumes from main `472662d`, after PRs [#79](https://github.com/jimmy-sim/poker-ai/pull/79)
and [#81](https://github.com/jimmy-sim/poker-ai/pull/81). PR #79's two final hosted
jobs passed 4,665 tests each, with 65 skipped and 150 deselected, on verified
Python 3.11.17/NumPy 2.4.6 and Python 3.12.15/NumPy 2.5.4; whole tested trees
matched the PR head. [Closing receipts](../results/compact-suit-learning/final-ci/manifest.json)
are retained in this implementation batch. PR #81's documentation checks also
passed before its merge. The ten unrelated user result changes were freshly
snapshotted before this isolated branch; their files remain untouched.

The [registered checkpoint investigation](checkpoint-replay-cpu.md) adds a
parent-only observer at the current own-archive callsite. It separates decode,
score and residual CPU without changing the reusable replay function or old
scientific source. Partial records retain original failures, and even failed
native outputs are marked as diagnostic. The saved-data reader checks the
complete ledger, raw files, producer identity and outer clock boundaries.

The initial regressions caught seven draft failures; retained development logs
record these rather than a successful first attempt. All 134 focused tests now
pass on Python 3.11.17 (25.45 seconds), and strict types and focused lint pass.
Eight actual tiny checkpoint cases use independent terminal/pure-choice math.
Complete immutable-source local/optional and hosted checks still precede formal
proof/measurement. No fresh reference, real trajectory, budget change, stronger
strategy or default promotion is claimed. Journal step 126 explains the question.


The first immutable local cohort on `04dbb78` passes all four roles: bases
4,799 / 65 skipped / 150 deselected each (626.73 / 598.87 seconds), and optional
1,702 each (315.51 / 252.07 seconds). Runtime/root/source guards and hooks pass.
[Raw logs and exact operator](../results/checkpoint-replay-cpu/qualification-history/pre-report-output-04dbb78/manifest.json)
are retained as a superseded cohort, before hosted checks or any formal run.
Review added a separate report-output destination to make re-rendering possible
without removing existing results. Two regression tests check routing, byte-equal
numerical exports and raw-input preservation. Focused tests pass 136 / 23.73
seconds; lint/format and strict types pass. Corrected-source full local/optional
and hosted checks precede collection. No original scientific byte or gate changed.


November 16 — All six corrected source roles pass on `899ad05` / source436
`81ea769018500d50c2dfcc48b0ced099d6fe424c8cff7f235540f14620da32ca`.
Local bases 4,801 / 65 skipped / 150 deselected each (621.86 / 594.09 seconds);
optional 1,704 each (311.83 / 252.73 seconds). Hosted run
[43844976093](https://github.com/jimmy-sim/poker-ai/actions/runs/43844976093) passes
both jobs, 4,801 each with the same skips/deselections and existing warning
(1,076.80 / 1,425.28 seconds). Actual patches/NumPy, all uv selections and entire
GitHub merge tree `55ff96dc6859bd558e5d24a1c2533fc5a2c95c62` equal the source head.

[All six raw receipts](../results/checkpoint-replay-cpu/checks.json), exact executed
launch/retention/publication operators and all process/filesystem/schema fixture
archives are published at this boundary, before the fresh own-only proof.
BOMs and original log whitespace remain intact. Six real process cases, four
synthetic retention cases and ten synthetic publication cases pass. No formal
proof, cost pair or new poker trajectory has run. Original seeds, caps and
failed budget/accuracy results are unchanged. [PR #82](https://github.com/jimmy-sim/poker-ai/pull/82)
remains open through the required evidence and final checks.


November 16 — Fresh own-only observer proof captured after public six-role
qualification `67b8b82`. Complete CLI 0.9871026249893475 seconds; complete inner
child 0.920909083011793 seconds, under 180. Eight actual tiny checkpoint cases,
three reads / 72 selected calls, independent maximum error 0.0, original and
instrumented results exact, hooks fully restored. Reference construction and
poker training flags remain false. [All 13 raw files and clocks](../results/checkpoint-replay-cpu/software-raw-manifest.json)
are retained in this own-before-reference publication. Saved-publication
verification still precedes the fresh cost-audit pair; no real trajectory or
production-cost admission follows this software proof.


November 16 — The single registered audit pair completes after the own proof
was public at `0533b61` and its saved-publication verification passed. All code,
Git head and inputs stayed fixed; local heavy checks stayed idle during capture.
Ordinary / instrumented complete-child clocks: 391.30728316598106 /
395.89443708298495 seconds, each under 900. Outer whole CLI
788.0160884579818 seconds under 1,800. All three reads, 432 profiles / 1,152 fixed
conditions, exact full scalar/computed-replay identity; profiled inventory
3,888 selected calls, final restoration true. Both receipts reject base-family
admission. [All 27 raw files](../results/checkpoint-replay-cpu/pair-raw-manifest.json)
and the earlier [published-own verification](../results/checkpoint-replay-cpu/proof-published-verification.json)
are retained in this raw publication before analysis. No new Hold'em training,
production forecast or stronger/default promotion. Full saved-pair verification,
report, blocked 3.12 exports and final checks remain.


November 16 — Published-pair verification passes, including raw inventories,
original ignored-byte equality, outer/inner clock bounds, producer IDs, all
workers/journals, full identity and the earlier own-proof blob in the capture
revision. Saved report renders both figures. Cost reads before / after reference
(CPU seconds): decode 1.253207 / 1.134554; score 23.423215 / 23.743813; other
checkpoint 7.680944 / 8.740500; outside selected root 97.371116 / 97.969336.
Every read is retained; [CSV/JSON and figures](../results/checkpoint-replay-cpu/pair/report/summary.json)
come from the unchanged saved-data entry. Most current whole-read CPU remains
outside this callsite. Next diagnosis should split current loader/replay phases
before choosing an optimizer; no causal/stable timing or production-admission
claim follows this pair.

Both actual runtimes regenerate all three numerical files byte-identically with
34 defining/captured game/kernel/replay/reference entry points blocked, plus
parent learner/reference guards. No forbidden call occurs and published inputs
stay unchanged. The first guard failed before report execution during descriptor-
sensitive import setup; its exact code/logs remain. The corrected guard preloads
static metadata and preserves class-method descriptors. [All guard receipts and
visual review](../results/checkpoint-replay-cpu/report-verification/manifest.json)
are retained. Both actual figures inspected; all axes/labels readable. No
collection source/data changed or measurement rerun. Final local/optional and
exact-report-head hosted checks remain before merge.


## November 16 — checkpoint measurement merged; reader phases registered

[PR #82](https://github.com/jimmy-sim/poker-ai/pull/82) history-merged at
`9a445959fd449c838ac5286c25146b96bfc1aa31`. All six final roles bind head
`32ab60d`: bases 4,801 passed / 65 skipped / 150 deselected (621.20 / 595.10s),
optional suites 1,704 each (319.14 / 260.44s); hosted workflow 43855113726 passes
both jobs (1,397.57 / 922.57s tests), with the existing 8.88e-16 historical
roundoff warning below 1e-12. Actual Python/NumPy/all uv and entire tested tree
`5c1b29e19b078ab51441db9b25684f2b161c2dc8` verified. Actual main 3.11.17/2.4.6:
136 focused tests pass in 19.58s; complete saved pair authenticates, all three
numerical exports byte-identical. Fresh snapshot/guarded fast-forward and
post-check verification preserve all ten user result bytes, status, changed-path
index entries and both patches. [Full closing receipts](../results/checkpoint-replay-cpu/final-ci/manifest.json)
are batched here, without a status-only commit or retrospective source admission.

The [next phase-CPU question](https://github.com/jimmy-sim/poker-ai/issues/4#issuecomment-6914870507)
was public before implementation: seven named source-load/stand-in-load/replay
calls across the original three complete reads, with a fixed 16-call cap. All
436 preceding scientific files and historical results stay unchanged. New private
observer/runner/config use a separate source identity and output namespace.
Thirty-five observer tests pass on each actual runtime; the first 27 runner tests
pass on 3.11. They distinguish actual archived fictional-game replay from
synthetic loader forwarding. Saved-pair clock checks also require individual
worker duration to fit within its enclosing body and both child executions to
fit the shared clock. These are software checks, not formal phase results.
Complete source checks, published own proof, raw-before-analysis pair and final
verification still precede any result or merge. Fixed 180/900/1,800-second caps,
120-second failure retention, seeds, math and admission criteria stay unchanged.

The production 912.5424664160237 / 900-second forecast and 2.390% / 1% accuracy
gates remain failed; no fresh trajectory, stronger/default/fresh/global claim or
optimizer follows these fixtures. Learning journal step 127 explains the
question. Codex-assisted; human hands-on time is not recorded.

Development optional check: one report fixture failed (82 other tests passed)
because it requested a separate report inside the raw folder. The runner refused
that destination as designed. The corrected fixture uses a fresh external
folder and explicitly checks inside-raw refusal; both focused report tests pass
in 12.27s. Exact failed code/log retained under
`results/reader-phase-cpu/qualification-history/report-fixture-in-raw`. No formal
capture or qualified source had been published.

Administrative operators: all six real temporary-process cases pass in the
required process-access context; the first restricted-context timeout check
failed when `ps` was denied, and its exact code, log and partial fixture files
remain in operator history. Four raw-retention/refusal cases and ten synthetic
publication-boundary cases pass. No formal collection ran. Both installed
OpenSpiel2.0.2 Apache2.0 license files were read/checked against the existing
`cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30` pin;
comparison-only use and strategy isolation remain unchanged.


Initial source `706d5d3`: bases 4,887 passed / 66 skipped / 150 deselected each
(642.84 / 612.18s), but both combined optional suites fail two new tests with
1,789 other passes (341.58 / 278.73s). Earlier tests had imported the reference
in the shared pytest parent. The preserved own-only guard correctly rejected
that process. Two tests now use fresh subprocesses, matching the actual CLI;
all 439 scientific files retain fingerprint
`39b5f696d15ed9994f190a5c928f030bbc348eb328103f451797c000146693bf`.
No runtime guard, algorithm, cap or tolerance was changed. Exact failed-cohort
logs, receipts, expected source and original tests are [retained](../results/reader-phase-cpu/qualification-history/reference-preloaded-706d5d3/manifest.json).
Deliberate reference-preloaded-parent regression passes five cases on each
runtime (7.56 / 5.96s); the first 3.12 driver path error happened before tests
and is retained too. Full strict typing (806 files) and Ruff pass. All four
local source roles and both same-head hosted jobs still need to qualify the
corrected test revision before formal collection. No source push or formal
phase run has occurred; first push batches the original commit and this fix.


November 16 — All six source roles qualify `4bef6ae` / 439-file fingerprint
`39b5f696d15ed9994f190a5c928f030bbc348eb328103f451797c000146693bf`.
Bases 4,887 / 66 skipped / 150 deselected each (648.19 / 616.01s); optional
1,791 each (337.25 / 278.26s). Workflow 43868816929: initial hosted 3.11 job
133304229996 cancelled at the existing 25-minute job limit after 84%, without
an assertion failure. Official annotations/full raw log retained. One unchanged-
source software retry, job 133321132029, passes all 4,887 / 66 / 150 plus the
existing historical warning in 1,115.64s. Original 3.12 job 133304230313 passes
in 875.19s; attempt2 logical job 133321136325 carries forward byte-identical
logs and original timestamps, not another execution. Both actual interpreters,
NumPy, all uv choices and complete tested checkout `ca7d1b2` / tree
`dbae69e8b69991425c5895aac7ec64ae784e3ae7` equal to the local head are verified.
[Six-role archive](../results/reader-phase-cpu/checks.json) retains every attempt,
exact source map, nine tested operators, installed licenses and fixture history.

Separate software-test duration diagnosis: unchanged local base selection
4,887 / 66 / 150 passes in 594.52s (595.3704771669873s complete wrapper),
actual 3.11.17/2.4.6, source identical before/after. Largest individual costs:
old 40-policy binding 44.57s, complete reduced-study publication 31.28s; new
archived-reader call and runner-proof setup about 4.3s each. These are local
software-test durations, not a causal hosted-runner diagnosis, poker strength
or production cost. The original workflow and all scientific caps stay fixed.

Both actual runtimes resolve, patch and restore all 40 proposed report-guard
entry points without executing a report, game or reference. This checks static
import/descriptor setup only; actual numerical-export reproduction still waits
for the complete published pair. All raw logs retain original BOM/whitespace.
The qualification and operator archive is published before a fresh own-only
proof; no formal phase measurement, new reference construction or new Hold'em
trajectory has run. [PR #83](https://github.com/jimmy-sim/poker-ai/pull/83) remains
draft through the required proof, pair, report and final checks.


November 16 — Fresh own-only phase proof follows public six-role qualification
`dde10b3` and source/operator readiness verification. Complete outer CLI
5.341215124994051s; complete inner child 5.2538408339896705s, under 180s.
One actual archived software read matches the separately computed ordinary
result exactly; two explicit synthetic phase-shape reads exercise six forwarding
fixtures, seven selected calls overall, full restoration. No real cost-loader
coverage or new independent poker-math claim. Reference and poker-training flags
remain false. Source 439-file fingerprint stays
`39b5f696d15ed9994f190a5c928f030bbc348eb328103f451797c000146693bf`.
[All 13 raw files](../results/reader-phase-cpu/software-raw-manifest.json), complete
outer/inner clocks and [source readiness](../results/reader-phase-cpu/source-published-verification.json)
are retained in this own-before-reference publication. Public-boundary validation
remains before any fresh reference construction. No formal phase audit pair or
new Hold'em trajectory has run; failed budget/accuracy gates remain unchanged.


November 16 — The single complete reader-phase pair finishes after published
own-proof verification, source head `262e7931c5aa9619be619d2bd13a4cc72fd6bbd1`.
Ordinary/observed complete children: 393.5271485419944 / 395.7039985000156s;
complete outer CLI: 790.3233785830089s. Exact complete scalar/computed-replay
identity and full restoration pass. Original three reads, 432 profiles, 1,152
fixed conditions and three reference workers remain; caps stay 900/1,800s.
[All 27 raw files](../results/reader-phase-cpu/pair-raw-manifest.json), outer
metadata/log and the earlier [own-publication verification](../results/reader-phase-cpu/software-published-verification.json)
are retained in this raw-before-analysis batch. Ignored originals are untouched.
No phase analysis, optimizer, new trajectory or admission claim is included.
Public-boundary verification, report reproduction and final checks remain.


November 16 — Raw pair publication `fb87f79` passes source/raw/clock and earlier
own-proof publication verification before phase analysis. Saved report:
source-load CPU 77.699410 / 78.599851s, stand-in-load 2.214787 / 2.093312s,
own-replay 49.279233 / 49.743959s, remaining read 0.586987 / 0.656897s;
complete cost-read CPU 129.780417 / 131.094019s. Actual software read CPU
2.010200s, of which own replay 1.563982s. Seven calls, exact full result identity
and restoration pass; full retained inventory remains 3 reads / 432 profiles /
1,152 conditions / 3 reference workers. Complete child walls 393.5271485419944 /
395.7039985000156s, parent body CPU 263.988770 / 266.671255s, summed parallel
worker body CPU 370.331519 / 369.548862s; these clocks are not interchangeable.
Both actual PNGs visually inspected.

Actual 3.11.17/NumPy2.4.6 and 3.12.15/NumPy2.5.4 report reproduction passes with
all 40 numerical paths blocked after static import setup: all three numerical
exports byte-equal, zero forbidden calls, raw inputs unchanged. Guard execution
10.826516333996551 / 11.016834832989844s, not trajectory replay or production
costs. [Receipts](../results/reader-phase-cpu/report311.json) and
[second runtime](../results/reader-phase-cpu/report312.json), logs and the
[published-pair verification](../results/reader-phase-cpu/pair-published-verification.json)
are retained with the report. Current source loading is the next target to
investigate; no causal speedup or new optimizer follows this single ordered
pair. Existing 912.54/900 budget and 2.390%/1% accuracy failures remain. Final
four local roles and both same-head hosted jobs still precede merge.


## November 16 — source-root children, prospective implementation

[Plan](https://github.com/jimmy-sim/poker-ai/issues/4#issuecomment-6918554952)
published before code/outcomes. PR83 final checks remain running; isolated
implementation only, formal collection waits for its verified merge/main check.
Preserve all439 preceding scientific files (fingerprint39b5f696...) and original
scientific data/caps/seeds. New private entry/support/config only; no optimizer.
Observe two source roots with six serial children each, fourteen calls/cap32,
root/child/outside arithmetic without double counting. Two module-alias proxies
leave original defining modules/functions unchanged. Complete audit180/900/1800
and failure-save120 rules remain, own-before-reference/raw-before-analysis.

Observer54 focused tests pass on each actual runtime36.51/35.41s during ongoing
software checks, not scientific timing. Strict typing passes both new modules;
Ruff passes. Initial runner unit suite3FAIL/48PASS/1SKIP76.82s caught three
inherited test assumptions: two erased already-empty software event streams,
one expected7 instead of14calls. Corrected runner suites51PASS/1SKIP63.69/63.38s.
Separate lifecycle fixtures initially1FAIL/6PASS/52deselected0.20s because the
shared-cap fixture omitted arm order; corrected7PASS/52deselected0.15/0.17s.
[Both failure histories](source-phase-cpu.md) retain exact logs/code; no guard,
source algorithm, compute limit or scientific result changed. These are unit
fixtures, not qualified source or a formal own/source-loader proof. Full runner
failure coverage, local/hosted qualification and documentation remain.


November16 — PR83 all final six roles pass exact head2981f61 / source439 FP39b5.
Bases4,887/66skip150deselect1,260.05/1,230.38s; optional1,791each809.88/747.76s.
Hostedrun43880737350 jobs133345763483/133345764103 pass1,081.90/901.00s plus
existing warning. Actual patch/NumPy/alluv and entire checkout903f893/tree
cbfa7dd1f6be0accf041a07abb9a6d281376bb33 equal checked head. Administrative verifier
first read connector-normalized jobs lacking head_sha; preserved that attempt
and verified full official metadata instead, without rerunning tests/captures.
History merge81ba6bf; fresh actual user snapshot before guarded FF. Main actual
3.11.17/2.4.6 passes223focused51.90s, authenticates complete saved pair and all
three numeric exports. User ten changed bytes/status/index entries/both patches
preserved after checks. [All closing raw receipts](../results/reader-phase-cpu/final-ci/manifest.json)
batched into this next substantive milestone, not a status-only commit.

Source-child observer/runner focused optional113PASS each61.36/60.62s. Full strict
typing810files passes after test-only explicit dynamic module-alias typing;
Ruff passes. New lifecycle tests retain full/partial pair without retries,
pre-child shared-cap failure and failed-receipt invalidation/error preservation.
No formal source-child proof, pair or reference has run. Scientific439preceding
bytes remain unchanged; next source442 qualification and tested operators remain.


November16 — Prequalification self-review moves proxy bookkeeping to private
fields so ordinary module attributes named selected/selected_name/delegate are
forwarded too. Four focused proxy/late-alias/cleanup checks pass each0.09/0.10s;
complete source qualification will include this final source. Both actual runtimes
resolve, patch and restore all45 future report-guard entry points, with zero
numerical calls; this is static setup only, not report reproduction. All six
owned-process launch cases, four exact-retention/refusal cases and ten synthetic
publication-boundary cases pass. These are software fixtures, not scientific
proofs or new timing. Source implementation now freezes for full qualification;
no source-child formal capture has begun.


November16 — Both initial base qualification logs stopped at27% around a chat
interruption; sessions no longer existed and no completion receipts were present.
All four original partial files/hash receipt retained, with termination signal
unknown. The unchanged software lanes restarted; then self-review identified
proof-parser metadata edge cases before source publication. Only owned software
processes were interrupted with SIGINT, retaining the second partial cohort and
operators. Neither cohort completed a qualification role or ran a scientific
measurement. A five-case regression reproduces acceptance of boolean actual,
synthetic and root read-index lists and invalid inner cap declarations.

New parser uses canonical typed index comparisons and explicitly requires the
already-declared finite numeric180second inner cap. Positive fixture now records
that actual supervisor field. Five failures/59deselected5.03s before fix retained
with exact code/log; after correction all118focused optional checks pass each
40.75/39.50s. No mathematical code, scientific cap, seed, tolerance or historical
input/result changed. [Regression](../results/source-phase-cpu/qualification-history/proof-metadata/manifest.json),
[external interruption](../results/source-phase-cpu/qualification-history/interrupted-local/interruption.json)
and [superseded checks](../results/source-phase-cpu/qualification-history/superseded-before-metadata-fix/manifest.json)
remain distinct. Corrected source must complete every local/hosted source role
before publication/own proof; no source-child formal collection has begun.


November16 — Resume authorized by the user after pause; PR84 source CI run
43987653002 both passes. Actual jobs133719848627/133719848928: 5,004 passed,
67 skipped,150 deselected plus existing historical warning,1,281.09/1,009.46s.
Actual interpreter/NumPy/alluv and entire checkout35ea65e1e45285f2bba1b7c279dd90b45012b8a4
match source headf784551 and all four prior immutable local roles.
[Six-role qualification and nine tested operators](../results/source-phase-cpu/checks.json)
archived before any formal own proof. All439 predecessor scientific bytes/128pins
remain unchanged, source442 fingerprint e4cd4c0ec8fbd59f407f667eafe7fd6cae15a9bcd8890a8c1dd841207a0acfdc.
No source-child proof/pair/new reference or trajectory has run. Next public-source
verification, then the fixed180s own-only proof; old budget/accuracy failures remain.


November 16 — The fresh own-only proof follows verified public six-role source
qualification. Its complete CLI finishes in 5.927510875000735 seconds, under
the fixed 180-second cap. The actual archived software replay is identical
before/during observation and records zero source roots. Two separately labeled
synthetic forwarding reads give 14 selected root/child calls, with full restoration.
[All raw proof files](../results/source-phase-cpu/software-raw-manifest.json)
and source-publication verification are retained before fresh reference use.
This does not claim real cost-loader coverage or new independent poker math.
Public-boundary verification remains before the single complete audit pair.


November 16 — Publication verification rejects the fresh proof: its parser
incorrectly requires an inner cap exactly180s, while the supervisor correctly
subtracts startup from the unchanged180s outer allowance (recorded inner cap
179.9989877909975s). Calculations/restoration completed, but this proof is not
accepted for admission. A mistakenly attempted pair was blocked by the same
guard before any child measurement or reference construction; its complete
failure is [retained](../results/source-phase-cpu/pair-raw-manifest.json). No
source-child timing result follows. Correct the remaining-budget parser, retain
negative cases, and fully qualify the corrected source before further collection.
No scientific cap, seed, tolerance or earlier outcome is changed.


## Startup-adjusted allowance correction — November 16

The [prospective correction](https://github.com/jimmy-sim/poker-ai/issues/4#issuecomment-6941037776)
keeps the rejected proof and blocked pair unchanged. A separate corrected entry
and config use `results/source-phase-cpu-v2`; all 442 predecessor scientific
files remain unchanged. The new parser accepts finite numeric inner allowances
with `0 < cap <= 180` and requires the complete child duration below that cap.
The fixed outer180-second limit remains. For example, startup can legitimately
leave 179.9989877909975 seconds; requiring exactly180 rejects valid evidence.

All78 corrected-runner tests pass on actual3.11.17/NumPy2.4.6 and3.12.15/NumPy2.5.4
(34.24/31.21s), including fractional/exact allowances, invalid/exhausted limits
and a CLI-calculation/publication round-trip. Full strict typing passes812files.
A launcher preflight verifies published own evidence inside the complete outer
clock; rejected or interrupted checks start no child and retain their clock.
These are software checks, not a new formal proof or real cost-loader result.
Full new local/hosted qualification remains before any revised collection.
No scientific cap, seed, tolerance, policy, dependency or CI behavior changes.


### November 17, 2026: startup-adjusted parser source requalified

[PR #84](https://github.com/jimmy-sim/poker-ai/pull/84) correction source
`5496ef1`, 444-file fingerprint `5b966422276208f50fff1fc4ab4126271cb4405f39edbcc7a982329c86829ee9`:
all six [qualification roles](../results/source-phase-cpu-v2/checks.json) pass. Local bases: 5,081 passed,
68 skipped, 150 deselected (1,355.23 / 1,341.81 seconds); optional suites:
1,987 each (927.39 / 853.82 seconds). Hosted run
[44040643292](https://github.com/jimmy-sim/poker-ai/actions/runs/44040643292)
passes both jobs; full logs verify actual patch/NumPy, every uv selection and
the entire checkout tree. All 442 predecessor scientific files remain unchanged.

Ten exact administrative tools and all fixture records are retained. The final
launcher passes six process and five preflight cases, including refusal to
launch after preflight exhausts the outer allowance. The initial tiny fixture
attempted a late child, then received PermissionError during cleanup before its
outer receipt; its exact script, partial output and traceback remain archived.
The corrected fixture retains PID-null/124 with no child. Four retention and ten
synthetic publication cases pass; report-guard setup resolves 50 entry points on
each actual runtime without numerical execution. Installed OpenSpiel 2.0.2
Apache-2.0 license bytes were read before fresh use; comparison stays scalar-only.

All original rejected proof/blocked-pair evidence remains. This publication
precedes any revised formal own proof or reference comparison. No scientific
cap, seed, tolerance, policy, dependency or CI change, and no training or strength
claim. Implementation, execution and documentation are Codex-assisted; personal
practice and hours are not inferred.


November 17 — Revised own-only proof after public qualification `01658dd`:
complete outer 6.215336457997182 seconds / 180, inner 6.118413584001246 seconds against
startup-adjusted allowance 179.9991310000005. All 13 raw files plus source-publication
verification retained. Exact actual archived software replay, zero source roots,
14 separately synthetic forwarding calls, full restoration; no reference or poker
training constructed. Public-boundary verification remains before the one fixed
complete pair; original rejected proof and blocked pair remain unchanged.


November 17 — Corrected public own-proof verification passes before the one fixed
complete ordinary/profiled pair. Both arms finish, exact complete scalar and
computed-replay identity recorded; original caps and work retained. All 27
raw pair members plus the prior own-publication verification are retained for
publication before analysis. No retries or stage selection; no timing conclusion,
new training or admission is claimed at this boundary.


### November 17: nested source-loader report

Raw pair `e931955` was public and verified before analysis. Ordinary/observed
complete commands: 413.95887391699944 / 415.1078454160015 seconds; full outer CLI
832.0623138330011 / 1,800. Every original read, 432 profiles, 1,152 conditions,
three reference workers and all 14 selected calls retained; exact complete
scalar/computed-replay identity and restoration. Independent maximum discrepancy
1.8474111129762605e-13 chips < 1e-9, scalar comparison-only.

[The generated report and limits](source-phase-cpu.md#what-the-complete-comparison-found--november-17)
locate 39.248285 / 37.222540 parent CPU seconds in sampled-parent archive
validation and 33.107687 / 34.100730 in earlier scientific sources. Source totals
82.683827 / 81.157078; their combined shares 87.50921991068459% / 87.88299401316542%.
No causal speedup or stable overhead inferred from one ordered pair.

All three report exports match byte for byte on actual Python 3.11.17/NumPy 2.4.6
and 3.12.15/2.5.4 with 50 numerical paths blocked, zero forbidden calls and every
original raw member unchanged. Both PNGs inspected. Work log, method, journal128
and current journal summary updated together; no README experiment update.
Final four local roles and both same-head hosted jobs remain before merge.
No training, failed-gate override, default/fresh/global or strength claim.


### November 17: retain final local failures and correct linked-index access

At report head `74087e2`, both hosted jobs pass actual patch/NumPy/all-uv and whole
checkout checks (1,295.03 / 1,039.34 seconds). Both local bases instead retain one
failed archived-software replay: **5,080 passed / one failed / 68 skipped /
150 deselected**, 2,113.39 / 2,112.53 seconds. Optional roles did not start.
[Full failure, hosted and recovery evidence](../results/source-phase-cpu-v2/qualification-history/final-index-refresh/manifest.json)
is preserved before the next full qualification; no gate waiver.

Git trace: restricted status scans all 6,680 contents without updating its linked
index; ordinary authorized status writes only refreshed index metadata. The next
restricted status scans zero contents. Diagnostic status wall times 5.485529 /
3.576894 (refresh) / 0.036168 seconds are environment evidence, not production
costs. Exact failing tests then pass 4.34 / 4.28 seconds with unchanged 180-second
caps. All 444 scientific sources/128 input pins and staged/working-tree contents
remain unchanged. No scientific pair retry, algorithm, dependency or CI change.

Complete new final checks remain required on this coherent evidence/documentation
revision. Use normal linked-index metadata access for local checks, preserving
all earlier failures and exact runtimes. Journal128 records the explanation;
Codex-assisted execution, no inferred human hours or mastery.


### November 17, 2026: nested archive observer source qualified

[PR #85](https://github.com/jimmy-sim/poker-ai/pull/85), source `a9c672a`,
447-file fingerprint `3c343e8f8963a4d73e0ea6a277db13d57f06918ba45cb1d5216be151e7089e5d`:
all six [source roles](../results/parent-archive-cpu/checks.json) pass. Actual results:

| Role | Actual pytest result |
| --- | --- |
| base 311 | 5220 passed, 69 skipped, 150 deselected in 724.62s (0:12:04) |
| base 312 | 5220 passed, 69 skipped, 150 deselected in 695.25s (0:11:35) |
| optional 311 | 2127 passed in 428.44s (0:07:08) |
| optional 312 | 2127 passed in 361.94s (0:06:01) |
| hosted 311 | 2026-11-17T11:41:24.3100421Z 5220 passed, 69 skipped, 150 deselected, 1 warning in 1213.39s (0:20:13) |
| hosted 312 | 2026-11-17T11:12:41.0651154Z 5220 passed, 69 skipped, 150 deselected, 1 warning in 1092.97s (0:18:12) |

[Hosted run 44068969082](https://github.com/jimmy-sim/poker-ai/actions/runs/44068969082)
verifies actual patch/NumPy, all uv selections and the complete tested tree.
The initial hosted 3.11 job was cancelled at its unchanged 25-minute limit,
with the test log at 88%; full logs and official annotations remain. Only that
unchanged-source software role was retried. The prior 3.12 success retains its
actual attempt1 execution identity, not a new execution claim. No scientific
pair was run or retried.
Ten exact administrative tools, all fixture bytes and both license records are
retained. Six process / five preflight / four retention / ten synthetic
publication cases pass. All 73 numerical report guards resolve and restore on
both runtimes without constructing a reference; report reproduction remains
post-collection. The pinned OpenSpiel 2.0.2 Apache-2.0 license was read before
fresh use; outputs remain comparison-only.

All 444 prior scientific files, 128 original input pins, seeds, full work and
180/900/1800-second caps remain fixed. This publication is before formal own
proof and fresh reference work. Own proof before comparison and raw pair before
analysis remain required. No training, stronger/default/fresh/global admission,
human hours or personal mastery is inferred. Codex-assisted implementation,
execution, checks and drafting.


### November 17: own-only nested archive proof retained

The published-source verifier exits zero with all six roles and ten exact tested
tools matched. The complete own-only command then takes 6.639982541
seconds / 180; inner measurement 6.538013000 against startup-adjusted
allowance 179.9988875420022. Actual saved software replay is unchanged;
two labeled synthetic trees give 802 calls and complete restoration. No reference,
training, real cost-loader coverage or independent new poker math is claimed.
[All 13 raw members](../results/parent-archive-cpu/software-raw-manifest.json) are
retained before any fresh comparison. Publish and verify this boundary with an
actual zero exit before launching the fixed pair. Caps, seeds, inputs and earlier
failures stay unchanged.


**November 17 — complete pair retained before analysis.** Both original full
arms finish with exact complete scalar/computed-replay identity, also matching
the previous published numerical identity. All 802 selected calls are present
and bindings restore. [All 27 raw files](../results/parent-archive-cpu/pair-raw-manifest.json)
are retained for publication before timing analysis. The successful public own-
proof verification preceded reference use; no training or new admission follows.
The next step is to verify the published raw pair, then interpret its stages.


### November 17: nested archive report and data-only reproduction

[All raw pair bytes](../results/parent-archive-cpu/pair-raw-manifest.json) public
at `a9097f4`, then publication verification exits zero before analysis. Complete
ordinary/profiled child wall: 394.975385875 /
398.778299084 seconds; enclosing CLI
797.198346292 / 1,800. All original work, 802 calls and restoration,
exact previous complete numerical identity; independent error
1.8474111129762605e-13 chips < 1e-9. No new training or admission.

[Full inclusive/residual table](parent-archive-cpu.md#what-the-complete-comparison-found--november-17):
archive 36.482965 / 36.735498 CPU seconds. Combined checkpoint decoding/checking
16.292417 / 15.881237 (44.66% / 43.23% of archive CPU); two explicit materialized
context calls 8.883226 / 8.748734 (about 24%). Other components and both complete
clock families are reported, without adding inclusive parents to children.

All three numerical exports reproduce byte for byte on both actual runtimes
with 73 numerical entry points blocked, zero forbidden calls and every raw input
unchanged; both PNGs inspected. Receipts and exact tested guards remain archived.
One ordered pair is not stable overhead, causal speedup, production costs or
strength. Next question: verify identical repeated contexts and safe reuse before
an optimization; none deployed here. Final four local/two same-head hosted roles
remain before merge. Existing failures, caps/seeds and AI-assistance attribution
remain; human hands-on time not recorded.


### November 17: close archive profiling and plan isolated context reuse

PR #85 is history-merged at `575c4596bf49a7bf3047167f3ae3dd690ad4a273`.
All six final roles pass the exact tested whole tree: bases 5,220 / 69 skipped /
150 deselected each, optional 2,127 each; final hosted 3.11 takes 1005.47 seconds
and 3.12 1053.37. Cancelled attempts and carried-success execution provenance
remain in [the closing archive](../results/parent-archive-cpu/final-ci/manifest.json).
A successful 3.11 run on the previously implicated image version refutes image
version alone as the cause. Actual main passes 559 focused tests (116.33 seconds),
authenticates all 27 raw files and regenerates three numerical exports exactly.
Ten unrelated user result bytes/statuses/index entries/both patches remain intact.

The next [prospective protocol](context-reuse.md) tests isolated root-local reuse
of repeated contexts, preserving all 447 scientific files, 128 pins, seeds,
180/900/1800-second caps and original complete scoring/reference work. No
implementation or new collection exists at this boundary. Exact graph/array
mutation isolation, six requests/two misses/four hits per reuse arm, cleanup,
complete qualification, own-before-reference and raw-before-analysis are fixed.
Journal step130 explains the question in plain English. One diagnostic pair
cannot admit a production default, fresh trajectory or stronger agent. Prior
912.54/900 runtime and 2.390%/1% accuracy gates remain failed. Codex-assisted
planning/checking/drafting; human hands-on time not recorded.


### November 17: isolated context reuse implementation and focused checks

Draft [PR #86](https://github.com/jimmy-sim/poker-ai/pull/86) implements the
prospectively specified root-local reuse without altering any of the 447 previous
scientific files or 128 input pins. New helper/entry/config bind 450 files. Exact
graph copying includes nested MatrixTree/SpotTree/engine state, array bits/layout/
flags and internal aliases. Each caller gets isolated mutable objects; cache and
aliases clear on exit, callback reentrancy rejects, and releasing the template is
inside the root clock. Both arms must share their complete context witness and
historical calculated-result identity. No policies or reference answers are cached.

Both actual runtimes pass 160 focused tests (60.80 / 72.90 seconds), including
saved-data plots, full receipt/clock/corruption tests and independent tiny-game
terminal/pure-reply sums. Strict typing passes 820 files; lint/821-file format
check pass. Initial malformed-NaN test failed in its strict writer rather than the
reader; corrected fixture directly writes invalid input and now tests the reader.
Six real tiny process, five preflight, four retention and ten synthetic publication
cases pass. The 103 report guards resolve/patch/restore on both actual runtimes,
zero forbidden calls. Earlier 93-target setup receipts remain retained as history.

This source publication precedes full four-role immutable local/two-role hosted
qualification, administrative-tool publication, formal own proof and comparison.
No fresh formal proof, reference comparison, training or performance admission has
started. Original caps/seeds/gates remain fixed. Codex-assisted implementation,
execution and drafting; personal hands-on time not recorded. Journal step130
explains the change and limits.


### November 17: complete context-reuse source qualification

[PR #86](https://github.com/jimmy-sim/poker-ai/pull/86), source `9ebd590`, now has
[all six exact-source roles and ten tested tools](../results/context-reuse/checks.json).
Local bases: 5,379 / 70 skipped / 150 deselected each (776.37 / 737.41 seconds
pytest; complete checks 788.112850 / 750.677537). Optional: 2,287 each
(470.71 / 407.94 pytest; complete checks 474.357324 / 411.847860). Hosted bases:
5,379 each, 1,179.75 / 1,174.25 seconds pytest, actual patch/NumPy/all uv verified.
Actual checkout `25f98f4` entire tree equals C0 `9ebd590`.

Initial hosted 3.12 reached the unchanged 25-minute limit at 93%; full raw log,
annotation/run/jobs were saved before the unchanged-source single-role retry.
The successful 3.12 execution is job134125636021/attempt2. Carried logical
3.11job134125639866 retains actual execution134108220465/attempt1, original
matching timestamps and exact log bytes. No scientific run or source change
occurred during that retry. All four local lanes exited zero and are finished.

Six process / five preflight / four retention / ten synthetic-publication fixtures,
103 final report guards and earlier 93-target receipts are retained. All exact
operator bytes match the tested map. The full pinned Apache-2.0 OpenSpiel 2.0.2
license was reread and matches both actual environments; comparison-only remains.
Source/code/docs checks and synthetic layout review are archived. Synthetic plots
are layout checks, not measured performance; actual figures still require review.

This batch is before formal own proof/reference work. Public qualification/tools
verification must actually exit zero; own raw publication and verification still
precede the pair. Original 447 source bytes, 128 input pins, seeds, scientific
work/limits and failed gates remain. Journal130 explains the status. Codex-assisted;
human hours and new personal learning are not inferred.


### November 17: own-only context-reuse proof retained

Public six-role/source/tool verification exits zero before collection. Complete
own-only command 9.022293542s / 180; child measurement
8.925335792s against startup-adjusted allowance 179.998911374998.
Actual archived software replay identical, zero archive roots. Separate actual
software-factory fixtures have two roots/six requests/two misses/four hits with
isolated template/return graphs, correct inventory, independent tiny terminal/
pure-reply sums, nested MatrixTree/SpotTree/engine mutation isolation and cleanup.
All 12 raw members, including complete outer clock/log, are
[retained](../results/context-reuse/software-raw-manifest.json) before any fresh
reference. No real cost-loader coverage, timing benefit, training or strength
admission follows. Publish and verify own evidence with an actual zero exit
before the pair; source450 fingerprint/caps/seeds/failed gates remain unchanged.


### November 17: complete context pair rejected; all raw retained

Both source-qualified arms finish all three reads with child status
`complete_context_reuse_diagnostic`, but the enclosing pair fails its joint
consistency check (`ArithmeticError`). [All 27 raw members](../results/context-reuse/pair-raw-manifest.json)
are retained unchanged, including the failed outer receipt/log. Public-own
verification actually exited zero before collection; its exact receipt/log are
retained with this batch. No source/seeds/work/caps/gates changed or scientific
retry occurred. Publish failed evidence before diagnosis or timing interpretation.
No valid-pair, runtime saving, training/default or strength admission is claimed.
Journal130 records the failure and next decision; Codex-assisted, human time unknown.


### November 17: rejected-pair diagnosis and negative result

All 27 raw bytes public at `00c93ad`; separate rejected-publication verification
exits zero without waiving the original gate. Both children complete three reads,
432 profiles / 1,152 conditions / three workers. Context witness matches; four
work counters alone differ (normalization requests/evaluations 918104→602980,
validation-cache requests 8316→8220 / hits8290→8194). All remaining identity fields
match exactly; maximum native scalar discrepancy1.8474111129762605e-13chips each.
The old complete identity includes those work counts, so the original gate stays
FAILED. The post-outcome projection is explicitly diagnosis, not new admission.

Observed ordinary/reuse complete wall409.749993/486.746614s; parent CPU
278.772282/356.275704; parallel-worker CPU369.053525/367.353604. Enclosing failed
command900.544028/1800s; no deadline failure. Archive CPU43.217785/44.302908
versus81.072654/81.525714 in the two dependent reads. Full-copy/witness checking
shows no benefit here; one ordered rejected pair is not stable causal evidence.
No unchanged-source pair retry, source/gate/cap/seed modification or model change.

[Failure report and two inspected figures](context-reuse.md#rejected-comparison-and-diagnosis--november-17),
[scripted data-only diagnosis](../results/context-reuse/diagnosis/manifest.json),
four exports byte-identical on BOTH actual runtimes under 103 blocked paths,
zero forbidden calls/raw unchanged. Original valid-pair parser still rejects.
New actual-data regression preserves that rejection and the four-field diagnosis.
Source450fingerprint unchanged. Journal130/current status and three explanation
questions record the lesson. Next: final checks and protected publication, then
another measured cost; no full-copy rollout, gate waiver, new training/default/
forecast/strength claim. Codex-assisted; human time unknown.


### November 17: close rejected context reuse; inspect saved source calls

[PR #86](https://github.com/jimmy-sim/poker-ai/pull/86) is history-merged at
`f5bde46daa540f89f4b8aafd313e100ca52b57be`. Both local base suites pass 5,380 tests
with 70 skipped and 150 deselected; both optional suites pass 2,288. Both hosted
jobs pass the same base inventory, each with one existing warning. Actual runtime,
NumPy and uv selections match, and the entire tested and merged trees are equal.
The initial hosted timeouts and interrupted local file reads remain in the
[68-member closing archive](../results/context-reuse/final-ci/manifest.json).

Main passes 720 focused tests in 178.56 seconds. All 27 raw members authenticate;
four numerical exports match with 103 construction paths blocked and zero
forbidden calls. The comparison remains rejected. All ten unrelated user result
files, their status, changed-path index entries and both patches are preserved
after verification. These receipts accompany the next substantive change.

The [next plan](https://github.com/jimmy-sim/poker-ai/issues/4#issuecomment-6954063964)
uses a saved lossless elapsed-stack graph to inspect five functions. Every direct
incoming/outgoing edge retains its identity, so a shared helper's total is not
assigned to just one caller. Original source, raw hashes, units and code positions
are checked. Self time plus direct child times must recover each selected
nonrecursive function's inclusive time; changed raw files or existing output
folders reject.

All 30 repository-focused graph, input/output and terminal tests pass on both
actual supported runtimes in 7.34/7.12 seconds. Strict typing passes for 823 files;
lint and formatting pass. All 450 earlier scientific files are unchanged. Full
final checks and saved-data reproduction remain pending, and selected historical
values are still unextracted. Publish this checked source before rendering, then
reproduce its exports on both runtimes with construction and profiling blocked.
Journal step131 explains the question and the caller-sharing example.

No strategy, dependency, CI, seed, compute limit or research acceptance rule has
changed. The 912.54/900-second forecast and 2.390%/1% accuracy targets remain failed.
Codex assisted with implementation, checks and drafting; human hands-on time was
not recorded.

### November 17: historical caller costs reproduced without construction

After source `395575b` was public, both guarded data-only executions complete.
All five numerical exports match exactly across actual Python 3.11.17/NumPy 2.4.6
and 3.12.15/NumPy 2.5.4. Each blocks 104 construction/profiling targets with zero
calls and preserves all 15 raw producer files. The complete 2,354-frame /
5,640-edge graph remains exported; all five selected functions conserve direct
child/self time within the fixed tolerance.

The historical earlier-source loader's two calls total 138.044 inclusive elapsed
seconds. Its direct earlier-archive-loader edge is 125.609 seconds; that loader's
`reduced_study_run.read_saved` edge is 125.552 seconds. The direct frozen-opponent
edge is 0.860610 seconds for 32 calls; another 16 tiny-fixture calls belong to a
separate caller. These nested profiled values include waits and instrumentation;
they cannot be added together or substituted for current CPU or forecast costs.
[All tables and receipts](earlier-source-profile.md#historical-saved-data-result--november-17)
retain the full detail. Next inspect the earlier archive reader, not a reply cache.

The real saved-data regression blocks construction/profiling and checks all five
output bytes. All 31 focused cases pass on both actual runtimes. Complete final
local/optional/hosted checks still need to run. No new measurement, solver, training or gate change;
Codex-assisted execution and documentation, human time not recorded.


### November 17: isolate the saved-data regression from optional reference imports

The full cohort on `03c7022` is not qualified. Both bases pass 5,411 tests with
70 skipped and 150 deselected; both hosted base jobs pass. Both optional suites
report one failed and 2,318 passed: the new regression enters an own-only guard
after other valid tests have imported OpenSpiel in the same interpreter. The
strict guard correctly rejects that state. [All failed local records and hosted
logs](../results/earlier-source-profile/failed-qualification-03/manifest.json)
are retained before another qualification attempt.

The fix changes only that regression: a reference-loaded parent is explicitly
refused, and a fresh child reads the saved data under all 104 blocks and checks
the five output files exactly. With real OpenSpiel preloaded in each parent,
31 focused cases pass on actual 3.11.17/NumPy 2.4.6 and 3.12.15/NumPy 2.5.4 in
3.06/3.04 seconds. Reader/config, source453 fingerprint, all 450 historical
scientific files and every reported numerical byte are unchanged. Complete
local/optional/hosted checks must now pass on the corrected head. No scientific
retry, relaxed guard, compute change or stronger-agent claim. Codex-assisted;
human hands-on time not recorded.

### November 17: earlier-source reader fully qualified; follow its archive checks

[PR #87](https://github.com/jimmy-sim/poker-ai/pull/87) is history-merged at
`23848b7d523127c50e7a9105c23274f9f80c2552`. Exact corrected head `b9213e3` passes
both local bases (5,411 passed, 70 skipped, 150 deselected; 758.71/726.27 seconds),
both optional suites (2,319 each; 485.50/423.26 seconds) and both hosted base jobs
(5,411 each; 1093.67/1164.38 seconds). Actual patch/NumPy and all hosted uv
selections match, and the whole tested and merged trees agree. The earlier failed
optional cohort remains retained, not counted. The fresh-child isolation fix
changes no reader, guard, config or numerical result.

Main passes 751 focused tests in 189.69 seconds, reproduces all five exports
byte-for-byte with 104 blocks/zero calls and preserves all 15 raw files. The
original context-reuse gate still rejects. All ten actual user edits, status,
changed-path index entries and both patches are preserved after verification.
The [39-member closing archive](../results/earlier-source-profile/final-ci/manifest.json)
retains final checks and main proof with this next substantive milestone.

The [prospective follow-up](https://github.com/jimmy-sim/poker-ai/issues/4#issuecomment-6957605618)
fixes seven archive-check definitions before additional values are extracted.
A thin query reuses the existing authenticated graph and direct-edge calculation;
it retains every original identity/edge and checks producer source coordinates.
The [method and terminal commands](archive-reader-edges.md) distinguish saved
receipt checking from new training, imported names from defining identities and
historical elapsed time from current CPU. Journal step132 explains the question.
All 53 focused tests pass on both actual runtimes; strict typing covers 825
files and lint/format pass. Both 104-target setups and four entry-exit fixtures
pass. Initial import-mode, fixture and typing errors were corrected and retained.
Selected values remain unextracted; full final checks and data reproduction wait
for source publication.
No new profiler, solver, trajectory, cache, dependency, CI or scientific-rule
change. Codex assisted; human time not recorded.


### November 17: fixed archive-reader selection reproduced on both runtimes

After public source `b26374f`, both actual readers complete with 104 blocks,
zero forbidden calls and 15 raw files unchanged. All five numerical exports are
byte-identical. Every original frame/edge and selected source coordinate remains
checked. [Full result and table generator](archive-reader-edges.md#historical-result--november-17)
retain the output, hashes and caller scope.

The historical reader's direct admission edge records 107.961533 seconds and
its direct prerequisite edge 17.361320. Prerequisites receive two direct reader
calls and twelve from receipt-profile checking. These are nested elapsed-stack
aggregates including waits, not current CPU or savings. Small row/grid checks
are not the large direct component. Next follow nested receipt/context checks;
no cache, new measurement, new training or failed-rule waiver. The fresh-child
real-data regression checks parent reference refusal and five exact exports.
Complete final local/optional/hosted checks remain pending. Journal132 updated;
Codex-assisted work, no human hours/practice inferred.


Pre-final verification: all 54 focused cases pass with real OpenSpiel deliberately
preloaded in the parent on both runtimes (1.31/1.29 seconds); the fresh children
retain all 104 blocks and five exact exports. Strict typing covers 825 files,
lint/format and 539 documentation destinations pass. Full final checks remain
pending. These are software/data checks, not new training or strength evidence.


November 17 qualification correction: both hosted jobs at `b5a58d4` fail test
collection because the new test imports scripts before establishing their path.
The local launcher's extra `PYTHONPATH` masked this portability error. Both local
base runs were stopped and retained; no final or optional success is counted.
[Failed jobs and partial local checks](../results/archive-reader-edges/failed-qualification-b5/manifest.json)
retain the evidence. The fix changes only the test's scripts-path setup, following
existing repository tests. With `PYTHONPATH` absent, all 54 focused cases pass on
both actual runtimes (1.14/1.07 seconds); strict typing covers 825 files. The
reader/config/guard, all 455 scientific bytes and original five-export result
remain unchanged. Full qualification must now pass on the corrected head without
the masking path override. No CI, dependency or scientific-rule change.


### November 17: archive-reader investigation verified; measure current receipt CPU

[PR #88](https://github.com/jimmy-sim/poker-ai/pull/88) is history-merged at
`2ac57b4a3f1ea02073b280e5d115009115f648a0`, preserving the source-before-data
commits. Corrected head `f078d2a` passes both bases (5,434 / 70 skipped / 150
deselected; 772.20/741.54 seconds), both optional suites (2,342 each;
488.81/423.50 seconds) and both hosted jobs (5,434 each, one existing warning;
1329.88/1125.82 seconds). Actual patch/NumPy, all uv selections and the entire
tested/merged tree match. Initial source/report CI import failures and interrupted
local checks are retained, not counted. Corrected local checks use no extra
`PYTHONPATH`.

Main passes 774 focused tests in 179.23 seconds; five numerical exports match
under 104 blocks/zero forbidden calls and all 15 raw files remain unchanged.
The original context-reuse gate still rejects. All ten actual user file bytes,
status, changed-path index entries and both patches remain preserved after
verification. The [44-member closing archive](../results/archive-reader-edges/final-ci/manifest.json)
accompanies this substantive next step.

The [prospective current-receipt plan](https://github.com/jimmy-sim/poker-ai/issues/4#issuecomment-6958619644)
fixes five caller boundaries and thirty selected calls/sixty events across the
original three-read pipeline. The observer adapts the existing framework without
changing its historical source, and adds elapsed/parent/reaped-child clock
reconciliation. All checks still run; no cache or new training. The
[method](receipt-source-cpu.md) and journal133 explain the difference between
historical elapsed costs and current CPU. Full source qualification and formal
proof remain pending; no complete comparison has started. Existing 900/1800/180/120
limits, scientific inputs, seeds and acceptance rules are unchanged. Codex-assisted;
human hands-on time not recorded.


Receipt observer foundation: both actual base environments pass 130 focused
cases with one plotting skip (23.65/23.54 seconds); both optional environments
pass 131 with real OpenSpiel preloaded (35.66/35.86 seconds). Runtime/source
checks bracket each run, with no extra launcher `PYTHONPATH`. Strict typing829,
lint/format and prototype documentation checks pass. Initial copied fixture
status, configuration metadata and typing issues were corrected before source
publication and retained. Synthetic plot layouts were inspected and the
exclusive-time legend moved outside the data. No plotted fixture values are
experimental results. The installed OpenSpiel 2.0.2 licenses match the recorded
Apache-2.0 hash in both environments. All 455 prior scientific bytes are
unchanged; new458 fingerprint `b475bfefb92963f25458d97260264743ff4d751b4513c307529742eaf10fc97d`.
Full exact-head qualification and checked published own proof must precede the
new complete comparison; no collection has started.


### November 17: retain the failed source qualification and child diagnostics

The first full cohort at `d2cd3f7` is not qualified. Both base suites pass
5,564 tests; the 3.11 optional suite passes 2,473. The 3.12 optional run has
2,437 passed and 36 setup errors, all from one failed shared fixture child.
Its original stderr was not retained, so the cause remains unknown. A fresh
software-only run of that same fixture passes; that does not explain the failure
or count as full qualification. GitHub's 3.12 job passes, while its 3.11 job hits
the existing 25-minute limit. [The failed cohort and fresh diagnostic](../results/receipt-source-cpu/failed-qualification-d2/manifest.json)
are retained together.

The test now saves child stdout and stderr beside its fixture directory and
still requires a zero exit code. Two regression cases check successful and
failed children. No reader, clock, configuration, scientific cap or acceptance
rule changes. Full qualification must be repeated on the new head before the
formal own proof or complete comparison. No new strength or timing result is
claimed. Codex-assisted work; human hands-on time is not recorded.


Resumed checks on November 17 pass 133 focused tests in each actual optional
environment (196.62/198.91 seconds), with strict typing829, lint and formatting
passing. A live sample during this run shows a parent waiting in an OS file
read; it does not establish the earlier child failure's cause. Temporary
environments removed during the pause were rebuilt from the unchanged lockfile.
Full exact-head qualification remains pending.


### November 18: qualify the receipt observer source

The first `00aae95` local rerun was interrupted near 15% of both bases, with
partial logs and no completion receipts. A detached shell launch also produced
no role results; both attempts remain retained and are not passes. A fresh
isolated attempt and [hosted run #549](https://github.com/jimmy-sim/poker-ai/actions/runs/44260849905)
pass all six required roles. Local bases: 5,566 passed / 71 skipped / 150
deselected each (861.76/858.37 seconds pytest), with strict typing829,
lint/format/hooks. Optional suites: 2,475 each (531.38/449.29 seconds).
Hosted bases: 5,566 each (1,316.05/1,148.07 seconds, one warning each).
Actual patch/NumPy, all uv selections, local source/import guards and the
hosted tested tree equal to head `00aae95` were checked. The
[six-role receipt](../results/receipt-source-cpu/checks.json) and
[retained logs](../results/receipt-source-cpu/checks/manifest.json) record the
exact evidence. Source fingerprint `b475bfefb92963f25458d97260264743ff4d751b4513c307529742eaf10fc97d`
is unchanged across all 458 scientific files. Next: publish this checked
source gate, then bounded formal own proof before any complete comparison.
No new timing, training, forecast admission or strength claim follows software
checks. Codex-assisted checks and writing; human hands-on time not recorded.


### November 18: bounded own proof after source publication

The pushed-source guard passes at `d1987a2`. The first private controller's
unsupported `--operation` flag failed before a proof child started (0.079
seconds); exact outer records are retained. A corrected private controller
changes only the CLI argument and fresh output name, with 180/1800-second caps
unchanged. Its focused argument/cap fixtures pass. The actual 3.11.17/NumPy
2.4.6 own-only proof completes in 8.070/180 outer seconds; the inner supervisor
completes in 8.008 seconds under its startup-adjusted allowance. Archived
fictional-game replay and two synthetic fifteen-call trees pass, with eleven raw
members and no native reference or training. The
[raw proof manifest](../results/receipt-source-cpu/software-raw-manifest.json)
retains both launcher attempts. Next: publish and verify own evidence before
the fixed ordinary/observed complete pair. No real cost-loader coverage,
performance forecast or stronger-play claim follows this proof. Codex-assisted;
human hands-on time not recorded.

### November 18: complete and retain the fixed raw pair

After the own-only checkpoint `181a400` was public and its publication verifier
passed, the single ordinary/observed comparison completed. Outer command:
879.144/1,800 seconds. Plain/observed children: 457.933/415.749 seconds, each
under 900. Both retain three reads, 432 profiles, 1,152 fixed conditions and
three native workers. The observed arm records thirty selected calls and sixty
events. The saved-data authenticator accepts the original exact scalar and
computed-replay identity `ccd8e493a22a04dd0514c180d234b3ee4b62df68531eb1ddda516ea7175a7185`.
The [27 raw members](../results/receipt-source-cpu/pair-raw-manifest.json)
and outer receipts are byte-exact. Next: publish raw evidence before data-only
cost analysis and two-runtime exports. No training, forecast admission or
stronger-play claim. Codex-assisted; human hands-on time not recorded.


### November 18: report current nested receipt CPU from published raw evidence

The [report](receipt-source-cpu.md#november-18-what-the-current-clocks-show)
uses only the [published raw pair](../results/receipt-source-cpu/pair-raw-manifest.json).
Both actual runtimes reproduce all five report files byte for byte with 109
numerical execution paths blocked, zero calls, no reference import and 25 raw
pair files unchanged. Both figures were inspected. In the observed cost reads,
six nested receipt prerequisite loads use 25.227/25.360 parent CPU seconds
inside 30.337/30.667 archive roots; one direct load uses 4.162/4.202. The
five exclusive categories reconcile each root. Complete read parent CPU is
136.472/137.320 seconds. Wall times 457.933/415.749 seconds for one ordered
plain/observed pair do not establish timer overhead or a speedup. Parent,
reaped-child and parallel worker clocks are reported separately. The
[report checks](../results/receipt-source-cpu/report-manifest.json) retain
actual versions and hashes. Next: assess identical contexts and mutation-safe
reuse under a prospective protocol before any optimization. The failed
forecast, accuracy and context-copy gates remain failed. Codex-assisted;
human hands-on time not recorded.


### November 18: finish exact-head software checks after the report

At `459c04d`, the first final local pair ran simultaneously and both base
suites failed one archived fictional-game replay at the unchanged 180-second
cap; each had 5,565 passes. The optional lanes were not started. An isolated
replay passed in 6.23 seconds. The serial retry of the same head passes both
base scopes (5,566 passed, 71 skipped, 150 deselected each), strict typing,
Ruff, all-files hooks and clean source guards. Both optional scopes pass 2,475
tests. Hosted CI [run #553](https://github.com/jimmy-sim/poker-ai/actions/runs/44271740130)
passes Python 3.11.17 and 3.12.15 on the same whole tree. The
[final archive](../results/receipt-source-cpu/final-checks/manifest.json)
retains all six passing logs, failed parallel logs, exact versions, run metadata
and verifier. Next: publish this record, verify documentation CI, then close
the focused PR. Scientific failures and strength limits remain unchanged.
Codex-assisted; human hands-on time not recorded.

### November 18: retain hosted documentation-head cancellation

On documentation/evidence head `33db2ae`, hosted [run #554](https://github.com/jimmy-sim/poker-ai/actions/runs/44285335607)
passes Python 3.12 (5,566 passed, 71 skipped, 150 deselected). Python 3.11
reaches 97% without a test failure before the 25-minute job allowance cancels
it. The [exact run and job logs](../results/receipt-source-cpu/final-ci-retry/manifest.json)
are retained. Raise only the workflow allowance to 35 minutes and rerun the
same checks on a new head. No scientific cap, source or claim changes; merge
remains gated on both successful hosted jobs. Codex-assisted; human hands-on
time not recorded.


### November 18: merge PR #89; preregister prerequisite identity audit

[PR #89](https://github.com/jimmy-sim/poker-ai/pull/89) is history-merged at
`26a1bc4`. Final local source-head bases pass 5,566 tests each, optional
suites 2,475 each, and hosted [CI #555](https://github.com/jimmy-sim/poker-ai/actions/runs/44289638378)
passes both exact runtimes and whole-tree checks. A concurrent local timeout
and an earlier hosted 25-minute cancellation remain in the evidence. The main
checkout fast-forward preserves ten unrelated modified files, status, index
entries and patches byte for byte. The result locates current nested receipt
CPU without accepting a saving, training forecast or stronger strategy.

The [next question](receipt-prerequisite-identity.md) was prospectively
[published on issue #4](https://github.com/jimmy-sim/poker-ai/issues/4#issuecomment-6977198494)
before source or collection: compare seven fresh prerequisite outputs, complete
graph identities and mutable isolation on both actual runtimes. No reuse or new
trajectory is admitted by that audit alone. Codex-assisted; human hands-on
time not recorded.

### November 18: retain first prerequisite-audit source failure

At `47852ff`, both local bases pass 5,574 tests each and both hosted CI #557
jobs pass. Optional 3.11 has 2,481 passes and two new synthetic failures:
its pytest parent had preloaded `pyspiel`, which the real audit child is
supposed to reject. The [full failed cohort](../results/prerequisite-identity/failed-source-478/manifest.json)
retains logs, receipts, source and CI metadata. No archived-input audit ran.
The synthetic tests now model a fresh module view and add an explicit
preloaded-reference refusal case. Nine focused cases pass on both optional
runtimes. Next: full exact-head requalification; no scientific cap or reader
changed. Codex-assisted; human hands-on time not recorded.

### November 18: qualify corrected prerequisite-audit source

At `4f040ff`, both local bases pass 5,575 tests, 71 skips, 150 deselections,
strict typing of 832 files, Ruff, hooks and clean source checks. Both optional
scopes pass 2,484 tests. Hosted [CI #558](https://github.com/jimmy-sim/poker-ai/actions/runs/44301595530)
passes both exact runtimes and the whole-tree checkout check. The
[complete six-role record](../results/prerequisite-identity/source-checks/manifest.json)
is retained, alongside the earlier failed optional cohort. Next: publish and
verify this source evidence before running seven actual archived prerequisite
loads. No caching, strength admission or forecast follows these software
checks. Codex-assisted; human hands-on time not recorded.

### November 18: publish fresh prerequisite identities before analysis

The fixed seven-load command runs serially on the two locked runtimes after
source qualification. Outer/parent CPU seconds are 47.721/46.936 on 3.11 and
43.013/42.251 on 3.12, all under the 180-second child cap. Seven exact graph
and semantic witnesses match within and across runtimes; each fresh result has
148,034 mutable nodes and 148 arrays with cross-result storage disjointness
checked. The [nine raw members](../results/prerequisite-identity/raw/manifest.json)
and verifier were published at `76952fe` before a report, with original input
pins unchanged. No complete-reader cache, saving forecast, trajectory or
strength admission follows. Next: checked data-only two-runtime exports.
Codex-assisted; human hands-on time not recorded.

### November 18: reproduce prerequisite identity report without readers

The [report](receipt-prerequisite-identity.md#data-only-report--november-18)
uses the public raw receipts only. Its summary and fourteen-row CSV are
byte-identical across Python 3.11.17 and 3.12.15. The
[checks](../results/prerequisite-identity/report-manifest.json) retain actual
versions, hashes and the operator: 114 reader/construction/profile entry points
blocked, zero calls, no reference import and ten raw files unchanged. Fresh
outputs are exactly identical and independently owned; reuse inside the
complete reader, forecast improvement and stronger play remain unproved.
Next: final exact-head local/optional/hosted qualification of this report
checkpoint, then history-preserving merge. Codex-assisted; human hands-on
time not recorded.

### November 18: final prerequisite-report source checks

At `6382cde`, both bases pass 5,578 tests, 71 skips, 150 deselections,
strict mypy on 834 files, Ruff, hooks and clean guards. Both optional scopes
pass 2,487 tests. Hosted [CI #562](https://github.com/jimmy-sim/poker-ai/actions/runs/44310335860)
passes both exact runtimes and the whole-tree checkout check. The
[final six-role record](../results/prerequisite-identity/final-checks/manifest.json)
retains complete logs and hashes. Next: verify the documentation-commit CI
before a history-preserving PR #90 merge and protected-main preservation.
The earlier optional failure stays failed, and no reuse or strength claim is
admitted. Codex-assisted; human hands-on time not recorded.

### November 18: merge PR #90; preregister consumer mutation audit

[PR #90](https://github.com/jimmy-sim/poker-ai/pull/90) is history-merged at
`826701f` after final documentation-commit CI #563 passed both exact
runtimes and whole-tree checks. The guarded main update
preserved ten unrelated user edits, status, index entries and patches. The
fresh-output audit found identical, separately owned outputs; it did not
establish safe sharing.

The [next question](receipt-consumer-mutation.md) was prospectively
[published on issue #4](https://github.com/jimmy-sim/poker-ai/issues/4#issuecomment-6981335805)
before source or collection: inspect each of seven prerequisite graphs after
its receipt consumer and the full original archive read. Four synthetic
wrapper tests pass; full source checks and actual archived reads remain
pending. No cache, saving, forecast or strategy claim is admitted.
Codex-assisted; human hands-on time not recorded.

Pre-commit full checks in the dirty working checkout do not qualify this
source. The final preliminary attempt passes Ruff and strict mypy on 837 files,
but nine existing fresh-child tests fail to import `poker_ai` after local
editable-path changes (5,573 other tests pass; 71 skip, 150 deselect). Earlier
attempts found a stale mypy cache or a missing package at conftest import.
[Original logs and exit receipts](../results/receipt-consumer-mutation/failed-precommit/manifest.json)
are retained.
Next: commit the source and run exact-head checks in an isolated, clean
environment before publishing any archived audit result.

### November 18: qualify consumer-mutation audit source

At `dd53e99`, both clean local bases pass 5,582 tests, 71 skips and 150
deselections with Ruff, formatting, strict mypy on 837 files and all-files
hooks. Both complete 69-file optional scopes pass 2,491 tests on the two
actual locked runtimes. An initial 68-file optional pass omitted three newer
report tests and is retained but excluded. The complete installed OpenSpiel
2.0.2 license was reread before each optional scope and matches the pinned
Apache-2.0 hash. Hosted [CI #565](https://github.com/jimmy-sim/poker-ai/actions/runs/44339006308)
passes both jobs on the same whole source tree, with 5,582 tests each and
actual Python/NumPy versions and uv selections verified. The
[six-role archive](../results/receipt-consumer-mutation/source-checks/manifest.json)
retains local, hosted and failed/incomplete records. Next: publish and verify
this source-check receipt before any actual archived consumer audit. No reuse,
savings, forecast or strength claim follows from software qualification.
Codex-assisted; human hands-on time not recorded.

### November 18: archive the consumer reads and render their result

The qualified source and exact six-role record were public at `9b40113`
before collection. The original saved-archive read passed on locked Python
3.11.17/NumPy 2.4.6 and Python 3.12.15/NumPy 2.5.4. Whole commands including
startup took 84.845 and 73.026 seconds under the 180-second cap. Both original
replays returned all 480 profiles with zero chip/unitless error. Six nested
prerequisite graphs matched after their timing receipt callers; all seven
matched after the complete reader. The direct graph had no timing caller.
The [six original output files and hash manifest](../results/receipt-consumer-mutation/raw/manifest.json)
were published at `1e9714f` before report rendering.

The [data-only renderer](../scripts/report_receipt_consumer_mutation.py)
reproduces the same [report JSON](../results/receipt-consumer-mutation/report.json)
byte-for-byte on both actual locked runtimes with poker reader imports blocked.
Four focused tests pass, including tampered bytes and a changed stage with
updated hash. The result supports only nonmutation in this observed read; a
future shared-graph candidate still needs a separately preregistered complete
ordinary/reuse comparison. Next: qualify the report commit locally and in
hosted CI, then history-merge PR #91 if gates pass. The failed 912.54/900
forecast, 2.390%/1% accuracy and full-context-copy result remain failed.
Codex-assisted; human hands-on time not recorded.

### November 18: qualify the consumer-mutation report head

At `ba5b183`, both clean local bases pass Ruff, formatting, strict mypy on
839 files and 5,586 tests each, with 71 skipped and 150 deselected. The
all-files hooks and exact JSON rerender pass. Hosted
[CI #568](https://github.com/jimmy-sim/poker-ai/actions/runs/44347717628)
passes both actual locked runtimes with 5,586 tests each, one warning and
passing hooks. The PR merge checkout tree equals the report tree. The
[final-check archive](../results/receipt-consumer-mutation/final-checks/manifest.json)
retains 15 hashed members and rerunnable verification. The original audit
source is unchanged since its earlier complete optional checks. Next:
publish this evidence checkpoint, verify its own CI, then history-merge PR
#91. No shared graph or saving is admitted. Codex-assisted; human hands-on
time not recorded.

### November 18: merge the consumer audit and preregister validated sharing

Evidence-only commit `3bf8a85` passes both jobs of
[CI #569](https://github.com/jimmy-sim/poker-ai/actions/runs/44353064617)
with 5,586 tests each, actual locked runtimes, strict typing and hooks. PR
[#91](https://github.com/jimmy-sim/poker-ai/pull/91) is history-merged at
`e22bdee`; its whole tree equals the checked head. The separate main checkout
passes eight focused tests, reproduces the committed data-only report, and
preserves all ten unrelated user result bytes, status, patches and index
entries after its guarded fast-forward.

The [new issue #4 protocol](validated-prerequisite-sharing.md) was published
before source work. It tests one donor graph per earlier archive root while
still running every original loader and validation, followed by a fixed
complete ordinary/validated-share comparison only after source qualification
and a public own proof. No new candidate or archived result exists yet. All
old forecast, accuracy and full-context-copy failures stay failed. Next:
commit this protocol checkpoint, then implement its root-local boundary and
synthetic tests. Codex-assisted; human hands-on time not recorded.

The first local wrapper step has nine focused synthetic tests passing on both
locked runtimes; Ruff, formatting and strict typing pass. It forwards the
first validated graph only after all later original loader calls finish and
match. The first test fixture used `None` in place of a graph, so two focused
tests failed; the corrected fixture passes without changing the candidate's
source boundary. No archived proof, pair, or savings claim exists. Next:
finish the source-bound proof and complete-pair runner before the first source
push. Codex-assisted; human hands-on time not recorded.

The bounded own-proof and complete-pair source is now drafted. The former
requires public six-role source checks and an unchanged 180-second outer
cap; the latter requires published own raw proof, two root-local archive
captures per complete child, the original 900/1,800/120-second limits, all
three reads, 432 profiles, 1,152 fixed conditions and three native workers.
Its identity gate retains every work counter and the old complete identity
hash. Fifteen focused tests pass on both locked runtimes; Ruff and strict
typing pass. No archived proof or pair has run. Next: commit the coherent
source locally and qualify clean exact-head local/optional/hosted roles before
the first source push. Codex-assisted; human hands-on time not recorded.

The source commits `c1eb75a` and `04d19ed` were pushed together after both
clean local base roles (5,597 passed, 71 skipped, 150 deselected each), both
complete 69-file optional roles (2,502 passed each), strict mypy on 842
files, Ruff, format, all-files hooks, exact source/runtime guards and the
comparison-only OpenSpiel license checks passed. Hosted
[CI #572](https://github.com/jimmy-sim/poker-ai/actions/runs/44370320685)
passes on both actual locked runtimes with 5,597 tests each and a tested
whole tree equal to the source commit. The
[source-check archive](../results/validated-prerequisite-sharing/source-checks/manifest.json)
retains 29 hashed members, official job logs and a verifier. Next: publish
this evidence-only checkpoint and verify its public bytes before the one
bounded reference-free own proof. No real sharing outcome or savings claim
exists yet. Old forecast, accuracy and full-context-copy gates remain failed.
Codex-assisted; human hands-on time not recorded.

After publication and byte verification of source-check commit `c9eb713`,
the one fixed reference-free own archive proof passed under its original
180-second cap. The full command took 95.85 seconds on locked Python
3.11.17/NumPy 2.4.6; seven original loaders, six root-local donor
substitutions, all post-consumer/archive witnesses and the original zero-error
480-row replay passed. The [raw own receipt](../results/validated-prerequisite-sharing/own/manifest.json)
records the clean proof head, input and lock hashes, runtime, hardware,
elapsed time and exact child/outer bytes. No reference was constructed.
Next: publish and verify these raw bytes before the fixed ordinary then
validated-share complete pair; no saving or complete identity claim yet.
Codex-assisted; human hands-on time not recorded.

The one fixed complete pair failed in its first ordinary child. The child
ran for 100.21 seconds and returned 1 when original runtime validation could
not find Numba package metadata in the launched base Python 3.11 environment.
The pair retained failure after 100.70 seconds; the first ordinary archive
root completed and the validated-share child never started. All 16 raw and
diagnostic members were [published at `09c760f`](../results/validated-prerequisite-sharing/failed-pair/manifest.json)
before the [data-only report](validated-prerequisite-sharing-result.md).
The report JSON reproduces byte-identically on both locked runtimes with
reader/numerical/reference imports blocked; eight focused tamper and import
tests pass on each. No favorable retry, complete identity or savings claim.
Next: final checks and CI on this report head, then decide the separate
prospective runtime-preflight protocol. Codex-assisted; human hands-on time
not recorded.

Final report head `32d81ed` passes both clean local base roles (5,605
passed, 71 skipped, 150 deselected each), both 70-file optional roles (2,510
passed each), strict mypy on 844 files, Ruff, format and all-files hooks.
Hosted [CI #576](https://github.com/jimmy-sim/poker-ai/actions/runs/44385401428)
passes both actual locked runtimes and an identical whole checkout tree.
The [32-member final-check archive](../results/validated-prerequisite-sharing/final-checks/manifest.json)
retains raw logs, guards, rerenders and verifiers. The first report commit
hook attempt failed before commit because `uv` was absent from the shell
`PATH`; the unchanged staged commit passed hooks after loading the documented
environment. Next: publish this evidence-only checkpoint, verify its CI,
then history-merge the failed experiment. No complete pair identity or
savings admission. Codex-assisted; human hands-on time not recorded.

### November 18: merge the failed sharing experiment and pin its runtime

Evidence-only [CI #577](https://github.com/jimmy-sim/poker-ai/actions/runs/44390220790)
passes both actual locked runtimes, 5,605 tests each, all steps and an
identical whole tree. [PR #92](https://github.com/jimmy-sim/poker-ai/pull/92)
is history-merged at `7d356cf`, preserving all research evidence commits.
The separate main checkout fast-forwarded with all ten unrelated user file
bytes, status, patches and index entries unchanged; its final-check and raw
failure verifiers and data-only rerender pass.

The [next prospective issue #4 protocol](validated-sharing-runtime-preflight.md)
was public before new source. Read-only metadata confirms that both saved
real own artifacts require Python 3.11.17, NumPy 2.4.6 and Numba 0.68.1;
the installed optional environment has those versions, OpenSpiel 2.0.2 and
the pinned Apache-2.0 license hash. No new pair or source implementation
has run. Next: commit this protocol checkpoint and implement a fail-closed
launcher, then qualify it before any complete comparison. The PR #92 pair
and older forecast, accuracy and full-context-copy gates remain failed.
Codex-assisted; human hands-on time not recorded.

The first launcher implementation calls the unchanged pair once only after
installed and saved optional-runtime metadata, license bytes, clean public
source and the carried-forward own proof pass. Focused tests reject missing
Numba, changed packages/license/saved metadata, `PYTHONPATH` and wrong
environment before any pair output. Twelve tests pass under the actual
optional Python 3.11 runtime; both bases and optional Python 3.12 pass
eleven with one expected real-runtime skip. Ruff, format and strict mypy
pass. Initial line-length and duplicate mypy module/type findings were
fixed before this source commit. No complete pair has run. Next: commit
source and finish all six exact-head qualification roles before the first
source push. Codex-assisted; human hands-on time not recorded.

Source commit `0b9ae32` was published after both clean locked base roles
passed 5,616 tests/72 skips/150 deselections, both 71-file optional roles
passed (2,522 on Python 3.11; 2,521/one expected skip on Python 3.12),
Ruff, format, strict mypy on 846 files and all-files hooks. A sandbox uv
cache-lock failure before the first optional 3.11 test is retained; the
unchanged suite passed with cache access. Official hosted
[CI #580](https://github.com/jimmy-sim/poker-ai/actions/runs/44404463094)
passes both jobs on the identical whole tree with actual locked runtimes
and 5,616 tests each. The [34-member six-role source-check archive](../results/validated-sharing-runtime-preflight/source-checks/manifest.json)
has verified local and hosted logs, guards, metadata and file hashes.
Next: publish/verify this evidence checkpoint, reauthenticate the carried
old own proof, then run one fixed complete pair in optional Python 3.11.
No new complete pair, saving or strategy admission yet. Codex-assisted;
human hands-on time not recorded.

The single fixed optional-runtime pair launched from clean `c5697ef` after
the six-role source-check record was public. Preflight reauthenticated the
old own proof and pinned Python/NumPy/Numba/OpenSpiel/license metadata.
Its first ordinary child returned 1 after 525.99 seconds; the pair failed
after 527.74 seconds, inside both original caps. Both independent archive
roots (seven original loads each), three reads and three native workers
completed. The validated-share child did not start. The unchanged source
compares the 432-element profile and 1,152-element condition lists directly
with integer counts, causing the retained scope/source/input gate failure.
The [19-member raw failure](../results/validated-sharing-runtime-preflight/failed-pair/manifest.json)
and verifier preserve exact bytes. No retry or complete identity/savings
claim. Next: publish this raw checkpoint, render a data-only failed result,
finish checks and update PR #93. Codex-assisted; human hands-on time not
recorded.

The [data-only failed-pair report](validated-sharing-runtime-preflight-result.md)
authenticates the public 34-member source-check and 19-member raw-pair
records plus the carried old own manifest, with poker reader, numerical and
reference imports blocked. Nine tamper/import tests pass on each locked
Python runtime; both render byte-identical JSON SHA-256
`a69f851d4bb238f4aeee85ca70d2096fd3ab3ed62afae06c1721722c64a753bf`.
The report records 14 ordinary loader calls, three complete reads, three
native workers and failure before the validated-share child. Next: commit
the data-only report, complete exact-report-head local, optional and hosted
checks, then close the failed investigation. No retry or savings claim.
Codex-assisted; human hands-on time not recorded.

Hosted [CI #583](https://github.com/jimmy-sim/poker-ai/actions/runs/44414936420)
failed four report tests per runtime (5,621 passed/72 skipped/150 deselected
each). The [official failed-run archive](../results/validated-sharing-runtime-preflight/failed-report-ci/manifest.json)
shows the source-check manifest listed a Python 3.13 `.pyc` absent from the
normal clone because Git ignored it. The local verifier saw the ignored file
and passed. The source-check checkpoint was incomplete before the fixed
pair, and the raw manifest's publication flag is historically inaccurate.
This makes the pair ineligible for admission in addition to its actual
ordinary-child failure. Next: publish the failed CI receipts, add the exact
missing byte later without rewriting the manifest, correct the data-only
report and repeat required checks. No pair retry. Codex-assisted; human
hands-on time not recorded.

Repair commit `97baaf2` force-published the exact 4,671-byte ignored member
named by the old source-check manifest and a [late-publication receipt](../results/validated-sharing-runtime-preflight/source-check-repair.json).
It does not retroactively satisfy the pair's source-publication gate. The
corrected data-only report checks the member's absence at pair head
`c5697ef` and presence at repair head `97baaf2`, and exports
`source_archive_complete_at_pair_time: false` and `pair_admissible: false`.
Ten focused tamper/import tests pass in each locked Python runtime; both
render corrected JSON SHA-256
`7f8ac9091a139708366bc402f8326b8eb5cb0d4c0cb18886c3351e5d413b702c`.
Next: commit the corrected report and run full local, optional and hosted
checks before closing this failed investigation. No pair retry or savings
claim. Codex-assisted; human hands-on time not recorded.

Corrected report head `e2825e3` passed clean locked base checks twice
(5,626 passed/72 skipped/150 deselected each), 72-file optional checks on
Python 3.11 (2,532 passed) and 3.12 (2,531 passed/one expected skip),
Ruff, formatting, strict mypy on 848 files and all-files hooks. Official
[CI #586](https://github.com/jimmy-sim/poker-ai/actions/runs/44422838341)
passed both jobs on the same whole tested tree, each with 5,626 tests. The
[32-member final-check archive](../results/validated-sharing-runtime-preflight/final-checks/manifest.json)
verifies local/hosted logs, guards and identical data-only rerenders. The
failed CI #583, late source-check member and failed ordinary child remain
historical failures; `pair_admissible: false`. Next: publish this final
evidence checkpoint and close PR #93 without a retry or savings claim.
Codex-assisted; human hands-on time not recorded.

The [new issue #4 protocol](https://github.com/jimmy-sim/poker-ai/issues/4#issuecomment-6995942999)
and [PR #94](https://github.com/jimmy-sim/poker-ai/pull/94) were opened after
PR #93 merged. Protocol commit `70bdcd3` precedes source. The count adapter
now checks list types and lengths 432/1,152; a new source/own gate requires
all listed qualification members to be committed and pushed. The scientific
core, shared-graph support, inputs, lock and caps are unchanged. Ruff and
formatting pass on touched files; clean strict mypy passes on 848 files;
30 focused optional Python 3.11 tests pass. An initial focused run missed
`UV_PROJECT_ENVIRONMENT` and failed its actual-runtime test; the configured
rerun passed. An incremental mypy attempt reported four unrelated cached
attribute errors; a clean non-incremental strict run passed all 848 files.
The ignored local venv needed a normal `.pth` path because its generated
underscore-prefixed editable path was skipped by this Python installation.
Next: complete source qualification locally and on GitHub,
publish its exact receipts, then attempt a fresh bounded reference-free own
proof. No archived read or complete pair has started. Codex-assisted;
human hands-on time not recorded.

Source commit `182fd7c` passed both clean locked base roles: 5,629 passed,
72 skipped, 150 deselected each; optional 72-file roles: 2,535 passed on
Python 3.11 and 2,534 passed/one expected skip on Python 3.12. Ruff,
formatting, strict mypy on 848 files, all-files hooks, clean guards and
full pinned OpenSpiel license checks passed. Official
[CI #591](https://github.com/jimmy-sim/poker-ai/actions/runs/44437224485)
passed both jobs with 5,629 tests each, actual locked runtimes and a whole
tree equal to the source commit. The [31-member exact-source archive](../results/validated-sharing-count-gate/source-checks/manifest.json)
verifies local and hosted logs; explicit membership has no missing, ignored
or extra files. The first evidence-commit hook rejected two archived operator
scripts named `.py`; they were renamed `.py.txt` without changing their
executed bytes, then the manifest and verifier passed. Next: publish and
byte-verify this archive before the fresh
reference-free own proof. No archived collection or pair yet.
Codex-assisted; human hands-on time not recorded.

The 31-member source archive at `f6b5ede` passed its in-repo gate; GitHub's
PR head showed all 32 manifest/member blob hashes and sizes matched local
bytes. One fresh reference-free own proof at clean `f6b5ede` passed on
Python 3.11.17/NumPy 2.4.6: seven original loads, six substitutions,
480-row saved replay with zero chip/unitless error and no reference. Child
93.02 seconds; outer command 93.87/180 seconds. The
[three-member raw proof](../results/validated-sharing-count-gate/own/manifest.json)
is prepared with exact hashes. Next: publish and GitHub-byte-verify it
before any complete pair. Codex-assisted; human hands-on time not recorded.

One fixed ordinary→validated-share pair at clean `bac111d` passed the
original complete scientific/work/predecessor identity gate. Ordinary
531.45 seconds and shared 542.31 seconds, each under 900; outer
1,076.04/1,800 seconds. Each child retained two archive roots, 14
original loads, three reads, 432 profiles, 1,152 conditions and three
native workers; shared recorded 12 substitutions. No reference output
entered training. The [32-member compressed raw archive](../results/validated-sharing-count-gate/pair-raw/manifest.json)
verifies 17,200,261 original bytes from a 1,395,773-byte archive and
matches exact result/work identity. The first verifier assumed an ordinary
row substitution field and failed; only the verifier changed, then passed.
Next: publish and byte-verify raw evidence before the data-only report.
No CPU savings or new strategy claim. Codex-assisted; human hands-on time
not recorded.

The [data-only report](validated-sharing-count-gate-result.md) now
authenticates source, own and the published compressed pair plus Git
publication order. Ten focused tamper/import tests pass in the locked
Python 3.11 base environment; both locked Python runtimes render identical
JSON SHA-256 `b7eda7fc00ecef6e3176da8c0d2c9bf7589ad1897332bf5a4284a936fe82819d`.
Ruff and clean strict mypy on 850 files pass. Next: commit the report,
complete final base/optional/hosted checks, retain evidence, then close
the behavior question. No CPU saving or new strategy claim. Codex-assisted;
human hands-on time not recorded.

The [18-member final check record](../results/validated-sharing-count-gate/final-checks/manifest.json)
verifies exact report head `9f40bd4`: two clean base roles each passed
5,639/72 skipped/150 deselected, optional roles passed 2,545 and 2,544
with one expected skip, Ruff, formatting, strict mypy on 850 files and
all-files hooks. Official [CI #595](https://github.com/jimmy-sim/poker-ai/actions/runs/44447765358)
passed both jobs on the actual locked runtimes and a whole merge tree
identical to the report head. Next: publish this receipt, check CI on the
final evidence commit, then close this behavior question. No savings or
strategy claim. Codex-assisted; human hands-on time not recorded.

### November 18: prerequisite skip boundary mapped

[PR #94](https://github.com/jimmy-sim/poker-ai/pull/94) is history-merged at
`5017f8a`; final [CI #596](https://github.com/jimmy-sim/poker-ai/actions/runs/44450847721)
passes both actual locked runtimes with 5,639/72 skipped/150 deselected
and a whole tree equal to the final head. The separate main checkout was
fast-forwarded with ten unrelated user files, bytes, status, changed-path
index entries and patches preserved; its merged report and verifier pass.
The next [prospective static audit](prerequisite-skip-contract.md) maps
three reduction replays × two nested prerequisite loads plus one direct
load, and identifies checks a skip would bypass. Seven mapped source
modules parse, the new relative links resolve, and 24 relevant tests pass
with one expected skip on each locked runtime. No new archived read,
pair, solver construction, training or saving claim. Next: review this
contract, pass hosted docs checks, then decide whether a separately
preregistered optimizer is safe and useful. Codex-assisted; human
hands-on time not recorded.

### November 18: guarded skip protocol published before source

The [prospective issue #4 contract](https://github.com/jimmy-sim/poker-ai/issues/4#issuecomment-6999526861)
and [protocol](pinned-prerequisite-skip.md) fix a scoped guard and unchanged
complete result/work gate before implementation or new collection. One
original full load per root, six later guarded returns, exact root/pins/
source/donor checks and restoration are required. Both original caps and
seeds remain; any failed or partial gate stops without a favorable retry.
The first step is synthetic software only, then full exact-source local,
optional and hosted qualification before an archived own proof. No new
runtime or saving claim. Codex-assisted; human hands-on time not recorded.

The guarded-skip source step adds a 486-path closed snapshot from 14 pinned
files, 458 current scientific source files, archived historical source
maps and four new operators; eleven historical-only paths would otherwise
be missed. One original
loader per archive root is retained in the wrapper, with six later guarded
returns, exact alias restoration and failure checks. Own-proof, pair and
optional preflight adapters retain the original caps and public evidence
gates. Local focused checks pass on Python 3.11.17 and 3.12.15: 35 passed,
one expected skip each; Ruff lint/format and strict mypy on seven touched
source/test files pass. Initial import-order/format and test-typing failures
were corrected before qualification. Next: commit all related source/tests/
docs, run full clean local and hosted source checks, and publish the exact
source archive before any archived read. No pair or savings claim.
Codex-assisted; human hands-on time not recorded.

### November 18: guarded skip exact-source qualification

Source `7fb8f8a` passed clean base roles on both locked runtimes: 5,674
passed/73 skipped/150 deselected each, including Ruff, formatting and
strict mypy. Fixed 76-file optional suites passed 2,581 on Python 3.11 and
2,579 with two expected skips on Python 3.12. Hooks, both installed
OpenSpiel Apache-2.0 license hashes, pre/post clean guards and identical
486-path snapshots passed. The first complete local logs were lost when a
Mac restart cleared `/private/tmp`; the same unchanged source was fully
requalified in persistent ignored `results/runs/guarded-skip-requalification-20261118/`.
No partial dots are counted. Official [CI #601](https://github.com/jimmy-sim/poker-ai/actions/runs/44461179593)
passed both jobs with actual locked runtimes and 5,674/73/150 counts;
the tested merge checkout has the exact source tree. The
[35-member source-check archive](../results/guarded-prerequisite-skip/source-checks/manifest.json)
now holds the durable local cohort, official hosted logs, byte inventories
and verifiers. Next: commit, publish and GitHub-byte-verify all members
before a fresh reference-free own proof. No archived read, pair, training
or saving claim yet. Codex-assisted; human hands-on time not recorded.

The source archive commit `316bfb3` passes its 35-member in-repo verifier;
GitHub's PR tree contains the manifest and all 35 listed bytes at matching
blob hashes/sizes. At clean `316bfb3`, one fresh reference-free own read
completed under the original 180-second enclosing cap: child 97.72 seconds,
outer 100.75 seconds. Seven consumer sites retained the fixed order: one
original loader, six guarded returns. The donor witness stayed unchanged
after callers and the archive root; 480 saved rows replayed with zero chip
and unitless error, and no reference constructor or training ran. The
[three-member own record](../results/guarded-prerequisite-skip/own/manifest.json)
binds the exact child/outer/log bytes. Next: publish and GitHub-byte-verify
the own record before the one fixed complete ordinary→guarded-skip pair.
This saved read is not a CPU-saving or strength claim. Codex-assisted;
human hands-on time not recorded.

The single fixed complete pair then ran from clean `e323279` after the
own-proof publication gate. Pinned Python 3.11.17/NumPy 2.4.6/Numba
0.68.1/OpenSpiel 2.0.2 and the installed Apache-2.0 license passed
read-only preflight. Ordinary finished in 557.21 seconds, guarded skip in
602.25 seconds, both under 900; the pair ended after 1,163.73/1,800
seconds with `failed_retained`. Ordinary made 14 original prerequisite
loads; guarded made two and 12 explicit guarded returns across two
archive roots. The scientific identity and context match, with 432
profiles, 1,152 conditions and three native workers, but four saved work
counters changed: normalization requests/reduced evaluations 918,104→
726,200; validation-cache requests 8,316→8,220 and hits 8,290→8,194.
The unchanged full-work gate rejects the pair; no favorable retry.
The [31-member compressed raw failure](../results/guarded-prerequisite-skip/pair-raw/manifest.json)
contains 17,357,388 raw bytes and verifies both complete children and
the failed pair. Next: publish/byte-verify this raw record, render a
data-only failure report on both locked runtimes, complete local/optional/
hosted checks, and then move to a prospective bounded river-strength
question. The guarded child was slower in this one observation; no CPU
saving, training, default or strength admission. Codex-assisted; human
hands-on time not recorded.

Raw failure commit `aa3c9c2` passed its 31-member verifier; GitHub's PR
tree matched the manifest, compressed tarball and verifier bytes. The
[data-only result](pinned-prerequisite-skip-result.md) authenticates all
three public evidence stages and the failed pair without importing poker,
NumPy, Numba, OpenSpiel or Treys. Both locked Python versions render the
same 2,026-byte JSON, SHA-256
`aa81c862946096a299f2673669f9848ea0b4d4239a088f2acd02b8d446d42f81`.
Eleven focused tamper/import tests pass in the locked base runtime; Ruff,
formatting and strict mypy pass for the new two files. An initial test
invocation in the preexisting `.venv` failed at `conftest` import because
that environment lacked the editable project; the exact locked base
environment ran the suite successfully. Next: full base/optional/hosted
report qualification, then close this failed optimization and publish a
separate prospective bounded river-strength contract. No pair retry or
saving claim. Codex-assisted; human hands-on time not recorded.

The exact `4559b42` failure-report source completed final qualification: both
locked local base roles passed 5,685 tests with 73 skips and 150 deselections;
the fixed 77-file optional scopes passed 2,592 on Python 3.11 and 2,590 with
two expected skips on Python 3.12. Ruff, formatting, strict mypy, hooks,
clean source/runtime guards and identical data-only exports passed. Official
[CI #605](https://github.com/jimmy-sim/poker-ai/actions/runs/44471843556)
passed both actual runtimes with the same base counts and exact tested tree.
The [42-member final receipt](../results/guarded-prerequisite-skip/final-checks/manifest.json)
retains every qualification log and the four earlier pretest launcher assertion
failures. Next: publish/verify the receipt and history-preserving merge, then
prospectively register the separate bounded river-strength question. The one
failed work-identity pair is retained without retry or saving claim.
Codex-assisted; human hands-on time not recorded.

The [prospective river-strength contract](https://github.com/jimmy-sim/poker-ai/issues/4#issuecomment-7002496679)
and [fixed protocol](river-strength-known-vulnerabilities.md) were written
before any candidate source or new outcome. PR #96's failed guarded-skip result
is merged at `434cb18`; the new focused branch starts there. The plan compares
unchanged q8 against exact legal information only at river decisions, retaining
q8 through the turn, across both known games, three seeds and fixed 100k/1m/10m
node-work labels. Primary final10m linear-average exploitability and all other
readouts, historical gates, source/proof/forecast/own-before-native publication
boundaries and caps are fixed. The cheaper initial stage is software checks and
capped 100k profiling; the full gated workflow may take a few hours. No new
real profile preceded the [forecast amendment](https://github.com/jimmy-sim/poker-ai/issues/4#issuecomment-7002846466):
three complete 100k repeats per path, whole-path seconds extrapolated to 10m
including setup/scoring/replay, fixed three-worker sum `T`, and strict
`2*(2*T+600)<7200` admission. A failed forecast stops long learning. No new
measurement, learned candidate or fresh-case claim exists. Next: publish the
protocol checkpoint, implement the candidate key and tests, then qualify exact
source before learning. Codex-assisted; human hands-on time not recorded.

The river-strength source now implements the exact river legal key, fixed
B4 runner, durable own replay, predeclared forecast/admission, comparison-only
native scalar audit and all-readout data-only report. Nineteen focused locked
Python 3.11 tests passed; the full exact-source base/optional/hooks/hosted
qualification remains pending. No new real profile or learned result has
been run. Next: complete source qualification and publication before the
small own proof. Codex-assisted; human hands-on time not recorded.

Exact committed river source `b694688` failed full base qualification on both
locked Python 3.11.17 and 3.12.15 after Ruff, format and strict mypy passed.
Each fast suite had 5,425 passed, 53 failed, 227 errors, 72 skipped and 150
deselected. [Raw retained logs](../results/river-strength/source-failure/manifest.json)
show historical research source guards rejecting changed pinned modules,
including `matrix.py`; the earlier local launcher-count and test-typing
failures are also retained. The required source gate stops this experiment
before optional qualification, own proof, real profiling, compute forecast,
training comparison or native audit. Scientific outcome: **inconclusive**;
no poker-strength claim. Next: publish the failed source and logs to PR #97,
record hosted CI status, and leave the PR open at a safe milestone. No new
investigation or budget change. Codex-assisted; human hands-on time not
recorded.

On November 19 Jimmy explicitly resumed issue #4 and authorized software
source-pin repair. Hosted run [#44484159855](https://github.com/jimmy-sim/poker-ai/actions/runs/44484159855)
concluded failure on the old `2e2f0fb` source; its official log and metadata
are retained separately from the earlier local failure archive. The direct
root cause is changed historically pinned `matrix.py` and `range_protocol.py`
bytes. Many of the 227 per-runtime errors were fixture setup cascades. The
first repair restored those historical files byte for byte. Representative
historical tests then revealed that old provenance hashes every `src` Python
file; adding a new adapter there changed the pinned aggregate. All new
candidate code now resides in a closed `scripts/river_strength/` package,
explicitly bound by the new experiment's fingerprint. The fixed scientific
protocol is unchanged. Nineteen focused candidate tests passed after this
move. Next: representative historical guards and complete
new exact-source local/optional/hosted qualification before any real profile.
No scientific run has been retried. Codex-assisted; human hands-on time not
recorded.

Before real measurements on November 19, exact source `147e624` passed four
locked local roles: base Python 3.11 and 3.12 each had 5,704 passed, 73 skipped
and 150 deselected, with lint, format and strict mypy passing; optional 3.11
had 2,584 passed, and optional 3.12 had 2,582 passed and two expected skips.
Hooks passed. Hosted run [#44492928520](https://github.com/jimmy-sim/poker-ai/actions/runs/44492928520)
was still in progress at the last check. A premeasurement review then found
that the report omitted saved whole-path time and counted three rather than
four persistent float64 trainer tables. The source now binds both to the own
record, checks zero recall and native scalar tolerance explicitly, and keeps
data-only reporting independent of solver imports. Nineteen focused tests
passed on this correction. The earlier local pass remains a historical
intermediate check; the corrected exact source requires fresh complete
qualification before proof/profile. No real scientific run started. Codex
assisted; human hands-on time not recorded.


Corrected source `7d2cb37` completed exact-source qualification on November
19: both local base Python roles passed 5,704 tests (73 skipped, 150
deselected), Ruff and strict mypy; optional Python 3.11 passed 2,584 and
optional 3.12 passed 2,582 with two expected skips. Hooks passed. Hosted
[run 44494459961](https://github.com/jimmy-sim/poker-ai/actions/runs/44494459961)
passed both jobs, full checks and hooks. The
[source receipt](../results/river-strength/source-checks/manifest.json)
retains complete local and official hosted logs, runtime/license guards and
fingerprint. The intermediate hosted run on `147e624` was cancelled by this
push; its metadata and available log remain in the ignored run folder. Next:
publish and GitHub-byte-verify this receipt, then run the small own proof.
There is still no real river profile or trained candidate. Codex assisted;
human hands-on time not recorded.

The source-qualified bounded own proof completed on November 19 in 0.266
seconds including startup, below the fixed 180-second cap. The fictional
signal-game path saved nine readouts at work 80/240/720, finished at 726,
and replayed its snapshots and cumulative masses. The
[own proof archive](../results/river-strength/own-proof/manifest.json)
preserves all 22 raw members plus a manifest. Next: publish and verify this
own proof before launching the fixed 36-path, 100k profile. No real river
trajectory yet. Codex assisted; human hands-on time not recorded.

The fixed 36-path, three-repeat 100k profile completed on November 19:
108 readouts, 35.806 seconds inside the stage and 36.057 seconds including
startup, below the 900-second cap. The independently recomputed prospective
max-of-three forecast has `T=1218.014` seconds and strict bound
`6072.057<7200` seconds. The
[profile archive](../results/river-strength/profile/manifest.json) retains
all 293 raw members, including events, snapshots and complete path timings.
Next: publish and GitHub-byte-verify this complete profile, then publish a
separate data-only admission receipt before long learning. No 10m training or
native audit has run. Codex assisted; human hands-on time not recorded.

The complete profile archive was published at `ea0d967` and all 294 members
were GitHub-byte-verified. A separate data-only admission recomputed the
same `T=1218.014` and strict `6072.057<7200` bound from the published
profile. Its [receipt](../results/river-strength/admission/manifest.json)
is ready for a distinct publication gate. Next: publish and verify admission,
then start exactly one fixed 12-path 10m own study under the 7,200-second cap.
Codex assisted; human hands-on time not recorded.

The single prospective own 12-path study completed on November 19 in
238.682 seconds inside the stage and 239.029 including startup, within the
7,200-second cap. All 108 fixed readouts were saved; each path reached 10m
actual node work (final range 10,000,013–10,000,119) and recorded zero
structural-recall violations. The
[own raw archive](../results/river-strength/own/manifest.json) retains 220
members, including policies, masses, events and scores. Next: publish and
GitHub-byte-verify own evidence before constructing the comparison-only
OpenSpiel audit. No strength conclusion yet. Codex assisted; human hands-on
time not recorded.

After the own raw checkpoint, the pinned comparison-only native audit
completed all 108 scalar comparisons on November 19 in 55.210 seconds
including startup (<900). Maximum absolute discrepancy was
`1.2079226507921703e-13` chips, below the fixed `1e-9`-chip tolerance.
The installed OpenSpiel 2.0.2 Apache-2.0 license matched the pinned hash.
The [native archive](../results/river-strength/native/manifest.json) retains
all rows and events. Next: publish and verify this separate audit, then
reproduce the full report and run final source-bound local/optional/hosted
checks. No final strength conclusion yet. Codex assisted; human hands-on
time not recorded.

The [fixed report](../results/river-strength/report/report.json) reproduced
all 108 rows from published own and native evidence. On medium-OOP at final
10m linear average, paired candidate-minus-control exploitability fractions
were -0.025009, +0.002854 and -0.031549 across the three fixed seeds;
median -0.025009. The candidate passed the 1% median and 2.5% worst gates
(median 0.2924%, worst 0.6607%), while control failed both (median 2.7933%,
worst 3.3495%). Both arms passed low-OOP gates; all final average coverages
were 100%, recall violations zero and maximum native error 1.208e-13 chips.
Medium candidate table cost was 4,697,088 bytes versus 2,340,096 control.
**Conclusion: positive descriptive result on the two known games, with one
unfavorable paired seed and a failed control gate; no fresh/global admission.**
The earlier held-out and other failed gates remain failed. Next: publish the
report and run final exact-source local, optional and hosted checks; then stop.
No scientific retry or next experiment. Codex assisted; human hands-on time
not recorded.

Final exact-head qualification on report commit `aae4d52` passed on November
19. Both local base roles had 5,704 passes (73 skips, 150 deselections) plus
lint, formatting and strict typing; optional 3.11/3.12 had 2,584 and 2,582
passes (two expected 3.12 skips). Hooks passed. [Hosted run 44502509319](https://github.com/jimmy-sim/poker-ai/actions/runs/44502509319)
passed both full-check and hook jobs. The
[final check receipt](../results/river-strength/final-checks/manifest.json)
retains local and official hosted logs, guards and report hash. Next: publish
and verify this receipt, update PR #97 and the safe handoff, then stop. The
fixed known-panel direction is positive; the control's failed medium gates,
one unfavorable paired seed, dependence and lack of fresh validation prevent
promotion. No new experiment is authorized from this result. Codex assisted;
human hands-on time not recorded.

On November 19, [PR #97](https://github.com/jimmy-sim/poker-ai/pull/97)
merged with research history preserved at `9707b993`. Its final source and
hosted checks passed and all raw evidence is retained; the result is positive
only on two known games, with a failed control gate and no promotion. Jimmy
then requested one bounded comparison on additional spots. The
[prospective issue #4 contract](https://github.com/jimmy-sim/poker-ai/issues/4#issuecomment-7027108691),
[config](../configs/river-generalization-fixed-spots.json) and
[protocol](river-generalization-fixed-spots.md) fix two structural strata,
selection seed/rules, both arms, three training seeds, 10m matched-work
endpoint, all metrics/thresholds, conservative profile forecast and original
caps before generating new card/range inputs. Earlier held-out and fresh
cases are explicitly known; the new cases reuse known betting templates.
Next: publish this protocol, generate and freeze the fixed new inputs by
structural rules only, then qualify exact source before any real profile.
No new outcome or profile has been observed. Codex assisted; human hands-on
time not recorded.

The isolated structural selector for the additional-spot comparison passed
three focused tests (determinism, rank-signature exclusion, legal fixed inputs
and refusal to replace a cohort), focused Ruff and strict mypy on November 19.
The historical `src/` and `scripts/river_strength/` bytes are unchanged.
Next: publish this tested selection source, then run the declared one-shot
selection from a clean published commit and freeze its exact outputs before
any score or training profile. No outcomes have been inspected. Codex
assisted; human hands-on time not recorded.

One-shot structural selection from published commit `3fc07f9` froze
`new_low_wet_ip` (board `9s 7d Jd 5d`, attempt 3) and
`new_medium_dry_oop` (board `2s 6h Jc 3c`, attempt 3). The
[freeze](../configs/river-generalization-freeze.json) binds both card/range
files, all prior tracked spot inputs, source hashes and selection commit.
Both loaded as legal spots. No tree, policy or outcome was constructed.
Next: publish and GitHub-byte-verify this fixed cohort, then implement and
qualify the exact-source experiment runner. Codex assisted; human hands-on
time not recorded.

The isolated generalization runner, native scalar auditor and all-readout
report now bind the frozen cohort and the unchanged PR #97 representations.
Twelve focused tests passed, including four legal tree/representation builds,
recall, stage gates, replay, and positive/negative/inconclusive synthetic
classifications. Ruff and strict mypy passed; `src/` and the historical river
adapter/entrypoints are byte unchanged from `origin/main`. This is the tested
source checkpoint, before real proof, profile or trained outcomes. Next:
publish the source, then run all exact-source local, optional and hosted
qualification roles. Codex assisted; human hands-on time not recorded.

Exact-source qualification of `d78b525` passed on November 19 (PST).
Both local base roles: 5,717 passes, 73 skips and 150 deselections with lint,
format and strict typing; optional 3.11: 2,589 passes; optional 3.12: 2,587
passes and two skips. All four clean pre/post source/lock/runtime guards,
local hooks and both jobs in [hosted CI 44652668301](https://github.com/jimmy-sim/poker-ai/actions/runs/44652668301)
passed. The [qualification receipt](../results/river-generalization/source-checks/manifest.json)
retains logs and scope. Next: publish and GitHub-byte-verify this gate, then
run a synthetic own proof; no real trajectories yet. Codex assisted; human
hands-on time not recorded.

The single qualified-source fictional-game own proof completed on November
19 (PST): nine saved readouts at labels 80/240/720, final actual work 720,
0.270 seconds including startup (<180). Capture/replay succeeded and the
[raw proof archive](../results/river-generalization/own-proof/manifest.json)
retains every policy, mass and event. No new-spot outcome yet. Next: publish
and GitHub-byte-verify the proof before the 36-path 100k compute profile.
Codex assisted; human hands-on time not recorded.

The single 36-path 100k profile completed on November 19 (PST) in 36.669
seconds including startup (<900), with all 108 readouts retained. The
[raw profile](../results/river-generalization/profile/manifest.json) gives
fixed worker extrapolation sums 1209.651, 1211.170 and 1221.884 seconds;
`T=1221.884`, so the prescribed strict bound is `6087.536<7200`.
Next: publish and GitHub-byte-verify all profile members, then make a
separate admission decision from those published bytes. This timing gate is
not a poker-strength result. Codex assisted; human hands-on time not
recorded.

After all 294 profile blobs were GitHub-byte-verified, the separate
admission reader recomputed `T=1221.8841232260268` and
`6087.536492904107<7200` seconds from the published profile, without
constructing a learner or reference. The
[admission receipt](../results/river-generalization/admission/manifest.json)
records the decision. Next: publish and verify it before the single fixed
12-path 10m own study. Codex assisted; human hands-on time not recorded.

The one admitted 12-path fixed own study completed on November 19 (PST) in
287.150 seconds including startup (<7200). All 108 readouts were saved;
final actual node work ranged 10,000,010–10,000,164, and recorded recall
violations were zero. The [own raw archive](../results/river-generalization/own/manifest.json)
retains policies, masses, events, scores and path times. Next: publish and
GitHub-byte-verify every own blob before constructing the comparison-only
OpenSpiel audit. No strength conclusion yet. Codex assisted; human hands-on
time not recorded.

After all 221 own blobs were GitHub-byte-verified, the pinned comparison-only
OpenSpiel 2.0.2 audit reproduced all 108 saved scalars on November 19 (PST).
Maximum discrepancy was `5.684341886080802e-14` chips (<1e-9); whole audit
55.588 seconds including startup (<900). The installed Apache-2.0 license
hash matched. The [native archive](../results/river-generalization/native/manifest.json)
retains rows and events. Next: publish and verify the independent audit,
then produce the fixed all-readout report. No final strength conclusion yet.
Codex assisted; human hands-on time not recorded.

The fixed all-readout report reproduced 108 rows from the published own and
native archives. All six final paired seeds favored the candidate; low/wet/IP
paired median was -0.005148597 initial pots, medium/dry/OOP -0.092425654,
pooled -0.039914876. **The preregistered conclusion is negative:** the
candidate's medium/dry median/worst absolute exploitability were
3.566%/3.954%, failing the unchanged 1%/2.5% gates. Control also failed
there (12.756%/13.065%). Both arms passed low/wet gates, all final average
coverages were 100%, recall violations zero and max native scalar error
5.684e-14 chips. The [full report](../results/river-generalization/report/report.json)
retains every seed, readout, gain, work, memory and time. Deterministic
first-river-row policy examples and a rerunnable inspection command are in
the [study document](river-generalization-fixed-spots.md). Next: publish the
negative report and complete final exact-source checks, then stop with no
promotion or next experiment. Codex assisted; human hands-on time not
recorded.

Final exact-report-head checks on `d7b3179` were mixed. Both local base roles
passed Ruff, formatting and strict mypy but **failed** their full pytest
suites: 3.11 had 1 failed/5,716 passed; 3.12 had 2 failed/5,715 passed,
with 73 skips and 150 deselections each. The direct failures were unchanged
20-second spawned fixture deadlines in the concurrent local runs. Optional
3.11/3.12 passed 2,589/2,587 tests (two expected 3.12 skips), hooks passed,
and both [hosted jobs 44657786167](https://github.com/jimmy-sim/poker-ai/actions/runs/44657786167)
passed. The [final archive](../results/river-generalization/final-checks/manifest.json)
retains every failed/passing log, guard, CI metadata and report hash. The
premeasurement exact-source qualification had passed all roles; final local
reproducibility is incomplete. The fixed scientific result remains negative
because medium/dry candidate absolute quality gates failed. Stop here with
no retry or next investigation. Codex assisted; human hands-on time not
recorded.

On November 19, after the final-receipt [hosted run 44660963477](https://github.com/jimmy-sim/poker-ai/actions/runs/44660963477)
passed both jobs, Jimmy requested a read-only diagnosis of the remaining
medium/dry weakness. The prior scientific classification stays negative and
the final local base timeouts remain failed. The [prospective diagnostic
plan](river-generalization-diagnosis.md) and
[fixed config](../configs/river-generalization-diagnosis.json) pin the 12
existing policies, three seeds/checkpoints, both responding seats, additive
best-response-loss ranking, assumptions, 1e-9 accounting checks and 900-second
wall cap before any new node ranking. Next: publish and verify the plan, then
implement isolated read-only analysis with focused tests. No training,
ablation or policy outcome analysis has started. Codex assisted; human
hands-on time not recorded.

The isolated read-only diagnostic source is ready on November 19 (PST).
It adds the fixed 12-snapshot grid, exact information-row best-response
accounting, saved-continuation action values, source/archive/hash checks,
bounded output retention and a ranked-row inspection command without
changing the historical river source fingerprint (`152b357b...`). Focused
tests passed 3/3. Full local Python 3.11 base checks passed Ruff, format,
strict mypy and 5,720 tests (73 skipped, 150 deselected) in 999.38 seconds.
This is a source check, not a repair or repetition of the prior failed final
qualification. Next: publish this tested source, require hosted CI, then run
the one 900-second saved-policy diagnostic. No node ranking has started.
Codex assisted; human hands-on time not recorded.

The diagnostic source checkpoint `f2533eab52b6910313e23ab69430865fb2fc90f3`
passed hosted [CI run 44680486302](https://github.com/jimmy-sim/poker-ai/actions/runs/44680486302)
on Python 3.11 and 3.12 before measurement. The one fixed read-only run then
completed all 12 saved policies and 24 seat traces in 7.170 seconds under its
900-second whole-process cap. The [raw diagnosis](../results/river-generalization/diagnosis/manifest.json)
retains 12 compressed full-row traces, events, report and launcher receipt.
Worst exact additive accounting error was `1.155e-14` chips and native scalar
error `1.421e-14` (<`1e-9`); all saved scores, hashes and source pins matched.
The [interpretation](river-generalization-diagnosis-report.md) finds no
candidate information collision on this 3,336-row finite spot. Three turn
rows contribute 0.301718 of 1.323959 mean chips; river rows contribute
0.999712 chips collectively. Candidate mean exploitability declined from
33.4855 to 4.8448 to 1.3240 chips across the fixed 100k/1m/10m snapshots,
consistent with but not proving unfinished convergence. The original
medium/dry acceptance result stays negative and the earlier final local
base qualification remains incomplete. Next: publish/verify this report,
leave PR #98 draft, and stop without a new experiment or promotion. Codex
assisted; human hands-on time not recorded.

On November 19 (PST), Jimmy authorized an ongoing bounded issue #4 research
cycle, with poker strength and reproducibility ahead of GitHub activity.
The [operating workflow](research-operating-workflow.md) and updated
[roadmap](roadmap.md) now record milestone selection, prospective publication,
exact-source qualification, conservative compute admission, own-before-
reference boundaries, failure retention, and durable handoffs without changing
any frozen protocol. Live PR #98 and its final hosted CI were verified;
the original local concurrent spawned-fixture failures remain failed. The
two parameterizations passed in isolation on both locked Python versions
with the unchanged 20-second deadline; raw focused logs and receipts are
retained under ignored `results/runs/river-generalization-requalification-20261120/`.
Next: publish this workflow, then complete all exact-head local roles
serially before considering PR #98 merge. No new training or budget outcome
has been collected. Codex assisted; human hands-on time not recorded.

On November 20 (PST), the original PR #98 final local base failures were
investigated without changing the spawned fixture or its 20-second deadline.
Both parameterizations passed alone on each locked Python minor. One new
exact-head **serial** attempt at `3e77a50195372fca00868dcdbeb773c7afc75d14`
then passed all four required local roles: base 3.11 and 3.12 each 5,720
passed/73 skipped/150 deselected with Ruff, formatting and strict mypy;
optional 3.11 2,589 passed; optional 3.12 2,587 passed/2 skipped. Each
role's pre/post clean-source, runtime and lock guard passed, as did both
optional installed-license checks and all-file hooks. Hosted
[CI 44694112687](https://github.com/jimmy-sim/poker-ai/actions/runs/44694112687)
passed both jobs/hooks; its PR merge tree matched the source tree. The
[new receipt](../results/river-generalization/requalification/manifest.json)
retains original failure hashes, focused and full logs, guards, CI and the
serial driver. The old failed receipt remains failed; contention is supported
as an explanation, not proven uniquely. The medium/dry scientific result
stays negative at 3.566%/3.954% versus fixed 1%/2.5% limits. Next: publish
and verify the new receipt, complete evidence-head CI and review, then
history-preserving PR merge if eligible. No new training started. Codex
assisted; human hands-on time not recorded.

PR #98 final evidence-head [CI 44701038807](https://github.com/jimmy-sim/poker-ai/actions/runs/44701038807)
passed both Python jobs and hooks on November 20. A recorded self-review
checked the frozen config/cohort, nine stage archives, retained failed
receipt, source pins, serial local roles and the negative scientific report;
it is not independent review. The PR was history-merged as
`702bce9658209b2cc653e31f5884e5ae8e2ef918`. The failed 1%/2.5%
medium/dry gates and original concurrent fixture failures remain recorded.
The [new prospective protocol](medium-dry-training-budget.md) asks whether
the unchanged candidate reaches those limits with a fixed longer budget
while still beating a matched-work control. It fixes the known spot, seeds,
10m/30m/100m checkpoints, diagnostics, thresholds, compute caps and
publication order before new measurements. No proof, profile or training
has begun. Codex assisted; human hands-on time not recorded.

On November 20 (PST), the isolated PR #99 source for the prospectively fixed
medium/dry 10m/30m/100m training-budget study was tested at `7fe07e7`. The
first local attempt at `1c3004d` stopped at base 3.11 test 22% after review
found an unpinned historical decision helper; its partial log is retained.
The decoder was moved into the isolated adapter, with a focused equality
regression. Corrected exact-head serial base 3.11/3.12 each passed 5,724
tests (73 skipped, 150 deselected) and Ruff/format/strict mypy. Optional
3.11 passed 2,589; optional 3.12 passed 2,587 with two expected skips;
all source/runtime/lock/license guards and hooks passed. Hosted
[CI 44713065490](https://github.com/jimmy-sim/poker-ai/actions/runs/44713065490)
first passed 3.12 but cancelled 3.11 at the unchanged 35-minute limit during
pytest 98%, with no assertion failure. The full official failed log was
retained. One documented same-source software requalification passed 3.11
and hooks under the same limit; both hosted jobs now pass. The
[source archive](../results/medium-dry-training-budget/source-checks/manifest.json)
binds the failed and passing attempts. Next: publish/verify that receipt,
then one capped synthetic proof. No profile, long training, reference audit
or new poker-strength outcome yet. Codex assisted; human hands-on time
not recorded.

The one PR #99 synthetic own proof on November 20 (PST) completed on the
qualified and published source. Its fictional signal game reached 720 charged
node work, captured/replayed nine fixed readouts at 80/240/720, and exited
zero in 0.312 seconds command wall time versus the 180-second cap. The
[21-member archive](../results/medium-dry-training-budget/own-proof/manifest.json)
retains snapshots, mass, events, runtime and launcher measurement. This is a
software proof only, not a new poker-strength result. Next: publish and
byte-verify the proof before any 1m medium/dry profile. Codex assisted;
human hands-on time not recorded.

The one fixed PR #99 18-path 1m profile ran on November 20 (PST) after the
published and GitHub-byte-verified proof. All six arm/seed paths × three
repeats completed 54 captures/replays in 66.369 seconds (<900); all three
workers exited zero. Actual final path work was 1,000,012–1,000,092;
maximum recorded worker high-water RSS was 239,075,328 bytes. The
predeclared maximum-of-three extrapolation gave fixed worker sums
2213.346/2212.450/2213.983 seconds, `T=2213.983`, and strict bound
`2*(2*T+600)=10055.934`, which **fails** the 7,200-second admission cap.
An independent data-only calculation matched. The complete
[failed-gate archive](../results/medium-dry-training-budget/profile-failure/manifest.json)
retains every raw path, forecast, failure and log. Stop this experiment:
no separate admission, 100m training, native audit or final paired strength
result. Poker-strength classification is **inconclusive** because compute
admission failed; the compute gate itself is a clear rejection. The older
PR #98 10m negative result remains unchanged. Next: publish/verify the
failed evidence and save a safe handoff; any distinct follow-up needs its
own prospective question and protocol. Codex assisted; human hands-on time
not recorded.

PR #99 [merged](https://github.com/jimmy-sim/poker-ai/pull/99) on November 20
after its final evidence-head CI 44727087971 passed both Python jobs/hooks,
all 150 failed-profile archive blobs matched GitHub, and a documented
self-review checked the source and gate decision. History-preserving merge
`a29f989` retains each prospective/source/proof/failure checkpoint. Its
compute admission is rejected and its 100m poker-strength effect remains
inconclusive; no default changed. Issue #4 continues with a **different**
question: can clipped accumulated regrets improve the unchanged exact-river
learner at 10m matched work on the already known medium/dry spot without
regressing the already known low/wet spot? The
[prospective protocol](medium-dry-clipped-regret.md) fixes both arms, two
known spots, three seeds, crossings, old absolute gates, paired criteria,
resource caps and publication order. No new outcome was collected for it at
this checkpoint. Codex assisted; human hands-on time not recorded.

PR #100's isolated signed-versus-clipped source was checked on November 20
at exact commit `c996c0a` before any formal proof or poker outcome. Historical
384-file river fingerprint stayed unchanged; new adapter fingerprint is
`7c2312727903a44a347be5ea1bf5c6d1d2c1ed17c447bac7e3605fa8773320ab`.
The seven focused tests include historical signed-rule equivalence, both-arm
fictional capture/replay, fixed forecast/classification and turn-row identity.
Serial exact-source base Python 3.11/3.12 each passed 5,731 tests/73 skipped/
150 deselected with Ruff, format and strict mypy; optional 3.11 passed 2,589,
optional 3.12 passed 2,587/2 expected skips. Source/runtime/lock and optional
license guards plus all-file hooks passed. Protocol-head CI 44732250767 and
source-head CI 44739782171 passed both jobs/hooks. The first launcher attempt
failed before tests when sandboxing denied uv a shared-cache lock; its log and
receipt are retained beside the successful roles in the [source qualification
archive](../results/medium-dry-clipped-regret/source-checks/manifest.json).
Next: publish and verify those bytes, then run the capped fictional proof.
No poker-strength measurement yet. Codex assisted; human hands-on time not
recorded.

The one formal PR #100 fictional signal-game proof ran on November 20 (PST)
after the published, GitHub-byte-verified source receipt. The signed and
clipped arms each saved and replayed all nine fixed current/uniform/linear
readouts at 80/240/720 charged work. Final work was 720/728 respectively;
launcher exit 0, wall 0.382537s versus the 180-second cap. The [proof
archive](../results/medium-dry-clipped-regret/own-proof/manifest.json)
contains both arms' snapshots, mass, events, receipts and launch timing.
This is a software proof only, not a Hold'em strength result. Next: publish
and GitHub-byte-verify the proof, and complete the source-receipt-head hosted
check before the one fixed 36-path 100k compute profile. Codex assisted;
human hands-on time not recorded.

The single fixed PR #100 36-path, three-repeat 100k-work compute profile ran
on November 20 (PST) after the proof archive was GitHub-byte-verified. All
12 game/seed/rule paths × three repeats completed 108 own captures/replays;
three workers exited zero. Internal whole profile time was 36.867s (<900),
launcher wall 37.145s, final charged work 100,027–100,114, and maximum
recorded worker high-water RSS 232,325,120 bytes. The frozen slowest-repeat
10m extrapolation gave fixed worker sums 1232.289/1231.593/1218.510s,
`T=1232.289s` and strict `2*(2*T+600)=6129.154s`, below 7200s. An independent
data-only recomputation matched the raw forecast exactly. The [full profile
archive](../results/medium-dry-clipped-regret/profile/manifest.json) retains
all 36 paths, snapshots, masses, events, timing, forecast and recheck.
Next: publish/verify these bytes, then publish a separate data-only admission
receipt before any 10m study. This is compute evidence, not poker strength.
Codex assisted; human hands-on time not recorded.

The PR #100 profile was published at `fb2e46f` on November 20 after
proof-head CI 44750299015 passed both Python jobs/hooks. All 295 profile
archive GitHub blobs matched the committed tree, and the clean reader passed.
The separate data-only admission at that clean head recomputed the unchanged
profile forecast: `T=1232.2885391607078s` and strict bound
`6129.154156642831s < 7200s`; status **admitted**. Its [receipt and raw
decision](../results/medium-dry-clipped-regret/admission/manifest.json) are
retained separately from the profile. Next: publish and verify the admission
bytes before the one fixed 12-path 10m matched-work run. No poker-strength
result yet. Codex assisted; human hands-on time not recorded.

The one admitted PR #100 own matched-work run finished on November 20 (PST)
at published admission head `1912440`, with all 12 prescribed paths, all 108
saved/replayed readouts, three workers exit zero, 287.779s internal and
288.118s launcher wall (<7200). Final work crossed 10m on each path, with
actual 10,000,014–10,000,169. The [complete own archive](../results/medium-dry-clipped-regret/own/manifest.json)
retains all policies, masses, summaries, events, timing and launcher receipt.
Own exact restricted-game final linear-average scores are provisionally
**negative**, pending comparison-only native scalar audit: medium/dry clipped
scores by seeds 20261371/72/73 are 0.072249/0.075562/0.074594 initial pots,
versus signed 0.035656/0.039542/0.035132. Low/wet clipped scores are
0.002512/0.002470/0.002447 versus signed 0.000946/0.000909/0.001146. All
candidate coverages are 100%, recall violations zero. The medium/dry absolute
1% median and 2.5% worst gates fail and both paired medians worsen. Next:
publish and GitHub-byte-verify this own evidence before any OpenSpiel audit;
retain the negative outcome, do not retry or tune it. Codex assisted; human
hands-on time not recorded.

After complete own raw policies were published and byte-verified, the single
pinned OpenSpiel 2.0.2 comparison-only scalar audit ran on November 20 (PST).
It checked all 108 fixed snapshots with 108 retained rows, exit zero,
55.094s internal and 55.452s launcher wall (<900). Maximum independent
own/native scalar error was `7.105427357601002e-14` chips, below the frozen
`1e-9`-chip tolerance. The [raw audit archive](../results/medium-dry-clipped-regret/native/manifest.json)
retains every row, runtime, launch receipt and log. No reference strategy
entered training. Next: publish/verify native bytes, then run the frozen
report and classify the already unfavorable own result with turn/river and
fixed-row diagnostics. Codex assisted; human hands-on time not recorded.

The frozen PR #100 report replayed all 108 own policy bytes after the
comparison-only native archive was published and GitHub-byte-verified.
Its [complete report](../results/medium-dry-clipped-regret/report/report.json)
classified the fixed comparison **negative**: medium/dry clipped 10m
linear-average median/worst 0.074594/0.075562 initial pots, failing 0.01/0.025;
paired median +0.036593 (worse). Low/wet clipped median/worst
0.002470/0.002512 pass absolute gates but paired median +0.001560 worsens
beyond +0.001. Each of six paired seeds worsened. Candidate coverage 100%
and recall zero; native maximum error `7.11e-14` chips. The
[result explanation](medium-dry-clipped-regret-result.md) gives fixed
turn/river loss decomposition, representative cards/actions/probabilities,
assumptions, limitations and a Terminal inspection command. Next: finish
exact-source local/optional/hosted qualification and review PR #100; do not
retry this failed experiment or promote a default. Any next strength question
requires its own prospective contract. Codex assisted; human hands-on time
not recorded.

Final PR #100 exact-head qualification at `16171aa` completed on November 20
(PST), after the negative report was published. Serial base Python 3.11 and
3.12 each passed 5,731 tests/73 skipped/150 deselected, Ruff, format,
strict mypy and pre/post source/runtime/lock guards. Optional 3.11 passed
2,589; optional 3.12 passed 2,587 with two expected skips; both passed the
pinned OpenSpiel 2.0.2, Numba 0.68.1 and installed Apache-2.0 license guards
before and after. All-file hooks passed. Hosted CI 44757177743 on exact
`16171aa` passed both Python jobs/hooks. The [complete final qualification
receipt](../results/medium-dry-clipped-regret/final-checks/manifest.json)
retains raw local/hosted logs, role receipts and source pins. Self-review
found only new isolated adapter/test/config code relative to main; historical
source pins and negative outcome remain unchanged. Next: publish/verify this
receipt, complete PR review and merge if eligible, then choose a distinct
prospective strength question. Codex assisted; human hands-on time not
recorded.

PR #100 history-merged at `50f979c` on November 20 after final receipt-head
CI 44764594652 passed both Python jobs/hooks and the solo self-review.
The negative clipped-rule outcome and all exact-source ancestors remain in
normal-clone history; issue #4 stays open. The next distinct question is
whether batch-one signed external-sampling updates improve the unchanged
exact-river learner over the published batch-four signed controls at the
same 10m charged work on the two **known** spots. The
[prospective B1 protocol](medium-dry-b1-updates.md) and machine contract fix
six candidate paths, three existing paired control seeds, 100k/1m/10m
crossings, historical absolute and paired gates, 18-path profile,
conservative forecast and caps before any B1 outcome. The earlier different
exact-game B1 advantage motivates a test but does not predict this spot.
Only JSON syntax, local links and diff format have been checked at this
planning stage; no B1 source, proof, profile or training exists. Next:
publish the protocol and open the focused draft PR before implementing the
isolated adapter. Codex assisted; human hands-on time not recorded.

On November 20 (PST), draft PR #101's isolated B1 source was implemented
after prospective protocol `9c8f613` was published. New
`scripts/medium_dry_b1/` and `scripts/study_medium_dry_b1.py` change only
batch size from four to one for the signed/linear/linear learner; historical
source and PR #100 control archives remain untouched. The new source
fingerprint is `64e92a742f865b6f19a87ad98e4b2ac3e94b2bf5ce8b26128fb2459a676669bd`.
Eight focused tests passed in 8.16s, covering exact B1 frozen-trainer
identity, same B4 information keys, published signed-control pairing,
fictional capture/replay, forecast and classification. Ruff and strict mypy
passed for ten new source/test files. These are focused software checks;
full exact-source base/optional/hosted qualification, formal proof, profile,
admission and poker training are pending. Next: publish tested source after
protocol-head CI, then run complete serial qualification. Codex assisted;
human hands-on time not recorded.

The same PR #101 tested source `47f2e74` completed exact-source qualification
on November 20 (PST). Serial base Python 3.11 and 3.12 each passed 5,739
tests/73 skipped/150 deselected, Ruff, format, strict mypy and pre/post
source/runtime/lock guards. Optional 3.11 passed 2,597; optional 3.12 passed
2,595 with two expected skips; both also passed pinned OpenSpiel 2.0.2,
Numba 0.68.1 and installed Apache-2.0 license guards. All-file hooks passed.
Hosted CI [44778469528](https://github.com/jimmy-sim/poker-ai/actions/runs/44778469528)
passed both Python jobs and hooks on exact `47f2e74`. The [complete source
receipt](../results/medium-dry-b1-updates/source-checks/manifest.json) retains
local/hosted logs, role receipts and the first pre-commit environment failure
before any commit. No B1 proof, profile or poker training has run. Next:
publish and byte-verify this receipt before the one fictional proof. Codex
assisted; human hands-on time not recorded.

After source-receipt CI 44782676606 passed both Python jobs/hooks, the one
formal PR #101 B1 fictional signal-game proof ran on clean `9e93f6a` on
November 20 (PST). It saved and replayed all nine fixed readouts at the
80/240/720-work crossings, finishing at 728 work. The launcher exited zero
in 0.557 seconds, under the 180-second internal cap; the [raw proof and
launcher record](../results/medium-dry-b1-updates/own-proof/manifest.json)
are retained. This checks software behavior, not poker strength. Next:
publish and byte-verify the complete proof before the one fixed 18-path
100k-work profile. Codex assisted; human hands-on time not recorded.

The fixed PR #101 18-path, three-repeat, 100k-work profile completed once
on November 20 (PST), after the fictional proof archive was byte-verified.
All 18 paths and 54 current/uniform/linear readouts saved and replayed;
final work ranged 100,000–100,034. Internal time was 18.597 seconds,
launcher time 19.103 seconds (<900), and maximum worker high-water RSS was
187,088,896 bytes. The predeclared slowest-repeat calculation gives fixed
worker sums 617.162/615.439/624.521 seconds, `T=624.521`, and strict
`2*(2*T+600)=3698.083<7200` seconds. The [complete raw profile](../results/medium-dry-b1-updates/profile/manifest.json)
is retained. This is a compute forecast, not a poker-strength outcome or
admission publication. Next: publish/byte-verify the profile and make a
separate data-only admission decision. Codex assisted; human hands-on time
not recorded.

After all 150 profile archive blobs and the clean reader were verified,
PR #101's separate data-only admission on November 20 recomputed the frozen
forecast from those published bytes: `T=624.5207492535935s`, strict bound
`3698.082997014374s < 7200s`, status **admitted**. The [admission
receipt](../results/medium-dry-b1-updates/admission/manifest.json) records
the exact input and command. Proof-head CI 44787891458 was cancelled by the
subsequent profile push; tested-source and source-receipt CI both passed.
No 10m B1 poker path has started. Next: publish/verify admission, then run
the single fixed six-path own comparison within its 7200-second cap. Codex
assisted; human hands-on time not recorded.

The one admitted PR #101 B1 six-path 10m own run completed on November 20
(PST) at clean `367a97f`, with all 54 fixed current/uniform/linear policy
readouts and scores saved and replayed. Final charged work was
10,000,012–10,000,037; internal time 142.760 seconds, launcher 143.139
seconds (<7200), and maximum worker high-water RSS 192,643,072 bytes.
The [complete own raw policies and scores](../results/medium-dry-b1-updates/own/manifest.json)
retain the six paths, launcher record and partial checkpoints. No new
OpenSpiel comparison or final B1-vs-B4 classification has occurred yet.
Next: publish and byte-verify all own bytes before constructing the fixed
comparison-only native audit. Admission-head CI 44789723277 was still
running at this checkpoint. Codex assisted; human hands-on time not
recorded.

After the complete B1 own archive was published and all 113 GitHub blobs
verified, the one pinned OpenSpiel 2.0.2 comparison-only scalar audit ran
on November 20 (PST). It retained all 54 rows, finished in 27.038 seconds
internally/27.438 seconds at the launcher (<900), and had maximum numerical
error `4.973799150320701e-14` chips (<`1e-9`). The [raw native audit](../results/medium-dry-b1-updates/native/manifest.json)
records the installed Apache-2.0 license hash, runtime and every row.
Reference values did not enter training. Next: publish/verify this audit,
then run the frozen report from published own, native and immutable B4
control bytes. Codex assisted; human hands-on time not recorded.

The fixed PR #101 report replayed the published B1 and immutable B4
policies and their independent scalar audits on November 20 (PST): all
108 cases complete, maximum combined native error `7.105427357601002e-14`
chips. The [negative result](medium-dry-b1-updates-result.md) records each
paired seed, memory/runtime/coverage, per-street contributions, fixed turn
decisions and assumptions. B1 medium/dry median/worst are
0.040639951/0.042400422 initial pots (limits 0.01/0.025), paired median
+0.001098290; low/wet absolute gates pass, paired median +0.000020953.
All six whole-coverage values are 100% and recall violations zero. This is
**negative** under the prospective rule; no retry or default promotion.
Next: publish/verify report, complete required final exact-source
local/optional/hosted checks and review PR #101. Codex assisted; human
hands-on time not recorded.

Final PR #101 exact negative-report-head qualification completed on
November 20 (PST) at `583291c`: serial local base Python 3.11 and 3.12
each passed 5,739 tests/73 skipped/150 deselected plus Ruff, format,
strict mypy and pre/post source/runtime/lock/report guards. Optional 3.11
passed 2,597; optional 3.12 passed 2,595 with two expected skips, both
with pinned OpenSpiel, Numba and installed Apache-2.0 license guards.
All-file hooks and hosted CI 44791539576 passed both jobs/hooks. The
[complete check receipt](../results/medium-dry-b1-updates/final-checks/manifest.json)
retains logs and exact pins. Next: publish/verify this receipt, complete
PR review and receipt-head CI, then history-merge if eligible. The poker
result remains negative. Codex assisted; human hands-on time not recorded.
