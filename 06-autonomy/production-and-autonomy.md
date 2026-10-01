# Production & Autonomy: Cortex PM Chief-of-Staff Agent

> Module 6 · Deliverable 5: bounds, trust and autonomy

## Autonomy Dial by segment

In the course's terms, the new eng lead is the Tesla driver who wants every action confirmable, and the project-owning PM can become the Waymo passenger once the evidence is there. Every segment starts at shadow on real data, because Cortex has only run on fixtures so far. The dial sets the ceiling each segment can climb to as Cortex earns it. It never moves the agent line: posting an update (rows 8 and 9) and committing a status or a date (row 4) stay with a human for everyone.

| Segment | Desired autonomy | Checkpoints that still fire | Why |
|---|---|---|---|
| The PM who owns the project, a weekly user | Bounded-autonomous, for the routine weekly draft only | the story-batch approval (row 7) and the PM's own review before anything is posted; the context review (row 2) is dropped once the gate is met | they read every update anyway and know the project; after months of correct drafts, a separate context check adds a step without adding safety |
| A new eng lead who inherits a project | Supervised | all of them: the brief (row 0), the context (row 2), the story batch (row 7) | they cannot yet tell a stale figure from a real one, so every output waits for their confirmation |
| An exec stakeholder who reads the leadership update | Assisted, permanently | Cortex queues and proposes nothing in their name; it only answers their questions with a summary they read | their segment carries the most blast radius (a company-wide update, row 9), and they want answers, not an agent acting for them |

**What Cortex may do, for every segment.** It reads the project record, this week's activity, past updates, the shareable roadmap and the norms. It advises on the status colour and on what to escalate. It writes only to the review queue and its own ledger. A human approves the status, every post, the creation of any story, and every go/no-go. The dial changes how many of the advise steps pause for a check; it never changes this list.

The project-owning PM is the hardest segment to set: it is the only one where the dial moves at all, so it is where the evidence has to be strongest.

## Trust Ladder

- **Current rung:** shadow, on real data. Cortex has never read a real Jira, GitHub or Slack source. On the fixtures it already behaves like supervised, since every output waits in the review queue, but the ladder is about real inputs, and calling it supervised would overstate it.
- **Eval gate to reach the next rung (assisted):** all of the following, over 4 consecutive weekly cycles with at least 20 shadow drafts (an assumption: about five active projects with one weekly draft each, so 4 weeks is the shortest window that yields 20 drafts; 20 matches the CI sample in bounds and evals, section 3).

  | Condition | Threshold | Source |
  |---|---|---|
  | Status colour agrees with the update the PM sent | at least 18 of 20 drafts | the shadow comparison, at the 90% bar of EV-4. The PM writes their own update without seeing Cortex's, so agreement is independent |
  | Invented figures in a queued draft | 0 | critic check 2; EV-4 |
  | EV-1 to EV-4 on the CI suite | at or above their thresholds every week | bounds and evals, section 3 |
  | EV-5 (jailbreak) and EV-6 (bound trip) | 100% on every change | bounds and evals, section 3 |
  | EV-8 (reworded injection) and EV-9 (cross-project bleed) | contained in 20 of 20 runs each | bounds and evals, section 3; both held 3 of 3 by the scope screen so far |
  | The Sev-1 "never Green" rule held in code, with the Vega case (EV-7) passing 20 of 20 | the code gate exists (2026-09-30), and EV-7 passed 3 of 3 in the eval runner with the go/no-go escalated in code; 20 of 20 still needed | bounds and evals, EV-7 |

- **Incident record that counts as clean for the window:** zero confidential items in any draft, zero Green statuses with an open Sev-1 or `launch_hold`, zero figures absent from that week's activity, zero bounds bypassed, zero kill-switch uses. One incident resets the 4-week window and drops Cortex back a rung.
- **Incident record so far:** none on the fixtures across the Module 2 to 6 runs. Every sabotaged draft in Module 3 was caught. The one real miss, the jailbreak in the Module 5 probe that Cortex did not flag, happened before the brief screen existed; the screen now escalates it before any model call. In Module 6 the drafter fell for a politely reworded injection every time it was tried, and pulled another project's Sev-1 into a Northstar update every time. Nothing reached the queue: first the critic, then a code screen held each run. They are the reason EV-8 and EV-9 sit in the gate.

## Deployment plan

The operator handoff has four parts: runtime and owner, runbook, rollback, and monitoring.

- **Runtime:** serverless functions, triggered by hooks. The loop spec chose a hook (a PM task arrives) with a weekly cron sweep as backup; runs are short (8 to 25 seconds) and bursty, so pay-per-run fits. The handled-task ledger and the spend ledger move from local files to a small key-value store. Ruled out: an always-on service, because there is no heartbeat to keep alive; a managed agent platform, because the bounds live in Cortex's own code and should stay under our control.
- **Operator / on-call owner:** Antje Barth, builder and owner, primary. The project's eng lead, backup, who takes the page when the owner is out. Anything that touches a company-wide update escalates to the Head of Product. Alerts page through the team's on-call tool, not email.
- **Runbook, the first three steps at 2am:** 1. Stop new runs: set the deployment flag `CORTEX_KILL=1`, which every run checks before it starts and at each iteration (`touch 00-build/KILL` does the same locally). 2. Read the held run's exit reason in the run log and its draft in the store; every run prints its bounds and why it stopped. 3. If it was a bound or a tool failure, replay it with `--force` and the probe switches (`CORTEX_WITHHOLD`, `CORTEX_FAIL_ONCE`); if it was a trust incident, drop that segment's dial a rung and leave the flag set until the cause is fixed. Resume with `CORTEX_KILL=0`.
- **Rollback, smallest first:** drop that segment's dial one rung; disable one tool; `git revert` the prompt or build change; the kill switch.
- **Monitoring:** eval pass rate per case (`python evals.py --n 20`, weekly and on every change); escalation rate by reason; cost per approved draft; trust incidents. Any trust incident pages the owner. An escalation rate above 30% of a week's runs, or the daily cap being hit, also alerts. The 30% is a starting value, to be reset from the rate the shadow weeks show.

## ROI metrics (beyond adoption & tokens)

The baselines come from the shadow weeks; no figure here is invented.

| Metric | Target | How it is captured |
|---|---|---|
| **Outcome:** drafts the PM approves with wording edits only | at least 18 of 20 (the 90% bar of EV-4) | the PM's approve-or-edit action in the review queue |
| **Time saved** | reviewing a draft takes at most a third of the PM's own writing time (an assumption, to verify) | the PM logs the time to write their own update during the shadow weeks; review time comes from queue timestamps |
| **Cost to serve, per approved update** | model cost under the $0.05 per-run cap (measured $0.007 to $0.02), plus the PM's review minutes; review minutes dominate, so they are the number to watch | the spend ledger plus queue timestamps |
| **Trust incidents** | zero per quarter at the severity that reaches a reader | an incident log fed by critic failures that reached the queue and by PM reports |

**Two readings of a high approval rate.** It can mean the drafts are right, or that the PM has stopped reading them. So the approval rate triggers an audit, not a verdict: every approval records the size of the edit as a diff, and one week in four a second PM checks Cortex's status colour blind against the project's real state.

**Riskiest assumptions, behavior first.** The value depends on what PMs do more than on what the model does, so the behavioral assumptions are tested first, all inside the four shadow weeks.

| # | Assumption | Test in the shadow weeks | It fails if |
|---|---|---|---|
| 1 | PMs read the drafts properly instead of approving them on sight | edit size per approval, and the blind second-PM check one week in four | the blind check disagrees with an approved status in more than 2 of 20 drafts |
| 2 | Reviewing a draft is faster than writing the update | the PM logs their own writing time; review time from queue timestamps | review takes more than a third of writing time (the time-saved assumption above) |
| 3 | PMs bring their weekly ask to Cortex at all | the share of weekly updates started by a task (the hook) rather than by the Monday sweep | fewer than half by week 4: a judgment, below which the PM is not choosing to use it |
| 4 | Drafts on real Jira, GitHub and Slack data hold the fixture-level accuracy | status agreement with the PM's own update, invented figures | below 18 of 20, or any invented figure (the Trust Ladder gate) |

## Widen-autonomy decision rule

A segment's dial goes up one notch only after that segment clears the next rung's gate for 4 consecutive weeks with a clean incident record; one incident drops it back a rung at once, and the 4 weeks start again.

**And the rule that stops it.** If, after the 4 shadow weeks, the status colour agrees with the PM's own update in fewer than 15 of 20 drafts, or any trust incident reaches a reader at any rung, Cortex goes back to design. The owner and the Head of Product decide within a week whether to rebuild the drafting step or stop. 15 of 20 is a judgment: below it the PM corrects one draft in four, and reviewing stops being faster than writing.

## Governance & forward strategy

- **Compliance:** items marked confidential or embargoed never enter a prompt, because the tools strip them first. The brief's text is never stored; the ledger keeps only a hash. Drafts are purged after review or after 30 days.
- **Safety:** for every segment, a company-wide post, a committed date or status, and the choice of whom to escalate to stay above the agent line. Kill switch: the `CORTEX_KILL` flag (or the `00-build/KILL` file locally), then revoking the API key. The hard no: no post tool, ever, for any segment. It rules out auto-posting even routine updates, auto-closing tickets, and committing dates, the steps the course's own worked example puts on the ladder.
- **Reliability:** caps of 8 iterations, $0.05 per run, $2 per day and 60 seconds per run; escalate when stuck. If the model is down, the run escalates "model unavailable" and the PM writes that week's update by hand. A cached draft is never reused as current, the memory plan's rule against drift.
- **Strategy, the next 90 days prove before they build:** three proofs, all from one team's four-week shadow, then a decision. (1) Drafts on real data hold the status gate (assumption 4). (2) PMs review rather than rubber-stamp, and review beats writing (assumptions 1 and 2). (3) The PM keeps bringing the weekly ask to Cortex after the four weeks (assumption 3). Only if all three hold does Cortex widen: first the project-owning PM toward bounded-autonomous for the weekly draft, then the Monday sweep across all projects, the parallel fan-out the orchestration map said would qualify later. The sweep is also gated by the cross-project bleed eval (EV-9): the drafter pulls another project's issues into an update whenever the brief mentions them, and today only the scope screen stops it.
- **Vendor dependency:** drafter and critic both run on OpenAI models today, which also weakens the critic's independence: the two share a vendor's blind spots. Model names are settings (`CORTEX_MODEL`, `CORTEX_CRITIC_MODEL`), but switching is only real once `python evals.py --n 20` passes on the new provider, and the prompts may need retuning. A critic from a different provider is the stronger form of independence, and the first change to try if the critic's misses grow.
- **Why build it instead of buying it:** the tools the team already uses can summarize a project, and drafting is a commodity any vendor can add, so it is not the advantage. What a vendor summary does not carry is this team's agent line: its norms as code gates, its embargo list stripped at the tool, its review queue, its dial per segment. If a vendor offers those as configuration, buy it, and this repo's evals become the acceptance test it has to pass.
