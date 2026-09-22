# Orchestration Map: Cortex PM Chief-of-Staff Agent

> Module 3 · Orchestration & Subagents, ★ Deliverable 3
>
> ✅ **What this validates:** nothing advances unchecked, by the end you'll have proven a justified topology, a roster, and a validator with a defined fail action.
>
> Builds on your M2 Loop Spec. Only split one agent into a team when there's a real reason, coordination has a cost.

## 1. Why split? (or why not)

**Current design, one line (from the Loop Spec):** a single hook-fired loop that pulls the fixtures, drafts one project's update plus a capped story batch, hands the draft to a critic, revises at most once, and stops at the PM checkpoint.

**The default-to-simple check:**

| Reason to split | Applies? | Why / why not |
|---|---|---|
| Separation of concerns | No | Drafting and norm-following have not contaminated each other in any run: the drafts were warm and compliant at the same time. The failures so far were the critic's, not the drafter's. |
| Parallelism | No | One task, one project, five reads that take about a second each. Nothing to run side by side. The Monday cron sweep over several projects would qualify later; it is not built. |
| Independent validator | **Yes** | In every run the drafter called the same data Green, then Yellow, then Green, and ended each draft with `DONE` while the critic disagreed. The author cannot judge its own status call. Only a check that never saw the drafting prompt catches that. |
| Context-window pressure | No | A full run is about 10k tokens; the fixtures fit many times over. |

**Verdict:** split for exactly one reason, the independent validator. Cortex stays a single agent with one subagent, the critic, which is a separate model call with its own context. Not a fleet.

## 2. Topology

**Pattern:** single + one subagent. One loop does the work; one independent check gates it; a human owns the exit.

```
[PM task arrives (hook) / Monday sweep (cron)]
        |  dedupe by task ID
        v
[Cortex: get_project · get_activity · search_past_updates · get_roadmap · get_norms
         -> draft update + propose_stories (queued)]
        |  proposed output + source log
        v
[Critic: 5 checks, own context, never saw the drafting prompt]
   |-- pass ------------------------------> [PM review checkpoint] -> queued, nothing sent
   |-- fail on check 1/2/3/5 -> back to Cortex with the failed check (max 2) -> then escalate
   '-- fail on check 4 (commitment or leak) -> escalate at once, draft held
```

## 3. Roster

| Agent / subagent | Responsibility | Runs which Loop Spec |
|---|---|---|
| Cortex | pull data, draft the update, propose a capped story batch, decide when to stop | the M2 hook loop (cron backup) |
| Critic | check the draft against five rules, return pass or fail with the failed check named | one call per draft, no loop of its own |
| PM (human) | set status and commitment level, approve stories, own every post | above the agent line, not a loop |

No research subagent, no reader subagent: the five read tools do that work, and a tool is cheaper than an agent.

## 4. Communication & hand-offs

In-process, plain structured text. No MCP or A2A: both agents live in one process, so a shared envelope buys nothing today. Noted for when a critic runs elsewhere.

| From | To | What passes | Form |
|---|---|---|---|
| Cortex | Critic | the proposed output plus the full source log (every tool call and its result) | text |
| Critic | Cortex | `{"verdict": "pass" or "fail", "reasons": [...]}`, each reason naming the failed check and the offending text | JSON |
| Critic | PM | the held draft plus the critic's reasons, when the run stops | `run-output/status-update-<task>.md` |
| Cortex | PM | the passing draft and the queued stories | the review queue |

## 5. The validator

One subagent, the critic. A separate model call with its own system prompt that never sees the drafting prompt or the conversation, only the source data and the proposed output. It exists because the drafter cannot judge its own status call.

**What the critic checks.** Five rules, each answerable yes or no against the source log. Wording, length, and tone are not checks.

| # | Check | How it is decided |
|---|---|---|
| 1 | Project and IDs match | Every PR or issue ID and the project name in the draft appear in the pulled data |
| 2 | Every number is traceable | Each figure, date, and metric appears verbatim in a tool result. No invented numbers |
| 3 | Status is evidence-backed and gate-safe | Green requires no open Sev-1 and no `launch_hold` in the pulled project data. A colour fails only when the data contradicts it, not because the critic would have chosen another |
| 4 | No commitment, no leak | No firm date, no launch gate marked, nothing posted or created, nothing tagged confidential or embargoed in the draft |
| 5 | Story batch is traced and capped | Every proposed story maps to an in-scope PRD item; the batch count is within the cap |

**Pass rule:** all five hold, `pass`, even if the critic would have written it differently.

**Fail action, tiered:**
- Checks 1, 2, 3, 5 fail: **revise**. The draft goes back to Cortex with the failed check and the offending text named. Cortex fixes it from the data it already has; no re-pull.
- Check 4 fails: **escalate** at once, no revision. A commitment or a leak is above the agent line; a second draft is not the fix, a human is.

**Revision cap:** 2. After the second rejection the run stops, the last draft is held in `run-output/`, and the PM gets the critic's reasons. Enforced in `agent.py` since M2.

**Pass action:** advance to the PM review checkpoint, queued. Never sent.

## 6. State: shared vs isolated

| | Cortex | Critic |
|---|---|---|
| **Shared** | the source log (both must judge the same data) and the proposed draft | same |
| **Isolated** | its system prompt, the conversation so far, the revision history. The critic never sees these, or it inherits the drafter's reasoning and blind spots | its own prompt and its deliberation. Cortex only ever receives the verdict and reasons |

Neither agent owns the handled-task ledger (`run-output/handled-tasks.json`); that belongs to the loop runner. Per-project memory across runs, from the Loop Spec, is still a plan.

## 7. Cost & latency budget

Measured 2026-09-21, drafter `gpt-4o-mini`, critic `gpt-4o`, critic priced at its own rates.

| Run | Model calls | Wall clock | Cost |
|---|---|---|---|
| Clean draft, critic passes | 3 drafter + 1 critic | 8.0 s | about $0.007, of which the critic is about $0.005 |
| Sabotaged draft, critic fails check 4, escalate | 3 drafter + 1 critic | 10.5 s | $0.0073 |
| Worst case at the revision cap (2 rejections) | 5 drafter + 3 critic | about 25 s | about $0.02 |
| The same run without a critic (the M2 build) | 2 to 3 drafter | about 5 s | about $0.002 |

The validator adds one `gpt-4o` call per draft, about $0.005 and 3 to 4 seconds each. A passing run costs about three times the unvalidated one and reaches the PM about three seconds later. The worst case at the cap is about $0.02 and 25 seconds.

**Budget, as a bound:** $0.05 and 60 seconds per run. Both sit well inside the existing $0.50 spend cap. The critic's tokens are printed per call so its share is visible.

## Build changes and evidence

| Map field | Change in `00-build/` |
|---|---|
| 5, the checks | `CRITIC_SYSTEM` rewritten: five yes/no checks, an explicit pass rule, "judge each check on its own", and a JSON shape with `failed_checks` so the fail action is decided in code |
| 5, tiered fail action | `agent.py`: a failed check 4 escalates at once with no revision; other failures revise, cap 2 (from M2); the rejection message names the failed check numbers |
| 3, roster | `CORTEX_CRITIC_MODEL` (default: the drafter's model) so the critic can run on a stronger model; set to `gpt-4o` in `.env.example`. Own price variables so the run cost counts it honestly |
| 4, evidence | `CORTEX_SABOTAGE=1`, a documented demo switch that tells the drafter to include a fake GA date and a fake 58% activation rate, so the critic has a bad draft to catch. Off by default; the trace prints a banner when it is on |

**What the runs showed.** Before this module the critic had never passed a draft: six fuzzy checks, no pass rule, and a status colour it could always call unsupported. With five checks and a pass rule, a clean draft passed on the first try (the first `HITL CHECKPOINT` in this build). On the sabotaged draft the `gpt-4o-mini` critic got the verdict right but the bookkeeping wrong: it filed the GA date under check 3 and missed the 58%. The `gpt-4o` critic caught both, quoting each line with the real value, and produced one false reason (it called a normal-severity issue a Sev-1). The verdict and the escalation were correct in every run; the reasons are what the stronger model buys, and the reasons are what the PM reads at an escalation.

**Independence, confirmed.** `critic.py` builds its own two-message context: its system prompt, then the source data and the proposed output. It never receives Cortex's messages, and Cortex only receives the verdict JSON.

Screenshots: `06-autonomy/screenshots/m3-critic-reject.png` and `m3-critic-pass.png`, linked from `06-autonomy/prototype.md`. Verbatim traces of all seven runs in the course archive, `2026-09-21/aaiac-m3-run-traces.md`.
