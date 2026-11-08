# Cache the immutable game-state interface

Issue [#4](https://github.com/jimmy-sim/poker-ai/issues/4), November 8, 2026.
Codex-assisted; personal hands-on time not recorded. Depends on PR #24.

## Fixed question and scope

The row-cache profile leaves repeated `actions`/`child`/state-wrapper overhead.
Precompute an immutable node graph for the already materialized bounded game:
menus, chance tuples, actor/information/payoff metadata and child pointers.
Keep row-policy math, original external sampler, updater, RNG calls, initialization
and rules frozen. No reach/strategy/RNG state belongs in cached game nodes.
Only values/interface and child routing are preserved, not Python object identity.
The game arrays must stay static during training, as in these pinned simulations.

Build a fresh graph per candidate trainer and charge construction to initialization
time. Record the number of static node records prepared separately from unchanged
CFR recursive/exact-initialization visits. This adds O(N) objects; no total-memory
saving or global Hold'em scalability claim. Use acyclic child references to avoid
parent/context reference cycles. Full traversal still uses the unchanged trainer.

## Gates before timing

Publish checked code/config before measurements. Exhaustively compare every node
and legal edge in both games and both representations to the original ArrayState:
terminal/chance flags, actions, actor/information/payoff/chance probabilities,
types, invalid-access ValueErrors and child node IDs. Cached nodes are immutable.
Object reuse must not affect the sampler, which reads only this interface.

Then compare all 96 external cells against the frozen row-policy parent at exact
iterations 1/2/16/64/128/1001: raw array bytes, exported policies, RNG, visited-key
sets and CFR work. No tolerance replacement or seed filtering. Preserve failures.

Use the same contemporaneous 708 timing rows, alternating parent/candidate order,
and six instrumented cases. Full cells are unchanged and shared in both forecasts.
Retain every paired observation and report slow cases, not just the median ratio.
Same 1000 external / 16 full extra iterations, max-of-three forecast to 10m visits,
2× guard and 7200s own-stage cap. Separate 1200s adapter/parity/profile cap includes
all setup, validation, timing, serialization and instrumentation. No scoring or
strategy-winner selection. Record source/lock/hardware, runtimes and counters.

The legacy paired validator may be reused through an explicit internal schema
adapter (`dense` = reference, `rows` = candidate); public data uses descriptive
`parent`/`nodes` names. Renaming validator roles must never change values, counters
or which implementation runs. Old source and evidence remain frozen.

## Definition of done and next decision

Opt-in backend, exhaustive interface checks, exact trajectories, complete paired
profile, rerunnable report, tests/typing/lint/hooks/CI and journal/work-log update.
Report regeneration validates saved timings, not reproduction of wall time.
No default, strength, river-cause, fresh/global or learning-run admission.
If guarded training still exceeds the cap, keep the large study off and measure
another justified compute change. If below, measure remaining pipeline cost.
The user authorized continued work through the day; subsequent milestones keep
their own prospective protocols and source identities.

## Implementation checkpoint

Thirty new tests and 65 previous focused checks pass. All 48,604 matrix nodes
and 48,600 legal edges are checked in the real-game unit gate. Reverse-level
construction also passes a permuted-node-ID fixture; cached nodes are frozen and
contain no parent/context back references. Direct value/error/type/edge checks
exclude Python object identity, which intentionally differs when objects are reused.
Ruff lint/format, strict mypy (256 files) and all-file hooks pass. Full local
suites pass: 1039 all-extras tests each on Python 3.11.17 / 3.12.15; base-only
1006 pass / 24 optional skips. Hosted CI and the fixed complete parity/profile
remain pending at this checked-code checkpoint.

### Three questions to explain this cache

1. **Why can game nodes persist while policy rows cannot?** A fixed game's menus,
   chance probabilities, terminal payoffs and information labels do not depend on
   current regrets. Policy probabilities do, so that cache still ends each pass.
2. **How do we check this does not change the game?** Exhaust all interface
   properties, errors and child routes in the four finite matrices, then compare
   raw learning arrays, policies, RNG and CFR counters at fixed checkpoints.
   This is bounded evidence, not proof of arbitrary mutable or unlimited games.
3. **Is construction free or a memory reduction?** No. Initialization includes
   fresh graph construction, with O(N) node objects recorded separately from CFR
   visits. Forecasts keep that setup time; no RSS or global scalability claim.

## Recorded complete run

Clean checked source `19910267a99da5d8dd37f91f9d5f7855839ba88a` completed the
entire fixed run in **213.256995 seconds** on Python 3.11.17 / NumPy 2.4.6.
All four exhaustive interface matrices pass (48,604 nodes / 48,600 edges), then
all 96 external trajectories / 576 exact checkpoints pass. All 708 timing rows
and six instrumented cases pass state/RNG/work checks. Paired order is balanced:
144 parent-first and 144 nodes-first observations. No outcomes were discarded.

| Game / representation | Paired loop ratio min | Median | Max |
|---|---:|---:|---:|
| low / exact | 1.040 | 1.482 | 1.668 |
| low / range mass | 1.105 | 1.483 | 1.545 |
| medium / exact | 1.133 | 1.318 | 1.479 |
| medium / range mass | 1.116 | 1.321 | 1.363 |

Each group has 72 observations; ratios are parent time / cached-node time.
Overall median **1.356×**; every observed paired loop ratio exceeds one, with
minimum 1.040×. These dependent local timings are not a population confidence
interval. Setup is outside these loop ratios and included in the forecast.
Measured graph construction spans 0.004272–0.040813s in low and
0.031665–0.085439s in medium, with all observations retained.

| Backend | Training-only forecast | 2× guarded forecast | Decision |
|---|---:|---:|---|
| parent | 8168.894s | 16337.788s | exceeds 7200s |
| nodes | 6216.028s | 12432.056s | exceeds 7200s |

[Raw receipt](../results/cached-node-profile/profile.json) and
[scripted table](../results/cached-node-profile/report/tables.md) retain all
rows, paired ratios, counters, source/lock/runtime and profiler functions.
All five report files regenerate byte-identically on Python 3.12.15. Report
regeneration checks recorded evidence; it does not reproduce historical wall time.
The instrumented medium candidate still spends 0.121683s cumulative in
`_policy_row`, 0.084339s in `select` and 0.073645s in `_apply` during its
0.363878s loop. Nested cumulative times overlap and must not be added.

```sh
.venv/bin/python scripts/profile_cached_nodes.py --report results/cached-node-profile/profile.json
.venv/bin/python -m pytest -q tests/test_cached_nodes.py tests/test_node_profile.py
```

Self-review: static metadata lifetime differs from one-pass policy-row lifetime;
full interface/error/edge checks deliberately exclude object identity. Node records
and setup never replace or discount CFR visits. Existing trainer/math/evidence
stay frozen. This is a solo Codex-assisted self-review, not independent human review.
The first commit-hook attempt lacked `uv` on PATH; the retry with the project
environment passed. Local checks pass; hosted CI remains separately pending at
this evidence checkpoint. The implementation was published before measurements.

## Next decision

The large learning study remains off. Serial training alone exceeds the cap even
before scoring/checkpoints. Next define and test parallel execution of independent
cells, preserving every cell, seed, work threshold and update equation. Measure
contention, process startup, tree construction and aggregate resource cost rather
than dividing the serial forecast by CPU count. A new prospective config must
precede measurements. No default, strength or river-cause claim follows this profile.
