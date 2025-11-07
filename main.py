"""
YouTube Summarizer - Cloud Functions Worker

Cloud Scheduler에서 1분마다 호출됨
Supabase에서 pending 작업을 가져와서 처리

배포:
gcloud functions deploy process-youtube-jobs \
  --gen2 \
  --runtime=python311 \
  --region=asia-northeast3 \
  --source=. \
  --entry-point=process_pending_jobs \
  --trigger-http \
  --allow-unauthenticated \
  --memory=512MB \
  --timeout=540s
"""

import os
import json
import requests
import functions_framework
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

# 환경변수 로드
load_dotenv()

# Core 모듈
from core.youtube_info import YouTubeInfoExtractor
from core.subtitle_extractor import SubtitleExtractor
from core.ai_summarizer import GeminiSummarizer, ClaudeSummarizer
from core.notion_saver import NotionSaver

# Supabase 클라이언트
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY')

if supabase_url and supabase_key:
    supabase: Client = create_client(supabase_url, supabase_key)
else:
    print("⚠️ Supabase 환경변수가 설정되지 않았습니다.")
    supabase = None


@functions_framework.http
def process_pending_jobs(request):
    """
    Cloud Scheduler에서 호출되는 메인 함수
    """
    try:
        if not supabase:
            return 'Supabase not configured', 500

        # 1. Pending 작업 가져오기 (최대 5개)
        response = supabase.table('jobs') \
            .select('*') \
            .eq('status', 'pending') \
            .order('created_at') \
            .limit(5) \
            .execute()

        jobs = response.data

        if not jobs:
            print("✅ 처리할 작업이 없습니다.")
            return 'No pending jobs', 200

        print(f"🔄 처리할 작업: {len(jobs)}개")

        # 2. 각 작업 처리
        for job in jobs:
            process_single_job(job)

        return f'Processed {len(jobs)} jobs', 200

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return f'Error: {str(e)}', 500


def process_single_job(job: dict):
    """
    단일 작업 처리
    """
    job_id = job['id']
    youtube_url = job['youtube_url']
    chat_id = job['telegram_chat_id']
    channel = job['channel']

    print(f"\n{'='*60}")
    print(f"[{job_id}] 작업 시작")
    print(f"URL: {youtube_url}")
    print(f"Channel: {channel}")
    print(f"{'='*60}")

    try:
        # 상태 업데이트: processing
        supabase.table('jobs').update({
            'status': 'processing',
            'started_at': datetime.utcnow().isoformat()
        }).eq('id', job_id).execute()

        # Step 1: YouTube 정보 추출
        print(f"[{job_id}] Step 1/4: YouTube 정보 추출...")
        info_extractor = YouTubeInfoExtractor()
        video_id = info_extractor.extract_video_id(youtube_url)

        if not video_id:
            raise Exception("YouTube URL에서 video_id를 추출할 수 없습니다.")

        video_info = info_extractor.get_video_info(video_id)

        if not video_info:
            raise Exception("YouTube 영상 정보를 가져올 수 없습니다.")

        print(f"✅ 제목: {video_info['title']}")
        print(f"✅ 채널: {video_info['channel']}")
        print(f"✅ 길이: {video_info['duration']}")

        # Step 2: 자막 추출
        print(f"\n[{job_id}] Step 2/4: 자막 추출...")
        subtitle_extractor = SubtitleExtractor()
        transcript, source = subtitle_extractor.extract_subtitle_text(youtube_url, video_id)

        if not transcript:
            raise Exception("자막을 추출할 수 없습니다. 자막이 없는 영상일 수 있습니다.")

        print(f"✅ 자막 추출 완료: {len(transcript)} 글자 (source: {source})")

        # Step 3: AI 요약
        print(f"\n[{job_id}] Step 3/4: AI 요약 생성...")

        # Gemini 우선 시도 (무료)
        try:
            summarizer = GeminiSummarizer()
            summary = summarizer.summarize(video_info, transcript, channel)

            if "오류" in summary or "❌" in summary:
                raise Exception("Gemini 요약 실패")

            print(f"✅ Gemini 요약 완료: {len(summary)} 글자")

        except Exception as gemini_error:
            print(f"⚠️ Gemini 실패, Claude Haiku로 전환: {gemini_error}")

            # Claude Haiku 백업 (유료지만 저렴)
            claude_summarizer = ClaudeSummarizer(model_name='claude-3-haiku-20240307')
            summary = claude_summarizer.summarize(
                video_info,
                transcript,
                channel,
                max_tokens=2048
            )

            if "오류" in summary or "❌" in summary:
                raise Exception("AI 요약에 실패했습니다.")

            print(f"✅ Claude 요약 완료: {len(summary)} 글자")

        # Step 4: Notion 저장
        print(f"\n[{job_id}] Step 4/4: Notion 저장...")
        notion_saver = NotionSaver()

        # 채널별 Notion Database ID
        database_ids = {
            'archive': os.getenv('NOTION_DATABASE_ID_ARCHIVE'),
            'agent-reference': os.getenv('NOTION_DATABASE_ID_AGENT_REF')
        }

        database_id = database_ids.get(channel)

        if not database_id:
            raise Exception(f"채널 '{channel}'의 Notion Database ID가 설정되지 않았습니다.")

        notion_url = notion_saver.save_to_notion(
            video_info,
            summary,
            youtube_url,
            database_id,
            channel
        )

        if not notion_url:
            raise Exception("Notion 저장에 실패했습니다.")

        print(f"✅ Notion 저장 완료: {notion_url}")

        # Step 5: 상태 업데이트 & Telegram 알림
        print(f"\n[{job_id}] Step 5/4: 완료 처리...")

        supabase.table('jobs').update({
            'status': 'completed',
            'completed_at': datetime.utcnow().isoformat(),
            'result': {
                'notion_url': notion_url,
                'summary_length': len(summary),
                'transcript_source': source
            }
        }).eq('id', job_id).execute()

        send_telegram_success(chat_id, video_info, notion_url, channel)

        print(f"✅ [{job_id}] 작업 완료!\n")

    except Exception as e:
        print(f"❌ [{job_id}] 오류 발생: {e}")
        import traceback
        traceback.print_exc()

        # 상태 업데이트: failed
        supabase.table('jobs').update({
            'status': 'failed',
            'completed_at': datetime.utcnow().isoformat(),
            'error_message': str(e)
        }).eq('id', job_id).execute()

        send_telegram_error(chat_id, str(e))


def send_telegram_success(chat_id: int, video_info: dict, notion_url: str, channel: str):
    """Telegram 성공 알림"""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        return

    channel_names = {
        'archive': '📚 Archive',
        'agent-reference': '🤖 Agent Reference'
    }

    text = f"""✅ 요약 완료!

📺 제목: {video_info['title']}
📍 채널: {video_info['channel']}
⏱️ 길이: {video_info['duration']}
🗂️ 분류: {channel_names.get(channel, channel)}

📄 Notion: {notion_url}
"""

    try:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={
                'chat_id': chat_id,
                'text': text,
                'parse_mode': 'HTML',
                'reply_markup': {
                    'inline_keyboard': [[
                        {
                            'text': '📄 Notion 열기',
                            'url': notion_url
                        }
                    ]]
                }
            },
            timeout=10
        )
        print(f"✅ Telegram 알림 전송 완료")
    except Exception as e:
        print(f"⚠️ Telegram 알림 전송 실패: {e}")


def send_telegram_error(chat_id: int, error_message: str):
    """Telegram 오류 알림"""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        return

    text = f"""❌ 요약 실패

오류 내용:
{error_message}

💡 다시 시도하시거나 다른 영상을 보내주세요."""

    try:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={
                'chat_id': chat_id,
                'text': text
            },
            timeout=10
        )
        print(f"✅ Telegram 오류 알림 전송 완료")
    except Exception as e:
        print(f"⚠️ Telegram 오류 알림 전송 실패: {e}")


if __name__ == '__main__':
    # 로컬 테스트
    print("🧪 로컬 테스트 모드")

    # Mock request
    class MockRequest:
        pass

    result = process_pending_jobs(MockRequest())
    print(f"\n결과: {result}")
