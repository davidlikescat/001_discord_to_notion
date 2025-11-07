# 빠른 시작 가이드 (15분)

이 가이드를 따라하면 15분 내에 YouTube Summarizer Bot을 완전히 배포할 수 있습니다.

---

## ✅ 체크리스트

시작하기 전에 다음 항목을 확인하세요:

- [ ] Google 계정 (YouTube API, Gemini API)
- [ ] Telegram 계정
- [ ] Notion 계정
- [ ] Cloudflare 계정 (무료)
- [ ] Supabase 계정 (무료)
- [ ] GCP 프로젝트 (`n8n-ai-work-agent-automation`)

---

## 🚀 Step 1: Telegram Bot 생성 (2분)

```bash
# 1. Telegram에서 @BotFather 검색
# 2. /newbot 명령 실행
# 3. 봇 이름: YouTube Summarizer Bot
# 4. Username: your_unique_name_bot

# 토큰 예시: 7890998482:AAFldx70NQ5V4fm3ZImXLFyH9YQr9jaIOUk
```

**Chat ID 확인:**
```bash
# 봇에게 메시지 전송 후
curl https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates | jq '.result[0].message.chat.id'
```

---

## 🗄️ Step 2: Supabase 설정 (3분)

1. https://app.supabase.com/ 접속
2. New Project → 이름 입력, Seoul 선택
3. Settings → API에서 키 복사:
   - `URL`
   - `service_role key`

4. SQL Editor에서 실행:

```sql
-- supabase_schema.sql 내용 복사 & 붙여넣기
CREATE TABLE IF NOT EXISTS jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  youtube_url TEXT NOT NULL,
  telegram_chat_id BIGINT NOT NULL,
  telegram_user_id BIGINT,
  channel TEXT DEFAULT 'archive',
  status TEXT DEFAULT 'pending',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  started_at TIMESTAMP WITH TIME ZONE,
  completed_at TIMESTAMP WITH TIME ZONE,
  error_message TEXT,
  result JSONB
);

CREATE INDEX idx_jobs_status ON jobs(status) WHERE status = 'pending';
```

---

## 📄 Step 3: Notion Database 생성 (2분)

1. https://www.notion.so/my-integrations 접속
2. New integration → 이름: `YouTube Summarizer`
3. API Key 복사

4. Notion에서 새 Database 생성:
   - 속성: Name (Title), URL (URL), Channel (Text), Duration (Text), Category (Select), Created (Date)
   - `...` → Add connections → Integration 선택
   - URL에서 Database ID 복사 (32자리 문자열)

---

## ☁️ Step 4: GCP Secrets 생성 (3분)

```bash
cd "Python/001_discord_to_notion"

# .env 파일 수정 (위에서 받은 키 입력)
nano .env

# Secrets 생성
export GCP_PROJECT_ID=n8n-ai-work-agent-automation
gcloud config set project $GCP_PROJECT_ID

# 한 번에 실행
cat .env | grep TELEGRAM_BOT_TOKEN | cut -d'=' -f2 | gcloud secrets create telegram-bot-token --data-file=-
cat .env | grep SUPABASE_SERVICE_KEY | cut -d'=' -f2 | gcloud secrets create supabase-service-key --data-file=-
cat .env | grep YOUTUBE_API_KEY | cut -d'=' -f2 | gcloud secrets create youtube-api-key --data-file=-
cat .env | grep GEMINI_API_KEY | cut -d'=' -f2 | gcloud secrets create gemini-api-key --data-file=-
cat .env | grep ANTHROPIC_API_KEY | cut -d'=' -f2 | gcloud secrets create claude-api-key --data-file=-
cat .env | grep NOTION_API_KEY | cut -d'=' -f2 | gcloud secrets create notion-api-key --data-file=-
cat .env | grep NOTION_DATABASE_ID_ARCHIVE | cut -d'=' -f2 | gcloud secrets create notion-db-archive --data-file=-
cat .env | grep NOTION_DATABASE_ID_AGENT_REF | cut -d'=' -f2 | gcloud secrets create notion-db-agent-ref --data-file=-
```

---

## 🚢 Step 5: Cloud Functions 배포 (3분)

```bash
# 배포 스크립트 실행
./deploy.sh

# 완료 후 Function URL 복사
# 예: https://asia-northeast3-n8n-ai-work-agent-automation.cloudfunctions.net/process-youtube-jobs
```

---

## ☁️ Step 6: Cloudflare Workers 배포 (2분)

```bash
cd cloudflare-worker

# Wrangler 설치
npm install

# 로그인
npx wrangler login

# wrangler.toml에서 SUPABASE_URL 수정
nano wrangler.toml

# Secrets 설정
echo "7890998482:AAF..." | npx wrangler secret put TELEGRAM_BOT_TOKEN
cat ../.env | grep SUPABASE_SERVICE_KEY | cut -d'=' -f2 | npx wrangler secret put SUPABASE_SERVICE_KEY

# 배포
npx wrangler deploy

# Worker URL 복사
# 예: https://youtube-summarizer-bot.your-subdomain.workers.dev
```

---

## 🔗 Step 7: Telegram Webhook 연결 (1분)

```bash
# Webhook 설정
curl -X POST "https://api.telegram.org/bot<YOUR_TOKEN>/setWebhook" \
  -d "url=https://youtube-summarizer-bot.your-subdomain.workers.dev"

# 확인
curl "https://api.telegram.org/bot<YOUR_TOKEN>/getWebhookInfo" | jq
```

---

## 🧪 테스트

1. Telegram Bot에게 YouTube URL 전송:
   ```
   https://www.youtube.com/watch?v=dQw4w9WgXcQ
   ```

2. 채널 선택 버튼 클릭

3. 1-2분 후 완료 알림 확인

4. Notion Database에서 결과 확인

---

## 🔍 문제 해결

### 봇이 응답하지 않음

```bash
# Webhook 상태 확인
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"

# Cloudflare Workers 로그
cd cloudflare-worker && npx wrangler tail
```

### 작업이 처리되지 않음

```bash
# Cloud Functions 로그
gcloud functions logs read process-youtube-jobs --region=asia-northeast3 --limit=50

# Supabase에서 jobs 테이블 확인
# → status가 'pending'인 작업이 있는지 확인
```

---

## ✅ 완료!

이제 폰에서 YouTube를 보다가 공유 → Telegram → 1-2분 후 Notion에 요약본이 자동으로 저장됩니다!

**비용: $0/월** 🎉

---

## 📚 다음 단계

- [README.md](README.md) - 상세 문서
- [core/ai_summarizer.py](core/ai_summarizer.py) - AI 프롬프트 커스터마이징
- Supabase Dashboard - 작업 통계 확인

---

## 💡 팁

### 자주 사용하는 명령어

```bash
# 로그 확인 (실시간)
gcloud functions logs read process-youtube-jobs --region=asia-northeast3 --follow

# Cloudflare Workers 로그 (실시간)
cd cloudflare-worker && npx wrangler tail

# Supabase 작업 통계
# Supabase Dashboard → SQL Editor:
SELECT channel, status, COUNT(*) FROM jobs GROUP BY channel, status;
```

### 비용 모니터링

- **GCP Console** → Billing → Cost Table
- **Cloudflare Dashboard** → Workers & Pages → Analytics
- **Supabase Dashboard** → Settings → Usage

모든 서비스는 무료 티어 내에서 작동하므로 비용이 $0여야 합니다.

---

**문제가 있나요?** README.md의 "문제 해결" 섹션을 참고하세요.
