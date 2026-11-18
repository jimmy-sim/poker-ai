# Validated prerequisite sharing: bounded result

The [prospective protocol](validated-prerequisite-sharing.md) asked whether
passing the first fully validated prerequisite graph to later unchanged
consumers would preserve the complete ordinary reader's result and work. All
seven original loaders and their validation still ran per archive root. The
fixed complete pair **did not answer that question**: it stopped in its first
ordinary child before the validated-share child began.

## Published sequence and checks

1. Source commit `04d19ed` passed both clean local base roles (5,597 passed,
   71 skipped, 150 deselected each), both complete 69-file optional roles
   (2,502 passed each), Ruff, formatting, strict mypy, hooks and actual locked
   runtime/source guards. Both jobs of hosted
   [CI #572](https://github.com/jimmy-sim/poker-ai/actions/runs/44370320685)
   passed on an identical whole checkout tree. The [six-role record](../results/validated-prerequisite-sharing/source-checks/manifest.json)
   was published at `c9eb713` before archived collection.
2. One reference-free [own archive proof](../results/validated-prerequisite-sharing/own/manifest.json)
   passed on Python 3.11.17/NumPy 2.4.6. The whole command took 95.85 seconds
   under the 180-second cap. All seven original prerequisite loaders ran;
   six later consumers received the first graph after their own fresh output
   matched. Six after-caller and seven after-archive witnesses matched their
   loads. The original 480-row replay had zero chip and unitless error. No
   reference output was constructed. Raw bytes were published at `b47cf8c`
   and byte-verified on GitHub before the pair.
3. The one fixed ordinary-then-validated-share pair was launched on the clean
   `b47cf8c` head in the locked *base* Python 3.11 environment. Its first
   ordinary archive root completed seven original loads. During the second
   read, the original complete reader's runtime validation raised
   `PackageNotFoundError: No package metadata was found for numba`. The child
   returned 1 after 100.2056 seconds against the 900-second cap. The enclosing
   pair retained failure after 100.7035 seconds, well before its 1,800-second
   cap. The validated-share child did not start. The [16-member raw and
   diagnostic record](../results/validated-prerequisite-sharing/failed-pair/manifest.json)
   was published at `09c760f` before this report; its verifier checks the
   exact bytes and the first-child failure boundary.

The original complete reader checks saved Numba distribution metadata. A
read-only post-failure check found none in the launched base environment and
Numba 0.68.1 in the installed optional Python 3.11 environment. This explains
the recorded exception; the second environment was **not** used to rerun the
fixed pair. No complete ordinary result, shared result, work-counter identity,
speedup or savings result exists. The previous 912.54/900 forecast failure,
2.390%/1% known-game accuracy failure and rejected full-context-copy result
remain failed.

The [data-only renderer](../scripts/report_validated_prerequisite_sharing.py)
checks all source, own and failed-pair member hashes and the expected failure
semantics without importing poker readers, NumPy, Numba or reference modules.
Its [JSON export](../results/validated-prerequisite-sharing/report.json) is
byte-identical on the two locked Python runtimes; eight focused tests on each
cover blocked imports, changed bytes and changed semantics even after a
matching member hash is supplied. These checks reproduce the failure report;
they do not replace a complete pair.

## Decision

The preregistered fixed pair is failed and will not be repeated for a
favorable outcome. A new complete comparison needs a new prospective
protocol that pins the intended optional runtime and checks required package
metadata before starting the timed pair, followed by its own publication
gates. The validated sharing behavior remains unadmitted. Codex assisted with
implementation, collection and reporting; human hands-on time was not
recorded.
