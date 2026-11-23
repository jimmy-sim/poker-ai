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

**Current order (November 23, 2026):** PR #98's medium/dry acceptance remains
failed; PR #99's 100m forecast rejected longer training; PRs #100/#101/#103
found negative clipped, batch-one and batch-eight results on two known spots.
PR #102's broader average-readout study stopped at its failed compute
admission. PR #104's [full expected update](medium-dry-full-expectation-result.md)
passed its frozen two-known-spot strength rule, then history-merged after
local, hosted and solo review. Its improvement is not a default or broader
strength claim. The next [prospective comparison](river-full-broader-spots.md)
tests the unchanged candidate on structurally selected new card/range inputs
against matched-work B4 paths under the same hard compute cap. Its one-time
[cohort freeze](../configs/river-full-broader-freeze.json) is published before
any tree or outcome measurement; source qualification and all scientific
stages remained pending at selection. Exact-source local and hosted
qualification has since passed; its [receipt](../results/river-full-broader/source-checks/manifest.json)
was published and verified before the fictional proof. The proof was published
and verified; the one fixed [profile](../results/river-full-broader/profile/manifest.json)
completed with a conservative 3,436.576-second bound; the separate
[admission](../results/river-full-broader/admission/manifest.json)
recomputed the bound and was published and verified before the single
[own study](../results/river-full-broader/own/manifest.json). The study
completed and all own bytes were verified before the one pinned
[48-row comparison-only audit](../results/river-full-broader/native/manifest.json).
The audit passed its numerical gate, was published and verified. The
[frozen report](river-full-broader-spots-result.md) is **negative** on the
medium/dry input. The report was published/verified and final local and
hosted checks passed; publish/verify the
[final receipt](../results/river-full-broader/final-checks/manifest.json)
and finish solo review before choosing a distinct prospective follow-up.
PR #105 then history-merged negative after the first receipt-head 3.11 CI
run canceled at its unchanged limit and a targeted same-SHA operational
requalification passed. The next [read-only prospective diagnosis](river-turn-loss-diagnosis.md)
uses only the saved, known medium/dry policies to test whether actual turn
collisions align with the candidate's largest losses; no new diagnostic
outcome or training exists at protocol publication. Its isolated source passed
all four exact-source local lanes, hooks and both hosted jobs; the source
receipt precedes proof and real-policy analysis. All earlier failures remain, including PR #104's
separate post-merge main Python 3.11 timeout (receipt-head CI passed both).
