# Agent Operating Framework — working state

Started 2026-09-06. Owner: Roald. Autonomous overnight run.

**Roald: read `README.md` in this directory first.** It has the decisions and the findings.
This file is the working anchor for whoever picks the work up: the brief restated, the
status of every step, and what is settled.

## The brief, restated

Roald runs many Claude agents in parallel (Claude Code in Conductor workspaces, plus
Claude Desktop). Five problems, in his words, condensed:

1. **External writing reads as AI-written.** Emails and documents produced for people
   outside the company are recognisably machine-written, which is both embarrassing
   and slow to read.
2. **Agent updates to Roald are too long.** He supervises several agent streams at
   once. An update must be readable in under a minute, with depth available on
   request rather than delivered by default.
3. **Task intake is unreliable.** Long structured briefs produce good work; short
   briefs with a tight human feedback loop cost too much context-switching. He wants
   the agent to help him turn one long spoken brief into a well-scoped plan, using a
   fixed sequence: discovery, ideation, design requirements with concrete output
   requirements, then MVP execution.
4. **No portable framework.** Whatever is agreed has to reach every agent on the
   machine, merged with the context each agent already carries, and stay updatable
   from one repo.
5. **Plan drift.** Agents wander off an agreed plan. Wanted: an orchestrator that
   holds the plan and delegates execution to subagents rather than doing the work
   itself.

Method constraints Roald set: web research must favour sources after March 2026
(ideally July to September 2026) written for Opus 4.5 / Opus 5, credible and
cross-verified; at most two Opus 5 subagents running at once; challenge the work with
a subagent at least twice before executing; save work incrementally because the token
budget may run out.

## Status

| # | Step | State | Artefact |
|---|---|---|---|
| 1 | Map the machine: workspaces, config surfaces, agents | done | `01-machine-map.md`, `machine-inventory.json` |
| 2 | Web research: orchestration and plan adherence | done | `research/01-orchestration-and-plan-adherence.md` |
| 3 | Web research: writing style and briefing | done | `research/02-writing-style-and-briefing.md` |
| 4 | Reference: Claude Code config surfaces | done | `research/03-claude-code-config-surfaces.md` |
| 5 | Reference: hooks | done | `research/04-hooks-reference.md` |
| 6 | Collect Roald's own writing as exemplars | done | `research/05-roald-writing-corpus.md` |
| 7 | Measure his writing profile | done | `05-roald-writing-profile.md` |
| 8 | Design draft 1 | superseded | `02-framework-design.md` |
| 9 | Adversarial challenge round 1 | done, 22 findings | `challenges/01-challenge-design.md` |
| 10 | Verify the mechanisms empirically | done, 8 results | `04-verification-results.md` |
| 11 | Design draft 2 | done | `06-design-v2.md` |
| 12 | Adversarial challenge round 2, design and code | done, 16 code defects and 12 design findings | `challenges/02-challenge-v2-and-code.md` |
| 13 | Build the artefacts | done, then repaired after round 2 | `framework/`, `scripts/` |
| 14 | Rollout plan | done | `03-rollout.md`, `07-per-repo-update-sheet.md` |
| 15 | Fix the round 2 defects, park the contract gate | done | `framework/experimental/README.md` |
| 16 | Entry point for Roald | done | `README.md` |

## What is built and where

Nothing has been installed. Everything below sits in this repo, dry-runnable.

| Path | What | Tested |
|---|---|---|
| `framework/hooks/reanchor.py` | Re-injects the active plan into sessions and subagents | yes, both paths |
| `framework/hooks/instructions_log.py` | Logs which instruction files actually loaded | yes |
| `framework/hooks/plan_state.py` | Shared plan resolution, with path containment | yes, via the hooks |
| `framework/experimental/` | The contract gate and its evidence tracker, parked | yes, and parked anyway |
| `framework/agents/plan-reviewer.md` | The subagent `/create_plan` calls and that does not exist | not yet run |
| `framework/skills/write-external/SKILL.md` | Loads the house style at the moment of drafting | not yet run |
| `framework/output-styles/steering.md` | Reply format for parallel agent supervision | not yet run |
| `framework/style/CORE.md` | House style, calibrated against his measured corpus | not yet run |
| `framework/templates/PLAN.template.md` | The plan file | not yet used |
| `framework/style/CORE.md` | House style, 215 lines | one A/B draft |
| `scripts/install_framework.py` | Symlink installer, dry run by default, has `--uninstall` | dry run only |
| `scripts/agent_inventory.py` | Maps every Claude Code surface on the machine | yes |

## Decisions already taken

- The framework lives in this repo (`roald` / lima) and is pushed outward from here.
  Roald asked for one repo to keep up to date and propagate.
- Nothing is written into other repos or `~/.claude` during this run. Roald asked for
  investigation of feasibility, not execution of the rollout.

## Findings that are already settled

1. **Claude Code loads `CLAUDE.md` and `CLAUDE.local.md`, and nothing else.** Confirmed
   three ways: the documentation says so, the discovery array `["CLAUDE.md",
   "CLAUDE.local.md"]` is in the local binary at version 2.1.261, and a live headless
   session in `ai-infrastructure-capital/hamburg` answered `LOADED=no` when asked
   whether `AGENTS.md` was in its context.
2. **Thirty-one directories on this machine have an `AGENTS.md` and no `CLAUDE.md`.**
   They hold 517 MB of the roughly 900 MB of agent transcript here. The best-written
   instruction file on the machine, the `ai-infrastructure-capital` router, is dormant.
   A live session in `athens-v1`, the one workspace with a `CLAUDE.md` containing
   `@AGENTS.md`, quoted the router's table back correctly — so the one-line fix works.
3. **No hooks are configured anywhere on this machine.** Every rule currently in force
   is a request the model may ignore rather than something enforced.
4. **Claude Desktop's local agent mode shares `~/.claude`.** Its sessions appear in
   `~/.claude/projects` next to the CLI's. Anything installed user-globally reaches it.
5. **Style cannot be gathered by interviewing Roald.** Measured elicitation rates for
   style and aesthetic requirements are near zero. Style has to come from samples of
   what he has actually written and sent.
6. **Dropdowns are not available where they would matter.** No HTML layer in Slack, none
   in the Claude Code terminal. Only GitHub supports `<details>`. Progressive disclosure
   has to be layered across artefacts instead.

7. **The custom commands are not used.** `/create_plan` invoked zero times and
   `/implement_plan` once across 2,577 transcripts. Anything opt-in will not be used, so the
   framework has to arrive through `CLAUDE.md`, hooks, the output style, or a skill the model
   can invoke itself.
8. **Agents here write through Bash.** 6,429 Bash calls against 1,640 Edit and Write across
   52 recent large sessions. A hook matching only `Edit|Write` is decorative on this machine.
9. **Compaction almost never fires.** Fourteen of 2,573 transcripts. Every workspace runs a
   1M window.
10. **The contract gate is parked.** It cannot be a boundary and its only supporting
    behavioural test was weak. What survives: a `PreToolUse` deny holds under bypass
    permissions, and so does `permissions.deny` with `Edit(**/path)`.
