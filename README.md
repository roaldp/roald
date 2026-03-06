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

## Dashboard

A local web dashboard for monitoring the companion in real time.

### Start the dashboard

```bash
./scripts/dashboard.sh        # opens http://localhost:7888
# or
python3 dashboard/server.py   # manual start
```

### What it shows

| Tab | Content |
|---|---|
| **Overview** | Live status badge (Running/Pulsing/Offline), pulse stats, sources, active context, pending tasks, inbox tracker, recent events |
| **Mind** | Raw view of `mind.md` (the companion's working memory) |
| **Knowledge** | File browser for meetings, emails, and notes with preview |
| **Logs** | Tail of `pulse.log` with color-coded entries and auto-scroll |
| **Config** | Runtime configuration, next-pulse instructions, and preferences |

Auto-refreshes every 10 seconds. Requires `pyyaml` (`pip install pyyaml`).

### Testing the dashboard

See [Testing instructions for the dashboard feature](#testing-the-dashboard-feature) below.

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

---

## Testing the dashboard feature

Step-by-step instructions for a conductor to verify the dashboard works correctly.

### Prerequisites

- Python 3 installed
- `pyyaml` installed (`pip install pyyaml`)
- Repo cloned locally

### 1. Start the dashboard (cold start — no companion running)

```bash
python3 dashboard/server.py
```

Open http://localhost:7888 in your browser.

**Verify:**
- [ ] Page loads with the title "Roald — Companion Dashboard"
- [ ] Status badge shows **Offline** (red/grey)
- [ ] Clock in the top-right updates every second
- [ ] All stat cards show "—" (no data yet)
- [ ] Footer shows auto-refresh countdown from 10

### 2. Overview tab — with no data

Since neither `mind.md`, `config.yaml`, nor `logs/pulse.log` exist yet, this tests the empty state.

**Verify:**
- [ ] Companion Status shows: Process = "Not running", Mind File = "Not created"
- [ ] Sources shows "No sources configured"
- [ ] Active Context, Pending Tasks, Inbox Zero Tracker, Recent Events all show placeholder text
- [ ] No JS errors in the browser console

### 3. Overview tab — with data

Start the companion so it generates runtime files:

```bash
./scripts/start.sh
```

Wait for the first pulse to complete (2–5 min), then check the dashboard.

**Verify:**
- [ ] Status badge switches to **Running** (green) or **Pulsing** (amber if a pulse is in progress)
- [ ] Stats populate: Total Pulses ≥ 1, Full Pulses ≥ 1
- [ ] Last Pulse shows a timestamp
- [ ] Sources list shows each configured source with its status (active / awaiting / unavailable)
- [ ] Active Context and Pending Tasks populate from `mind.md`
- [ ] Recent Events shows at least one entry
- [ ] Data refreshes automatically every 10 seconds (watch the countdown)

### 4. Mind tab

Click the **Mind** tab.

**Verify:**
- [ ] Raw contents of `mind.md` are displayed in a code block
- [ ] "Refresh" button reloads the content
- [ ] If `mind.md` doesn't exist, shows "mind.md not found — companion has not run yet."

### 5. Knowledge tab

Click the **Knowledge** tab.

**Verify:**
- [ ] Three columns: Meetings, Emails, Notes
- [ ] If knowledge files exist, they appear as clickable items with name and modified date
- [ ] Clicking a file opens a preview panel below with the file contents
- [ ] "Close" button hides the preview
- [ ] Knowledge Index section shows indexed entries (or "No knowledge indexed yet")

### 6. Logs tab

Click the **Logs** tab.

**Verify:**
- [ ] Log entries appear with timestamps in brackets
- [ ] Color coding works: errors in red, TOOL entries highlighted, SLACK entries highlighted, pulse entries highlighted
- [ ] Line count selector (50/100/250/500) reloads with the selected number of lines
- [ ] Auto-scroll checkbox keeps the view at the bottom
- [ ] "Refresh" button reloads the log
- [ ] If no log file exists, the viewer is empty (no errors)

### 7. Config tab

Click the **Config** tab.

**Verify:**
- [ ] Configuration grid shows: Timezone, Full Pulse Interval, Slack Poll Interval, Claude Model
- [ ] Slack User ID shows "Set" or "Not set" as appropriate
- [ ] Each enabled source shows "Enabled" (green) or "Disabled" (orange)
- [ ] Next Pulse Instructions and Preferences sections render content from `mind.md`

### 8. Tab switching

**Verify:**
- [ ] Clicking each tab (Overview → Mind → Knowledge → Logs → Config) switches content
- [ ] Only one tab is highlighted/active at a time
- [ ] Returning to Overview still shows up-to-date data

### 9. Auto-refresh

**Verify:**
- [ ] Footer countdown decrements from 10 to 0
- [ ] At 0, data reloads and countdown resets to 10
- [ ] If you trigger a pulse mid-countdown, the next refresh picks up the new data

### 10. API endpoints (optional, for deeper validation)

Test the API directly with curl:

```bash
# Status endpoint — returns full companion state
curl -s http://localhost:7888/api/status | python3 -m json.tool

# Logs endpoint — returns parsed log entries
curl -s http://localhost:7888/api/logs?lines=50 | python3 -m json.tool

# Knowledge listing
curl -s http://localhost:7888/api/knowledge | python3 -m json.tool

# Mind raw content
curl -s http://localhost:7888/api/mind/raw | python3 -m json.tool

# Knowledge file preview (replace filename)
curl -s "http://localhost:7888/api/knowledge/file?path=example.md" | python3 -m json.tool
```

**Verify:**
- [ ] Each endpoint returns valid JSON with no errors
- [ ] `/api/status` includes: `running`, `locked`, `mind_exists`, `stats`, `config`, `sources`, `tasks`, `events`
- [ ] `/api/logs` returns `entries` array with `timestamp` and `message` fields
- [ ] `/api/knowledge` returns `index` and `files` with `meetings`, `emails`, `notes` arrays
- [ ] `/api/knowledge/file` returns file content (or empty string for missing files)
- [ ] Unknown endpoints return `{"error": "Unknown endpoint"}`

### 11. Edge cases

- [ ] Stop the companion (`Ctrl+C` on `start.sh`), verify dashboard shows "Offline" on next refresh
- [ ] Delete `mind.md`, verify Overview shows empty state and Mind tab shows "not found" message
- [ ] Start a second dashboard instance on a different port: `DASHBOARD_PORT=7889 python3 dashboard/server.py` — verify it works independently
- [ ] Rapidly switch tabs — no crashes or stale data
