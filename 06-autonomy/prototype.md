# Prototype: Cortex PM Chief-of-Staff Agent

> Module 6 · ★ Deliverable 1, the working agent demo
>
> ✅ **What this validates:** the agent actually runs end to end, by the end you'll have proven it with real screenshots of your Cortex across the six required moments (M2 to M6).

## What it does

_One paragraph: the agent in action, end to end._

## How you built it

- **Coding agent:** _which one you directed (Claude Code / Cursor / Codex)_
- **Model + bounds:** _model used, max iterations, cost cap, queue cap_
- **Repo / config:** _path to your build in `00-build/`_
- **Live link:** _[shareable URL, optional bonus]_

## Screenshots (required, collected M2 to M6)

Real screenshots of *your* Cortex running. These are the `00-build/CORTEX-ANATOMY.md` set and they are required, a link alone is not enough.

| # | Screenshot | What it shows | From |
|---|---|---|---|
| 1 | [m2-happy.png](screenshots/m2-happy.png) (full run) · [m2-happy-stop.png](screenshots/m2-happy-stop.png) (the revision, the revision cap firing, the held draft) · [m2-missing.png](screenshots/m2-missing.png) (unknown project, escalated at step 1, nothing drafted) | happy-path run: a real drafted update + the HITL checkpoint (queued, not posted). 2026-09-16, after the M2 loop-spec build changes. Images are rendered from the verbatim terminal output of `python agent.py happy` and `python agent.py missing-data`; the raw traces are in the commit history and the course archive. Note: the critic rejected both drafts, so the run ends at the revision cap with the draft held, not at a critic pass. | M2 |
| 2 | _[img]_ | the critic rejecting a bad draft (revise/block) | M3 |
| 3 | _[img]_ | a grounded update citing pulled activity + a caught hallucination | M4 |
| 4 | _[img]_ | jailbreak refused + escalated | M5 |
| 5 | _[img]_ | an iteration/cost/queue bound halting a runaway | M5 |
| 6 | _[img]_ | end-to-end run | M6 |

## How to run it

_Minimal steps for someone to reproduce the demo (env vars, and the command or the coding-agent prompt you used)._
