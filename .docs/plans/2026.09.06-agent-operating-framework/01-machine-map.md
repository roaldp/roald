# What is running on this machine

Generated 2026-09-06 from `scripts/agent_inventory.py`, which reads
`~/.claude/projects` and resolves each entry back to the directory Claude Code ran in.
Raw data is in `machine-inventory.json`. Rerun the script to refresh it.

Transcript size in megabytes is the activity measure throughout. It is a better proxy
for how much agent work a directory has absorbed than a session count, because one long
session can carry a hundred times the work of a short one.

## The shape of the estate

Fifty-nine directories have Claude Code history. They group into thirteen families.

| Last active | MB | Sessions | Dirs | Has CLAUDE.md | Has AGENTS.md | Family |
|---|---|---|---|---|---|---|
| 2026-09-06 | 581 | 82 | 32 | 2 | 30 | Conductor: **ai-infrastructure-capital** |
| 2026-08-08 | 169 | 1698 | 1 | 1 | 0 | `~/roald` (the pulse companion's own runtime) |
| 2026-09-05 | 67 | 6 | 3 | 0 | 0 | Conductor: icp-nodes-tracker |
| 2026-09-05 | 24 | 5 | 3 | 0 | 3 | Conductor: accounting |
| 2026-08-31 | 24 | 2 | 2 | 2 | 0 | Claude Desktop: Obsidian Vault backup / ac-aicapital-os |
| 2026-09-05 | 20 | 5 | 5 | 5 | 0 | Conductor: NODAO-GPU |
| 2026-09-01 | 12 | 5 | 4 | 2 | 0 | Claude Desktop: Obsidian Vault / NODAO GPU Fund |
| 2026-09-06 | 8 | 1 | 1 | 1 | 1 | Conductor: tiny-skylines |
| 2026-09-05 | 6 | 2 | 1 | 0 | 0 | Conductor: accounting-v1 |
| 2026-09-06 | 5 | 11 | 1 | 0 | 0 | `~` (ad-hoc sessions in the home directory) |
| 2026-08-31 | 2 | 4 | 1 | 0 | 0 | `~/nodewatch-runner` |
| 2026-09-06 | 1 | 4 | 4 | 4 | 0 | Conductor: roald (this repo) |
| 2026-09-06 | 0 | 1 | 1 | 0 | 0 | Conductor: icp-nodes-claude-directory-v1 |

**One family carries two thirds of all agent work.** `ai-infrastructure-capital` has 581
of roughly 900 megabytes of transcript, spread over 32 Conductor workspaces, and it was
active today. Anything that does not land there does not move the needle.

`~/roald` shows 1,698 sessions but only 169 MB. That is the pulse companion looping
every thirty minutes, not interactive work. It matters for a different reason: it is the
one agent on this machine that writes to Roald unprompted, so the update-format rules
apply to it more directly than to anything else.

## The instruction files each family loads

Claude Code auto-loads `CLAUDE.md` and `CLAUDE.local.md` only. This was confirmed two
ways: the documentation states "Claude Code reads `CLAUDE.md`, not `AGENTS.md`", and the
strings in the local binary at
`/Users/roaldp/.local/share/claude/versions/2.1.261` contain the discovery array
`["CLAUDE.md","CLAUDE.local.md"]` with no `AGENTS.md` beside it. The only `AGENTS.md`
handling in the binary belongs to `/import` and `/init`, both one-off migration paths.

### The AGENTS.md files are not being loaded

Thirty-one directories hold an `AGENTS.md` and no `CLAUDE.md`. Between them they account
for 517 MB of agent transcript — the majority of all work done on this machine.

The `ai-infrastructure-capital` root `AGENTS.md` is the most carefully written
instruction file in the estate. It is a 9 kB router that separates three vehicles which
are routinely confused with one another, names the specific error agents keep making
(reusing the Swiss Iceland story for the Texas vehicle), lists ten sub-`AGENTS.md` files,
flags two stale files by name, and restates the house writing rules.

None of it loads at session start. An agent in `bozeman` or `stuttgart` sees it only if
something in the conversation tells it to open the file.

One workspace, `athens-v1`, has a one-line `CLAUDE.md` containing `@AGENTS.md`. Someone
found the fix and it was never committed to `main`. `origin/main` has no `CLAUDE.md`.

**The cheapest high-value change available on this machine is a one-line `CLAUDE.md`
containing `@AGENTS.md`, committed to the `main` branch of each repo that has an
`AGENTS.md`.** That is `ai-infrastructure-capital`, `accounting`, `tiny-skylines`. It
costs one line per repo and turns the best instruction file here from dormant to loaded.

This needs an empirical check before it is presented as fact, since it rests on binary
strings and one documentation sentence. The check is in `02-framework-design.md`.

### User-global surfaces, `~/.claude`

- `CLAUDE.md`, 2,589 bytes. Covers explaining technical problems, headings, weighting
  findings, and chat response length. It does **not** cover external writing, task
  intake, or plan adherence. Those are the three gaps this framework fills.
- `agents/`: `documentation-fetcher.md`, `typescript-type-error-fixer.md`.
- `skills/`: `goldfish`, `gpu-util`.
- `commands/`: eleven files, including `create_plan`, `implement_plan`, `check_plan`,
  `thoroughly_test`, `create_PR`. These are on the deprecated commands path; skills now
  take precedence over commands on a name clash.
- `settings.json`: model `opus[1m]`, Cloudflare plugin enabled, light theme. **No hooks
  are configured anywhere on this machine.** Every rule currently in force is a request
  the model may ignore.

### Conductor

`~/.conductor/settings.toml` sets the default model to `claude:opus-5-1m` and the branch
prefix to the GitHub username. Every workspace therefore runs Opus 5 on a 1M-token
window.

Per-repo Conductor config lives in `.conductor/conductor.json`, which this repo uses to
run `conductor-setup.sh` on workspace creation. That setup script is a propagation point:
it runs in every new workspace of a repo.

### Claude Desktop

Claude Desktop runs local agents, not just cloud conversations. Its bundle at
`~/Library/Application Support/Claude/claude-code/2.1.260` is a full Claude Code, and
`git-worktrees.json` records the directories it has worked in:

- `~/Documents/Obsidian Vault/Projects/nodao/NODAO GPU Fund`
- `~/Documents/Obsidian Vault/Projects/nodao/NODAO ICP Nodes/ICP Nodes Dashboard`
- `~/Documents/Obsidian Vault/Projects/Borealis (Swiss)/ai-infrastructure-capital`
- `~/Documents/Obsidian Vault/Allusion Ventures`
- `~/Documents/2026.06.12 Obsidian Vault backup/Projects/Borealis (Swiss)/ac-aicapital-os`
- `~/Documents/codebases/BoTH3 - Team #1`
- `~/Documents/codebases/Allusion Ventures site`
- `~/Documents/Allusion Ventures Dealflow`
- `~/Documents/GPU Fund`
- `~/roald`
- `~/Downloads`

These sessions appear in `~/.claude/projects` alongside the CLI's, which is direct
evidence that **Claude Desktop's local agent mode shares `~/.claude`**. A file dropped in
`~/.claude/skills/` or `~/.claude/CLAUDE.md` reaches Claude Desktop's local agents as
well as the CLI.

Claude Desktop's cloud-side Projects are a different matter. Their custom instructions
live server-side and cannot be written from this machine. Propagating to those means
either pasting by hand or syncing skills through claude.ai, and a skill synced that way
must stay inside the smaller Agent Skills frontmatter field set.

## Prior art already on this machine

Two systems already solve parts of this brief. Neither is portable, and that is the whole
problem.

### The AIC house writing style, `docs/pitch-materials/style/`

On `origin/main` in `ai-infrastructure-capital`. Seven files:

- `STYLE.md`, 209 lines, capped by its own rule at 210. Governs wording, rhythm,
  structure and punctuation for investor-facing copy. Built from real before/after pairs
  taken from Roald's own edits.
- `MESSAGES.md`. WhatsApp, Telegram and SMS. Derived from one edit where Roald's sent
  version was 40% shorter than the draft and cut every line that explained, positioned or
  asked.
- `CLAIMS.md`. Claims the company cannot stand behind. Overrides the content brief.
- `FORMATS.md`. Skeletons and length budgets per document type.
- `BRIEF-TEMPLATE.md`. The intake form for a document.
- `lint.py`, 182 lines. Mechanical enforcement: banned words, banned patterns, vague
  quantifiers, sentence length cap, bold density, unit-of-account errors.
- `README.md`.

Plus two skills in `.claude/skills/`: `pitch-copy` (draft or revise in house style) and
`pitch-style-feedback` (fold a human's hand-edits back into the guide).

The feedback skill is the part worth copying wholesale. It diffs the agent's draft
against what Roald actually sent, triages every change into style, claim, fact or noise,
looks for the single rule behind a cluster of edits, and requires the human's own text to
score zero on the linter — if a new rule flags Roald's own writing, the rule is wrong.

What is general and what is not: sections 4 through 8 of `STYLE.md` — sentences, numbers,
emphasis, punctuation, banned constructions — transfer to any external writing. Sections
1, 2, 3, 9 and 10 are specific to investor pitch material.

### The AIC AGENTS.md router pattern

A root file that routes rather than instructs, ten sub-`AGENTS.md` files at the folders
that need their own rules, a table of live workstreams with state, and an explicit
"known stale files, do not trust these" section naming `memory.md` and a `_superseded/`
folder.

The stale-file section is the interesting part. It is the only mechanism observed here
that protects an agent from confidently reading outdated material.

### What is duplicated by hand right now

`~/.claude/CLAUDE.md`'s writing rules appear verbatim inside the AIC `AGENTS.md` under
"Writing rules for agents". Someone copy-pasted them. That is the propagation problem in
miniature: a rule improved in one place does not reach the other.

## Verification still needed

1. Confirm empirically that a Claude Code session in an AIC workspace does not load
   `AGENTS.md`. Binary strings and one documentation sentence are strong but not proof.
2. Confirm that Claude Desktop's local agent mode reads `~/.claude/CLAUDE.md` and
   `~/.claude/skills/`. Shared `~/.claude/projects` is strong circumstantial evidence,
   not direct confirmation.
3. Confirm whether `.conductor/conductor.json` supports anything beyond a setup script,
   and whether Conductor has a per-repo `settings.toml`.
