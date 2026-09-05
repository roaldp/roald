# The framework: design

Draft 1, 2026-09-06. Not yet challenged. Nothing here has been installed.

Read `00-STATE.md` for the brief this answers and `01-machine-map.md` for what is
actually running on the machine. The evidence behind every claim is in `research/`.

## What the framework has to do

Five things, from Roald's brief:

1. Make external writing read as his, not as an agent's.
2. Make agent updates readable in under a minute, with depth on request.
3. Turn one long spoken brief into a scoped plan through discovery, ideation, design
   requirements, then MVP execution.
4. Reach every agent on the machine from one repo, merged with what each agent already
   knows.
5. Stop agents drifting off the plan, using an orchestrator that delegates rather than
   executes.

## The distinction everything else follows from

Anthropic's own documentation states it in one line: Claude treats `CLAUDE.md` as
context, not as enforced configuration. To block an action regardless of what Claude
decides, use a `PreToolUse` hook.

Every rule Roald has written down anywhere on this machine is currently context. No
hooks are configured in any settings file here. That is the single largest gap, and most
of what follows is moving specific rules one rung up, from instruction to mechanism.

A rule has one of four homes and the choice is not stylistic:

| Home | Loads when | Survives compaction | Use for |
|---|---|---|---|
| `CLAUDE.md` at project root | Every session | Re-injected from disk | Short always-true facts. Under 200 lines total. |
| `.claude/rules/*.md` with `paths:` | When a matching file is read | No, reloads on next matching read | Rules tied to a file type |
| Skill | When the task triggers it | Re-injected, 5,000 tokens per skill, 25,000 total | Anything long. Procedures. Style guides. |
| Hook | Unconditionally | `SessionStart` matching `compact` re-runs; other hook output is summarised away | Enforcement and re-anchoring |

Three consequences that are easy to get wrong and that changed this design:

**Hook-injected context is not durable.** A `UserPromptSubmit` hook that re-injects the
plan works within a session and is summarised away at the next compaction. The durable
re-injection point is a `SessionStart` hook with `matcher: "compact"`, which Anthropic
documents as re-run after compaction with its output added to the compacted context.

**`@path` imports do not save context.** Splitting a long `CLAUDE.md` into imports makes
it tidier and no cheaper.

**Skill descriptions cost every session.** Every installed skill's name and description
is charged against a listing budget of one per cent of the context window, whether or not
the skill is used. Skill sprawl is a real cost, so this framework adds few skills.

---

## Part 1. Writing

### Split the existing system rather than write a new one

Roald already has a working writing system in `ai-infrastructure-capital`
(`docs/pitch-materials/style/`, seven files plus two skills, on `origin/main`). It is
better than anything we would write from scratch, because it was built from real
before-and-after pairs of his own edits. Parts of it are investor-pitch-specific and
parts are general. The design is to split it, not to replace it:

- **`style/CORE.md`** governs any prose a person outside the company reads. It comes
  from sections 4 to 8 of the existing `STYLE.md` — sentences, numbers, emphasis,
  punctuation, banned constructions — plus the general rules in
  `research/02-writing-style-and-briefing.md`. It ships from this repo and installs
  user-globally.
- **Overlays** name a medium and carry only what differs: `PITCH.md`, `MESSAGES.md`,
  `EMAIL.md`. The two existing AIC files become overlays and stay in that repo. AIC
  claims and vehicle facts never leave it.

### Exemplars are the mechanism, rules are the backstop

Anthropic's own prompt guidance says examples are the tool for tone and format, that
positive framing beats negative, and that Claude attends closely to details in examples.
Its worked example is on the nose for this problem: "Do not use markdown in your
response" is the weaker form, "Your response should be composed of smoothly flowing prose
paragraphs" is the stronger.

Measured elicitation rates for style and aesthetic requirements are near zero, so asking
Roald what he wants does not work. What works is samples of what he has written and sent.
Those are being collected into `research/05-roald-writing-corpus.md`.

Two things follow that are easy to get wrong:

An exemplar must contain nothing we do not want copied, formatting included.

The style guide must itself obey its own rules, because the formatting of a prompt
influences the formatting of the output. A style guide written in stacked bullets teaches
the agent to write stacked bullets.

### The rules that survive into CORE.md

The full list, with confidence ratings and sources, is in
`research/02-writing-style-and-briefing.md`. In order of how often they will fire:

No em dashes inside a sentence. The general claim that AI overuses em dashes is now
false — the Economist's July 2026 corpus of 55,940 sentences found ChatGPT below the
human rate — but Claude was the one model of four still above it. The ban stays, the
justification changes.

No "not just X, it's Y" and no "not X, but Y". State Y.

Every authority claim carries a name, a number or a link, or it is deleted.

Vary sentence length deliberately. Every paragraph gets one sentence under eight words
and one over twenty. Uniform length is the structural marker every source agrees on.

At most one three-item parallel list per two hundred words.

Prose stays prose. Bullets are for genuinely enumerable, parallel, unordered items.

No closing summary paragraph in short-form writing.

Banned vocabulary with replacements, carrying a review date, because these lists drift
every six to twelve months.

The deletion test before sending: if a third of the sentences can be cut without losing
information, rewrite. This is the only rule that attacks "inefficient to read" rather
than "sounds like an AI", and that was half of Roald's complaint.

**No AI-detector score is used as an acceptance test.** Detectors run at 61 to 69 per
cent accuracy, near zero on mixed human-and-AI text, which is exactly what we produce,
and they misclassify non-native English as machine-written. The acceptance test is
Roald's own read.

### Enforcement, weakest to strongest

**A skill, `write-external`.** Triggers on drafting or revising anything a person outside
the company reads. It loads `CORE.md`, the right overlay, and the exemplars for that
genre. This is the fix for style-guide drift: the guide arrives at the moment of writing,
in a short fresh context, rather than sitting at the top of a long session where
attention has moved on.

**A linter, `style_lint.py`.** A generalisation of the AIC `lint.py`, which already
catches banned words, banned patterns, vague quantifiers standing in for a figure,
sentences over forty words and runaway bold density. Added: em-dash count, sentence-length
variance, triplet density, transition-word ratio.

**A `PostToolUse` hook on `Edit|Write`.** Runs the linter on files that are actually
outbound copy and returns `decision: "block"` with the issues, so the agent fixes them
before moving on. Scope this narrowly at first. A linter that fires on every markdown
file in every repo gets switched off within a day.

### The feedback loop

The best input this system can get is the diff between what an agent drafted and what
Roald actually sent. The AIC `pitch-style-feedback` skill already does this and
generalises with almost no change: diff at sentence level, triage every change into
style, claim, fact or noise, find the one rule behind a cluster of edits rather than
recording seven separate pairs, and require that Roald's own text scores zero on the
linter. If a new rule flags his own writing, the rule is wrong.

Its cap matters as much as its content. `STYLE.md` is capped at 210 lines and adding a
pair means cutting a rule that has stopped earning its place. Anthropic's own guidance
puts the same ceiling on `CLAUDE.md`: under 200 lines, because longer files consume more
context and reduce adherence.

---

## Part 2. Updates to Roald

### Dropdowns are not available where they would help

Roald asked whether dropdown items are possible in the chat interface. Verified per
surface:

| Surface | Does `<details>` collapse |
|---|---|
| GitHub issues, pull requests, READMEs | Yes. Needs a blank line after `</summary>`. |
| Slack | No. mrkdwn has no HTML layer at all. |
| Claude Code terminal | No. The renderer is a GFM subset with no HTML handling. |
| Claude Desktop chat body | Unverified. Assume no until tested. |
| Claude artifacts | Yes in principle, since artifacts render real HTML. |

Progressive disclosure therefore has to be layered across artefacts rather than delivered
by a widget.

Two further terminal facts change how updates should be written. Headings `h2` through
`h6` all render as identical bold, so hierarchy is invisible. Link labels are discarded,
leaving a bare URL in the middle of a sentence. **Use at most one heading level and print
bare paths.**

### The shape

Bottom line up front is the doctrine that matches the one-minute constraint, and AR 25-50
supplies the numbers: main point first, active voice, roughly fifteen words per sentence,
paragraphs under ten lines and one idea each, understood in a single rapid reading.

Nielsen's constraint on progressive disclosure is the one most often violated and the one
that matters here. **The first layer must contain everything the reader frequently
needs.** A summary carrying only a topic label has relocated the complexity rather than
reduced it, and now costs Roald a click and a re-read.

For an agent update that means four things in this order and nothing else:

1. What happened, in one line.
2. What needs a decision, stated as a decision, with a recommendation.
3. What changed that would alter the plan — a contradiction, a blocker, a number that
   does not reconcile.
4. Where the detail lives. A path.

Roald's `~/.claude/CLAUDE.md` already says most of this. What it lacks is the per-surface
specifics and any enforcement.

### Per surface

**Claude Code terminal.** Half a page. One heading level. Bare paths.

**Slack.** Summary in the parent message, detail in the thread. That is Slack's native
progressive disclosure. Parent under four thousand characters, which is Slack's own
guidance; the hard limit is forty thousand. No headers, no tables, no HTML.

**GitHub pull request descriptions.** `<details>` for logs, diffs and test output.

**The pulse companion in this repo.** `prompts/pulse_full.md` and
`prompts/pulse_reactive.md` produce the only unprompted messages Roald gets. The Slack
rules apply there most directly, and because the companion fires every thirty minutes it
is the cheapest place to find out whether the format actually saves him time.

---

## Part 3. From a spoken brief to a scoped plan

### What exists and what does not

Spec-driven development is the 2026 convergence and every major agent tool ships a
flavour: GitHub Spec Kit, AWS Kiro, Cursor, OpenSpec, BMAD, Tessl, Antigravity. The
stages are consistent — specify, plan, decompose, implement — and the claimed value is
externalising the intermediate artefacts so intent is explicit and auditable.

**Read the evidence honestly.** The one controlled study, Spec Kit Agents, ran 128 runs
over 32 features and measured a composite quality gain of 4.3 per cent and 1.7 percentage
points on SWE-bench Lite, at 46 per cent more wall-clock time. The "3 to 10 times higher
first-pass success" and "60 to 80 per cent fewer rework cycles" figures in circulation
trace to vendor marketing, not measurement. The mechanism is worth adopting; the expected
gain is single-digit percentages, and we should not tell ourselves otherwise.

**Every framework surveyed starts at "specify" and assumes intent is already decided.**
None has a discovery stage. The step Roald describes, from a rambling voice brief to
something worth specifying, sits upstream of where the whole ecosystem begins. That part
we design ourselves, and there is no prior art to lean on.

### Intake is a separate pass, not an instruction

The strongest evidence available: an underspecified variant of SWE-bench Verified tested
clarification scaffolds and found that a **separate** intent-checking agent watching the
working agent scored 69.4 per cent, the same uncertainty-awareness folded into the single
working agent scored 61.2 per cent, and no asking at all scored 54.8 per cent. Decoupling
detection from execution moved the number by 8.2 points.

Calibration from the same work, single-sourced but from a clean controlled design: about
three questions per task it chose to query, and it chose not to ask at all on 31 per cent
of tasks without losing accuracy on those. Roughly a third of apparent ambiguity is
resolvable by reading the repository. Questions arrived both early and mid-trajectory,
because some ambiguity is only visible after you have read the code.

A separate benchmark of LLMs conducting elicitation interviews found they favour open
probing over precise clarification, surface about a third of implicit requirements, and
score near zero on style and aesthetic requirements. Making the model reason before asking
cut interview length while improving question quality.

Three rules follow:

**Resolve from the repository first.** Ask only what reading cannot answer.

**Budget about three questions per genuinely ambiguous area, and attach the agent's own
proposed answer to each**, so Roald can reply "yes" rather than write a paragraph. That is
the concession to his context-switching cost, and it is the whole reason the long-brief
workflow is preferable to a tight feedback loop for him.

**Never ask about style.** Collect exemplars.

### The plan file, and the contract beside it

Two files per job in `.docs/plans/<yyyy.mm.dd>-<slug>/`.

`PLAN.md` is for humans and for the agent to read. Fixed sections:

**Brief.** What Roald said, verbatim, never edited. The anchor every anti-drift mechanism
points back to.

**Discovery.** What is true: what exists, what was found, what the constraints are, what
prior art is already on the machine. It ends with the problem restated in the agent's own
words. Roald reads that restatement to check the agent understood him, and reading one
paragraph is cheaper for him than answering five questions.

**Open questions.** The intent-check output. Each carries a proposed answer and is marked
resolved or unresolved. An unresolved question that blocks nothing does not stop work; the
assumption is recorded and flagged.

**Approach.** Options considered, one chosen, why, rejected ones named. Roald's ideation
stage.

**Success criteria.** Given, when, then. Observable trigger, observable outcome. These get
checked mechanically at the end, so they have to be mechanically checkable.

**MVP scope.** What is in and explicitly what is out. Roald asked for the minimum format
that meets the goal, prioritising scope success, speed and simplicity for reviewers. The
"out" list is the section that does the work.

**Steps.** A checklist. Each step names its verification.

**Log.** Append-only. What was done, and what deviated from the plan and why. A deviation
that is written down is a decision. One that is not is drift.

`contract.json` is for the harness. Every phase starts failing:

```json
{ "discovery": {"passes": false}, "approach": {"passes": false}, "step-1": {"passes": false} }
```

The agent cannot end the run by asserting it is done. It ends when a file it had to
justify editing says so. Part 4 explains how that justification is enforced.

### The four stages map onto the file

| Roald's stage | Section | Gate before moving on |
|---|---|---|
| Discovery | Brief, Discovery, Open questions | The restatement is accepted |
| Ideation | Approach | An option is chosen |
| Design requirements | Success criteria, MVP scope | Every criterion is observable |
| Execution | Steps, Log | Each step's verification passes |

---

## Part 4. Not drifting

Three failure modes get called drift and they need different fixes. **Instruction
eviction**: a long session pushes the brief out of the attention window. **Compaction
loss**: anything that existed only as conversation gets summarised away. **Silent scope
creep**: the agent keeps working, on an adjacent task, and nothing checks the work against
the agreed definition of done.

### The plan on disk, re-anchored by a SessionStart hook

Best-supported technique in the corpus, and partly native already. Anthropic's
context-window documentation gives an explicit table of what survives compaction. Project
-root `CLAUDE.md`, unscoped `.claude/rules/*.md`, auto memory and **a plan written in plan
mode** are all re-injected from disk. Conversation, including anything a hook injected
earlier, is summarised away.

So the hook has to be `SessionStart` with `matcher: "compact|resume|startup"`, and it
emits a pointer rather than the plan:

```json
{ "hooks": { "SessionStart": [ { "matcher": "compact|resume|startup",
  "hooks": [ { "type": "command",
    "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/reanchor.sh" } ] } ] } }
```

`reanchor.sh` emits
`{"hookSpecificOutput":{"additionalContext":"<active plan path, current phase, next step>"}}`
and nothing at all when there is no active plan, so it costs nothing on ordinary sessions.
Keep it to the pointer and the phase. The plan is on disk and Claude can read it.

The same hook is registered on `SubagentStart`, because a subagent inherits no
conversation history, no files the parent read, no invoked skills and no auto memory.
Without this, a delegated worker has no idea a plan exists.

Cross-verification: an independent skill, `planning-with-files`, implements exactly this
shape and reports a 96.7 per cent assertion pass rate with it versus 6.7 per cent without,
and 5.0 versus 13.3 turns to resume after a deliberate context wipe. Those numbers are
author-reported on their own tool and were measured on Sonnet 4.6, so treat the magnitude
as unverified. The direction agrees with Anthropic's documented compaction behaviour.

### The default-FAIL contract with a PreToolUse write gate

This is the only mechanism in the corpus an agent cannot talk its way past, and it comes
from Anthropic's own long-running-agents demo repo.

Every phase in `contract.json` starts `{"passes": false}`. Two hooks make marking one
`true` conditional on having looked at evidence:

- A `PostToolUse` hook increments a counter when the agent reads a file matching an
  evidence pattern — test output, a diff, a screenshot, a log.
- A `PreToolUse` hook **denies** any write to `contract.json` while that counter is zero,
  and resets it after each gated write.

"Mark this step passing" is then only reachable through "open the evidence first".

**This matters more on this machine than the sources assume.** Conductor launches sessions
with bypass permissions — this session's own harness confirms it — and Anthropic's
permission-modes documentation states that in sessions with bypass permissions available,
plan mode's blocks are not enforced. Claude is still instructed to plan without editing,
but an edit it attempts during planning runs without prompting. So plan mode here is a
human approval step, not a gate, and the `PreToolUse` gate is load-bearing rather than
belt-and-braces.

### A fresh-context evaluator with no write tools

Both Anthropic harness examples use a grader that has never seen the generator's
reasoning: a subagent with `tools: Read, Grep, Glob, Bash` and `disallowedTools: Write,
Edit`, asked one question. Does the diff satisfy this phase's acceptance criteria, yes or
no, and if no, what is missing. Findings go to a file that becomes the next phase's
prompt.

It must be a plain subagent. **Never a fork.** A fork inherits the entire parent
conversation and so inherits the generator's rationalisations, which makes it useless as
an independent check.

### Turn on InstructionsLoaded logging before tuning anything else

The `InstructionsLoaded` hook reports `file_path` and `reason` — `session_start`,
`nested_traversal`, `path_glob_match`, `include`, `compact`. Logging it to a file, plus
`/context`, is the only way to know whether an instruction that was ignored was ever
actually loaded.

**This should be the first thing installed**, before any rule is written or moved. Every
other tuning decision is guesswork until it is on, and it costs one hook and a log file.

### Two things deliberately not adopted

**The in-session todo tools.** `TaskCreate` and friends are disabled by default on Opus
4.8, Sonnet 5, Fable 5 and later, on Anthropic's stated grounds that these models track
multi-step work without a written checklist. That contradicts a large body of 2025-era
anti-drift advice. The on-disk plan file serves a different purpose — surviving compaction
and session restarts — and stays. Re-enabling the in-session checklist is worth an A/B on
this machine rather than taking either side on faith.

**Plan mode as an enforcement boundary.** Worth using for the human approval step it
genuinely provides, and its plan does get re-injected from disk after compaction. Not
worth relying on for enforcement here, for the bypass-permissions reason above.

---

## Part 5. The orchestrator

### One rule, from two sources that agree on almost nothing else

Anthropic's multi-agent research post reports an orchestrator-worker system beating
single-agent Opus 4 by 90.2 per cent on their internal research eval, with token usage
explaining 80 per cent of the performance variance and multi-agent costing about fifteen
times chat. Cognition's "Don't Build Multi-Agents" argues the opposite: parallel subagents
make independent decisions that conflict, and the fix is a single-threaded linear agent
with a compression step when context runs out.

They converge on one thing, and each says it in their own words:

> Fan out for reading. Keep writing single-threaded.

Anthropic's post warns that most coding tasks involve fewer truly parallelisable subtasks
than research, and that multi-agent is poor where agents need shared context or have many
inter-dependencies. Cognition observes that Claude Code itself uses subagents only for
read-only investigation. That convergence is the strongest cross-verified claim in the
research.

So: research, codebase exploration and review fan out. Implementation does not.

### Keep the pipeline shallow

OrchestraBench measured cascade radius against pipeline depth: 0.93 at depth 3, rising to
4.67 at depth 7. Roughly one additional contaminated agent per extra stage. It also found
that latent failures — context pollution, conflicting subagent outputs, premature action —
recover at a rate of 0.0. They never self-correct, and retry only lengthens the time to
detection.

Rate that evidence MODERATE and read its limitation: the authors ran a single Claude agent
over arithmetic chains, not a true multi-agent system. It is a mechanism probe.

Even so, the practical reading is clear. Set `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=2`.
Claude Code's default is 3, nested subagent results do not surface to the main
conversation anyway, and depth 3 is already the zone where a contaminated intermediate
result is invisible.

### The delegation brief carries four fields and hands back a path

There is no schema-typed return from a subagent. The Agent tool returns text. So handoff
goes through files by convention, which is also what Anthropic's own artefact-system
appendix recommends: subagents store their work externally and pass lightweight references
back, which avoids both information loss across stages and the token cost of copying large
outputs through conversation history.

Each delegation carries exactly four things — Anthropic's list, corroborated in shape by
OrchestraBench's finding that an explicit decompose policy gave 1.0 delegation fidelity
against 0.37 for a monolithic prompt:

1. The objective, including the plan file path and which step this is.
2. The output format, including the exact path to write.
3. Guidance on tools and sources.
4. Task boundaries: what this subagent must not do.

The subagent writes the file and returns a short summary plus the path.

The orchestrator does three things per step. Delegate. Verify the output against the
step's criterion. Tick the step and log. It does not do the work.

### Scale it to the job

Anthropic's own documented early failures were spawning too many subagents for simple
queries and duplicating work through an unclear division of labour. Their scaling
heuristic: one subagent for simple fact-finding, two to four for a direct comparison, ten
or more only for complex research with clearly divided responsibilities.

The orchestration skill needs a floor below which it does not fire at all. A three-agent
pipeline on a ten-minute job is pure overhead.

### The challenge round

Roald asked to be challenged at least twice before execution and named thoroughness as the
thing he most wants forced. That belongs in the procedure rather than in a good intention.
After the plan is drafted and before any step runs, a subagent is spawned whose only job
is to attack it, twice, from different angles. What survives gets built. This is the same
fresh-context evaluator pattern, applied to the plan instead of the diff.

---

## Part 6. Getting it onto every agent

### The layers

**User-global, `~/.claude/`.** Reaches the CLI, every Conductor workspace, and Claude
Desktop's local agent mode, since all three share this directory. This is where the
framework lives: `CLAUDE.md` for the short always-on rules, `skills/` for style, intake
and orchestration, `hooks/` for the anchor, the gate and the linter, `settings.json` to
wire them up.

**Per-repo, committed.** Only what is specific to that repo. Its own router content,
facts and constraints. The framework is inherited, not copied in.

**Per-workspace.** Nothing. Conductor workspaces are checkouts, and anything written in
one alone is lost. The `ai-infrastructure-capital` repo's own hygiene document already
records that roughly four in ten counterparty records never make it back to `main`.

### Installing from one repo

This repo is the source of truth. A `scripts/install_framework.py` symlinks the canonical
files into `~/.claude/`. Symlinks are supported for skills directories and for
`.claude/rules/`, so an update is a `git pull` with no re-copy and no drift between the
repo and what is installed.

The alternative is packaging this as a Claude Code plugin and adding this repo as a
marketplace. Roald already has one marketplace configured, so the machinery works. It is
cleaner for versioning and rollback. Its cost is that plugin skills are namespaced and
plugin hook behaviour needs checking first.

**Recommendation: symlinks now, because they are reversible in one command and easy to
reason about. Revisit plugins once the content has stopped changing weekly.**

### Merging with what each agent already knows

Roald asked for an update sequence per agent that marries the framework with the
context-specific knowledge each already has. The framework never overwrites a repo's own
instructions. It installs user-globally, and the per-repo work is three small things:

1. **Make the repo's existing instructions load at all.** A one-line `CLAUDE.md`
   containing `@AGENTS.md`, committed to `main`, for each of the thirty-one directories
   that currently have an `AGENTS.md` and no `CLAUDE.md`. This is the highest-value change
   available and it costs one line per repo.
2. **Remove what the global layer now supplies**, so each rule has one home. The AIC
   `AGENTS.md` currently restates Roald's global writing rules verbatim, copy-pasted from
   `~/.claude/CLAUDE.md`. That copy becomes a pointer. Anthropic's documentation is
   explicit that when two rules contradict each other Claude may pick one arbitrarily, so
   duplication is not harmless.
3. **Add only what is genuinely repo-specific.**

Concrete per-repo steps are in `03-rollout.md`.

### Claude Desktop's cloud projects

Local agent mode is covered by `~/.claude`. Claude Desktop's cloud-side Projects are not:
their custom instructions live server-side and cannot be written from this machine. The
options are pasting by hand or syncing skills through claude.ai, and a skill synced that
way must stay inside the smaller Agent Skills frontmatter field set, which excludes every
Claude-Code-only field. This is a real limit rather than something to design around.

---

## Build order

Ordered by evidence strength divided by cost, not by which part is most interesting.

| # | Change | Why first | Cost |
|---|---|---|---|
| 1 | `InstructionsLoaded` logging | Every later decision is guesswork without it | One hook |
| 2 | One-line `CLAUDE.md` with `@AGENTS.md` in the three repos that need it | Turns 517 MB of agent work from unguided to guided | One line per repo |
| 3 | `CORE.md` plus the `write-external` skill and exemplars | The complaint Roald led with | Extraction, not invention |
| 4 | Update-format rules per surface, into `~/.claude/CLAUDE.md` | Second complaint, and it is short | An hour |
| 5 | `PLAN.md` and `contract.json` template, plus the intake skill | The scoping workflow | A day |
| 6 | `SessionStart` and `SubagentStart` re-anchor hook | Anti-drift, best-supported mechanism | A script |
| 7 | `PreToolUse` contract gate | The only unbypassable check, and bypass permissions make it necessary here | A script |
| 8 | Fresh-context evaluator subagent | Catches silent scope creep | An agent definition |
| 9 | `style_lint.py` and the `PostToolUse` lint hook | Mechanical style enforcement | Port from AIC |
| 10 | Orchestration skill | Depends on everything above | A day |

---

## What has to be verified before installing

1. Whether `/goal` can be set programmatically at session start rather than typed.
2. Whether a `SubagentStart` hook fires for subagents spawned through the Agent tool in a
   Conductor session, and whether its `additionalContext` lands.
3. Whether Claude Desktop's local agent mode reads `~/.claude/CLAUDE.md` and
   `~/.claude/skills/`. Shared `~/.claude/projects` is strong circumstantial evidence, not
   proof.
4. Whether Opus 5 is inside the "todo tools disabled by default" list, and what its
   auto-compact threshold is. Check `/context` in a live session.
5. Whether plugin hooks apply globally, if the plugin route is taken later.
6. Whether `.conductor/conductor.json` supports anything beyond a setup script.
7. Roald's own em-dash rate and sentence-length profile, so the rules are calibrated
   against his corpus rather than a published baseline.
8. Whether a `Stop`-hook completion gate is net positive in interactive use. All the
   evidence for it comes from unattended loops, and it may be actively hostile in
   conversation.

## Known risks

**The linter fires too often and gets switched off.** Scope the hook to explicitly
outbound files only.

**The style guide grows until nobody reads it.** The line cap, inherited from the AIC
system, where adding a rule means cutting one.

**Skill sprawl.** Every skill's description costs listing budget every session. Add few.

**The framework diverges from the repo after install.** Symlinks rather than copies.

**Orchestration costs multiples of the token budget.** Reported ratios range from about
fifteen times chat to a twenty-two times cost ratio on one build that went from broken to
working. Both are single-sourced anecdotes from the vendor. The floor below which
orchestration does not fire is the mitigation, and the real number has to be measured on
this workload.

**The plan file is written and then ignored.** This is what all of Part 4 exists to
prevent and it is still the most likely failure. The honest test is whether, four weeks
in, the log sections have entries.
