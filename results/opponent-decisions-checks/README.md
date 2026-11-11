# Saved-decision diagnostic checks

These checks apply to source `9bfe45c18472fc949a7236afa193300684757b7f`,
fingerprint `0927e4b4656f11dcb6a6469e25e445ddc2ee792beb0930ec3c59d7fad3116116`.
They do not authorize a new learning trajectory or change the prior failed gate.

- Full local bases: Python3.11.17/NumPy2.4.6 and Python3.12.15/NumPy2.5.4,
  each 2,625 passed, 58 skipped, 149 deselected. Lint, format, strict typing,
  commit hooks and before/after source/runtime/module guards pass. Exact logs,
  installation logs and wrapper timing receipts are retained.
- Relevant optional checks: all extras installed on both runtimes, all 35 new
  tests pass (1.00/0.97 seconds). These are focused optional checks; they are not
  a claim that the complete optional repository suite was repeated.
- `run_checks.py.txt` is an exact record of the launcher used in a detached immutable
  checkout. Its absolute checkout/environment paths describe this execution;
  use the repository's documented commands in a different clone.
- `source-ci.json` and decoded job logs retain both successful source CI jobs.
  Each has 2,625 passed, 58 skipped, 149 deselected and one historical
  numerical-roundoff warning; this is not silently removed.
- `diagnostic-command.log` records the actual complete read-only command.
  The diagnostic manifest records 139.8018285 seconds from thin-script entry,
  all 24/48/192 inventories and maximum trace error1.2273010890382813e-13 chips.
- `viewer-smoke.json` and compressed stdout record an **agent-run** actual-cache
  Terminal smoke test covering all 48 game/seed/method/seat selections with one
  cache load, n/p navigation, invalid-key recovery, q exit and invalid-rank
  rejection. It records no user practice, human time or understanding.

Original own/native files and input hashes remain unchanged. New off-diagonal
crosses are own calculations, not a new independent native comparison. Final
artifact CI is checked separately before merge; source CI alone is not that check.
