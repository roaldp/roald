# Local Claude Companion

Personal note: Using your local Claude Code account to run a recurring heartbeat for a proactive assistant that communicates over Slack.

## 5 min setup

Requires [Claude Code](https://docs.anthropic.com/en/docs/claude-code) installed.

```bash
./setup.sh
```

Or manually: copy `config.template.yaml` to `config.yaml`, fill in your Slack IDs and timezone, then run `python3 pulse.py`.

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
