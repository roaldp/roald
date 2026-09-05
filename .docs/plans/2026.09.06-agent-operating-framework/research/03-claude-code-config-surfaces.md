# Claude Code configuration surfaces, verified September 2026

Captured from a research subagent that cross-checked the official docs at
`code.claude.com/docs` against the Claude Code `CHANGELOG.md`. Claude Code version
bundled with Claude Desktop on this machine is 2.1.260.

This file is reference material for the rollout. It answers one question: where can a
rule be put so that an agent actually follows it, and what gets loaded when.

## Slash commands have been folded into Skills

`.claude/commands/deploy.md` and `.claude/skills/deploy/SKILL.md` both produce
`/deploy`. Commands still work and are documented as the legacy path; Skills are the
recommended form for anything new. On a name clash, the Skill wins.

Precedence, highest first:

1. Enterprise skills
2. Personal `~/.claude/skills/`
3. Project `.claude/skills/`
4. Bundled skills
5. Project `.claude/commands/` (deprecated)
6. Personal `~/.claude/commands/` (deprecated)

Consequence for us: the eleven files in `~/.claude/commands/` are on the deprecated
path. Anything we add should be a Skill.

Subdirectory namespacing works: `.claude/commands/frontend/component.md` becomes
`/frontend:component`.

### Command and skill frontmatter

Command files accept the same fields as skills except `name` and `paths`:
`description`, `when_to_use`, `argument-hint`, `arguments`, `disable-model-invocation`,
`user-invocable`, `allowed-tools`, `disallowed-tools`, `model`, `effort`, `shell`,
`metadata`.

### Argument and interpolation syntax

- `$ARGUMENTS` — everything the user typed after the command.
- `$ARGUMENTS[N]` or `$N` — positional, zero-indexed.
- `$name` — named argument, requires an `arguments` frontmatter block.
- `${CLAUDE_SESSION_ID}`, `${CLAUDE_EFFORT}`, `${CLAUDE_PROJECT_DIR}`.
- `${CLAUDE_SKILL_DIR}` — skills only.
- `${CLAUDE_PLUGIN_ROOT}`, `${CLAUDE_PLUGIN_DATA}` — plugin skills only.
- Inline shell: `` !`cmd` `` or a fenced ```` ```! ```` block. Runs before the prompt is
  sent, two-minute timeout, disabled for skills synced from claude.ai, and switchable
  with `disableSkillShellExecution`.
- `@filename` inlines a file's contents.
- Shell-style quoting applies. A literal dollar sign is escaped as `\$`.

## Output styles are alive, the `/output-style` command is not

Output styles are documented at `code.claude.com/docs/en/output-styles`. The standalone
`/output-style` command was deprecated in v2.1.73 and removed in v2.1.91; the setting
moved to `/config` and the `outputStyle` field in settings.

An output style modifies the system prompt itself — role, tone, format. This is a
different insertion point from the other three surfaces:

| Surface | How it reaches the model |
|---|---|
| Output style | Replaces or modifies the system prompt |
| `CLAUDE.md` | Appended as a message after the system prompt |
| Subagent definition | A separate agent with its own system prompt |
| Skill | Instructions loaded when the task triggers them |

**An output style applies only to the main conversation, not to subagents.** The one
exception is a `fork` subagent, which inherits the parent's full system prompt.

This matters for us: a writing-style rule placed in an output style will not reach a
subagent, so a subagent that drafts an email will not follow it.

## Subagents

Source: `code.claude.com/docs/en/sub-agents`, cross-checked against `CHANGELOG.md`.

Required frontmatter: `name`, `description`.

Optional frontmatter, each confirmed present in the changelog: `tools`,
`disallowedTools`, `model`, `permissionMode`, `maxTurns`, `skills`, `mcpServers`,
`hooks`, `memory` (`user` / `project` / `local`), `background`, `effort`, `isolation`
(`worktree`), `color`, `initialPrompt`, `experimental.cacheTtl`.

Two fields, `color` and `initialPrompt`, were not independently corroborated in the
changelog section the researcher reviewed. Spot-check before relying on them.

### What a subagent does and does not inherit

A normal subagent does **not** see: the parent's conversation history, skills the
parent already invoked, files the parent already read, the parent's output style, or
the parent's auto-memory.

It **does** get: its own system-prompt body, the delegation task message, the full
`CLAUDE.md` hierarchy, a git status snapshot, and any skills named in its `skills`
frontmatter. The built-in `Explore` and `Plan` agents skip the `CLAUDE.md` hierarchy.

A `fork` subagent is the exception and inherits the entire parent conversation, system
prompt, tools and model.

**Consequence for the orchestrator design:** everything a subagent needs must be in the
delegation message, in `CLAUDE.md`, or in a file it is told to read. There is no
implicit shared context. This is the mechanism behind most reported handoff failures.

### Returning results

A subagent returns a single final text message. There is no documented structured
JSON-schema return for `.claude/agents/` subagents. If `maxTurns` is hit, the return
carries a partial-output marker.

**Consequence:** structured handoff has to go through a file the subagent writes, not
through its return value. This is an argument for making the plan file the shared state
rather than the chat.

### Subagent precedence

Managed settings, then the `--agents` CLI flag, then project `.claude/agents/`
(recursive, and it walks up the directory tree), then user `~/.claude/agents/`, then
plugin `agents/` (namespaced as `plugin:agent` or `plugin:folder:agent`).

### Background and isolation

Subagents run in the background by default, unless the agent was spawned in-process by
a teammate, `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1` is set, or the parent needs the
result synchronously. `isolation: worktree` runs the subagent in its own git worktree
with boundary checks enforced on Bash and Monitor commands.

## Memory files: what loads automatically

Source: `code.claude.com/docs/en/memory`, checked September 2026.

Load order, broadest first. All of these are concatenated into context rather than
overriding one another, so "precedence" here means order and recency, plus the fact
that managed policy cannot be excluded.

1. `/Library/Application Support/ClaudeCode/CLAUDE.md` on macOS — managed policy, not
   excludable by the user. Can also be set inline through the `claudeMd` key in
   `managed-settings.json`.
2. `~/.claude/CLAUDE.md` — personal, applies to every project.
3. `./CLAUDE.md` or `./.claude/CLAUDE.md` — project, shared through version control.
4. `./CLAUDE.local.md` — personal and project-specific, gitignored. Not deprecated. It
   is appended after `CLAUDE.md` within each directory.

Claude Code loads `CLAUDE.md` and `CLAUDE.local.md` from the working directory and
every ancestor directory at launch, root first, so the working directory's own file is
read last and sits most recently in context.

**Subdirectory `CLAUDE.md` files are not loaded at launch.** They load on demand, only
when Claude reads a file inside that subdirectory.

### The `@import` syntax

`@path/to/file` imports another file. Relative paths resolve against the importing
file's location, not the working directory. Imports recurse to a maximum depth of four
hops. `~/` paths work, for example `@~/.claude/my-project-instructions.md`, and the
docs recommend this as the way to share personal instructions across git worktrees.
A backtick-wrapped `` `@README` `` is literal text, not an import. An import that
resolves outside the working directory triggers a one-time approval dialog for
project-level files.

### `.claude/rules/`

Markdown files, one topic per file, discovered recursively including subdirectories and
symlinks.

- A rule file **without** `paths:` frontmatter loads at launch, at the same priority as
  `.claude/CLAUDE.md`.
- A rule file **with** `paths:` frontmatter (glob patterns) loads on demand, only when
  Claude reads a file matching the glob.
- `~/.claude/rules/` is the user-level equivalent and loads before project rules, so
  project rules take precedence.

This is the mechanism we want for style rules: a rule file scoped to `paths: ["**/*.md"]`
costs nothing until an agent actually opens a markdown file.

## Claude Code does not read AGENTS.md

The memory documentation states it directly: "Claude Code reads `CLAUDE.md`, not
`AGENTS.md`."

Supported workarounds:

- A `CLAUDE.md` whose first line is `@AGENTS.md`.
- `ln -s AGENTS.md CLAUDE.md`. Fails on Windows without administrator rights or
  Developer Mode.
- `/import` (needs Claude Code v2.1.213 or later) copies AGENTS.md content into
  CLAUDE.md once, and carries over MCP servers, commands, subagents and skills.
- With `CLAUDE_CODE_NEW_INIT=1`, `/init` will read AGENTS.md when generating CLAUDE.md.

**This has a direct consequence on this machine and it needs verifying before we act on
it.** The `ai-infrastructure-capital` repo is the busiest agent surface here and its
instructions live in a root `AGENTS.md` with no `CLAUDE.md` beside it. If the
documentation is accurate, none of that router file is loaded at session start. Agents
in those workspaces only see it if something tells them to open it. Verification task
is recorded in `../02-framework-design.md`.

## Skills: what loads when

Sources: `code.claude.com/docs/en/skills` and
`platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices`.

Directory precedence, highest first: enterprise
`/etc/claude-code/.claude/skills/<name>/SKILL.md`, then personal
`~/.claude/skills/<name>/SKILL.md`, then project `.claude/skills/<name>/SKILL.md`
(which also loads from nested `.claude/skills/` in every parent directory up to the
repo root, and from `--add-dir` paths), then plugin skills (namespaced
`plugin-name:skill-name`, so they never conflict). Enterprise, personal and project
skill directories support symlinks.

**Symlink support is what makes a single source repo viable.** A skill can live in this
repo and be symlinked into `~/.claude/skills/`.

### Loading behaviour

- At startup, only the name and description of every discoverable skill load — the
  "listing". It is budgeted at **1% of the model's context window**
  (`skillListingBudgetFraction`, overridable with the `SLASH_COMMAND_TOOL_CHAR_BUDGET`
  environment variable). Over budget, Claude Code drops descriptions starting with the
  least-invoked skills. Names always remain.
- On invocation, whether by `/name` or automatic trigger, the full `SKILL.md` body loads
  and stays in context for the rest of the conversation.
- Bundled reference files and scripts do not load automatically. They enter context only
  when Claude follows a markdown link to them, and for scripts only the stdout costs
  tokens, not the source. This is the documented progressive-disclosure mechanism.
- After compaction, skills re-attach within a **25,000-token combined budget**, keeping
  the first **5,000 tokens per skill**, and least-recently-used skills may drop entirely.

### Two frontmatter specs that must not be conflated

Claude Code's own spec accepts: `name`, `description`, `when_to_use`, `argument-hint`,
`arguments`, `disable-model-invocation`, `user-invocable`, `context`, `agent`,
`background`, `model`, `effort`, `allowed-tools`, `disallowed-tools`, `paths`, `shell`,
`hooks`, `metadata`, `license`, `compatibility`. All optional; only `description` is
recommended. `description` and `when_to_use` together are capped at 1,536 characters in
the listing (`skillListingMaxDescChars`).

The Agent Skills spec, which governs claude.ai uploads and the Skills API, accepts only
`name`, `description`, `license`, `compatibility`, `metadata` and `allowed-tools`.
`name` is capped at 64 characters, lowercase letters, numbers and hyphens only, and may
not contain "anthropic" or "claude". `description` is capped at 1,024 characters.
Including a Claude-Code-only field such as `disable-model-invocation` is a hard
packaging error there.

If we ever want a skill to work both in Claude Code and uploaded to claude.ai, it has
to stay inside the smaller field set.

### Size guidance

Keep the `SKILL.md` body under 500 lines. Split anything longer into reference files one
level down from `SKILL.md`, and avoid nested reference chains — Claude may only
partially read a deeply nested file.

## Plan mode and the `/goal` command

Sources: `code.claude.com/docs/en/permission-modes`, `.../tools-reference`,
`.../common-workflows`, `.../goal`.

### Plan mode

Entered by cycling `Shift+Tab` (`default → acceptEdits → plan → default`), by
prefixing a prompt with `/plan`, or with `claude --permission-mode plan`. It can be
made the session default with `defaultMode: "plan"` in `.claude/settings.json`, or
`claudeCode.initialPermissionMode` in the VS Code extension.

In plan mode Claude reads files and runs read-only shell commands but cannot edit
files. Edits stay blocked until the plan is approved. In a bypass-permissions session
the block is instruction-only, not enforced. Shell commands outside the built-in
read-only set prompt for approval unless auto mode's classifier is reviewing them
(`useAutoModeDuringPlan`, on by default).

The `ExitPlanMode` tool presents the plan for approval and exits plan mode. Approving
switches the session into an editing permission mode.

**Relevance to the drift problem:** `defaultMode: "plan"` is a settings-level way to
force the discovery-before-execution sequence Roald wants, without relying on the model
choosing to plan first.

### `/goal`

`/goal [condition|clear]` sets a completion condition for the session. After every turn
a small fast model — Haiku by default on the Anthropic API — reads the transcript and
returns one of: not yet met, met, or impossible. It is implemented as a session-scoped
prompt-based Stop hook.

**This is the closest thing Claude Code ships to a built-in anti-drift mechanism**, and
nothing else in the documented feature set does the same job. There is no other
generator-evaluator loop as a named built-in.

Open question for the design: whether a `/goal` condition can be set programmatically at
session start, for example from a hook or a skill, rather than typed by hand.

## Context management

Sources: `code.claude.com/docs/en/commands`, `.../costs`, `.../model-config`,
`.../settings-reference`, `.../env-vars`, `.../hooks`.

- `/compact [instructions]` summarises the conversation to free context. Trailing text
  becomes focus instructions for the summary.
- `/context [all]` renders current context usage as a grid with optimisation
  suggestions. `all` expands the per-item breakdown.
- `autoCompactEnabled` (boolean, settings.json) switches automatic compaction on and
  off. Manual `/compact` still works when it is off.
- `autoCompactWindow` (100,000 to 1,000,000 tokens) sets how full the window gets before
  auto-compaction fires. Settable with `/autocompact <value>`, the `--autocompact` flag,
  or `CLAUDE_CODE_AUTO_COMPACT_WINDOW`, which takes highest precedence.
- With no window set, compaction happens at the model's context limit, except that
  Sonnet 4.6, Opus 4.6, Opus 4.8 and Opus 5 on a 200K window compact at 200K, and
  Sonnet 5 compacts at roughly 967K.
- `DISABLE_AUTO_COMPACT=1` disables automatic compaction only. `DISABLE_COMPACT=1`
  disables both automatic and manual. `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` (1 to 100) can
  lower, never raise, the percentage trigger.
- The `PreCompact` hook takes matcher values `manual` and `auto`, and receives `trigger`
  and `custom_instructions`. Exit code 2 or `decision: block` blocks compaction.

**Relevance to the drift problem:** compaction is where a plan gets lost. A `PreCompact`
hook that forces the summary to carry the plan file path and the current step is a
concrete, cheap anti-drift mechanism. Confidence that this works is untested; it is on
the verification list.

The term "microcompaction" does not appear in the official documentation. Treat it as
unconfirmed.

### Context windows, September 2026

| Model | API ID | Context window |
|---|---|---|
| Claude Opus 5 | `claude-opus-5` | 1M tokens, default, no beta header |
| Claude Sonnet 5 | `claude-sonnet-5` | 1M tokens, always |
| Claude Fable 5.1 | `claude-fable-5-1` | 1M tokens |
| Claude Haiku 4.5 | `claude-haiku-4-5-20251001` | 200K tokens |

Legacy but available: Fable 5, Opus 4.8, 4.7, 4.6, 4.5, Sonnet 4.6 and 4.5. Older
models needing extended context use the `[1m]` alias suffix, for example
`/model opus[1m]`. `CLAUDE_CODE_DISABLE_1M_CONTEXT=1` forces a 200K cap.

Roald's Conductor default is `claude:opus-5-1m`, so every workspace is already on a
1M-token window.

### API context editing

Not used by Claude Code, which implements its own client-side compaction. Recorded here
only so nobody confuses the two. Beta header `context-management-2025-06-27`, request
field `context_management.edits[]`, edit type `clear_tool_uses_20250919`, with `trigger`,
`keep`, `clear_at_least`, `exclude_tools` and `clear_tool_inputs`.
