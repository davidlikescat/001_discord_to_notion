# YouTube Summarizer Bot (Serverless v3.0)

📱 **Telegram Bot**으로 YouTube URL을 전송하면, AI가 자동으로 요약하여 **Notion**에 저장하는 완전 무료 서버리스 봇입니다.

---

## 🎯 주요 특징

✅ **완전 무료** - 모든 서비스의 무료 티어만 사용 ($0/월)
✅ **서버리스** - VM 불필요, 사용한 만큼만 과금
✅ **모바일 최적화** - 폰에서 YouTube 공유 → Telegram Bot → Notion
✅ **AI 요약** - Gemini 2.0 Flash (무료) 또는 Claude Haiku (저렴한 백업)
✅ **자동 번역** - 영어 자막 → 한글 요약
✅ **2개 채널 지원** - Archive (텍스트 정제), Agent Reference (AI 인사이트)

---

## 🏗️ 아키텍처

```
📱 Phone (YouTube 공유)
  ↓
🤖 Telegram Bot
  ↓ Webhook
☁️ Cloudflare Workers (무료 100K req/일)
  ↓ 작업 등록
🗄️ Supabase (무료 500MB)
  ↓ Pub/Sub 역할
⏰ Cloud Scheduler (1분마다, 무료)
  ↓
☁️ Cloud Functions (무료 400K GB-s)
  ├─ YouTube API (무료 10K req/일)
  ├─ youtube-transcript-api (무료)
  ├─ Gemini 2.0 Flash (무료 1500 req/일)
  └─ Notion API (무료)
  ↓
📱 Telegram 알림
```

---

## 💰 비용 분석

| 서비스 | 무료 티어 | 월 100회 사용량 | 비용 |
|--------|----------|----------------|------|
| Telegram Bot | 무제한 | 200 calls | **$0** |
| Cloudflare Workers | 100K req/일 | 200 req | **$0** |
| Supabase | 500MB DB | ~10MB | **$0** |
| Cloud Functions | 400K GB-s | 100 GB-s | **$0** |
| Cloud Scheduler | 3 jobs | 1 job | **$0** |
| YouTube API | 10K req/일 | 100 req | **$0** |
| Gemini API | 1500 req/일 | 100 req | **$0** |
| Notion API | 무제한 | 100 req | **$0** |

### 총 비용: **$0/월** 🎉

---

## 📦 설치 및 배포

### 1. 환경 준비

```bash
# 저장소 이동
cd Python/001_discord_to_notion

# Python 가상환경 생성 (선택)
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

---

### 2. Telegram Bot 생성 (5분)

1. **BotFather와 대화**
   - Telegram에서 [@BotFather](https://t.me/botfather) 검색
   - `/newbot` 명령 실행
   - 봇 이름 입력: `YouTube Summarizer Bot`
   - Username 입력: `your_bot_name_bot`
   - **API Token 저장** (예: `123456:ABC-DEF...`)

2. **Chat ID 확인**
   - 방금 만든 봇에게 메시지 전송
   - 브라우저에서 접속:
     ```
     https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
     ```
   - `"chat":{"id":1234567890}` 부분의 숫자가 Chat ID

---

### 3. Supabase 설정 (10분)

1. **Supabase 프로젝트 생성**
   - [Supabase 대시보드](https://app.supabase.com/) 접속
   - "New Project" 클릭
   - 프로젝트 이름 입력, 비밀번호 설정
   - Region: `Northeast Asia (Seoul)` 선택

2. **API 키 확인**
   - Settings → API
   - `URL` 복사 → `SUPABASE_URL`
   - `service_role` key 복사 → `SUPABASE_SERVICE_KEY`
   - `anon public` key 복사 → `SUPABASE_ANON_KEY`

3. **데이터베이스 스키마 실행**
   - SQL Editor 메뉴 클릭
   - `supabase_schema.sql` 파일 내용 복사 & 붙여넣기
   - "Run" 버튼 클릭
   - ✅ "Success" 메시지 확인

---

### 4. Notion 설정 (5분)

1. **Notion Integration 생성**
   - [Notion Integrations](https://www.notion.so/my-integrations) 접속
   - "New integration" 클릭
   - 이름 입력: `YouTube Summarizer`
   - Type: `Internal`
   - Capabilities: `Read`, `Update`, `Insert` 모두 체크
   - "Submit" → **API Key 복사**

2. **Notion Database 생성**

   **Archive Database:**
   - Notion에서 새 페이지 생성
   - `/database` 입력 → "Table - Inline" 선택
   - 속성 추가:
     - `Name` (Title) - 기본
     - `URL` (URL)
     - `Channel` (Text)
     - `Duration` (Text)
     - `Category` (Select)
     - `Created` (Date)
   - 페이지 우측 상단 `...` → "Add connections" → Integration 선택
   - 페이지 URL에서 Database ID 복사:
     ```
     https://notion.so/YOUR-WORKSPACE/290b592202868160becbe90aeaf8dfeb
                                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
     ```

   **Agent Reference Database:**
   - 위와 동일하게 생성
   - Database ID 복사

---

### 5. 환경변수 설정

`.env` 파일을 수정:

```bash
# API Keys
YOUTUBE_API_KEY=AIzaSy...  # 기존 키 사용
GEMINI_API_KEY=AIzaSy...   # 기존 키 사용
ANTHROPIC_API_KEY=sk-ant-api03-...  # 기존 키 사용 (백업용)
NOTION_API_KEY=ntn_...  # 위에서 생성한 키

# Telegram Bot
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...  # 위에서 생성한 토큰
TELEGRAM_CHAT_ID=1234567890  # 위에서 확인한 Chat ID

# Notion Databases
NOTION_DATABASE_ID_ARCHIVE=290b592...  # Archive DB ID
NOTION_DATABASE_ID_AGENT_REF=28ab59...  # Agent Reference DB ID

# Supabase
SUPABASE_URL=https://xxx.supabase.co  # 위에서 복사한 URL
SUPABASE_SERVICE_KEY=eyJhbGci...  # service_role key
SUPABASE_ANON_KEY=eyJhbGci...  # anon public key

# GCP Project
GCP_PROJECT_ID=n8n-ai-work-agent-automation
```

---

### 6. GCP Secret Manager 설정 (10분)

```bash
# GCP 프로젝트 설정
export GCP_PROJECT_ID=n8n-ai-work-agent-automation
gcloud config set project $GCP_PROJECT_ID

# Secrets 생성
echo -n "YOUR_TELEGRAM_TOKEN" | gcloud secrets create telegram-bot-token --data-file=-
echo -n "YOUR_SUPABASE_KEY" | gcloud secrets create supabase-service-key --data-file=-
echo -n "YOUR_YOUTUBE_KEY" | gcloud secrets create youtube-api-key --data-file=-
echo -n "YOUR_GEMINI_KEY" | gcloud secrets create gemini-api-key --data-file=-
echo -n "YOUR_CLAUDE_KEY" | gcloud secrets create claude-api-key --data-file=-
echo -n "YOUR_NOTION_KEY" | gcloud secrets create notion-api-key --data-file=-
echo -n "YOUR_ARCHIVE_DB_ID" | gcloud secrets create notion-db-archive --data-file=-
echo -n "YOUR_AGENT_REF_DB_ID" | gcloud secrets create notion-db-agent-ref --data-file=-

# Secrets 확인
gcloud secrets list
```

---

### 7. Cloud Functions 배포 (10분)

```bash
# 배포 스크립트 실행
./deploy.sh

# 또는 수동 배포:
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
  --set-env-vars="SUPABASE_URL=https://xxx.supabase.co" \
  --set-secrets="TELEGRAM_BOT_TOKEN=telegram-bot-token:latest,SUPABASE_SERVICE_KEY=supabase-service-key:latest,YOUTUBE_API_KEY=youtube-api-key:latest,GEMINI_API_KEY=gemini-api-key:latest,ANTHROPIC_API_KEY=claude-api-key:latest,NOTION_API_KEY=notion-api-key:latest,NOTION_DATABASE_ID_ARCHIVE=notion-db-archive:latest,NOTION_DATABASE_ID_AGENT_REF=notion-db-agent-ref:latest"
```

배포 후 Function URL 복사:
```
https://asia-northeast3-n8n-ai-work-agent-automation.cloudfunctions.net/process-youtube-jobs
```

---

### 8. Cloud Scheduler 설정 (5분)

```bash
# Cloud Scheduler 생성 (1분마다 실행)
gcloud scheduler jobs create http youtube-job-processor \
  --location=asia-northeast3 \
  --schedule="* * * * *" \
  --uri="https://asia-northeast3-n8n-ai-work-agent-automation.cloudfunctions.net/process-youtube-jobs" \
  --http-method=GET

# 확인
gcloud scheduler jobs list --location=asia-northeast3
```

---

### 9. Cloudflare Workers 배포 (10분)

1. **Cloudflare 계정 생성**
   - [Cloudflare Dashboard](https://dash.cloudflare.com/) 접속
   - Workers & Pages 메뉴 클릭

2. **Wrangler 설치 및 로그인**
   ```bash
   cd cloudflare-worker
   npm install
   npx wrangler login
   ```

3. **환경변수 설정**
   - `wrangler.toml` 파일에서 `SUPABASE_URL` 수정
   - Secrets 설정:
     ```bash
     npx wrangler secret put TELEGRAM_BOT_TOKEN
     # 프롬프트에 토큰 입력

     npx wrangler secret put SUPABASE_SERVICE_KEY
     # 프롬프트에 Supabase service key 입력
     ```

4. **배포**
   ```bash
   npx wrangler deploy
   ```

   배포 후 Worker URL 복사:
   ```
   https://youtube-summarizer-bot.your-subdomain.workers.dev
   ```

---

### 10. Telegram Webhook 연결 (1분)

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_TELEGRAM_TOKEN>/setWebhook" \
  -d "url=https://youtube-summarizer-bot.your-subdomain.workers.dev"

# 확인
curl "https://api.telegram.org/bot<YOUR_TELEGRAM_TOKEN>/getWebhookInfo"
```

응답에서 `"url"` 항목이 올바르게 설정되었는지 확인.

---

## 🧪 테스트

### 1. Telegram Bot 테스트

1. 봇에게 YouTube URL 전송:
   ```
   https://www.youtube.com/watch?v=dQw4w9WgXcQ
   ```

2. 봇이 채널 선택 버튼 표시
   - 📚 Archive 또는 🤖 Agent Reference 선택

3. 봇 응답:
   ```
   ⏳ 요약을 시작합니다!
   📺 채널: Archive
   🔄 1-2분 내 완료 예상
   ```

4. 1-2분 후 완료 알림:
   ```
   ✅ 요약 완료!
   📺 제목: ...
   📄 Notion: [링크]
   ```

### 2. Supabase Database 확인

- Supabase Dashboard → Table Editor → `jobs` 테이블
- 작업 상태 확인: `pending` → `processing` → `completed`

### 3. Notion 확인

- Notion Database에 새 페이지 생성 확인
- YouTube 영상 임베드 확인
- AI 요약 내용 확인

---

## 🔧 문제 해결

### Telegram Bot이 응답하지 않음

1. **Webhook 확인**
   ```bash
   curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
   ```
   - `"url"` 항목이 올바른지 확인
   - `"last_error_message"` 확인

2. **Cloudflare Workers 로그 확인**
   ```bash
   cd cloudflare-worker
   npx wrangler tail
   ```

### 작업이 처리되지 않음

1. **Supabase 확인**
   - jobs 테이블에 `pending` 상태 작업이 있는지 확인

2. **Cloud Functions 로그 확인**
   ```bash
   gcloud functions logs read process-youtube-jobs \
     --region=asia-northeast3 \
     --limit=50
   ```

3. **Cloud Scheduler 실행 확인**
   ```bash
   gcloud scheduler jobs describe youtube-job-processor \
     --location=asia-northeast3
   ```

### AI 요약 오류

1. **Gemini API 키 확인**
   ```bash
   gcloud secrets versions access latest --secret=gemini-api-key
   ```

2. **Claude API 키 확인** (백업용)
   ```bash
   gcloud secrets versions access latest --secret=claude-api-key
   ```

### Notion 저장 실패

1. **Notion API 키 확인**
   ```bash
   gcloud secrets versions access latest --secret=notion-api-key
   ```

2. **Notion Database 권한 확인**
   - Database 페이지 → `...` → "Connections"
   - Integration이 연결되어 있는지 확인

---

## 📊 모니터링

### Supabase Dashboard

- **Table Editor**: jobs 테이블에서 작업 상태 실시간 확인
- **SQL Editor**: 통계 쿼리 실행
  ```sql
  -- 오늘 처리된 작업 수
  SELECT channel, COUNT(*) as count
  FROM jobs
  WHERE DATE(created_at) = CURRENT_DATE
  GROUP BY channel;

  -- 평균 처리 시간
  SELECT
    channel,
    AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) as avg_seconds
  FROM jobs
  WHERE status = 'completed'
  GROUP BY channel;
  ```

### GCP Cloud Logging

```bash
# Cloud Functions 로그
gcloud functions logs read process-youtube-jobs \
  --region=asia-northeast3 \
  --limit=100

# Cloud Scheduler 로그
gcloud logging read "resource.type=cloud_scheduler_job" \
  --limit=50 \
  --format=json
```

---

## 🎨 커스터마이징

### AI 프롬프트 수정

`core/ai_summarizer.py` 파일의 `system_prompts` 딕셔너리를 수정:

```python
system_prompts = {
    'archive': """당신의 커스텀 프롬프트""",
    'agent-reference': """당신의 커스텀 프롬프트"""
}
```

### 채널 추가

1. Notion에 새 Database 생성
2. `.env`에 Database ID 추가
3. `main.py`의 `database_ids` 딕셔너리에 채널 추가
4. `cloudflare-worker/index.js`의 Inline Keyboard에 버튼 추가

---

## 📈 확장 가능성

### Discord 봇 추가

기존 Discord 코드(`old/` 폴더)를 참고하여:
- Discord Slash Command 구현
- Cloudflare Worker와 동일한 Supabase에 작업 등록

### Web 프론트엔드 추가

- Vercel에 Next.js 앱 배포
- URL 제출 폼 제공
- 작업 상태 실시간 확인 (Supabase Realtime 구독)

### Slack 봇 추가

- Slack App 생성
- Slash Command 구현
- Cloudflare Worker 또는 별도 Worker 생성

---

## 📝 라이선스

MIT License

---

## 🙋‍♂️ 지원

문제가 발생하면:
1. [GitHub Issues](링크) 등록
2. 또는 [이메일](mailto:your-email@example.com) 문의

---

**마지막 업데이트**: 2025년 11월 3일
**버전**: 3.0.0 (Serverless)
**기존 버전**: `old/` 폴더 참고
