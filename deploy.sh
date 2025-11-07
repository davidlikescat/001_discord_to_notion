#!/bin/bash

# YouTube Summarizer Bot - 배포 스크립트
# GCP Cloud Functions 배포

set -e  # 오류 발생 시 중단

echo "🚀 YouTube Summarizer Bot 배포 시작..."
echo ""

# 환경변수 확인
if [ ! -f .env ]; then
    echo "❌ .env 파일이 없습니다. 먼저 .env 파일을 생성하세요."
    exit 1
fi

# .env 로드
export $(cat .env | grep -v '^#' | xargs)

# GCP 프로젝트 확인
if [ -z "$GCP_PROJECT_ID" ]; then
    echo "❌ GCP_PROJECT_ID가 설정되지 않았습니다."
    exit 1
fi

echo "📦 GCP Project: $GCP_PROJECT_ID"
echo ""

# Cloud Functions 배포
echo "☁️  Cloud Functions 배포 중..."
gcloud functions deploy process-youtube-jobs \
  --gen2 \
  --runtime=python311 \
  --region=asia-northeast3 \
  --source=. \
  --entry-point=process_pending_jobs \
  --trigger-http \
  --allow-unauthenticated \
  --memory=512MB \
  --timeout=540s \
  --project=$GCP_PROJECT_ID \
  --set-env-vars="SUPABASE_URL=$SUPABASE_URL" \
  --set-secrets="TELEGRAM_BOT_TOKEN=telegram-bot-token:latest,SUPABASE_SERVICE_KEY=supabase-service-key:latest,YOUTUBE_API_KEY=youtube-api-key:latest,GEMINI_API_KEY=gemini-api-key:latest,ANTHROPIC_API_KEY=claude-api-key:latest,NOTION_API_KEY=notion-api-key:latest,NOTION_DATABASE_ID_ARCHIVE=notion-db-archive:latest,NOTION_DATABASE_ID_AGENT_REF=notion-db-agent-ref:latest"

echo ""
echo "✅ Cloud Functions 배포 완료!"
echo ""

# Cloud Scheduler 생성 (이미 존재하면 업데이트)
echo "⏰ Cloud Scheduler 설정 중..."

FUNCTION_URL=$(gcloud functions describe process-youtube-jobs \
  --region=asia-northeast3 \
  --project=$GCP_PROJECT_ID \
  --format='value(serviceConfig.uri)')

echo "Function URL: $FUNCTION_URL"

# Scheduler 존재 여부 확인
if gcloud scheduler jobs describe youtube-job-processor --location=asia-northeast3 --project=$GCP_PROJECT_ID &>/dev/null; then
    echo "⚠️  기존 Scheduler 업데이트..."
    gcloud scheduler jobs update http youtube-job-processor \
      --location=asia-northeast3 \
      --schedule="* * * * *" \
      --uri="$FUNCTION_URL" \
      --http-method=GET \
      --project=$GCP_PROJECT_ID
else
    echo "✨ 새 Scheduler 생성..."
    gcloud scheduler jobs create http youtube-job-processor \
      --location=asia-northeast3 \
      --schedule="* * * * *" \
      --uri="$FUNCTION_URL" \
      --http-method=GET \
      --project=$GCP_PROJECT_ID
fi

echo ""
echo "✅ Cloud Scheduler 설정 완료!"
echo ""

echo "🎉 배포 완료!"
echo ""
echo "📋 다음 단계:"
echo "1. Telegram Bot Webhook 설정"
echo "   curl -X POST 'https://api.telegram.org/bot<TOKEN>/setWebhook' -d 'url=<CLOUDFLARE_WORKER_URL>'"
echo ""
echo "2. Cloudflare Workers 배포"
echo "   cd cloudflare-worker && npx wrangler deploy"
echo ""
echo "3. Supabase 스키마 실행"
echo "   Supabase 대시보드 > SQL Editor에서 supabase_schema.sql 실행"
echo ""
