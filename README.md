# Local Claude Companion

Run a personal, proactive assistant from your local Claude Code account. It checks your enabled sources on a pulse and communicates via Slack DM.

## Quick Setup (2-3 min)

1. Clone the repo and open it in Claude Code.
2. Paste this in Claude Code:
   `Set up this project end-to-end. Run ./scripts/setup.sh, resolve any blockers, set up Slack IDs if possible. Then run ./scripts/start.sh to start the companion. If start.sh fails, tell me what went wrong and how to start it manually.`
3. The companion starts automatically. Watch for a Slack DM — the first full pulse takes 2–5 minutes.

This keeps setup simple for users while still letting Claude handle the details.

## What setup does

- Verifies local prerequisites (`claude`, `python3`, `pyyaml`).
- Creates `config.yaml` from `config.template.yaml` when missing.
- Applies guided defaults (for example timezone).
- Auto-resolves your Slack user ID via MCP if possible.
- Shows unresolved user-specific values clearly (`slack_user_id`, `slack_channel_id`).
- Runs a best-effort MCP integration check for required sources.
- Starts the companion in a new Terminal window (macOS), or as a background process if that fails.

## Slack ID fallback (if Claude cannot resolve it automatically)

1. Send a DM to yourself in Slack.
2. Copy that message URL.
3. Give the URL to Claude Code and ask it to extract/store your user ID (`U...`) and DM channel ID.

## How It Works

### The Mind

`mind.md` is the agent's persistent working memory. It tracks active context, pending tasks, inbox progress, and recent events with local timestamps.

### The Pulse

The pulse runs in two modes:

- **Full pulse:** every 30 minutes. Scans enabled sources, stores context in `knowledge/`, updates `mind.md`, and only sends Slack for urgent or high-value updates.
- **Reactive pulse:** triggered by your Slack DM. Responds quickly with context, without doing a full scan.

### Time-Aware Urgency

| Time | Mode |
|---|---|
| Morning | Surface new items and plan the day |
| Afternoon | Propose quick wins and flag open items |
| Late afternoon (17–18h) | Inbox-zero push with ready-to-send drafts |
| Evening | Urgent items only |

### Knowledge Store

Detailed context (meetings, emails, notes) is saved as markdown in `knowledge/` and indexed in `knowledge/index.md`.

## Privacy model

Runtime state files may contain private data and are gitignored:

- `mind.md`
- `knowledge/`
- `logs/`
- `config.yaml`
- `.context/`

Commit-safe templates live under `templates/`.

## Notes

- If `mind.md` or `knowledge/index.md` are missing, `pulse.py` initializes them from templates.
- MCP tools must be enabled in Claude Code for sources you want to monitor (Slack, Gmail, Fireflies, Calendar, Google Drive).
