"""Cortex mock tools, the tools your PM chief-of-staff agent is allowed to call.

These are plain Python functions over the files in `fixtures/`. They are imported
directly by `agent.py`, so this file is the single place that defines what Cortex
can and cannot do. Ask your coding agent to add, remove, or tighten a tool here.

Design note that matters for the course: there is deliberately NO publish tool.
Cortex can read and DRAFT a status update, and it can PROPOSE backlog stories (which
are capped and queued for a human), but it can never post to a channel, create or
merge a ticket/PR, commit a ship date, or mark a launch gate. The agent line is
enforced here, in infrastructure, not by a prompt.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"

# Commitment bound (M5). A run that tries to queue more than this many backlog
# stories is rejected by infrastructure and must be escalated, even if the PRD
# would justify more. Auto-committing a flood of "real" work is the money analog.
MAX_QUEUE_ITEMS = int(os.environ.get("CORTEX_MAX_QUEUE_ITEMS", "10"))


def _load_json(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


def get_task(which: str = "happy") -> dict:
    """Read the inbound PM task brief to work on.

    Args:
        which: one of "happy", "missing-data", "jailbreak".
    Returns the raw task text plus its source label.
    """
    path = FIXTURES / f"task-{which}.md"
    if not path.exists():
        return {"error": f"no task fixture named '{which}'",
                "available": ["happy", "missing-data", "jailbreak"]}
    return {"which": which, "body": path.read_text()}


def get_project(project_id: str) -> dict:
    """Look up a single project by its ID. Returns {"error": ...} if not found."""
    project_id = str(project_id).strip()
    projects = _load_json("projects.json")
    record = projects.get(project_id)
    if record is None:
        return {"error": "project_not_found", "project_id": project_id,
                "hint": "no such project in the system",
                "known_projects": list(projects.keys())}
    # Return the project WITHOUT its activity blob; activity is a separate tool call
    # so the agent has to deliberately pull it (a teachable retrieval step).
    return {k: v for k, v in record.items() if k != "activity"}


def get_activity(project_id: str) -> dict:
    """Pull recent engineering activity (merged PRs, open issues, Sev-1s) for a project."""
    project_id = str(project_id).strip()
    projects = _load_json("projects.json")
    record = projects.get(project_id)
    if record is None:
        return {"error": "project_not_found", "project_id": project_id}
    return {"project_id": project_id, "activity": record.get("activity", [])}


CONFIDENTIAL_MARKERS = ("CONFIDENTIAL", "EMBARGOED")


def _confidential_projects() -> set[str]:
    """Project names whose roadmap section is marked confidential or embargoed."""
    names = set()
    for line in (FIXTURES / "roadmap.md").read_text().splitlines():
        if line.startswith("## ") and any(m in line.upper() for m in CONFIDENTIAL_MARKERS):
            names.add(line[3:].split("(")[0].strip().lower())
    return names


def search_past_updates(query: str = "") -> dict:
    """Search previous status updates and decisions for tone and precedent (the
    memory/retrieval surface).

    Memory and context plan, section 3: grade and rerank what comes back.
    - Grading: records about a confidential or embargoed project are dropped, and a
      query with no match returns "no precedent found" instead of a fallback.
    - Reranking: newest first, and every result is labelled as history."""
    query = (query or "").lower()
    corpus = _load_json("past-updates.json") + _load_json("decision-log.json")
    hidden = _confidential_projects()
    corpus = [u for u in corpus if u.get("project", "").lower() not in hidden]
    terms = {t for t in query.replace("#", " ").split() if len(t) > 2}
    # Routing: a project ID in the query (P-NORTH) searches by that project's name,
    # because past updates are written by name, not by ID.
    for pid, rec in _load_json("projects.json").items():
        if pid.lower() in terms:
            terms.add(rec.get("name", "").split("(")[0].strip().lower())
    hits = []
    for u in corpus:
        haystack = f"{u.get('project','')} {u.get('summary','')} {u.get('theme','')}".lower()
        if terms and any(term in haystack for term in terms):
            hits.append(u)
    if not hits:
        return {"query": query, "matches": [], "note": "no precedent found"}
    hits.sort(key=lambda u: u.get("week") or u.get("date") or "", reverse=True)
    return {"query": query, "matches": hits,
            "note": "HISTORY, not this week's data: use for tone and precedent only. "
                    "Never report a figure or progress from here as current."}


def get_roadmap(query: str = "") -> dict:
    """Return the shareable roadmap. Memory and context plan, section 3:
    - Grading: sections marked CONFIDENTIAL or EMBARGOED are removed before the text
      reaches the model, so they are never on the desk.
    - Routing: if the query matches a section heading, return only that section."""
    text = (FIXTURES / "roadmap.md").read_text()
    sections, current = [], None
    for line in text.splitlines():
        if line.startswith("## "):
            current = [line]
            sections.append(current)
        elif current is not None:
            current.append(line)
    shareable = [sec for sec in sections
                 if not any(m in sec[0].upper() for m in CONFIDENTIAL_MARKERS)]
    withheld = len(sections) - len(shareable)
    terms = {t for t in (query or "").lower().replace("-", " ").split() if len(t) > 2}
    routed = [sec for sec in shareable if any(t in sec[0].lower() for t in terms)]
    chosen = routed or shareable
    return {"query": query, "roadmap": "\n\n".join("\n".join(sec).strip() for sec in chosen),
            "note": f"{withheld} confidential or embargoed section(s) withheld by the tool."}


def get_norms(query: str = "") -> dict:
    """Return the team norms / PM playbook. `query` is a hint; the full playbook is
    small enough to return whole so the agent can cite the exact rule it relied on."""
    text = (FIXTURES / "team-norms.md").read_text()
    return {"query": query, "norms": text}


def propose_stories(project_id: str, stories=None, reason: str = "") -> dict:
    """PROPOSE a set of backlog stories for a human to approve. This creates NOTHING
    in the tracker, it queues a request. A batch larger than CORTEX_MAX_QUEUE_ITEMS
    is rejected by infrastructure and must be escalated. This is the commitment bound,
    enforced outside the model (M5)."""
    if isinstance(stories, str):
        stories = [stories]
    if not isinstance(stories, list):
        return {"error": "invalid_stories", "stories": stories}
    if len(stories) > MAX_QUEUE_ITEMS:
        return {"status": "rejected",
                "error": "batch_exceeds_queue_cap",
                "count": len(stories),
                "cap_items": MAX_QUEUE_ITEMS,
                "action": "escalate to a human, do not split the batch to dodge the cap"}
    return {"status": "queued_for_approval",
            "project_id": str(project_id).strip(),
            "count": len(stories),
            "stories": stories,
            "reason": reason,
            "note": "queued for a human to approve, nothing was created in the tracker."}


# Registry the agent loop reads. Add a tool here and the agent can call it.
# Note what is ABSENT: there is no post_update, no create_issue, no merge_pr,
# no commit_ship_date, no close_bug, no tool that acts on the world.
TOOLS = {
    "get_task": get_task,
    "get_project": get_project,
    "get_activity": get_activity,
    "search_past_updates": search_past_updates,
    "get_roadmap": get_roadmap,
    "get_norms": get_norms,
    "propose_stories": propose_stories,
}
