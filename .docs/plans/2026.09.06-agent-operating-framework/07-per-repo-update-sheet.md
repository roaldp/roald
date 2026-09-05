# Per-repo update sheet

Roald asked for an update sequence run against every agent on the machine, marrying the
framework with the context each agent already carries. This is that sequence, applied.

Nothing here has been executed. Every row changes a repo outside this one.

## The four questions, asked of every repo

1. **Does this repo's instruction file load at all?** An `AGENTS.md` with no `CLAUDE.md`
   beside it does not. Claude Code loads `CLAUDE.md` and `CLAUDE.local.md` only.
2. **Does it restate something the global layer supplies?** Replace the restatement with a
   pointer. Two contradicting rules mean Claude may pick one arbitrarily.
3. **Does it name a subagent, skill or command that does not exist?**
4. **What is genuinely specific to this repo?** Leave that alone. It is the part with the
   most value and the least coverage anywhere else.

## The estate, ordered by how much agent work runs there

### ai-infrastructure-capital — 581 MB, 32 workspaces, active today

The busiest agent surface on the machine by a factor of three, and the most carefully
written instruction file on it.

**Loads: no.** A 9 kB root `AGENTS.md` and no `CLAUDE.md` on `main`. One workspace,
`athens-v1`, has a one-line `CLAUDE.md` containing `@AGENTS.md` that was never committed.
A live probe in `hamburg` answered `LOADED=no`; the same probe in `athens-v1` quoted the
router's table back correctly.

**What is in it, and it is good.** A router rather than an instruction set. It separates
three vehicles that are routinely confused, names the specific error agents keep making —
reusing the Swiss Iceland story for the Texas vehicle — routes to ten sub-`AGENTS.md`
files with a state column, and carries a section headed "Known stale files, do not trust
these" that names `memory.md` and a `_superseded/` folder. That last section is the only
mechanism found anywhere on this machine that protects an agent from confidently reading
outdated material, and it should be copied outward rather than changed.

**Duplication.** Lines 50 to 62 restate the global writing rules. Not verbatim — it is a
condensed paraphrase, and in one respect it is better than the global file, because it
carries a scoping sentence the global file lacks: these rules govern how you explain
things to Roald and do not govern investor-facing copy. Move that distinction up into
`~/.claude/CLAUDE.md` and make the AIC section a pointer.

**Actions.**

| | |
|---|---|
| 1 | `echo '@AGENTS.md' > CLAUDE.md` at the repo root, commit to `main` |
| 2 | The same one-liner beside each sub-`AGENTS.md` that carries real rules: `portal/`, `website/`, `docs/calls/`, `docs/hardware-procurement/`, `docs/crm/`, `docs/pitch-materials/`, `nexara/`, `ragnarok/`, `us/website/`. A subdirectory `CLAUDE.md` loads when Claude reads a file in that directory, which is exactly when those rules are wanted |
| 3 | Replace the "Writing rules for agents" section with a pointer, once the global file carries the scoping sentence |
| 4 | Leave `docs/pitch-materials/style/` where it is. `CORE.md` in the framework is the general extraction; `STYLE.md`, `MESSAGES.md` and `CLAIMS.md` stay here as the overlay because they carry vehicle facts and claims that must not go global |

### accounting — 24 MB, 3 workspaces

**Loads: no.** A 66-line `AGENTS.md`, no `CLAUDE.md`.

**What is in it.** A binding protocol with golden rules that matter: this repo records and
never moves money, every change goes through a pull request, never commit secrets, respect
`SCHEMA.md` as the contract. These are exactly the rules you want an agent to have loaded
before it does anything, and right now it has none of them.

**Action.** `echo '@AGENTS.md' > CLAUDE.md`, commit to `main`. Nothing else. The content is
repo-specific and correct.

### icp-nodes-tracker — 67 MB, 3 workspaces

**Loads: nothing exists.** No `CLAUDE.md`, no `AGENTS.md`. Sixty-seven megabytes of agent
work with no repo-level instructions at all, which is the second-largest unguided surface
here after AIC.

There is one skill, `.claude/skills/nodewatch-review/SKILL.md`, and `/nodewatch-review` is
one of only three custom commands ever actually invoked on this machine — four sessions.
So the skill route works here and the instruction route has never been tried.

**Action.** Write a short `CLAUDE.md`. Not a long one: what the repo is, what must never
happen, and where the real documentation lives. Ask Roald what belongs in it rather than
inferring it from the code, because this is the case where the agent genuinely does not
know.

### NODAO-GPU — 20 MB, 5 workspaces

**Loads: yes.** An 11-line `CLAUDE.md` with five hard rules, the first of which stops
agents writing to two read-only upstream repos.

**Action.** None. It is short, loaded, and specific. This is the shape the others should
be in.

### Claude Desktop directories — 36 MB across two Obsidian vault trees

`~/Documents/Obsidian Vault/Projects/nodao/NODAO GPU Fund` has a `CLAUDE.md`.
`~/Documents/2026.06.12 Obsidian Vault backup/Projects/Borealis (Swiss)/ac-aicapital-os`
has one. `~/Documents/Obsidian Vault/Allusion Ventures` has none, and neither do several
other directories Claude Desktop has worked in, including `~/Documents/GPU Fund`,
`~/Documents/codebases/BoTH3 - Team #1` and `~/Downloads`.

The global layer reaches all of these, because Claude Desktop's local agent mode writes
into `~/.claude/projects` alongside the CLI and therefore shares `~/.claude`.

**Action.** Nothing per directory. Install globally and let it inherit. Worth confirming
directly by running a Desktop local agent in a scratch directory and asking it what it
loaded.

### tiny-skylines — 8 MB

**Loads: yes**, and the duplication is already acknowledged in writing. Its `AGENTS.md`
opens: "`CLAUDE.md` contains the same rules; if the two ever disagree, `CLAUDE.md` wins and
this file is stale — fix it." Two files, maintained by hand, with a manual reconciliation
rule.

Three skills in `.claude/skills/`: `studio-loop`, `playtest`, `balance-run`.

**Action.** Make `AGENTS.md` the single source and reduce `CLAUDE.md` to `@AGENTS.md`, or
the reverse. Either is fine. Maintaining both by hand is the thing to stop. Then delete
the rules that the global layer now supplies — no emoji, be to the point, do not
overengineer, propose a plan first — since they are already global.

### accounting-v1 — 6 MB, and roald, and the rest

`accounting-v1` has no instruction file of any kind. This repo, `roald`, has a 24-line
`CLAUDE.md` that loads. `~` itself has 5 MB of ad-hoc sessions with nothing but the global
file.

**Action.** Global install covers them. Leave them alone.

## What this sequence does not solve

**The commands Roald wrote are not used.** Across 2,577 transcripts, `/create_plan` was
invoked zero times and `/implement_plan` once. Adding better instruction files does not
change that, because instruction files and commands are different surfaces. What follows
from it is that the framework has to arrive through the surfaces that fire without being
asked for: `CLAUDE.md`, hooks, the output style, and skills, which the model can invoke
when their description matches.

**Claude Desktop's cloud Projects.** Their instructions live server-side and cannot be
written from this machine. Pasting by hand, or syncing a skill through claude.ai within
the smaller Agent Skills field set, are the only routes.

**Two built-in agents skip the whole hierarchy.** `Explore` and `Plan` do not load
`CLAUDE.md`. Anything that must reach them belongs in the delegation prompt.
