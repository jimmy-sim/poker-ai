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


### November 17: retain the failed source qualification and child diagnostics

The first full cohort at `d2cd3f7` is not qualified. Both base suites pass
5,564 tests; the 3.11 optional suite passes 2,473. The 3.12 optional run has
2,437 passed and 36 setup errors, all from one failed shared fixture child.
Its original stderr was not retained, so the cause remains unknown. A fresh
software-only run of that same fixture passes; that does not explain the failure
or count as full qualification. GitHub's 3.12 job passes, while its 3.11 job hits
the existing 25-minute limit. [The failed cohort and fresh diagnostic](../results/receipt-source-cpu/failed-qualification-d2/manifest.json)
are retained together.

The test now saves child stdout and stderr beside its fixture directory and
still requires a zero exit code. Two regression cases check successful and
failed children. No reader, clock, configuration, scientific cap or acceptance
rule changes. Full qualification must be repeated on the new head before the
formal own proof or complete comparison. No new strength or timing result is
claimed. Codex-assisted work; human hands-on time is not recorded.


Resumed checks on November 17 pass 133 focused tests in each actual optional
environment (196.62/198.91 seconds), with strict typing829, lint and formatting
passing. A live sample during this run shows a parent waiting in an OS file
read; it does not establish the earlier child failure's cause. Temporary
environments removed during the pause were rebuilt from the unchanged lockfile.
Full exact-head qualification remains pending.

### November 18: source checks qualified before collection

The test-only `00aae95` head passes all six source roles. Both complete local
bases pass 5,566 tests with 71 skipped and 150 deselected (861.76 and 858.37
seconds of pytest); strict typing covers 829 files, and lint, formatting and
commit hooks pass. Both optional suites pass 2,475 tests (531.38 and 449.29
seconds). Every local role checks its actual Python, NumPy, clean 458-file source
fingerprint and package import roots before and after, without a launcher
`PYTHONPATH`.

Both [hosted jobs](https://github.com/jimmy-sim/poker-ai/actions/runs/44260849905)
pass the same 5,566-test base scope (1,316.05 and 1,148.07 seconds, with one
warning each). Saved exact logs and official metadata verify Python 3.11.17 /
NumPy 2.4.6 and Python 3.12.15 / NumPy 2.5.4, every uv selection, and that the
tested merge commit's entire tree equals the source head. The
[six-role receipt](../results/receipt-source-cpu/checks.json) and
[retained records](../results/receipt-source-cpu/checks/manifest.json) include
the earlier interrupted local attempt, the detached launch that produced no
role results, and the successful new attempt. Neither partial attempt is counted
as a pass. The earlier `d2cd3f7` failure remains failed.

These are source and software checks, not a timing observation or evidence of
stronger poker play. The formal own-only proof and complete ordinary/observed
comparison have not run. Publication of this checked source evidence is the
next gate before proof.

### November 18: bounded own-only proof before comparison

The pushed-source guard passes on the six-role receipt. The first private
launcher used an unsupported `--operation` flag and exited during argument
parsing in 0.079 seconds; it started no proof child or reference. Its outer log
and receipt are retained. A corrected private launcher passes the positional
`proof` argument and uses a fresh output path. It changes no observer, source,
input, acceptance rule or 180-second cap.

The complete [own-only proof](../results/receipt-source-cpu/software-raw-manifest.json)
takes 8.070 seconds for the enclosing command against 180 seconds. Its inner
supervisor takes 8.008 seconds against the startup-adjusted 179.999-second
allowance. All eleven raw members are copied byte for byte. The actual archived
fictional-game software replay matches the saved calculation; two separately
labelled fifteen-call forwarding trees test hook behavior. Full observer-state,
event, arithmetic, source and command-inventory checks pass without loading
OpenSpiel. The proof has no real cost-loader coverage, no new independent poker
math and no training or native comparison. Its own evidence must be public and
verified before the complete ordinary/observed pair starts.

### November 18: retain the complete pair before cost analysis

The fixed ordinary/observed pair completes once, in that order. The outer
command takes 879.144 of 1,800 seconds, including preflight and startup. Its
plain and observed children take 457.933 and 415.749 seconds, each below the
unchanged 900-second child cap. Both execute three reads, 432 profiles, 1,152
fixed conditions and three native workers. The observed arm records the fixed
thirty selected calls and sixty events; the ordinary arm has timers disabled.

The [27 raw members](../results/receipt-source-cpu/pair-raw-manifest.json)
are copied byte for byte before any report. The saved-pair authenticator checks
source, child clocks, event streams, native rows, original work and exact
scalar/computed-replay identity. The identity hash is
`ccd8e493a22a04dd0514c180d234b3ee4b62df68531eb1ddda516ea7175a7185`.
No training or strength admission follows. One ordered pair does not establish
stable observation overhead or savings. Publish and verify these raw files
before rendering the data-only cost report.

### November 18: what the current clocks show

The [data-only report](../results/receipt-source-cpu/report/summary.json) reads
the already published raw pair. On both actual runtimes, 109 game construction,
replay and profiling paths are blocked, with zero forbidden calls; all three
numerical exports and both figures reproduce byte for byte. The raw pair is
unchanged. The [report checks](../results/receipt-source-cpu/report-manifest.json)
retain versions, hashes and the runnable operator. Codex inspected both
[archive stages](../results/receipt-source-cpu/report/archive-stages.png) and
[separate clocks](../results/receipt-source-cpu/report/complete-clocks.png).

The table reports **exclusive parent CPU seconds** inside the earlier-archive
reader for the two observed cost reads. Each column sums to its archive root;
inclusive parent and child times must not be added together.

| Boundary | Cost before reference | Cost after reference |
| --- | ---: | ---: |
| Six nested receipt prerequisite loads | 25.227 | 25.360 |
| One direct prerequisite load | 4.162 | 4.202 |
| Admission outside those loads | 0.677 | 0.825 |
| Six report checks outside their loads | 0.197 | 0.202 |
| Archive reader outside selected calls | 0.074 | 0.079 |
| **Earlier-archive parent CPU** | **30.337** | **30.667** |

Nested receipt prerequisites account for 83.16% and 82.69% of the selected
archive-root CPU. They account for about 18.5% of the respective complete
cost-read parent CPU (136.472 and 137.320 seconds); 106.135 and 106.653 seconds
per read lie outside the archive root. These prerequisite calls include input
construction and validation, not just disk I/O. The six report-check wrappers
themselves use about 0.20 parent CPU seconds outside their prerequisites.

The complete ordinary and observed child wall times are 457.933 and 415.749
seconds in this single ordered pair. The observed arm being faster here is not
a measured speedup from timers. Parent body CPU is 275.886/279.789 seconds;
the sums of three native worker body CPU clocks are 373.607/373.097 seconds,
and the operating system's reaped-child body CPU is 383.450/382.780 seconds.
These counters have different windows and parallel work; they are not additive
elapsed totals. Historical elapsed-stack measurements include waits and cannot
be subtracted from these current CPU clocks to forecast savings.

The next research question is whether the repeated inputs are identical and
whether reuse preserves mutation isolation and every work counter. No cache is
admitted by this measurement. The 912.54/900 forecast, 2.390%/1% accuracy and
full-context-copy failures remain failed; competitive full-game strength is
unestablished.


### November 18: final source-head qualification

The [final check archive](../results/receipt-source-cpu/final-checks/manifest.json)
retains both the failed parallel attempt and the complete serial retry at
`459c04d`. In the parallel attempt, the two local base suites each passed
5,565 tests but the same archived software replay exceeded its unchanged
180-second wall cap. The isolated test then passed in 6.23 seconds. The failed
results are not counted as qualification, and the optional lanes did not start.

The serial retry changed no source, test, threshold or cap. Python 3.11.17 and
3.12.15 base suites each pass 5,566 tests, skip 71 and deselect 150, followed
by lint, format, strict typing of 829 files, commit hooks and clean source
guards. The optional scopes pass 2,475 tests each. GitHub run
[#553](https://github.com/jimmy-sim/poker-ai/actions/runs/44271740130) passes
both hosted jobs on the same source head and whole tree, with the same actual
Python and NumPy versions. The retained verifier checks all six role logs,
source hashes and the hosted merge checkout. These are software qualifications;
they do not reverse any failed research gate or establish stronger play.

The later documentation/evidence head `33db2ae` did not pass its first hosted
run. In [CI #554](https://github.com/jimmy-sim/poker-ai/actions/runs/44285335607),
Python 3.12 passes the complete suite; Python 3.11 reaches 97% without a test
failure and is cancelled by the workflow's 25-minute job limit. The
[cancelled job log](../results/receipt-source-cpu/final-ci-retry/manifest.json)
is retained. The workflow allowance is raised to 35 minutes for a complete
rerun. This changes no scientific proof, measurement or child-time cap.
