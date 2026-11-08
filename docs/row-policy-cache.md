# On-demand policy rows, unchanged training behavior

Issue [#4](https://github.com/jimmy-sim/poker-ai/issues/4), November 8, 2026.
Codex-assisted; personal hands-on hours not recorded.

## Definition of done and scope

The prior profile found repeated full-table policy construction in sampled passes.
Add an **opt-in** external-sampling backend that constructs a row only when the
frozen pass first visits it, then reuses that row for the rest of the pass. Keep
the padded action width and reduction/division operations. Discard the cache
before the next target pass. Preserve the original updater, sampler, adapter,
initialization, averaging, clipping, RNG calls and work accounting. No menu-cache,
JIT, action/range/bucket change, new strength measurement or default change.

Stop after exact parity and a contemporaneous paired profile, reporting the
unchanged compute gate honestly. Do not launch the later learning study even if
training-only cost improves: scoring/checkpoint cost remains unmeasured.
The [config](../configs/row-policy-profile.json) pins the prior profile and fixes
all counts/orders before outcomes. Frozen historical source and evidence remain
unchanged, including the existing terminal commands.

## Parity before profiling

Use every one of the 96 original external cells: both known games, exact and
range-mass groups, all eight clipping/regret/average-weight rules and all three
seeds. Compare fresh dense and row-cache trainers at iterations 1 (charged exact
initialization), 2, 16, 64, 128 and 1001. Require exact array **bytes** for regrets,
strategy sums, current and average policies, RNG state, sampled-key set, counters
and work. A floating tolerance is not an acceptable replacement for this gate.
Retain an incomplete/failing run instead of choosing favorable seeds or relaxing
the rule. These are short software regression traces, not strength experiments.

Unit tests additionally cover padded widths/rounding, zero-regret uniform fallback,
cache reuse within a pass and invalidation between passes, clipped/signed and
independent time weights, zero-support policies, stale-cache regressions and
unsupported traversal. Existing update-equation and legacy CLI tests must pass.
Full-state exports continue to use the inherited dense validator. The lazy callback
validates visited rows; it does not promise immediate detection of externally
corrupted unvisited memory before that row is visited or exported.

## Timing and forecast

After parity, repeat all original 140 dense cells three times: 420 rows. Pair each
of the 96 external cells with a fresh cached run: another 288 rows. Alternate
first backend by `(external cell index + repeat) % 2`, balancing order over the
full grid. Use the original 1000 external / 16 full additional iterations, charging
and timing exact initialization separately. Full cells use unchanged dense code
and are shared when computing both 140-cell forecasts; do not invent a full-backend
speedup. Each timing repeat and each paired backend must match state/work hashes.

Instrument the four original profiler cases plus cached variants of the two
external cases: six instrumented cases. Instrumentation stays outside timing
estimates; require identical final state/work. Save the top 25 cumulative functions
and do not add overlapping cumulative times. Record cache size, when applicable,
as a diagnostic only; no total-memory-saving claim.

Use the same per-cell maximum of three estimates to 10m visits, 2× planning guard,
and 7200s own-stage cap. Retain all individual paired timing ratios; summarize
the median across all paired observations with no confidence/population claim.
Fresh timings compare both implementations on this environment, not against the
old historical wall times. Forecasts are extrapolations, not bounds. Setup, scoring,
checkpoint and native-audit cost remain unestimated by this training forecast.

The separate 1200s measurement cap includes prerequisite checks, parity, setup,
timing, instrumentation and serialization. Keep incomplete evidence on failure or
timeout. Publish checked code/config before new evidence; record source, lock,
hardware, actual counters and runtimes. Report validation recomputes predictions
from recorded timings, not wall time. Verify report regeneration under both Python
versions, local checks and hosted CI, and update the journal/work log in the PR.

## Next decision

If exact parity fails, debug the first differing checkpoint before timing. If the
forecast still exceeds the cap, keep the full study off and use the new hotspots
to decide the next optimization. If training-only cost falls below it, measure
remaining pipeline overhead before admission. Neither outcome establishes a
stronger agent or which training rule caused the saved river weakness.

## Implementation checks and explanation

The backend retains padded axis-1 reductions and division. Since `maximum(R,0)`
ensures nonnegative weights, it omits that redundant check; it retains finite
and legal-weight validation for accessed rows. A positive row does not construct
a uniform fallback that would immediately be overwritten. Zero-weight rows use
the same padded legal-row normalization. No update or RNG operation is removed.

At the implementation checkpoint, 32 new tests and 33 prior focused checks pass,
including extreme padded rounding, cold/warm all-rule per-step state checks,
real-game prefixes and synthetic complete/tampered profiling receipts. Full local checks pass **1009 all-extras tests** each Python 3.11.17/3.12.15;
base-only **976 passed / 24 optional skips**. Ruff lint/format, strict mypy
(251 files) and hooks pass. Both code-head hosted CI jobs passed in [42508619364](https://github.com/jimmy-sim/poker-ai/actions/runs/42508619364).
The measured result follows below.

### Three questions to explain this change

1. **Why can a cached row be reused?** Regrets are frozen until the target pass
   finishes. The cache is local to that pass, then discarded before the next
   player's policy can reflect updated regrets.
2. **Why keep zero padding in a sum?** Floating reductions can group additions
   differently when the array width changes. We preserve width and require exact
   tested state/RNG equality rather than assuming approximate probabilities imply
   the same sampled trajectory.
3. **Does a faster backend make the agent stronger?** At the same confirmed
   updates/work it should produce the same strategy. This bounded parity/profile
   can enable the controlled learning study; it does not establish its results
   or bit identity forever/on every machine.

## Recorded result

All **96 trajectories / 576 checkpoints** match exact array bytes, exported
policies, RNG state, visited-key sets and charged work. All **708 timing rows**
and **six instrumented cases** complete from clean
`4cc0cc4928afb93881604d214d38d4a2eea50bb3` in **323.345249s**, below 1200s.
Every timing repetition/backend and instrumented case matches its parity digest.
[Raw evidence](../results/row-policy-profile/profile.json),
[table](../results/row-policy-profile/report/tables.md).

| Contemporary backend | Training-only forecast | With fixed 2× guard |
|---|---:|---:|
| Dense | 15,228.659s / 4.230h | 30,457.318s / 8.460h |
| On-demand rows | 8,219.338s / 2.283h | 16,438.675s / 4.566h |

Both return **`training_only_guarded_forecast_exceeds_cap`** against 7200s.
The lower forecast is not an observed full-study runtime, and no study/default
is admitted. Actual measured median dense/cache loop-time ratio across all
288 paired observations is **1.695×**. All observations remain, including slower
cached repeats. By game/group, medians are low exact **1.452×**, low range mass
**1.073×**, medium exact **3.103×**, medium range mass **1.950×**. The low candidate
individual ratios span **0.888–1.140×**; the optimization is not uniformly faster.
No confidence interval, statistical population inference or universal speed claim.

The six profiler cases preserve matching state/work. In the fixed medium cached
case, `_policy_row` has 17,176 calls, `actions` 96,122 and `child` 33,473 over
1000 extra iterations. Their cumulative times overlap and are not added.
The unchanged state adapter still reconstructs menus and child wrappers; this
is the next measured target, before rerunning the same compute gate. The current
change intentionally leaves that adapter untouched. The ordinary row validation
and RNG selection also remain costs, so another change is not guaranteed to fit.

All five report files regenerate byte-identically on Python 3.12. This verifies
recorded-data reporting, not repeatability of wall time. Old correctness/profile
terminal commands remain valid. The bounded parity does not prove all possible
states or unlimited trajectories on every architecture; learning quality and
river-cause attribution remain unmeasured.

The user subsequently authorized continued project work through the day. This
PR ends at the fixed parity/profile boundary; the next measured optimization
belongs in its own protocol/PR with the old implementations frozen.
