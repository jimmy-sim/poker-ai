# Working in public

Development happens in [jimmy-sim/poker-ai](https://github.com/jimmy-sim/poker-ai).
The [work log](docs/work-log.md) connects decisions to commits, experiments and
verification. Existing commits retain their original dates and authors.

## Issue to reviewed result

1. Open an implementation or research issue before a substantive step. State the
   problem and acceptance criteria; research also fixes seeds, configs and budget.
2. Create a focused branch, such as `research/river-integration`. Keep commits
   coherent: implementation, meaningful checks and recorded evidence.
3. Run `make check`. Run relevant optional validation separately and retain failed
   experiment outcomes. A passing software check does not accept a performance gate.
4. Open a PR linked to the issue. Explain the resulting behavior, actual checks,
   evidence paths and limitations. Let hosted CI check the branch.
5. Merge after applicable checks pass. Close the issue only when its acceptance
   criteria are met; a negative experiment can complete an investigation without
   meeting its performance target. Record that distinction explicitly.
6. Add a concise work-log entry linking the PR and result. Update the README only
   when the new evidence changes the current project summary.

For this solo project, a self-review explains a design decision and checks the
diff/evidence; it should not imply an independent reviewer participated.

## Recording work and time

Git records changes and dates, not hours worked. Record hands-on time only from
an actual timer or contemporaneous notes. Keep assistant session elapsed time,
experiment wall time and CPU time in separate fields; overlapping intervals must
not be summed as personal work. Use "not recorded" for missing historical data.

For AI-assisted work, describe what the assistant implemented or checked and what
the developer actually did: choices, code review, experiments reproduced, and
concepts learned. A useful personal note is a decision you can explain or a bug
you reproduced. Do not invent review, learning or time entries.

The existing baseline is published with its real history. Historical milestone
links are a retrospective index, not retroactively created PRs or issues. Prefer
meaningful commits over a contribution-count target.

## Local commands

```sh
uv sync --locked --dev
make check
uv run --locked pre-commit run --all-files
```

Optional solver/evaluator/JIT checks require their locked extras. See the relevant
phase document for the command, expected result and compute budget. In particular,
`make validate-holdem-learning` retains a failed performance gate and returns
nonzero in the recorded study; `make report-holdem-learning` audits and renders
its committed policies offline.

Keep large runs/checkpoints in ignored directories. Add reviewed evidence
explicitly; do not stage someone else's uncommitted experiment outputs.
