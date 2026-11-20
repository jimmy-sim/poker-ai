# Operating workflow for issue #4 research

The aim is stronger poker decisions with reproducible evidence and a clear
account of what remains uncertain. Follow [AGENTS.md](../AGENTS.md),
[CONTRIBUTING.md](../CONTRIBUTING.md), the [roadmap](roadmap.md), and each
experiment's published protocol. Those requirements, historical source pins,
licenses, thresholds, permissions, and publication order remain binding.
GitHub records the work; contribution counts are not a research objective.
Within those bounds, Codex chooses the next justified milestone without
asking Jimmy to select it.

## Choose and finish one bounded milestone

1. Read the latest handoff, live Git/PR/CI state, current results and retained
   failures. Check for existing workers and partial logs before launching jobs.
   Finish an active experiment under its own protocol before choosing another.
2. Identify the leading poker-strength weakness or a concrete blocker to its
   next test. State one answerable question and why it matters to decisions.
   Prefer saved-policy evidence before new training when it can answer the
   question. Limit validation or infrastructure work to demonstrated
   correctness or budget blockers.
3. Publish a prospective issue/PR protocol **before outcomes**: fixed cases,
   control and candidate, seeds, work/checkpoints, metrics and estimator,
   acceptance/classification rules, compute forecast and hard caps, and stop
   rule. Previously used inputs are known evidence. Never select cases or
   seeds for favorable results after inspection.
4. Keep new code isolated from historical source pins. Test the math and
   implementation, complete every applicable exact-source local, optional,
   hook and hosted check, and retain failures. Publish tested source, own
   proof, profile and admission at their required boundaries. A failed
   conservative compute forecast blocks the longer run.
5. Run the admitted fixed experiment once. Retain partial and unfavorable
   outcomes. Publish and verify own raw policies and scores **before** any
   licensed, comparison-only reference audit. Reference strategies never
   enter training. Classify improvement, regression or inconclusive evidence
   using the frozen gates; do not loosen a gate, extend a budget or retry a
   scientific failure for a better result.
6. Update the dated work log, learning journal, PR and continuing roadmap
   with actual checks, poker decisions, limitations and the next decision.
   A failed scientific gate ends that experiment. A distinct follow-up may
   proceed only with a new prospective protocol and an evidence-based reason;
   software defects may be fixed with the failed evidence retained and full
   requalification. Keep PRs open through their gates and preserve referenced
   commits with history-preserving merges.

At each milestone, save a durable handoff with exact branch/commit and dirty
state, job owner/PIDs and persistent logs, completed and pending checks, CI,
evidence paths and next steps. Batch related commits and pushes without
crossing protocol, source, admission or own-before-reference publication
checkpoints. Record human time or learning only when Jimmy supplies it. Stop
when Jimmy asks, a real permission/compute blocker needs input, or execution
limits intervene; this workflow creates no unattended scheduler.

Autonomous research here does not authorize spending, paid services, external
competitions, messages to others, repository visibility changes, a C++/Rust
core, subagents or scheduled tasks. Existing restrictions on real-money
integration and default promotion also remain in force. Finish independent
work and present a concrete proposal if one of those permissions is needed.

**Current order (November 20, 2026):** PR #98's failed acceptance gates remain
negative; PR #99's 100m compute admission rejected the longer run; PR #100's
clipped update worsened all paired seeds and was history-merged. The distinct
[B1 update-frequency comparison](medium-dry-b1-updates-result.md) has a
**negative** fixed 10m result on the two known spots. Complete own raw
policies preceded the comparison-only audit. Finish PR #101's final exact-head
qualification and review before selecting a new question. No failed gate is
relabelled as a retry, and no default has changed.
