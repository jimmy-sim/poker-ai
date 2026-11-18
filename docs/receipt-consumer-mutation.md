# Check whether receipt consumers mutate prerequisites

The [prospective issue #4 protocol](https://github.com/jimmy-sim/poker-ai/issues/4#issuecomment-6981335805) fixes one read-only archive audit on each locked runtime. The preceding [fresh-output audit](receipt-prerequisite-identity.md) found seven identical, separately owned prerequisite graphs. It did not inspect what receipt readers do to one of those graphs after loading it.

## Definition of done for this step

- A fresh Python 3.11.17/NumPy 2.4.6 child and a fresh Python 3.12.15/NumPy 2.5.4 child each run the original `reduced_study_run.read_saved` on `results/reduced-batch-study/own.json`, including its six nested timing receipt loads and one direct prerequisite load. Each complete command, startup included, stays under 180 wall seconds. The exact seven-call order is required.
- Preserve every original source, admission, saved scalar, work-grid and replay validation. The wrapper forwards the original arguments, result and exceptions. It observes each graph at loader return, after each timing receipt returns and after the archive read returns. All closed graph and semantic witnesses for an object must match its first observation. The original read must return the observed direct object. Input pins, own receipt bytes and clean source must match before and after. Unknown shapes, unexpected calls and failed/partial reads reject and remain in logs.
- Publish exact audit source and local, optional and hosted qualification before actual archived reads. Publish raw receipts before any data-only report; reproduce that report on both actual runtimes with original readers blocked. Complete final local and hosted checks before a history-preserving merge.

The audit does not share a prerequisite object between consumers. A pass establishes only that the seven objects in this read were not changed by their own consumers. It is not a cache admission or speed estimate. A later complete ordinary/reuse comparison needs its own prospective protocol and must preserve original validation, work counters, scalar and computed replay, context identity and the original 180/900/1800/120-second caps. The failed 912.54/900 forecast, 2.390%/1% known-game accuracy and rejected full-context-copy result remain failed.

The tool writes partial `child.json` observations and `child.log` before finishing, plus `outer.json` after a child exit or timeout. Codex assisted with the audit source and synthetic tests; human hands-on time is not recorded.

## Exact source qualification — November 18

At source commit `dd53e99`, the two clean local base suites each pass 5,582
tests, with 71 skipped and 150 deselected. Ruff, formatting, strict mypy on
837 files, commit hook configuration and all-files hooks pass. Both complete
69-file optional scopes pass 2,491 tests each on the pinned 3.11.17/NumPy
2.4.6 and 3.12.15/NumPy 2.5.4 environments. The complete installed
OpenSpiel 2.0.2 Apache-2.0 license was reread before optional tests in both
environments: 11,358 bytes and SHA-256
`cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`.
It remains a comparison-only validation dependency.

Hosted [CI #565](https://github.com/jimmy-sim/poker-ai/actions/runs/44339006308)
passes both jobs: each has 5,582 tests passed, 71 skipped, 150 deselected and
one warning. The actual Python and NumPy selections, every uv interpreter
selection, job IDs, raw logs and the PR merge checkout tree are verified. The
entire merge tree equals the source commit tree. The prior 458-file scientific
source fingerprint remains
`b475bfefb92963f25458d97260264743ff4d751b4513c307529742eaf10fc97d`.
The [six-role archive](../results/receipt-consumer-mutation/source-checks/manifest.json)
retains all source checks and operator receipts. An earlier dirty-checkout
attempt failed nine fresh-child imports; an initial 68-file optional pass
omitted three newer report tests. Both are retained and excluded from
qualification.

This qualifies the audit software, not the mutation question on actual
archived inputs. The checked source record must be public and verified before
the two bounded reads begin. No cache, saving, new trajectory, reference
strategy or stronger play is admitted here.

## Archived consumer audit and data-only result — November 18

The checked source was published at `9b40113` before the two archived reads.
The [raw archive](../results/receipt-consumer-mutation/raw/manifest.json) was
published separately at `1e9714f` before this report. The six raw files are
byte-for-byte copies of the ignored originals in `/private/tmp`; the manifest
records their hashes and sizes. Neither child loaded OpenSpiel. Each original
`read_saved` returned `completed_own_native_pending` and replayed all 480
profiles, 432 mass reconstructions and 216 current observations with zero
reported chip or unitless error. The source, lock, own receipt and declared
input pins matched the pre-read values after the read.

| Runtime | Whole command, including startup | Nested receipt checks | Complete-read checks | Result |
| --- | ---: | ---: | ---: | --- |
| Python 3.11.17, NumPy 2.4.6 | 84.845 s / 180 s | 6 unchanged | 7 unchanged | Pass |
| Python 3.12.15, NumPy 2.5.4 | 73.026 s / 180 s | 6 unchanged | 7 unchanged | Pass |

Each of the seven fresh graphs has the same complete witness
`5ddfac5c71c46fbc4895867b2de072e3bea45d16c84c9274b8eae044ca88c5bf`
and semantic inventory hash
`04a485bdcbea8ea4f79be5ea1723602390282e3a59510812ef19bbe2d09e7053`
on both runtimes, covering 148,034 tracked mutable objects and 148 arrays per
graph. Every nested graph matches at loader return, after its timing receipt
returns, and after the entire archive read. The direct graph matches at loader
return and after the archive read; it has no timing receipt caller.

The [data-only report](../results/receipt-consumer-mutation/report.json) is
reproduced byte-for-byte by `scripts/report_receipt_consumer_mutation.py` on
both locked runtimes. The renderer blocks `poker_ai` imports and rejects
any such module already imported. It verifies all raw member hashes, statuses,
caps, stage equality, exact call order and cross-runtime semantic equality.
Four focused tests cover an unmodified archive, blocked reader import, a
changed raw byte and a changed stage with a correspondingly updated hash.

This establishes nonmutation only for the observed graph, consumers and saved
archive. It does not establish that a *shared* graph is safe, preserve a work
counter under reuse, or save CPU. A separately preregistered complete
ordinary/reuse comparison remains necessary before sharing can be admitted.
The failed 912.54/900 forecast, 2.390%/1% known-game accuracy and rejected
full-context-copy result remain failed. Codex assisted with the audit and
report; human hands-on time was not recorded.
