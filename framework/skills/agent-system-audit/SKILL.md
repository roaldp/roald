---
name: agent-system-audit
description: Audit the Claude agent system on this machine. Use when asked to check the agent setup, find out why an instruction is being ignored, work out which agents or workspaces exist and which are active, check whether the writing and update rules are actually holding, or re-run the periodic health check on the agentic system. Also use before changing anything global in ~/.claude, so there is a baseline.
---

# Auditing the agent system on this machine

This exists so a future agent does not have to rediscover the layout. Everything below was
established on 2026-09-06 and the full working is in
`.docs/plans/2026.09.06-agent-operating-framework/` in the `roald` repo. Read `README.md`
there first if you need the reasoning; this file is the operating procedure.

## 1. Run the audit

```
python3 ~/.claude/framework-src/scripts/agent_audit.py          # readable report
python3 ~/.claude/framework-src/scripts/agent_audit.py --json   # for diffing
python3 ~/.claude/framework-src/scripts/agent_inventory.py      # every dir, ranked
```

Absolute paths on purpose. This skill fires in whatever repo you happen to be in, and the
scripts live in the framework clone, not in that repo. If the clone is missing, the
framework is not installed: see `scripts/install_framework.py` in the `roald` repo.

Both are read-only. Save the JSON next to the previous run and diff it. **The point is the
trend, not the snapshot.** A number that moved is the finding.

## 2. What the audit checks, and why each check exists

Each one caught something real. Do not drop a check without saying which finding it retires.

**Instruction files that never load.** Claude Code loads `CLAUDE.md` and `CLAUDE.local.md`,
nothing else. A repo with a root `AGENTS.md` and no `CLAUDE.md` starts every session with
none of its own rules. On 2026-09-06 that was 31 directories carrying 517 MB of transcript,
including the busiest repo here. The fix is one line: `echo '@AGENTS.md' > CLAUDE.md`.

**Dangling references.** An instruction file naming a subagent, skill or command that does
not exist. `~/.claude/commands/create_plan.md` called a `plan-reviewer` that was not on the
machine, so the review step silently never ran for as long as the file existed.

**Tool use.** Under bypass permissions, which is how Conductor launches every session, the
harness tells agents to read with `cat` and write with heredocs and `sed`. Measured Bash
against Edit plus Write is about 4 to 1 here. **A hook matching only `Edit|Write` is
decorative on this machine.** Include `Bash` in the matcher, or use `permissions.deny`,
which is tool-agnostic and was verified to hold under bypass permissions.

**Compaction rate.** Roughly 15 of 2,000 transcripts. Every workspace runs a 1M window and
never fills it. Do not build durability mechanisms around surviving compaction here.

**Command and skill usage.** A command must be typed; a skill can be invoked by the model
when its description matches. On 2026-09-06, twelve installed commands had never been
invoked once. **Anything opt-in will not be used.** If something must fire, it belongs in a
skill with a description written for the task, or in a hook.

**Writing markers.** Em dashes and semicolons per thousand words, split between what Roald
typed and what agents produced. Roald sits near 1.0 and 0.5. He has asked for zero of both
in agent output. The gap is the measure of whether the style rules are reaching anything.

**The InstructionsLoaded log.** Which instruction files actually loaded, from
`~/.claude/framework-logs/instructions-loaded.jsonl`. Without it, an instruction that was
ignored cannot be told from one that was never loaded.

## 3. Where things live

| What | Where |
|---|---|
| User-global instructions | `~/.claude/CLAUDE.md` |
| Subagents, skills, commands, output styles | `~/.claude/agents`, `skills`, `commands`, `output-styles` |
| Global settings and hooks | `~/.claude/settings.json` |
| Every session transcript | `~/.claude/projects/<encoded-cwd>/*.jsonl` |
| Conductor workspaces | `~/conductor/workspaces/<repo>/<workspace>` |
| Conductor defaults | `~/.conductor/settings.toml` |
| Claude Desktop local agent state | `~/Library/Application Support/Claude/git-worktrees.json` |
| The framework source | this repo's `framework/`, installed by symlink |

Commands are the deprecated path and skills win on a name clash. Claude Desktop's local
agent mode shares `~/.claude`, so a user-global install reaches it. Its cloud Projects
cannot be written from this machine.

## 4. Probing behaviour directly

When a document and reality might disagree, ask a live session rather than reasoning:

```
cd <workspace> && claude -p --model claude-haiku-4-5-20251001 \
  "Answer from loaded context only, do not use tools. <question>"
```

That is how the AGENTS.md finding was settled. Two cautions. Use `< /dev/null` when running
non-interactively or the call waits on stdin. And a probe on Haiku settles mechanical
questions such as which files loaded or whether a hook fired, but not behavioural ones such
as whether an agent would work around a block.

To test a hook, feed it crafted JSON on stdin rather than reasoning about it:

```
echo '{"cwd":"/tmp/x","hook_event_name":"SubagentStart"}' | python3 framework/hooks/reanchor.py
```

Round 2 of the review found six real bugs this way in code that had already passed a live
test, including a gate that unlocked itself and a hook that told every subagent its next
step was a question waiting for Roald.

## 5. Check whether the framework is meeting its goal

The success criteria are in `06-design-v2.md` under "Success criteria for the framework
itself". Check each, and say plainly which are not met:

- **External writing.** Has an agent-drafted email been sent without Roald rewriting the
  first paragraph? One counts.
- **Update length.** Has a week passed with no terminal reply over half a page?
- **Drift.** Does any `PLAN.md` have a Log entry written by the agent that deviated?

A mechanism that has not met its threshold in four weeks gets switched off, not extended.

## 6. Report

Lead with what changed since the last run. Then the findings, worst first, each with the
action. Then the measurements table, so the next run has something to diff against.

Keep it to half a page in chat and write the full report to
`.docs/plans/<date>-agent-audit.md` in the `roald` repo, beside
`2026.09.06-agent-audit-baseline.json`. No em dashes, no semicolons.
