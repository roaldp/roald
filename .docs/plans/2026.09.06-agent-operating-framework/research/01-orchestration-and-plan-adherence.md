# Research: Orchestration and Plan Adherence for Claude Code agents

Research date: 2026-09-06. Scope: what actually keeps a long-running Claude Code / Claude Desktop
agent faithful to an agreed plan on a single developer machine.


## Sources table

| Title | Author / org | Date | Rating | Reason |
|---|---|---|---|---|
| [Harness Design for Long-Running Application Development](https://www.anthropic.com/engineering/harness-design-long-running-apps) | Anthropic Engineering | 2026-03-24 | STRONG | Primary vendor engineering post with real runs, wall-clock times and dollar costs for each harness variant. |
| [cwc-long-running-agents](https://github.com/anthropics/cwc-long-running-agents) | Anthropic (Code with Claude 2026 demo) | 2026 (event demo) | STRONG | Actual runnable code: hooks, evaluator subagent, contract file. Not a blog claim — you can read the shell scripts. Caveat: explicitly unmaintained. |
| [Scaling Managed Agents: Decoupling the brain from the hands](https://www.anthropic.com/engineering/managed-agents) | Anthropic Engineering | 2026-04-08 | STRONG | Primary source, production system, reports P50/P95 latency deltas. Infra-oriented, less directly about plan adherence. |
| [OrchestraBench: Evaluating Multi-Agent Orchestration Failure Modes, Recovery, and Decomposition Quality](https://arxiv.org/html/2608.05263) | Chen, Gu, Vidra, Setty, Zheng (Anote) | 2026-08-05 | MODERATE | Quantitative, seed-reproducible failure injection with N per experiment. Downgraded from STRONG because the authors admit the experiments ran a single Claude agent over arithmetic chains, not a real multi-agent system. |
| [Spec Kit Agents: Context-Grounded Agentic Workflows](https://arxiv.org/html/2604.05278v1) | Taghavi, Bhavani | 2026-04-07 | STRONG | 128 runs, 32 features, 5 real repos, ablation table, blinded human preference votes, SWE-bench Lite numbers. |
| [Claude Code anti-patterns: what to stop doing](https://www.aicodex.to/articles/claude-code-antipatterns) | AI Codex (no byline) | undated | WEAK | No author, no date, no data. Curated best-practice listicle; useful only as a signal of what advice is circulating. |

| [How Claude remembers your project (memory docs)](https://code.claude.com/docs/en/memory) | Anthropic, Claude Code docs | current (fetched 2026-09-06) | STRONG | Official product documentation; states load order, size limits and AGENTS.md handling explicitly. |
| [Subagents docs](https://code.claude.com/docs/en/sub-agents) | Anthropic, Claude Code docs | current | STRONG | Official; enumerates every frontmatter field, what loads at subagent startup, nesting and concurrency limits. |
| [Explore the context window](https://code.claude.com/docs/en/context-window) | Anthropic, Claude Code docs | current | STRONG | Official; contains the "what survives compaction" table, which is the single most decision-relevant artefact here. |
| [Skills docs](https://code.claude.com/docs/en/skills) | Anthropic, Claude Code docs | current | STRONG | Official; states exactly what is always in context vs loaded on invocation, plus budgets. |
| [Hooks reference](https://code.claude.com/docs/en/hooks) | Anthropic, Claude Code docs | current | STRONG | Official; full event list and JSON contracts. |
| [Choose a permission mode](https://code.claude.com/docs/en/permission-modes) | Anthropic, Claude Code docs | current | STRONG | Official; plan mode semantics including the bypassPermissions carve-out. |
| [planning-with-files](https://github.com/OthmanAdi/planning-with-files) | Ahmad Othman Ammar Adi | v3.16.1, benchmarks dated 2026-03-06 and 2026-07-06 | MODERATE | Real installable code with published A/B numbers and large adoption (~26.6k stars), but the benchmarks are run and reported by the tool's own author with no independent replication. |
| [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) | Anthropic Engineering | 2025-09-29 | STRONG (older) | Foundational and still the reference framing for compaction / note-taking / sub-agents. Pre-dates Opus 4.6+; no measured numbers. |
| [How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system) | Anthropic Engineering | 2025-06 | STRONG (older) | Foundational orchestrator-worker source with the 90.2% and ~15x token figures. Research domain, not coding; pre-Opus-4.5. |
| [Claude Code Anti-Patterns: Team Adoption Failure Modes](https://www.digitalapplied.com/blog/claude-code-anti-patterns-team-adoption-failure-modes-2026) | digitalapplied | 2026 | WEAK | Listicle format, no traces or measurements; overlaps heavily with other SEO content on the same keywords. |
| Assorted 2026 "Claude Code best practices / subagents 2026" posts (totalum.app, ayautomate, nimbalyst, fast.io, mcp.directory, saascity, claudedirectory, tygartmedia, techsy, claude-world) | various | 2026 | WEAK | Same keyword cluster, mutually copied, no evidence. Not cited below except to note what advice is circulating. |

Older sources are marked "(older)" where used.

---

## 1. Plan adherence and drift

### What the drift actually is

Three distinct failure modes get called "drift" and they need different fixes.

1. **Instruction eviction.** Long sessions push the original brief out of the attention window. Anthropic's
   own context-engineering post (2025-09-29, older) names this "context rot": recall degrades as token
   count rises, before the hard limit is reached.
2. **Compaction loss.** When the context window fills, Claude Code summarises the conversation. Anything
   that existed only as conversation is summarised away.
3. **Silent scope creep.** The agent keeps working but on a task adjacent to the one agreed, and nothing
   in the loop checks the work against the agreed definition of done.

### Mechanism A: put the plan on disk, not in the conversation

This is the best-supported single technique, and it is now partly native.

The Claude Code context-window docs give an explicit table of what survives compaction. The rows that
matter:

| Content | After compaction |
|---|---|
| Project-root `CLAUDE.md` and unscoped `.claude/rules/*.md` | Re-injected from disk |
| Auto memory (`MEMORY.md`) | Re-injected from disk |
| **The plan Claude wrote in plan mode** | **Re-injected from disk** |
| Rules with `paths:` frontmatter | Reloaded only when Claude next reads a matching file |
| Nested `CLAUDE.md` in subdirectories | Reloaded only when Claude next reads a file there |
| Files Claude read or edited | Up to five re-read, most recently modified first |
| Invoked skill bodies | Re-injected, capped 5,000 tokens per skill, 25,000 total, oldest dropped |
| Context that hooks added earlier | Summarised away with the rest of the conversation |
| `SessionStart` hooks matching source `compact` | Re-run, output added to compacted context |

Two consequences follow directly and are not obvious:

- A plan produced through **plan mode** already gets re-injected from disk after compaction. A plan
  produced by asking Claude to "write a plan" in normal chat does not.
- **Context injected by a hook is not durable.** If you write a `UserPromptSubmit` hook that re-injects
  the plan, its output is part of message history and gets summarised away at the next compaction.
  The durable re-injection point is a `SessionStart` hook with `matcher: "compact"`, which the docs
  document as a supported pattern ("re-inject context after compaction").

Corroboration outside Anthropic: `planning-with-files` (MODERATE) implements exactly this shape — three
gitignored markdown files at the project root (`task_plan.md` with phase checkboxes, `findings.md`,
`progress.md`), re-read from disk via `SessionStart`, `UserPromptSubmit` and `PreCompact` hooks. Its
self-reported benchmarks: 96.7% assertion pass rate with the skill vs 6.7% without (claude-sonnet-4-6,
2026-03-06), and 5.0 vs 13.3 average turns to resume after a deliberate context wipe (77/77 runs,
2026-07-06). Treat the magnitudes as unverified — the author ran the benchmark on their own tool — but
the direction agrees with Anthropic's documented compaction behaviour, so the mechanism is
two-source; the effect size is single-source.

Anthropic's `cwc-long-running-agents` demo repo (STRONG, but explicitly unmaintained) uses the same
pattern under different names: `PROGRESS.md` as agent-maintained handoff notes, re-read on restart,
plus git commits as the durable record.

### Mechanism B: a machine-checkable contract file, default-FAIL

The strongest anti-drift device in the Anthropic demo repo is not a prompt at all. It is
`test-results.json`:

```json
{ "feature-1": { "passes": false }, "feature-2": { "passes": false } }
```

Every feature starts `false`. The loop condition is literally
`while grep -q '"passes": false' test-results.json`. The agent cannot end the run by asserting it is
done; it ends when a file the agent must justify editing says so.

That justification is enforced by two hooks:

- `track-read.sh` (PostToolUse) increments a counter at `.claude/.evidence-reads` when the agent Reads
  a file matching an evidence pattern (screenshots, logs, test output).
- `verify-gate.sh` (PreToolUse) **denies** any Write to `test-results.json` when the evidence counter is
  zero, then resets the counter after each gated write.

So "mark this feature passing" is only reachable through "open the evidence first". This is a
deterministic gate in the harness, not an instruction the model can rationalise past. The Claude Code
memory docs make the same point in the abstract: "Claude treats them as context, not enforced
configuration. To block an action regardless of what Claude decides, use a PreToolUse hook instead."
Two independent sources, one of them the vendor's own docs. Well supported.

### Mechanism C: fresh-context evaluator as a separate agent

Both Anthropic sources use a grader that has never seen the generator's reasoning.

- `cwc-long-running-agents`: `.claude/agents/evaluator.md`, a subagent with **no Write or Edit tools**,
  invoked as `claude --agent evaluator -p "Review the most recent commit against its spec."` Verdict
  `PASS` or findings written to `NEXT_FINDINGS.md`, which becomes the next session's prompt.
- Harness Design for Long-Running Application Development (2026-03-24): a three-agent split of
  planner / generator / evaluator, where the evaluator drives the running app through Playwright MCP
  and scores against a weighted rubric rather than binary pass/fail.

Reported effect, from the harness-design post: on a "Retro Game Maker" task with Opus 4.5, a solo run
took ~20 minutes and $9 and produced a broken game; the full harness took ~6 hours and $200 and
produced a working, polished application. A later DAW build on Opus 4.6 took ~3h50m and $124.70. These
are single-project anecdotes from the vendor, not a benchmark — the direction is credible, the
magnitude is not generalisable, and the cost ratio (~22x) is the number to remember.

The point about the evaluator being context-fresh matters mechanically: per the subagents docs, a
non-fork subagent starts with the agent's own system prompt, the delegation prompt, and CLAUDE.md — but
**no conversation history, no files already read, no auto memory**. It cannot inherit the generator's
rationalisations. A `fork` subagent, by contrast, inherits the entire parent conversation and so is
useless as an independent grader.

### Mechanism D: plan-mode / execute-mode separation

Native and cheap, with one important caveat for this machine.

Plan mode is entered with `Shift+Tab` or by prefixing a prompt with `/plan`, or `claude
--permission-mode plan`, or `defaultMode: "plan"` in `.claude/settings.json`. Claude reads and explores
but edits stay blocked until you approve. `Ctrl+G` opens the proposed plan in your editor so you can
edit it before approving.

**Caveat, from the official permission-modes docs:** "In sessions with bypass permissions available,
Claude Code also doesn't enforce plan mode's blocks. Claude is still instructed to plan without editing,
but a file edit or shell command it attempts during planning runs without prompting." If this machine
runs with bypass permissions, plan mode degrades from an enforced gate to a suggestion. That is a
direct conflict between the workflow advice in every practitioner post ("always use plan mode") and how
the tool actually behaves under the permission mode many power users run.

### Mechanism E: validation gates between phases (spec-driven development)

The cleanest quantitative evidence for phase gates is Spec Kit Agents (arXiv 2604.05278, 2026-04-07),
128 runs over 32 features across FastAPI, Airflow, Dexter, Plausible and Strapi. The workflow is
Specify → Plan → Tasks → Implement with two hook classes at phase boundaries:

- **Discovery hooks (pre-phase):** read-only probing of the repo — file layouts, conventions,
  dependencies, git history — before each stage.
- **Validation hooks (post-phase):** check `SPEC.md`, `PLAN.md`, `TASKS.md` for structural consistency
  and repository compatibility, then run project checks (pytest, linters) after implementation.

Ablation, LLM-as-judge composite on 1–5:

| Condition | Quality | Δ vs Full baseline (3.51) | Time |
|---|---|---|---|
| Discovery-only | 3.53 | +0.57% | 25.5 min |
| Validation-only | 3.57 | +1.71% | 31.2 min |
| Full-Augmented | 3.66 | +4.27% | 37.2 min |

Blinded human preference on paired tasks: 33 Full-Augmented, 19 Full, 8 ties (n=60). SWE-bench Lite:
58.2% Pass@1 with augmentation vs 56.5% baseline.

**Read this honestly: the effect is small.** +0.15 on a 5-point scale and +1.7pp on SWE-bench Lite are
statistically significant but modest, and the augmented runs took ~46% longer. The wider claims
circulating about SDD — "3–10x higher first-pass success", "60–80% fewer rework cycles" — trace to
vendor marketing (GitHub, AWS Kiro) and unattributed "community reports", not to measurement. Where a
controlled study exists it reports single-digit percentage gains. Note the disagreement rather than
splitting the difference.

### Mechanism F: todo / checklist tools — the advice has changed

Claude Code has task tracking tools: `TaskCreate`, `TaskGet`, `TaskList`, `TaskUpdate` (v2.1.233+),
replacing the deprecated `TodoWrite`. But per the official tools reference, on **Opus 4.8, Sonnet 5,
Fable 5, Mythos 5 and later these tools are disabled by default**, on the stated grounds that these
models "keep track of multi-step work without a written checklist". You opt back in with
`CLAUDE_CODE_ENABLE_TODO_TOOLS=1`, `--allowedTools TaskCreate`, or `--tools`.

This contradicts a large body of 2025-era advice that says an in-session todo list is a primary
anti-drift device. Anthropic's position is now that the in-session checklist is redundant on current
models. Note that this says nothing about the *on-disk* plan file, which serves a different purpose
(surviving compaction and session restarts) and which Anthropic's own harness examples still use.

### Mechanism G: steering and kill-switch files

From `cwc-long-running-agents`, two small operator controls worth copying:

- `steer.sh` — a hook that reads `STEER.md` if present, surfaces it to the agent, then clears it. Gives
  you a way to redirect a running unattended agent without interrupting it.
- `kill-switch.sh` — blocks all tool calls while a file named `AGENT_STOP` exists at the project root.

Single-sourced (Anthropic demo repo only), but trivially cheap and the mechanism is obvious.

---

## 2. Orchestrator + subagent architectures

### The two sources genuinely disagree

This is the sharpest disagreement in the material and it should not be smoothed over.

**Anthropic (2025-06, older), How we built our multi-agent research system:** an orchestrator-worker
system with Opus 4 lead and Sonnet 4 subagents outperformed single-agent Opus 4 by **90.2%** on their
internal research eval. Token usage alone explained **80% of performance variance**. Cost: agents use
~4x the tokens of chat; multi-agent uses ~15x.

**Cognition (2025-06-12, older), Don't Build Multi-Agents:** parallel subagents make independent
decisions on the same problem and those decisions conflict. Their example: split a Flappy Bird clone
across two subagents and you get a Super Mario background with a mismatched bird. Their principles are
(1) share full agent traces, not individual messages, and (2) actions carry implicit decisions.
Recommendation: single-threaded linear agent; if context runs out, use a dedicated model to compress
history into key decisions and events, not a subagent swarm.

**The disagreement resolves on task shape, and both sources actually say so.** Anthropic's own post
states multi-agent suits "heavy parallelization, information that exceeds single context windows, and
interfacing with numerous complex tools", and explicitly warns that "most coding tasks involve fewer
truly parallelizable tasks than research" and that multi-agent is poor where agents need shared context
or have many inter-dependencies. Cognition observes that Claude Code itself uses subagents only for
read-only investigation, not parallel writing. Both converge on:

> Fan out for **reading**. Keep **writing** single-threaded.

That convergence is the strongest cross-verified claim in this document, from two sources that
otherwise disagree.

### Quantitative failure-mode data

OrchestraBench (arXiv 2608.05263, 2026-08-05) injected five MAST-derived failure modes and measured
recovery. Rate this MODERATE and read the limitation first: **the authors state their experiments used
a single Claude agent over arithmetic chains, not a true multi-agent system** — a mechanism probe, not
production validation.

With that caveat:

- **Recovery by failure mode (N=150):** tool-invocation faults recover at 1.0. Ambiguous delegation
  recovers at 0.30. Latent/semantic failures — context pollution, conflicting sub-agent outputs,
  premature action — recover at **0.0**. They never self-correct.
- **Cascade radius by pipeline depth (N=750):** 0.93 at depth 3, rising 1.85 → 2.80 → 3.63 → 4.67 at
  depth 7. Roughly one additional contaminated agent per extra pipeline stage.
- **Decomposition quality (N=40):** an explicit decompose policy gave 1.0 delegation fidelity and 0.0
  granularity error; a monolithic prompt gave 0.37 fidelity and 2.0 granularity error (p<0.001).
- **Routing:** keyword-heuristic routing scored 0% on adversarial cases with misleading flags;
  model-driven routing and a TF-IDF description reader both scored 100%.
- **Retry is useless for the modes that matter:** "retry does not repair the latent modes... only
  lengthens time-to-detection." The paper's conclusion is that "detection and attribution, not blind
  retry, is the necessary containment mechanism."

Practical reading: **keep pipelines shallow.** Depth is the variable that multiplies damage, and the
failures that cascade are precisely the ones that never self-heal.

### Cost data

Reported figures, all single-sourced and not directly comparable:

- ~15x tokens vs chat for Anthropic's multi-agent research system (2025-06, older).
- 29,000 tokens for a three-agent pipeline vs 10,000 for the equivalent single agent — from
  prefactor.tech (WEAK: vendor blog, no methodology given). Cited only as an order-of-magnitude
  indication that matches Anthropic's direction.
- ~$9 solo vs ~$200 full harness on the same task in Anthropic's harness-design post — a ~22x cost
  ratio for a build that went from broken to working.

There is a directly contradictory figure circulating ("single-agent executions consume nearly twice
the tokens of multi-agent, 121K vs 63K"). I could not trace it to a methodology and do not recommend
relying on it.

### Handoff artefacts: what works

The appendix of Anthropic's multi-agent post describes the pattern most relevant here:

> "Rather than requiring subagents to communicate everything through the lead agent, implement artifact
> systems where specialized agents can create outputs that persist independently... Subagents call tools
> to store their work in external systems, then pass lightweight references back to the coordinator."

Stated benefits: avoids information loss across multi-stage processing (the "game of telephone"), and
avoids token overhead from copying large outputs through conversation history.

The delegation prompt itself, per the same post, needs four things: **an objective, an output format,
guidance on tools and sources, and clear task boundaries.** Their scaling heuristic:

| Task | Subagents | Tool calls each |
|---|---|---|
| Simple fact-finding | 1 | 3–10 |
| Direct comparison | 2–4 | 10–15 |
| Complex research | 10+ | clearly divided responsibilities |

Their documented early failures were the mirror image of this: spawning excessive subagents for simple
queries, and duplicated searches from an unclear division of labour — one subagent researching the 2021
automotive chip crisis while others duplicated 2025 supply-chain work.

### What Claude Code actually gives you (official docs)

Concrete constraints that shape any design here:

- A **non-fork subagent** starts with: its own system prompt, the delegation prompt, the full CLAUDE.md
  hierarchy, a git-status snapshot from parent session start, any preloaded `skills`, and a sibling
  roster for `SendMessage`. It does **not** get conversation history, files the parent read, invoked
  skills, output style, the parent's auto memory, or the parent's context window size.
- A **fork subagent** inherits the entire parent conversation, system prompt, tools and model. Use for
  "same work, separate scratchpad"; never for independent verification.
- Subagent frontmatter fields: `name`, `description` (only these two required), `tools`,
  `disallowedTools`, `model`, `permissionMode`, `maxTurns`, `skills`, `mcpServers`, `hooks`, `memory`,
  `background`, `effort`, `isolation`, `color`, `initialPrompt`, `experimental.cacheTtl`.
- Precedence when names collide: managed settings > `--agents` flag > `.claude/agents/` >
  `~/.claude/agents/` > plugin agents.
- **Nesting depth defaults to 3** below the main conversation (`CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`;
  set to 1 to disable). At the limit the `Agent` tool is withheld. **Nested subagents do not return to
  the main conversation** — only the top-level summary does.
- **Concurrency defaults to 20** (`CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`).
- There is **no schema-typed return**. The Agent tool returns a text result. Structured handoff has to
  be done by convention: have the subagent write a file and return the path.
- Subagent transcripts persist at
  `~/.claude/projects/{project}/{sessionId}/subagents/agent-{agentId}.jsonl`, so post-hoc attribution
  of a bad handoff is possible.

Note the interaction between two of these: OrchestraBench says cascade radius grows with depth, and
Claude Code's default depth is 3 with nested results not surfacing to the main conversation. Depth 3 is
already the zone where a contaminated intermediate result is invisible to you.

---

## 3. Context engineering, Opus 4.5 / Opus 5 era

### What is in the window before you type anything

From the official context-window page, with the doc's own representative token counts:

- System prompt (~4,200 tokens) — never visible to you.
- Auto memory `MEMORY.md` — first 200 lines or 25KB, whichever comes first.
- Environment info (~280 tokens); git branch/status/recent commits as a separate block at the end of
  the system prompt.
- MCP tool **names** only (~120 tokens) — full schemas stay deferred and are loaded on demand via tool
  search. `ENABLE_TOOL_SEARCH=auto` loads schemas upfront when they fit within 10% of the window;
  `ENABLE_TOOL_SEARCH=false` loads everything.
- Skill **descriptions** for every installed skill. Listing budget defaults to **1% of the context
  window** (`skillListingBudgetFraction`).
- CLAUDE.md hierarchy, plus unscoped `.claude/rules/*.md`.
- Output style and `--append-system-prompt` text, both of which go into the system prompt.

### Window sizes and compaction

- Fable 5.1, Fable 5, Sonnet 5, Opus 4.6 and later, and Sonnet 4.6 support a **1 million token** window.
  Sonnet 5 runs at 1M with no `[1m]` variant to select; others need the `[1m]` model variant.
- Auto-compact threshold varies by model; adjustable with `/autocompact 500k`.
- `/compact <instructions>` lets you steer what the summary keeps.
- `/rewind` → "Summarize from here" / "Summarize up to here" compacts part of the conversation.
- As of v2.1.198 the summarisation request inherits the session's extended-thinking setting.

I could not find, in official docs, any feature called "microcompaction" or an explicit tool-result
clearing feature in Claude Code. The Claude **API** has context-editing / tool-result clearing (see the
platform cookbook on memory, compaction and tool clearing); that is a different surface. Flagging this
as unconfirmed rather than asserting it.

### Progressive disclosure: the actual budget hierarchy

Ordered from "costs you tokens in every single session" to "costs nothing until needed":

| Layer | Loaded when | Cost |
|---|---|---|
| Managed / user / project `CLAUDE.md`, unscoped rules | Every session, at launch | Full text, always |
| `MEMORY.md` index | Every session | First 200 lines / 25KB |
| Skill descriptions | Every session | ~50–200 chars each, 1% window budget total |
| MCP tool names | Every session | Names only; schemas deferred |
| `.claude/rules/*.md` with `paths:` frontmatter | When Claude reads a matching file | Full text, on demand |
| Nested `CLAUDE.md` in subdirectories | When Claude reads a file there | Full text, on demand |
| Skill body | On invocation; then persists for the session | Keep under 500 lines |
| Skill supporting files (`reference.md`, `scripts/`) | Only if Claude reads them | Zero until read |
| Subagent definition body | Only inside that subagent | Zero in main context |

Two non-obvious rules that follow:

- `@path` **imports do not save context.** The docs are explicit: "Splitting into `@path` imports helps
  organization but doesn't reduce context, since imported files load at launch." Path-scoped rules are
  the mechanism that actually defers loading.
- **Skill body truncation after compaction keeps the start of the file.** "Truncation keeps the start of
  the file, so put the most important instructions near the top of `SKILL.md`."

### Structured note-taking

Anthropic's context-engineering post (2025-09-29, older) names three long-horizon techniques:
compaction, structured note-taking (an external `NOTES.md`-style file the agent writes and re-reads),
and sub-agent architectures returning condensed summaries of "typically 1,000–2,000 tokens" to the
coordinator. The 1,000–2,000 token figure is a useful sizing target for what a subagent should hand
back — and it is single-sourced.

---

## 4. The CLAUDE.md / AGENTS.md / skills / hooks landscape

### AGENTS.md: settled, and not the way the blogs say

The official memory docs are unambiguous:

> "Claude Code reads `CLAUDE.md`, not `AGENTS.md`."

The 2026 SEO posts on this keyword contradict each other — some assert Claude Code gained native
AGENTS.md support in June 2026. The vendor documentation as of 2026-09-06 says it did not. Believe the
docs.

The documented workarounds:

```markdown
<!-- CLAUDE.md -->
@AGENTS.md

## Claude Code

Use plan mode for changes under `src/billing/`.
```

or, if you need no Claude-specific additions, `ln -s AGENTS.md CLAUDE.md` (needs Administrator or
Developer Mode on Windows, so prefer the import there).

Two adjacent facts: `/init` with `CLAUDE_CODE_NEW_INIT=1` reads `AGENTS.md`, `.cursor/rules/`,
`.github/copilot-instructions.md`, `.devin/rules/`, `.windsurf/rules/` and `.clinerules` when generating
CLAUDE.md. `/import` (v2.1.213+) appends a one-time copy of another agent's instruction files and
carries over MCP servers, commands, subagents and skills.

Separately, AGENTS.md as a cross-tool standard is real and widely adopted (reported 60,000+ GitHub
repos, stewarded by the Agentic AI Foundation) — but every claim I found about its provenance and
adoption numbers came from SEO content that also got the Claude Code support question wrong. Treat the
adoption figures as unverified.

### CLAUDE.md load order and limits

Load order runs broadest to most specific, so later files are read last:

1. Managed policy — macOS `/Library/Application Support/ClaudeCode/CLAUDE.md`, Linux/WSL
   `/etc/claude-code/CLAUDE.md`, Windows `C:\Program Files\ClaudeCode\CLAUDE.md`. Cannot be excluded.
   Also settable inline as the `claudeMd` key in `managed-settings.json`.
2. User — `~/.claude/CLAUDE.md`, then `~/.claude/rules/`.
3. Project — `./CLAUDE.md` or `./.claude/CLAUDE.md`, plus `.claude/rules/`.
4. Local — `./CLAUDE.local.md`, appended after `CLAUDE.md` at the same level.

Across the directory tree, content is ordered from filesystem root down to the working directory. All
discovered files are **concatenated, not overridden**.

Hard numbers from the docs:

- **Target under 200 lines per CLAUDE.md.** "Longer files consume more context and reduce adherence."
- A CLAUDE.md up to **4 MiB** loads in full; larger is skipped entirely.
- `@path` imports resolve to a **maximum depth of four hops**, and skip code spans and fenced blocks.
- `.claude/rules/*.md` without `paths:` load at launch with the same priority as `.claude/CLAUDE.md`.
- `paths:` glob expansion has a budget of **1,000 expanded patterns and 4 MiB** per rule.
- Block-level HTML comments in CLAUDE.md are **stripped before injection** — free space for human
  maintainer notes.
- `claudeMdExcludes` (glob, any settings layer, arrays merge) skips other teams' files in monorepos.
- `/doctor` (v2.1.206+) proposes trims: it cuts what Claude can derive from the codebase (directory
  layouts, dependency lists, architecture overviews) and keeps pitfalls, rationale, and conventions
  that differ from tool defaults. That is a good editorial rule to apply by hand.

The docs are also explicit about the ceiling on this mechanism:

> "CLAUDE.md content is delivered as a user message after the system prompt, not as part of the system
> prompt itself. Claude reads it and tries to follow it, but there's no guarantee of strict compliance."

And the escalation path: "If the instruction is something that must run at a specific point, such as
before every commit or after each file edit, write it as a hook instead."

### Skills

Layout `~/.claude/skills/<name>/SKILL.md`, `.claude/skills/<name>/SKILL.md`, or
`<plugin>/skills/<name>/SKILL.md`. Invoked as `/<directory-name>`.

Frontmatter fields that matter for this framework: `description` (always in context),
`disable-model-invocation: true` (you only), `user-invocable: false` (Claude only),
`allowed-tools` (pre-approve tools for the turn), `context: fork` + `agent:` + `background:` (run the
skill as a subagent), `arguments: [...]`, `paths: [glob, ...]`.

Loading: description always in context; body added on invocation and **stays in context for the rest of
the session**; after compaction the body is re-injected truncated to 5,000 tokens per skill within a
25,000-token shared budget, oldest dropped first. Keep SKILL.md under ~500 lines and push detail into
sibling files that are only read when needed.

Skills can also run shell commands before their content reaches Claude, via `` !`git diff HEAD` `` or a
```` ```! ```` fenced block. Failed commands abort the whole invocation. Useful for a
"re-anchor on current state" skill.

`skillOverrides` in `.claude/settings.json` supports `"on"`, `"name-only"`, `"user-invocable-only"`,
`"off"` — the tool for skill sprawl, since every installed skill's description is charged to the 1%
listing budget every session. `/skill-doctor` finds unused skills.

### Slash commands vs skills

Skills have absorbed most of what slash commands did: they are user-invocable as `/<name>`, take
`$ARGUMENTS` / `$0` / `$1` / named arguments, and can run shell commands. The meaningful remaining
distinction is that a skill also carries a `description` that Claude sees, so Claude can invoke it
itself. If you never want Claude to auto-invoke, set `disable-model-invocation: true` — which also
removes the description from context, making it free.

Output styles still exist and go into the system prompt; the docs list them as surviving compaction
unchanged. I found no deprecation notice.

### Hooks: the full event list as of now

`SessionStart`, `Setup`, `UserPromptSubmit`, `UserPromptExpansion`, `PreToolUse`, `PermissionRequest`,
`PermissionDenied`, `PostToolUse`, `PostToolUseFailure`, `PostToolBatch`, `Notification`,
`MessageDisplay`, `SubagentStart`, `SubagentStop`, `TaskCreated`, `TaskCompleted`, `Stop`,
`StopFailure`, `TeammateIdle`, `InstructionsLoaded`, `ConfigChange`, `CwdChanged`, `DirectoryAdded`,
`FileChanged`, `WorktreeCreate`, `WorktreeRemove`, `PreCompact`, `PostCompact`, `PreModelSwitch`,
`PostModelSwitch`, `Elicitation`, `ElicitationResult`, `SessionEnd`.

The three JSON contracts this framework needs:

Deny a tool call:
```json
{ "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Write to plan contract blocked: no evidence file read this cycle." } }
```

Inject context (available on `UserPromptSubmit`, `SessionStart`, `Stop`, `SubagentStop`, others):
```json
{ "hookSpecificOutput": { "additionalContext": "..." } }
```

Refuse to let the turn end:
```json
{ "hookSpecificOutput": {
    "hookEventName": "Stop",
    "permissionDecision": "deny",
    "permissionDecisionReason": "task_plan.md still has an in_progress phase." } }
```

Exit code 2 blocks regardless of JSON, using `permissionDecisionReason` or stderr as the message.

`SessionStart` matchers: `startup`, `resume`, `clear`, `compact`, `fork`. The `compact` matcher is the
durable post-compaction re-injection point.

`InstructionsLoaded` matchers: `session_start`, `nested_traversal`, `path_glob_match`, `include`,
`compact`. This is the instrument for auditing what actually loaded, and is worth wiring up once before
tuning anything else.

Hooks can be configured in `~/.claude/settings.json`, `.claude/settings.json`,
`.claude/settings.local.json`, managed policy, plugin `hooks/hooks.json`, **skill frontmatter**
(registered while the skill runs), and **subagent frontmatter** (removed when the subagent finishes).
Those last two are the mechanism for scoping enforcement to a phase rather than the whole session.

---

## 5. Anti-patterns

Rated honestly: the anti-pattern literature is the weakest part of this corpus. The 2026 "Claude Code
anti-patterns" posts are an SEO cluster with no author bylines, no dates, no traces and heavy mutual
copying. Where their claims coincide with vendor documentation I have cited the documentation instead.

**Supported by vendor documentation:**

- **Over-stuffed CLAUDE.md.** Official: target under 200 lines; "longer files consume more context and
  reduce adherence"; `/doctor` exists specifically to trim it. The widely-repeated "200 line" figure in
  blog posts is just this doc line being restated, so treat it as one source, not many.
- **Contradictory instructions.** Official: "if two rules contradict each other, Claude may pick one
  arbitrarily." Review nested CLAUDE.md files and rules periodically.
- **Using CLAUDE.md for things that must happen.** Official: CLAUDE.md is context, not configuration;
  use a hook or `permissions.deny`. This is the single most repeated point in the official docs and the
  most commonly ignored in practice.
- **Assuming `@path` imports reduce context.** They do not.
- **Skill sprawl.** Every installed skill's description is charged to a 1%-of-window listing budget every
  session, and descriptions get cut short when the budget is exceeded. `/skill-doctor` and
  `skillOverrides: "off"` are the remedies.
- **Deep pipelines.** OrchestraBench: cascade radius 0.93 at depth 3 → 4.67 at depth 7.
- **Blind retry as an error strategy.** OrchestraBench: retry does not repair latent failure modes, it
  only delays detection.
- **Spawning subagents for simple queries; unclear division of labour.** Anthropic's own documented
  early failures in the research system.
- **Parallel subagents that write.** Cognition's core argument; consistent with Anthropic's caution that
  most coding tasks are less parallelisable than research.

**Circulating but unsupported by any source I could verify:**

- "Claude Code now reads AGENTS.md natively." Contradicted by official docs.
- "SDD gives 3–10x first-pass success" / "60–80% fewer rework cycles." Vendor marketing and
  unattributed community claims. The one controlled study reports +4.3% composite quality and +1.7pp on
  SWE-bench Lite.
- "Single-agent uses twice the tokens of multi-agent (121K vs 63K)." Untraceable methodology; conflicts
  with Anthropic's own ~15x figure in the other direction.

---

## Recommended for this machine

Current state, checked 2026-09-06: Claude Code **2.1.261**. `~/.claude/` has `CLAUDE.md`, `agents/`
(two subagents), `commands/`, `skills/` (`goldfish`, `gpu-util`), `plugins/`, `settings.json`,
`settings.local.json`. **No hooks are configured in any settings file.** No `~/.claude/rules/`. The
`lima` project has a root `CLAUDE.md` (1.5KB) but no `.claude/` directory. The workflow commands
(`/create_plan`, `/implement_plan`, `/check_plan`) exist as slash commands with no enforcement behind
them.

The single largest gap is that every plan-adherence mechanism currently in use is an instruction, and
the docs are explicit that instructions are context rather than configuration. Everything below moves
one rung up from instruction to mechanism.

**R1. Write the plan to a file at a fixed path, and make the file the source of truth.**
Confidence: HIGH. Sources: Anthropic context-window docs (compaction table), `cwc-long-running-agents`
(`PROGRESS.md`), `planning-with-files` (three-file layout), Anthropic context-engineering post
(structured note-taking).
Concretely, `/create_plan` should end by writing `.docs/plans/<date>-<name>/PLAN.md` plus a machine-readable
`.docs/plans/<date>-<name>/contract.json`, and `/implement_plan` should begin by reading both. The
existing plan-directory convention in CLAUDE.md already gets you most of the way; what is missing is
that nothing reads it back.

**R2. Re-inject the plan pointer with a `SessionStart` hook matching `compact`, not with
`UserPromptSubmit`.** Confidence: HIGH. Source: Anthropic context-window docs, which state that context
hooks added earlier is "summarized with the rest of the conversation" while `SessionStart` hooks matching
`compact` are re-run and their output added to the compacted context.

```json
{ "hooks": { "SessionStart": [ { "matcher": "compact|resume|startup",
  "hooks": [ { "type": "command",
    "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/reanchor.sh" } ] } ] } }
```
where `reanchor.sh` emits `{"hookSpecificOutput":{"additionalContext":"<active plan path + current
phase + next step>"}}`. Keep it to a pointer and the current phase, not the whole plan — the plan file
is on disk and Claude can read it.

**R3. A default-FAIL contract file with a `PreToolUse` write gate.**
Confidence: HIGH for the mechanism, MEDIUM for effect size. Sources: `cwc-long-running-agents`
(`test-results.json` + `verify-gate.sh` + `track-read.sh`), Anthropic memory docs ("to block an action
regardless of what Claude decides, use a PreToolUse hook").
Every phase in `contract.json` starts `{"passes": false}`. A `PreToolUse` hook denies any Write/Edit to
`contract.json` unless a counter file shows the agent has read evidence (test output, a diff, a
screenshot) since the last gated write. This is the only mechanism in the corpus that an agent cannot
talk its way past.

**R4. A fresh-context evaluator subagent with no write tools.**
Confidence: HIGH. Sources: `cwc-long-running-agents` (`evaluator.md`), Anthropic harness-design post
(planner/generator/evaluator split), Claude Code subagent docs (non-fork subagents get no conversation
history).
`.claude/agents/plan-auditor.md` with `tools: Read, Grep, Glob, Bash` and
`disallowedTools: Write, Edit`. Its job is one question: does the diff satisfy the phase's acceptance
criteria in `contract.json`, yes or no, and if no, what is missing. Findings go to a file that becomes
the next phase's prompt. Must be a plain subagent, never `context: fork` — a fork inherits the
generator's reasoning and cannot audit it.

**R5. Fan out for reading, stay single-threaded for writing.**
Confidence: HIGH. Sources: Anthropic multi-agent research post (which itself warns coding tasks are
less parallelisable than research) and Cognition's "Don't Build Multi-Agents" — two sources that
disagree about almost everything else and agree on this.
Research, codebase exploration and review fan out. Implementation does not. Set
`CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=2` unless you have a specific reason for deeper nesting;
OrchestraBench shows cascade radius roughly doubling from depth 3 to depth 5, and Claude Code does not
surface nested subagent results to the main conversation anyway.

**R6. Subagent briefs must carry four fields, and hand back a file path.**
Confidence: MEDIUM-HIGH. Sources: Anthropic multi-agent post (objective / output format / tool and
source guidance / task boundaries; and the artifact-system appendix), corroborated in shape by
OrchestraBench's decomposition result (explicit decompose policy: 1.0 delegation fidelity vs 0.37
monolithic).
Because Claude Code has no schema-typed return, enforce this by convention: the brief names an output
file path, the subagent writes it, and returns a ~1,000–2,000 token summary plus the path. This keeps
large intermediate output out of the orchestrator's window and gives you an auditable artefact.

**R7. Move `.claude/rules/` path-scoped rules in, and trim the root CLAUDE.md.**
Confidence: HIGH. Source: Anthropic memory docs (under 200 lines; `@path` imports do not reduce
context; `paths:` frontmatter defers loading; `/doctor` trim heuristic).
The current project CLAUDE.md is already short, so this is preventive. The rule to hold to: anything
that only matters when touching a particular area gets `paths:` frontmatter and lives in
`.claude/rules/`; anything procedural becomes a skill; only always-true facts stay in CLAUDE.md. Be
aware that `paths:`-scoped rules do **not** survive compaction — they reload only when a matching file
is next read. Anything that must always hold belongs in the root CLAUDE.md.

**R8. Turn on `InstructionsLoaded` logging before tuning anything.**
Confidence: HIGH (low cost, official feature). Source: Anthropic memory and hooks docs.
Log `file_path` and `reason` (`session_start` / `nested_traversal` / `path_glob_match` / `include` /
`compact`) to a file. Combined with `/context`, this is the only way to know whether an instruction
that was ignored was actually loaded. Do this first; it makes every later decision empirical.

**R9. Do not re-enable the todo tools by default.**
Confidence: MEDIUM. Source: Claude Code tools reference (single official source), stating the task
tools are disabled by default on Opus 4.8 / Sonnet 5 / Fable 5 / Mythos 5 and later because those
models track multi-step work without a written checklist.
The on-disk plan file (R1) covers the durability need. An in-session checklist is a different thing and
Anthropic's current position is that it is redundant. If you want it back:
`CLAUDE_CODE_ENABLE_TODO_TOOLS=1`. Worth an A/B on this machine rather than taking either side on
faith.

**R10. A `STEER.md` + `AGENT_STOP` pair for unattended runs.**
Confidence: MEDIUM (single-sourced, but trivial and low-risk). Source: `cwc-long-running-agents`.
A hook that surfaces `STEER.md` once and clears it lets you redirect a running agent without killing
it; a hook that denies all tool calls while `AGENT_STOP` exists gives you a stop button that works even
when the terminal is not in front of you. Only worth building if you actually run unattended.

**Not recommended yet: plan mode as an enforcement boundary on this machine.**
Plan mode is worth using for the review-and-approve step, and its plan does get re-injected from disk
after compaction, which is a real benefit. But per the official permission-modes docs, "in sessions
with bypass permissions available, Claude Code also doesn't enforce plan mode's blocks." If you run
with bypass permissions, plan mode is advisory. Rely on the `PreToolUse` gate (R3) for enforcement, and
use plan mode for the human approval gate it genuinely provides.

---

## Explicitly rejected / unproven

- **Native AGENTS.md support in Claude Code.** Does not exist as of 2026-09-06 per official docs. Use
  `@AGENTS.md` from CLAUDE.md, or a symlink. Do not build on the blog claims that say otherwise.
- **Splitting CLAUDE.md into `@path` imports to save context.** Explicitly does not save context.
  Rejected on vendor documentation.
- **A large roster of specialist subagents.** No source supports it. Anthropic's own documented early
  failure was spawning too many subagents for simple tasks; Cognition argues against parallel writing
  subagents entirely; OrchestraBench shows cascade damage growing with depth. Add a subagent when a
  specific context-pollution or independence problem exists, not speculatively.
- **Retry loops as an error-recovery strategy.** OrchestraBench: retry recovers tool faults (rate 1.0)
  but never recovers context pollution, conflicting outputs, or premature action (rate 0.0); it "only
  lengthens time-to-detection". Detect and attribute instead.
- **The headline SDD claims (3–10x first-pass success, 60–80% less rework).** Vendor marketing and
  unattributed community reports. The one controlled study on the same idea measures +4.3% composite
  quality at +46% wall-clock time.
- **`UserPromptSubmit` re-injection as the primary durability mechanism.** It works within a session but
  its output is summarised away at compaction. `planning-with-files` uses it alongside `SessionStart`
  and `PreCompact`, which is the correct combination; using it alone is not.
- **"Microcompaction" and tool-result clearing in Claude Code.** I could not confirm either exists as a
  Claude Code feature. Context editing / tool-result clearing is documented on the Claude API surface,
  which is not the same thing. Unproven, not rejected.
- **Any specific token-cost ratio for multi-agent vs single-agent on coding work.** The figures in
  circulation (15x, 2.9x, 0.5x) come from different domains and methodologies and contradict each
  other. Measure on your own workload.

---

## Open questions

1. **Does this machine run with bypass permissions by default?** If yes, plan mode's blocks are not
   enforced and R3 becomes load-bearing rather than belt-and-braces. This determines whether the
   framework needs the hook gate on day one.
2. **What is Opus 5's status in the todo-tool default-off list?** The docs name Opus 4.8, Sonnet 5,
   Fable 5 and Mythos 5 "and later". Whether Opus 5 is covered, and what its auto-compact threshold and
   window size are, was not confirmed. Check `/context` in a live Opus 5 session.
3. **Does `planning-with-files`' 96.7%-vs-6.7% result replicate on Opus-class models?** The benchmark
   was on claude-sonnet-4-6 and is author-reported. If the effect is largely "weaker model needs an
   external scaffold", the gain on Opus 5 may be much smaller. This is worth one afternoon of
   measurement before committing to a per-turn re-injection design.
4. **Is a `Stop`-hook completion gate net positive or net annoying in interactive use?** All the
   evidence for it comes from unattended loops. A hook that refuses to let the turn end while a phase is
   `in_progress` may be actively hostile in a conversational session. `planning-with-files` makes it
   opt-in (`--gated`) with a block cap, which suggests the author found the same.
5. **Do the agent-teams features (`SendMessage`, `TeammateIdle`, sibling roster) change the
   read-fan-out / write-single-thread rule?** They give subagents a way to share context that neither
   Anthropic's 2025 post nor Cognition's had. No evidence either way; nothing found that evaluates them.
6. **How much of the root `CLAUDE.md` is actually being followed?** Unknown until `InstructionsLoaded`
   logging (R8) is on. Every other tuning decision is guesswork until then.
7. **What is the right granularity for a phase?** OrchestraBench measures granularity error but on
   arithmetic chains. Nothing in the corpus tells you whether a phase should be an hour or a day of
   agent work.
