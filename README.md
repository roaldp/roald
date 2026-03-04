# Local Claude Companion

Personal note: Using your local Claude Code account to run a recurring heartbeat for a proactive assistant that communicates over Slack.

## 5 min setup:
Ask Claude how to set up this project. Get your Slack ID (dm yourself, copy url, drop in Claude)

## Privacy model

- Runtime state files can contain personal/sensitive data and are ignored:
  - `mind.md`
  - `knowledge/`
  - `logs/`
  - `config.yaml`
  - `.context/`
- Commit-safe templates are provided under `templates/`.

## First-time local setup

1. Copy config template:
   - `cp config.template.yaml config.yaml`
2. Fill local values in `config.yaml` (Slack IDs, timezone).
3. Run:
   - `python3 pulse.py`

If `mind.md` or `knowledge/index.md` are missing, `pulse.py` auto-initializes them from templates.
