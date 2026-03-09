# Local Claude Companion

Delegate your knowledge monitoring to a proactive assistant that runs from your Claude Code account. It monitors your email, calendar, meetings, and Slack — then messages you on Slack with what matters.

## What you'll need

- **macOS** (the companion runs as a background service using launchd)
- **Claude Code** installed and open
- **Slack** connected in Claude Code (required)
- Gmail, Calendar, Fireflies, Google Drive are optional — the companion works with whatever you have connected

## Get Started (3 minutes)

1. Open Claude Code (anywhere — no need to download anything first).
2. Paste this into the chat:<br>
   `Clone https://github.com/roaldp/roald, then set it up end-to-end: run ./scripts/setup.sh, resolve any issues it reports (you may need to connect Slack under /integrations in Claude Code), then run ./scripts/start.sh to start the companion as a background service. Tell me once it's running and what I should expect from the first Slack message.`
3. Watch for a Slack DM — your companion is running.

That's it. Claude handles the rest.

## What it does

- **Monitors your knowledge sources** every 30 minutes (email, calendar, meetings, Slack)
- **Tries to resolve to-dos** — drafts replies, preps meeting briefs, flags action items before you see them
- **DMs you on Slack** only when something needs your attention or has been acted on
- **Responds to your DMs** — ask questions, delegate tasks, get context on anything it knows
- **Pushes for inbox zero** around 5pm with ready-to-send draft replies
- **Adapts to your schedule** — active during work hours, quiet in the evenings

### Example things you can DM your companion

- "What's on my calendar today?"
- "Prep me for my 2pm meeting"
- "What did we discuss in the product sync?"

---

## How it works

### The Mind

`mind.md` is the companion's persistent working memory. It tracks active context, pending tasks, inbox progress, and recent events with local timestamps.

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

---

## Setup details

The setup script (`scripts/setup.sh`):
- Verifies local prerequisites (`claude`, `python3`)
- Creates `config.yaml` from `config.template.yaml` when missing
- Auto-detects your timezone from macOS system settings
- Auto-resolves your Slack user ID via Slack MCP
- Checks which apps are connected to Claude Code

The start script (`scripts/start.sh`) registers the companion as a **persistent background service** using macOS launchd. It keeps running when your screen is locked or the machine sleeps, and restarts automatically after a reboot. To stop it: `bash scripts/start.sh stop`.

### Slack ID fallback (if Claude cannot resolve it automatically)

1. Send a DM to yourself in Slack.
2. Copy that message URL.
3. Give the URL to Claude Code and ask it to extract your user ID and DM channel ID.

---

## Privacy

Runtime state files may contain private data and are gitignored:

- `mind.md`
- `knowledge/`
- `logs/`
- `config.yaml`
- `.context/`

Commit-safe templates live under `templates/`.
