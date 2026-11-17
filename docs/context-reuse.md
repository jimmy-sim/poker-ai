# Reuse exact contexts within one archive check

[Prospective protocol](https://github.com/jimmy-sim/poker-ai/issues/4#issuecomment-6950002262) — November 17, 2026. No implementation or fresh collection
exists at publication. PR #85 is merged and its final verification is
[archived](../results/parent-archive-cpu/final-ci/manifest.json).
This is a validation optimization experiment, not agent training.

Question: can validation reuse a completely built context collection within one
archive check while preserving fresh-result semantics, every input check and all
calculated results? The checked parent-archive diagnostic puts 8.88/8.75 CPU
seconds in the two materialized context calls, plus a prior-full residual that
includes another context-generator traversal. This is an opportunity to test,
not a saving estimate. Full/prior decode remains required and is not cached.

Static source facts, not new experimental results:
- compact_sampled_own.gather calls its inputs.game_contexts(root, scope).
- compact_fixed_inputs.replay_sources later calls old_inputs.game_contexts(root,
  the same software/real scope). Both refer to compact_sampled_inputs.
- compact_sampled_prior.verify subsequently consumes its imported contexts(root,
  software=False) iterator. This defining factory is also used by game_contexts.
- Context/ScoringContext/ArrayTree are frozen dataclasses, but arrays, diagnostics
  and nested MatrixTree/SpotTree objects remain mutable. Frozen is insufficient
  for safe sharing. Context.binding alone omits fields and is not a full object
  mutation witness.

Proposed bounded scope:
1. Reuse only under the caller-held compact_fixed_inputs.replay_sources archive
   root, only the explicitly declared materialized calls and prior iterator.
   Every defining function stays untouched; all outside-root calls pass through.
2. First materialized call executes its complete original factory. Cache only a
   complete, independently isolated template after success. Failed/partial work
   never populates an entry. Subsequent materialized and prior-iterator requests
   may reuse that exact input collection with fresh isolated results in original
   order; unsupported/unproved cases fail closed rather than silently changing
   scientific work. First construction/generator behavior remains original.
3. Each request reruns the original compact public-range contract/check_inputs,
   including all seven actual pinned input bytes and range-context identities.
   Bind root/scope, source/function/dispatch identity and complete result contents,
   not just a top-level hash. Keep full original 128 scientific input pins and
   whole source checks at the complete command's required boundaries.
4. Template/results share no mutable arrays/dicts with each other or prior
   returns. Verify template mutation witnesses before/after use and root exit.
   Tests cover all dataclass fields and nested MatrixTree.source, array dtype,
   shape/bits/writeability and relevant internal alias relationships. Unknown
   object/array types, changed inputs, mutated template or mismatched bindings
   reject before reuse. Caller mutations cannot contaminate subsequent returns.
   Use the bounded graph rules below; generic deepcopy is not assumed to
   preserve NumPy flags or cross-array memory semantics.
5. Keep one serial PID/thread owner; no nesting/reentrancy/late-alias leaks.
   Cache lifetime is one archive invocation, cleared on every exit. No reuse
   across complete reads, processes, references, training or user gameplay.
6. Expected complete cached cost-command inventory (verified against the frozen
   caller-held source before implementation): two cost roots; per root one complete original
   materialization and two reuse requests (second dictionary, prior iterator).
   Thus two misses/four hits overall, zero software-read roots. Report both
   root-local inventories and all factory/input/template/clone checks. The
   original full scientific profiles/conditions/scoring/native work stays fixed.

Acceptance before any fresh real cost comparison:
- Unit forwarding and error identity; exact object/array field equality; object
  isolation and caller/template mutation tests; changed file/source/scope/key,
  partial factory/iterator, thread/process, alias and cleanup rejection cases.
- Actual tiny factory Context outputs plus a declared tiny MatrixTree/SpotTree
  fixture exercise nested source fields, not only plain ArrayTree. Compare own
  terminal/policy metrics with independent tiny sums, without reference imports.
- A formal own-only proof under unchanged180s compares the actual archived
  software read before/after and separately exercises real software factories
  under a labeled synthetic root, with no real cost-loader coverage or new
  independent poker strength claim. Exact args/results/clocks/clearance retained.
- Freeze all447 previous scientific files at fingerprint
  3c343e8f8963a4d73e0ea6a277db13d57f06918ba45cb1d5216be151e7089e5d.
  A new helper/entry/config would bind450 files; no core edit or dependency.
- All four immutable local roles and two exact-source hosted roles, actual patch/
  NumPy/all uv/entire tree; tested exact launch/retention/publication/report tools
  public before own proof. Installed pinned reference license read/recorded.
- Publish every own raw byte and verify publication ACTUAL EXIT0 before reference.

One fixed complete ordinary/reuse comparison:
- Original repetition0, three reads/432 profiles/1152 conditions/three native
  workers per arm; original ranges/actions/seeds/ordering and all validation facts.
  Only explicitly proved repeated context construction may be reused; no archive
  verdict, policy, scalar/native answer or trajectory is cached.
- Existing caps180own/900perchild/1800sharedouter/120failure-save unchanged. All
  source/input/template/copy checks and cloning costs count. Retain every partial/
  failing outcome; no favorable retry, reseed, shortened work or cap extension.
- Require complete scalar/calculated identity vs both arms and old ccd8e493...
  identity, full original inventories, expected cache counts and complete cleanup.
- Publish all raw files before timing interpretation. Show complete command and
  parent/worker clocks, memory/copy costs if already captured, both dependent
  reads and all cache facts. One ordered pair is not a stable causal speedup.
  An unfavorable or tiny result is retained. No rollout/default/forecast admission
  based solely on this diagnostic; the old production/accuracy gates remain.
- Three data-only numerical exports reproduce on both actual runtimes with all
  newly identified numerical/factory/clone entrypoints and captured aliases blocked,
  zero forbidden calls, raw unchanged, all figures inspected. Four final local/
  two same-head hosted checks precede history merge and protected-main checks.

Next decision: only a fully correct result can support a later prospective
integration and unchanged full conservative forecast. The912.54/900 forecast and
2.390%/1% accuracy remain failed. No new Hold'em trajectory/stronger/global claim.
Keep one coherent PR through plan, implementation, qualification, evidence,
report and final checks; publish closing PR85 receipts in that next substantive
batch. Actual dates/AI assistance/no invented personal practice or human hours.


## Exact object and call contract

The implementation may use explicit graph traversal, a memo and raw-field
allocation of the known dataclasses. It must not rerun dataclass constructors as
a substitute for an exact clone. The allowed dataclasses are Context,
ScoringContext, ArrayTree, MatrixTree, SpotTree, Spot, SpotState, RangeHand,
NoLimitRules, ActionAbstraction, HoldemState, Action, ActionRecord, Pot, Deck,
and software Tree/ToyState. Every declared field is traversed; extra instance
attributes and unknown subclasses reject. Only the fixed Street/ActionKind enums,
built-in scalar types, tuple/list/dict and NumPy bool/int64/float64 scalars/arrays
are supported. Dict key/value order and internal repeated-object relationships
are preserved. Cyclic graphs reject. Scalars retain exact types and bit patterns.

Arrays must have a non-object, non-structured supported dtype and contiguous
layout whose exact shape, strides, dtype and flags can be preserved by isolated
copying. Distinct ndarray objects with overlapping storage reject; repeated
references to the same array are preserved by the memo. This deliberately bounded
support is checked against the actual factory outputs during proof/collection;
unsupported real layouts produce a retained failure, never an unrecorded fallback.
Every clone must have the same full graph witness and no mutable buffers or
containers shared across graphs. Witnesses include all fields, dtype, shape,
strides, exact bytes, writeability and alias topology. A cached template is checked
before and after reuse and on root exit, including exceptional exits. A caller's
mutations may change its own returned graph; they must not change the template or
later returns. Root exit clears entries even when validation or cleanup fails.

One complete ordinary arm has two roots, four original materialized factory
calls, two original prior iterators, no hits/misses, no added request guards or
clones, and zero final entries. One complete reuse arm has two roots, six
requests, two original materializations, zero original prior iterators, two
misses/four hits, six added original public-range input guards, two template
clones/four return clones, and zero final entries. Both arms record each root
and each of its three requests: eight boundaries per complete arm, each with a
start/end event. A new cap of 32 boundaries bounds this new ledger; the older
1,024-call observer cap is unchanged. Events retain PID/thread, wall/CPU clocks,
request kind, status, cache facts and cleanup. Generator request events begin on
consumption, not creation; complete status requires all 12 original ordered keys
and exhaustion. Partial consumption and deferred use are covered by tests and
cannot count as complete collection. Outside-root calls preserve original
arguments, lazy behavior, results and exception identity.

The own-only proof compares the actual archived software CLI read before and
with hooks (zero roots in both). A separately labeled synthetic root exercises
the actual software factory in the declared dictionary/dictionary/iterator order
for each of two roots: 12 contexts per request, two misses/four hits when enabled.
It tests nested source fields using a tiny actual MatrixTree/SpotTree fixture and
independent own terminal/pure-reply sums. This is software correctness evidence,
not real cost-loader coverage, reference validation or new poker strength.
No numerical speed target is introduced: complete correctness is required; the
measured outcome can justify a later prospective integration/forecast or reject
reuse as too costly. It cannot relax either existing failed research gate.

## Qualification and reporting

Keep one coherent PR. Publish this protocol before implementation, then the
complete tested source and exact tested administrative tools before own proof.
All four immutable local roles and two exact-source hosted roles must pass using
actual Python 3.11.17/NumPy 2.4.6 and Python 3.12.15/NumPy 2.5.4 as applicable,
all uv selections and entire tested checkout-tree equality. Any software retry
retains previous failures and the actual execution identity of carried successes.
Read and record the installed pinned OpenSpiel license before fresh reference use.

The fixed pair remains ordinary then reuse, original repetition zero. Own raw
publication must verify with actual zero exit before the pair, and every pair raw
byte must be public and verified before analysis. Report three data-only numerical
exports (reads.csv, commands.csv, summary.json) and figures for complete clocks
and root/request work. Independently reproduce all three exports byte for byte on
both actual runtimes while numerical, construction, graph/clone and captured-alias
entry points are blocked, with zero forbidden calls and unchanged raw inputs.
Inspect every figure. Final four local and two same-head hosted roles precede a
history-preserving merge and protected-main checks. No production/default rollout
or fresh Hold'em trajectory follows this diagnostic alone.


## Implementation and review — November 17

The isolated implementation uses a bounded graph copier and witnesses every
supported field, array layout and internal alias. Only the declared caller-held
module/function aliases are installed. Event-callback reentrancy rejects before
construction, and the root clock includes releasing the cached template.
The prior iterator clock includes decoding performed by its consumer between
yields; it must not be described as pure context-construction time.

The new config retains all 128 original input pins and binds 450 scientific files
while preserving all 447 predecessor bytes. Both arms must produce identical
full context witnesses as well as the complete historical numerical identity.
The runner retains actual read boundaries, raw events and worker clocks, marks
all output diagnostic-only, and authenticates the full saved pair before export.
No fresh formal proof or comparison has run yet. The 103 saved-report guards
cover construction, numerical work, clones, caller hooks and captured aliases;
all resolve and restore on both actual runtimes with zero forbidden calls.
Six process, five preflight, four retention and ten synthetic-publication cases
pass. Full immutable local and hosted source qualification remains required.


## Complete source qualification — November 17

Source `9ebd5900667674564751d806e5e0c9673f83da75` preserves all 447
predecessor scientific files and binds 450 at
`901415dc66139b48866bdf07dba9231e63fbaf3d0267d87af33b31028e4999a9`.
[All six source roles and ten exact tested tools](../results/context-reuse/checks.json)
are retained before any new formal proof or comparison:

| Role | Python / NumPy | Actual pytest result | Pytest seconds |
| --- | --- | --- | ---: |
| Local base | 3.11.17 / 2.4.6 | 5,379 passed, 70 skipped, 150 deselected | 776.37 |
| Local base | 3.12.15 / 2.5.4 | 5,379 passed, 70 skipped, 150 deselected | 737.41 |
| Local optional | 3.11.17 / 2.4.6 | 2,287 passed | 470.71 |
| Local optional | 3.12.15 / 2.5.4 | 2,287 passed | 407.94 |
| Hosted base | 3.11.17 / 2.4.6 | 5,379 passed, 70 skipped, 150 deselected | 1,179.75 |
| Hosted base | 3.12.15 / 2.5.4 | 5,379 passed, 70 skipped, 150 deselected | 1,174.25 |

Both hosted logs confirm all uv-selected runtimes and actual checkout
`25f98f4ed881e62c870888404a143c49c5fcb261`, whose complete tree
`e05a6b116b1757cb0875c53a47654bd27907a5d4` equals the source checkpoint.
[Hosted run](https://github.com/jimmy-sim/poker-ai/actions/runs/44103138056).
The first Python 3.12 execution reached the unchanged 25-minute limit at 93%;
its complete log, official timeout annotation and run/job metadata are retained.
Only that unchanged-source software role was retried. The carried Python 3.11
success keeps actual execution `134108220465`, attempt 1, with identical original
timestamps and log bytes; logical job `134125639866` is not another execution.
The successful Python 3.12 execution is `134125636021`, attempt 2.

All fixture bytes, earlier 93-guard setup records, final 103-guard setup and
operator hashes are archived. The complete installed OpenSpiel 2.0.2 Apache-2.0
license was reread before fresh use; both environments match the existing
[central license record](solver_validation.md#solvers-versions-and-licenses),
11,358 bytes / SHA256
`cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`.
Reference outputs remain comparison-only. No source, seed, scientific cap or
acceptance criterion changed for CI. Published qualification and exact tools must
verify successfully before the formal own-only proof; no new proof/comparison or
training has run at this publication boundary.
