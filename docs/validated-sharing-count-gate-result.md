# Validated prerequisite sharing: one complete behavior pair

The [prospective protocol](validated-sharing-count-gate.md) asked whether
one already validated, root-local prerequisite graph could be handed to
later original consumers without changing the complete reader's result or
work. One fixed ordinary-then-validated-share pair **passed exact complete
identity** in the pinned optional runtime. Every original loader and
validator still ran, so this result establishes observed sharing behavior,
not CPU savings.

## Publication and qualification sequence

1. Corrected source commit `182fd7c` passed both clean local base roles
   (5,629 passed, 72 skipped, 150 deselected each), both fixed 72-file
   optional roles (2,535 passed on Python 3.11; 2,534 passed and one
   expected skip on Python 3.12), Ruff, formatting, strict mypy and
   all-files hooks. Official [CI #591](https://github.com/jimmy-sim/poker-ai/actions/runs/44437224485)
   passed both jobs on actual locked runtimes and a whole tested tree
   identical to the source head. The [31-member source-check record](../results/validated-sharing-count-gate/source-checks/manifest.json)
   was published at `f6b5ede`; all members and its manifest matched
   GitHub's blob hashes before any archived collection.
2. The new source-publication gate passed from that pushed head. One fresh
   [reference-free own proof](../results/validated-sharing-count-gate/own/manifest.json)
   then passed on clean `f6b5ede`: seven original loader calls, six
   validated substitutions, unchanged 480-row saved replay with zero chip
   and unitless error, and 93.87 seconds under the unchanged 180-second
   command cap. Its three raw members were published at `bac111d` and
   GitHub-byte-verified before reference use.
3. Read-only preflight checked clean `bac111d`, source and own proof,
   actual Python 3.11.17/NumPy 2.4.6/Numba 0.68.1/OpenSpiel 2.0.2,
   the full pinned 11,358-byte OpenSpiel Apache-2.0 license, saved real
   runtime metadata, unchanged lock and pinned inputs. It constructed no
   reference output. The pair started once from that head, and its
   [32-member raw record](../results/validated-sharing-count-gate/pair-raw/manifest.json)
   was published at `297c4f5` before this interpretation. The
   deterministic compressed archive preserves 17,200,261 original bytes
   in 1,395,773 bytes, with per-member hashes and a data-only verifier.

The scientific-source fingerprint remains
`b475bfefb92963f25458d97260264743ff4d751b4513c307529742eaf10fc97d`
for 458 files; the committed lock SHA-256 remains
`db5529861ae56225daaf8a18513013e52bee88ef667227855b719a7e1364250c`.
The frozen batch seeds remain `[20261301, 20261302, 20261303]`. The
actual run was on an Apple M4 with ten logical CPUs and macOS 27.2.1;
the raw child and preflight receipts record the complete runtime and
hardware fields. No reference output entered training.

## Observed complete pair

| Check | Ordinary | Validated share |
| --- | ---: | ---: |
| Child wall seconds, cap 900 | 531.45 | 542.31 |
| Independent archive roots | 2 | 2 |
| Original prerequisite loader calls | 14 | 14 |
| Validated donor substitutions | 0 | 12 |
| Complete saved reads | 3 | 3 |
| Profiles / fixed conditions | 432 / 1,152 | 432 / 1,152 |
| Native reference workers | 3 | 3 |

The outer pair took 1,076.04 seconds under the unchanged 1,800-second
cap. Both children had distinct process IDs and the same complete context
witness. Their entire sorted scientific **and work** identities matched
byte-for-byte, and their SHA-256 matched the published predecessor identity
`ccd8e493a22a04dd0514c180d234b3ee4b62df68531eb1ddda516ea7175a7185`.
Work identity includes the original loader, replay, validation and cache
counters, rather than only the final poker values. The original native
scalar, source, admission and payout checks remained in the complete
reader. This is one observed pair, not an estimate of a stable speed
effect; no uncertainty interval or CPU saving is inferred from the two
wall times.

The [data-only report script](../scripts/report_validated_sharing_count_gate.py)
authenticates the source, own and compressed raw records plus their Git
publication order, then reproduces the [JSON export](../results/validated-sharing-count-gate/report.json)
without importing poker readers, NumPy, Numba, OpenSpiel or Treys. Ten
focused tests cover blocked imports, changed compressed bytes, changed
profile shape and work identity even after matching archive hashes, and
publication drift. Both locked Python runtimes render byte-identical JSON
SHA-256 `b7eda7fc00ecef6e3176da8c0d2c9bf7589ad1897332bf5a4284a936fe82819d`.
Full final local, optional and hosted checks remain pending.

The old missing-Numba and incomplete-publication pairs remain failed.
The 912.54/900 forecast, 2.390%/1% known-game accuracy and rejected
full-context-copy result also remain failed. This behavior pair does not
admit a new strategy, training/default, fresh/global result or real-money
use. A later skipped-work optimizer would need a separate prospective
contract and proof. Codex assisted with implementation, verification and
writing; human hands-on time was not recorded.
