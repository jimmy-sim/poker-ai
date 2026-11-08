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
