# Optional-runtime sharing pair: failed ordinary-child gate

**Publication-gate correction (November 18):** hosted
[CI #583](https://github.com/jimmy-sim/poker-ai/actions/runs/44414936420)
found that the source-check manifest at `c5697ef` listed an ignored generated
bytecode file absent from a normal clone. Both report-head hosted jobs failed
four archive-authentication tests. The [official failure record](../results/validated-sharing-runtime-preflight/failed-report-ci/manifest.json)
retains both logs and the tested tree. The pair therefore did **not** meet
its required fully public source-check gate, in addition to the ordinary
child failure below. The original raw pair and manifests remain unchanged;
the exact missing byte was [published later](../results/validated-sharing-runtime-preflight/source-check-repair.json)
at `97baaf2` for audit. No pair retry or admission is justified by that
repair. The corrected JSON report explicitly marks the pair ineligible.

The [prospective protocol](validated-sharing-runtime-preflight.md) fixed one
ordinary-then-validated-share complete pair after the launcher and its six
source-check roles were public. Source commit `0b9ae32` passed both local base
roles, both complete optional roles and hosted [CI #580](https://github.com/jimmy-sim/poker-ai/actions/runs/44404463094)
on an identical whole tree. The [source-check archive](../results/validated-sharing-runtime-preflight/source-checks/manifest.json)
was published at `c5697ef` before the pair. The old public seven-loader own
proof was reauthenticated without rerunning its reader.

## Observed result

The [single raw pair](../results/validated-sharing-runtime-preflight/failed-pair/manifest.json)
started from clean `c5697ef` in the pinned optional Python 3.11.17,
NumPy 2.4.6, Numba 0.68.1 and OpenSpiel 2.0.2 environment. Preflight read
the complete installed Apache-2.0 license and matched its pinned SHA-256.
The ordinary child completed two independent archive roots with seven
original loaders each, three complete reads, 432 profiles, 1,152 fixed
conditions and three native reference workers. Its result was then rejected
by `complete reader scope, source or input changed` after 525.99 seconds;
the supervised child returned 1 after 527.36 seconds. The outer pair failed
after 527.74 seconds, inside the unchanged 900-second child and 1,800-second
pair caps. The validated-share child never started. No favorable retry ran.

The rejection has a deterministic source-level explanation. The old
candidate's child gate compares `identity["profiles"]` with integer `432`
and `identity["fixed_conditions"]` with integer `1152`. The numerical
identity returns the complete profile and condition *lists*. The saved
native output confirms lists of the correct lengths, so each list-to-integer
comparison is false. This is an inference from the unchanged source and
retained data; no ordinary/validated-share identity result was produced.
The paired behavior and any CPU saving remain unestablished.

## Reproduce the report

The [JSON report](../results/validated-sharing-runtime-preflight/report.json)
is rendered by `scripts/report_validated_sharing_runtime_preflight.py` from
the published source, raw and repair records. It authenticates all 34
source-check members and 19 raw-pair members, checks the old own manifest,
and confirms from Git history that the missing member was absent at the
pair head and present only at the later repair commit. It blocks reader,
numerical and reference imports. Run:

```sh
python3 results/validated-sharing-runtime-preflight/source-checks/verify-all.py.txt
python3 results/validated-sharing-runtime-preflight/failed-pair/verify.py.txt
python3 scripts/report_validated_sharing_runtime_preflight.py
```

The ten focused tamper/import tests pass on both locked Python runtimes;
both produce byte-identical corrected JSON SHA-256
`7f8ac9091a139708366bc402f8326b8eb5cb0d4c0cb18886c3351e5d413b702c`.
The actual outer runtime and hardware,
source/input hashes, child clocks, work inventory and failure are retained
in the raw preflight, child, native and supervisor receipts. These tests
validate the report, not the failed scientific or publication gates. Final
local, optional and hosted checks for this corrected report head were
completed as described below.

## Closing verification

Corrected report head `e2825e3` passes both clean locked base roles:
5,626 tests passed, 72 skipped and 150 deselected each, with Ruff,
formatting and strict mypy on 848 files. The 72-file optional roles pass
2,532 tests on Python 3.11 and 2,531 with one expected real-runtime skip
on Python 3.12. All-files hooks and both byte-identical data-only rerenders
pass. Official [CI #586](https://github.com/jimmy-sim/poker-ai/actions/runs/44422838341)
passes both jobs with 5,626 tests each, actual Python 3.11.17/NumPy 2.4.6
and Python 3.12.15/NumPy 2.5.4, and a whole tested tree identical to the
report head. The [32-member final-check archive](../results/validated-sharing-runtime-preflight/final-checks/manifest.json)
retains exact local and hosted logs, guards, rerenders and verifiers. The
earlier failed CI #583 remains failed and retained; the pair remains
ineligible and was not rerun.

PR #92's missing-Numba failure, the 912.54/900 forecast failure, the
2.390%/1% known-game accuracy failure and the rejected full-context-copy
candidate remain failed. No new strategy, training/default change, fresh
admission or real-money use follows from this result. A corrected count gate
would require a separate prospective question and source qualification
before any new complete pair. Codex assisted with code, checks and writing;
human hands-on time was not recorded.
