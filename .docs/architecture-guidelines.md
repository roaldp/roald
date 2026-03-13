# Roald Architecture Guidelines

## Purpose

This document is the design baseline for feature workplans, PR reviews, and branch reviews in Roald.
Use it to judge whether new work strengthens or weakens the core product intention.

## Product Intention

Roald is a proactive AI companion that aggregates the user's working context across meetings, email, calendar, Slack, and related knowledge sources, then uses that context to reduce low-value work and keep the human prepared.

The product is not a generic chat shell. It should notice, prepare, draft, remind, and resolve where possible before the user asks.

## Core Principles

1. Be proactive, not passive.
   The default behavior is to scan, prepare, draft, and surface useful actions. Reactive chat is important, but it is the secondary mode.

2. Aggregate real user context.
   Product value comes from combining transcripts, email, calendar, Slack, and evolving memory into one working model of the human's world.

3. Optimize for preparedness and task reduction.
   Features should help the user arrive prepared, close loops faster, and offload repetitive coordination work.

4. Keep the user out of the plumbing.
   Setup, uptime, and updates should be handled for the user. The product should not require technical babysitting.

5. Design for non-technical users.
   New capabilities should feel simple from the user's point of view, even if the implementation is complex.

6. Slack is the primary interface.
   Notifications, summaries, follow-ups, and reactive interactions should work cleanly in Slack first.

7. Claude Code is the execution substrate.
   Roald should leverage the locally installed Claude Code runtime and its MCP integrations rather than rebuilding a parallel integration platform.

8. Fail gracefully and quietly.
   Temporary source failures should degrade without drama. User-facing alerts should happen only when action is required.

## Current Architectural Shape

The current implementation already reflects the intended direction:

- `pulse.py` runs the companion event loop locally.
- Full pulses perform broad monitoring and memory updates.
- Reactive pulses handle inbound Slack messages quickly without doing a full scan.
- Runtime memory lives in local markdown files (`mind.md`, `knowledge/`), initialized from `templates/`.
- Behavior is defined primarily through prompt contracts in `prompts/`.
- Integrations are reached through Claude Code MCP tools, not direct vendor SDKs.
- The companion is kept alive as a background service through `launchd` via `scripts/start.sh`.
- Updates are handled in-product through the built-in git-based auto-update loop.

This means Roald is currently:

- local-first
- Slack-first
- Claude-orchestrated
- prompt-driven
- file-backed for state
- designed to self-manage operations where possible

New work should preserve those properties unless there is a strong, explicit reason to change them.

## Design Guardrails

### Prefer extending the pulse model

If a feature can be expressed as:

- new source scanning logic
- better memory structure
- better proactive decision rules
- better reactive handling
- better Slack delivery

then extend the existing pulse architecture before introducing new services or surfaces.

### Prefer Claude MCP over custom integrations

If Claude Code already provides the required integration through MCP, treat that as the default path.
Do not add direct API clients, token storage, or a separate integration control plane without a clear gap that MCP cannot cover.

### Prefer local state over hosted infrastructure

The current design stores runtime knowledge locally and operates from the user's machine.
Do not introduce databases, backend services, queues, or dashboards unless the feature truly cannot be delivered within the current local model.

### Protect zero-maintenance operation

Any feature that adds manual setup, ongoing supervision, fragile auth steps, or update friction should be treated as suspect.
The user should not need to learn system internals to benefit from the companion.

### Protect Slack-first usefulness

A feature is stronger if it results in:

- better proactive Slack messages
- faster useful answers in Slack
- fewer steps between detection and action

Be cautious about adding UI surfaces that dilute the main workflow.

### Preserve trust and signal quality

The companion should not become noisy, speculative, or high-maintenance.
Features must improve relevance, timeliness, or actionability, not just increase activity.

## Non-Goals

Avoid drifting into these shapes without explicit product direction:

- a generic internal agent framework
- a web app that users must manage directly
- a manual knowledge base that depends on constant user curation
- a technical operations console for the end user
- a multi-surface product that makes Slack optional
- direct replacement of Claude Code as the orchestration/runtime layer

## Workplan Review Standard

Every feature workplan should answer these questions clearly:

1. What user problem is being removed or reduced?
2. What proactive behavior will exist after this ships?
3. Which knowledge sources are used, and how are they combined?
4. Where does state live?
5. How does the user experience the feature in Slack?
6. What happens when the source or integration is unavailable?
7. Does this reduce user effort, or does it create new setup/maintenance burden?
8. Why is this the smallest architecture change that works?

If a workplan cannot answer these, it is not ready.

## PR Review Standard

When reviewing a PR or branch, check for adherence to the following:

1. The change strengthens proactive assistance rather than just adding passive capability.
2. The user-facing workflow remains simple for a non-technical person.
3. Claude Code and MCP remain the default execution and integration path.
4. Slack remains the primary communication surface unless there is a deliberate exception.
5. Runtime state stays local and commit-safe where appropriate.
6. Failure handling is quiet, recoverable, and concrete.
7. The implementation fits the existing pulse/reactive/update model where possible.
8. The feature increases signal quality, preparedness, or task resolution speed.
9. The change does not create hidden operational burden for the user.

## Preferred Feature Shape

Strong features usually follow this loop:

1. Detect new context from connected systems.
2. Enrich or merge it into persistent memory.
3. Infer what matters now.
4. Draft or complete a useful next action.
5. Deliver only the highest-value output in Slack.
6. Keep running without user intervention.

## Current Code Anchors

Use these files as the primary architectural reference points while planning or reviewing:

- `pulse.py`: core runtime loop, Slack polling, full/reactive pulses, auto-update flow
- `prompts/pulse_full.md`: proactive monitoring contract
- `prompts/pulse_reactive.md`: Slack response contract
- `prompts/pulse_onboarding.md`: first-run experience and setup value
- `scripts/start.sh`: persistence and background execution model
- `scripts/run_loop.sh`: restart and rollback behavior
- `templates/mind.template.md`: memory structure
- `templates/knowledge_index.template.md`: knowledge indexing structure

## Decision Rule

If a proposal makes Roald more proactive, more context-aware, more self-managing, and easier for a non-technical user to benefit from in Slack, it is likely aligned.

If it adds infrastructure, surfaces, or maintenance burden without materially improving proactive usefulness, it is likely misaligned.
