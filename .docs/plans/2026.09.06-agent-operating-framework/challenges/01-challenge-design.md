# Challenge round 1: attack on 02-framework-design.md

Adversarial review, 2026-09-06. Target: `02-framework-design.md` draft 1. Everything below was
checked against `research/`, against the machine, or both. Commands used are named where a claim
rests on them so they can be re-run.

## Verdict

Send it back, keep about a fifth of it. Two of the five problems in the brief are addressed by
mechanisms that would plausibly change the outcome: the missing `CLAUDE.md` shim for `AGENTS.md`,
and a write-time style skill. The rest is a twenty-artefact harness whose three enforcement
mechanisms are all defeated by how this machine actually runs. The style linter and the contract
write-gate both key on `Edit` and `Write`, and 83 per cent of tool calls in recent large sessions
on this machine are `Bash` (3,051 Bash against 626 Edit plus Write across 25 sessions over two
weeks); Claude Code's own bypass-permissions system reminder actively instructs agents to write
files with heredocs and `sed` instead of `Edit` or `Write`, and to read them with `cat` instead of
`Read`. That single fact disables the linter hook, disables the contract gate, and starves the
evidence counter the gate depends on. Separately the design's answer to problem 2 is to write more
prose into the file whose failure is the problem, four paragraphs after it explains that this file
is context rather than configuration. The anti-drift section is built on compaction survival, and
compaction fires in 12 of 114 sessions over 2 MB on this machine because every workspace runs a
1M-token window. The writing section rests on an exemplar corpus that does not exist yet, and its
headline rule flags Roald's own hand-written `~/.claude/CLAUDE.md` six times under the very
criterion the design proposes for deciding a rule is wrong.

## Kill list

**`style_lint.py` and the `PostToolUse` lint hook.** Delete both. Run against the design document
itself, the existing AIC `lint.py` produces 24 findings, including a fabricated GPU unit-of-account
violation triggered by the filename `01-machine-map.md` matching `\b\d[\d,]*[-\s]*machines?\b`.
It also fires on `several`, `various`, `numerous` and `highly \w+` as vague quantifiers, which are
ordinary English. A blocking hook with that false-positive rate, firing on a surface that carries a
minority of this machine's file writes, is switched off in a day. The design says so itself and
then ships it anyway.

**The `PreToolUse` write gate on `contract.json`, in its current form.** Two independent kills.
First, `Bash: echo '{...}' > contract.json` is not matched by a hook whose matcher is a tool name,
and the harness tells the agent to prefer exactly that. Second, the evidence counter increments on
`PostToolUse` for `Read`, and the same harness instruction tells the agent to read with `cat`. On
this machine the counter would stay at zero, the gate would deny every write, and the run would
deadlock. It is not an unbypassable check. It is a check that is simultaneously trivially bypassed
and prone to locking up.

**`CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=2`.** The only evidence for it is OrchestraBench, which the
design itself rates MODERATE and describes as a single Claude agent over arithmetic chains. The cost
is real and asymmetric: it silently withholds the `Agent` tool at the limit, and it would break the
design's own Part 5, where an orchestrator spawns a worker that spawns a challenger. Roald's stated
method for this very project — challenge with a subagent at least twice — runs at that depth.

**"Two files per job" as a universal.** `contract.json` earns nothing once the gate that reads it is
gone. Keep `PLAN.md`.

**The claim that `CORE.md` is "sections 4 to 8" of AIC `STYLE.md`.** Not a kill of the split, a kill
of that boundary. See finding 5.

## Findings

### 1. The two enforcement mechanisms are defeated by the harness this machine runs. SEVERE

The claim: *"A `PostToolUse` hook on `Edit|Write`. Runs the linter on files that are actually
outbound copy and returns `decision: "block"`"* and *"This is the only mechanism in the corpus an
agent cannot talk its way past."*

What is wrong: both hooks match on tool name. Conductor launches every session with bypass
permissions, which the design correctly establishes. What it did not check is what bypass
permissions does to tool selection. The system reminder injected into a bypass-permissions session
reads, verbatim: "Do your work through the Bash tool wherever it can accomplish the job: read files
with cat, head, or sed -n, search with grep and find, and make file changes with sed, heredocs, or
short scripts, rather than using the dedicated Read, Edit, or Write tools." The measured consequence
is in the transcripts. Across 25 sessions over 2 MB modified in the last fourteen days, the tool
histogram is Bash 3,051, Read 464, Edit 459, Write 167. The busiest single session on the machine,
`ai-infrastructure-capital/stuttgart` at 104 MB, contains 131 Bash calls, 96 Read calls and 3 Write
calls, and it produced files.

So the linter sees a minority of writes, and the contract gate sees none of the ones that matter.
Worse, the gate's precondition is a `PostToolUse` counter on `Read`, and the same instruction routes
reads to `cat`. The gate would therefore deny writes it should allow, forever.

What would have to be true for the design to be right: that agents on this machine write files with
`Edit` and `Write`. They do not, and the harness tells them not to.

Instead: if you want file-level enforcement here, the matcher has to include `Bash` with argument
inspection for redirection and `sed -i` against the protected path, and the evidence counter has to
count `Bash` reads too. That is a materially harder script than the design budgets ("a script"), and
it should be built and measured before anything depends on it. Cheaper alternative: drop enforcement
and use `permissions.deny` on the contract path, which is declarative and tool-agnostic.

### 2. Problem 2 gets no mechanism at all. SEVERE

The claim: build order item 4, *"Update-format rules per surface, into `~/.claude/CLAUDE.md` —
Second complaint, and it is short — An hour"*, preceded by the admission *"Roald's
`~/.claude/CLAUDE.md` already says most of this. What it lacks is the per-surface specifics and any
enforcement."*

What is wrong: the design opens by establishing that `CLAUDE.md` is context rather than enforced
configuration, and that "most of what follows is moving specific rules one rung up, from instruction
to mechanism." It then answers problem 2 by adding instructions to `CLAUDE.md`. The current file
already contains a hard rule — "**Half a page maximum.** This is a hard ceiling, not a target to
approach" — with a bulleted list of exactly what a reply may contain. Roald's complaint is that this
is not being obeyed. The proposed fix is more of the text that is not being obeyed, plus per-surface
variants, which lengthens the file and, on the design's own cited guidance, reduces adherence.

What would have to be true: that the existing rule fails because it lacks surface-specific detail
rather than because it is a request. Nothing in the research supports that reading, and the
persona-drift material in `research/02` argues the opposite — a rule stated once at session start
loses force over a long session regardless of how precise it is.

Instead: the design never considers the one surface documented in `research/03-claude-code-config-surfaces.md`
that modifies the system prompt rather than appending a message after it. An output style is the
correct home for "how you talk to Roald". Its documented limitation is that it does not reach
subagents, which is fine, because subagents do not message Roald. Second option, cheaper still: a
`Stop` hook of type `prompt` that measures the final assistant message and injects a correction when
it exceeds the budget — the same shape as `/goal`, which the research names as the only built-in
generator-evaluator loop. Neither is evaluated anywhere in the design.

### 3. The anti-drift design is built around an event that fires in roughly a tenth of long sessions. SEVERE

The claim: *"The durable re-injection point is a `SessionStart` hook with `matcher: "compact"`,
which Anthropic documents as re-run after compaction"* and the framing of drift as three modes of
which *"compaction loss"* gets the mechanism.

What is wrong: the compaction analysis is correct and largely irrelevant here. Counting compaction
markers across `~/.claude/projects`, 13 of 2,565 transcript files contain one. Restricting to
sessions over 2 MB, 12 of 114. The 104 MB `stuttgart` session contains the string "compact" zero
times. This is what a 1M-token window buys: `~/.conductor/settings.toml` sets
`default = "claude:opus-5-1m"`, so every workspace already runs at 1M, and per `research/03`
Opus 5 compacts at its context limit unless `autoCompactWindow` is set.

Meanwhile the mode that does fire — instruction eviction, or context rot within one very long
uncompacted session — gets no mechanism. `SessionStart` runs at startup, resume and compaction. None
of those is a point inside a 104 MB session. The design rejects `UserPromptSubmit` re-injection on
durability grounds, but durability across compaction is the wrong axis when compaction does not
happen; within-session recency is the axis that matters, and `UserPromptSubmit` is the mechanism
that addresses it.

What would have to be true: that Roald's sessions compact often. They do not.

Instead: re-anchor with `UserPromptSubmit` gated on elapsed turns or context size, and keep
`SessionStart` for `resume` and `startup` only. Or, before building either, set `autoCompactWindow`
deliberately and find out whether a shorter window with a good `PreCompact` summary is better than a
1M window that never compacts.

### 4. The intake question budget is an agent-to-agent simulation number applied to a time-poor human. SEVERE

The claim: *"Budget about three questions per genuinely ambiguous area, and attach the agent's own
proposed answer to each ... That is the concession to his context-switching cost."*

What is wrong on three counts. The source, Ask or Assume?, reports 3.06 questions **per task it
chose to query**, not per ambiguous area. A plan with four ambiguous areas becomes twelve questions
under the design's phrasing, which is four times the source figure. `research/02` propagates the
same slip in its rule 26; the design repeats it without checking.

Second, the questions in that study were answered by a simulated oracle with zero annoyance cost.
`research/02` flags this itself as open question 7: "Is there a measurable annoyance ceiling for
intake questions with a human in the loop? The 3.06-questions figure comes from an agent-agent
simulation, not from human subjects." The design lifts the number, drops the caveat, and then calls
it a concession to Roald's context-switching cost. It is the opposite: it is the number that a
system with no context-switching cost converged on.

Third, the design picks the convenient side of its own table. It reports 69.4, 61.2 and 54.8 and
omits that the interactive baseline scored 70.4 and the full-spec baseline 70.8. The honest reading
is that the elaborate uncertainty scaffold does not beat simply having a decent brief, at roughly
twice the token cost ($3.50 against $1.63). Roald's stated position is that long structured briefs
already produce good work. The study agrees with him and the design does not say so.

Instead: state the finding as it is. A separate intent-check pass beats folding the check into the
worker, and neither beats a good brief. Cap the whole intake at three questions total, all with
proposed answers, and measure whether Roald answers them.

### 5. The style-guide split boundary is wrong, and was asserted without reading the file. SEVERE

The claim: *"`style/CORE.md` ... comes from sections 4 to 8 of the existing `STYLE.md` — sentences,
numbers, emphasis, punctuation, banned constructions"* and *"AIC claims and vehicle facts never
leave it."*

What is wrong, checked against `git show origin/main:docs/pitch-materials/style/STYLE.md`:

- Section 5 contains subsection 5.1, "Capacity is counted in GPUs. Always", which is a vehicle fact
  about AIC's unit of account. The design's chosen range imports it into a user-global file.
- Section 8 contains AIC close lines by name: "Happy to walk you through the offtake deal terms",
  "Roald will take you through the numbers." Also vehicle-specific.
- Section 1, "three beats per claim: fact then mechanism then consequence", is fully general and is
  the same rule as `~/.claude/CLAUDE.md`'s "if A caused B which caused C, write all three steps". The
  design excludes it.
- Section 3, "Do not write closing lines", is general and matches the design's own rule "No closing
  summary paragraph in short-form writing". Excluded.
- Section 9, "Before and after", holds the real before-and-after pairs. The design's own thesis is
  that exemplars are the primary mechanism and rules are the backstop. It excludes the only
  exemplars that exist today.

So the split as specified keeps the AIC-specific parts and discards the general ones, which is the
exact inversion of its stated intent.

Instead: the boundary is not sectional. It is per rule. Include sections 1, 3, 4, 6, 7 minus the
house separator, 8 minus the close lines, and 9 minus the AIC content. Exclude 2, 5.1, 10.

### 6. The rule set drives writing toward the marker the research names as the current tell. SEVERE

The claim: `CORE.md` is *"sections 4 to 8 of the existing `STYLE.md` ... plus the general rules in
`research/02-writing-style-and-briefing.md`."*

What is wrong: those two sources contradict each other on punctuation and the design merges them
without noticing. AIC section 7 says "No semicolons in body copy. Split the sentence" and "No
parentheses for asides." Research rule 5 says "Use commas, semicolons and parentheses; do not run
two ideas into one long unpunctuated sentence joined by 'and'", and it is sourced to the Economist
study's finding that under-punctuation and "and" over-use are the markers that **replaced** the em
dash. Add the em-dash ban on top and the writer is left with commas and full stops. That is a
recipe for the long, undifferentiated, "and"-joined sentence the same study names as the 2026 tell.

The design's own documentation of Anthropic guidance says Claude may pick one arbitrarily when two
rules contradict. It applies that observation to other people's repos and not to the file it is
about to write.

Instead: resolve the conflict explicitly in `CORE.md`. Ban the em dash inside a sentence, permit the
semicolon and the parenthesis, and say why in one line so a future reader does not re-ban them.

### 7. The em-dash rule fails the design's own acceptance test on Roald's own writing. SEVERE

The claim: *"No em dashes inside a sentence"*, listed first because it is *"In order of how often
they will fire"*, alongside the feedback rule *"require that Roald's own text scores zero on the
linter. If a new rule flags his own writing, the rule is wrong."*

What is wrong: run the existing linter against `~/.claude/CLAUDE.md`, which Roald wrote by hand.
Seven findings, six of them em dashes in prose, one thin bold density. Against the design document
itself: 16 em dashes in 4,977 words, a rate of 3.21 per thousand, which is indistinguishable from
the 3.23 human baseline the research quotes. Against `research/02-writing-style-and-briefing.md`:
46 in 6,096 words, 7.55 per thousand, more than double the human baseline.

Two separate problems. The rule as written is a ban, and Roald's own writing violates it, so by the
design's own stated criterion the rule is wrong and should be a density budget rather than a ban.
And the two documents that define the house style are themselves the worst offenders in the
repository, in a design that says "an exemplar must contain nothing we do not want copied" and "the
style guide must itself obey its own rules."

Also note the evidence chain. `research/02` states plainly that the Economist study is paywalled,
that both secondary reports returned HTTP 403, and that its figures "reach us third-hand via search
summaries". The design presents the per-model result as settled fact — "Claude was the one model of
four still above it" — and makes it the load-bearing justification for the highest-frequency rule in
the system. Third-hand, single-study, per-model breakdown, not verified.

Instead: express it as a density budget calibrated against Roald's own corpus, which the design
already lists as verification item 7 and then does not wait for.

### 8. Part 1 depends on an artefact that does not exist. SEVERE

The claim: *"Exemplars are the mechanism, rules are the backstop ... Those are being collected into
`research/05-roald-writing-corpus.md`"*, and build order item 3, *"`CORE.md` plus the
`write-external` skill and exemplars — Extraction, not invention."*

What is wrong: `ls` on the plan directory shows four files under `research/`. There is no
`05-roald-writing-corpus.md`. `00-STATE.md` still lists step 6 as "running (subagent)". The design
therefore asserts that exemplars are the primary mechanism, has never seen a single exemplar, and
costs the work as extraction. The one empirical contact with Roald's actual prose available today is
the linter run in finding 7, and it disconfirms the rule set.

Instead: block Part 1 on the corpus. If the corpus does not arrive, Part 1 reduces to "point the
`write-external` skill at the existing AIC `STYLE.md` sections 1, 3, 4, 6 to 9", which is a
half-hour of work and captures most of the value.

### 9. Problem 5 is quietly reframed into a different problem. SEVERE

The brief: *"Wanted: an orchestrator that holds the plan and delegates execution to subagents rather
than doing the work itself."*

The design: *"Fan out for reading. Keep writing single-threaded ... So: research, codebase
exploration and review fan out. Implementation does not."*

What is wrong: those are not the same thing, and the design never tells Roald they differ. He asked
for execution to be delegated. The design's best cross-verified evidence says implementation should
not fan out. Both can be satisfied — one worker at a time, writing, driven by an orchestrator that
does not write — but the design never states that reconciliation, so a reader takes away either
"my request was granted" or "my request was refused" depending on which paragraph they read last.

Worse, the design does not diagnose the existing failure. `~/.claude/commands/implement_plan.md`
already says, in Roald's own words: "Delegate work to subagents. You are a coordinator who is
responsible for the eventual outcome ... For each phase, spin up a subagent to execute the phase."
That instruction exists, is loaded, and drifts. Part 5 proposes to restate it as a skill without
asking why the current statement fails. Anything built here that does not answer that question is a
rewrite of a thing that already did not work.

Instead: before writing an orchestration skill, read three transcripts where `/implement_plan` was
used and find the turn where delegation stopped. That is an afternoon and it determines whether the
fix is a skill, a hook, or nothing.

### 10. The existing `/create_plan` challenge loop is broken, and the design did not find it. SEVERE for the audit, MODERATE for the design

`~/.claude/commands/create_plan.md` step 2 reads: "Use the subagent plan-reviewer to review the
plan", and step 4 repeats it. `grep -rl plan-reviewer ~/.claude/` returns the command file itself and
one subagent transcript. `~/.claude/agents/` contains `documentation-fetcher.md` and
`typescript-type-error-fixer.md`. There is no `plan-reviewer` agent anywhere on the machine.

So Roald's plan-review loop, the thing he asked to be forced ("challenge the work with a subagent at
least twice"), has been silently no-op or improvised for as long as that file has existed. The design
proposes the same capability in Part 5 as new work and never notices the broken instance. A framework
whose job is to make sure instructions actually take effect failed to detect a dangling reference in
the eleven-file command directory it inventoried.

While there: the same file instructs the agent to summarise "using green checkmark, red cross, and
other emojis", which contradicts both `~/.claude/CLAUDE.md`'s standing instruction and the project
`CLAUDE.md`'s "do not use emoji's". The design's Part 6 makes "each rule has one home, duplication is
not harmless" a principle and cites the AIC `AGENTS.md` as the example. It missed the contradiction
sitting in the user-global command directory.

Instead: audit `~/.claude/commands/` before writing anything new. Fixing `plan-reviewer` is one file
and delivers the challenge round the design schedules for later.

### 11. The `reanchor.sh` hook as specified cannot work where the design installs it. SEVERE

The claim: the JSON block specifying
`"command": "$CLAUDE_PROJECT_DIR/.claude/hooks/reanchor.sh"`, against Part 6's
*"This is where the framework lives: `CLAUDE.md` ... `hooks/` for the anchor, the gate and the
linter, `settings.json` to wire them up"* in `~/.claude/`.

What is wrong: `${CLAUDE_PROJECT_DIR}` resolves to the project the session is running in, not to the
framework repo. Installed user-globally, that hook points at `.claude/hooks/reanchor.sh` inside
whichever of the fifty-nine directories the session started in, and almost none of them have one.
Per `research/04-hooks-reference.md`, a hook that fails surfaces as a visible `<hook name> hook
error`. So the first effect of installing the framework is an error banner at the start of every
session in every repo, plus every subagent start, plus every one of the pulse companion's sessions.
`~/roald` alone has 1,698 sessions in the inventory, one every thirty minutes.

Instead: use an absolute path to the installed location, or `$HOME/.claude/hooks/reanchor.sh`. Then
test it in one repo for a week before it goes user-global. This is a small bug, but it is the one
that determines whether the whole framework survives its first morning.

### 12. The single-repo install story does not survive Conductor. MODERATE

The claim: *"A `scripts/install_framework.py` symlinks the canonical files into `~/.claude/` ... an
update is a `git pull` with no re-copy and no drift between the repo and what is installed."*

What is wrong: `git worktree list` in this repo returns the primary checkout at
`/Users/roaldp/conductor/repos/roald` plus seven live workspaces. The primary checkout is currently
on branch `fix/deferred-update-apply` at `24f314e`, with untracked files, while every workspace is
on `ed0d491` or later. If the symlinks point at the primary checkout, the globally installed
framework is whatever branch that worktree happens to be parked on, and it changes under all seven
concurrent workspaces the moment someone checks out a branch there. A `git pull` is not the update
path; `git checkout` is the accidental update path.

Second, `lima` is the pulse companion: `pulse.py`, `prompts/`, `templates/`, `tests/`. Putting a
machine-wide agent framework in it means every framework edit ships in a pull request against the
Slack companion, and every companion branch carries the framework.

Instead: install to a fixed path that is not a Conductor worktree — clone to `~/.agent-framework`
and pull there, or copy on install with a version stamp so drift is visible. If it stays a symlink,
pin it to a directory whose branch nobody changes.

### 13. The one-line `@AGENTS.md` fix is real and oversold. MODERATE

The claim: build order item 2, *"One-line `CLAUDE.md` with `@AGENTS.md` in the three repos that need
it — Turns 517 MB of agent work from unguided to guided — One line per repo."*

What is right: the mechanism. This is the best item in the design.

What is wrong: the accounting. `git ls-tree -r origin/main` in `ai-infrastructure-capital` shows ten
`AGENTS.md` files — root plus `docs/calls`, `docs/crm`, `docs/hardware-procurement`,
`docs/pitch-materials`, `nexara`, `portal`, `ragnarok`, `us/website`, `website`. The import only
loads the root router. Claude Code's on-demand nested loading applies to nested `CLAUDE.md`, not to
nested `AGENTS.md`, so the nine sub-files stay dormant unless the model chooses to open them. The
root router does list them, which helps, but "turns 517 MB from unguided to guided" is not what one
line buys.

Also, one of the three named repos already has the file. `/Users/roaldp/conductor/repos/tiny-skylines`
has both `CLAUDE.md` (67 lines) and `AGENTS.md` (53 lines), and the `CLAUDE.md` does not import the
`AGENTS.md` — it duplicates the global rules instead ("Be to the point. Do not overengineer"). So the
work item there is different from the work item in AIC, and the design does not distinguish them.

Instead: one line in the root of each repo that has a root `AGENTS.md` and no `CLAUDE.md`, plus a
one-line `CLAUDE.md` next to each sub-`AGENTS.md` that matters, plus a de-duplication pass in
`tiny-skylines`. Still cheap. Just not one line.

### 14. Skill cost and hook cost are priced backwards. MODERATE

The claim: *"Skill descriptions cost every session. Every installed skill's name and description is
charged against a listing budget of one per cent of the context window ... Skill sprawl is a real
cost, so this framework adds few skills."*

What is wrong: one per cent of a 1M window is 10,000 tokens, and `~/.conductor/settings.toml` puts
every workspace on `claude:opus-5-1m`. Description plus `when_to_use` is capped at 1,536 characters
per skill. Twenty skills is on the order of 7,500 tokens, still inside budget, and roughly 0.75 per
cent of context. On this machine skill sprawl is close to free.

Meanwhile the design adds five hook registrations — `InstructionsLoaded`, `SessionStart`,
`SubagentStart`, `PreToolUse`, `PostToolUse` — and prices none of them. `PostToolUse` on
`Edit|Write` fires roughly 25 times per large session at current rates. `SubagentStart` fires per
subagent, and the concurrency default is 20. Each is a process spawn with a 600-second default
timeout and a visible error path.

So the design suppresses the cheap mechanism that its own evidence says works best — re-injecting
the style guide at the point of writing, which is what a skill does — on a cost argument that is
wrong by an order of magnitude, and adds five instances of the expensive mechanism without counting
them.

Instead: add skills freely, add hooks one at a time with a week between each.

### 15. Manufactured corroboration on the 200-line ceiling. MODERATE

The claim: *"Its cap matters as much as its content. `STYLE.md` is capped at 210 lines ... Anthropic's
own guidance puts the same ceiling on `CLAUDE.md`: under 200 lines."*

What is wrong: `research/01` explicitly warns against this move — "The widely-repeated '200 line'
figure in blog posts is just this doc line being restated, so treat it as one source, not many." The
AIC 210-line cap is a number someone on this machine chose. Anthropic's 200 is a documentation
guideline about a different file type. Placing them next to each other and calling it "the same
ceiling" turns one source into two by coincidence of magnitude.

The cap is still a good idea. It just has one source, which is Roald's own past judgement, and that
should be said.

### 16. `planning-with-files` is called cross-verification and is not. MODERATE

The claim: heading *"Cross-verification: an independent skill, `planning-with-files`, implements
exactly this shape and reports a 96.7 per cent assertion pass rate with it versus 6.7 per cent
without."*

The design does then disclose that the numbers are author-reported on their own tool and measured on
Sonnet 4.6. Good. But the word "cross-verification" and the word "independent" do the persuasive work
before the caveat arrives, and a tool author benchmarking their own tool is neither. `research/01`
open question 3 asks the sharper question the design skips: whether the effect is largely "a weaker
model needs an external scaffold", in which case the gain on Opus 5 may be near zero. Every workspace
here runs Opus 5.

Instead: cite it as a design precedent, not as verification, and treat the 96.7 figure as unusable.

### 17. The design exempts itself from its own success-criteria rule. MODERATE

The claim: *"**Success criteria.** Given, when, then. Observable trigger, observable outcome. These
get checked mechanically at the end, so they have to be mechanically checkable."*

What is wrong: the design contains no success criteria for itself. The closest thing is the last line
of the document — "The honest test is whether, four weeks in, the log sections have entries" — which
is one observable test for one of six parts, buried under "Known risks". Nothing states what would
count as problem 1 being solved, or what number would tell Roald to switch any of this off.

Instead: three observable criteria before any build. Roald sends an agent-drafted external email
without rewriting the first paragraph. A week of agent updates where none exceeds half a page. A plan
whose `Log` section has an entry written by the agent that deviated.

### 18. The moving-part count contradicts the standing instruction. MODERATE

Project `CLAUDE.md`: "BE TO THE POINT. Less is more." and "DO NOT OVERENGINEER. KEEP IT SIMPLE."

A single job under this design touches: `CORE.md`, a medium overlay, an exemplar set, the
`write-external` skill, `style_lint.py`, a `PostToolUse` hook, an intake skill, `PLAN.md` with eight
mandated sections, `contract.json`, a `SessionStart` hook, a `SubagentStart` hook, `reanchor.sh`, a
`PreToolUse` gate, an evidence counter file, a `plan-auditor` subagent, an orchestration skill, a
challenge subagent, an `InstructionsLoaded` logger, an install script, a per-repo `CLAUDE.md` shim
and one environment variable. That is twenty-one artefacts, five hook registrations, four skills and
two subagents, to answer five complaints from a man whose two loudest standing instructions are be
brief and do not overengineer.

The design has an answer to this — build order, evidence over cost — and the build order is honest.
But it never asks the question "what is the smallest thing that would change the outcome", and that
question has a good answer. See the smaller design below.

### 19. Third-time-mildly-wrong, per mechanism. MODERATE

- **Lint hook.** Blocks a write because the file says "several". Demonstrated: 24 findings on the
  design's own document, one of them hallucinated from a filename. Off within three days.
- **Contract gate.** Denies the write because the agent read the evidence with `cat`. Deadlock, not
  friction. Off within one job.
- **Reanchor hook.** Announces an active plan in a session that has nothing to do with it, because a
  stale plan directory is the newest one on disk. Roald starts ignoring the banner in week one, which
  costs nothing, and then ignores it in week three when it matters.
- **Intake questions.** Three questions where the answer was in the repo. The research says a third
  of apparent ambiguity is self-resolvable, and nothing in the design measures whether the agent
  actually attempted resolution first. Roald starts skipping the intake skill.
- **Depth cap.** Fails invisibly. The `Agent` tool is withheld at the limit and there is no error.
- **Evaluator subagent.** Costs a full extra subagent run per phase for a binary answer. On the ten
  minute jobs that make up the median session here — median non-pulse transcript is 259 KB, p90 is
  1.8 MB — that is pure overhead. The design acknowledges a floor is needed for orchestration and
  does not define one for the evaluator.

### 20. `@AGENTS.md` duplication claim is overstated. MINOR

The design says the AIC `AGENTS.md` "restates Roald's global writing rules verbatim, copy-pasted from
`~/.claude/CLAUDE.md`." It does not. Lines 50 to 62 of that file are a condensed prose paraphrase,
and they carry a scoping sentence the global file lacks: "These govern how you explain things to
Roald, in chat, in commits and in docs. They do not govern investor-facing copy." That is the
core-plus-overlay split the design presents as its own contribution. Prior art, already written, in
the busiest repo on the machine.

### 21. Global `CLAUDE.md` compaction survival is assumed, not sourced. MINOR

The four-homes table says `CLAUDE.md` at project root is "Re-injected from disk", which matches
`research/01`. Part 6 then puts the framework's always-on rules in `~/.claude/CLAUDE.md`. The
compaction table in the research names project-root `CLAUDE.md` and unscoped `.claude/rules/*.md`.
Whether the user-level file is re-injected is not established anywhere in the corpus. Given finding
3 this matters less than it looks, but it belongs on the verification list and is not there.

### 22. Two built-in agents do not receive the framework. MINOR

`research/03` records that the built-in `Explore` and `Plan` agents skip the `CLAUDE.md` hierarchy,
and that output styles do not reach subagents at all. Part 6 claims the user-global layer "reaches
the CLI, every Conductor workspace, and Claude Desktop's local agent mode". Two of the agent types
most likely to be used for the read fan-out in Part 5 are exceptions, and the design does not say so.

## The smaller design

In order. Stop after step 3 and re-read the brief before continuing.

1. **Fix what is already broken and already loaded.** Create the missing `plan-reviewer` subagent
   that `~/.claude/commands/create_plan.md` has been calling into the void. Remove the emoji
   instruction from that same file. Audit the other ten command files for dangling references. Half
   a day, no new concepts, and it delivers the challenge round Roald asked for.

2. **One line per repo, done properly.** A committed `CLAUDE.md` containing `@AGENTS.md` at the root
   of every repo with a root `AGENTS.md` and no `CLAUDE.md`, starting with
   `ai-infrastructure-capital` because it holds 581 of 900 MB. A one-line `CLAUDE.md` beside each
   sub-`AGENTS.md` that carries real rules. In `tiny-skylines`, delete the duplicated global rules
   from its `CLAUDE.md` and import its `AGENTS.md`. An hour, and it is the highest-value change
   available on this machine.

3. **A `write-external` skill, rules only, no enforcement.** Point it at AIC `STYLE.md` sections 1,
   3, 4, 6, 7, 8 and 9 with the vehicle-specific paragraphs stripped, and at nothing else until the
   corpus exists. No `CORE.md` rewrite, no linter, no hook. The mechanism that matters is that the
   guide arrives in a short fresh context at the moment of writing, and a skill delivers that on its
   own. Half a day.

4. **`InstructionsLoaded` logging, then two weeks of silence.** One hook, one log file, absolute
   path, no other change. Then look at what actually loaded before deciding anything else.

5. **An output style for updates to Roald.** The system prompt is the only insertion point stronger
   than `CLAUDE.md`, and the update-length problem is a main-conversation problem. Try it, measure it
   for a week against the existing rule, keep whichever wins.

Everything else — `contract.json`, the write gate, the evaluator subagent, the orchestration skill,
the depth cap, the linter, the plugin question — waits for a measurement that does not exist yet.
Four of those five steps are edits to files that already exist. None of them adds a blocking hook.

## Untested assumptions

| Assumption | What breaks if false | Cheapest test |
|---|---|---|
| Agents on this machine write files with `Edit` and `Write` | The lint hook and the contract gate both see a minority of writes; the evidence counter never increments | Already tested and false. Bash 3,051 against Edit plus Write 626 across 25 recent large sessions; harness instructs Bash-first under bypass permissions |
| Long sessions compact, so compaction survival is the durability axis | Part 4's entire re-anchor design targets an event that rarely fires | Already tested. 12 of 114 sessions over 2 MB carry a compaction marker |
| Roald's own writing conforms to the proposed rules | The feedback loop's own criterion says the rules are wrong, and the linter blocks his voice | Already tested and false. `python3 lint.py ~/.claude/CLAUDE.md` gives 7 findings, 6 of them em dashes |
| A style guide plus exemplars beats a style guide alone, for Claude | Part 1's ordering of mechanism and backstop is inverted; exemplar collection is wasted | `research/02` open question 4. Draft the same email three ways — rules only, exemplars only, both — and have Roald rank them blind. One hour |
| Three intake questions per ambiguous area is tolerable to a human | The intake skill is abandoned after two uses | Run the next real brief through it, count questions, count how many Roald answers. One job |
| `~/.claude/CLAUDE.md` is re-injected after compaction like a project-root file | Global rules silently vanish in any session that does compact | One session, `/compact`, then ask the model to quote a distinctive line from the global file |
| A `SubagentStart` hook fires for Agent-tool subagents in a Conductor session and its `additionalContext` lands | Delegated workers get no anchor, which is the whole point of Part 5 | On the design's own verification list. Register a hook that echoes a nonce, spawn a subagent, ask it for the nonce. Ten minutes |
| The `PreToolUse` deny on `contract.json` is not bypassable | The "only unbypassable check" is a speed bump | `echo '{"x":{"passes":true}}' > contract.json` through Bash with the hook installed. Five minutes |
| Symlinking `~/.claude` into a Conductor primary checkout gives a stable install | Global agent behaviour changes whenever that worktree changes branch | `git worktree list` already shows the primary on `fix/deferred-update-apply` while workspaces sit on `ed0d491`. Confirmed unstable |
| Skill listing budget is a real constraint here | The design under-uses its most effective mechanism for no reason | Run `/context` in an Opus 5 session and read the skills line. Two minutes |
| Opus 5 is inside the todo-tools-disabled list, and drift is not a checklist problem | An A/B that might resolve Part 4 cheaply never gets run | `CLAUDE_CODE_ENABLE_TODO_TOOLS=1` on one workspace for a week |
| The existing `/implement_plan` orchestration fails for a reason a skill can fix | Part 5 is a rewrite of an instruction that already did not work | Read three transcripts where `/implement_plan` ran and find the turn delegation stopped. One afternoon |
| An output style can carry the update-format rules and is stronger than `CLAUDE.md` | Problem 2 has no mechanism at all, which is the current position | Write one, use it for three days, count replies over half a page |
