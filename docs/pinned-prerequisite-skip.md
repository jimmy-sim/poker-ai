# Test a guarded skip of repeated prerequisite loads

The [prospective issue #4 contract](https://github.com/jimmy-sim/poker-ai/issues/4#issuecomment-6999526861)
was published before this branch's source change or new collection. The
[source audit](prerequisite-skip-contract.md) mapped six nested and one
direct original prerequisite calls per archive root. The completed
[validated-sharing pair](validated-sharing-count-gate-result.md) ran all
seven loaders per root and passed exact result and work identity; it
established safe forwarding behavior, not a saving.

## Question and definition of done

Can one fully validated, root-local graph stand in for the six later
original loads while an independent guard detects changed inputs, source
or graph, and the complete reader retains its scientific result and
downstream work?

1. The first nested call in each archive root must run the original
   `frozen_batch_inputs.prerequisites` in full and establish a complete
   graph and independent semantic witness. Before and after that load,
   bind the exact root, arguments, pinned input/config/lock bytes, and
   scientific source inventory. Before each of the next five nested and
   one direct calls, recheck those bytes, source inventory, original
   importing aliases, exact call order and the donor's complete witness;
   return only the donor. The original receipt caller still performs its
   own validation on the returned graph. Recheck donor and pins after
   each caller and archive root. No cross-root or cross-process state;
   restore all aliases on success and every exception.
2. Synthetic tests must reject changed root, arguments, pin, source,
   receipt, archive, graph, call order or alias; unsupported graph shape,
   original-loader failure, partial output and consumer mutation. A skip
   cannot silently use a cached graph after any failed check. Retain
   exact source/lock and explicit runtime guards. The first proof stage
   is software-only. Both clean locked base roles, both applicable
   optional roles, Ruff, format, strict mypy, all-files hooks and both
   hosted jobs must qualify the exact source. Publish and byte-verify
   every qualification member in a normal clone before archived input.
3. Run one fresh reference-free own saved-archive proof under the
   original 180-second enclosing cap, including startup. Publish and
   GitHub-byte-verify its raw evidence before a reference-bearing pair.
   Failure stops and is retained; no favorable retry.
4. Read-only preflight the pinned optional Python 3.11.17/NumPy 2.4.6/
   Numba 0.68.1/OpenSpiel 2.0.2 runtime and full installed Apache-2.0
   license before one ordinary-then-guarded-skip complete pair. Preserve
   fixed seeds `[20261301, 20261302, 20261303]`, two independent archive
   roots per child, three reads, 432 profiles, 1,152 fixed conditions,
   three native workers, all existing source/admission/replay/scalar
   checks and original 900-second child, 1,800-second pair and
   120-second failure-save caps. Ordinary makes 14 original loader calls;
   guarded skip must make two, one per root, and record 12 explicit
   guarded returns. Require the **entire original scientific and
   downstream work identity**, context and published predecessor hash to
   match exactly. Only the separately observed original-loader/skip
   counters are intentionally different. A changed saved work counter
   fails; do not relax the gate after seeing the outcome.
5. Publish exact raw pair bytes before a data-only report. Reproduce the
   report on both locked runtimes with poker, numerical and reference
   imports blocked. Complete final local, optional and hosted checks
   before history-preserving merge.

The guard's byte inventory must cover every file the original loader
validates, including archived own/native receipts and traces, and its
source inventory must cover the original checked implementation. A
partial inventory is a failed software gate, not permission to skip.
Byte checks plus one validated construction are a proposed scoped
equivalence argument, to be challenged by mutation tests and one exact
complete comparison. This is a behavioral candidate; one ordered pair
cannot establish stable CPU savings. No new training, strategy,
default/fresh/global admission or real-money use is involved. Open-source
reference output remains comparison-only and never enters training.
The original 912.54/900 forecast, 2.390%/1% known-game accuracy and
rejected full-context-copy, missing-Numba and count/publication pairs
remain failed. This study will likely exceed a few hours across source
checks and a complete pair; its cheaper first gate is synthetic software
qualification, with no archived read before publication. Codex assisted
with this protocol; human hands-on time was not recorded.

## Local software implementation — November 18

The [guarded wrapper](../scripts/guarded_prerequisite_skip_support.py) now
builds a closed byte snapshot from 14 declared pins, the 458-file current
scientific source, archived source maps in six pinned JSON receipts, and
the four new qualified operator scripts. The union is 486 paths, including
eleven historical files absent from the current scientific inventory.
A first nested call runs the full original
loader; later five nested and one direct site use the donor only after
snapshot, alias and complete graph checks. The unchanged receipt callers
still run. The new [own proof](../scripts/prove_guarded_prerequisite_skip.py),
[complete pair](../scripts/compare_guarded_prerequisite_skip.py) and
[optional preflight](../scripts/launch_guarded_skip_optional.py) retain the
original caps and require new public source and own-proof records.

**Example:** changing one historical audit script makes the byte snapshot
reject even though that script is outside the current 458-file fingerprint.
Changing a pin, source, receipt, archive, root, alias or donor in synthetic
tests stops before a guarded return and restores the original importing
aliases. Thirty-five focused tests pass with one expected optional-runtime
skip on each locked Python version. Ruff lint/format and strict mypy on
the seven new source/test files pass. The first focused iteration found
import-order/format and test typing errors; these were corrected before
qualification. No archived read, complete pair, CPU saving or new strategy
result exists. Next: commit the complete source, run both clean base and
both optional roles plus hooks and hosted CI, and publish every check byte
before a reference-free own proof.

## Exact-source qualification — November 18

The published source `7fb8f8a` passed both locked base roles (5,674 passed,
73 skipped, 150 deselected each), both fixed 76-file optional roles (2,581
passed on Python 3.11; 2,579 passed and two expected skips on Python 3.12),
Ruff, formatting, strict mypy, all-files hooks and both pinned installed
OpenSpiel license reads. Each role passed a clean exact-commit/source/runtime
guard before and after its test suite. Both runtimes produced the same 486-path
closed byte inventory. The initial local log cohort was lost from temporary
storage during a Mac restart; all four roles were rerun against the unchanged
source with complete receipts retained in ignored repository storage.

Official [CI #601](https://github.com/jimmy-sim/poker-ai/actions/runs/44461179593)
passed Python 3.11 and 3.12 with the expected 5,674/73/150 counts. Its actual
runtime checks and full tested merge tree match the source commit. The
[35-member source-check archive](../results/guarded-prerequisite-skip/source-checks/manifest.json)
retains the second local cohort and official hosted bytes. This is source
qualification only. The archive must be committed, published, and byte-verified
on GitHub before one fresh reference-free own proof; no archived proof or
complete pair has run. No CPU saving or stronger strategy follows.
