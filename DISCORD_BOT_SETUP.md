# Discord 봇 설정 가이드

## 📋 봇 정보 (템플릿)
- **Application ID**: YOUR_APPLICATION_ID
- **Public Key**: YOUR_PUBLIC_KEY
- **Bot Token**: YOUR_BOT_TOKEN (Discord Developer Portal에서 확인)

## 🔧 1단계: Bot 설정 (Discord Developer Portal)

### 1.1 기본 설정
1. https://discord.com/developers/applications/1432281456859680880 접속
2. 왼쪽 메뉴에서 **"Bot"** 탭 선택

### 1.2 필수 권한 설정 (Privileged Gateway Intents)

다음 3가지를 **모두 활성화**해야 합니다:

- ✅ **PRESENCE INTENT** (선택사항, 꺼도 됨)
- ✅ **SERVER MEMBERS INTENT** (선택사항, 꺼도 됨)
- ✅ **MESSAGE CONTENT INTENT** ⚠️ **반드시 켜야 함!**

> **중요**: MESSAGE CONTENT INTENT를 켜지 않으면 봇이 메시지 내용을 읽을 수 없습니다!

### 1.3 Bot 권한 설정

"Bot Permissions" 섹션에서 다음 권한들을 체크:

#### 필수 권한:
- ✅ **View Channels** (채널 보기)
- ✅ **Send Messages** (메시지 보내기)
- ✅ **Read Message History** (메시지 기록 읽기)
- ✅ **Embed Links** (링크 임베드)
- ✅ **Attach Files** (파일 첨부)
- ✅ **Add Reactions** (반응 추가)

#### 권한 값 (숫자):
전체 권한 값: `412317240384`

## 🔗 2단계: 봇을 서버에 초대

### 2.1 OAuth2 URL 생성

1. 왼쪽 메뉴에서 **"OAuth2" → "URL Generator"** 선택
2. **SCOPES** 섹션에서 체크:
   - ✅ `bot`

3. **BOT PERMISSIONS** 섹션에서 체크:
   - ✅ View Channels
   - ✅ Send Messages
   - ✅ Read Message History
   - ✅ Embed Links
   - ✅ Attach Files
   - ✅ Add Reactions

4. 하단에 생성된 URL 복사

### 2.2 직접 사용 가능한 초대 URL

```
https://discord.com/api/oauth2/authorize?client_id=1432278641655681054&permissions=412317240384&scope=bot
```

위 링크로 접속하여:
1. 봇을 추가할 서버 선택
2. 권한 확인 후 "승인" 클릭

## 🎯 3단계: 채널별 접근 제한 (선택사항)

봇이 특정 채널에만 접근하도록 제한하려면:

### 방법 1: 채널 권한으로 제한 (추천)

1. Discord 서버에서 **01-archive** 채널 설정 열기
2. **"권한"** 탭 선택
3. **"고급 권한"** 클릭
4. 봇 역할 또는 @everyone 찾기
5. 봇에게만 다음 권한 허용:
   - ✅ 채널 보기
   - ✅ 메시지 전송
   - ✅ 메시지 기록 보기
   - ✅ 링크 임베드
   - ✅ 첨부 파일

6. **02-agent-reference** 채널에도 동일하게 적용

7. **다른 채널들**에는:
   - ❌ "채널 보기" 권한 제거

### 방법 2: 역할 기반 제한

1. 서버 설정 → 역할
2. 봇 전용 역할 생성 (예: "YouTube Bot")
3. 기본 권한을 최소화
4. 특정 채널에서만 권한 부여

### 방법 3: 코드로 제한 (현재 구현됨)

[config/channel_config.json](config/channel_config.json)에서 `channel_id` 설정:

```json
{
  "channels": {
    "01-archive": {
      "channel_id": 960907092439478374
    },
    "02-agent-reference": {
      "channel_id": 1432206876635824148
    }
  },
  "blocked_channels": [
    1425020218182467665
  ]
}
```

봇은 설정된 채널에서만 작동합니다.

## 🧪 4단계: 테스트

### 4.1 봇 실행

```bash
python3 main.py
```

### 4.2 Discord에서 테스트

1. **01-archive** 또는 **02-agent-reference** 채널로 이동
2. YouTube 링크 전송:
   ```
   https://www.youtube.com/watch?v=dQw4w9WgXcQ
   ```

3. 봇이 자동으로:
   - 🎬 영상 감지
   - 📊 정보 수집
   - 📝 자막 추출
   - 🤖 AI 요약
   - 💾 Notion 저장
   - ✅ 완료 메시지 전송

## 🔍 문제 해결

### 봇이 메시지를 읽지 못함
→ **MESSAGE CONTENT INTENT** 활성화 확인

### 봇이 응답하지 않음
→ 채널 권한 확인 (View Channels, Send Messages)

### "Missing Permissions" 오류
→ Bot Permissions에서 필수 권한 체크

### 특정 채널에서만 작동 안 함
→ [config/channel_config.json](config/channel_config.json)에서 `channel_id` 확인

## 📊 현재 설정된 채널

| 채널 이름 | 채널 ID | 용도 |
|----------|---------|------|
| 01-archive | 960907092439478374 | 텍스트 정제/아카이브 |
| 02-agent-reference | 1432206876635824148 | AI 에이전트 참고자료 |

## 🚀 다음 단계

1. ✅ 봇 토큰 업데이트 완료
2. ⏳ MESSAGE CONTENT INTENT 활성화
3. ⏳ 봇을 서버에 초대
4. ⏳ 채널 권한 설정
5. ⏳ 테스트 실행

---

**완료되면 Discord 채널에 YouTube 링크를 올려서 테스트하세요!** 🎉
