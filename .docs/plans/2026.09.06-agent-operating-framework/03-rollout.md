# Rollout: getting this onto every agent on the machine

Nothing in here has been executed. Roald asked for the feasibility to be investigated, not
for the rollout to be run, and every step below touches something outside this repo.

Run `python3 scripts/install_framework.py` for a dry run of the user-global part, and
`--report-repos` for the per-repo list.

## The four layers, and what reaches what

**User-global, `~/.claude/`.** Reaches the Claude Code CLI, every Conductor workspace, and
Claude Desktop's local agent mode. Desktop's local sessions appear in `~/.claude/projects`
next to the CLI's, which is direct evidence they share the directory.

Two exceptions worth knowing before relying on this. The built-in `Explore` and `Plan`
subagents skip the `CLAUDE.md` hierarchy, and output styles do not reach subagents at all.
So a rule that must reach a subagent belongs in a skill, a hook or `CLAUDE.md`, never in an
output style.

**Per-repo, committed.** Only what is specific to that repo. The framework is inherited
from the global layer, never copied in. Anthropic's documentation says that when two rules
contradict, Claude may pick one arbitrarily, so a duplicated rule is worse than no rule.

**Per-workspace.** Nothing. Conductor workspaces are checkouts and anything written in one
alone is lost. The `ai-infrastructure-capital` repo's own hygiene document already records
that roughly four in ten counterparty records never reach `main`.

**Claude Desktop's cloud Projects.** Not reachable from this machine. Their custom
instructions live server-side. The options are pasting by hand, or syncing a skill through
claude.ai — and a skill synced that way must stay inside the smaller Agent Skills
frontmatter field set, which excludes every Claude-Code-only field. This is a real limit.

## Step 1: install the source clone

Clone this repo to `~/.claude/framework-src` and pin it to `main`.

**Do not install from `~/conductor/repos/roald`.** That checkout is currently on
`fix/deferred-update-apply` while every workspace sits on `ed0d491`. Symlinking global
agent behaviour into it would tie every agent on the machine to whatever branch that
checkout happens to be on.

```
git clone <this repo> ~/.claude/framework-src
cd ~/.claude/framework-src && git checkout main
python3 scripts/install_framework.py            # dry run, shows what it would do
python3 scripts/install_framework.py --apply
```

The installer symlinks rather than copies, so an update is `git -C ~/.claude/framework-src
pull` with nothing to re-run. It backs up `settings.json` before its first write, marks
every hook entry it adds so `--uninstall` removes exactly those and nothing else, and adds
no blocking hook unless `--with-gate` is passed.

What it installs by default:

| Path | What |
|---|---|
| `~/.claude/agents/plan-reviewer.md` | The subagent `/create_plan` has been calling into the void |
| `~/.claude/skills/write-external/` | Loads the house style at the moment of drafting |
| `~/.claude/output-styles/steering.md` | Reply format for someone supervising several agents |
| `~/.claude/framework-hooks/` | The hook scripts |
| `~/.claude/framework-style/` | `CORE.md` |
| `settings.json` hooks | `InstructionsLoaded` logging, `SessionStart` and `SubagentStart` re-anchor |

## Step 2: fix what is already broken

These are edits to files Roald already has, and they are the highest-value part of the
whole rollout because the instructions already exist and already fail.

**`~/.claude/commands/create_plan.md`.** Steps 2 and 4 call a subagent named
`plan-reviewer`. It does not exist. Installing `plan-reviewer.md` in step 1 fixes it.
Then remove the emoji instruction from step 5, which contradicts both `~/.claude/CLAUDE.md`
and this repo's `CLAUDE.md`.

**The other ten command files.** Audit them for the same class of defect: a named subagent
or skill that does not exist, and an instruction that contradicts a global rule. That
directory has never been checked.

**One note on those eleven files.** They live on the deprecated commands path. Skills now
take precedence over commands on a name clash, and the documentation recommends skills for
anything new. Converting them is not urgent, but do not add to them.

## Step 3: the one-line CLAUDE.md, per repo

This is the single highest-value change available on this machine and it costs one line per
repo.

Claude Code loads `CLAUDE.md` and `CLAUDE.local.md` only. Thirty-one directories here hold
an `AGENTS.md` and no `CLAUDE.md`, and between them they carry 517 MB of the roughly 900 MB
of agent transcript on this machine. None of that instruction text is loaded at session
start.

Verified both directions on 2026-09-06. A headless session in
`ai-infrastructure-capital/hamburg` answered `LOADED=no` when asked whether `AGENTS.md` was
in its context. The same probe in `athens-v1`, the one workspace that happens to have a
`CLAUDE.md` containing `@AGENTS.md`, quoted the router's table header back correctly.

| Repo | Sessions | Action |
|---|---|---|
| `ai-infrastructure-capital` | 581 MB, 32 workspaces | `echo '@AGENTS.md' > CLAUDE.md`, commit to `main` |
| `accounting` | 24 MB, 3 workspaces | same |
| `tiny-skylines` | 8 MB | has both files already. Delete the duplicated global rules from its `CLAUDE.md` and make it import `AGENTS.md` |

Then do the same beside each sub-`AGENTS.md` that carries real rules. In
`ai-infrastructure-capital` those are `portal/`, `website/`, `docs/calls/`,
`docs/hardware-procurement/`, `docs/crm/`, `docs/pitch-materials/`, `nexara/`, `ragnarok/`
and `us/website/`. A subdirectory `CLAUDE.md` does not load at session start; it loads when
Claude reads a file in that directory, which is exactly when those rules are wanted.

**This changes other people's repos and needs Roald's go-ahead.** It is a one-line file per
location, added by pull request, reversible by deleting the file.

## Step 4: remove the duplication

`~/.claude/CLAUDE.md`'s writing rules appear again, as a condensed paraphrase, inside the
`ai-infrastructure-capital` `AGENTS.md` under "Writing rules for agents". Someone
maintained both by hand.

The AIC version is not a straight copy and is in one respect better: it carries a scoping
sentence the global file lacks, saying these rules govern how you explain things to Roald
and do not govern investor-facing copy. That distinction should move up into the global
file, and the AIC section should become a pointer.

## Step 5: measure before building anything else

Install the `InstructionsLoaded` logging and change nothing for two weeks.

The log is at `~/.claude/framework-logs/instructions-loaded.jsonl`, one line per loaded
file with `file_path`, `load_reason` and `memory_type`. After two weeks it answers a
question nothing else can: when an instruction was ignored, was it ever loaded?

In the same period, run the two cheap experiments in `06-design-v2.md`. Switch the
`steering` output style on and count replies over half a page against the current baseline.
Draft one email three ways — rules only, exemplars only, both — and rank them blind.

Everything held back until those measurements exist: the contract gate and `contract.json`,
the evaluator subagent, the orchestration skill, the linter as a blocking hook, plugin
packaging, and `UserPromptSubmit` re-injection.

## Merging with what each agent already knows

Roald asked for an update sequence per agent that marries the framework with the
context-specific knowledge each already has. The sequence is the same four questions
everywhere, and it is short because the framework installs globally rather than per repo:

1. Does this repo's own instruction file load at all? If there is an `AGENTS.md` and no
   `CLAUDE.md`, no.
2. Does it restate something the global layer now supplies? Replace the restatement with a
   pointer.
3. Does it name a subagent, skill or command that does not exist? Fix or delete the
   reference.
4. What does it say that is genuinely specific to this repo? Leave that alone. It is the
   part with the most value and the least coverage anywhere else.

The AIC `AGENTS.md` is the model for question 4 and worth copying elsewhere. It routes
rather than instructs, it names the specific mistake agents keep making, and it has a
section headed "Known stale files, do not trust these" that names `memory.md` and a
`_superseded/` folder by name. That last section is the only mechanism found anywhere on
this machine that protects an agent from confidently reading outdated material.

## Reversing it

`python3 scripts/install_framework.py --uninstall --apply` removes every symlink it created
and every hook entry it marked, and leaves the rest of `settings.json` alone. A backup of
the file as it was before the first write sits at `~/.claude/settings.json.pre-framework`.

The per-repo changes are one-line files. Delete them.
