# Measure time spent rechecking earlier experiments

Opening a saved experiment also checks the earlier evidence it depends on. The
[saved caller graph](archive-reader-edges.md#historical-result--november-17)
points toward nested receipt checks and repeated context loading. Those old
elapsed values include waits and instrumentation, so they cannot tell us the
current CPU cost or what a proposed optimization would save.

This step adds a few timers inside the complete validation reader. Every original
check still runs. The [plan](https://github.com/jimmy-sim/poker-ai/issues/4#issuecomment-6958619644)
fixes the boundaries and expected calls before collection. It introduces no cache,
training, broad profiler or change to a poker decision.

## What is being observed

The five categories describe caller boundaries, without changing their defining
functions:

| Category | Meaning |
| --- | --- |
| `earlier_archive` | Read the earlier training archive |
| `admission` | Reconstruct and check its permission to run |
| `profile_receipt` | Check one saved timing report |
| `receipt_prerequisites` | Load the prior context needed to check that report |
| `direct_prerequisites` | Load the prior context directly for the archive reader |

Here, a timing report is an existing record. Reading it does not launch another
profiling run or create a new strategy profile.

The expected tree has one archive root, an admission check with six timing-report
checks, then a direct prerequisite load. Each timing-report check has one nested
prerequisite load. That is fifteen selected calls per real archive read. The
complete reader has one fictional-game read and two known cost reads: thirty
selected calls and sixty start/end events altogether. The fictional read has no
real archive root.

Static code explains the six repeated report checks: admission checks the saved
correctness and timing receipts; the timing receipt also checks correctness.
Each of those three paths checks a timing report directly and through a saved
cost receipt. The actual inventory must match this prospective tree. An
unexpected path is retained as a failed observation, rather than changing the
expected counts after seeing it.

## Three clocks, separate meanings

- **Elapsed seconds** include waiting.
- **Parent CPU seconds** measure work in the observing process, including its threads.
- **Reaped child CPU seconds** are the operating system's accumulated CPU for finished child processes. This counter advances when children are reaped; it does not show running workers continuously.

Each boundary records all three. **Inclusive** time includes calls below it;
**exclusive** time subtracts only immediate children. For example, five parent
CPU seconds minus four in direct children leaves one exclusive CPU second.
Nested inclusive values overlap and must not be added together. Child CPU is
kept separate from parent CPU and elapsed time. The report also retains each
native worker's body clocks; these use different windows from the operating
system's reaped-child counter and are not interchangeable totals.

The parser reconstructs the full ordered tree and event stream, checks typed,
finite, monotone clocks from one PID/thread, and reconciles every clock vector.
The existing absolute 1e-9-second arithmetic tolerance remains. Caller hooks
forward arguments, return identities and exceptions, leave unrelated calls alone,
and restore bindings after success or failure. Reentrant callbacks, changed
hooks, another owner thread and excess boundaries reject. Partial events and
primary failures remain available even if cleanup also fails.

## Correctness before measurement

The observer and complete-runner implementation adapt the existing archive-stage
tools while preserving their historical files. All 455 preceding scientific
source files and pinned inputs stay unchanged; the new entry, support module and
config produce a 458-file source map.

Independent fixtures check clock arithmetic, alias forwarding, call order,
restoration and failure paths. Complete-reader regressions also cover source and
proof checks, retained partial outcomes, data-only reports and startup-adjusted
time allowances. Their invented clocks are schema fixtures, not measured data.
The actual archived fictional-game read in the unit tests is explicitly separate
from formal source qualification and from the two synthetic forwarding trees.

Before the complete comparison, publish qualified source and its checked own-only
proof. That proof rechecks the archived fictional-game calculation and exercises
two synthetic fifteen-call trees; it does not prove real Hold'em performance or
real cost-loader coverage. Full relevant local, optional and hosted checks must
pass. Only actual Python 3.11.17/NumPy 2.4.6 can run the real comparison;
Python 3.12.15/NumPy 2.5.4 is for software/data checks.

The ordinary and observed children must retain the same three complete reads,
432 profiles, 1,152 fixed conditions, three native workers and exact original
scalar, semantic, work and context records. Reference outputs stay comparison-only. The pinned OpenSpiel 2.0.2 Apache-2.0
license was reread and matched in both optional environments; [license record
and obligations](solver_validation.md#solvers-versions-and-licenses) remain.
Caps remain 900 seconds per child, 1,800 shared, 180 for the own proof and 120 for
failure saving. Startup and all required stage work count. A partial or failed
attempt is retained and cannot be reported as a complete observation.

## Explore the foundation

```sh
.venv/bin/python -m pytest -q tests/test_receipt_cpu_support.py tests/test_receipt_cpu_runner.py
.venv/bin/python scripts/profile_receipt_cpu.py --help
```

Formal proof, collection and saved-report commands require their source-bound
prerequisites; the implementation refuses to skip them. No new complete
measurement has run yet.

The result will decide whether repeated receipt validation is a useful current
target. One ordered comparison can describe costs and observation overhead; it
does not establish stable savings, a successful compute forecast or stronger play.
The 912.54/900-second forecast and 2.390%/1% accuracy results remain failed, and
the earlier full-context-copy experiment remains rejected. Any proposed receipt
reuse needs its own correctness and current-performance evidence.

Codex assisted with implementation, fixtures and documentation. Human hands-on
time is not recorded.


Foundation checks: both base environments pass 130 focused tests with one plot
skip (23.65/23.54 seconds). Both optional environments pass 131 with real
OpenSpiel deliberately preloaded in the parent (35.66/35.86 seconds); the own
software fixture uses a fresh child. Strict typing passes for 829 files, and
lint/format pass. All 455 prior scientific files are byte-identical; the new
458-file fingerprint is `b475bfefb92963f25458d97260264743ff4d751b4513c307529742eaf10fc97d`.
The [prototype records](../results/receipt-source-cpu/source-checks/manifest.json)
retain initial fixture/typing corrections, licenses and layout checks. These
checks precede publication; full published-source qualification, formal proof
and complete collection remain pending.
