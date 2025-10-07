#!/bin/bash
# GCP VM에서 Discord-Notion 봇 상태를 빠르게 진단하는 스크립트

set -euo pipefail

PROJECT_ID="${PROJECT_ID:-n8n-ai-work-agent-automation}"
LOG_PATH="${LOG_PATH:-$HOME/001_discord_to_notion/bot.log}"
SECRETS=(
  discord-bot-token
  youtube-api-key
  gemini-api-key
  notion-api-key
  notion-database-id
)

printf '=== bot.log tail (last 50 lines) ===\n'
if [[ -f "$LOG_PATH" ]]; then
  tail -n 50 "$LOG_PATH"
else
  printf 'WARNING: log file not found: %s\n' "$LOG_PATH"
fi

printf '\n=== Secret Manager access check ===\n'
for secret in "${SECRETS[@]}"; do
  printf ' - %s... ' "$secret"
  if gcloud secrets versions access latest --secret="$secret" --project="$PROJECT_ID" >/dev/null 2>&1; then
    printf 'ok\n'
  else
    printf 'FAILED (check permissions/secret name)\n'
  fi
  sleep 0.2
fi

printf '\n=== Environment variable summary ===\n'
for key in DISCORD_BOT_TOKEN YOUTUBE_API_KEY GEMINI_API_KEY NOTION_API_KEY NOTION_DATABASE_ID; do
  value="${!key:-}"
  if [[ -n "$value" ]]; then
    printf '%s: set (length %d)\n' "$key" "${#value}"
  else
    printf '%s: not set\n' "$key"
  fi
done

printf '\nTip: override PROJECT_ID or LOG_PATH via environment variables.\n'
