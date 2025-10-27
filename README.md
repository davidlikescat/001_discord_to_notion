# Discord YouTube to Notion Bot (v2.0)

Discord에서 공유된 YouTube 영상을 자동으로 분석하고, AI로 요약하여 Notion에 저장하는 봇입니다.

## 🎯 주요 기능

### 2개 채널 지원
1. **01-archive**: 텍스트 정제 및 아카이브
   - 영상 내용을 1000줄 이내로 정리
   - 한글 번역 및 정제 (영어 → 한글)
   - 일목요연한 구조화

2. **02-agent-reference**: AI 에이전트 참고자료
   - AI 에이전트 개발/활용 중심 정리
   - 실무 적용 가능한 인사이트 추출
   - Feed view 형식

### 핵심 특징
- ✅ **youtube-transcript-api 우선 사용**: 빠르고 정확한 자막 추출
- ✅ **Claude 3.7 Sonnet**: 고품질 AI 요약
- ✅ **채널별 시스템 프롬프트**: 맞춤형 요약 스타일
- ✅ **YouTube URL 임베딩**: Notion 페이지에 영상 직접 임베딩
- ✅ **GCP Secret Manager 연동**: 안전한 API 키 관리

## 📁 프로젝트 구조

```
001_discord_to_notion/
├── config/
│   ├── channel_config.json    # 채널별 설정
│   └── prompts.py              # 시스템 프롬프트 정의
├── core/
│   ├── youtube_detector.py     # YouTube 링크 감지
│   ├── youtube_info.py         # 영상 정보 추출
│   ├── subtitle_extractor.py   # 자막 추출 (youtube-transcript-api + yt-dlp)
│   ├── ai_summarizer.py        # Claude AI 요약
│   └── notion_saver.py         # Notion 저장
├── old/                        # 기존 코드 백업
├── main.py                     # 메인 컨트롤러
├── requirements.txt
└── README.md
```

## 🚀 설치 및 실행

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env` 파일 생성:

```bash
# Discord
DISCORD_BOT_TOKEN=your_discord_bot_token

# YouTube Data API
YOUTUBE_API_KEY=your_youtube_api_key

# Claude API (Anthropic)
ANTHROPIC_API_KEY=your_anthropic_api_key

# Notion API
NOTION_API_KEY=your_notion_api_key
```

### 3. 채널 설정

`config/channel_config.json`에서 채널 ID 확인:

```json
{
  "channels": {
    "01-archive": {
      "channel_id": 960907092439478374,
      "notion_database_id": "290b592202868160becbe90aeaf8dfeb"
    },
    "02-agent-reference": {
      "channel_id": 1432206876635824148,
      "notion_database_id": "28ab59220286804c8b6fe9950825fb86"
    }
  }
}
```

### 4. 봇 실행

#### 로컬 실행
```bash
python main.py
```

#### GCP 실행 (백그라운드)
```bash
# SSH 접속
gcloud compute ssh discord-youtube-bot --zone=asia-northeast3-a

# 봇 실행
cd ~/001_discord_to_notion
nohup python3 main.py > bot.log 2>&1 &

# 로그 확인
tail -f bot.log
```

## 🔄 워크플로우

```
1. Discord 메시지 수신
   ↓
2. 채널 ID 확인 및 설정 로드
   ↓
3. YouTube 링크 감지
   ↓
4. 영상 정보 추출 (YouTube Data API)
   ↓
5. 자막 추출 (youtube-transcript-api → yt-dlp)
   ↓
6. AI 요약 (Claude + 채널별 시스템 프롬프트)
   ↓
7. Notion 저장 (채널별 DB + YouTube URL 임베딩)
   ↓
8. Discord에 완료 메시지 전송
```

## 📋 채널별 시스템 프롬프트

### Archive 프롬프트
```
당신은 텍스트 정제 및 아카이브 전문가입니다.

주요 작업:
1. 영상 자막/설명을 한글로 정제 (영어는 번역 후 정제)
2. 1000줄 이내로 정제 및 정리
3. 일목요연하게 구조화하여 가독성 향상
```

### Agent References 프롬프트
```
당신은 AI 에이전트 참고자료 번역 및 정리 전문가입니다.

주요 작업:
1. 영상 내용을 한글로 번역 및 정제
2. AI 에이전트 개발/활용에 유용한 인사이트 추출
3. 실무에 바로 적용 가능한 정보 우선 정리
```

## 🔧 주요 설정 변경

### AI 모델 변경

`config/channel_config.json`:

```json
{
  "ai_model": "claude-3-haiku-20240307"  // 빠르고 저렴 (무료 티어)
}
```

사용 가능한 모델:
- `claude-3-7-sonnet-20250219` (최신, 고품질, 추천)
- `claude-3-5-sonnet-20241022` (안정적)
- `claude-3-haiku-20240307` (빠르고 저렴)

### 자막 추출 우선순위 변경

```json
{
  "subtitle_priority": ["youtube_transcript_api", "yt_dlp"]
}
```

## 📊 Notion 데이터베이스 속성

### Archive Database
- **Name** (Title): 영상 제목
- **URL** (URL): YouTube URL
- **Channel** (Text): 채널명
- **Created** (Date): 생성일

### Agent References Database
- **Name** (Title): 영상 제목
- **URL** (URL): YouTube URL
- **Source** (Text): 출처 (채널명)
- **Created** (Date): 생성일
- **Rating** (Select): 사용자 평가 (비워둠)

## 🧪 테스트

### 개별 모듈 테스트

```bash
# 자막 추출 테스트
python core/subtitle_extractor.py

# AI 요약 테스트
python core/ai_summarizer.py

# Notion 저장 테스트
python core/notion_saver.py

# 프롬프트 확인
python config/prompts.py
```

## 🔐 GCP Secret Manager 설정

```bash
# Secret 업로드
echo "your_token" | gcloud secrets create discord-bot-token --data-file=-
echo "your_api_key" | gcloud secrets create claude-api-key --data-file=-
echo "your_api_key" | gcloud secrets create notion-api-key --data-file=-
echo "your_api_key" | gcloud secrets create youtube-api-key --data-file=-

# Secret 확인
gcloud secrets list
```

## 📈 변경 사항 (v1.0 → v2.0)

### ✨ 새로운 기능
- ✅ 2개 채널 지원 (Archive, Agent References)
- ✅ youtube-transcript-api 통합 (빠른 자막 추출)
- ✅ Claude API 연동 (Gemini 대체)
- ✅ 채널별 시스템 프롬프트
- ✅ YouTube URL 임베딩
- ✅ 1000줄 이내 정리 기능

### 🔧 개선 사항
- 모듈화된 구조 (config/, core/)
- 채널별 설정 시스템
- 향상된 에러 처리
- 상세한 로깅

## 🐛 트러블슈팅

### 문제: 자막 추출 실패
**해결**: 영상 설명으로 자동 대체됨

### 문제: Claude API 오류
**해결**:
1. API 키 확인
2. 모델명 확인 (config/channel_config.json)
3. Haiku 모델로 폴백 시도

### 문제: Notion 저장 실패
**해결**:
1. API 키 확인
2. Database ID 확인
3. Integration 권한 확인

## 📝 License

MIT License

## 🙋‍♂️ 문의

문제가 발생하면 GitHub Issues에 등록해주세요.

---

**마지막 업데이트**: 2025년 10월 27일
**버전**: 2.0.0
**작성자**: Discord YouTube Notion Bot Team
