# PR #118 source iteration failures, 2026-11-27 PST

These occurred before source qualification and before any real mixed policy or strength measurement. The subsequent tested-source checkpoint is `71d74a1346f8f46ece8a23045678f824bfda0c5c`.

- Initial targeted `uv run` check inside the restricted shell failed to acquire a lock in the shared `../uv-cache` (`Operation not permitted`). No test started. Subsequent pinned checks used the authorized environment and direct pinned venv tools.
- Initial Ruff/format on the new files found import ordering and long-line formatting; fixed before the source commit. The final targeted Ruff and format check passed all 16 new files.
- First direct strict mypy invocation omitted the repository `MYPYPATH` and reported 104 import-not-found/cascading typing errors in historical and new modules. With `MYPYPATH=src:scripts`, strict targeted mypy passed 16 source files.
- First targeted pytest invocation omitted `PYTHONPATH`; collection failed at `tests/conftest.py` with `ModuleNotFoundError: poker_ai`. With `PYTHONPATH=src:scripts`, all ten new tests passed.
- First `git commit` hook invocation inherited ambient uv 0.13.9 and stopped both Ruff hooks before code checks because the repository requires uv 0.13.5. Repeating the same commit with `source ../poker-env.sh` passed both locked Ruff hooks and produced the source commit.

No frozen protocol, historical source, threshold, seed, cap, saved parent or scientific outcome was changed to resolve these operational/source-format issues. Full raw terminal output of the early invocations was not redirected to a file; their command outcomes are preserved in the active session transcript and summarized here without claiming a complete log.

- After first source commit `71d74a13`, a code review found missing explicit recall-count and native peak-RSS receipts. Its source runner PID 41168 was stopped as a process group during base Python 3.11 at 47% of the fast suite; ignored `interrupted.json` hashes the partial `base311.log`. Hosted run 46102759428 was canceled by the corrective push; official JSON/log are retained separately. None of these checks qualifies corrected source `73b5e117`. The correction adds only the receipt/guard fields and is undergoing full requalification.

- Corrected-head full optional312 source qualification had one historical `test_published_profile_reproduces_all_numeric_exports_without_construction` failure: the test's child subprocess exceeded its unchanged 120-second watchdog. The full lane recorded 2,598 pass/two skip/one failure; no source pin or new mixture test failed. The `optional312.{json,log}` receipt is retained. A targeted standalone diagnostic initially failed at collection (`earlier_source_profile_support` absent from import path) before running the test; its `.log/.exit` are retained. One corrected standalone diagnostic with `PYTHONPATH=src:scripts` was launched against the same source; this does not qualify the full optional lane.
