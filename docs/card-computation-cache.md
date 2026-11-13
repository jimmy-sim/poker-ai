# Reuse deterministic card calculations without changing the audit

Prospective protocol, November13,2026; issue#4. Codex-assisted implementation.
The completed elapsed profile measured918,104canonicalizations and4,099,136best
hand evaluations in the parent. Inclusive frame times overlap:32.0032and35.2272s
are clues, not an additive speedup forecast. Both functions depend only on cards.

Before implementation or outcome, fix [the contract](../configs/card-computation-cache.json).
Use two bounded LRU stores:16,384exact ordered private/board tuple keys for
canonical_cards,65,536exact ordered card tuple keys for evaluate_best. Only
builtin tuples of builtin ints enter; no type-coercion, sorting or set keys.
Cache only successful immutable original results; preserve exceptions and
unsupported iterable behavior by invoking the original. If captured function
or constant dependencies change, fall back. Count every request, original call,
hit, unsupported/dependency fallback, successful insertion, eviction and size.
No RNG, policy, payoff vector, strategy or reference output is cached.

Install parent-only hooks on loaded poker_ai aliases and defining modules, so
later imports see wrappers. Restore all aliases even on failure. Spawned reference
workers remain the unchanged source-bound implementation, not a hidden optimized
worker. This deliberately tests a narrow parent change before production work.

Required tests cover original equality for all categories and5/6/7cards, suit/order
permutations, invalid/unsupported inputs and repeat errors, bounded eviction,
changed dependencies, counters, alias restoration including late imports/failure,
RNG and policy/equity invariance, missing/tampered source/checks and retained
partial failures. Full local base and relevant optional checks on both versions
plus both correctly pinned hosted jobs at ONE source head must be public before
formal data. Actual Python/NumPy guards, not matrix labels, establish runtimes.

Then ONE fixed uncached/cached complete saved cost0 native-audit pair:900seconds
per whole command,1800shared,1800finalCI+120save reserve before9a.m.Pacific.
The complete unchanged command includes initial/final own mathematical replays,
all three spawned native workers, loading, scalar checks and output writes.
Record all432scalar scores,1,152fixed conditions,three computed reads and worker
summaries; compare exactly. Preserve every raw command/journal/result and partial
failure. Fresh pair only, no retry or seed/cap change to improve the result.
Original published own evidence precedes any reference construction. Apache2.0
OpenSpiel2.0.2 remains comparison-only under its recorded pinned license.

Pass only if all identities match, counters reconcile and stay bounded, cached
hits are positive and original calls lower, and the cached whole command is
strictly faster. One ordered saved case cannot establish population runtime,
peak memory, training cost, a stronger agent or a new study permit. Even if it
passes, a production integration still needs fresh source gates, software proof,
all three own costs published before native costs, conservative full forecast
and checked admission. The old933.8894>900failure and runtime-label correction
remain. The latest real-study start has passed tonight; no new trajectory here.

Both modes install the same observation wrappers and record actual requests; the
uncached mode still performs primitive/dependency guards and counter updates.
That shared instrumentation adds work relative to an unwrapped historical command.
A measured reduction is relative to this instrumented uncached baseline. It must
not be relabeled as a measured production speedup, and cannot replace the fresh
three-repetition complete production costs or their maximum-based forecast.
