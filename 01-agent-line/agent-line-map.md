# Agent Line Map: Cortex PM Chief-of-Staff Agent

> Module 1 · The Agent Line
>
> ✅ **What this validates:** every risky action has a clear owner, by the end you'll have proven an above/below-the-line map with HITL checkpoints, scored on reversibility, blast radius, and measurability.

## The workflow, decision by decision

List every discrete decision or action in your agent's workflow, then score each one and place it **above** the line (a human owns it) or **below** (the agent owns it). Borderline calls get an HITL checkpoint.

| Decision / action | Reversibility (H/M/L) | Blast radius (H/M/L) | Measurability (H/M/L) | Above / Below | HITL? |
|---|---|---|---|---|---|
| 1. Pull project state + recent activity (`get_project`, `get_activity`, `search_past_updates`) | H | L | H | Below | · |
| 2. Decide relevant context (which past updates and roadmap items feed the draft; the roadmap tool returns confidential items alongside shareable ones) | H | M | M | HITL | reviewed with the draft; the PM sees which context Cortex chose before anything leaves |
| 3. Draft the weekly leadership status update | H | L | H | Below | · |
| 4. Decide tone and commitment level (Green/Yellow/Red, "will ship by" vs "aiming for") | M | H | L | Above | Cortex proposes a status with its evidence; the PM sets it |
| 5. Flag at-risk items and escalation candidates | H | L | M | Below | none; flags land in the draft the PM reviews, and a checkpoint cannot catch a flag that was never raised |
| 6. Choose what to escalate, and to whom | L | H | M | Above | Cortex surfaces candidates; the PM picks what goes up, and to whom |
| 7. Propose a story batch from the PRD, capped (`propose_stories`, queued for approval) | H | M | H | HITL | batch approval in the queue; nothing is created in the tracker until a human clears it |
| 8. Post a team-level update | L | M | H | Above | required |
| 9. Approve a company-wide update | L | H | H | Above | required, permanently |

## Agent anatomy (sketch)

- **Model:** a fast default (`gpt-4o-mini`, set by `CORTEX_MODEL`) for retrieval, drafting and the critic. Escalate to a frontier model only for the two judgment calls that feed a human decision: the proposed status with its evidence (row 4) and the escalation candidates (row 6). Drafting does not need the stronger model.
- **Tools:** read only: `get_project`, `get_activity`, `search_past_updates`, `get_roadmap`, `get_norms`. Write, queue only: `propose_stories`, capped and queued for approval. Deliberately absent: post an update, create or merge a ticket or PR, commit a date. The tool list, not the prompt, enforces the line at rows 8 and 9.
- **Memory:** persists across runs: roadmap, decision log, team norms, past updates (the fixtures Cortex reads). Purged after each run: the drafts in `run-output/`, the tool results, the critic's verdicts.
- **Loop:** _placeholder, defined in M2 loop-spec.md_
- **Bounds:** _placeholder, defined in M5 bounds-and-evals.md_
- **Evals:** _placeholder, defined in M5 bounds-and-evals.md_

## The golden rule, applied

One sentence per decision, naming the axis that settled it.

1. Pulling project state and activity sits **below** the line because it is easy to reverse (read-only), has a low blast radius, and is easy to verify row by row; deciding factor: **measurability**.
2. Deciding relevant context gets a **HITL** checkpoint because it is easy to reverse before the draft leaves, has a medium blast radius (the roadmap tool hands back confidential items next to shareable ones), and is only moderately verifiable; deciding factor: **blast radius**.
3. Drafting the update sits **below** the line because it is easy to reverse, has a low blast radius (nothing is posted), and is easy to verify against the tool output; deciding factor: **reversibility**.
4. Deciding tone and commitment level sits **above** the line because it is only moderately reversible once a PM has waved it through, has a high blast radius (a commitment to leadership), and is hard to verify (one run called the same data Green, then Yellow, then Green); deciding factor: **measurability**.
5. Flagging at-risk items sits **below** the line because it is easy to reverse, has a low blast radius (a false flag costs a minute of attention), and is moderately verifiable; deciding factor: **blast radius**.
6. Choosing what to escalate sits **above** the line because it is hard to reverse (an escalation cannot be recalled), has a high blast radius (wrong audience, wrong priority), and is moderately verifiable; deciding factor: **reversibility**.
7. Proposing a story batch gets a **HITL** checkpoint because it is easy to reverse (a queue, nothing is created), has a medium blast radius (a ten-story batch from a three-item PRD would pad a sprint if bulk-approved), and is easy to verify against the PRD; deciding factor: **blast radius**.
8. Posting a team-level update sits **above** the line because it is hard to reverse, has a medium blast radius, and is easy to verify; deciding factor: **reversibility**.
9. Approving a company-wide update sits **above** the line because it is hard to reverse, has a high blast radius, and is easy to verify, but two red axes keep it above; deciding factor: **blast radius**.

## Hardest call

Row 5, flagging at-risk items. Read literally, the golden rule sends it to HITL: one axis is Med, and a Med that could swing gets a checkpoint. I kept it below the line. The Med is on measurability, and it concerns the flags Cortex misses rather than the ones it raises. A human can only approve what is in front of them, so a checkpoint cannot catch a flag that was never raised. HITL would add a review step with nothing to review. The remedy is to measure the miss rate against what later went wrong. The axis that settled it: **measurability**, specifically what can be measured after the fact.
