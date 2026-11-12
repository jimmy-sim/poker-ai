# Compact public own-range representation

## Definition of done, before implementation

Issue #4 [comment6816637695](https://github.com/jimmy-sim/poker-ai/issues/4#issuecomment-6816637695)
and [config](../configs/compact-public-range.json) define ONE candidate,
`texture_range_q8_own_q8_b8`. Implement an opt-in encoder, offline inspector,
structural/privacy/math tests and pure acceptance functions on explicitly
synthetic metrics. Stop before partition-size/compression measurements, saved-Q
regrouping or learning. Software fixtures never supply actual study admission.
Historical source/data stay intact; no subagents or automation are introduced.

## Exact feature

Keep the complete existing `texture_range_q8_b8` parent: private eight-bucket
history, public texture, own made-category history and opponent static-prior
blocked/loss/tie/win bins. Only on the river, append a summary of the acting
player's COMPLETE fixed declared prior using the PUBLIC BOARD ALONE.

Pool each alternative hand's unconditional normalized prior mass into ten
coordinates: blocked; high card; one pair; two pair; trips; straight; flush;
full house; quads; straight flush. Royal flush belongs to straight flush.
Public-card overlap means blocked; otherwise evaluate the alternative with the
visible board. Never filter alternatives using our actual private hand. No
actual opponent hand, policy, betting posterior, future card or reference output
is a feature input. The parent retains its permitted own-private-card inputs.

Reuse immutable canonical `RangePrior`/`RangeContext`: sorted physical combos,
positive finite weights, exact rational normalization and context SHA. Masses
sum exactly to one, blocked included; no renormalization. Standalone all-blocked
public summaries are explicit and valid. An encoder still requires a valid
acting own view in the context and compatible opponent mass through its parent.
The existing spot-loader arbitrary-large-integer precision limit remains; the
pinned spots have unit weights. No alternate prior is chosen from outcomes.

Use `min(7, floor(8*p))` rationally, without epsilon. Pack bin k into bits3k..3k+2,
blocked first: `sum(bin[k] << (3*k))`. Ten bins give one word in `[0,2**30)`.
Unpacking gives interval labels, not exact probabilities. Earlier streets append
`None`; their partitions stay unchanged. Keys are `[new version, complete parent
information key, word]`. The parent binds both full priors; the version prevents
historical-key reuse. The unchanged finite matrix adds texture/action history.
No global registration, serializer or default change; reject save/load that
could discard the range context.

Illustrative arithmetic, NOT a new policy result: equal QhKh/9c9d on Ts9s4d2h9h
is half pair/half quads, bins at indices2/8 equal4, word67,109,120. On9d it is
half blocked/half pair, word260. This notices removal without a per-combo vector.
It does not inherit the earlier diagnostic's19-of23 resolved-conflict count.

Only the added word is fixed width. Full keys/context storage, fraction
arithmetic, computation and strategy-table size have no memory-saving or
constant-cost guarantee. Pooling loses identity/tiebreakers/suit-rank links;
bin0 merges zero and small positive mass. Important rivers may still collide.
No sweep or post-outcome adjustment belongs to this candidate.

## Acceptance tests now

- Independent physical-set/exhaustive-five-card category oracle; exact weighted
  conservation, all-blocked/invalid inputs, decimal/large integer priors, every
  rational quantizer boundary, packing order/bounds and immutable values.
- Whole-input suit/range-order/weight-scale transformations; no actual-hand
  parameter; alternatives sharing actual private cards stay possible. No hidden
  opponent/future dependence, no added feature before river. Context/version
  separation, wrong-owner/terminal/out-of-range guards, serialization rejection.
- Constant payload across range sizes and an explicit pooled collision. On both
  known games verify parent-partition refinement, concrete legal menus/owners and
  zero imperfect-recall violations. Structural tree building is allowed; publish
  NO row counts, compression, runtime forecast or playing strength here.
- Complete SYNTHETIC metric grids, strict types/nonfinite rejection, all boundary
  gates, missing/duplicate observations/audits, wrong contexts/readouts/work/
  method and prior-full-contract mismatch. Pure functions ALWAYS return
  `actual_admission=False` and `fresh_global_admission=False`, even on a pass.

## Future acceptance, not run here

All five historical controls plus this candidate (six), same model/two spots.
Full own fused CFR+/linear at1/16/64/256/1024/4096 gives72 PLANNED profiles.
On BOTH games: exact exploitability<=.001 initial pots; candidate excess<=.005;
candidate rows<=75% raw-public; all-control average uniform-reach coverage>=95%;
zero recall and compatible menus/owners; independent value/BR error<=1e-9chips
for EVERY profile. Charge2*iteration*tree_nodes, <=200k nodes/game;900s own/900s
independent caps. Report full key/table/RSS costs separately. Only authenticated
full-stage evidence can permit a separately implemented sampled stage.

Future sampled: existing IID B4 reduced-dispatch trainer, signed regrets, linear
regret weights and LINEAR primary average. Retain current/uniform/linear at
100k/1m/10m visited nodes, seeds20261301–03:108 planned primary policies and
324 planned readouts, ALL audited. Simultaneous exact uniform initialization
costs two full tree passes; include it and both players' work. Cross each work
boundary in one complete iteration. Keep7200s own/900s native caps. Candidate
and exact primary median<=1%pot/worst<=2.5% on both games; candidate/public row
ratio<=.75; both average readouts' all-control coverage>=95%; zero recall and
all source/numeric/audit gates. Other readouts cannot rescue primary failure.
Report every signed candidate-baseline effect. Strict superiority requires
positive paired median gain in BOTH games; accuracy admission alone does not
assert dominance. The old mixed-training superiority failure is unchanged.

Report warm/initialized/sampled/fallback quantities and whole/post-warm,
all-street/river coverage separately. Warm coverage is not learned support.
The metric functions here check only the declared scalar thresholds; future
raw ledgers and policy/work replay must substantiate those reporting quantities.

Metric functions here authenticate NO raw artifacts. Future real factories,
runner/capture/archive/replay/partial retention, native schema/failure integration,
full local/relevant optional/both hosted checks, source-bound toy proof, fixed
conservative forecast and checked published admission precede ANY trajectory.
Publish complete/partial/failing own evidence BEFORE comparison-only native
outputs; read/record pinned permitted solver licenses. Never load reference
strategies into learning. Old seeds/caps/failed gates/defaults stay unchanged;
fresh/global work needs its own later prospective contract. None starts here.

## Status

Prospective protocol7ace4a3 preceded implementation. The public feature,
context-bound opt-in encoder/finite adapter, offline inspector and pure metric
assessors are implemented. All 98 focused tests pass in 4.10s; whole-repository
Ruff lint/format and strict mypy 629 files pass. The original sources remain
unchanged. An initial strict-typing/format pass caught two local annotations
and formatting issues; corrected before proceeding, without feature/gate changes.
Full immutable02b7c9b checks pass on Python3.11.17/NumPy2.4.6 and3.12.15/NumPy2.5.4:
each2,914passed/58skip/149deselect,528.28/509.72s. Lint/format/mypy629/hooks and
before/after clean HEAD/runtime/module/source guards pass. Relevant ALL-EXTRAS
suites (new candidate plus unchanged parent) each165pass9.17/8.44s; this is not
the entire optional historical suite. Exact [local receipts](../results/compact-public-range-checks/local/summary.json)
and the two public-encoding examples are retained. Source fingerprint
f1f91bc0b107cf71685bfb510937ba1d78889c540a41ea50c2723aa6787f2111 is unchanged
by this later documentation/evidence checkpoint. Both final hosted jobs must
pass before history-preserving merge; [PR #54](https://github.com/jimmy-sim/poker-ai/pull/54)
records their conclusions.
No row-count/compression measurement, policy, exploitability, native audit or
stronger-agent result. Codex assists; no personal practice/time/mastery inferred.

The two structural fixture observations 1013/1049, pinned to the earlier known
game, have equal parent keys and distinct new keys. The test constructs only
observations; it loads no saved Q/strategy values. Both structural games have
compatible concrete menus and zero recall violations. The pooled 5c/5h example
intentionally keeps the same word; this is not exact-board information.

Whole-input suit relabeling preserves the public histogram/bins. Full keys
still bind literal physical priors, so namespaces may differ under a suit
renaming. Compare the induced partitions up to that namespace. The public
histogram ignores final board order; the complete parent still retains the
legitimate earlier-street reveal history. Neither fact removes parent context.

After updating your checkout, inspect the encoding:

```sh
.venv/bin/python scripts/inspect_public_range_feature.py 9h
.venv/bin/python scripts/inspect_public_range_feature.py 9d
.venv/bin/python -m pytest -q tests/test_public_range.py tests/test_public_range_acceptance.py
```

The first word is 67,109,120 (half pair/half quads); the second is 260 (half
blocked/half pair). These are interval labels, not action probabilities, chips
or strategic recommendations. Run these commands directly in Terminal.

Three questions to practice:

1. **Why pool categories?** The extra key has ten bins regardless of range size,
   while an ordered compatibility vector grows with the range. Whole memory
   costs and useful strategy compression remain unmeasured.
2. **Why not filter with our private hand?** We are describing what the opponent
   can think we represent. Alternative own hands are mutually exclusive
   hypotheses; the opponent does not get our actual private cards.
3. **Do these tests admit training?** No. They establish feature/contract behavior.
   Real source-bound runner, replay/audit, forecast and published admission are
   still needed; the old learning failure/default remains unchanged.
