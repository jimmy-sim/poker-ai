# Working in public

Development happens in [jimmy-sim/poker-ai](https://github.com/jimmy-sim/poker-ai).
The [work log](docs/work-log.md) connects decisions to commits, experiments and
verification. Existing commits retain their original dates and authors.

Project success comes first: model quality, correctness, reproducibility,
efficient progress and the developer's understanding. GitHub provides a visible
record. Contribution counts and the appearance of the contribution graph do not
determine what work to do, how to divide it or when to publish it.

## Issue to reviewed result

1. Open an implementation or research issue before a substantive step. State the
   problem and acceptance criteria; research also fixes seeds, configs and budget.
2. Create a focused branch, such as `research/river-integration`. Prefer one PR
   per coherent research question or implementation milestone, keeping it open
   through its required stages. Group related implementation, tests, fixes,
   documentation and evidence into meaningful commits. Split PRs when scope,
   risk or independent review benefits justify it.
3. Run checks appropriate to the change. Implementation changes require
   `make check` and relevant optional validation. Documentation-only changes
   require appropriate diff, format and link checks. Required hosted CI still
   passes before merge. Experiment-specific local, optional, source-bound and
   admission gates remain mandatory; retain failed outcomes. A passing software
   check does not accept a performance gate.
4. Open a PR linked to the issue. Explain the resulting behavior, actual checks,
   evidence paths and limitations. Let hosted CI check the branch.
5. Merge after applicable checks pass. Close the issue only when its acceptance
   criteria are met; a negative experiment can complete an investigation without
   meeting its performance target. Record that distinction explicitly.
6. Add a concise work-log entry linking the PR and result. Update the README only
   when the new evidence changes the current project summary.
7. For substantive implementation/research milestones, update the
   [learning journal](docs/learning-journal.md) in the same PR. Explain the question,
   change, example, actual result and next decision in plain English. Keep earlier
   failures and link the evidence. Personal learning notes must come from the
   developer's actual comments or actions; do not invent them.

For this solo project, a self-review explains a design decision and checks the
diff/evidence; it should not imply an independent reviewer participated.

## Commit boundaries and research history

Keep separately required publication checkpoints intact: the prospective
protocol, exact tested source, checked admission and own results published
before reference comparison. Grouping work never permits crossing these
boundaries with unpublished or unverified evidence.

Research receipts can depend on exact commit IDs and source trees. Preserve
those commits and their availability in a normal clone with history-preserving
merges. Squashing may suit housekeeping without those dependencies; check before
using it. Existing history remains intact.

Use PR/issue updates for routine status. Commit logs and CI receipts when the
protocol or reproducibility needs them; a status update alone need not create
another commit. Avoid repeated full checks when no change, failure or unresolved
concern justifies them, while completing every prescribed validation gate.

## Publication cadence

Publish meaningful, checked increments on the day the work happens, during the
session or by its end. For work spanning multiple days, update the same issue/PR
and add dated progress/evidence as each day's work is completed. A partial result
can remain on a clearly marked draft PR while checks or experiments are pending.

Keep actual author dates and publish completed work promptly. Daily visibility
comes from real work on different days, rather than holding finished changes for
future publication. This is a publishing preference for active sessions; paused
research remains paused and no recurring work schedule is implied.

There is no daily quota for commits, PRs or contributions. A quieter graph may
result from coherent milestones, but it is not a measure of project success.

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
