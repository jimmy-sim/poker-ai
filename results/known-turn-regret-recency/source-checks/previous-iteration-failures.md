# Isolated fictional test iterations — 2026-11-24 PST

First focused run under pinned Python 3.11.17: 2 passed, 1 failed. The test incorrectly applied bitwise `~` to `ArrayTree.legal`, which is a float mask; the earliest failure was `TypeError: ufunc 'invert' not supported` in the padded-cell assertion. Candidate code completed the preceding signed-regret assertions. Correct the test mask to `legal == 0` and rerun; do not alter the prospective protocol or any known-game outcome.

Second focused run: all 3 fictional tests passed, then Ruff I001 stopped the chained check because the new local-script import needed a blank group separator before `poker_ai` imports. This is a formatting issue; later format/mypy commands in that chain did not run. Add the separator and rerun all focused checks.

Third focused run: 3 tests and Ruff lint passed; Ruff format check requested a single-line work-identity assertion and stopped the chained mypy command. Apply the formatter's exact layout and rerun.

Fourth focused run: 3 tests passed but Ruff lint E501 rejected the formatter's one-line three-way node assertion. Split it into two short, equivalent assertions; no implementation arithmetic changed.

The first capture-adapter lint check stopped before mypy: Ruff I001 found the copied import groups unsorted and F401 found an unused replay import. The new capture had no known-game execution. Reorder imports and import the existing replay function directly from the runner instead of re-exporting it.

The next lint pass still found one extra blank line between the local adapter and `poker_ai` imports under repository import grouping. Remove that separator; static checks had not yet reached mypy.

After lint passed, Ruff format check found two trailing blank lines copied from the parent capture split and stopped before mypy. Remove only those trailing blanks.

The fictional capture/replay test passed all 4 tests, then Ruff stopped on import order and one 90-character call. No poker input was read. Reorder the test imports and wrap the call; retain the passing test output as a software fixture result only.

The first new plan-guard lint check found five overlong lines in the prospective pin assertions; no guard or known-game candidate was executed. Factor frozen work/row tuples into named constants and wrap file-path checks, preserving all values.

Historical guard dry/wet source fingerprints and all eight old control archives passed. The first guard static check then stopped on three overlong lines; no candidate policy was trained or scored. Wrap those lines and rerun.

The next static pass reached mypy after Ruff passed and found only the not-yet-created prospective `forecast` module import in the staged gate; no math test failed. Implement the already registered fixed profile formula before rerunning strict typing.

The first seven-test learner/capture/forecast run passed all fictional cases, then Ruff E501 rejected a 93-character synthetic worker receipt line; format/mypy were not reached. Split only the fixture layout and rerun.

The first stage-runner static pass stopped on import grouping and three long work-identity lines. No stage launched. Reformat only the guard; work labels and equality conditions stay fixed.

Stage-runner lint then passed; formatter requested the condition inside the multiline `any` on one line. The source was still not executed. Apply its layout.

After runner lint/format passed, strict mypy found that the stage gate imported `require_archive` without an explicit re-export. The runner was not launched. Mark the historical verifier as an intentional re-export, preserving its behavior.

The first comparison-only adapter static pass passed lint but Ruff format requested a one-line error message and stopped before mypy. No reference runtime or new policy was loaded. Apply the format-only change.

2026-11-24 05:01 PST: initial isolated report lint found 22 overlong lines (E501); formatter reduced this to two; both strings were wrapped, and subsequent full focused Ruff/format/strict mypy plus ten tests passed. No known-game candidate was trained or scored. The read-only replay of both immutable control archives passed six captures each and exact final work 10,117,956 wet / 10,012,410 dry.

2026-11-24 05:08 PST: first source commit was blocked by repository hooks because the shell had uv 0.13.9, while the committed project requires 0.13.5. The same staged bytes had passed all-file hooks in a preceding shell with `source ../poker-env.sh`; no source/experiment result changed. Retry the commit only with the pinned environment and retain this failure.

2026-11-24 05:09 PST: first nohup background launch left an empty driver.log and no state file or worker. Process inventory confirmed no qualification process before starting the same one-time driver in a persistent exec session; no role or scientific job was duplicated.

2026-11-24 05:17 PST: independently running only `tests/test_known_turn_regret_recency_report.py` on published source HEAD 4526fc2 failed during collection with `ModuleNotFoundError: known_turn_regret_recency`. In the earlier ten-test bundle, forecast/learning tests inserted `scripts/` first, masking this test-order dependency. This is a source/test import defect, not a poker outcome. The first exact-source local base311 lane was safely terminated at its partial progress; driver-state.json records `failed_retained`, base311 exit -15 and base311.log remains. No other lane started. Correct the isolated test import, commit a new source HEAD and requalify every prescribed lane and hosted job; do not accept old-source passing checks.
