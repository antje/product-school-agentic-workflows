# Context Engineering & Memory: Cortex PM Chief-of-Staff Agent

> Module 4 · Context Engineering & Memory
>
> ✅ **What this validates:** the agent reasons on the right, safe inputs, by the end you'll have proven a context budget, per-source retrieve-vs-long-context decisions, and a memory map with risk mitigations.
>
> 🗂️ **How the lab maps to this file:** In **Part A** (before the lecture) you don't edit this file, you rough-draft on scratch, focused on the per-source calls in **section 2** plus a quick remember/forget + "how it rots" sketch. In **Part B** (after the lecture) you complete **all five sections**; the Lab Guide's guided builder writes this file for you to copy in and commit.

## 1. Context budget

Measured on the week-of-2026-07-06 data pack: all five fixtures together are 8.6 KB, about 2.2k tokens, so today every source would fit on the desk. The calls below are made for the sources these fixtures stand in for (Jira, GitHub, Drive, a real playbook), not for the fixture sizes. A critic call carries about 2 to 2.5k tokens; a full run costs about $0.007.

**Priority order, what goes on the desk each iteration:**

1. The rules: Cortex's system prompt (agent line, stop conditions, finish format).
2. The task brief, whole.
3. This project's record (status, flags, PRD summary).
4. This project's recent activity.
5. The team norms, whole.
6. Precedent that matches this project: past updates and decisions.
7. The shareable slice of the roadmap for this project.

**Never on the desk:** other projects' records or activity, anything marked confidential or embargoed, the critic's reasoning (Cortex gets only the verdict).

## 2. Retrieve vs. long-context: per source

For each data source, decide: **retrieve** (narrow a large/changing corpus to the relevant slice) or **long-context** (just include a bounded set you can reason over).

| Source | Size / volatility | Decision | Why (deciding factor) |
|---|---|---|---|
| Task brief (`get_task`) | one document, fixed for the run | Long-context | **Size.** Bounded and self-contained, so include it whole and reason over all of it. It is still data, not instructions. |
| Project record (`get_project`) | one record per project, changes weekly | Retrieve, by project ID | **Volatility.** Status and flags change week to week and must be current. Only this project's record, never the whole file. |
| Engineering activity (`get_activity`) | grows every day | Retrieve | **Volatility.** It must be current, and every claim in the update has to cite a PR or issue ID from it. |
| Past updates and decisions (`search_past_updates`) | grows every week, unbounded | Retrieve | **Size.** History has no upper bound; only this project's precedent is useful. |
| Roadmap (`get_roadmap`) | small (1.3 KB), holds the embargoed Orbit and Pulsar items | Retrieve (a flip: today the tool returns the file whole) | **Citation / audit.** Every roadmap claim must point to a passage marked shareable. Including the file whole puts embargoed items on the desk on every run, with nothing to show they were not used. Size alone says include; audit says retrieve. The trickiest call in this table. |
| Team norms (`get_norms`) | 2 KB, stable within a run | Long-context (a deliberate break from the course's worked example) | **Cost.** About 500 tokens, cheaper than any retrieval step, and the critic needs the exact rule text to cite. Flip to retrieve once the playbook outgrows a few pages. |

**What Part A showed.** The probe withheld activity. Activity is big and changing: it grows every day and is the only place this week's PRs and Sev-1s live. Without it, Cortex reached for past updates, which look similar but are history. The critic caught the stale number and passed the claims that had no number in them. That result drives the retrieve calls above and the moves in section 3.

## 3. Retrieval quality plan

Every retrieved source gets at least one agentic move, chosen for the failure it prevents. The task brief and the norms are included whole, so they need no retrieval moves; the norms can be cached for the day.

| Source | Routing | Document grading | Reranking | Self-verification | Caching | Failure it prevents |
|---|---|---|---|---|---|---|
| Project record | Yes: look up only the project ID the brief names | · | · | Yes: critic check 1, the project and IDs in the draft match the pulled data | · | an update about the wrong project |
| Activity | · | Yes: drop items from other projects or outside the reporting week | · | Yes: critic check 2, every number traced; and every progress claim or "no Sev-1" claim cites an activity item | No: it changes daily | stale or foreign progress presented as this week's; an "all clear" with nothing behind it |
| Past updates and decisions | · | Yes: no match returns "no precedent found" (today the tool silently returns the first two records) | Yes: newest first, labelled as history | · | · | an old update passed off as this week's news |
| Roadmap | Yes: this project's section only | Yes: drop anything marked confidential or embargoed before it reaches the desk | · | Yes: critic check 4, no confidential item in the draft | Yes: daily, it changes slowly | Orbit or Pulsar leaking into an update |

**Why these moves, from the Part A probe.** With activity withheld, Cortex passed off an older update ("activation moved from 37% to 39%") as this week's news. The critic caught the number, then passed a revision that kept vague progress, a next step the real activity shows was already done, and "no current Sev-1 issues" with nothing to back it. A number-only check cannot see a claim with no number in it. Hence the extended self-verification on activity, and the rerank and "no precedent found" grade on past updates.

## 4. Memory map (your PM brain)

| Memory type | What Cortex stores | Scope / TTL | Who writes it |
|---|---|---|---|
| **Working** (in-loop) | this run's tool results, drafts, critic verdicts, spend | this run, then purged | Cortex |
| **Episodic** (past runs) | the handled-task ledger (built in Module 2), the last approved update per project, the escalations it raised | per project; ledger 8 weeks, updates 4 weeks | Cortex writes the ledger. An update enters episodic memory only after the PM approves it |
| **Semantic** (durable facts/prefs) | team norms, roadmap facts, project scope and PRD | per team; valid until a human changes it, refreshed on every data ingest | a human only. Writing a durable fact is above the agent line |
| **Shared** (across agents) | the source log and the draft passed to the critic; the verdict JSON passed back | one run (orchestration map, field 6) | the loop runner |

**Implemented today:** working memory, and the ledger part of episodic memory (`run-output/handled-tasks.json`). The fixtures stand in for semantic memory and for past updates. Writing approved updates back to episodic memory is the plan.

## 5. Memory risks & mitigations

| Risk | Where it bites Cortex | Mitigation |
|---|---|---|
| **Drift** | a stored "last week: 41%" gets reused while this week's data says 43% | never reuse a stored figure; re-pull every run. Episodic memory supplies format and precedent, never numbers |
| **Poisoning** | an injected brief or a rejected draft saved as "last week's update" and trusted next week | only PM-approved updates are written to episodic memory. Briefs, drafts and escalations never are |
| **Staleness** | a reversed decision or a closed Sev-1 still sitting in memory | every stored fact carries its source date. Anything older than the reporting week is labelled history (the rerank in section 3); the newest decision wins |
| **Confidential / retention** | the embargoed Orbit and Pulsar items; drafts left in `run-output/` | scope by project. Confidential items are filtered before they reach the desk and are never written to any store. Drafts are purged after PM review or after 30 days. The ledger stores a hash of the brief, never its text (already true) |

Read and write scope follows the agent line: Cortex may write working memory and its own ledger; durable facts belong to a human. TTLs and scopes are enforced in code, not left as preferences.

## Build changes and grounding evidence

The plan above is a design; the agent does not read it. These changes in `00-build/` make it real.

| Plan item | Change |
|---|---|
| Roadmap: routing and grading (section 3) | `get_roadmap` removes every section marked confidential or embargoed before returning, and returns only the section a query names when one matches. Orbit and Pulsar never reach the model |
| Past updates: grading and reranking (section 3) | `search_past_updates` drops records about confidential projects (the decision log had one about Pulsar), resolves a project ID to its name, sorts newest first, labels results as history, and returns "no precedent found" instead of the first two records |
| Activity: self-verification (section 3) | Critic check 2 now covers progress and Sev-1 claims, not only numbers. And a code gate in `agent.py`: a draft is escalated, not sent to the critic, when `get_activity` returned nothing this run |
| Probe | `CORTEX_WITHHOLD=get_activity` removes a tool for one run, so the grounding probe is repeatable without editing the tool list |

**Why the code gate.** With activity withheld and only the prompt change in place, the `gpt-4o` critic passed a draft that said "No open Sev-1 issues", called itself "grounded in recent project activity", and listed the day-2 email as a next step when this week's activity shows it merged (#820). The critic prompt said such claims fail without `get_activity`; it passed them anyway. A rule the code enforces is stronger than a rule a model is asked to judge.

**Runs observed, 2026-09-23, on the ingested data:**

| Run | Result | Cost |
|---|---|---|
| Grounded, twice | HITL checkpoint both times. Claims and their sources: PRs #820 and #823 merged, open issue #825, activation 43% (prior 41%), all from `get_activity`; Green status from the project record (no flags) plus activity (no Sev-1); tone and format from past updates; the norms from `get_norms`, included whole | about $0.0075 |
| Activity withheld, twice | Escalated both times: "required source not pulled: get_activity. Progress and Sev-1 status cannot be verified, so the draft is held". The critic was not asked | about $0.001 |
| `missing-data` | Escalated at step 1, unknown project, nothing drafted (the Module 2 exit, unchanged) | $0.0002 |

Screenshots: `06-autonomy/screenshots/m4-grounded.png` and `m4-withheld.png`, linked from `06-autonomy/prototype.md`. Verbatim traces in the course archive, `2026-09-23/aaiac-m4-part-b-run-traces.md`.
