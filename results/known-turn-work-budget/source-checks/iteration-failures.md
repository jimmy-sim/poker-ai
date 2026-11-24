# Prepublication implementation checks — November 24, 2026 PST

Before exact-source qualification, initial Ruff check found long lines/import order; formatter and import fixes followed. Initial isolated `pytest` invocation lacked the repository's tests-to-scripts import setup; test modules were aligned with prior conventions. One isolated mypy invocation specified only the test files and could not resolve the scripts package; the repository-wide strict invocation passed 1,061 files. None of these commands collected a poker outcome.

The first `git commit` invocation used ambient uv 0.13.9 and its two commit hooks failed the repository's required uv == 0.13.5 version guard. The same staged code committed under `source ../poker-env.sh` with pinned uv 0.13.5; both hooks passed. The later exact-source all-file hook run exited 0. The failed hook output is present in the Codex tool transcript; this note preserves its cause and disposition in the persistent run directory.
