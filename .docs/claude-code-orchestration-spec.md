# Claude Code Project Orchestration Spec

Analysis of ArthurDevel's methodology for structuring and orchestrating Claude Code projects, derived from his [Notion setup guide](https://stockman.notion.site/Claude-Code-Setup-01-02-2026-2fab0029ba85805a8f68dfd234fbaa5c) and the [voicecc](https://github.com/ArthurDevel/voicecc) reference implementation.

---

## 1. Overview

ArthurDevel uses a **workplan-driven, agent-aware** development methodology built on one core principle:

> **Codebase structure is the primary way to stay "on top" of your code.**

When planning features, he always asks for file trees, which files get edited, what files import from where. This keeps the codebase clean and understandable, even though he doesn't read 90% of the code. Being explicit about code formatting and repository conventions makes the output of the agent much more predictable.

The methodology has these pillars:

1. **User-level guidelines** — behavioral and formatting rules that apply across all projects
2. **Detailed, pre-written workplans** — not vague instructions
3. **Specialized subagents** — plan reviewer, type fixer, documentation fetcher
4. **Slash commands as workflows** — `/create_plan`, `/implement_plan` as repeatable processes
5. **Context window management** — aggressive delegation to subagents to keep the main agent's context clean

---

## 2. The Guidelines Layer (User-Level)

### 2.1 User `~/.claude/` Structure

All cross-project guidelines live in the user's home `.claude` directory, making them available across every project:

```
~/.claude/
  CLAUDE.md                    # Root behavioral contract — references the files below
  guidelines/
    claude_primer.md           # How the agent should behave (no emojis, no overengineering, etc.)
    code_formatting.md         # Explicit formatting rules for all generated code
  commands/                    # Slash commands (see Section 5)
    create_plan.md
    implement_plan.md
    ...
  agents/                      # Custom subagent definitions (see Section 4)
    plan-reviewer.md
    typescript-type-error-fixer.md
    documentation-fetcher.md
```

**Key insight:** After implementing `claude_primer.md` and `code_formatting.md`, ArthurDevel reports "one of the biggest jumps in code quality — no more overuse of emojis, way less overengineered code, and all files in a readable format so I can quickly skim."

### 2.2 Project-Level Guidelines

Individual projects add a `project_guidelines.md` (referenced by the project's CLAUDE.md) that defines:
- File location conventions (e.g., `page.tsx`, `components.tsx`, `actions.ts`, `types.ts`)
- Colocation rules (keep files together if only used in one place)
- Promotion rules (move to `lib/actions`, `lib/types`, `lib/components` when code becomes shared)

### 2.3 Hierarchy

```
~/.claude/CLAUDE.md                    → references guidelines/claude_primer.md, guidelines/code_formatting.md
  └─ project/CLAUDE.md                 → references project_guidelines.md
      └─ project/module/CLAUDE.md      → module-specific behavior (e.g., voice agent persona)
```

---

## 3. The Workplan: Core Orchestration Artifact

The workplan is the central document that drives implementation. Each workplan lives in `.docs/plans/` and follows a strict, repeatable structure.

### 3.1 Workplan Template

Every workplan contains these sections in order:

```markdown
# Feature Name

## Goal
One paragraph describing what this feature does and why. Written as a
high-level spec, not a task list. References existing architecture
where relevant (e.g., "Follows the same pattern as settings.ts").

## File Tree
Explicit list of every file that will be created (NEW) or modified (MODIFIED).
This is the scope boundary — the agent should not touch files outside this list.

## Types and Methods Per File

### path/to/file.ts (NEW|MODIFIED)

Brief description of the file's responsibility and how it fits into
the existing architecture.

#### Types
Type definitions with field-level documentation.

#### Methods
| Method | Arguments | Returns | Description |
|--------|-----------|---------|-------------|
| name   | typed args| return  | What it does|

#### Changes (for MODIFIED files)
| Change | Description |
|--------|-------------|
| What   | Why and how |

## Important Technical Notes
Numbered list of non-obvious implementation details, edge cases,
cross-process concerns, concurrency issues, and fail-safe behaviors.
These are the things an agent would get wrong without explicit guidance.

## Phases
Sequential implementation phases, each with a checkbox list of tasks.
Phases should be independently verifiable.

### Phase 1: Foundation
- [ ] Task A
- [ ] Task B

### Phase 2: Integration
- [ ] Task C

## Success Criteria
Bulleted list of observable, testable outcomes that confirm the
feature works correctly. Written from the user's perspective.
```

### 3.2 Why This Structure Works

- **File Tree** prevents scope creep — the agent knows exactly what to touch
- **Types/Methods** eliminate ambiguity — the agent doesn't have to guess interfaces
- **Technical Notes** encode senior knowledge — the tricky parts that would otherwise require multiple iterations to discover
- **Phases** enable incremental verification — you can check each phase before proceeding
- **Success Criteria** define "done" — the agent has a clear stopping point

### 3.3 What ArthurDevel Actually Reviews

He doesn't read most code, but he **does** check:
- The **file tree** — to verify structural decisions
- The **methods and types** — to confirm the implementation aligns with intent
- The **review iteration table** — to see what feedback was applied (see Section 4.1)

### 3.4 Real Examples from voicecc

**Agent Heartbeat System plan** (`.docs/plans/2026.03.05-agent-heartbeat-system.md`):
- 326 lines, 6 phases, 6 files scoped
- Specifies cross-process token registration flow in detail
- Documents concurrent heartbeat guards, session timeouts, and fail-safe defaults
- Defines the exact `query()` SDK call pattern with code example
- Covers interval drift as an acceptable trade-off

**Agent Text Chat plan** (`.docs/plans/2026.03.12-agent-text-chat.md`):
- 350 lines, 4 phases, 10 files scoped
- Introduces the base + overlay prompt pattern to eliminate duplication
- Specifies WebSocket message protocol with JSON examples
- Documents authentication/pairing flow reuse
- Explicitly states what the chat path does NOT need (VAD, STT, TTS)

---

## 4. Custom Subagents

Subagents are specialized Claude Code agents that the main agent delegates to. The key motivation is **context window management** — by delegating research, review, and fixing to subagents, the main agent stays focused and doesn't fill up its context with intermediate work.

### 4.1 Plan Reviewer (`plan-reviewer.md`)

**Purpose:** Reviews workplans before implementation. Runs as a subagent so it isn't biased by the context the main agent already has.

**Process:**
1. The `/create_plan` command instructs the main agent to spawn the plan-reviewer subagent
2. The reviewer thoroughly checks all referenced files and the plan's consistency
3. The reviewer returns suggestions to the main agent
4. The main agent decides which feedback to implement
5. This happens **twice** — two review iterations are required
6. A table of review iterations is included in the plan output so the human can check what feedback was applied

**Why a subagent?** Fresh context means no bias from the planning conversation. Can read all referenced files without consuming the main agent's context window.

### 4.2 TypeScript Type Error Fixer (`typescript-type-error-fixer.md`)

**Purpose:** Fixes type errors after implementation, delegated from the main agent.

**Motivation:** Type checking was consuming a significant chunk of the main agent's work during implementation. By delegating this to a specialized subagent, the main agent stays on track with feature logic.

### 4.3 Documentation Fetcher (`documentation-fetcher.md`)

**Purpose:** Fetches external documentation using the Context7 MCP server.

**Process:**
1. Reads relevant files in the codebase first
2. Uses the Context7 MCP to fetch documentation
3. Returns **only the relevant** documentation to the main agent

**Why a subagent?** Fetching documentation consumes significant tokens. The subagent filters and returns only what matters, keeping the main agent's context clean.

### 4.4 Subagent Design Principles

- **Context isolation:** Each subagent gets a fresh context, unbiased by the main agent's conversation
- **Token efficiency:** Subagents absorb the cost of reading files, fetching docs, running checks — only the filtered result returns to the main agent
- **Specialization:** Each subagent has a focused purpose and instructions optimized for that task
- **Main agent as orchestrator:** The main agent coordinates and makes final decisions, but delegates the heavy lifting

---

## 5. Slash Commands (Workflows)

Slash commands encode repeatable workflows. These are the key ones:

### 5.1 `/create_plan` — The Planning Workflow

The most-used command. The agent is positioned as a "senior engineer skilled at making clear documentation for other developers."

**Plan structure (required sections in order):**
1. **High-level goal**
2. **File tree** — all files involved, marked as NEW / DELETED / MODIFIED (with explanation of what changes)
3. **Per-file methods and types/DTOs** — high level, no code. Methods need: arguments, return type, explanation. Arguments and returns should ideally be DTOs.
4. **Important technical notes** — only for difficult/intricate code. Can be omitted if straightforward.
5. **Phases** — step-by-step implementation phases with todos
6. **Success criteria**

**Per-file format (actual template):**

```markdown
### use-report-tutorial-navigation.ts (NEW)

#### Types
NavigationState {
  section: number
  isAnimating: boolean
  cameFromContact: boolean
}

UseReportTutorialNavigationProps {
  sectionSlugs: string[]
}

#### Methods
| Method | Arguments | Returns | Description |
|--------|-----------|---------|-------------|
| `useReportTutorialNavigation` | `props: Props` | `Return` | Main hook... |
| `calculateNextIndex` | `current: number, direction: "up" \| "down", config: IndexConfig` | `number` | Pure function... |
```

**Workflow (5 steps):**
1. Create plan with the structure above
2. Spawn **plan-reviewer subagent** to review the plan
3. Review suggestions — the main agent decides what to implement (it has more context, "it is the boss")
4. Spawn **plan-reviewer subagent** for a second review iteration
5. Summarize to the user: the plan + a table per review cycle showing suggestions received, what was implemented (green checkmark), what was ignored (red cross)

**Typical usage flow:**
1. Human discusses the feature with Claude — options, pros/cons, which files would be adapted
2. When happy, human types `/create_plan`
3. Agent produces the plan with two review iterations
4. Human checks file tree, types/methods, and the review tables

### 5.2 `/implement_plan` — The Execution Workflow

When the human is happy with a plan:

1. Human types `/implement_plan`
2. Each **phase** of the plan is implemented by a **subagent** (not the main agent)
3. The main agent acts as **orchestrator** — it coordinates phase execution and monitors progress
4. This keeps the main agent's context clean for decision-making

### 5.3 Other Commands

| Command | Purpose |
|---------|---------|
| `/check_plan` | (Deprecated) Replaced by plan-reviewer subagent integrated into `/create_plan` |
| `/show_filetree_with_edits` | For smaller features done in-chat: shows the file tree with edit indicators so the human can verify structural changes |
| `/thoroughly_test` | Instructs subagents to create unit tests, integration tests, and end-to-end tests |
| `/check_coding_conventions` | Sanity check that code follows project conventions |
| `/check_project_structure` | Overview of project structure to catch structural issues |
| `/draft_git_commit_message_for_staged_changes` | Auto-generates commit messages |
| `/push_all_changes_to_git` | Stages, commits, and pushes |
| `/create_PR` | Creates pull request with generated description |

---

## 6. Project File Structure

### 6.1 Configuration Layer

| File/Dir | Purpose |
|----------|---------|
| `CLAUDE.md` (root) | Top-level behavioral contract. References `~/.claude/guidelines/` and project-specific `project_guidelines.md` |
| `.claude/settings.local.json` | Permission allowlist. Whitelists safe commands (`git pull`, `npm test`, `npm run`) |
| `conductor.json` | Conductor workspace setup. Points to `.conductor/conductor-setup.sh` |
| `.conductor/conductor-setup.sh` | Symlinks all `.env*` files from repo root and subdirectories (`web/`, `worker/`) into the workspace. Ensures each Conductor workspace gets the right env config without copying secrets. |

### 6.2 Documentation Layer

```
.docs/
  plans/                    # Dated workplans — the core orchestration artifact
    2026.02.19-twilio-voice-calls.md
    2026.02.20-dashboard-vite-react-hono.md
    2026.03.05-agent-heartbeat-system.md
    2026.03.12-agent-text-chat.md
    ...
  design/
    designprinciples.md     # Visual/UX design system
```

### 6.3 Permission Model (`.claude/settings.local.json`)

```json
{
  "permissions": {
    "allow": [
      "Bash(git pull:*)",
      "Bash(npm test:*)",
      "Bash(npm run:*)"
    ]
  }
}
```

---

## 7. MCP Servers (Recommended)

Installed with **user scope** so they're available across all projects:

| Server | Purpose |
|--------|---------|
| **Context7** | Documentation fetching (used by documentation-fetcher subagent) |
| **Figma MCP** | Feed designs directly to Claude Code |
| **Chrome DevTools MCP** | Frontend agent can check its own visual output |

---

## 8. The Full Workflow

```
Human discusses feature with Claude
        │
        ▼
Human types /create_plan
        │
        ▼
┌──────────────────────┐
│ Main Agent           │  Writes workplan (goal, file tree, types,
│ (Planning)           │  methods, technical notes, phases, criteria)
│                      │
│  ┌─────────────────┐ │
│  │ Plan Reviewer   │ │  Review iteration 1: checks files, returns suggestions
│  │ (Subagent)      │ │  Main agent applies accepted feedback
│  └─────────────────┘ │
│  ┌─────────────────┐ │
│  │ Plan Reviewer   │ │  Review iteration 2: re-checks, returns suggestions
│  │ (Subagent)      │ │  Main agent applies accepted feedback
│  └─────────────────┘ │
│                      │
│  Outputs: plan + review iteration table
└──────────┬───────────┘
           │
           ▼
   Human reviews plan
   (checks file tree, types/methods, review table)
           │
           ▼
Human types /implement_plan
           │
           ▼
┌──────────────────────┐
│ Main Agent           │  Orchestrator — does NOT implement directly
│ (Orchestration)      │
│                      │
│  ┌─────────────────┐ │
│  │ Phase 1         │ │  Subagent implements Phase 1
│  │ (Subagent)      │ │
│  └─────────────────┘ │
│  ┌─────────────────┐ │
│  │ Phase 2         │ │  Subagent implements Phase 2
│  │ (Subagent)      │ │
│  └─────────────────┘ │
│  ┌─────────────────┐ │
│  │ Type Fixer      │ │  Subagent fixes type errors
│  │ (Subagent)      │ │
│  └─────────────────┘ │
│  ┌─────────────────┐ │
│  │ Doc Fetcher     │ │  Subagent fetches docs if needed
│  │ (Subagent)      │ │
│  └─────────────────┘ │
└──────────────────────┘
           │
           ▼
   Human verifies against success criteria
```

---

## 9. Key Insights for Adoption

### 9.1 Context Window Management is the Core Constraint

The entire subagent architecture exists to solve one problem: **the main agent's context window fills up, causing quality degradation.** Every delegation decision flows from this:
- Plan review → subagent (don't pollute planner context with file reads)
- Type fixing → subagent (don't burn context on mechanical fixes)
- Doc fetching → subagent (don't burn context on large documentation)
- Phase implementation → subagent (don't burn orchestrator context on implementation details)

### 9.2 The Human Reviews Structure, Not Code

The methodology is designed for a developer who doesn't read most generated code. Instead, they verify:
- **File tree:** Are the right files being created/modified?
- **Types and methods:** Does the interface match intent?
- **Review iteration table:** Was the plan reviewed and improved?
- **Success criteria:** Is "done" defined correctly?

This is a high-leverage review pattern — structural correctness is faster to verify than line-by-line code review.

### 9.3 Conductor vs. IDE

ArthurDevel uses Conductor (multi-agent parallel workspaces) for most work — backend changes, frontend changes, new features, large refactors. He switches to a traditional IDE only when something fundamental needs close visual inspection.

---

## 10. Applying This to Roald

### What Roald already has:
- `docs/architecture-guidelines.md` — strong architectural north star with workplan and PR review standards
- Prompt-driven architecture (`prompts/`)
- File-backed state (`mind.md`, `knowledge/`)
- Clear product intention and non-goals

### Recommended adoptions:

| Practice | Priority | Recommendation |
|----------|----------|----------------|
| **Dated workplans in `.docs/plans/`** | High | Adopt. Write workplans before implementation. |
| **`/create_plan` slash command** | High | Create a project-specific version that enforces the workplan template and includes plan-reviewer iterations. |
| **`/implement_plan` slash command** | High | Create a version where phases are delegated to subagents. |
| **Plan-reviewer subagent** | High | Adopt. Two review iterations catch issues before implementation starts. |
| **File Tree in workplans** | High | Every workplan lists exactly which files are created/modified. |
| **User-level guidelines** | Medium | Create `claude_primer.md` and `code_formatting.md` in `~/.claude/guidelines/` for cross-project consistency. |
| **`.claude/settings.local.json`** | Medium | Whitelist safe commands for smoother agent execution. |
| **`/show_filetree_with_edits`** | Medium | Useful for verifying smaller changes without reading code. |
| **Documentation-fetcher subagent** | Low | Relevant if using Context7 or similar doc-fetching MCPs. |
| **TypeScript type-fixer subagent** | Low | Roald is primarily Python, so less relevant. Could adapt for Python linting/typing. |

### Recommended directory structure:

```
.docs/
  plans/
    YYYY.MM.DD-feature-name.md    # Workplans (architect output)

.claude/
  commands/
    create_plan.md                # Planning workflow
    implement_plan.md             # Execution workflow
  agents/
    plan-reviewer.md              # Plan review subagent
```

---

## Appendix: Attached Files Not Yet Downloaded

The Notion page references these downloadable files that contain the actual prompt content. If these can be obtained, they should be analyzed and adapted for Roald:

- `CLAUDE.md` — root behavioral contract
- `claude_primer.md` — agent behavior guidelines
- `code_formatting.md` — code formatting rules
- `plan-reviewer.md` — plan review subagent definition
- `typescript-type-error-fixer.md` — type fixer subagent
- `documentation-fetcher.md` — doc fetcher subagent
- `create_plan.md` — planning slash command
- `implement_plan.md` — implementation slash command
- `check_plan.md` — (deprecated) plan checking command
- `thoroughly_test.md` — testing slash command
- `check_coding_conventions.md` — convention checking command
- `check_project_structure.md` — structure checking command
- `show_filetree_with_edits.md` — edit visualization command
- `draft_git_commit_message_for_staged_changes.md` — commit message command
- `push_all_changes_to_git.md` — git push command
- `create_PR.md` — PR creation command
- `conductor.json` — Conductor workspace config
- `conductor-setup.sh` — Conductor setup script
