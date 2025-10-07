# Discord YouTube to Notion 봇 - 전체 워크플로우 문서

## 📋 프로젝트 개요

이 프로젝트는 Discord에서 공유된 YouTube 영상 링크를 자동으로 감지하고, 영상 정보를 수집하여 AI로 요약한 후 Notion 데이터베이스에 저장하는 자동화 봇입니다.

## 🏗️ 아키텍처 구조

```
discord_main_controller.py (메인 컨트롤러)
├── discord_sub_1.py (YouTube 링크 감지)
├── discord_sub_2.py (영상 정보 추출)
├── discord_sub_3.py (자막 추출)
├── discord_sub_4.py (AI 요약 생성)
└── discord_sub_5.py (Notion 저장)
```

## 🔧 모듈별 상세 기능

### 1. discord_main_controller.py - 메인 컨트롤러
**역할**: 전체 워크플로우 조율 및 Discord 봇 관리

**주요 기능**:
- Discord 봇 초기화 및 이벤트 처리
- GCP Secret Manager 연동 (API 키 관리)
- 워크플로우 단계별 실행 관리
- 중복 처리 방지 (동일 영상 동시 처리 방지)
- 에러 처리 및 로깅

**핵심 클래스**: `DiscordWorkflowManager`

### 2. discord_sub_1.py - YouTube 링크 감지
**역할**: Discord 메시지에서 YouTube 링크 감지 및 비디오 ID 추출

**주요 기능**:
- 다양한 YouTube URL 패턴 지원:
  - 일반 YouTube: `youtube.com/watch?v=...`
  - 단축 URL: `youtu.be/...`
  - YouTube Shorts: `youtube.com/shorts/...`
  - 모바일 URL: `m.youtube.com/...`
- Embed 메시지, 첨부파일, 참조 메시지에서도 링크 감지
- 중복 제거 및 유효성 검증

**핵심 클래스**: `YouTubeDetector`

### 3. discord_sub_2.py - 영상 정보 추출
**역할**: YouTube Data API를 사용한 영상 메타데이터 수집

**주요 기능**:
- 영상 제목, 설명, 채널 정보
- 조회수, 좋아요 수, 댓글 수
- 영상 길이 (ISO 8601 형식 파싱)
- 썸네일 URL (최고 품질)
- 태그, 카테고리, 언어 정보

**핵심 클래스**: `YouTubeInfoExtractor`

### 4. discord_sub_3.py - 자막 추출
**역할**: yt-dlp를 사용한 YouTube 자막 추출

**주요 기능**:
- 다국어 자막 지원 (한국어 우선, 영어 대안)
- 수동 자막과 자동 자막 모두 지원
- 자막 형식: VTT, SRT
- 중복 제거 및 텍스트 정리
- 자막이 없는 경우 영상 설명으로 대체

**지원하는 자막 소스**:
- `yt_dlp_manual_ko`: 수동 한국어 자막
- `yt_dlp_manual_en`: 수동 영어 자막
- `yt_dlp_auto_ko`: 자동 한국어 자막
- `yt_dlp_auto_en`: 자동 영어 자막
- `description`: 영상 설명란

**핵심 클래스**: `SubtitleExtractor`

### 5. discord_sub_4.py - AI 요약 생성
**역할**: Google Gemini AI를 사용한 영상 내용 요약

**주요 기능**:
- Gemini 1.5 Flash/Pro 모델 사용
- 자막 소스별 맞춤 프롬프트 생성
- 토큰 제한 고려한 텍스트 길이 조정
- 구조화된 요약 형식 (주요 내용, 핵심 포인트, 결론)

**핵심 클래스**: `GeminiSummarizer`

### 6. discord_sub_5.py - Notion 저장
**역할**: Notion API를 사용한 데이터베이스 저장

**주요 기능**:
- Notion 데이터베이스에 페이지 생성
- 영상 정보와 AI 요약을 구조화하여 저장
- 마크다운 형식 지원
- Discord 메타데이터 포함 (채널, 작성자)

**필수 데이터베이스 속성**:
- 제목 (Title)
- 채널 (Text)
- URL (URL)
- 조회수 (Number)
- 좋아요 (Number)
- 길이 (Text)
- 자막소스 (Text)
- 디스코드채널 (Text)
- 상태 (Select)

**핵심 클래스**: `NotionSaver`

## 🔄 전체 워크플로우 과정

### Step 1: 영상 감지 🎬
1. Discord 메시지 수신
2. 메시지에서 모든 텍스트 추출 (content + embeds + attachments)
3. YouTube URL 패턴 매칭
4. 비디오 ID 추출 및 중복 제거

### Step 2: 영상 정보 수집 📊
1. YouTube Data API 호출
2. 영상 메타데이터 수집
3. 통계 정보 (조회수, 좋아요 등) 수집
4. 썸네일 및 기타 정보 수집

### Step 3: 자막 추출 📝
1. yt-dlp로 자막 정보 확인
2. 우선순위: 한국어 수동 → 영어 수동 → 한국어 자동 → 영어 자동
3. 자막 다운로드 및 텍스트 변환
4. 자막이 없는 경우 영상 설명 사용

### Step 4: AI 요약 생성 🤖
1. Gemini AI 모델 초기화
2. 자막 소스별 맞춤 프롬프트 생성
3. AI 요약 생성
4. 구조화된 요약 결과 반환

### Step 5: Notion 저장 💾
1. Notion API 인증
2. 데이터베이스 페이지 생성
3. 영상 정보와 요약 저장
4. 노션 페이지 URL 반환

## 🔐 환경 설정

### 필수 API 키
```bash
DISCORD_BOT_TOKEN=your_discord_bot_token
YOUTUBE_API_KEY=your_youtube_api_key
GEMINI_API_KEY=your_gemini_api_key
NOTION_API_KEY=your_notion_integration_token
NOTION_DATABASE_ID=your_notion_database_id
```

### GCP Secret Manager 연동
- 프로젝트 ID: `n8n-ai-work-agent-automation`
- 시크릿 매핑:
  - `discord-bot-token` → `DISCORD_BOT_TOKEN`
  - `youtube-api-key` → `YOUTUBE_API_KEY`
  - `gemini-api-key` → `GEMINI_API_KEY`
  - `notion-api-key` → `NOTION_API_KEY`
  - `notion-database-id` → `NOTION_DATABASE_ID`

## 🚀 실행 방법

### 로컬 실행
```bash
python3 discord_main_controller.py
```

### GCP 실행
```bash
# SSH 접속
gcloud compute ssh discord-youtube-bot --zone=asia-northeast3-a --project=n8n-ai-work-agent-automation

# 봇 실행
cd ~/001_discord_to_notion
python3 discord_main_controller.py

# 백그라운드 실행
nohup python3 discord_main_controller.py > bot.log 2>&1 &
```

## 📊 지원하는 YouTube URL 형식

- 일반 YouTube: `https://www.youtube.com/watch?v=VIDEO_ID`
- 단축 URL: `https://youtu.be/VIDEO_ID`
- YouTube Shorts: `https://www.youtube.com/shorts/VIDEO_ID`
- 모바일 URL: `https://m.youtube.com/watch?v=VIDEO_ID`
- Embed URL: `https://www.youtube.com/embed/VIDEO_ID`

## 🔧 문제 해결

### 일반적인 문제들
1. **토큰 오류**: Discord 봇 토큰 재발급 필요
2. **API 키 누락**: GCP Secret Manager 또는 .env 파일 확인
3. **자막 추출 실패**: 영상 설명으로 자동 대체
4. **AI 요약 실패**: 토큰 제한 또는 API 오류
5. **Notion 저장 실패**: 데이터베이스 권한 또는 속성 확인

### 디버깅 도구
- `discord_bot_debug.py`: 봇 연결 테스트
- `discord_token_diagnosis.py`: 토큰 진단
- 각 모듈의 `test_*()` 함수들

## 📈 성능 최적화

### 중복 처리 방지
- `processing_videos` 세트로 동시 처리 방지
- 동일한 video_id 중복 제거

### 에러 처리
- 각 단계별 예외 처리
- 실패 시 적절한 대체 방법 사용
- 상세한 로깅 및 에러 메시지

### 리소스 관리
- 비동기 처리로 성능 향상
- 메모리 효율적인 텍스트 처리
- API 호출 제한 고려

## 🔮 향후 개선 사항

1. **다국어 지원 확장**: 더 많은 언어 자막 지원
2. **음성 인식 추가**: Whisper API 연동
3. **실시간 처리**: 웹훅 기반 실시간 처리
4. **대시보드**: 처리 현황 모니터링
5. **배치 처리**: 여러 영상 동시 처리
6. **캐싱**: 중복 요청 방지

## 📝 라이선스 및 기여

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 기여는 언제나 환영합니다!

---

**마지막 업데이트**: 2024년 12월
**버전**: 1.0.0 