# Test validated sharing inside the complete reader

The [prospective issue #4 protocol](https://github.com/jimmy-sim/poker-ai/issues/4#issuecomment-6986270276)
was published on November 18 before this branch's implementation or archived
collection. [PR #91](receipt-consumer-mutation.md) established that seven
fresh prerequisite graphs in one saved-archive read have identical contents,
separate mutable ownership, and no observed consumer mutation. It did not
pass one graph to multiple consumers.

## Definition of done

1. Run all six nested and one direct original `frozen_batch_inputs.prerequisites`
   calls per earlier archive root with their original arguments and validations.
   Keep the first fully loaded graph as that root's donor. For every later site,
   finish its own original loader, require exact complete graph and independent
   semantic equality, and pass the donor to the unchanged consumer. Require
   exact seven-call order, six substitutions, post-consumer and post-root
   equality, the same direct object returned by the archive reader, and no
   cross-root or cross-process state. Restore all aliases on every exit. An
   unexpected call, changed input, alias, shape or graph rejects. Do not skip
   source/admission checks, archive decoding, receipt validation or replay.
2. Publish source after tests and complete clean qualification: fast base suites,
   all applicable optional suites, Ruff, format, strict mypy and hooks on actual
   locked Python 3.11.17/NumPy 2.4.6 and Python 3.12.15/NumPy 2.5.4, plus
   both hosted jobs with exact source-tree and runtime proof. Preserve failures.
3. Only after public source qualification, run one reference-free own
   saved-archive proof under the original 180-second outer cap, startup
   included. Publish its raw result and verify the publication before starting
   any reference-bearing complete pair.
4. Run one fixed ordinary-then-validated-share complete pair on actual locked
   Python 3.11.17/NumPy 2.4.6. Preserve the original three read scopes, two
   archive roots, 432 profiles, 1,152 fixed conditions, three reference
   workers, all replay/scalar/source/admission checks and the original seeds
   `[20261301, 20261302, 20261303]` in the frozen batch inputs. Every
   ordinary and shared root makes seven original loader calls; each shared
   root substitutes the donor at six sites after the independent call passes.
   Require exact complete ordinary/shared/predecessor identity, including
   all work counters. Retain the original 900-second per-child, 1,800-second
   shared outer, and 120-second failure-save caps. Any gate failure rejects
   the candidate and remains published; do not rerun for a favorable outcome.
5. Publish complete raw pair evidence before a data-only report. Reproduce
   its numerical exports on both locked runtimes with original reader,
   numerical and reference entry points blocked. Complete final local and
   hosted checks before history-preserving merge.

This is a sharing *behavior* test: all original loaders and validations still
run, so even a pass cannot establish CPU savings. A later skipped-work
optimizer would need a separate prospective contract and proof. One ordered
pair cannot establish stable runtime effects. No new Hold'em learning,
strategy, default, fresh/global admission or real-money use is involved.
Reference outputs stay comparison-only and never enter agent strategy or
training. The failed 912.54/900 forecast, 2.390%/1% known-game accuracy and
rejected full-context-copy result remain failed. Codex assisted with this
protocol; human hands-on time was not recorded.

## Local wrapper implementation — November 18

The first source step adds a root-local `ValidatedShare` capture. It calls
each original loader, compares its fresh complete graph and semantic witness
with the first donor, checks that donor and fresh graph share no mutable
storage, then forwards the donor. The existing receipt-caller and complete
archive checks run on that forwarded object. Five new synthetic cases cover
14 original calls across two independent roots, consumer mutation, a changed
fresh result, original-loader failure and alias conflict; the existing four
consumer-audit cases still pass. The nine focused tests, Ruff, formatting and
strict typing pass on both locked runtimes. An initial synthetic fixture
returned `None` as a fake graph and failed two wrapper tests; correcting that
fixture made the intended graph contract explicit. These are software checks
only. No archived proof or complete comparison has run.

The bounded own runner and complete-pair adapter are now implemented locally.
The own runner requires a committed, public six-role source-check manifest,
clean locked runtime, exact new script bytes and unchanged pins before it
can read archived inputs. Its fresh child and enclosing command retain
partial receipts under the original 180-second cap. The pair adapter requires
the public own proof and runs the original three-read cost audit using the
old independent numerical identity, with two separately scoped archive
captures per child. It binds the original 900/1,800/120-second caps, 432
profiles, 1,152 fixed conditions, three native worker summaries and all
work counters. Synthetic tests cover both pair modes, restoration on reader
failure, work-counter rejection and no favorable retry after a failed first
child. Fifteen focused tests pass on both locked runtimes with Ruff and
strict typing. No real own proof, complete pair or reference construction
has run on this branch. Full clean source qualification and hosted CI remain
pending before any archived read.

## Exact source qualification — November 18

The checked implementation commit `04d19ed` has passed both clean local
base roles on actual locked Python 3.11.17/NumPy 2.4.6 and Python
3.12.15/NumPy 2.5.4. Each has 5,597 passed, 71 skipped and 150 deselected;
Ruff, format and strict mypy on 842 files pass. Both complete fixed 69-file
optional roles pass 2,502 tests each, as do the all-files hooks and exact
source/runtime guards. The comparison-only OpenSpiel 2.0.2 Apache-2.0
license was read before each optional run. Hosted
[CI #572](https://github.com/jimmy-sim/poker-ai/actions/runs/44370320685)
passes on both actual locked runtimes with the same base count and a whole
checkout tree identical to the checked source tree. The
[six-role record](../results/validated-prerequisite-sharing/source-checks/manifest.json)
retains the raw logs, runtime and license receipts, official hosted metadata
and a hash verifier. This is source qualification only. The real reference-free
own proof and complete ordinary/shared pair have not run; a shared graph and
savings are not admitted by these software checks. Next: publish and verify
the six-role record before the bounded own proof.

## Reference-free own proof — November 18

After the six-role record was public and its committed GitHub blob matched,
the one fixed saved-archive proof passed on actual locked Python 3.11.17 and
NumPy 2.4.6. The [raw receipt](../results/validated-prerequisite-sharing/own/manifest.json)
shows a clean `c9eb713` proof head, seven original loader calls, six
root-local donor substitutions, six unchanged after-caller witnesses and
seven unchanged after-archive witnesses. The original 480-row saved replay
has zero chip and unitless error. The complete command took 95.85 seconds,
within the unchanged 180-second outer cap; no reference output was
constructed. The raw child and outer receipts are the evidence for this
bounded read. They must be published and byte-verified before the one fixed
complete ordinary/validated-share pair. This own proof cannot establish
complete result identity or CPU savings.

The fixed complete pair subsequently stopped in its first ordinary child
because the launched base environment lacked Numba package metadata. Its
[data-only failure report](validated-prerequisite-sharing-result.md) links
the published raw bytes and records the failed gate; no validated-share
child or favorable retry followed.
