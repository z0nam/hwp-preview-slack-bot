#!/usr/bin/env bash
# Launch the HWP preview Slack bot in Socket Mode.
# Reads tokens from .env in repo root.
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ ! -f .env ]]; then
  echo "ERROR: .env not found in $(pwd)" >&2
  echo "Copy .env.example to .env and fill in SLACK_BOT_TOKEN / SLACK_APP_TOKEN." >&2
  exit 1
fi

exec uv run python -m hwp_preview_slack_bot
