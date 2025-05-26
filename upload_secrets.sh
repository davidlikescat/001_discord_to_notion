#!/bin/bash

# ====================================================================
# 필수 설정: 본인의 GCP 프로젝트 ID로 변경해주세요!
PROJECT_ID="n8n-ai-work-agent-automation"
# ====================================================================

echo "=== Secret Manager에 API 키 저장 시작 ==="

# Claude API Configuration
echo -n "***CLAUDE_API_KEY_REDACTED***" | gcloud secrets create claude-api-key --data-file=- --project="${PROJECT_ID}" --replication-policy="automatic"
echo "claude-api-key 저장 완료"

# Notion API Configuration
echo -n "***NOTION_API_KEY_REDACTED***" | gcloud secrets create notion-api-key --data-file=- --project="${PROJECT_ID}" --replication-policy="automatic"
echo "notion-api-key 저장 완료"

echo -n "***NOTION_PAGE_ID_REDACTED***" | gcloud secrets create notion-page-id --data-file=- --project="${PROJECT_ID}" --replication-policy="automatic"
echo "notion-page-id 저장 완료"

echo -n "***NOTION_DATABASE_ID_REDACTED***" | gcloud secrets create notion-database-id --data-file=- --project="${PROJECT_ID}" --replication-policy="automatic"
echo "notion-database-id 저장 완료"

# Apple App-specific Password
echo -n "***APPLE_APP_PASSWORD_REDACTED***" | gcloud secrets create apple-app-password --data-file=- --project="${PROJECT_ID}" --replication-policy="automatic"
echo "apple-app-password 저장 완료"

# OpenAI Configuration
echo -n "***OPENAI_API_KEY_REDACTED***" | gcloud secrets create openai-api-key --data-file=- --project="${PROJECT_ID}" --replication-policy="automatic"
echo "openai-api-key 저장 완료"

# Discord Bot Configuration
echo -n "***DISCORD_BOT_TOKEN_REDACTED***" | gcloud secrets create discord-bot-token --data-file=- --project="${PROJECT_ID}" --replication-policy="automatic"
echo "discord-bot-token 저장 완료"

echo -n "***DISCORD_CHANNEL_ID_REDACTED***" | gcloud secrets create discord-channel-id --data-file=- --project="${PROJECT_ID}" --replication-policy="automatic"
echo "discord-channel-id 저장 완료"

# MIRO Configuration
echo -n "***MIRO_ACCESS_TOKEN_REDACTED***" | gcloud secrets create miro-access-token --data-file=- --project="${PROJECT_ID}" --replication-policy="automatic"
echo "miro-access-token 저장 완료"

echo -n "***MIRO_CLIENT_ID_REDACTED***" | gcloud secrets create miro-client-id --data-file=- --project="${PROJECT_ID}" --replication-policy="automatic"
echo "miro-client-id 저장 완료"

echo -n "***MIRO_SECRET_REDACTED***" | gcloud secrets create miro-secret --data-file=- --project="${PROJECT_ID}" --replication-policy="automatic"
echo "miro-secret 저장 완료"

# Google Cloud Console Configuration (OAuth 관련 ID/Secret은 API Key와 다르게 관리)
echo -n "***GOOGLE_CLIENT_ID_REDACTED***" | gcloud secrets create google-client-id --data-file=- --project="${PROJECT_ID}" --replication-policy="automatic"
echo "google-client-id 저장 완료"

echo -n "***GOOGLE_CLIENT_SECRET_REDACTED***" | gcloud secrets create google-client-secret --data-file=- --project="${PROJECT_ID}" --replication-policy="automatic"
echo "google-client-secret 저장 완료"

echo -n "***GOOGLE_REFRESH_TOKEN_REDACTED***" | gcloud secrets create google-refresh-token --data-file=- --project="${PROJECT_ID}" --replication-policy="automatic"
echo "google-refresh-token 저장 완료"

echo -n "***GOOGLE_SHEETS_API_KEY_REDACTED***" | gcloud secrets create google-sheets-api-key --data-file=- --project="${PROJECT_ID}" --replication-policy="automatic"
echo "google-sheets-api-key 저장 완료"

# Google APIs (별도로 분리된 항목들)
echo -n "***GEMINI_API_KEY_REDACTED***" | gcloud secrets create gemini-api-key --data-file=- --project="${PROJECT_ID}" --replication-policy="automatic"
echo "gemini-api-key 저장 완료"

echo -n "***YOUTUBE_API_KEY_REDACTED***" | gcloud secrets create youtube-api-key --data-file=- --project="${PROJECT_ID}" --replication-policy="automatic"
echo "youtube-api-key 저장 완료"

# Apify API Configuration
echo -n "***APIFY_API_KEY_REDACTED***" | gcloud secrets create apify-api-key --data-file=- --project="${PROJECT_ID}" --replication-policy="automatic"
echo "apify-api-key 저장 완료"

# Telegram
echo -n "***TELEGRAM_BOT_TOKEN_REDACTED***" | gcloud secrets create telegram-bot-token --data-file=- --project="${PROJECT_ID}" --replication-policy="automatic"
echo "telegram-bot-token 저장 완료"

echo -n "***TELEGRAM_CHAT_ID_REDACTED***" | gcloud secrets create telegram-chat-id --data-file=- --project="${PROJECT_ID}" --replication-policy="automatic"
echo "telegram-chat-id 저장 완료"

echo "=== 모든 Secret 저장 완료! Secret 목록 확인 중... ==="
gcloud secrets list --project="${PROJECT_ID}"

echo "이제 Phase 3: VM 배포 단계로 넘어갈 준비가 되었습니다."