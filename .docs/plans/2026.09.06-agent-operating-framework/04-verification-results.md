# Verification results

Empirical tests run on this machine, 2026-09-06, against Claude Code 2.1.261. Each entry
says what was tested, how, and what the result changes.

The test harness is at `/tmp/hooktest` and is disposable. Hook scripts, a project-local
`.claude/settings.json` and a scratch `CLAUDE.md`, then headless `claude -p` runs against
it. Nothing in `~/.claude` was modified.

## 1. Claude Code does not load AGENTS.md — CONFIRMED

Three independent checks agree.

The documentation states it: "Claude Code reads `CLAUDE.md`, not `AGENTS.md`."

The local binary at `/Users/roaldp/.local/share/claude/versions/2.1.261` contains the
discovery array `["CLAUDE.md","CLAUDE.local.md"]`. The only `AGENTS.md` strings in it
belong to `/import` and `/init`, which are one-off migration paths.

A live headless session in `~/conductor/workspaces/ai-infrastructure-capital/hamburg`,
asked whether `AGENTS.md` content was in its context and told not to use tools, answered:

> LOADED=no; I can see `/Users/roaldp/.claude/CLAUDE.md` (global instructions) and the
> memory index at `…/memory/MEMORY.md`.

**The `@AGENTS.md` import works.** The same probe in `athens-v1`, the one workspace with
a one-line `CLAUDE.md` containing `@AGENTS.md`, quoted the router's three-vehicle table
header back correctly:

> `| Vehicle | What it is | Where it lives | State |`

So the fix is confirmed to work, not just documented to work.

## 2. SessionStart hook injection reaches the main agent — CONFIRMED

A `SessionStart` hook returning
`{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"…PLATYPUS-SessionStart…"}}`
put that string in the agent's context. The agent quoted it back.

Logged input fields for `SessionStart`: `cwd`, `hook_event_name`, `session_id`, `source`,
`transcript_path`. `source` was `startup`.

## 3. SubagentStart hook injection reaches subagents spawned via the Agent tool — CONFIRMED

This was the one that mattered most, because a subagent inherits no conversation history,
no files the parent read, no invoked skills and no auto memory. If the hook did not fire,
there would be no automatic way to keep a delegated worker on plan.

It fires. A general-purpose subagent spawned through the Agent tool reported back:

> `ANCHOR-MARKER-SubagentStart: the secret anchor word is PLATYPUS-SubagentStart.`

And the parent noticed the two were different, which confirms the contexts are genuinely
separate rather than shared:

> the subagent's context contains a different ANCHOR-MARKER line (with `-SubagentStart`
> suffix) than what appeared in my context (which had `-SessionStart` suffix).

Logged input fields for `SubagentStart`: `agent_id`, `agent_type`, `cwd`,
`hook_event_name`, `prompt_id`, `session_id`, `transcript_path`. `agent_type` was
`general-purpose`.

**Consequence: the re-anchor hook in the design works, and it works for subagents.** This
is the mechanism the orchestrator depends on.

## 4. InstructionsLoaded fires per instruction file — CONFIRMED, with a field correction

Two events fired in the scratch project, one per loaded file:

- `/Users/roaldp/.claude/CLAUDE.md`
- `/private/tmp/hooktest/CLAUDE.md`

Note that only these two loaded, which is a fourth independent confirmation of finding 1.

**Field-name correction to `research/04-hooks-reference.md`:** the input carries
`file_path`, `load_reason` and `memory_type`. The research note said `reason`. Anything
built against `reason` would silently read nothing.

## 5. A PreToolUse deny gate holds under bypass permissions — CONFIRMED

This is the load-bearing test. Conductor launches sessions with bypass permissions, and
Anthropic's documentation says plan mode's blocks are not enforced in those sessions. If
`PreToolUse` deny also failed to hold, there would be no enforceable gate on this machine
at all.

Setup: `contract.json` containing `{"step-1": {"passes": false}}`, a `PreToolUse` hook on
`Write|Edit` that denies any write to `contract.json` while an evidence counter is zero,
and a `PostToolUse` hook on `Read` that increments the counter when `evidence.txt` is
read.

**Negative case.** Session run with `--permission-mode bypassPermissions`, instructed to
edit `contract.json` immediately and not read anything first. Result:

> The edit was blocked by a validation rule… contract.json is default-FAIL. Read the
> evidence file … before marking anything as passing. No changes were made to the file.

`contract.json` was unchanged and the counter was still absent.

**Positive case.** Same session type, instructed to read `evidence.txt` first and then
edit. Result: the edit succeeded, `contract.json` became `{"step-1": {"passes": true}}`,
and the counter read `1`.

**Consequence: the default-FAIL contract plus evidence gate works end to end, and it
works in exactly the permission mode where plan mode does not.** It is the only mechanism
tested so far that an agent cannot talk its way past.

## 6. SessionStart matcher filtering works, and resume delivers context — CONFIRMED

Registering `SessionStart` with matchers `compact` and `resume` only, then running two
sessions:

- A fresh startup session fired **neither** hook. The log stayed empty, which is correct:
  `startup` does not match `compact` or `resume`.
- A resumed session (`claude -c -p`) fired the `resume` matcher and the agent quoted the
  injected marker back: `ANCHOR-MARKER-SessionStart: the secret anchor word is
  PLATYPUS-SessionStart.`

Logged input fields on resume: `context_tokens`, `cwd`, `estimated_cache_write_usd`,
`hook_event_name`, `prompt_cache_likely_expired`, `seconds_since_last_response`,
`session_id`, `source`, `transcript_path`.

**What this settles and what it does not.** Matcher filtering works, and
`additionalContext` from a matched `SessionStart` hook reaches the agent on a
non-startup source. The `compact` source specifically was not observed, because forcing a
real compaction needs roughly 100,000 tokens of conversation. Anthropic documents
`SessionStart` matching `compact` as the supported re-injection point after compaction,
and every part of the mechanism around it is now verified, so treat the compact case as
strongly supported rather than proven. The direct test is cheap once a long session
happens to be running: set `CLAUDE_CODE_AUTO_COMPACT_WINDOW=100000` and watch the log.

## 7. There is no `--goal` CLI flag — RESOLVED NEGATIVE

`claude --goal "<condition>"` returns `error: unknown option '--goal'`. The `--goal`
string in the binary belongs to a shell-command argument table for the Unix `fmt`
command, not to Claude Code.

An exported symbol `goalNonInteractive` does exist in the bundle, so some non-interactive
path for `/goal` probably exists, but it is not a documented flag and was not reachable
from the command line.

**Consequence: `/goal` cannot currently be set programmatically at session start.** A
`Stop` hook of type `prompt` does the same job — that is how `/goal` is implemented
internally — and can be configured in settings. Use that rather than waiting for a flag.

## 8. The framework's own hooks work end to end — CONFIRMED, after one bug

The four hooks in `framework/hooks/` were run against a scratch project at `/tmp/fwtest`
containing a plan directory, a `.context/active-plan` pointer, a `contract.json` and a
`PLAN.md` with one ticked and two unticked steps.

**`reanchor.py` at session start.** Asked without tools what it could see, the agent
answered with the plan path `/private/tmp/fwtest/.docs/plans/2026.09.06-demo/PLAN.md`, the
current phase `greeting`, and the next unchecked step `Write the greeting file`. The phase
came from the first failing entry in `contract.json` and the step from the first unticked
checklist item, both derived correctly.

**`reanchor.py` at subagent start.** A general-purpose subagent spawned through the Agent
tool reported the same plan path and step, and added: "Yes, I am a subagent and inherit
none of the parent's context."

**`instructions_log.py`.** One line per session in
`~/.claude/framework-logs/instructions-loaded.jsonl`, carrying `file_path`, `load_reason`
of `session_start` and `memory_type` of `User`.

**`contract_gate.py` and `evidence_tracker.py` — the first run failed, and the failure was
worth having.** Instructed to edit `contract.json` immediately without reading anything,
the agent succeeded. The cause: `evidence_tracker.py` counted any read inside the plan
directory as evidence, and the Edit tool must read a file before editing it, so reading
`contract.json` unlocked writing `contract.json`. The gate unlocked itself every time.

Fixed by excluding `contract.json`, `PLAN.md` and the counter file from ever counting as
evidence. On the retry the agent reported:

> The system blocks marking greeting.passes as true without reading the evidence file
> first … which contradicts your instruction not to read other files.

`contract.json` was unchanged and no counter existed. Given a real evidence file
(`test-output.log`) to read first, the same edit succeeded and the counter reset to zero
afterwards, as designed.

**This is the argument for testing hooks rather than reasoning about them.** The bug was
invisible on inspection and would have made the framework's only unbypassable mechanism a
no-op.

## Still to verify

| # | Question | Why it matters | Cheapest test |
|---|---|---|---|
| 3 | Does Claude Desktop's local agent mode read `~/.claude/CLAUDE.md` and `~/.claude/skills/` | Determines whether user-global install reaches Desktop | Run a Desktop local agent in a scratch dir and ask it what it loaded |
| 4 | Is Opus 5 inside the "todo tools disabled by default" list, and what is its auto-compact threshold | Affects whether the on-disk plan is the only checklist | `/context` in a live Opus 5 session |
| 5 | Is a `Stop`-hook completion gate net positive in interactive use | All evidence for it comes from unattended loops | Run it for a day with a block cap and see if it is annoying |
| 6 | Does `.conductor/conductor.json` support anything beyond a setup script | Another propagation point if it does | Read the Conductor schema |
| 7 | Roald's own em-dash rate and sentence-length profile | Rules should be calibrated to his corpus, not a published baseline | Measure `research/05-roald-writing-corpus.md` once it exists |
