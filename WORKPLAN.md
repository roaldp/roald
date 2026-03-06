# Workplan: Skill Learning for Roald

## Context

Roald is a personal AI companion running as an async Python event loop (`pulse.py`). It
spawns Claude CLI subprocesses to handle full pulses (every 30 min) and reactive pulses
(Slack DM). The agent is already resource-heavy — each pulse blocks a Claude subprocess
for the full duration. Adding skills must **not** increase pulse weight.

OpenClaw's skill format is elegant: a folder with a `SKILL.md` (YAML frontmatter +
markdown instructions). No SDK, no compilation. Skills are instruction manuals that tell
the agent which tools to run. We adopt this format directly so we can import popular
OpenClaw skills unchanged.

---

## Architecture: Lightweight Skill Dispatch

### Core Idea

Skills are **not loaded into the main pulse context**. Instead:

1. The pulse prompt gets a **skill index** — a short name→description table (~20 lines).
2. When Claude decides a skill is needed, it outputs a **structured skill request**
   (JSON block in its response) instead of trying to do the work itself.
3. `pulse.py` detects the skill request and spawns a **separate Claude subprocess** for
   the skill, running in parallel.
4. The skill subprocess gets the `SKILL.md` instructions + the task context and runs
   independently.
5. Results are written to `knowledge/skill_results/` and optionally relayed to the user
   via Slack.

This keeps the main pulse thin — it only ever sees the index, never the full skill body.

```
┌─────────────┐       skill_index.md (auto-generated)
│  pulse.py   │───────────────────────────►┌────────────┐
│  main loop  │  "Use @deep-research for   │ Claude CLI │
│             │   this question"           │ main pulse │
└──────┬──────┘◄───────────────────────────└────────────┘
       │         skill_request JSON
       │
       ├──► spawn_skill("deep-research", context)  ──► Claude CLI subprocess
       ├──► spawn_skill("email-draft", context)     ──► Claude CLI subprocess
       │         (parallel, non-blocking)
       │
       ▼
  results → knowledge/skill_results/{timestamp}_{skill}.md
          → optional Slack notification
```

---

## Implementation Steps

### Phase 1: Skill Format & Registry

**Step 1.1 — Create `skills/` directory structure**

```
skills/
├── _index.yaml          # auto-generated skill index (git-ignored)
├── bundled/             # skills that ship with roald
│   └── deep-research/
│       └── SKILL.md
├── community/           # imported OpenClaw skills (git-ignored)
│   └── .gitkeep
└── local/               # user's custom skills (git-ignored)
    └── .gitkeep
```

**Step 1.2 — Skill loader (`skills.py`)**

A small module (~120 lines) that:
- Scans `skills/bundled/`, `skills/community/`, `skills/local/` for `SKILL.md` files
- Parses YAML frontmatter to extract `name`, `description`, `requires` (env/bins)
- Filters out skills whose requirements aren't met
- Generates `skills/_index.yaml` — a flat list of `{name, description, path}`
- Generates a markdown snippet for injection into pulse prompts
- Precedence: local > community > bundled (same name = higher precedence wins)

**Step 1.3 — Skill index prompt injection**

Add to `prompts/pulse_full.md` and `prompts/pulse_reactive.md`:

```markdown
## Available Skills

{{SKILL_INDEX}}

When a task matches a skill, respond with a skill request block:
\```json
{"skill_request": {"name": "skill-name", "task": "what to do", "context": "relevant info"}}
\```
Do NOT attempt the skill's work yourself. The system will handle it.
```

### Phase 2: Skill Execution Engine

**Step 2.1 — `run_skill()` function in `pulse.py`**

```python
async def run_skill(skill_name: str, task: str, context: str, config: dict) -> str:
```

- Loads the skill's `SKILL.md` from the resolved path
- Constructs a prompt: skill instructions + task + context
- Determines allowed tools from the skill's `requires` section
- Spawns a Claude CLI subprocess via `run_claude()` (non-blocking via asyncio)
- Writes result to `knowledge/skill_results/{timestamp}_{skill_name}.md`
- Returns the result text

**Step 2.2 — Skill request detection in `run_claude()` response parsing**

After `run_claude()` returns, scan the result text for `{"skill_request": ...}` blocks.
For each detected request:
- Validate the skill name exists in the index
- Fire off `run_skill()` as an asyncio task (parallel, non-blocking)
- Don't hold the pulse lock while skills run

**Step 2.3 — Parallel execution with result relay**

- Skills run as `asyncio.create_task()` — fully parallel
- Each skill gets its own lock-free Claude subprocess
- On completion, if the skill produced user-facing output, send a brief Slack message
- A simple `active_skills: dict[str, asyncio.Task]` tracks running skills

### Phase 3: Import OpenClaw Skills

**Step 3.1 — `skill_import.py` CLI tool**

A standalone script to import skills:

```bash
python3 skill_import.py install deep-research    # from ClawHub
python3 skill_import.py install ./path/to/skill  # from local folder
python3 skill_import.py list                      # show installed skills
python3 skill_import.py remove skill-name         # remove a community skill
```

How it works:
- Fetches the skill folder from ClawHub (GitHub raw or git sparse checkout)
- Copies into `skills/community/{skill-name}/`
- Validates the `SKILL.md` frontmatter
- Regenerates the index

**Step 3.2 — Bundle popular OpenClaw skills**

Pre-import these high-value skills into `skills/bundled/`:

| Skill | Why |
|-------|-----|
| `deep-research` | Autonomous multi-step web research |
| `capability-evolver` | Self-improving agent patterns |
| `memory` | Local-first persistent memory (SQLite) |
| `email-draft` | Compose and polish email replies |
| `meeting-prep` | Pre-meeting briefing from calendar + notes |

These will be adapted versions with Roald-specific tweaks (use `mind.md` for context,
write to `knowledge/`).

### Phase 4: Integration into Pulse Loop

**Step 4.1 — Update `pulse.py` main flow**

Minimal changes to `pulse.py`:

1. Import `skills` module
2. At startup: `skills.build_index()` to generate the index
3. In prompt building: inject `{{SKILL_INDEX}}` with the generated markdown
4. After `run_claude()` returns: parse for skill requests, spawn them
5. Add `--once-skill` CLI flag for testing individual skills

**Step 4.2 — Update config.yaml**

```yaml
# Skills
skills:
  enabled: true
  max_parallel: 3           # max concurrent skill subprocesses
  timeout_seconds: 600      # per-skill timeout
  notify_on_complete: true  # Slack notification when skill finishes
```

**Step 4.3 — Update `.gitignore`**

```
skills/community/
skills/local/
skills/_index.yaml
knowledge/skill_results/
```

### Phase 5: Skill-Triggered Learning

**Step 5.1 — Skill creation from conversation**

When the user says "learn how to do X" or "remember this workflow":
- The reactive pulse detects the learning intent
- Creates a new skill in `skills/local/` with a generated `SKILL.md`
- The skill captures the workflow as natural-language instructions
- Index auto-regenerates on next pulse

**Step 5.2 — Skill refinement loop**

After a skill runs, its result is reviewed:
- If the user says "that was good" → skill confidence increases (tracked in index)
- If the user says "fix this" → skill instructions are updated
- Skills that consistently fail get flagged for review

---

## File Changes Summary

| File | Change |
|------|--------|
| `pulse.py` | Add skill index injection, skill request parsing, `run_skill()`, parallel task mgmt |
| `skills.py` | **New** — skill loader, index builder, requirement checker |
| `skill_import.py` | **New** — CLI for importing OpenClaw skills |
| `prompts/pulse_full.md` | Add `{{SKILL_INDEX}}` section and skill request instructions |
| `prompts/pulse_reactive.md` | Add `{{SKILL_INDEX}}` section and skill request instructions |
| `prompts/skill_runner.md` | **New** — system prompt template for skill subprocess |
| `config.template.yaml` | Add `skills` section |
| `.gitignore` | Add skill runtime paths |
| `skills/bundled/*/SKILL.md` | **New** — bundled skill definitions |

---

## Design Principles

1. **Zero cost when idle** — Skills don't exist in the pulse context until needed. The
   index is ~20 lines regardless of how many skills are installed.

2. **Parallel, not serial** — Skills run as separate Claude subprocesses. The main pulse
   returns immediately after dispatching. No lock contention.

3. **OpenClaw-compatible** — We use the exact same `SKILL.md` format. Drop an OpenClaw
   skill folder into `skills/community/` and it works.

4. **Learnable** — The agent can create new skills from conversation, building a personal
   skill library over time.

5. **Minimal blast radius** — Only ~40 lines change in `pulse.py`. All new logic lives
   in `skills.py` and `skill_import.py`.
