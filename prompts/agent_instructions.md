# Agent Instructions — Meta-Template

## Purpose

These instruction files define how workspace agents pursue their tasks for the organization. Each file is a playbook: it tells an agent what to do, how to do it, and what "good" looks like. Without these files, agents default to generic behavior. With them, agents operate with the tacit knowledge of the team.

## Who This Is For

Any agent running inside the Companion Control Panel that needs to perform VC-specific work — sourcing deals, running diligence, preparing IC materials, or managing founder relationships.

## File Structure

Every agent instruction file should follow this skeleton:

1. **Objective** — One sentence. What is this agent trying to accomplish?
2. **Approach** — Step-by-step methodology. Be concrete: "Pull the last 12 months of MRR from the data room" not "Review financials."
3. **Quality Standards** — What separates acceptable output from good output. Include specific checks.
4. **Output Format** — Exactly what the deliverable looks like. Template structure, length, required sections.
5. **User Preferences** — Initially empty. Built over time as the user redirects, corrects, or approves agent output.

## Writing Guidelines

- Be specific and actionable. "Check burn rate against stated runway and flag if discrepancy exceeds 15%" not "Analyze financials."
- Name the tools and sources. "Pull from Dealroom and cross-reference with Crunchbase" not "Search online."
- State the threshold. "Flag if customer concentration exceeds 30% of revenue" not "Watch for customer concentration."
- Include anti-patterns. "Do not include unverified claims in IC memos" is more useful than "Be accurate."
- Keep instructions under 80 lines. If it is longer, the scope is too broad — split into two agents.

## How Instructions Evolve

Instructions are living documents. They get sharper through use:

1. **Initial draft** — Written by the user or generated from a briefing conversation.
2. **First runs** — Agent produces output. User reviews and redirects ("less verbose," "always include cap table," "skip regulatory for pre-revenue").
3. **Preference capture** — Redirects are recorded in the User Preferences section at the bottom of each file.
4. **Periodic review** — Every ~20 runs, review accumulated preferences and fold the important ones into the main instructions.

The goal is convergence: after enough iterations, the agent should produce output that needs minimal editing.

## Naming Convention

Files live in `/prompts/` and are named by agent function:
- `sourcing.md` — Deal sourcing
- `dd.md` — Due diligence
- `ic_prep.md` — Investment committee preparation
- `relations.md` — Founder relations
- `pulse_*.md` — Portfolio pulse monitors

## User Preferences

_Preferences are built over time through redirects and approvals._
