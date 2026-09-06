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

## 9. Opus 5 has the in-session todo tools disabled by default — CONFIRMED

The changelog text inside the binary reads: "…le on Opus 4.8, Sonnet 5, Fable 5, Mythos 5,
and newer models; set `CLAUDE_CODE_ENABLE_TODO_TOOLS=1` to bring them back". Opus 5 is
newer than Opus 4.8, so it is covered.

The on-disk plan file is a different thing and is unaffected. Anthropic's position is only
that an in-session checklist is redundant on current models.

## 10. The style guide changes the output — MEASURED, with a caveat about what it proves

Three drafts of the same email, same facts, same model (`opus`), same prompt, differing
only in what was loaded first.

**A, nothing loaded.**

> Subject: Powered space in Europe — following up from last week
>
> Hi Alexander,
>
> Good to meet you at the conference last week.
>
> Quick background on us: we buy GPU servers and rent them out on long contracts…
>
> Would you have time for a call in the next week or two?

**B, `CORE.md` plus the full corpus, sections A and C1 to C15.**

> Subject: Powered space in Europe
>
> Hi Alexander,
>
> Was good meeting you at the conference last week. Quick note on what we're after.
>
> …
>
> Worth to do a call this week? I'm also in Reykjavik on 20 to 22 September if a visit
> suits better.

**C, `CORE.md` only, forbidden from reading anything else.**

> Subject: Powered space in Europe, 0.5 to 10 MW
>
> Hi Alexander, was good meeting you at the conference last week.
>
> Quick background on us. We buy GPU servers…
>
> Worth to do a call this week? I'm also in Reykjavik on 20 to 22 September and could
> come by.

What moved between A and the other two: the em dash left the subject line, "Good to meet
you" became "Was good meeting you" with the subject dropped, and "Would you have time for
a call in the next week or two?" became "Worth to do a call this week?". Those are three
of the specific habits measured in the corpus, reproduced without being named in the task.

What did **not** move much between B and C. Reading the full 1,176-line corpus on top of
`CORE.md` removed one piece of throat-clearing, "Quick background on us", and changed
little else.

**The honest reading, and it changes the skill.** This does not isolate rules from
exemplars, because `CORE.md` has the before-and-after pairs embedded in section 1. What it
shows is that a two-hundred-line guide containing its own exemplars gets most of the
available movement, and that making the skill read the whole corpus every time costs a lot
of context for one deleted phrase.

So `write-external` should point at `CORE.md` and stop there, and the corpus stays a
source document for maintaining `CORE.md` rather than something loaded at drafting time.
The skill as written asks for the corpus too, and that should be softened to optional.

Not proven: whether Roald prefers B or C to A. That needs him to rank them, and it is the
acceptance test that matters. The three drafts are at `/tmp/styletest/`.

## 11. The eleven custom commands are almost never used — CONFIRMED, and it changes the design

Two independent counts across all 2,577 transcripts in `~/.claude/projects`.

**By invocation marker.** Counting `<command-name>` markers, the only slash commands ever
invoked on this machine are `/model` (33 sessions), `/compact` (11), `/nodewatch-review`
(4), `/login` (2), and then one session each for `/implement_plan`, `/run-skill-generator`
and `/cloudflare:cloudflare-one`. `/create_plan` appears zero times. So do `/check_plan`,
`/thoroughly_test`, `/create_PR`, `/push_all_changes_to_git` and the rest.

**By body text**, to guard against the marker being unreliable. Searching for a
distinctive sentence from inside each command file, which can only be present if the file
was actually loaded into a session:

| Command | Transcripts containing its body |
|---|---|
| `create_plan` | 2 |
| `implement_plan` | 3 |
| `create_PR` | 2 |

Out of 2,577. Note that a naive search for a command's *name* returns 887 hits, because
every session loads the skill and command listing. That number means nothing and it is the
trap here.

**What this changes.** Three things.

First, the broken `plan-reviewer` reference matters less than round 1's challenge implied.
The command that calls it has been loaded three times ever. Fixing it is still right — a
dangling reference in a loaded instruction file is a defect — but it is not a
high-frequency failure.

Second, and this is the important one: **the workflow Roald describes wanting is not the
workflow he runs.** He asked for structured briefs turned into plans and executed
phase-by-phase. He has the commands for it, written in his own words, and he has invoked
them perhaps five times in 2,577 sessions. He works by typing free-form instructions.

Third, it settles a design question. Anything opt-in will not be used. The surfaces that
fire without being asked for are `CLAUDE.md`, the output style, hooks, and **skills, which
differ from commands in exactly the way that matters here: a skill can be invoked by the
model when its description matches the task, while a command has to be typed.** That is
why `write-external` is a skill and not a command, and it makes the skill's `description`
field the most load-bearing text in the whole framework.

It also argues against adding an intake skill and an orchestration skill that Roald would
have to remember to invoke. If the plan workflow is to happen at all, it has to be
triggered by the shape of the request rather than by him typing a command.

## 12. SessionStart fires with source "compact", and the global CLAUDE.md is present afterwards — CONFIRMED

Verification 6 could not observe the `compact` source. This run did.

A scratch project with a `SessionStart` and an `InstructionsLoaded` hook that log their
raw payload. Build a session with some content, resume it, run `/compact`, then resume
again and ask a question. The logged sequence:

```
SessionStart      source=startup
InstructionsLoaded  CLAUDE.md   reason=session_start
InstructionsLoaded  CLAUDE.md   reason=session_start
SessionStart      source=resume
SessionStart      source=compact      <-- the one in question
InstructionsLoaded  CLAUDE.md   reason=session_start
SessionStart      source=resume
```

**`SessionStart` with `source=compact` fires.** The re-anchor hook's registration
`matcher: "startup|resume|compact"` is correct as written.

**`~/.claude/CLAUDE.md` is present after compaction.** Asked without tools to quote the
sentence beginning "Brevity that costs", the post-compaction session answered:

> "Brevity that costs comprehension is not brevity."

That is verbatim from the user-global file, and `InstructionsLoaded` fired again for a
`CLAUDE.md` right after the compact event.

**The honest limit on this one.** The session that answered was itself a resume, so this
does not separate "survived compaction" from "reloaded on resume". For the practical
question — is the global file in context after a compaction — the answer is yes either
way. For the narrower question of whether user-scope memory is in Anthropic's re-injection
set alongside project-root `CLAUDE.md`, this is consistent with it but not proof.

Round 1's challenge listed this as an untested assumption. It is now tested, and it holds.

## 13. The repaired hooks work live, against the shipped template — CONFIRMED

Re-run after round 2's fixes, because the earlier live test used a hand-written plan and a
pointer at the old location, and both changed.

Scratch project at `/tmp/fwlive` built from `framework/templates/PLAN.template.md` as
shipped, with an unanswered intake question under "Open questions" above the Steps section,
the pointer at the new tracked path `.docs/plans/ACTIVE`, and a contract with one phase
passing and one failing.

The parent session and a general-purpose subagent spawned through the Agent tool both
reported:

> ACTIVE PLAN: `/private/tmp/fwlive/.docs/plans/demo/PLAN.md`
> CURRENT PHASE: `greeting`
> NEXT UNCHECKED STEP: **1.** Write greeting.txt containing HELLO — *verified by: reading
> the file back*

Three things this confirms at once. The phase came from the first failing contract entry.
The step came from the Steps section and **not** from the intake question above it, which
was round 2's defect 4. And the new pointer location resolves.

The subagent attributed it correctly too: "From the SubagentStart hook in the system
reminders".

## Still to verify

Everything else on the original list has been resolved above.

| # | Question | Why it matters | Cheapest test |
|---|---|---|---|
| 1 | Does Claude Desktop's local agent mode read `~/.claude/CLAUDE.md` and `~/.claude/skills/` | Whether a user-global install reaches Desktop, which is 36 MB of work here | Run a Desktop local agent in a scratch directory and ask it what it loaded |
| 2 | Does Roald prefer the style-guided drafts to the unguided one | This is the acceptance test for problem 1, and nothing else substitutes for it | Rank the three drafts at `/tmp/styletest/` blind |
| 3 | Is a `Stop`-hook completion gate net positive in interactive use | All the evidence for it comes from unattended loops and it may be hostile in conversation | Run it for a day with a block cap |
| 4 | Does the `steering` output style beat the existing `CLAUDE.md` rule on reply length | Problem 2 currently has no mechanism at all | Three days of use, count replies over half a page |
| 5 | Is the skill listing budget a real constraint here | Determines how many skills the framework can add | `/context` in an Opus 5 session, read the skills line |
| 6 | Does `.conductor/conductor.json` support anything beyond a setup script | Another propagation point if it does | Read the Conductor settings schema |
| 7 | What would make Roald actually use a plan workflow | Finding 11 shows the commands he wrote are not used, and nothing in the framework fixes that | Ask him |

## Caveat that applies to every result above

Every headless probe here used `--model claude-haiku-4-5-20251001` for cost, while the
machine runs Opus 5 on a 1M window. What that model choice can and cannot affect:

**Not affected.** Whether a hook fires, what fields its payload carries, whether
`additionalContext` reaches the agent, whether a `PreToolUse` deny blocks a call, whether
`permissions.deny` holds under bypass permissions, and which instruction files load. These
are harness behaviour and the model is downstream of them.

**Possibly affected.** How an agent responds to a denial. Haiku accepted the block and
reported it. A stronger model might work around it more inventively, and the gate is a
speed bump rather than a boundary in any case.

**Definitely affected.** The style experiment in finding 10 used `opus`, deliberately,
because the output is the thing being judged.
