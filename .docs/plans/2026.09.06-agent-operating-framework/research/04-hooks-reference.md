# Claude Code hooks, verified September 2026 against CLI v2.1.261

Sources: `code.claude.com/docs/en/hooks`, `.../hooks-guide`, `.../settings`,
`.../managed-settings`, and `CHANGELOG.md` in `anthropics/claude-code`. The
`docs.claude.com` and `platform.claude.com` Claude Code paths now permanently redirect
to `code.claude.com`; the content is the same official documentation.

Hooks matter here because they are the only surface that **enforces** rather than
asks. Everything in `CLAUDE.md` is a request the model may ignore. A hook runs whether
the model cooperates or not.

## The event list

Thirty-two events exist, not the nine that older write-ups describe:

`SessionStart`, `Setup`, `UserPromptSubmit`, `UserPromptExpansion`, `PreToolUse`,
`PermissionRequest`, `PermissionDenied`, `PostToolUse`, `PostToolUseFailure`,
`PostToolBatch`, `Notification`, `MessageDisplay`, `SubagentStart`, `SubagentStop`,
`TaskCreated`, `TaskCompleted`, `Stop`, `StopFailure`, `TeammateIdle`,
`InstructionsLoaded`, `ConfigChange`, `CwdChanged`, `DirectoryAdded`, `FileChanged`,
`WorktreeCreate`, `WorktreeRemove`, `PreCompact`, `PostCompact`, `PreModelSwitch`,
`PostModelSwitch`, `Elicitation`, `ElicitationResult`, `SessionEnd`.

Version each was added, from the changelog: `Setup` v2.1.10, `SubagentStart` v2.0.43,
`PermissionRequest` v2.0.45, `TeammateIdle` and `TaskCompleted` v2.1.33, `ConfigChange`
v2.1.49, `WorktreeCreate` and `WorktreeRemove` v2.1.50, `InstructionsLoaded` v2.1.69,
`Elicitation` and `ElicitationResult` v2.1.76, `StopFailure` v2.1.78, `CwdChanged` and
`FileChanged` v2.1.83, `TaskCreated` v2.1.84, `PermissionDenied` v2.1.89,
`MessageDisplay` v2.1.152, `DirectoryAdded` v2.1.219, `PreModelSwitch` and
`PostModelSwitch` v2.1.251.

`UserPromptExpansion` and `PostToolBatch` are in the current docs but no "Added" entry
was found for either in the changelog. Treat their availability as unconfirmed by date.

## The five events this framework would use

| Event | Why |
|---|---|
| `SessionStart` | Inject the active plan file and current step into every new session, including resumes and post-compact restarts. Matcher: `startup\|resume\|clear\|compact\|fork`. |
| `SubagentStart` | Inject the same anchor into every subagent. A subagent inherits no parent context, so this is the only automatic way to keep a delegated worker on-plan. |
| `PreCompact` | Force the compaction summary to carry the plan path and current step, so the plan survives the one moment it is most likely to be lost. |
| `Stop` | Check the transcript against the plan's success criteria before the turn ends, and inject a correction if a step was skipped. This is what `/goal` does natively. |
| `PostToolUse` on `Edit\|Write` | Run the style linter on any markdown or outbound copy the agent just wrote, and block on failure. This is how a writing rule becomes enforced rather than requested. |

## Injecting context

`additionalContext` is supported on `SessionStart`, `SubagentStart`, `UserPromptSubmit`,
`UserPromptExpansion`, `PreToolUse`, `PostToolUse`, `PostToolUseFailure`,
`PostToolBatch`, `Stop`, `SubagentStop` and `PostModelSwitch`.

It must be nested under `hookSpecificOutput.additionalContext`, not placed at the top
level. It is capped at 10,000 characters; overflow is written to a file and only a
preview is injected.

```json
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "Active plan: .docs/plans/…/PLAN.md, step 3 of 7."
  }
}
```

## Blocking a tool call

Two equivalent mechanisms on `PreToolUse`:

1. Exit code 2 with a message on stderr. Blocks unconditionally, and no JSON can
   override it.
2. Exit code 0 with
   `{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"…"}}`.

`permissionDecision` on `PreToolUse` takes `allow`, `deny`, `ask` or `defer`, with
precedence deny, then defer, then ask, then allow. `PreToolUse` has deprecated the
top-level `decision` and `reason` fields; the old `approve` and `block` map to `allow`
and `deny`. Other events, including `PostToolUse` and `Stop`, still use top-level
`decision` and `reason`.

`PostToolUse` additionally supports `updatedToolOutput`, which replaces the tool result
Claude sees, and `classifierContext` (v2.1.236 and later) for auto mode.

## Exit codes

- **0** — success. Stdout is parsed as JSON when it starts with `{` and ends with `}`,
  otherwise treated as plain text. Only `UserPromptSubmit`, `UserPromptExpansion`,
  `SessionStart` and `PostModelSwitch` treat plain-text stdout as injected context.
- **2** — blocking error. Blocks regardless of any JSON returned. Elicitation events
  ignore `hookSpecificOutput` on exit 2.
- **Anything else** — non-blocking, but a validly parsed JSON object's fields are still
  honoured. Invalid or absent JSON surfaces as a `<hook name> hook error`.
  `WorktreeCreate` is the exception: any non-zero exit fails it regardless of JSON.

## Universal JSON output fields

```json
{
  "continue": true,
  "stopReason": "shown to the user only, when continue is false",
  "suppressOutput": false,
  "systemMessage": "shown to the user and the transcript; some events discard it",
  "terminalSequence": "ANSI OSC 0/1/2/9/99/777 or BEL only"
}
```

`continue: false` stops the session entirely and takes precedence over event-specific
fields. `suppressOutput` is documented as a no-op: accepted and ignored.

## Common input fields

Every event receives `session_id`, `prompt_id` (v2.1.196 and later),
`transcript_path`, `cwd`, `permission_mode` (`default`, `plan`, `acceptEdits`, `auto`,
`dontAsk`, `bypassPermissions`), `effort.level` (`low`, `medium`, `high`, `xhigh`,
`max`) and `hook_event_name`. Inside a subagent it also receives `agent_id` and
`agent_type`.

Per-event fields worth knowing for this design:

- `PreToolUse`: matcher is the tool name, for example `Bash`, `Edit|Write` or
  `mcp__.*`. Fields `tool_name`, `tool_input`, `tool_use_id`.
- `PostToolUse`: matcher is the tool name. Adds `tool_response` — note the name, it is
  not `tool_result` — and `duration_ms`.
- `UserPromptSubmit`: no matcher. The field is `prompt`.
- `SessionStart`: matcher `startup|resume|clear|compact|fork`. Fields `source`, and
  optionally `model`, `agent_type`, `session_title`. On resume and fork it also carries
  `seconds_since_last_response`, `context_tokens`, `prompt_cache_likely_expired` and
  `estimated_cache_write_usd` (v2.1.251 and later).
- `Stop` and `SubagentStop`: no matcher on `Stop`; `SubagentStop` matches agent type.
  Field `last_assistant_message`.
- `PreCompact` and `PostCompact`: matcher `manual|auto`. Fields `trigger` and
  `custom_instructions` on `PreCompact`, `compact_summary` on `PostCompact`.
- `FileChanged`: matcher is a literal filename. Fields `file_path`, `change_type`.
- `ConfigChange`: matcher `user_settings|project_settings|local_settings|policy_settings|skills`.

## Settings file locations and precedence

| Scope | Path |
|---|---|
| User | `~/.claude/settings.json` |
| Project, shared | `.claude/settings.json` |
| Project, local | `.claude/settings.local.json`, automatically gitignored |
| Managed, macOS | `/Library/Application Support/ClaudeCode/managed-settings.json` |
| Managed, Linux and WSL | `/etc/claude-code/managed-settings.json` |
| Managed, Windows | `C:\Program Files\ClaudeCode\managed-settings.json` |

Precedence, highest first: managed, then the `--settings` CLI flag, then project local,
then shared project, then user.

## Hook configuration schema

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "...",
            "args": [],
            "timeout": 600,
            "if": "Bash(rm *)",
            "async": false
          }
        ]
      }
    ]
  }
}
```

`type` takes `command`, `http`, `mcp_tool`, `prompt` or `agent`. A `prompt` hook runs a
model call; an `agent` hook runs a subagent. Both are relevant to us — a `Stop` hook of
type `prompt` is how `/goal` is implemented.

Default timeouts: 600 seconds for `command`, `http` and `mcp_tool`; 30 seconds for
`prompt`; 60 seconds for `agent`. Lowered to 30 seconds for `UserPromptSubmit`,
`PreModelSwitch` and `PostModelSwitch`; 10 seconds for `MessageDisplay`; and 1.5 seconds,
extensible to 60, for `SessionEnd`.

Other fields: `statusMessage`, `once` (skill frontmatter only), and `if`, which takes
permission-rule syntax and works on tool events only.
