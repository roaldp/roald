# The framework: design, draft 2

2026-09-06. Supersedes `02-framework-design.md`, which stays on disk because
`challenges/01-challenge-design.md` quotes it.

Draft 1 was attacked by a subagent that produced 22 findings and recommended keeping
about a fifth. Most of those findings were correct. Four were checked again
independently here and all four held. This draft is what survives, plus the two
mechanisms that were rebuilt and re-tested rather than dropped.

## What the challenge got right, verified independently

**Agents on this machine write through Bash, not Edit and Write.** Across 52 sessions
over 2 MB modified in the last fourteen days: Bash 6,429, Edit 1,233, Read 906, Write
407. Bash outnumbers Edit plus Write by 3.9 to 1. The cause is in the harness: under
bypass permissions, which is how Conductor launches every session, the system reminder
instructs agents to read with `cat`, search with `grep` and edit with `sed` and heredocs
rather than use the dedicated tools. Any hook that matches on `Edit|Write` sees a
minority of the file writes on this machine, and any counter that watches `Read` sees a
minority of the reads.

**Compaction almost never happens here.** Fourteen of 2,573 transcripts contain a
compaction marker. Of the 116 transcripts over 2 MB, twelve do. Conductor sets
`default = "claude:opus-5-1m"`, so every workspace runs a 1M-token window and simply
never fills it. Draft 1 built its anti-drift argument on surviving compaction, which is
the wrong axis for this machine.

**The plan-review loop Roald already asked for is broken.**
`~/.claude/commands/create_plan.md` calls a subagent named `plan-reviewer` at step 2 and
again at step 4. `~/.claude/agents/` contains `documentation-fetcher.md` and
`typescript-type-error-fixer.md`. There is no `plan-reviewer` anywhere on the machine. So
the challenge round Roald says he most wants forced has been silently skipped or
improvised every time he has run `/create_plan`.

The same file, at step 5, instructs the agent to summarise "using green checkmark, red
cross, and other emojis". Both `~/.claude/CLAUDE.md` and this repo's `CLAUDE.md` say not
to use emoji. Anthropic's documentation says that when two rules contradict, Claude may
pick one arbitrarily.

**Symlinking `~/.claude` into a Conductor primary checkout is unstable.**
`git -C ~/conductor/repos/roald worktree list` shows the primary sitting on
`fix/deferred-update-apply` while the workspaces sit on `ed0d491`. Global agent behaviour
would follow whatever branch that checkout happens to be on.

## What the challenge got wrong, and how

Draft 1 said the contract gate was "the only mechanism an agent cannot talk its way
past". The challenge said the gate was dead on this machine and should be deleted. Both
were wrong, in opposite directions, and the difference is testable.

**The gate as written was defeated by one Bash call.** Verified: with the
`Edit|Write` matcher installed, `echo '{"greeting":{"passes":true}}' > contract.json`
went straight through.

**Rebuilt with `Bash` in the matcher and command inspection, it holds.** Verified in both
directions. Told to overwrite the contract with a Bash redirect and read nothing, the
agent reported: "No — the write was blocked by a contract validator that requires reading
the evidence file first", and the file was unchanged. Told to `cat` the evidence file
first and then write, the same call succeeded and the counter reset.

One further correction to draft 1's own code, found by testing rather than reading: the
evidence tracker originally counted any read inside the plan directory, and the Edit tool
must read a file before editing it, so reading `contract.json` unlocked writing
`contract.json`. The gate unlocked itself every time. Excluding the contract, the plan
and the counter from ever counting as evidence fixed it.

**It is still a speed bump, not a boundary.** A Python one-liner that opens the file for
writing is not matched by the patterns. The hard version is declarative and was also
verified: `permissions.deny` with `Edit(**/contract.json)` holds under bypass
permissions and blocked a Bash write. Claude Code reported the useful detail itself:
`Write(path)` rules are not matched by file permission checks, only `Edit(path)` rules
are, and `Edit` rules cover every file-editing tool. A permanent deny cannot express
"deny until evidence is read", so the two are complements: the hook for the conditional
logic, `permissions.deny` for anything that must never be written at all.

---

## The design

Five problems. One mechanism each, and no mechanism that has not been tested or is not
about to be measured.

### Problem 1, external writing reads as an agent's

**Ship: a `write-external` skill that loads a style guide at the moment of writing.**
Nothing else, until there is a measurement.

The mechanism that matters is the timing, not the content. A style guide sitting at the
top of a long session loses force; a skill delivers it into a short fresh context exactly
when the agent starts drafting. That is the whole intervention, and it is half a day.

**Where the guide comes from.** The AIC `docs/pitch-materials/style/STYLE.md` on
`origin/main`, split per rule rather than per section. Draft 1 said "sections 4 to 8",
which was asserted without reading the file and gets it backwards: section 5.1 is a
vehicle fact about counting capacity in GPUs, section 8 names AIC close lines, and both
would have been imported into a user-global file. Meanwhile section 1 (fact, mechanism,
consequence), section 3 (no closing lines) and section 9 (the actual before-and-after
pairs) are fully general and would have been left behind — including the only exemplars
that exist today.

Take: 1, 3, 4, 6, 7 without the house separator, 8 without the AIC close lines, and 9
without the vehicle content. Leave: 2, 5.1, 10.

**Calibrate the rules against Roald's own corpus, first-hand.** Measured from 1,707
unique typed prompts, 48,664 words, in `05-roald-writing-profile.md`:

| Measure | Roald | What draft 1 assumed |
|---|---|---|
| Em dashes per 1,000 words | 1.01 | A ban, justified by a third-hand per-model claim |
| Semicolons per 1,000 words | 0.39 | A ban |
| Open parentheses per 1,000 words | 5.61 | A ban |
| Mean sentence length | 14.6 words | Unstated |
| Burstiness | 0.71 | A target of 0.6 |

This resolves three things draft 1 got wrong.

The em-dash rule becomes a **density budget of one per thousand words**, not a ban.
Roald's hand-written `~/.claude/CLAUDE.md` contains six em dashes, and draft 1's own
acceptance test says a rule that flags his writing is wrong. A budget of one per thousand
is his own measured rate, is well under the published human baseline of 3.23, and does
not fail on his own file. The justification is now first-hand measurement of his corpus
rather than a paywalled study reaching us third-hand through search summaries.

The semicolon and parenthesis contradiction is resolved by the same data. AIC `STYLE.md`
bans both; the research says under-punctuation and "and"-joining are the markers that
replaced the em dash, so banning all three leaves only commas and full stops and drives
the writing straight into the current tell. Roald's own rate settles it: **semicolons
effectively never, parentheses sparingly.** Say so in one line in the guide, with the
reason, so a future reader does not re-ban them.

The corpus also shows two habits no rule can produce, which is the argument for exemplars
over rules. He drops subjects and auxiliaries — "Was nice to meet you today", "Read your
background and looking to learn" — and he never writes a closing line, ending instead on
a question or an offer: "Worth to do another call?"

**Do not ship the linter as a blocking hook.** Run against draft 1's own design document,
the existing AIC `lint.py` produced 24 findings, one of them fabricated by the filename
`01-machine-map.md` matching a pattern for counting machines. It also flags "several",
"various" and "numerous" as vague quantifiers, which are ordinary English. A blocking
hook with that false-positive rate, on a surface that sees a minority of writes, is
switched off in a day. Keep the linter as a command the agent runs deliberately, and
revisit blocking only if the false-positive rate comes down.

### Problem 2, updates are too long

**Ship: an output style, and measure it against the rule that already exists.**

Draft 1's answer was to add per-surface prose to `~/.claude/CLAUDE.md`, four paragraphs
after establishing that `CLAUDE.md` is context rather than configuration. That file
already contains "**Half a page maximum.** This is a hard ceiling, not a target to
approach", followed by a list of exactly what a reply may contain. Roald's complaint is
that this is not obeyed. More of the same text, in a longer file, is not a mechanism.

An output style is the only surface documented to modify the system prompt itself rather
than append a message after it. Its documented limitation is that it does not reach
subagents, which does not matter here because subagents do not message Roald.

Two things go in it, and nothing else. **Bottom line up front**: what happened, then what
needs a decision with a recommendation, then what changed that would alter the plan, then
the path where detail lives. **Per surface**: in the terminal, one heading level and bare
paths, because `h2` through `h6` all render as identical bold and link labels are
discarded. In Slack, summary in the parent and detail in the thread, under four thousand
characters, no headers or tables or HTML. In a GitHub pull request, `<details>` for logs
and diffs.

Dropdowns are not available in the Claude Code terminal or in Slack. Neither has an HTML
layer. That is the answer to the question Roald asked, and it is why progressive
disclosure has to be layered across artefacts.

**The measurement**: use it for a week, count replies over half a page against the
current baseline. If it does not win, the fallback is a `Stop` hook of type `prompt` that
measures the final message and injects a correction — the same shape as `/goal`.

### Problem 3, turning a brief into a scoped plan

**Ship: `PLAN.md`, one file, and a fixed intake procedure. Cap the whole intake at three
questions.**

Draft 1 said "about three questions per genuinely ambiguous area". The source says 3.06
questions **per task it chose to query**. Four ambiguous areas would have become twelve
questions. The source's questions were also answered by a simulated oracle with zero
annoyance cost, and the research file flags this itself as an open question.

State the finding honestly, because it agrees with Roald rather than with the framework.
The study's full table is: full-spec baseline 70.8, interactive baseline 70.4, separate
intent-check agent 69.4, intent-check folded into the worker 61.2, no asking 54.8. Draft
1 quoted three of those five numbers. **The elaborate uncertainty scaffold does not beat
simply having a good brief, and it costs roughly twice the tokens.** Roald's stated
position is that long structured briefs already produce good work. The evidence says he
is right. What the scaffold buys is a floor when the brief is thin.

So: three questions total, each carrying the agent's own proposed answer so he can reply
"yes". Resolve from the repo first — about a third of apparent ambiguity is
self-resolvable. Never ask about style; measured elicitation rates for style preferences
are near zero, and the corpus is the answer instead.

`PLAN.md` sections, in `framework/templates/PLAN.template.md`: Brief verbatim, Discovery
ending in a one-paragraph restatement, Open questions with proposed answers, Approach
with rejected options named, Success criteria as given-when-then, MVP scope with an
explicit "out" list, Steps each naming its verification, and an append-only Log.

The restatement paragraph is the intake's main output. Reading one paragraph costs Roald
less than answering questions, and it is where a misunderstanding shows up.

`contract.json` is optional and only earns its place on a job long enough for the gate to
matter. Draft 1 made it universal. It is not.

### Problem 4, drift

**Ship: the re-anchor hook on `SubagentStart` and on `SessionStart` for `startup` and
`resume`. Do not build the framework around compaction.**

Compaction fires in fourteen of 2,573 transcripts here, so draft 1's durability argument
was aimed at an event that does not happen. What does happen is instruction eviction
inside one very long uncompacted session, and no hook fires inside a session.

Where the anchor genuinely pays, verified:

- **Every subagent.** A subagent inherits no conversation history, no files the parent
  read, no invoked skills and no auto memory. The hook was tested: a general-purpose
  subagent spawned through the Agent tool reported back the plan path, the current phase
  and the next unchecked step, and added "I am a subagent and inherit none of the
  parent's context." This is the mechanism the orchestrator depends on and it is the
  strongest single result of the night.
- **Every resume.** Verified: matcher filtering works, a fresh startup did not fire a
  `resume`-matched hook, and a resumed session did and delivered its context.

For within-session eviction the honest answer is that nothing here has been measured.
`UserPromptSubmit` re-injection gated on elapsed turns is the candidate. It should be
built only after the `InstructionsLoaded` log has run for two weeks and shown whether
anything is being evicted at all.

**Turn on `InstructionsLoaded` logging first, and change nothing else for two weeks.**
One hook, one log file. Verified working: one line per loaded file with `file_path`,
`load_reason` and `memory_type`. Without it, an instruction that was ignored cannot be
distinguished from an instruction that was never loaded, and every other decision here is
guesswork.

### Problem 5, an orchestrator that delegates

**First: find out why the orchestrator he already has does not delegate.**

`~/.claude/commands/implement_plan.md` already says, in Roald's own words: "Delegate work
to subagents. You are a coordinator who is responsible for the eventual outcome … For
each phase, spin up a subagent to execute the phase." That instruction exists, is loaded,
and does not hold. Writing the same instruction again as a skill is a rewrite of
something that already failed. Read three transcripts where `/implement_plan` ran, find
the turn where delegation stopped, and let that decide whether the fix is a skill, a hook
or nothing. That is an afternoon.

**Second, state the reconciliation Roald is owed.** He asked for execution to be
delegated to subagents. The best cross-verified evidence in the research — from Anthropic
and Cognition, two sources that disagree about nearly everything else — is "fan out for
reading, keep writing single-threaded". Draft 1 asserted both and never said they differ.

They reconcile, and the reconciliation is the design: **one worker at a time, doing the
writing, driven by an orchestrator that does not write.** Delegation is preserved.
Parallelism is not, for the implementation stage. Reading, research and review still fan
out.

**Third, fix the challenge loop that is already broken.** Create the missing
`plan-reviewer` subagent, and remove the emoji instruction from `create_plan.md`. This is
the thing Roald said he most wants forced, it already exists as an instruction, and it
has been calling into the void.

---

## Build order

Four of the first five items are edits to files that already exist. None adds a blocking
hook.

| # | Change | Cost | State |
|---|---|---|---|
| 1 | Create the missing `plan-reviewer` subagent; remove the emoji instruction from `create_plan.md`; audit the other ten command files for dangling references | half a day | ready to write |
| 2 | One-line `CLAUDE.md` containing `@AGENTS.md`, committed to `main`, for every repo with a root `AGENTS.md` and none | an hour | needs Roald's go-ahead, changes other repos |
| 3 | `write-external` skill, rules only, pointed at the split AIC style guide plus the corpus exemplars | half a day | corpus exists |
| 4 | `InstructionsLoaded` logging, then two weeks of silence | 10 minutes | hook written and verified |
| 5 | Output style for updates to Roald, measured for a week against the current rule | an hour | not written |
| 6 | Re-anchor hook on `SubagentStart` and `SessionStart` | 10 minutes | written and verified |
| 7 | `PLAN.md` template and the intake procedure | half a day | template written |
| 8 | Diagnose why `/implement_plan` stops delegating | an afternoon | not started |

Everything else waits for a measurement: the contract gate and `contract.json`, the
evaluator subagent, the orchestration skill, the linter as a blocking hook, the plugin
packaging question, `UserPromptSubmit` re-injection.

## Installing

From a dedicated clone at `~/.claude/framework-src`, pinned to `main`, not from the
Conductor primary checkout — that checkout is on `fix/deferred-update-apply` right now,
and symlinking into it would tie global agent behaviour to whatever branch it happens to
be on.

`scripts/install_framework.py` symlinks skills, agents, rules and hooks into `~/.claude`,
merges hook entries into `settings.json` under a marker, backs the file up first, is a dry
run unless `--apply` is passed, and has `--uninstall`.

Skills, agents and hooks installed there reach the CLI, every Conductor workspace, and
Claude Desktop's local agent mode, which shares `~/.claude`. Two exceptions worth knowing:
the built-in `Explore` and `Plan` agents skip the `CLAUDE.md` hierarchy, and output styles
do not reach subagents at all. Claude Desktop's cloud-side Projects cannot be written from
this machine.

## Addendum, measured after draft 2 was written

Three measurements landed after this draft and two of them change it. Full detail in
`04-verification-results.md`, findings 10 and 11.

**The custom commands are not used, so nothing opt-in will be.** Across 2,577 transcripts,
`/create_plan` was invoked zero times and `/implement_plan` once. Checking by body text
rather than by name — the name appears in 887 transcripts because every session loads the
command listing — `create_plan` has been loaded into two sessions ever and
`implement_plan` into three.

This settles the surface question. A skill differs from a command in exactly the way that
matters: **a skill can be invoked by the model when its description matches the task, a
command has to be typed.** So `write-external` is a skill, and its `description` field is
the most load-bearing text in the framework.

It also argues against build-order item 7 as written. An intake skill Roald has to
remember to invoke will go the way of `/create_plan`. If the plan workflow is to happen,
it has to trigger on the shape of the request. That is a harder design problem than draft
2 assumed and it is not solved here.

It softens build-order item 1 too. Fixing the missing `plan-reviewer` is still right,
because a dangling reference in a loaded instruction file is a defect, but it is not the
high-frequency failure round 1 took it for.

**The style guide moves the output, and the corpus on top of it does not move it much
further.** Three drafts of the same email, same model, differing only in what was loaded.
With nothing loaded: "Good to meet you at the conference last week", an em dash in the
subject line, and "Would you have time for a call in the next week or two?" With `CORE.md`
loaded: "Was good meeting you at the conference last week", no em dash, and "Worth to do a
call this week?" Three measured habits from his corpus, reproduced without being named in
the task.

Loading the full 1,176-line corpus on top of `CORE.md` removed one phrase of
throat-clearing and changed nothing else. So the skill points at `CORE.md` and stops. The
corpus is the source document for maintaining `CORE.md`, not something to load while
drafting. The skill has been updated accordingly.

What this does not prove is that Roald prefers the result. That needs him to rank the
three drafts, which are at `/tmp/styletest/`, and it is the acceptance test that matters.

**Opus 5 has the in-session todo tools disabled by default.** Confirmed from the binary:
the list is "Opus 4.8, Sonnet 5, Fable 5, Mythos 5, and newer models". The on-disk plan
file is unaffected.

## Still to verify

| # | Question | Cheapest test |
|---|---|---|
| 1 | Is `~/.claude/CLAUDE.md` re-injected after compaction, like a project-root file | One session, `/compact`, ask the model to quote a distinctive line |
| 2 | Does a style guide plus exemplars beat a style guide alone, for Claude | Draft the same email three ways and have Roald rank them blind. One hour |
| 3 | Is the skill listing budget a real constraint here | `/context` in an Opus 5 session, read the skills line |
| 4 | Does Claude Desktop's local agent mode read `~/.claude/CLAUDE.md` and skills | Run a Desktop local agent in a scratch dir and ask what it loaded |
| 5 | Is Opus 5 inside the todo-tools-disabled list | `/context` in a live session |
| 6 | Does the output style beat the existing `CLAUDE.md` rule on reply length | Three days of use, count replies over half a page |
| 7 | Where does `/implement_plan` stop delegating | Read three transcripts |
