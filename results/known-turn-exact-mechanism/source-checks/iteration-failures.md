# Isolated source iteration failures — November 23, 2026 PST

At unpublished, uncommitted source on branch `research/known-turn-mechanism` after prospective commit `0dca303`, before any new tree/policy/score/profile/scientific run:

- First focused Ruff lint found 69 style/import issues, mostly E501 from initial unformatted source. `ruff check --fix` and `ruff format` reduced this to two E501 report metadata strings; splitting those strings resolved lint. Original terminal output was displayed by the tool; a retained formatter summary is in `/private/tmp/known-turn-ruff-fix.log` but that temporary path is not reboot durable. No protocol or old pinned file was changed.
- First focused `pytest -q tests/test_known_turn_mechanism_math.py` stopped during collection (exit 2, 1 error) with `ModuleNotFoundError: No module named 'known_turn_mechanism'`; the new test omitted the repo convention `sys.path.insert(0, str(ROOT / "scripts"))`. Zero tests or real-game trajectories ran.
- First `mypy --strict` over nine new source files exited 1 with five `attr-defined` errors: three imports of `require_archive` from the new gate and two imports of `CONTROL`/`CANDIDATE` from the new plan lacked explicit re-exports. No scientific work ran.

Correct the wiring and rerun focused checks. Retain this record; do not treat it as a poker-strength failure.
