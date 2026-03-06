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

### Quick test via Claude Code (paste this prompt)

Open Claude Code locally in the `roald` repo directory and paste:

```
Test the dashboard feature end-to-end. Do these steps in order:

1. Install pyyaml if needed: pip install pyyaml
2. Start the dashboard server in the background: python3 dashboard/server.py &
3. Wait 2 seconds, then curl http://localhost:7888/ and verify the HTML loads with title "Roald — Companion Dashboard"
4. Test each API endpoint and report what you get:
   - curl -s http://localhost:7888/api/status | python3 -m json.tool
   - curl -s http://localhost:7888/api/mind/raw | python3 -m json.tool
   - curl -s http://localhost:7888/api/logs?lines=50 | python3 -m json.tool
   - curl -s http://localhost:7888/api/knowledge | python3 -m json.tool
   - curl -s http://localhost:7888/api/knowledge/file?path=nonexistent.md | python3 -m json.tool
   - curl -s http://localhost:7888/api/doesnotexist | python3 -m json.tool
5. Verify static assets load:
   - curl -s http://localhost:7888/css/style.css | head -5
   - curl -s http://localhost:7888/js/app.js | head -5
6. Test with mock data — create a minimal mind.md from the template, then re-check /api/status to see if sections parse correctly
7. Kill the dashboard background process when done
8. Report a summary: which endpoints work, which fail, any errors found

Expected results:
- /api/status returns JSON with keys: running, locked, mind_exists, stats, config, sources, tasks, events
- /api/mind/raw returns {"content": ""} or the mind.md contents
- /api/logs returns {"entries": [...]}
- /api/knowledge returns {"index": [...], "files": {"meetings": [], "emails": [], "notes": []}}
- /api/knowledge/file returns {"content": ""} for missing files
- /api/doesnotexist returns {"error": "Unknown endpoint"}
- Static files (CSS, JS, HTML) all load with correct content
```

### Manual browser test (for visual verification)

After confirming the API works via Claude Code above, open the dashboard yourself:

```bash
cd roald
python3 dashboard/server.py
```

Open http://localhost:7888 and walk through these checks:

**Overview tab:**
- [ ] Page loads with title "Roald — Companion Dashboard"
- [ ] Status badge shows **Offline** (no companion running) or **Running** (companion active)
- [ ] Clock updates every second in the top-right
- [ ] Stats row shows pulse counts (or "—" if no pulses yet)
- [ ] Sources, Active Context, Pending Tasks, Inbox Tracker, Recent Events all render
- [ ] Footer countdown ticks from 10 to 0 and auto-refreshes

**Mind tab:**
- [ ] Shows raw `mind.md` contents in a code block
- [ ] Refresh button works
- [ ] Shows "not found" message if `mind.md` doesn't exist

**Knowledge tab:**
- [ ] Three columns: Meetings, Emails, Notes
- [ ] Clicking a file opens preview panel; Close button hides it
- [ ] Knowledge Index renders

**Logs tab:**
- [ ] Log entries appear with timestamps
- [ ] Line count selector (50/100/250/500) works
- [ ] Auto-scroll checkbox keeps view at bottom

**Config tab:**
- [ ] Shows Timezone, Pulse Interval, Slack Poll Interval, Claude Model
- [ ] Source toggles show Enabled/Disabled
- [ ] Next Pulse Instructions and Preferences sections render

**Tab switching:**
- [ ] Each tab switches content cleanly
- [ ] Only one tab active at a time

**Edge cases:**
- [ ] Stop companion → dashboard shows "Offline" on next refresh
- [ ] Delete `mind.md` → Overview shows empty state
- [ ] Alternative port works: `DASHBOARD_PORT=7889 python3 dashboard/server.py`
