# Follow the remaining reader work

The [checkpoint measurement](checkpoint-replay-cpu.md) found about 97–98 CPU
seconds per cost read outside its selected checkpoint callsite. This follow-up
separates three current phases: loading the scientific inputs, loading the saved
own-policy stand-ins, and replaying the own archive. It does not change a poker
decision or introduce a faster implementation.

The [prospective plan](https://github.com/jimmy-sim/poker-ai/issues/4#issuecomment-6914870507)
was published before implementation. No formal phase measurement has run.

## The boundaries

Only three aliases in `compact_suit.cli` are observed: `load`, `load_standins`
and `replay`. Their reusable defining functions stay unchanged. The original
software read calls replay once; the two cost reads call all three phases in
order. That gives seven selected calls, plus three whole-read clocks. The fixed
call limit is 16. Calls elsewhere are outside these selected boundaries.

The selected phases are sequential. Their CPU times plus the remaining read CPU
equal the complete read CPU, within the existing 1e-9-second roundoff allowance.
A phase includes all its nested work and measuring overhead; it does not identify
one serializer or leaf function. Parent CPU, worker CPU and elapsed time remain
separate.

## Check the observer first

The new observer reuses the checkpoint observer's clock validation, read lifecycle
and restoration machinery. Synthetic fixtures check forwarding, call inventories,
disjoint arithmetic, corrupt records, errors, ownership, caps and cleanup.
They do not establish real cost-loader behavior. A separate test runs the actual
saved fictional-game reader and requires identical complete calculated results.

Before formal collection, all four local roles and both hosted jobs must qualify
the complete source on the intended runtimes. The own-only proof then compares
ordinary and observed archived software reads under the existing 180-second cap,
with synthetic loader-forwarding checks separately labeled. This is saved
software evidence, not new poker evidence or cost-branch coverage.

## Keep the complete comparison

One ordinary/instrumented pair retains the original three reads, 432 profiles,
1,152 fixed conditions, three reference workers and complete validation path.
Limits stay 900 seconds per child and 1,800 seconds shared; the 120-second failure
reserve only saves partial outputs. Own evidence must be public before the fresh
reference, and raw pair evidence before analysis. Exact complete results,
inventory and restoration are required. No favorable retry or smaller workload.

All 436 preceding scientific source files and historical data stay unchanged.
OpenSpiel 2.0.2 remains a pinned Apache 2.0 comparison reference; its strategies
cannot enter training. The installed license was read again on November 16 in
both optional environments; both match SHA-256
`cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`.
[Solver versions, licensing and comparison-only rules](solver_validation.md)
remain in force. A saved-data report must reproduce on the second runtime
with game execution blocked before final checks and merge.

This diagnostic cannot replace the production forecast. The 912.54 / 900-second
budget failure and 2.390% versus 1% accuracy failure remain. One ordered pair
does not establish stable overhead, a causal speedup or competitive full-game
strength.
