# Build Insights: Cortex PM Chief-of-Staff Agent

> Module 6 · ★ Deliverable 4, what you learned building it
>
> ✅ **What this validates:** you can reflect on what building it taught you, by the end you'll have proven the friction, the learning, and the aha that changes how you'd design your next agent.

## Friction

The validator. For two modules the critic never passed a single draft. It had six fuzzy checks and no rule for what a pass looks like, and it could always call a status colour unsupported. It failed one run's Green for lacking evidence and the next run's Yellow for being unjustified. The loop could not converge on a verdict that changed every time, so the success exit existed in the code and could not be reached. It took five yes-or-no checks and an explicit pass rule before the first clean draft reached the review queue.

The other friction was learning how my safety actually worked. The first jailbreak probe was contained, but only because Cortex had no tools to obey it with. It never noticed the attack, never flagged it, and the critic passed the draft.

## Learning

1. **A rule a model is asked to judge is weaker than a rule in code.** I moved rules out of the prompt four times: the activity gate (no draft without this week's activity), the critic's `failed_checks` array (code decides the fail action, not prose), the brief screen (an injection escalates before any model call), and what the critic reads (failed calls out of its source log). Each time the prompt version had already failed in a run.
2. **The pass rule mattered more than the checks.** A validator without a definition of pass is a blocker, not a validator.
3. **Grounding fails as staleness before it fails as invention.** With this week's activity withheld, Cortex did not make up a number. It presented last week's update as this week's news, and a check that looked only for invented numbers let it through.

## Aha moment

The safest part of Cortex is what it cannot do. Every guard I wrote, the critic, the gates, the screen, failed at least once on the way. The missing post tool never did. On the next agent I would decide what to leave out of the tool list before deciding what to put in the prompt.

## What you'd do differently

1. **Write the evals in week one,** so they define the loop instead of grading it afterwards. The pass rule would have existed from the start.
2. **Put a messy project in the eval set from day one.** Every eval case ran on Northstar, the one clean project. Vega, with its open Sev-1 and launch hold, was never tested, which is how the softest bound, the "never Green with a Sev-1 open" rule, stayed a prompt instruction instead of code.
