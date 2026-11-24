# Source iteration, 2026-11-24

Initial focused Ruff check failed on 49 import/line-format findings before mypy or tests ran. No saved poker policy was traced. Formatting the isolated new source and tests is the planned correction; full exact-source qualification has not started.

The first direct mypy invocation against only new scripts reported 164 import-not-found errors because it omitted the repo's `src` package path; one real `no-any-return` finding in `saved_capture` was fixed. The first focused fictional suite then had one failure from binary floating-point non-tie in a synthetic equal-delta test, with five tests passing. The fixture was changed to exactly representable dyadic values; no real-policy trace or score was run. These are software-iteration failures, not scientific outcomes.

A subsequent command chain scoped `UV_PROJECT_ENVIRONMENT` only to its first `uv run`; the later pytest used the wrong environment and failed to import the installed project before tests. Retained as an operational invocation failure. Re-run with the task environment exported for every command; no scientific data was touched.
