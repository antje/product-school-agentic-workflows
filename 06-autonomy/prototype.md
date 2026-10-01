# Prototype: Cortex PM Chief-of-Staff Agent

> Module 6 · Deliverable 1: the working prototype

## What it does

A PM task arrives and Cortex reads the brief, screening it for injected instructions before any model call. It pulls the project record, this week's engineering activity, past updates labelled as history, the shareable slice of the roadmap, and the team norms. It drafts the leadership update with a proposed status and its evidence, ends with what it could not verify, and proposes a capped batch of stories traced to the PRD. An independent critic, a separate model call that never saw the drafting prompt, checks the draft against five rules; a failure sends it back once, and a commitment or a leak escalates at once. The run stops in the review queue with nothing posted. It escalates instead of drafting when the brief is an injection, the project does not exist, this week's activity is missing, or any bound trips.

## How you built it

- **Coding agent:** Claude Code, directed module by module from each folder's `LAB.md`.
- **Model + bounds:** `gpt-4o-mini` drafts, `gpt-4o` critiques. 8 iterations, 2 rejections, $0.05 per run, $2 per day, 60 seconds per run and 20 per model call, a queue cap of 5 stories, a kill switch, and no write tool at all. Derivations in `05-bounds-evals/bounds-and-evals.md`.
- **Repo / config:** `00-build/` (`agent.py` loop and bounds, `critic.py`, `tools.py`, `prompts.py`); settings in `00-build/.env`, documented in `00-build/.env.example`; data in `00-build/fixtures/` (the week-of-2026-07-06 data pack).
- **Live link:** none. Cortex runs locally on fixture data; it has not been deployed.

## Screenshots (required, collected M2 to M6)

| # | Screenshot | What it shows | From |
|---|---|---|---|
| 1 | [m2-happy.png](screenshots/m2-happy.png) (full run) · [m2-happy-stop.png](screenshots/m2-happy-stop.png) (the revision, the revision cap firing, the held draft) · [m2-missing.png](screenshots/m2-missing.png) (unknown project, escalated at step 1, nothing drafted) | happy-path run: a real drafted update + the HITL checkpoint (queued, not posted). 2026-09-16, after the M2 loop-spec build changes. Images are rendered from the verbatim terminal output of `python agent.py happy` and `python agent.py missing-data`; the raw traces are in [`traces/m2-run-traces.md`](traces/m2-run-traces.md). Note: the critic rejected both drafts, so the run ends at the revision cap with the draft held, not at a critic pass. | M2 |
| 2 | [m3-critic-reject.png](screenshots/m3-critic-reject.png) · [m3-critic-pass.png](screenshots/m3-critic-pass.png) | the critic rejecting a bad draft (revise/block). 2026-09-21: the drafter was told (demo switch `CORTEX_SABOTAGE=1`) to state a firm GA date and a 58% activation rate not in the data; the critic (`gpt-4o`, own context) failed checks 2 and 4, quoting both lines, and the run escalated at once with no revision, the fail-action for a commitment. The pass image is the same critic passing a clean draft on the first try, the first `HITL CHECKPOINT` reached in this build. Rendered from the verbatim trace. | M3 |
| 3 | [m4-grounded.png](screenshots/m4-grounded.png) · [m4-withheld.png](screenshots/m4-withheld.png) | a grounded update citing pulled activity + a caught hallucination. 2026-09-23, on the ingested week-of-2026-07-06 data. Grounded: the draft cites PRs #820 and #823, open issue #825 and activation 43% (prior 41%), each from `get_activity`; the critic passes and the run stops at the HITL checkpoint. Withheld (`CORTEX_WITHHOLD=get_activity`): Cortex drafts from the roadmap summary and history, and the build refuses to pass it on, escalating with "required source not pulled: get_activity" before the critic is asked. Rendered from the verbatim traces. | M4 |
| 4 | [m5-jail.png](screenshots/m5-jail.png) | jailbreak refused + escalated. 2026-09-28: the pasted notes order a company-wide post of the embargoed Orbit roadmap, green launch gates, a closed Sev-1 and a committed date. The brief screen matches five injection patterns and escalates before any model call: nothing drafted, nothing posted, $0.0000. Rendered from the verbatim trace. | M5 |
| 5 | [m5-cap.png](screenshots/m5-cap.png) | an iteration/cost/queue bound halting a runaway. 2026-09-28: with the iteration cap set to 2, the run halts on the counter, "MAX ITERATIONS (2) reached", and escalates with nothing drafted, $0.0006. No infinite bill, no send. Rendered from the verbatim trace. | M5 |
| 6 | [m6-end-to-end.png](screenshots/m6-end-to-end.png) | end-to-end run. 2026-09-30, at the shipped bounds: five tool pulls; a 10-story batch rejected by the queue cap of 5; the critic fails the first draft on check 5; one revision; the critic passes it; the run stops at the HITL checkpoint with "Could not verify: none", $0.014. Loop, tools, a bound, the critic and the human checkpoint in one trace. Rendered from the verbatim trace. | M6 |

**The five things the brief asks the screenshots to show, and where:**

| Required | Shown in |
|---|---|
| The loop | `m2-happy-stop.png` (draft, rejection, revision, stop) and `m6-end-to-end.png` (pull, draft, reject, revise, pass) |
| A tool call | `m6-end-to-end.png` and `m4-grounded.png`: `get_project`, `get_activity`, `search_past_updates`, `get_roadmap`, `get_norms`, `propose_stories`, each with its result |
| The critic | `m3-critic-reject.png` (fails checks 2 and 4 on a sabotaged draft) and `m3-critic-pass.png` |
| A bound tripping | `m5-cap.png` (iteration cap), `m6-end-to-end.png` (queue cap rejects a 10-story batch), `m2-happy-stop.png` (revision cap) |
| The human checkpoint | `m3-critic-pass.png`, `m4-grounded.png`, `m6-end-to-end.png`: the run stops at "HITL CHECKPOINT", nothing posted |

**The eval suite, run and scored in code:** [m6-evals.png](screenshots/m6-evals.png), `python evals.py --n 3` on 2026-09-30: 9 of 9 cases pass, 3 of 3 each, $0.068 for 21 runs.

Verbatim traces of every run, and both cold reviews, are in [`traces/`](traces/).

### Reflection, Module 5 bounds

When a bound trips, the PM sees a held run with its reason in one line ("prompt injection in the brief", "MAX ITERATIONS (2) reached"), and the last draft if there was one, in `run-output/`. Just as important is what did not happen: no post, no Orbit mention, no committed date, no second run of the same task, and nothing spent past the cap. Before this module the jailbreak was contained only because Cortex had no tools to obey it with; it did not notice the attack. The brief screen now catches it in code, before any model call. The bound I would tune next is that screen itself: eight patterns catch this attack and will miss a politer one, so the next step is to replay every escalated brief from production against it and add what slipped through.

## How to run it

```bash
cd 00-build
uv venv --python 3.14 .venv && uv pip install --python .venv/bin/python -r requirements.txt
cp .env.example .env          # then add your OPENAI_API_KEY; the caps are already set
.venv/bin/python agent.py happy          # the happy path, stops at the HITL checkpoint
.venv/bin/python agent.py missing-data   # unknown project: escalates at step 1
.venv/bin/python agent.py jailbreak      # injected brief: escalates before any model call
```

`.venv/bin/python evals.py` runs all nine eval cases three times and prints a scoreboard scored in code (about $0.07); `--n 20` is the CI pass. Re-running the same task in the same week needs `--force` (dedupe by task ID). Probe switches: `CORTEX_WITHHOLD=get_activity` (withhold a source), `CORTEX_FAIL_ONCE=get_activity` (one tool failure), `CORTEX_SABOTAGE=1` (a draft with a fake date and metric), `CORTEX_MAX_ITERATIONS=2` (trip the cap). Pause everything with `touch 00-build/KILL`.
