# Train the coarse learner against finer own opponents

Prospective issue #4 comment
[6791111602](https://github.com/jimmy-sim/poker-ai/issues/4#issuecomment-6791111602)
registers the comparison before new Hold'em trajectories. Supporting work stays
in [PR #49](https://github.com/jimmy-sim/poker-ai/pull/49). This is a new source
cohort and a diagnostic research question, not an inherited training admission.
The [config](../configs/own-opponent-learning.json) fixes the complete design.

## Question and definition of done

Does a coarse agent learn a less exploitable policy when its own training
opponent can use finer legal own-card/public-board information? Keep the
agent's `texture_range_q8_b8` information groups, poker game, ranges, action
menus, updater and compute accounting fixed. No actual hidden opponent cards
are revealed. No reference strategy supplies learning targets or actions.

The [software foundation](exact-opponent-views.md) establishes the two mixed
views and an analytic counterexample. The [static river diagnostic](river-refinement-diagnosis.md)
ruled out two feature refinements on the saved strategies; it did not establish
that finer-opponent training helps. This experiment changes a training opponent,
not the learner's representation or the historical results.

Done means the complete fixed comparison, raw policies/books and partial/failure
records, own numerical replay, independent scalar audit, all-seed tables/plots,
source/runtime/compute evidence and a plain-English account of the result.
Missing or failed conditions remain failures. No default/fresh/global promotion
belongs to this experiment, even if its known-game diagnostic passes.

## Matched work controls

Both original known games and seeds 20261301, 20261302 and 20261303 are retained.
Use the unchanged `ReducedDispatchBatchTrainer`: IID B4, signed accumulated
regrets, linear regret weights and linear primary averaging. Exact simultaneous
uniform initialization costs two full-tree passes. Retain current, uniform-
average and linear-average policies at every prescribed checkpoint.

At logical total work W in 100k, 1m and 10m visited nodes:

| Arm | Actual training components used by this policy |
| --- | --- |
| Ordinary coarse self-play | One coarse/coarse path through W |
| Paired coarse control | Coarse seat 0 from one coarse/coarse path through W/2; coarse seat 1 from another through W/2 |
| Mixed treatment | Coarse seat 0 from coarse0/fine1 through W/2; coarse seat 1 from fine0/coarse1 through W/2 |
| Ordinary fine self-play | One fine/fine path through W |

The paired control isolates opponent information while matching the number of
learning games and work per retained seat. Ordinary coarse self-play is the
practical same-total-work comparison. Fine self-play is a separate information
control. Each component charges **both** players' updates and its warm start.
The final coarse policy discards finer-opponent rows. It does not average
different games, seeds or reference policies together.

Reuse the ordinary coarse path's W/2 checkpoint for the first paired-control
component. This is the exact same own trajectory, not an independent repeat.
Charge that prefix fully in the logical arm; count its execution only once in
actual total compute. Additional observations must preserve all state/RNG bits.

Five actual paths per game/seed give 30 paths:

- `coarse0`: capture 50k, 100k, 500k, 1m, 5m and 10m.
- `coarse1`, `mixed0`, `mixed1`: capture 50k, 500k and 5m each.
- `fine`: capture 100k, 1m and 10m.

Role 0 keeps the original scalar-seed PCG64 stream. Role 1 uses PCG64 with
`SeedSequence([seed,1])`; its paired control and treatment share this declaration.
Pair components can each overshoot by one whole iteration. Report their separate
iterations, prior work, endpoint work, warm work and overshoots; do not call the
combined overshoot one iteration or hide the second opponent's updates.

There are 108 raw work boundaries, 324 raw policies, 216 raw average ledgers,
30 warm origins and 108 new seat compositions. The 216 logical arm/readout/work
profiles include 108 aliases of raw ordinary coarse/fine policies, leaving
432 unique policy objects to score and audit. Extra raw mixed-opponent policies
are source/debug evidence, not additional coarse-agent candidates.

All 36 ordinary coarse/fine B4 work boundaries must match the original archived
work, guards, current/average probabilities and raw ledger fingerprints exactly.
Real trajectory work uses Python 3.11.17 and NumPy 2.4.6. Newer data-only
environments do not establish bit-exact replay eligibility.

## Fixed opponents and metrics

Read-only source loading confirms eight frozen **own** full controls per known
game: exact/coarse encoding × signed/clipped regrets × uniform/linear averaging.
Their IDs and policy hashes are fixed in the config. Expand all eight to the
same legal fine game. Use every control without choosing by its measured result.

All 72 final arm/readout profiles face every fixed control in both target seats:
72 × 8 × 2 = 1,152 conditions. Opponent policies stay fixed for each condition.
Report target-seat EV and the gain available to an own fine-information best
response against that opponent. These unilateral quantities differ from
self-play exploitability, which is half the sum of both best-response gains.

For every own profile, retain exact exploitability, within-partition gain, extra
information gap, the fixed-opponent river-only reply decomposition and all own
reply fingerprints. Chips and percentage of each game's initial pot must be
explicit. Fictional software values are never labeled poker measurements.

Primary comparison: final 10m logical work, signed/linear/linear coarse policy.
The paired-coarse minus mixed exploitability improvement must have a strictly
positive median separately in **both** known games. Also report the original
absolute accuracy limits per game: median at most 1% and worst at most 2.5% of
initial pot over all three seeds. Keep the original coverage requirement of at
least 95% uniform-reach average support and zero recall violations, together with
all source/independent numerical gates. Report whole and post-warm, all and river,
row and uniform-reach support separately; warm coverage is not learned support.

Report mixed versus ordinary coarse and fine controls separately. Do not rescue
a failed primary with a better seed, readout, checkpoint or opponent. These are
six known game/seed observations with dependent arms/readouts and reused prefixes,
not a population confidence interval or evidence about general Hold'em strength.

## Before any new real trajectory

1. Finish real source/context factories and the complete own capture, composition,
   archive, score, replay, report and partial/failure paths.
2. Finish the independent native inventory/schema/failure integration. OpenSpiel
   2.0.2, Apache-2.0, supplies scalar comparisons only. Recheck its pinned license
   recorded in [solver validation](solver_validation.md). Never request or load a
   native strategy into training.
3. Run a complete tiny-game 30-path/432-profile/1,152-fixed-condition software
   proof with all capture/books/archives/replay and native checks under one shared
   180-second deadline. Its two fictional sign mirrors and logical labels are
   software coverage, not new poker games or learned poker strength. Publish own
   evidence before constructing the native comparison.
4. Complete relevant local base/optional checks and both hosted CI jobs against
   the exact source. Added modules change the source cohort; old admission does
   not cover them.
5. Complete the fixed conservative forecast and publish a checked source-bound
   admission. Its artifact is required at each real worker boundary. Retain a
   denied admission instead of adjusting caps, seeds, gates or inventory.

Real own/native caps remain **7,200/900 seconds**, including all required stage
work. Complete/partial/failing own evidence must be published before any real
native construction. No long run has been admitted at this checkpoint.

## Fixed forecast rule, before measuring its outcome

Use all 24 original complete B4 path timings: two games × two encodings × two
regret rules × three seeds. For **each** new path, take the maximum original
complete-path seconds among all 12 historical B4 rows of its game. Give no
half-budget discount to the 5m components. T is the maximum sum under fixed
path-index-modulo-three worker assignment. The full historical cost includes
initialization; it is deliberately charged even for a shorter new component.

Measure three complete data-only own pipeline repetitions using explicitly old
own policies as cost stand-ins for all 432 contexts and 1,152 fixed targets.
Include source loading, writes, scoring, report and replay. D is their maximum
end-to-end time. Admission requires `2*(2*T+D+600) < 7200`.

Publish this own data-only evidence before native construction. Measure three
complete native cost repetitions over the exact same stand-in inventory,
including construction, reference comparison and replay. N is their maximum.
Require `2*(N+60) < 900`. Each forecast command has its own fixed 900-second cap;
these data-only commands train no new poker trajectory. A runtime forecast is a
conservative estimate, not a guarantee or evidence of playing strength.

No favorable subset, missing-stage estimate, cherry-picked retry or later rule
change can accept a failed forecast. Source/config or implementation changes
invalidate the corresponding source-bound checks/admission.

## Capture implementation checkpoint — November 11

The design generator, IID capture and raw-book/composition replay are implemented.
Tests exercise all 30 fictional paths, every raw export and every seat projection.
Added half-budget observations preserve all final training-state bits in those
fixtures. Tests reject missing/duplicate/changed coordinates, uncharged warm
work, wrong source/view, repacked inconsistent averages and warm masses, altered
compositions, unsafe member paths, overwrite and interruption. Partial members
remain on disk after an interruption. No real poker learning has run here.

Sixty-six focused checks pass in 3.62 seconds including the 32 original mixed-view
checks. The full score/archive/fixed-opponent/native/report/forecast/admission
pipeline is still pending; these unit tests are not its published full-shape
software proof. The current source cohort still needs its wider checks.

1. **Why compare two coarse paths as well?** Otherwise a difference could come
   from splitting training across two games rather than the opponent's information.
2. **Is a reused prefix free compute?** It saves duplicate execution. Every
   logical comparison still charges all the work used to create its policy.
3. **Would success mean a strong general Hold'em agent?** It would support a
   narrower known-game training result. Fresh games and a general agent still
   need their own separate acceptance evidence.
