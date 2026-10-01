# Production & Autonomy: Cortex PM Chief-of-Staff Agent

> Module 6 · ★ Deliverable 5, how you'd ship it, govern it, and widen trust over time
>
> ✅ **What this validates:** you can ship it, govern it, and widen trust deliberately, by the end you'll have proven an autonomy dial, a Trust Ladder rung with its eval gate, and a governance plan.

## Autonomy Dial by segment

_Autonomy is a product decision per user, not one global setting._

Every segment starts at shadow on real data, because Cortex has only run on fixtures so far. The dial sets the ceiling each segment can climb to as Cortex earns it. It never moves the agent line: posting an update (rows 8 and 9) and committing a status or a date (row 4) stay with a human for everyone.

| Segment | Desired autonomy | Checkpoints that still fire | Why |
|---|---|---|---|
| The PM who owns the project, a weekly user | Bounded-autonomous, for the routine weekly draft only | the story-batch approval (row 7) and the PM's own review before anything is posted; the context review (row 2) is dropped once the gate is met | they read every update anyway and know the project; after months of correct drafts, a separate context check adds a step without adding safety |
| A new eng lead who inherits a project | Supervised | all of them: the brief (row 0), the context (row 2), the story batch (row 7) | they cannot yet tell a stale figure from a real one, so every output waits for their confirmation |
| An exec stakeholder who reads the leadership update | Assisted, permanently | Cortex queues and proposes nothing in their name; it only answers their questions with a summary they read | their segment carries the most blast radius (a company-wide update, row 9), and they want answers, not an agent acting for them |

The project-owning PM is the hardest segment to set: it is the only one where the dial actually turns, so it is where the evidence has to be strongest.

## Trust Ladder

- **Current rung:** shadow, on real data. Cortex has never read a real Jira, GitHub or Slack source. On the fixtures it already behaves like supervised, since every output waits in the review queue, but the ladder is about real inputs, and calling it supervised would overstate it.
- **Eval gate to reach the next rung (assisted):** all of the following, over 4 consecutive weekly cycles with at least 20 shadow drafts.

  | Condition | Threshold | Source |
  |---|---|---|
  | Status colour agrees with the update the PM actually sent | at least 18 of 20 drafts | the shadow comparison, at the 90% bar of EV-4 |
  | Invented figures in a queued draft | 0 | critic check 2; EV-4 |
  | EV-1 to EV-4 on the CI suite | at or above their thresholds every week | bounds and evals, section 3 |
  | EV-5 (jailbreak) and EV-6 (bound trip) | 100% on every change | bounds and evals, section 3 |
  | The Sev-1 "never Green" rule enforced in code, with a Vega case passing 20 of 20 | must exist before the climb | the bounds-and-evals pressure test: today this rule is a prompt plus a critic check, and no eval runs a project with an open Sev-1 |

- **Incident record that counts as clean for the window:** zero confidential items in any draft, zero Green statuses with an open Sev-1 or `launch_hold`, zero figures absent from that week's activity, zero bounds bypassed, zero kill-switch uses. One incident resets the 4-week window and drops Cortex back a rung.
- **Incident record so far:** none on the fixtures across the Module 2 to 6 runs. Every sabotaged draft in Module 3 was caught. The one real miss, the jailbreak in the Module 5 probe that Cortex did not flag, happened before the brief screen existed; the screen now escalates it before any model call.

## Deployment plan

- **Runtime:** serverless functions, triggered by hooks. The loop spec chose a hook (a PM task arrives) with a weekly cron sweep as backup; runs are short (8 to 25 seconds) and bursty, so pay-per-run fits. The handled-task ledger and the spend ledger move from local files to a small key-value store. Ruled out: an always-on service, because there is no heartbeat to keep alive; a managed agent platform, because the bounds live in Cortex's own code and should stay under our control.
- **Operator / on-call owner:** Antje Barth, builder and owner, primary. The project's eng lead, backup. Anything that touches a company-wide update escalates to the Head of Product.
- **Runbook (so someone else can operate it):** pause with `touch 00-build/KILL`; replay a failed run with the same command plus `--force` and the probe switches (`CORTEX_WITHHOLD`, `CORTEX_FAIL_ONCE`); resume by deleting `KILL`. Every run prints its bounds and its exit reason, and the held draft is in `run-output/`.
- **Rollback, smallest first:** drop that segment's dial one rung; disable one tool; `git revert` the prompt or build change; the kill switch.
- **Monitoring:** eval pass rate per case (weekly CI run); escalation rate by reason; cost per approved draft; trust incidents. Any trust incident pages the owner. An escalation rate above 30% of a week's runs, or the daily cap being hit, also alerts.

## ROI metrics (beyond adoption & tokens)

No figure here is invented: the baselines are measured during the shadow weeks.

| Metric | Target | How it is captured |
|---|---|---|
| **Outcome:** drafts the PM approves with wording edits only | at least 18 of 20 (the 90% bar of EV-4) | the PM's approve-or-edit action in the review queue |
| **Time saved** | reviewing a draft takes at most a third of the PM's own writing time (an assumption, to verify) | the PM logs the time to write their own update during the shadow weeks; review time comes from queue timestamps |
| **Cost to serve, per approved update** | model cost under the $0.05 per-run cap (measured $0.007 to $0.02), plus the PM's review minutes; review minutes dominate, so they are the number to watch | the spend ledger plus queue timestamps |
| **Trust incidents** | zero per quarter at the severity that reaches a reader | an incident log fed by critic failures that reached the queue and by PM reports |

## Widen-autonomy decision rule

A segment's dial goes up one notch only after that segment clears the next rung's gate for 4 consecutive weeks with a clean incident record; one incident drops it back a rung at once, and the 4 weeks start again.

## Governance & forward strategy

- **Compliance:** items marked confidential or embargoed never enter a prompt, because the tools strip them first. The brief's text is never stored; the ledger keeps only a hash. Drafts are purged after review or after 30 days.
- **Safety:** for every segment, a company-wide post, a committed date or status, and the choice of whom to escalate to stay above the agent line. Kill switch: the `00-build/KILL` file, then revoking the API key.
- **Reliability:** caps of 8 iterations, $0.05 per run, $2 per day and 60 seconds per run; escalate when stuck. If the model is down, the run escalates "model unavailable" and the PM writes that week's update by hand. A cached draft is never reused as current, the memory plan's rule against drift.
- **Strategy:** the next segment to widen is the project-owning PM on routine projects, toward bounded-autonomous for the weekly draft, gated by the rule above. The next capability is the Monday cron sweep across all projects, the parallel fan-out the orchestration map said would qualify later. It is gated by a cross-project bleed eval that does not exist yet: in the Module 5 jailbreak probe, a Northstar draft picked up a Vega item.
