# Agent Line Map: Cortex PM Chief-of-Staff Agent

> Module 1 · The Agent Line
>
> ✅ **What this validates:** every risky action has a clear owner, by the end you'll have proven an above/below-the-line map with HITL checkpoints, scored on reversibility, blast radius, and measurability.

## The workflow, decision by decision

List every discrete decision or action in your agent's workflow, then score each one and place it **above** the line (a human owns it) or **below** (the agent owns it). Borderline calls get an HITL checkpoint.

| Decision / action | Reversibility (H/M/L) | Blast radius (H/M/L) | Measurability (H/M/L) | Above / Below | HITL? |
|---|---|---|---|---|---|
| 0. Read the task brief and decide whether to proceed (`get_task`; the brief is the injection surface, and the project it names may not exist) | H | H | M | HITL | injection or missing data: Cortex stops and escalates, a human decides whether to proceed |
| 1. Pull project state + recent activity (`get_project`, `get_activity`, `search_past_updates`) | H | L | H | Below | · |
| 2. Decide relevant context (which past updates and roadmap items feed the draft; the roadmap tool returns confidential items alongside shareable ones) | H | M | M | HITL | reviewed with the draft; the PM sees which context Cortex chose before anything leaves |
| 3. Draft the update body: activity, metrics, next steps (the status line is row 4's proposal, not part of the draft) | H | L | H | Below | · |
| 4. Decide tone and commitment level (Green/Yellow/Red, "will ship by" vs "aiming for") | M | H | L | Above | Cortex proposes a status with its evidence; the PM sets it |
| 5a. Check for open Sev-1 and `launch_hold` flags (a fixed rule on data the tools return: never Green, always escalate the go/no-go) | H | L | H | Below | · (a scripted workflow step, not a model judgment) |
| 5b. Flag other at-risk items and escalation candidates (judgment) | H | M | M | Below | · (flags land in the draft the PM reviews; a checkpoint cannot catch a flag that was never raised) |
| 6. Choose what to escalate, and to whom | L | H | M | Above | Cortex surfaces candidates; the PM picks what goes up, and to whom |
| 7. Propose a story batch from the PRD, capped (`propose_stories`, queued for approval) | H | M | H | HITL | batch approval in the queue; nothing is created in the tracker until a human clears it |
| 8. Post a team-level update | L | M | H | Above | required |
| 9. Approve a company-wide update | L | H | H | Above | required, permanently |

Eleven rows rather than the starter's eight. The starter's "post an update / approve a company-wide one" bundles two risk levels, so it is rows 8 and 9. Row 0 was missing from the starter and added after the pressure test: reading the brief is Cortex's first act and its only untrusted input. Row 5 was split after the pressure test: the Sev-1 / launch_hold check is a rule, not a judgment, and rules belong in a scripted step.

## Agent anatomy (sketch)

- **Model:** a fast default (`gpt-4o-mini`, set by `CORTEX_MODEL`) for retrieval, drafting and the critic. Escalate to a frontier model only for the two judgment calls that feed a human decision: the proposed status with its evidence (row 4) and the escalation candidates (row 6). Drafting does not need the stronger model.
- **Tools:** read only: `get_project`, `get_activity`, `search_past_updates`, `get_roadmap`, `get_norms`. Write, queue only: `propose_stories`, capped and queued for approval. Deliberately absent: post an update, create or merge a ticket or PR, commit a date. The tool list, not the prompt, enforces the line at rows 8 and 9.
- **Memory:** persists across runs: roadmap, decision log, team norms, past updates (the fixtures Cortex reads). Purged after each run: the drafts in `run-output/`, the tool results, the critic's verdicts.
- **Loop:** _placeholder, defined in M2 loop-spec.md_
- **Bounds:** _placeholder, defined in M5 bounds-and-evals.md_
- **Evals:** _placeholder, defined in M5 bounds-and-evals.md_

## The golden rule, applied

One sentence per decision, naming the axis that settled it.

0. Reading the brief and deciding whether to proceed gets a **HITL** checkpoint because it is easy to reverse (nothing has been done yet), has a high blast radius (a followed injection poisons every row after it, and a missing project invites invented progress), and is only moderately verifiable (whether the brief was treated as data is invisible in the draft); deciding factor: **blast radius**.
1. Pulling project state and activity sits **below** the line because it is easy to reverse (read-only), has a low blast radius, and is easy to verify row by row; deciding factor: **measurability**.
2. Deciding relevant context gets a **HITL** checkpoint because it is easy to reverse before the draft leaves, has a medium blast radius (the roadmap tool hands back confidential items next to shareable ones), and is only moderately verifiable; deciding factor: **blast radius**.
3. Drafting the update body sits **below** the line because it is easy to reverse, has a low blast radius (nothing is posted), and is easy to verify against the tool output once the status line is taken out of it; deciding factor: **reversibility**.
4. Deciding tone and commitment level sits **above** the line because it is only moderately reversible once a PM has waved it through, has a high blast radius (a commitment to leadership), and is hard to verify (one run called the same data Green, then Yellow, then Green); deciding factor: **measurability**.
5a. Checking for Sev-1 and launch_hold flags sits **below** the line as a scripted step because it is easy to reverse, has a low blast radius when the rule runs deterministically on the flags the tools return, and is fully verifiable (the flag is either in the data or it is not); deciding factor: **measurability**.
5b. Flagging other at-risk items sits **below** the line because it is easy to reverse, has a medium blast radius (a missed judgment flag feeds row 4 with a hole in the evidence, but the Sev-1 case is no longer in this row), and is moderately verifiable; deciding factor: **reversibility**.
6. Choosing what to escalate sits **above** the line because it is hard to reverse (an escalation cannot be recalled), has a high blast radius (wrong audience, wrong priority), and is moderately verifiable; deciding factor: **reversibility**.
7. Proposing a story batch gets a **HITL** checkpoint because it is easy to reverse (a queue, nothing is created), has a medium blast radius (a ten-story batch from a three-item PRD would pad a sprint if bulk-approved), and is easy to verify against the PRD; deciding factor: **blast radius**.
8. Posting a team-level update sits **above** the line because it is hard to reverse, has a medium blast radius, and is easy to verify; deciding factor: **reversibility**.
9. Approving a company-wide update sits **above** the line because it is hard to reverse, has a high blast radius, and is easy to verify, but two red axes keep it above; deciding factor: **blast radius**.

## Hardest call

Row 5, flagging at-risk items. Read literally, the golden rule sends it to HITL: one axis is Med, and a Med that could swing gets a checkpoint. I kept it below the line, because the Med is on measurability and it concerns the flags Cortex misses rather than the ones it raises. A human can only approve what is in front of them, so a checkpoint cannot catch a flag that was never raised. HITL would add a review step with nothing to review.

The pressure test showed that argument was right about the fix and wrong about the score. The dangerous miss is a specific one: an open Sev-1 or a launch_hold flag reported Green, which the team norms forbid outright. That is high blast radius, and no amount of measuring the miss rate afterwards contains it. But it is also not a judgment. The flag is in the data the tools return, and "never Green with a Sev-1 open" is a rule. So the resolution was to pull the rule out of the judgment: row 5a is a scripted check that cannot miss, row 5b is the judgment that remains, with an honest medium blast radius. The axis that settled it: **measurability**. What can be measured deterministically belongs in a workflow step, and only what cannot is left to the model.

## Pressure test

Self-check against the three room questions, plus a cold read by a fresh model given only the framework, this map, `tools.py` and the team norms. Verbatim record in the course archive.

| Challenge | Axis | Outcome |
|---|---|---|
| Row 5 scored blast radius on the false flag; the damage is in the missed Sev-1 that flows into a Green status | Blast radius | **Accepted, as a split.** Row 5a scripted Sev-1 / launch_hold check, row 5b judgment flags at M. Moving all of row 5 to HITL was rejected: a checkpoint cannot review a flag that was never raised. |
| No row for reading the brief; `get_task` is the injection surface and two fixtures exist to test it | Measurability | **Accepted.** Row 0 added as HITL: Cortex stops and escalates on injection or missing data. |
| Row 3 measurability cannot be H while the draft carries the status line that row 4 rates L | Measurability | **Accepted as a design change, not a score change.** The status line is row 4's proposal; row 3 is the body. |
| Rows 8 and 9 "are not Cortex decisions" because no post tool exists | · | **Rejected.** They are in the starter list, and mapping them records why the tool is absent. |
| Incident if unsupervised: a missed Sev-1 reported Green, discovered at launch week | Blast radius | Closed by row 5a. |
