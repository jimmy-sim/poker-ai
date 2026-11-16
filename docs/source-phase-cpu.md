# Follow the work inside source loading

The [complete reader measurement](reader-phase-cpu.md) puts about 78–79 parent
CPU seconds per cost read in source loading. That includes building and checking
scientific inputs, not just reading files. This follow-up asks which named stages
inside that boundary account for the work.

The [plan](https://github.com/jimmy-sim/poker-ai/issues/4#issuecomment-6918554952)
was published before implementation. The preceding PR now has all six final checks, a history-preserving
merge and a protected-main check. This follow-up still requires its own complete
source qualification before formal collection. This page describes software under development, not a timing result.

## What is measured

The original three complete reads stay intact. The software read has no selected
source root. Each cost read enters `compact_suit.cli.load` once, enclosing these
six sequential calls:

| Stage | Calls in each source root |
| --- | ---: |
| Previous scientific sources | 1 |
| Compact game construction | 2 |
| Sampled-parent archive validation | 1 |
| Original contexts | 1 |
| Original boundaries | 1 |

The two roots plus their children give 14 selected calls overall, capped at 32.
Children plus the source residual must equal inclusive source CPU. Source CPU
plus CPU outside that root must equal the complete read. Adding a root to its
children would count the same work twice.

Only the source module's selected aliases are temporarily observed. Two aliases
refer to modules; forwarding proxies select one member while delegating other
attributes to the unchanged original module. Reusable defining functions remain
untouched. Calls outside the active root are not timed. Ownership, ordered
inventories, clocks, restoration and separately saved event streams are checked.
All 439 preceding scientific files and historical inputs/results stay unchanged.

## Check the tool before using it

The observer passes 54 focused tests on both actual Python versions, including
proxy forwarding, defining-function identity, nested arithmetic, corrupt records,
process/thread ownership, partial output, late aliases and cleanup failures.
An actual archived fictional-game read agrees before/during observation and
correctly records zero source roots. It does not prove real cost-loader coverage.

The runner's initial unit suite found three inherited fixture assumptions: two
corruption tests erased already-empty software event streams, and one positive
check expected seven calls rather than fourteen. The corrected tests target the
first synthetic cost-shaped stream and the declared inventory. [The failed log
and exact code](../results/source-phase-cpu/qualification-history/initial-fixture-adaptation/manifest.json)
remain. A separate shared-cap fixture omitted the required arm order before it
could reach the clock check; [that failure](../results/source-phase-cpu/qualification-history/shared-cap-fixture/manifest.json)
is retained too. No runtime guard or scientific limit was relaxed.

Full source qualification, own-only proof, complete pair and final checks are
still required. The own proof separates actual archived software replay from
nested forwarding fixtures. Fixtures are not real source-loader timing or new
independent poker mathematics.

## Keep the original experiment

One ordinary/instrumented complete cost-audit repetition retains all startup,
source/license/publication checks, three original reads, 432 profiles, 1,152
fixed conditions, three reference workers, current normalization/recall caching,
restoration, validation and final writes. Exact complete calculated results must
match. Source qualification and own evidence are published before new reference
construction; complete raw evidence is published before analysis.

Limits stay 180 seconds for the own proof, 900 per complete child and 1,800
shared, with 120 seconds only for retaining a failure. Real replay stays on
Python 3.11.17/NumPy 2.4.6. The newer runtime can check software and saved data;
it does not establish bit-exact real-trajectory replay. OpenSpiel 2.0.2 remains
a pinned Apache 2.0 comparison reference whose outputs cannot enter training.
Its installed license must be read and recorded before fresh use.

This step introduces no optimizer, cache or new trajectory. One ordered diagnostic
pair cannot replace the production forecast or establish stable overhead, causal
speedup or playing strength. The 912.54/900-second budget and 2.390%/1% accuracy
failures remain.
