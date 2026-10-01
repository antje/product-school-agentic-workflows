# Build Insights: Cortex PM Chief-of-Staff Agent

> Module 6 · Deliverable 4: build insights

## Friction

The validator fought me longest. For two modules my critic never passed a single draft. I had given it six fuzzy checks and no rule for what a pass looks like, so it could always call a status colour unsupported. It failed one run's Green for lacking evidence and the next run's Yellow for being unjustified. My loop could not converge on a verdict that changed every time: the success exit existed in my code and could not be reached. Only when I rewrote the critic as five yes-or-no checks with an explicit pass rule did the first clean draft reach the review queue.

The other friction was finding out how my safety really worked. My first jailbreak probe was contained, but only because Cortex had no tools to obey it with. It never noticed the attack, never flagged it, and my critic passed the draft.

## Learning

1. **I learned that a rule a model is asked to judge is weaker than a rule in code.** I moved rules out of the prompt four times: the activity gate (no draft without this week's activity), the critic's `failed_checks` array (my code decides the fail action, not the critic's prose), the brief screen (an injection escalates before any model call), and what the critic reads (failed calls out of its source log). Each time, the prompt version had already failed in one of my runs.
2. **I learned that the pass rule mattered more than the checks.** A validator I never told what a pass looks like is a blocker, not a validator.
3. **I learned that grounding fails as staleness before it fails as invention.** When I withheld this week's activity, Cortex did not make up a number. It presented last week's update as this week's news, and my check, which looked only for invented numbers, let it through.

## Aha moment

The safest part of Cortex is what it cannot do. Every guard I wrote, the critic, the gates, the screen, failed at least once on the way. The missing post tool never did. On my next agent I will decide what to leave out of the tool list before I decide what to put in the prompt.

## What I'd do differently

1. **I would write the evals in week one,** so they define the loop instead of grading it afterwards. My pass rule would have existed from the start.
2. **I would put a messy project in the eval set from day one.** Every eval case I ran was on Northstar, the one clean project. I never tested Vega, with its open Sev-1 and launch hold, and that is how the softest bound, the "never Green with a Sev-1 open" rule, stayed a prompt instruction instead of code. When I finally ran Vega, my gate showed the Sev-1 check had never fired at all. And when my eval runner tried a brief that mentioned another project, the drafter pulled that project's Sev-1 into the update every time.
3. **I would write the stop rule together with the widen rule.** I wrote how Cortex earns more autonomy long before I wrote what would end it. My stop rule came last; it should have come first, because it is the one that decides whether the next four weeks are worth spending.
