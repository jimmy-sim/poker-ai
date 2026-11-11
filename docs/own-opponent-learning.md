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

## Complete command implementation — November 11

The new entry point is `scripts/validate_opponent_learning.py`. Software and
real training use the same three spawned workers, raw event journal, collector,
book replay, seat composition, scoring and archive path. The independent scalar
comparison also has three fixed worker partitions. Every complete own receipt
contains 324 raw policies, 216 raw books, 30 warm origins, 108 new compositions,
432 scored profiles, 216 logical arm points and 1,152 fixed target conditions.
The report retains every seed/readout, with separate whole/post-warm support.
Its three figures show primary learning curves, paired seed differences and
fixed-opponent gaps. Fine fixed replies can use extra information; their gap
is not self exploitability.

The prospective [cost supplement](../configs/own-opponent-cost-standins.json),
registered in [comment6792824092](https://github.com/jimmy-sim/poker-ai/issues/4#issuecomment-6792824092),
specifies old OWN stand-ins before any cost forecast measurement. Labels50k/100k
reuse old100k, 500k/1m reuse old1m, and5m/10m reuse old10m. All original source IDs,
archive/member hashes and actual old checkpoint work are retained. A mixed cost
table copies old coarse own rows and old fine opponent rows; those tables were
never learned together. Both projected raw books and their warm origins remain
available for exact replay. No new iteration, regret guard, first crossing,
learning RNG stream or training work is fabricated. These COST records cannot
enter the learner or satisfy the original36 B4 barriers.

The command clock begins before numerical imports and includes child startup,
preflight, prerequisites, worker work, archives, replay and final report writes.
The parent records the subsequent administrative measurement/copy separately.
Software own publication, independent comparison and final replay share180s on
one host. Each own/native cost repetition has900s. Actual own/native study caps
remain7200/900s. Interrupted receipts, raw messages, archives and temporary
write bytes are retained; missing or changed evidence denies advancement.

The required order is:

1. Publish exact source with local base/optional checks on311/312, the relevant
   slow archive check on both, both hosted jobs and retained raw logs.
2. Run and publish the complete fictional `software-own` evidence before
   `software-audit`, within the shared180s clock. Fictional means no poker.
3. Run all three `cost-own --repetition 0/1/2` commands and publish own results
   before any `cost-audit` construction. Run all three independent repetitions.
4. `forecast` fully replays all own cost archives and verifies scalar audits,
   publication, source and complete command clocks. Use the unchanged fixed
   conservative formulas above. Retain a failed forecast; do not select retries.
5. Publish a passing forecast, then `admit`, then publish that compute permit.
   `study` checks it before workers; workers also bind its unchanged bytes and
   the original311.17/NumPy2.4.6 runtime before initialization. Ordinary controls
   must match all36 original B4 boundaries before scoring. Publish complete,
   partial or failing own evidence before `audit`.

At this implementation checkpoint,175 focused base checks pass in18.04s, with
10 optional checks skipped and one slow check deselected. The slow check passes
separately in34.42s, decoding all180 required original own members without a new
learner or reference construction. Ruff/format/strict typing pass for the new
modules/tests. With optional dependencies,185 focused checks pass18.24s. The
fictional command integration includes actual spawned
workers; mocked schema tests are explicitly not independent numerical evidence.
The previous missing-work-field test failure is fixed by binding raw books to
their original saved checkpoint work records, rather than inventing fields.

All three draft figures were visually inspected after correcting crowded ticks
and a colorbar overlap. Their three numeric files remain byte-identical through
the plot-only corrections. Wider exact-source local/optional/hosted checks,
formal published full-shape proof, actual forecasts and compute admission are
still pending. No new real trajectory or model-strength improvement is claimed.

## Coverage-tolerance correction before advancement — November11

Source627427b completes both full local base2576/optional2643 suites and the
relevant archive check on both runtimes. Both hosted43004096870 jobs pass2576
tests with58skips/149deselections and one retained historical warning, in
906.60/887.49s. The full PR checkout source inventory equals627427b. Raw logs,
hashes and local/hosted receipts are retained in
[source-627427b-checks](../results/opponent-information/source-627427b-checks/receipt.json).

Final protocol review catches a mismatch before the new formal proof, forecast
or any real trajectory: coverage replay used1e-9 instead of the already-frozen
unitless1e-12. New consistently repacked whole/post-warm archive fixtures with
coverage error5e-10 are wrongly accepted before the repair (2failed/1passed).
The correction rejects them at1e-12, separately from chip scores at1e-9. Error
maxima keep separate units. The within-tolerance5e-13 fixture still passes;
all3 regression cases pass after the fix. The earlier full checks remain valid
for their historical source, not the corrected source. Complete corrected local/
optional/hosted checks are required again. No threshold, seed, work cap, learning
rule, historical result or agent default changes.

Corrected focused checks:178base/10optional skips/1slow deselection23.51s;
188optional/1slow deselection23.45s. Full repository lint/format/strict typing pass.

## Truthful partial-work flags before advancement — November11

Coverage-corrected source7f191d4 completes full base2579/optional2646 each and
the relevant archive check on both runtimes. Hosted43006909815 BOTH SUCCESS:
2579pass/58skip/149deselect/1historical warning,638.31/866.85s. Local pytest
434.84/421.63s base,487.04/470.06s optional,50.76/48.89s slow. Retain complete
logs/hash receipts in [source-7f191d4-checks](../results/opponent-information/source-7f191d4-checks/receipt.json).

Interruption review then reproduces an initialFalse poker-work flag surviving
an attempted/partial study. No actual real study has run. Before any worker can
initialize, the command now persists attempted/unknown progress and unknown
completed work. Raw warm/capture/completion acknowledgments establish observed
work lower bounds, taking the maximum per actual path rather than adding its
repeated cumulative checkpoints. Missing messages remain unknown; they never
prove zero work. Native construction attempts similarly retain unknown/confirmed
state. A checked compute permit is distinct from study completion. Hard-kill
retention preserves the last truthful running receipt even without an exception
handler. Complete own scalar/work gates and native publication gates are unchanged.

Synthetic REAL-label tests use mocked permits/source/worker events, not actual
real factories, learning or reference construction. Before repair:2failed8deselected
0.88s; afterward4 training/native interruption cases pass8deselected0.82s. The
clock timeout case preserves unknown flags too. Focused182base/10optional skipped/
1slow deselected21.54s,192optional/1slow deselected20.85s; repository lint/format/
strict typing pass. Source7f191d4 remains preserved, but these source changes
require fresh complete checks. No formal new proof/forecast/permit/real trajectory
yet; mathematical thresholds, seeds, learning rules and caps stay fixed.

## Published full-shape software rehearsal — November11

Checked source4878eb9, sourceSHA2fdf2e2844cce31d1c25fc4bc23b5088a46efa53c74f03b07c720cd2c48c5a4a:
own stage14.940791666s, raw own publicationf969a04 BEFORE native construction;
native stage7.353254167s, full shared software clock25.260755625s<180. Complete
324raw/216books/30warm/108composed/432unique/216logical/1152fixed replay passes,
chip and unitless errors0 and policy/book bits exact. Actual comparison-only
OpenSpiel2.0.2 verifies all432/1152, maximum scalar discrepancy
1.1102230246251565e-16<1e-9, publishedf84d698. No reference actions exported or
training on reference output. Base312 replay of the published own archive passes.
The checked published software gate accepts this fictional proof only.

Before actual cost measurements, use fresh ignored output directories for each
of the three own repetitions, preserving a clean source checkout for every
entry. Publish byte-identical copies at canonical cost/{0,1,2} paths afterward;
retain original outputs/scratch and exact command arguments. The same output
choice applies to native repetitions after all own evidence is published. Child
source/load/archive/score/report/replay/construction work is timed; subsequent
administrative publication copying is separate, as with the command measurement
receipts. Output location changes no coordinate, seed, inventory, tolerance or
forecast rule. No cost forecast or real run is admitted by this software result.

## Complete fixed forecast — November11

All3own and3native cost repetitions complete and are published with exact-copy
manifests. Maximum D=233.21964283299894s, N=371.6489725419997s. Every native run
verifies432/1152, maxerror1.8474111129762605e-13chips. Actual forecast command
408.798313416s<900 replays all own costs, checks every native receipt and87input
seals, and computes T=610.943356249918s from ALL24 original complete B4 timings.
Every new path uses its game's maximum of all12 old full10m paths; no half-work
discount. Guarded own2*(2*T+D+600)=4110.21271066567<7200; guarded native
2*(N+60)=863.2979450839994<900. Both strict forecast gates pass unchanged.
The published checked compute permit is still required before any real worker.
This estimate is not actual training runtime or strength/default/fresh/global
admission. Keep the full actual caps and all original B4/numerical/quality gates.

## Persisted permit failure — November11

The first actual study attempt on source4878eb9 fails preflight in8.845484625s,
before any worker initialization or poker training. The command overwrote the
permit builder's89-file input_sha256 inventory with19 routine input pins; the
reader correctly rejected the mismatch. Exact failed parent/child/log evidence
is retained in failed-admission-4878eb9; the prior complete source cohort is
preserved byte-identically in source-4878eb9-pipeline with original-path hashes.
Historical relative paths are reproduced in an isolated checkout at f5771e7.

Separate permit_input_sha256 from routine command input_sha256. A new synthetic
CLI persistence-to-reader regression reproduces the original failure;39 related
tests pass after repair. Missing/edited seals, legacy overwritten inventories,
changed caps/source and changed historical input bytes remain rejected. No real
learner or solver executes in those tests. The fixed scientific config, seeds,
inventory, budgets, updater and acceptance thresholds remain unchanged. Fresh
complete corrected-source checks/proof/costs/forecast/published permit must precede
another real attempt; old source evidence cannot be inherited.
