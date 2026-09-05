# Start here

Overnight run, 2026-09-06, against the brief you pasted. Nothing has been installed and no
other repo has been touched. Everything below is on this branch.

## What you have to decide

**1. Commit a one-line `CLAUDE.md` to three repos.** Claude Code loads `CLAUDE.md` and
`CLAUDE.local.md` and nothing else. Thirty-one directories here have an `AGENTS.md` and no
`CLAUDE.md`, and they carry 517 MB of the roughly 900 MB of agent transcript on this
machine. Your `ai-infrastructure-capital` router — the one that separates the three
vehicles and names the Iceland-story mistake — is not loaded in any workspace. `athens-v1`
has the one-line fix uncommitted, and a live probe there quoted the router back correctly
while the same probe in `hamburg` answered `LOADED=no`.

The change is `echo '@AGENTS.md' > CLAUDE.md` at the root of `ai-infrastructure-capital`,
`accounting` and `tiny-skylines`, by pull request. **Recommend doing it.** It is the
highest-value change available here and it is reversible by deleting a file.

**2. Install the user-global layer.** `python3 scripts/install_framework.py` for a dry run.
It symlinks a `plan-reviewer` subagent, a `write-external` skill, a `steering` output style,
`CORE.md` and two hooks into `~/.claude`, and adds three hook entries to `settings.json`.
Nothing it installs blocks a tool call. It backs up `settings.json` and has `--uninstall`.

It refuses to run from this workspace on purpose. Clone to `~/.claude/framework-src` on
`main` and run it there, so global agent behaviour is not tied to a branch. **Recommend
doing it, starting with the logging hook alone for two weeks.**

**3. Rank three drafts of the same email.** They are at `/tmp/styletest/A.txt`, `B.txt`,
`C.txt` — no style guide, guide plus corpus, guide only. This is the acceptance test for
the writing problem and nothing substitutes for your read. If A wins, the style work is
wrong and should stop.

**4. Tell me what the two-subagent limit was for.** Cost, reviewability, or just this job?
`CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS=2` would enforce it permanently.

## Findings that change what you would do

**Your custom commands are effectively unused.** Across 2,577 transcripts, `/create_plan`
was invoked zero times and `/implement_plan` once. Checked twice, because searching for a
command's name returns 887 hits from the listing every session loads; searching for a
sentence from inside each file gives 2, 3 and 2. The workflow you describe wanting is not
the workflow you run. So anything opt-in will not be used, and the framework has to arrive
through surfaces that fire without being asked for: `CLAUDE.md`, hooks, the output style,
and skills, which the model can invoke when their description matches.

**`/create_plan` calls a subagent that does not exist.** It asks for `plan-reviewer` at
steps 2 and 4. There is no such agent anywhere on this machine, so the challenge round you
said you most want forced has never run. Step 5 of the same file also tells the agent to use
emojis, which contradicts both your `CLAUDE.md` files.

**Agents here write through Bash, not Edit and Write.** 6,429 Bash calls against 1,640 Edit
and Write across 52 recent large sessions, because the bypass-permissions harness tells them
to prefer heredocs and `sed`. Any hook matching only `Edit|Write` is decorative on this
machine. This killed one mechanism outright.

**Compaction almost never happens.** Fourteen of 2,573 transcripts. Every workspace runs a
1M window and never fills it. A whole class of anti-drift advice does not apply here.

**Dropdowns are not available.** No HTML layer in Slack or in the Claude Code terminal. Only
GitHub. That was your question about the chat interface, and the answer is no.

**Your writing was measured.** 1,707 typed prompts, 48,664 words. Em dashes at 1.01 per
thousand against a human baseline of 3.23, semicolons at 0.39, mean sentence 14.6 words. The
style rules are now calibrated to that rather than to a published study. The gap: no long
English prose you wrote unaided and no cold outbound email, which are exactly the registers
you complained about.

## What was built

Seven artefacts in `framework/` and two scripts. All tested except the three marked.

| | |
|---|---|
| `framework/hooks/reanchor.py` | Re-injects the plan into every session and every subagent. Tested against a live subagent |
| `framework/hooks/instructions_log.py` | Logs which instruction files actually load. Tested |
| `framework/agents/plan-reviewer.md` | The subagent `/create_plan` has been calling into the void. Not yet run |
| `framework/skills/write-external/SKILL.md` | Loads the style at the moment of drafting. Not yet run |
| `framework/output-styles/steering.md` | Reply format for supervising several agents. Not yet run |
| `framework/style/CORE.md` | House style, 215 lines, calibrated to your corpus |
| `framework/templates/PLAN.template.md` | The plan file |
| `framework/experimental/` | The contract gate, parked, with a README on why |
| `scripts/install_framework.py` | Symlink installer, dry run by default, `--uninstall` |
| `scripts/agent_inventory.py` | Maps every Claude Code surface on the machine |

## Where the detail is

| File | What |
|---|---|
| `00-STATE.md` | The brief restated, and the status of every step |
| `01-machine-map.md` | Every directory Claude Code has run in, ranked, with what loads where |
| `06-design-v2.md` | The design. Read its first section, which lists what round 2 changed |
| `03-rollout.md` | How the framework reaches every agent, and what it cannot reach |
| `07-per-repo-update-sheet.md` | The update sequence applied per repo |
| `04-verification-results.md` | Twelve empirical results, with what each does and does not prove |
| `05-roald-writing-profile.md` | Your measured writing, and why it is the wrong register for half of what it is used for |
| `challenges/01-...md`, `challenges/02-...md` | Two adversarial passes, 22 and 28 findings. Round 2 found six real bugs in code that had already been tested |
| `research/` | Five research files, sources rated and cross-verified |

## What I would not claim

Every empirical probe ran on Haiku 4.5 for cost while this machine runs Opus 5. The
mechanical results hold regardless — which hooks fire, what their payloads carry, what
loads. Two behavioural results do not transfer and are marked as such.

The intake procedure and the orchestration skill are designed and not built, because the
command-usage finding says you would not invoke them. That problem is not solved.
