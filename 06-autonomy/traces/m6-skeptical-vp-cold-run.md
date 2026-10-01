# M6 stranger test: skeptical-VP review, cold run (verbatim)

> 2026-09-30. Fresh agent, no session history, given only the repo README (uncommitted version with the pitch link and ship-plan sections) and the Deliverables Builder's own AI-review prompt, word for word.

---

**1. Would I ship it at the autonomy it claims?**
I need more. Cortex has only ever run on fixtures, and the README says plainly that "it has never read a real Jira, GitHub or Slack source."

**2. Is the dial set right?**
Today the dial is set right. Shadow mode with no post tool fits the blast radius, because the worst case is a bad draft sitting in a queue. The target rung is the problem. This is the line that worries me most:

> "the project-owning PM can climb to bounded-autonomous for the routine weekly draft"

The gate to climb is 4 weeks and 20 drafts. That is a small sample for a status report going to leadership. Worse, the one rule that actually protects leadership trust is still not enforced: "the 'never Green with a Sev-1 open' rule moved into code" is listed as something left to do. A rule that is still in the prompt is a rule the model judges for itself. Their own build insights say that is the weaker kind.

**3. Where does the 2am handoff break?**
The kill switch doesn't fit the deployment. The plan says "serverless," but the way to pause it is "`touch 00-build/KILL`," which is a file in a local repo. At 2am, who touches which file, on which machine, and does the serverless function even read it? The README also names no alert route. When the critic escalates, or the $2 daily cap trips, or the 60-second timeout fires, nothing says who gets paged. It only says the output "waits in the review queue." The owner is one named person, with the eng lead as backup. That is a contact list, not an on-call rotation. A runbook is mentioned but not summarized, so I can't see the first three steps.

**4. Which ROI claim would I push back on first?**
"Review time against the PM's own writing time." No baseline number is given, only "measured in shadow." The approval metric (18 of 20 drafts approved with wording edits only) can also hide rubber-stamping. A PM who skims and approves makes both numbers look great.

Evidence that would change my mind:
- Four weeks of timed PM writing before Cortex, compared with timed review after.
- The size of each edit as a diff, not just approved or rejected.
- One or two weeks where a second PM does a blind check of Cortex's status colour against the real project state.

**5. The single addition that makes it production-fundable**
A completed shadow run on live sources, with the results published. That means:
- 4 weeks of real Jira and GitHub data
- match rate on the status colour
- invented figures caught
- escalations fired, and who answered them
- cost per approved update

That turns a well-built design into evidence. While they're at it, the kill switch should become a deployment flag with a paging hook.

**Smaller flags a VP would notice**
- The progress table says "Pitch deck still to generate," but the top of the README links `pitch.html`.
- The repo tree is labeled `pm-os-agent/`.
- The "How to submit" section is left over from the course template.

None of these block shipping, but they suggest nobody did a final review.

**Verdict:** this is a strong cohort submission with honest framing about where it sits on the Trust Ladder. It isn't fundable for production until it has run on real data.
