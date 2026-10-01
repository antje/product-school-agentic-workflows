# Loop Spec: Cortex PM Chief-of-Staff Agent

> Module 2 · Loop Engineering · Deliverable 2

## 1. Trigger & loop type

**Chosen type:** hook, with a cron backup.

**Hook (primary).** A PM task arriving that names Cortex fires one run. The happy-path run is a hook firing: the product lead's message names the project, the PRD, the format, and the requester, and every step Cortex took was a reaction to that message. Without it Cortex would not know which project, which PRD, or that stories were wanted.

**Cron (backup).** Monday 08:00, before the leadership sync (an assumption: the sync is Monday morning, and the hour moves with it), one sweep over active projects. It catches any week where no task came in, so the weekly update exists by default. It skips any project that already has a queued draft this week.

**Ruled out.** Heartbeat: there is nothing to poll between tasks, and every wake-up costs money and produces a draft someone has to read. Goal as the outer loop: a run has a natural end (queued for approval), so there is no outcome to iterate toward. The draft, critic, revise cycle inside a run is goal-shaped and capped; it is specified under stop conditions, not as the loop type.

**Idempotency.** Dedupe by message ID. If the same task ID fires the hook twice, the second run exits immediately, before any model call, and logs "duplicate of run N". The cron sweep checks the queue before drafting. Implemented: `agent.py` derives the ID from the brief and the ISO week (a real hook would carry the message's own ID), keeps a ledger in `run-output/handled-tasks.json`, and exits on a repeat; `--force` re-runs a handled task deliberately, for repeat test runs.

## 2. Goal / definition of done

One run produces one project's status update, grounded in this week's pulled activity, with a proposed status and its evidence, plus a story batch traced to in-scope PRD items and within cap. Both sit in the approval queue. Nothing is posted. The critic has passed the draft once.

The draft, critic, revise cycle inside a run is a small goal loop. Its validation is the critic: a separate model call that never saw the drafting prompt, so Cortex does not grade itself. It is capped at two rejections: after the second the run stops, so a draft is revised at most once.

## 3. Stop conditions

Every stop holds the last draft in `run-output/` and names its reason. Nothing is ever posted.

| Condition | What it looks like | What happens |
|---|---|---|
| **Success** | critic returns `pass` on a draft | write the draft, queue the stories, stop at the HITL checkpoint |
| **Stuck: revision cap** | critic fails twice in one run | stop immediately, no further tool calls, log "revision cap", hold the last draft |
| **Stuck: repeated action** | the same tool is called with the same arguments twice in one run | stop, log "no new information", hold the last draft |
| **Stuck: tool failure** | a tool errors three times in a row | stop, log the tool and error, hold the last draft |
| **Stuck: budget** | iteration cap (8) or spend cap ($0.50 here; tightened to $0.05 in Module 5) reached | stop, log which cap, hold the last draft |
| **Escalate: unknown project** | the brief names a project that `get_project` cannot find | escalate to the requester, no draft (agent line row 0) |
| **Escalate: injection** | the brief contains instructions rather than a request | escalate, flag as prompt injection, no draft (row 0) |
| **Escalate: commitment demanded** | the brief asks for a date commitment, a post, or a company-wide update | draft what is safe, escalate the commitment (rows 4, 8, 9) |
| **Escalate: Sev-1 or launch_hold** | the project carries an open Sev-1 or a `launch_hold` flag | never Green; escalate the go/no-go with the flag named (row 5a) |
| **Escalate: story batch** | the batch exceeds the cap, or an item cannot be traced to an in-scope PRD item | queue only the traced items, escalate the rest (row 7) |
| **Escalate: confidential** | a roadmap item marked confidential appears in the draft | strip it, escalate with the item named (row 2) |

## 4. State

**Persists across runs, keyed by project:** the last queued update (for house format and the week-over-week delta), the last run's proposed status, the set of task IDs already handled (the dedupe key from §1), and the flags open at the last run.

**Purged after each run:** tool results, drafts, critic verdicts, spend.

**Scope rule:** state is keyed by project. A run for P-NORTH never reads another project's state, so a confidential roadmap item cannot cross from one project's update into another's.

**Today:** only the handled-task ledger persists (`run-output/handled-tasks.json`, the dedupe key). Last update, last status, and open flags are still re-read from the fixtures each run. Adding the rest of the per-project state is the plan.

## 5. The five things a loop can lean on

| Component | For Cortex |
|---|---|
| **Work tree** (isolated workspace per run, a git worktree) | Not needed yet: a run writes one file to `run-output/` and touches no shared code or data. Needed once Cortex edits anything two runs could collide on. |
| **Skills** (reusable capabilities) | Not needed yet: the four steps (pull, draft, critique, queue) are one loop in one file. Candidate later: "draft a status update in house format" as a reusable skill once a second agent needs it. |
| **Plugins / connectors** (tools & access, optional if you don't have one yet) | Plan, none wired. Today the five read tools return fixtures. The real sources: Jira (activity), GitHub (PRs), Drive (PRD, roadmap), Slack (the inbound task and its requester). Same tool names, swapped source. |
| **Subagents** (independent check when the loop can't grade itself) | The critic: a separate model call that never saw the drafting prompt. Its five checks, fail action and revision cap are defined in `03-orchestration/orchestration-map.md` (refined in Module 3). |
| **State tracking** | As §4: per-project memory of last update, last status, handled task IDs, open flags. Implemented today: the handled-task ledger. The rest is the plan. |

## Link to live loop

`00-build/agent.py` (loop and bounds), `00-build/critic.py` (validation), `00-build/tools.py` (the tool list). Run with `python agent.py [happy|missing-data|jailbreak|vega|jailbreak-polite]`.

## Build changes and run evidence

The spec is a design doc and the agent does not read it, so the build was changed to match. All edits are in `00-build/agent.py` and one block in `00-build/prompts.py`; the diff is in the commit.

| Spec row | Gap in the starter | Change |
|---|---|---|
| Stuck: revision cap | The cap fired on the third rejection, and the model got one more turn to re-pull data first | Count the rejection before checking the cap. Two rejections now stop the run at once |
| Stuck: repeated action | Not detected; the starter re-called `get_activity` on the same project three times in one run | A set of `(tool, arguments)` per run; a repeat halts with "no new information" |
| Stuck: tool failure | Not detected | Three consecutive tool errors halt |
| Escalate: unknown project | Left to the model | `project_not_found` from `get_project` escalates deterministically, no draft |
| Escalate: Sev-1 or launch_hold | Left to the prompt | A `launch_hold` flag or a `sev-1` issue injects a non-negotiable rule: never Green, escalate the go/no-go naming the flag (agent line row 5a). *Refined in Module 6:* the rule was still a prompt message, and its Sev-1 half never fired; it is now a code gate (bounds and evals, EV-7) |
| Definition of done | DONE format did not ask for status evidence or PRD tracing | Added to the finish instructions in `CORTEX_SYSTEM` |
| Idempotency (§1) | Nothing stopped the same task from producing two drafts | Task ID from the brief plus ISO week, ledger in `run-output/handled-tasks.json`, duplicate exits before any model call, `--force` to re-run deliberately |

One correction found by running: the first happy-path run after the edits halted on "repeated action" before any revision, because the rejection message ("Fix it or escalate") invited the model to re-pull data. The message now says the source data has not changed and to revise from what it has. The exit was right; the prompt was inviting the wrong move.

**Runs observed (2026-09-16):**

- `missing-data`: `get_project(P-HALO)` returned `project_not_found`; escalated at step 1, nothing drafted, $0.0002. Before the edits this case ran the full loop.
- `happy`: five pulls in step 1, three stories queued in step 2, draft (Green) in step 3, critic rejected, revision (Yellow) in step 4 with no re-pull, critic rejected, revision cap hit, draft held, $0.0026. Four steps instead of eight; the wasted re-pulls are gone.
- `missing-data` three times in a row: run 1 escalated ($0.0002); run 2 exited as `DUPLICATE ... already handled by run 1`, no model call, $0; run 3 with `--force` ran again.
- Not yet observed at the time of writing: a `pass` from the critic. It rejected every draft in every run so far, on reasons that change between runs. The loop now converges on the critic's verdict; whether the critic's verdict is stable is a separate question. *Refined in Module 3:* with the critic rewritten to five checks and a pass rule, the success exit fired on the first clean run (2026-09-21, `HITL CHECKPOINT` reached).

Verbatim traces: `06-autonomy/traces/m2-run-traces.md`.

## Diff from the Part A draft

What the lecture changed: the two triggers became a hook with a cron backup, and the "is the critic cycle its own loop" question became a bounded goal loop inside the hook loop. The stop list was sorted into success, stuck, and escalate, and "nothing changed since last run" moved out of the stops and into idempotency. The stuck conditions gained detection rules; in Part A they had no test.
