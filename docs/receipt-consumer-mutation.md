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
