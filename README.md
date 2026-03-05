# Local Claude Companion

**Personal note:** turns your local Claude Code account into a companion by running a recurring heartbeat (pulse) as a proactive assistant that communicates over Slack. 

## Quick Setup:
1. Ask Claude/Cursor to set up the project dependencies
2. Add your Slack user ID to `config.yaml` (DM yourself on Slack, copy the URL — the ID starts with `U`)
3. Run `python3 -u pulse.py`


## How It Works

### The Mind

`mind.md` is the agent's persistent working memory: a single markdown file that carries state across every session. It tracks active context, pending tasks, an inbox zero countdown (with proposed actions for each open email), and a rolling event log. Every entry is timestamped with local time so the agent always knows where it is in the day.

### The Pulse

The pulse is the heartbeat of the system. It runs in two modes:

**Full pulse:** fires every 30 minutes. Scans Slack, Gmail, Fireflies transcripts, and Calendar for updates since the last run. Extracts action items, saves context to `knowledge/`, and updates `mind.md`. Notifies you on Slack only for urgent items or EOD inbox nudges, never for routine updates.

**Reactive pulse:** fires instantly when you send a Slack DM. Reads your message, loads `mind.md` for context, and responds directly. No full source scan, no noise.

### Time-Aware Urgency

The agent knows what time it is and behaves accordingly:

| Time | Mode |
|---|---|
| Morning | Surface new items, plan the day |
| Afternoon | Propose quick wins, flag open items |
| Late afternoon (17–18h) | Inbox zero push — drafts replies before nudging you |
| Evening | Urgent items only |

EOD nudges are always solution-first: *"3 emails still open — I've drafted replies for 2, the 3rd needs your call on the budget. Want me to send the drafts?"*

### Knowledge Store

Detailed context (meeting summaries, email threads, notes) lives in `knowledge/` as plain markdown files, indexed in `knowledge/index.md`. The agent reads the index to find relevant files at runtime — no vector DB needed for MVP.

## Privacy model

- **Be aware:** runtime state files usually contain personal/sensitive data and are ignored:
  - `mind.md`
  - `knowledge/`
  - `logs/`
  - `config.yaml`
  - `.context/`
- Commit-safe templates are provided under `templates/`.

## First-time manual local setup

1. Copy config template:
   - `cp config.template.yaml config.yaml`
2. Fill local values in `config.yaml` (Slack IDs, timezone).
3. Run:
   - `python3 pulse.py`

If `mind.md` or `knowledge/index.md` are missing, `pulse.py` auto-initializes them from templates.
