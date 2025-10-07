# Discord YouTube to Notion Bot

Discord에서 YouTube 링크를 감지하여 자동으로 요약하고 Notion에 저장하는 봇입니다.

## 🚀 주요 기능

- 🎬 YouTube 링크 자동 감지 (일반 영상 + 숏츠 지원)
- 📝 자막 추출 (한국어/영어 우선순위)
- 🤖 AI 요약 생성 (Gemini API)
- 💾 Notion 데이터베이스 자동 저장
- 🔗 임베드 메시지 및 포워드 메시지 지원

## 🏗️ 아키텍처

```
Discord 메시지 → 링크 감지 → 영상 정보 수집 → 자막 추출 → AI 요약 → Notion 저장
```

## 📦 모듈 구조

- `discord_main_controller.py` - 메인 봇 컨트롤러
- `discord_sub_1.py` - YouTube 링크 감지기
- `discord_sub_2.py` - 영상 정보 추출기 (YouTube API)
- `discord_sub_3.py` - 자막 추출기 (yt-dlp)
- `discord_sub_4.py` - AI 요약기 (Gemini)
- `discord_sub_5.py` - Notion 저장기

## 🔧 설정 방법

### 1. 환경 변수 설정

로컬 개발용 `.env` 파일:
```env
DISCORD_BOT_TOKEN=your_discord_bot_token
YOUTUBE_API_KEY=your_youtube_api_key
GEMINI_API_KEY=your_gemini_api_key
NOTION_API_KEY=your_notion_api_key
NOTION_DATABASE_ID=your_notion_database_id
# 선택: 최신 모델을 강제로 지정하려면 (예: models/gemini-1.5-flash-latest)
# GEMINI_MODEL_NAME=models/gemini-1.5-flash-latest
```

### 2. GCP Secret Manager (프로덕션)

봇은 자동으로 다음 우선순위로 설정을 읽습니다:
1. 로컬 환경변수 (`.env` 파일)
2. GCP Secret Manager

GCP Secret Manager 시크릿 이름:
- `discord-bot-token`
- `youtube-api-key`
- `gemini-api-key`
- `notion-api-key`
- `notion-database-id`

### 3. Discord 봇 설정

Discord Developer Portal에서:
1. Bot 생성 및 토큰 복사
2. Privileged Gateway Intents 활성화:
   - ✅ Message Content Intent
3. 봇 권한 설정:
   - ✅ Read Messages
   - ✅ Send Messages
   - ✅ Embed Links
   - ✅ Attach Files

### 4. Notion 데이터베이스 설정

1. Notion Integration 생성
2. 데이터베이스 속성 설정:
   - Title (제목)
   - Channel (텍스트)
   - URL (URL)
   - Status (셀렉트)
   - Duration (텍스트)

## 🚀 설치 및 실행

### 로컬 실행
```bash
# 의존성 설치
pip install -r requirements.txt

# 기존 환경에 설치된 google-generativeai가 오래되었다면 강제로 업그레이드
pip install --upgrade google-generativeai

# 봇 실행
python discord_main_controller.py
```

### GCP VM 배포
```bash
# 저장소 클론
git clone <repository-url>
cd discord-youtube-bot

# 배포 스크립트 실행
chmod +x deploy.sh
./deploy.sh
```

### systemd 서비스 등록
```bash
# 서비스 파일 생성
sudo nano /etc/systemd/system/discord-youtube-bot.service

# 서비스 활성화
sudo systemctl enable discord-youtube-bot.service
sudo systemctl start discord-youtube-bot.service
```

## 🔍 로그 및 모니터링

```bash
# 실시간 로그 확인
sudo journalctl -u discord-youtube-bot.service -f

# 서비스 상태 확인
sudo systemctl status discord-youtube-bot.service

# 서비스 재시작
sudo systemctl restart discord-youtube-bot.service
```

## 🛠️ 문제 해결

### 토큰 오류 해결
```bash
# 토큰 검증
python -c "
import requests
token = 'YOUR_TOKEN'
r = requests.get('https://discord.com/api/v10/users/@me', 
                headers={'Authorization': f'Bot {token}'})
print(f'Status: {r.status_code}')
print(f'Response: {r.json() if r.status_code == 200 else r.text}')
"
```

### 환경변수 확인
```bash
# 현재 설정 확인
cat .env | grep DISCORD_BOT_TOKEN

# GCP Secret Manager 확인
gcloud secrets versions access latest --secret="discord-bot-token"
```

## 🔄 업데이트 및 배포

### GitHub 푸시
```bash
git add .
git commit -m "🔧 Update bot features"
git push origin main
```

### 자동 배포
```bash
# VM에서 실행
./deploy.sh
```

## 📊 지원하는 YouTube URL 형식

- `https://www.youtube.com/watch?v=VIDEO_ID`
- `https://youtu.be/VIDEO_ID`
- `https://youtube.com/shorts/VIDEO_ID` (숏츠)
- `https://m.youtube.com/watch?v=VIDEO_ID` (모바일)
- Embed/Forward 메시지 내 URL

## 🤝 기여하기

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 🔗 관련 링크

- [Discord Developer Portal](https://discord.com/developers/applications)
- [YouTube Data API](https://developers.google.com/youtube/v3)
- [Google AI Studio](https://makersuite.google.com/)
- [Notion API](https://developers.notion.com/)
- [GCP Secret Manager](https://cloud.google.com/secret-manager)

---

## 📈 최근 업데이트

### v2.0.0 (2025-05-28)
- 🔧 GCP Secret Manager 통합으로 토큰 관리 개선
- 🐛 "Improper token has been passed" 오류 해결
- 🚀 자동 배포 스크립트 추가
- 📝 환경변수와 클라우드 시크릿 자동 fallback 지원
