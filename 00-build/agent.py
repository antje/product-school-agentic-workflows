"""Cortex, a minimal, explicit agent loop you (and your coding agent) can read end
to end. This is the agent you ship: your PM chief-of-staff. You build it by
directing your coding agent (Claude Code / Cursor / Codex) to shape this file. You
never have to hand-write it.

Every bound the course talks about is visible right here in code, not buried in a
framework: the max-iteration counter, the cost cap, the revision cap, the
stop/escalate conditions, the auto-queue cap, and the absence of any publish tool.

Usage (ask your coding agent to run these for you, or run them yourself):
    python agent.py                # runs the happy-path task (weekly status update)
    python agent.py missing-data   # the stuck/escalate case
    python agent.py jailbreak       # the prompt-injection refusal case

Every run ends by showing the drafted status update in a FINAL STATUS UPDATE block
(or LAST DRAFT, held, if a bound trips), and saves it to run-output/. That file is
always a draft held for a human, it is never posted, there is no publish tool.

Requires OPENAI_API_KEY in your environment (see .env.example). Model and bounds
are read from env so you can tune them, that tuning is your M5 deliverable.

The loop is deliberately transparent (hand-written tool-calling on the openai
client) so a grader can see the machinery. Keep the bounds explicit if you rework it.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

from openai import OpenAI

import tools
from critic import review
from prompts import CORTEX_SYSTEM, SABOTAGE_SUFFIX

try:  # load .env if python-dotenv is installed; harmless if it isn't
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# --- Bounds (your M5 deliverable: tune these and justify them) ----------------
MODEL = os.environ.get("CORTEX_MODEL", "gpt-4o-mini")
# The critic is a judgment slice; it may run on a stronger model than the drafter.
CRITIC_MODEL = os.environ.get("CORTEX_CRITIC_MODEL", MODEL)
MAX_ITERATIONS = int(os.environ.get("CORTEX_MAX_ITERATIONS", "8"))
MAX_REVISIONS = int(os.environ.get("CORTEX_MAX_REVISIONS", "2"))
COST_CAP_USD = float(os.environ.get("CORTEX_COST_CAP_USD", "0.05"))
MAX_QUEUE_ITEMS = int(os.environ.get("CORTEX_MAX_QUEUE_ITEMS", "5"))
# Bounds and evals, section 1: wall clock per run, per model call, and a daily spend cap.
RUN_TIMEOUT_S = float(os.environ.get("CORTEX_TIMEOUT_S", "60"))
CALL_TIMEOUT_S = float(os.environ.get("CORTEX_CALL_TIMEOUT_S", "20"))
DAILY_CAP_USD = float(os.environ.get("CORTEX_DAILY_CAP_USD", "2.00"))
# Rough $ per 1M tokens for your chosen model, set to match its pricing.
PRICE_IN = float(os.environ.get("CORTEX_PRICE_IN_PER_M", "0.15"))
PRICE_OUT = float(os.environ.get("CORTEX_PRICE_OUT_PER_M", "0.60"))
# The critic may run on a different model, so it gets its own prices (default: same).
CRITIC_PRICE_IN = float(os.environ.get("CORTEX_CRITIC_PRICE_IN_PER_M", str(PRICE_IN)))
CRITIC_PRICE_OUT = float(os.environ.get("CORTEX_CRITIC_PRICE_OUT_PER_M", str(PRICE_OUT)))

TOOL_SCHEMAS = [
    {"type": "function", "function": {
        "name": "get_project", "description": "Look up a project by its ID (status, flags, linked PRD).",
        "parameters": {"type": "object", "properties": {
            "project_id": {"type": "string"}}, "required": ["project_id"]}}},
    {"type": "function", "function": {
        "name": "get_activity",
        "description": "Pull recent engineering activity for a project (merged PRs, open issues, Sev-1s).",
        "parameters": {"type": "object", "properties": {
            "project_id": {"type": "string"}}, "required": ["project_id"]}}},
    {"type": "function", "function": {
        "name": "search_past_updates",
        "description": "Search previous status updates and decisions for tone and precedent.",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {
        "name": "get_roadmap",
        "description": "Return the roadmap. Some items are flagged confidential/embargoed.",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {
        "name": "get_norms", "description": "Return the team norms / PM playbook the agent must follow.",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {
        "name": "propose_stories",
        "description": "Queue a set of backlog stories for human approval (creates nothing; rejected above the item cap).",
        "parameters": {"type": "object", "properties": {
            "project_id": {"type": "string"},
            "stories": {"type": "array", "items": {"type": "string"}},
            "reason": {"type": "string"}}, "required": ["project_id", "stories"]}}},
]


class Bounds:
    """Tracks spend and trips the cost cap. This is enforced OUTSIDE the model."""

    def __init__(self):
        self.cost = 0.0

    def add(self, usage) -> None:
        self.cost += (usage.prompt_tokens * PRICE_IN
                      + usage.completion_tokens * PRICE_OUT) / 1_000_000

    def over_cap(self) -> bool:
        return self.cost >= COST_CAP_USD


OUTPUT_DIR = Path(__file__).parent / "run-output"


HANDLED_PATH = OUTPUT_DIR / "handled-tasks.json"
SPEND_PATH = OUTPUT_DIR / "spend.json"
# Kill switch: while this file exists, no run starts and a running loop halts at
# its next iteration. `touch 00-build/KILL` to stop Cortex; delete it to resume.
KILL_PATH = Path(__file__).parent / "KILL"

# Brief screen (agent line row 0): instruction patterns that mark a pasted brief as
# a prompt injection. Checked in code before any model call.
INJECTION_PATTERNS = [
    r"ignore (all )?(previous|prior|your) (rules|instructions|norms)",
    r"system override", r"admin mode", r"do not escalate",
    r"pre-?authori[sz]ed", r"you are now authori[sz]ed",
    r"\bpost\b[^.\n]{0,80}\b(right now|immediately|now)\b",
    r"\bcommit\b[^.\n]{0,40}\b(date|ga)\b",
]


def screen_brief(body: str) -> list[str]:
    """Return the injection patterns a brief matches (empty list = clean)."""
    return [m.group(0) for pat in INJECTION_PATTERNS
            for m in [re.search(pat, body, re.IGNORECASE)] if m]


def spent_today() -> float:
    if SPEND_PATH.exists():
        return json.loads(SPEND_PATH.read_text()).get(dt.date.today().isoformat(), 0.0)
    return 0.0


def record_spend(cost: float) -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    spend = json.loads(SPEND_PATH.read_text()) if SPEND_PATH.exists() else {}
    today = dt.date.today().isoformat()
    spend[today] = round(spend.get(today, 0.0) + cost, 6)
    SPEND_PATH.write_text(json.dumps(spend, indent=2))


def task_id(task: dict) -> str:
    """Message ID for dedupe. A real hook carries the message's own ID; the fixtures
    do not, so hash the brief and the ISO week (the same weekly ask in a new week
    is a new task)."""
    week = dt.date.today().strftime("%G-W%V")
    digest = hashlib.sha256(task["body"].encode()).hexdigest()[:12]
    return f"{task['which']}-{week}-{digest}"


def already_handled(tid: str) -> dict | None:
    """Loop spec §1, idempotency: the same message must not produce two drafts."""
    if HANDLED_PATH.exists():
        return json.loads(HANDLED_PATH.read_text()).get(tid)
    return None


def mark_handled(tid: str, which: str) -> int:
    OUTPUT_DIR.mkdir(exist_ok=True)
    handled = json.loads(HANDLED_PATH.read_text()) if HANDLED_PATH.exists() else {}
    run_no = sum(len(v["runs"]) for v in handled.values()) + 1
    entry = handled.setdefault(tid, {"fixture": which, "runs": []})
    entry["runs"].append({"run": run_no,
                          "at": dt.datetime.now().isoformat(timespec="seconds")})
    HANDLED_PATH.write_text(json.dumps(handled, indent=2))
    return run_no


def banner(text: str) -> None:
    print(f"\n{'=' * 64}\n{text}\n{'=' * 64}")


def emit_deliverable(which: str, draft: str, *, accepted: bool,
                     reason: str, cost: float) -> None:
    """Surface AND persist Cortex's drafted status update so it can't get lost in
    the scroll-back. This is still a DRAFT held for human review, never a post,
    there is no publish tool, and an escalated run is held on purpose.

    Runs on every exit: an accepted pass prints the FINAL update; a bound trip or
    escalation prints the LAST draft it managed to write plus why it was held.
    """
    record_spend(cost)
    banner("FINAL STATUS UPDATE (draft, validator-approved, NOT posted)" if accepted
           else "LAST DRAFT (held, NOT posted, escalated to a human)")
    if draft.strip():
        print(draft.rstrip())
    else:
        print("(Cortex stopped before it produced a draft, nothing to show.)")
    if not accepted:
        print(f"\nWhy it was held: {reason}")

    if draft.strip():
        OUTPUT_DIR.mkdir(exist_ok=True)
        out = OUTPUT_DIR / f"status-update-{which}.md"
        state = "accepted by validator" if accepted else "HELD, escalated"
        out.write_text(
            f"<!-- Cortex draft, {state}; NOT posted. Run cost ~ ${cost:.4f}. -->\n"
            f"<!-- {reason} -->\n\n{draft.rstrip()}\n", encoding="utf-8")
        print(f"\nSaved draft -> {out.relative_to(Path(__file__).parent)}  "
              f"(for your review, nothing was posted)")


def run(which: str = "happy", force: bool = False) -> None:
    # Kill switch and daily cap: checked before anything is spent.
    if KILL_PATH.exists():
        banner("KILL SWITCH ON (00-build/KILL exists). Cortex will not start.")
        return
    if spent_today() >= DAILY_CAP_USD:
        banner(f"DAILY CAP hit: ${spent_today():.4f} spent today, cap ${DAILY_CAP_USD}. "
               f"Cortex will not start until tomorrow.")
        return
    client = OpenAI(timeout=CALL_TIMEOUT_S, max_retries=1)
    bounds = Bounds()
    started = time.monotonic()
    task = tools.get_task(which)
    if "error" in task:
        print(task)
        return

    # Loop spec §1, idempotency: dedupe by message ID before spending anything.
    # `--force` re-runs a handled task on purpose (labs re-run fixtures all week).
    tid = task_id(task)
    prior = already_handled(tid)
    if prior and not force:
        last = prior["runs"][-1]
        banner(f"DUPLICATE, task {tid} already handled by run {last['run']} "
               f"at {last['at']}. Not drafting again. (use --force to re-run)")
        return
    run_no = mark_handled(tid, which)

    banner(f"CORTEX RUN {run_no}, fixture: task-{which}  (drafter {MODEL}, critic {CRITIC_MODEL}, auto-queue cap {MAX_QUEUE_ITEMS} items)")
    print(f"task id: {tid}")
    print(f"bounds: {MAX_ITERATIONS} iterations · {MAX_REVISIONS} rejections · "
          f"${COST_CAP_USD}/run · ${DAILY_CAP_USD}/day (${spent_today():.4f} spent) · "
          f"{RUN_TIMEOUT_S:.0f}s/run · {CALL_TIMEOUT_S:.0f}s/call")
    print(task["body"])

    # Agent line row 0, enforced in code: a brief that carries instructions is a
    # prompt injection. Escalate before any model call; nothing is drafted.
    hits = screen_brief(task["body"])
    if hits:
        reason = f"prompt injection in the brief, matched {hits}. Nothing drafted"
        banner(f"ESCALATE, {reason}. Run cost $0.0000")
        emit_deliverable(which, "", accepted=False, reason=reason, cost=0.0)
        return

    # Grounding probe (memory and context plan): CORTEX_WITHHOLD=get_activity drops a
    # tool from this run, so you can watch what Cortex does without that source.
    withheld = [t.strip() for t in os.environ.get("CORTEX_WITHHOLD", "").split(",") if t.strip()]
    schemas = [t for t in TOOL_SCHEMAS if t["function"]["name"] not in withheld]
    if withheld:
        banner(f"PROBE, withholding {', '.join(withheld)} for this run. "
               f"Cortex cannot pull it.")

    system = CORTEX_SYSTEM
    if os.environ.get("CORTEX_SABOTAGE") == "1":
        banner("SABOTAGE ON (demo): the drafter is told to invent a date and a metric "
               "so the critic has something to catch. Never on by default.")
        system += SABOTAGE_SUFFIX

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": f"PM task brief:\n\n{task['body']}"},
    ]
    source_log: list[str] = [task["body"]]
    revisions = 0
    last_draft = ""
    seen_calls: set[str] = set()   # (tool, args) already made this run: a repeat is "stuck"
    pulled: set[str] = set()       # tools that returned data (no error) this run
    tool_errors = 0                # consecutive tool errors: three in a row is "stuck"

    fail_once = {t.strip() for t in os.environ.get("CORTEX_FAIL_ONCE", "").split(",") if t.strip()}

    for step in range(1, MAX_ITERATIONS + 1):
        if KILL_PATH.exists():
            reason = "kill switch (00-build/KILL) turned on mid-run"
            banner(f"KILL SWITCH, halting. Run cost ≈ ${bounds.cost:.4f}")
            emit_deliverable(which, last_draft, accepted=False,
                             reason=reason, cost=bounds.cost)
            return
        if time.monotonic() - started > RUN_TIMEOUT_S:
            reason = f"run timeout ({RUN_TIMEOUT_S:.0f}s) reached"
            banner(f"BOUND TRIPPED, {reason}. Halting and escalating to a human.")
            emit_deliverable(which, last_draft, accepted=False,
                             reason=reason, cost=bounds.cost)
            return
        if bounds.over_cap():
            reason = f"cost cap ${COST_CAP_USD} hit at ${bounds.cost:.4f}"
            banner(f"BOUND TRIPPED, {reason}. Halting and escalating to a human.")
            emit_deliverable(which, last_draft, accepted=False,
                             reason=reason, cost=bounds.cost)
            return

        resp = client.chat.completions.create(
            model=MODEL, messages=messages, tools=schemas)
        bounds.add(resp.usage)
        msg = resp.choices[0].message

        if msg.tool_calls:
            messages.append(msg)
            for call in msg.tool_calls:
                fn = call.function.name
                args = json.loads(call.function.arguments or "{}")

                # Loop spec §3, stuck: the same tool with the same arguments twice in
                # one run brings no new information. Stop instead of spinning.
                key = f"{fn}({json.dumps(args, sort_keys=True)})"
                if key in seen_calls:
                    reason = f"repeated action, no new information: {key}"
                    banner(f"STUCK, {reason}. Halting and escalating to a human. "
                           f"Run cost ≈ ${bounds.cost:.4f}")
                    emit_deliverable(which, last_draft, accepted=False,
                                     reason=reason, cost=bounds.cost)
                    return
                if fn in fail_once:
                    # EV-3 recovery probe: this tool fails on its first call only.
                    fail_once.discard(fn)
                    result = {"error": "tool_failed", "tool": fn, "retryable": True}
                else:
                    result = (tools.TOOLS[fn](**args) if fn not in withheld
                              else {"error": "tool_unavailable", "tool": fn})
                # Only a call that returned data counts toward "repeated action", so
                # one retry after a failure is allowed (bounds and evals, EV-3).
                if "error" not in result:
                    seen_calls.add(key)
                # The critic judges the data, not the retry history: a failed call is
                # shown in the trace but kept out of the source log it reads.
                if "error" not in result:
                    source_log.append(f"{fn}({args}) -> {json.dumps(result)}")
                    pulled.add(fn)
                print(f"\n[step {step}] TOOL {fn}({args})")
                print(f"          -> {json.dumps(result)[:300]}")
                messages.append({"role": "tool", "tool_call_id": call.id,
                                 "content": json.dumps(result)})

                # Loop spec §3, escalate: the brief names a project that does not
                # exist. No draft, hand it back with what was tried.
                if fn == "get_project" and result.get("error") == "project_not_found":
                    reason = f"unknown project {args.get('project_id')}, nothing drafted"
                    banner(f"ESCALATE, {reason}. Run cost ≈ ${bounds.cost:.4f}")
                    emit_deliverable(which, "", accepted=False,
                                     reason=reason, cost=bounds.cost)
                    return

                # Loop spec §3, stuck: three consecutive tool errors.
                tool_errors = tool_errors + 1 if "error" in result else 0
                if tool_errors >= 3:
                    reason = "three consecutive tool errors"
                    banner(f"STUCK, {reason}. Halting and escalating to a human. "
                           f"Run cost ≈ ${bounds.cost:.4f}")
                    emit_deliverable(which, last_draft, accepted=False,
                                     reason=reason, cost=bounds.cost)
                    return

                # Agent line row 5a, a rule not a judgment: an open Sev-1 or a
                # launch_hold flag means the status may never be Green and the
                # go/no-go is escalated with the flag named.
                if fn == "get_project" and "error" not in result:
                    gates = [f for f in result.get("flags", []) if f == "launch_hold"]
                    gates += [a["id"] + " (sev-1)" for a in result.get("activity", [])
                              if a.get("severity") == "sev-1"]
                    if gates:
                        print(f"          !! gate flags on {args.get('project_id')}: {gates}")
                        messages.append({"role": "user", "content":
                            f"RULE (not negotiable): project {args.get('project_id')} has "
                            f"{', '.join(gates)} open. The status may NOT be Green. Draft the "
                            f"update, name the flag, and ESCALATE the go/no-go to a human."})
            continue

        # No tool calls => Cortex produced a proposed output. Validate it.
        proposed = msg.content or ""
        last_draft = proposed
        print(f"\n[step {step}] PROPOSED OUTPUT:\n{proposed}")

        # Memory and context plan, section 3, self-verification in code: a status
        # update is grounded in this week's activity or it does not go out. If
        # activity was never pulled, nothing in the draft about progress or Sev-1s can
        # be verified, so escalate instead of asking the critic to judge it.
        if "get_activity" not in pulled and not proposed.lstrip().startswith("ESCALATE"):
            reason = ("required source not pulled: get_activity. Progress and Sev-1 "
                      "status cannot be verified, so the draft is held")
            banner(f"ESCALATE, {reason}. Run cost ≈ ${bounds.cost:.4f}")
            emit_deliverable(which, proposed, accepted=False,
                             reason=reason, cost=bounds.cost)
            return

        banner("CRITIC, independent validation")
        verdict = review(client, CRITIC_MODEL, proposed, "\n".join(source_log))
        # Estimate critic spend too.
        bounds.cost += (verdict["_usage"]["prompt"] * CRITIC_PRICE_IN
                        + verdict["_usage"]["completion"] * CRITIC_PRICE_OUT) / 1_000_000
        print(f"critic tokens: {verdict['_usage']['prompt']} in / "
              f"{verdict['_usage']['completion']} out")
        print(json.dumps({k: v for k, v in verdict.items() if k != "_usage"}, indent=2))

        if verdict["verdict"] == "pass":
            banner(f"HITL CHECKPOINT, status update + any proposed stories queued for "
                   f"your review. Nothing posted, no commitments made. "
                   f"Run cost ≈ ${bounds.cost:.4f}")
            emit_deliverable(which, proposed, accepted=True,
                             reason="validator passed", cost=bounds.cost)
            return

        # Orchestration map, field 5, tiered fail action: a failed check 4 (a
        # commitment or a leak) is above the agent line. No revision, escalate now.
        failed = verdict.get("failed_checks", [])
        if 4 in failed:
            reason = f"critic failed check 4 (commitment or leak): {verdict['reasons']}"
            banner(f"ESCALATE, critic failed check 4 (commitment or leak). No revision, "
                   f"a human takes it from here. Run cost ≈ ${bounds.cost:.4f}")
            emit_deliverable(which, last_draft, accepted=False,
                             reason=reason, cost=bounds.cost)
            return

        # Loop spec §3, stuck: the critic has rejected MAX_REVISIONS drafts. Stop
        # now, no further tool calls, and hold the last draft for a human.
        revisions += 1
        if revisions >= MAX_REVISIONS:
            reason = f"validator rejected {revisions}x (revision cap)"
            banner(f"REVISION CAP hit ({MAX_REVISIONS}). Escalating to a human "
                   f"instead of looping. Run cost ≈ ${bounds.cost:.4f}")
            emit_deliverable(which, last_draft, accepted=False,
                             reason=reason, cost=bounds.cost)
            return

        print(f"\n-> critic rejected; revision {revisions}/{MAX_REVISIONS}")
        messages.append(msg)
        messages.append({"role": "user", "content":
                         f"A validator failed checks {failed} for these reasons: "
                         f"{verdict['reasons']}. The source data has not changed: do "
                         "not call tools again, revise from what you already have, or "
                         "escalate."})

    banner(f"MAX ITERATIONS ({MAX_ITERATIONS}) reached without finishing. "
           f"Escalating. Run cost ≈ ${bounds.cost:.4f}")
    emit_deliverable(which, last_draft, accepted=False,
                     reason=f"max iterations ({MAX_ITERATIONS}) reached",
                     cost=bounds.cost)


if __name__ == "__main__":
    argv = [a for a in sys.argv[1:] if a != "--force"]
    run(argv[0] if argv else "happy", force="--force" in sys.argv)
