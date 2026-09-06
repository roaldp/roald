# How work runs on this machine

Roald does not type slash commands and will not invoke a skill by name. If a skill should
run, you invoke it. Read the skill listing at the start of a job and pick, the same way you
would pick a tool.

## Route by the shape of the request

| What the request looks like | Invoke |
|---|---|
| Long, dictated, more than one goal, or an outcome with no named work | `scope-brief` |
| A decided piece of work with nothing written down yet | `create_plan` |
| A plan exists and has not been attacked | `check_plan`, or the `plan-reviewer` subagent |
| A plan exists and it is time to build | `implement_plan` |
| Anything a person outside the team will read | `write-external` |
| Code written, before a pull request | `check_coding_conventions` |
| A branch is finished | `create_PR` |
| Commit and push | `push_all_changes_to_git` |
| Something is wrong with the agent setup itself | `agent-system-audit` |

Say in one line which one you are running and why. Do not ask permission first.

## Three standing rules

**Long brief, then execute.** Roald would rather explain once at length than be interrupted
every few minutes. Interruptions cost him a context switch across several parallel
workspaces. Front-load the questions, cap them at three, and attach your own proposed
answer to each so he can reply "yes".

**Scope to a number before scoping to a feature.** Archer mode, inside `scope-brief`. Any
job worth a plan gets one metric with a unit, the value it holds today, the value that makes
the work worth doing, and the date the number gets read. The MVP is then whatever is
smallest that moves that number to that threshold, and everything cut is written down. If
there is genuinely no number, use an observable event as a proxy. Never skip it and never
invent one.

**Delegate the doing.** On a job with more than two steps, hold the plan and give each step
to a subagent, one at a time. Fan out for reading, research and review. Do not fan out for
writing to the same code. A subagent inherits nothing, so its brief must carry the plan
path, its one step, the success criterion, the output path, and what it must not do.

## Punctuation, everywhere, including in chat

No em dash. The character is `—`, the long one. Use a comma, a full stop, a colon, or a
comma with "and", "so" or "but". A hyphen in a compound word is fine.

No semicolon. The character is `;`. Split the sentence.
