# Verified claims and interview notes

These notes describe the project's recorded capabilities and results. Development
includes Codex-assisted implementation, testing, experiment execution, and writing;
specific attribution remains in the journal and work log.

The bullet drafts are project-level descriptions. First-person accounts of
implementation or discovery should come from actual contributions and practice.
Numbers refer to the configurations and hardware in the linked reports.

## Four resume bullet drafts

- AI-assisted poker research project with a Python Hold'em engine and 5–7-card
  evaluators: validation covers all 2,598,960 five-card hands and 2,000,000 seeded
  six/seven-card samples against Treys, plus 1,000 engine traces compared with
  PokerKit.
- CFR, CFR+, Linear CFR and DCFR with exact information-set best responses:
  matched OpenSpiel's Kuhn/Leduc exploitability within 1.39e-16 ante
  chips/hand at the configured iteration checkpoints.
- Resumable sampled-CFR training and a fixed-seed postflop diagnostic with
  378 independently checked frozen policy records; identified public-card aliasing
  while retaining a failed 1% pot held-out exploitability target.
- A 36,000-hand duplicate-deal evaluation using 1,000 independent deck
  clusters and conservative familywise inference; reported zero confirmed positive
  advantages across six opponents rather than treating point estimates as proof.

Evidence: [fundamentals](phase1-verification.md), [toy solvers](phase2-solvers.md),
[postflop diagnostic](holdem-strength-v2.md), [evaluation](phase4-evaluation.md). The
evaluator samples are validation inputs, not played hands; the 378 policy records are
neither independent statistical samples nor global trained agents.

## Interview answers

**1. How strong is the agent?** It is a bounded research prototype. In the local
duplicate study, point estimates lose to tight-aggressive and equity bots; no positive
advantage passes the predeclared six-opponent family test. Tiny spot solutions and
toy-game numerical agreement do not establish global Hold'em skill.

**2. What does CFR minimize?** At each information set, CFR accumulates the advantage
of each action over the current mixed policy, weighted by chance and the other
player's reach, excluding the updating player's own reach. Regret matching converts
positive cumulative regret into a policy. The reach-weighted average strategy, rather
than the last iterate, is the object of the usual convergence guarantee.

**3. How is external sampling different?** It samples chance and opponent actions,
enumerates the updating player's actions, and defers updates until that pass finishes.
Correct sampling probabilities preserve counterfactual-regret expectations. The tests
include nonuniform chance, analytic expected updates and bit-identical checkpoint
continuation. Finite sampled runs still have variance.

**4. What does exploitability mean here?** In two-player zero-sum games, NashConv is
BR0 + BR1 using each responder's net payoff. The project reports NashConv/2 and
divides by the initial pot in the postflop diagnostics. It is exact for that
restricted range/action game, not full-game exploitability or bb/100 win rate.

**5. What went wrong with card abstraction?** Existing keys could merge different
observed public boards. Adding the public board removes those collisions in the small
study and sharply improves the two medium-SPR results. In those games the new keys are
as fine as exact cards, so this is a diagnostic of information loss, not evidence of
global generalization. Exact raw boards would greatly expand a global sparse table;
that change has not been promoted to the global agent.

**6. Did the original postflop procedure pass?** The development cases passed. The
medium-IP hold-out median was 0.01015285879237701 pots versus a fixed <=0.01 target.
The failure and all controls are retained; the global comparison was not launched. All
four games are now known evidence; a revised procedure needs fresh hold-outs.

**7. Why can a policy with high exploitability do well against an equilibrium
control?** A fixed opponent does not necessarily punish all its weaknesses.
Exploitability searches for a constrained best response, whereas cross-play evaluates
against one particular policy. Both are reported; action distance from a possibly
nonunique equilibrium is not treated as a strength ordering.

**8. Was 100% row coverage a training success?** One exact uniform expectation gave
every row a real averaging update. Some rows were never visited again; the audit
separates those initial-only rows, subsequent sampling and the initialization cost.
This finite full-tree control cannot initialize global Hold'em affordably.

**9. Why did two exact solvers initially diverge?** Tiny tied regrets around 1e-16
became pure choices after normalization. Fused versus separately rounded arithmetic
changed those ties. Eight scalar contraction modes and an explicit FMA kernel were
tested, with independent checks of frozen-policy payoffs and best responses. The
original failure is preserved and numerical tolerances stay fixed.

**10. Why are 36,000 hands only 1,000 clusters?** Both seats, three frozen policies
and opponents reuse each independently drawn deck. Outcomes are aggregated within each
deck, preserving covariance before inference. The conservative primary familywise
bound and secondary pointwise CLT intervals answer different questions. Training seeds
are fixed policies here, not independent samples from all possible agents.

**11. What do the Bayesian and risk results prove?** The Bayesian extension can
improve toy transcript prediction, but can worsen under misspecification or drift. A
root mixture bounds degradation from the own blueprint's worst-case value only in
those exact toy games. Risk simulations are conditional on return laws and stake
scaling; all five empirical confidence-robust sizing fractions are zero before fees.
Neither result establishes a real-world edge or bankroll advice.

**12. What would you do next?** The current focus is validation overhead before the
proposed compact/finer-opponent training comparison. The experiment design, seeds,
accuracy targets, and compute limits remain fixed. Subsequent work needs measured
improvements and fresh cases before broader strength claims. That follows the
project's continuing goal: strengthen the model through reproducible experiments and
understand its weaknesses.

## Reproduction and limits

`make check` verifies the current software. Reproduction instructions in the linked
reports specify the required dependencies and historical checkout. The original `make
validate-holdem-learning` study intentionally returns nonzero for its failed
performance criterion. Keep configs, seeds, source/dirty status, lock hash, runtime,
hardware and frozen policy hashes. The reference is comparison-only and uses this
project's game mechanics/export; historical independent engine/evaluator checks have a
separate role. Current publication and check results are linked from the [work
log](work-log.md) and [GitHub Actions](https://github.com/jimmy-sim/poker-ai/actions).
Older verification reports retain their original dates and scopes.
