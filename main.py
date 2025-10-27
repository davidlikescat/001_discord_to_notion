"""
Discord YouTube to Notion Bot - 메인 컨트롤러
채널별 라우팅 및 워크플로우 관리
"""

import discord
import os
import asyncio
import json
import subprocess
import logging
from dotenv import load_dotenv
from typing import Dict, Optional

# 로깅 설정
logging.getLogger('discord').setLevel(logging.ERROR)
logging.getLogger('discord.client').setLevel(logging.ERROR)
logging.getLogger('discord.gateway').setLevel(logging.ERROR)

# 환경 변수 로드 (기존 환경변수 덮어쓰기)
load_dotenv(override=True)

# 코어 모듈 import
from core.youtube_detector import YouTubeDetector
from core.youtube_info import YouTubeInfoExtractor
from core.subtitle_extractor import SubtitleExtractor
from core.ai_summarizer import ClaudeSummarizer
from core.notion_saver import NotionSaver


def load_channel_config() -> Dict:
    """채널 설정 파일 로드"""
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'channel_config.json')

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print("✅ 채널 설정 파일 로드 완료")
        return config
    except Exception as e:
        print(f"❌ 채널 설정 파일 로드 실패: {e}")
        return {"channels": {}, "blocked_channels": []}


def get_secret_from_gcp(secret_name, project_id="n8n-ai-work-agent-automation"):
    """GCP Secret Manager에서 비밀값 가져오기"""
    try:
        # 먼저 환경변수에서 시도
        env_value = os.getenv(secret_name.upper())
        if env_value:
            print(f"✅ {secret_name}: 환경변수에서 읽기 성공")
            return env_value

        # 환경변수가 없으면 GCP Secret Manager에서 읽기
        print(f"🔍 {secret_name}: GCP Secret Manager에서 읽는 중...")

        secret_mapping = {
            'DISCORD_BOT_TOKEN': 'discord-bot-token',
            'YOUTUBE_API_KEY': 'youtube-api-key',
            'ANTHROPIC_API_KEY': 'claude-api-key',
            'NOTION_API_KEY': 'notion-api-key'
        }

        gcp_secret_name = secret_mapping.get(secret_name.upper())
        if not gcp_secret_name:
            return None

        result = subprocess.run([
            'gcloud', 'secrets', 'versions', 'access', 'latest',
            f'--secret={gcp_secret_name}',
            f'--project={project_id}'
        ], capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            secret_value = result.stdout.strip()
            if secret_value:
                print(f"✅ {secret_name}: GCP Secret Manager에서 읽기 성공")
                os.environ[secret_name.upper()] = secret_value
                return secret_value

        return None

    except Exception as e:
        print(f"❌ {secret_name}: GCP 읽기 오류 - {e}")
        return None


# Discord 봇 설정
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents, enable_debug_events=False)


class DiscordWorkflowManager:
    """
    디스코드 워크플로우 관리자
    채널별 설정에 따라 다른 처리 방식 적용
    """

    def __init__(self, channel_config: Dict):
        self.channel_config = channel_config
        self.channels = channel_config.get('channels', {})
        self.blocked_channels = channel_config.get('blocked_channels', [])

        # 공통 모듈 초기화
        self.youtube_detector = YouTubeDetector()
        self.info_extractor = YouTubeInfoExtractor()
        self.subtitle_extractor = SubtitleExtractor()
        self.notion_saver = NotionSaver()

        # 채널별 AI Summarizer (모델이 다를 수 있음)
        self.summarizers = {}

        # 중복 처리 방지
        self.processing_videos = set()

        print("🚀 DiscordWorkflowManager 초기화 완료")
        self._check_module_status()

    def _check_module_status(self):
        """모듈 상태 확인"""
        print("🔍 모듈 상태 확인:")
        print(f"   YouTubeDetector: ✅")
        print(f"   YouTubeInfoExtractor: {'✅' if self.info_extractor.api_key else '❌'}")
        print(f"   SubtitleExtractor: ✅")
        print(f"   NotionSaver: {'✅' if self.notion_saver.api_key else '❌'}")
        print(f"\n📋 설정된 채널:")
        for channel_key, config in self.channels.items():
            print(f"   - {channel_key}: {config.get('description', 'N/A')}")

    def get_channel_config_by_id(self, channel_id: int) -> Optional[Dict]:
        """Discord 채널 ID로 설정 찾기"""
        for channel_key, config in self.channels.items():
            if config.get('channel_id') == channel_id:
                return config
        return None

    def _get_or_create_summarizer(self, model_name: str) -> ClaudeSummarizer:
        """AI Summarizer 가져오기 (캐싱)"""
        if model_name not in self.summarizers:
            self.summarizers[model_name] = ClaudeSummarizer(model_name=model_name)
        return self.summarizers[model_name]

    async def process_youtube_workflow(self, message: discord.Message, video_id: str):
        """유튜브 영상 처리 워크플로우"""

        # 채널 설정 확인
        channel_config = self.get_channel_config_by_id(message.channel.id)

        if not channel_config:
            print(f"⚠️ 설정되지 않은 채널: {message.channel.name} (ID: {message.channel.id})")
            await message.channel.send(
                f"❌ 이 채널은 봇이 활성화되지 않았습니다.\n"
                f"💡 관리자에게 채널 ID `{message.channel.id}`를 config/channel_config.json에 추가하도록 요청하세요."
            )
            return False

        # 중복 처리 방지
        if video_id in self.processing_videos:
            print(f"⏸️ 이미 처리 중인 영상: {video_id}")
            return False

        self.processing_videos.add(video_id)

        processing_msg = None

        try:
            channel_name = channel_config.get('channel_name', 'unknown')
            print(f"\n{'='*60}")
            print(f"🎬 워크플로우 시작: {channel_name}")
            print(f"   영상 ID: {video_id}")
            print(f"{'='*60}")

            # Step 1: 초기 메시지
            processing_msg = await message.channel.send(
                f"🎬 **영상 분석 시작!**\n"
                f"📍 채널: {channel_name}\n"
                f"🆔 Video ID: `{video_id}`\n\n"
                f"**진행 상황:**\n"
                f"🔵⚪⚪⚪⚪ **Step 1/5**: 초기화 중..."
            )

            # Step 2: 영상 정보 추출
            await processing_msg.edit(
                content=f"🎬 **영상 분석 진행 중**\n"
                        f"📍 채널: {channel_name}\n\n"
                        f"**진행 상황:**\n"
                        f"🔵🔵⚪⚪⚪ **Step 2/5**: 영상 정보 수집 중...\n"
                        f"⏱️ YouTube API 호출 중..."
            )
            video_info = await self._run_step_2(video_id, processing_msg)
            if not video_info:
                return False

            video_url = f"https://www.youtube.com/watch?v={video_id}"
            video_info['url'] = video_url

            # Step 3: 자막 추출
            await processing_msg.edit(
                content=f"🎬 **영상 분석 진행 중**\n"
                        f"📺 제목: {video_info['title'][:50]}...\n"
                        f"⏱️ 길이: {video_info['duration']}\n\n"
                        f"**진행 상황:**\n"
                        f"🔵🔵🔵⚪⚪ **Step 3/5**: 자막 추출 중...\n"
                        f"🔍 youtube-transcript-api 시도 중..."
            )
            transcript, transcript_source = await self._run_step_3(
                video_url, video_id, video_info, processing_msg
            )

            if not transcript:
                await processing_msg.edit(content="❌ 자막 추출에 실패했습니다.")
                return False

            # Step 4: AI 요약
            await processing_msg.edit(
                content=f"🎬 **영상 분석 진행 중**\n"
                        f"📺 제목: {video_info['title'][:50]}...\n"
                        f"📝 자막: {len(transcript):,} 글자 추출 완료 ✅\n\n"
                        f"**진행 상황:**\n"
                        f"🔵🔵🔵🔵⚪ **Step 4/5**: AI 요약 생성 중...\n"
                        f"🤖 Claude AI 분석 중... (1-2분 소요)\n"
                        f"💡 프롬프트: {channel_config.get('system_prompt_key', 'default')}"
            )
            summary = await self._run_step_4(
                video_info, transcript, channel_config, processing_msg
            )
            if not summary:
                return False

            # Step 5: Notion 저장
            await processing_msg.edit(
                content=f"🎬 **영상 분석 거의 완료!**\n"
                        f"📺 제목: {video_info['title'][:50]}...\n"
                        f"📝 자막: {len(transcript):,} 글자 ✅\n"
                        f"🤖 AI 요약: {len(summary):,} 글자 ✅\n\n"
                        f"**진행 상황:**\n"
                        f"🔵🔵🔵🔵🔵 **Step 5/5**: Notion 저장 중...\n"
                        f"💾 데이터베이스에 업로드 중..."
            )
            discord_info = {
                'channel': message.channel.name,
                'author': message.author.display_name
            }

            notion_url = await self._run_step_5(
                video_info, summary, video_url, channel_config, discord_info, processing_msg
            )
            if not notion_url:
                return False

            # Step 6: 완료 메시지
            await self._send_completion_message(
                processing_msg, video_info, notion_url, transcript_source, channel_config
            )

            return True

        except Exception as e:
            error_msg = f"❌ 워크플로우 실행 중 오류 발생: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()

            if processing_msg:
                await processing_msg.edit(content=error_msg)
            return False

        finally:
            self.processing_videos.discard(video_id)
            print(f"🏁 워크플로우 정리 완료: {video_id}\n")

    async def _run_step_2(self, video_id: str, processing_msg) -> Optional[Dict]:
        """Step 2: 영상 정보 추출"""
        try:
            video_info = await asyncio.to_thread(
                self.info_extractor.get_video_info, video_id
            )

            if video_info:
                print(f"✅ Step 2 성공: {video_info['title']}")
                return video_info
            else:
                await processing_msg.edit(content="❌ 영상 정보를 가져올 수 없습니다.")
                return None

        except Exception as e:
            print(f"❌ Step 2 오류: {e}")
            await processing_msg.edit(content="❌ 영상 정보 추출 중 오류가 발생했습니다.")
            return None

    async def _run_step_3(
        self, youtube_url: str, video_id: str, video_info: Dict, processing_msg
    ) -> tuple:
        """Step 3: 자막 추출"""
        try:
            transcript, source = await asyncio.to_thread(
                self.subtitle_extractor.extract_subtitle_text, youtube_url, video_id
            )

            if transcript and len(transcript) > 100:
                print(f"✅ Step 3 성공: {len(transcript)} 글자 ({source})")
                return transcript, source
            else:
                # 자막이 없으면 실패 처리 (영상 설명은 사용하지 않음)
                print(f"❌ Step 3 실패: 자막을 찾을 수 없습니다 (source: {source})")
                await processing_msg.edit(
                    content="❌ 자막을 찾을 수 없습니다.\n"
                            "💡 자막이 있는 영상만 처리할 수 있습니다."
                )
                return None, None

        except Exception as e:
            print(f"❌ Step 3 오류: {e}")
            import traceback
            traceback.print_exc()
            return None, None

    async def _run_step_4(
        self, video_info: Dict, transcript: str, channel_config: Dict, processing_msg
    ) -> Optional[str]:
        """Step 4: AI 요약"""
        try:
            # AI 모델 가져오기
            model_name = channel_config.get('ai_model', 'claude-3-haiku-20240307')
            prompt_key = channel_config.get('system_prompt_key', 'archive')

            summarizer = self._get_or_create_summarizer(model_name)

            # 요약 생성
            summary = await summarizer.summarize_with_claude(
                video_info, transcript, prompt_key, max_tokens=8192
            )

            if summary and "오류가 발생했습니다" not in summary:
                print(f"✅ Step 4 성공: {len(summary)} 글자")
                return summary
            else:
                await processing_msg.edit(content="❌ AI 요약 생성에 실패했습니다.")
                return None

        except Exception as e:
            print(f"❌ Step 4 오류: {e}")
            await processing_msg.edit(content="❌ AI 요약 중 오류가 발생했습니다.")
            return None

    async def _run_step_5(
        self,
        video_info: Dict,
        summary: str,
        video_url: str,
        channel_config: Dict,
        discord_info: Dict,
        processing_msg
    ) -> Optional[str]:
        """Step 5: Notion 저장"""
        try:
            notion_url = await self.notion_saver.save_to_notion(
                video_info, summary, video_url, channel_config, discord_info
            )

            if notion_url:
                print(f"✅ Step 5 성공: Notion 저장 완료")
                return notion_url
            else:
                await processing_msg.edit(content="❌ Notion 저장에 실패했습니다.")
                return None

        except Exception as e:
            print(f"❌ Step 5 오류: {e}")
            await processing_msg.edit(content="❌ Notion 저장 중 오류가 발생했습니다.")
            return None

    async def _send_completion_message(
        self,
        processing_msg,
        video_info: Dict,
        notion_url: str,
        transcript_source: str,
        channel_config: Dict
    ):
        """완료 메시지 전송"""
        try:
            embed = discord.Embed(
                title="✅ 영상 분석 완료!",
                description=f"**{video_info['title']}**",
                color=0x00ff00
            )

            embed.add_field(
                name="📺 채널",
                value=video_info['channel'],
                inline=True
            )
            embed.add_field(
                name="⏱️ 길이",
                value=video_info['duration'],
                inline=True
            )
            embed.add_field(
                name="🤖 처리 방식",
                value=channel_config.get('channel_name', 'unknown'),
                inline=True
            )
            embed.add_field(
                name="📝 자막 소스",
                value=transcript_source,
                inline=True
            )
            embed.add_field(
                name="📄 Notion 페이지",
                value=f"[바로가기]({notion_url})",
                inline=False
            )

            # 썸네일 설정
            thumbnail_url = video_info.get('thumbnail', '')
            if thumbnail_url:
                embed.set_thumbnail(url=thumbnail_url)

            await processing_msg.edit(content="", embed=embed)
            print("✅ 완료 메시지 전송 성공")

        except Exception as e:
            print(f"❌ 완료 메시지 전송 오류: {e}")
            await processing_msg.edit(content=f"✅ 요약 완료! Notion: {notion_url}")


# 전역 변수
workflow_manager = None


def extract_all_text_from_message(message: discord.Message) -> str:
    """메시지에서 모든 텍스트 추출"""
    all_text = []

    # 1. 기본 메시지 내용
    if message.content:
        all_text.append(message.content)

    # 2. Embed 내용
    if message.embeds:
        for embed in message.embeds:
            if embed.url:
                all_text.append(embed.url)
            if embed.title:
                all_text.append(embed.title)
            if embed.description:
                all_text.append(embed.description)

    # 3. 첨부파일
    if message.attachments:
        for attachment in message.attachments:
            if attachment.url:
                all_text.append(attachment.url)

    # 4. 참조 메시지
    if message.reference and message.reference.resolved:
        ref_message = message.reference.resolved
        if ref_message.content:
            all_text.append(ref_message.content)

    return " ".join(all_text)


@client.event
async def on_ready():
    print(f'🤖 {client.user}가 로그인했습니다!')
    print(f'📦 Discord.py 버전: {discord.__version__}')
    print("="*60)


@client.event
async def on_message(message: discord.Message):
    # 봇 자신의 메시지는 무시
    if message.author == client.user:
        return

    # 차단된 채널 확인
    if message.channel.id in workflow_manager.blocked_channels:
        print(f"🚫 차단된 채널: {message.channel.name}")
        return

    try:
        # 메시지에서 텍스트 추출
        all_text = extract_all_text_from_message(message)

        if not all_text.strip():
            return

        # YouTube 링크 감지
        youtube_urls = workflow_manager.youtube_detector.detect_youtube_urls(all_text)

        if youtube_urls:
            print(f"🎬 YouTube 링크 감지: {len(youtube_urls)}개")

            # 중복 제거
            unique_video_ids = list(set(youtube_urls))

            for video_id in unique_video_ids:
                success = await workflow_manager.process_youtube_workflow(message, video_id)

                if success:
                    print(f"✅ 워크플로우 성공: {video_id}")
                else:
                    print(f"❌ 워크플로우 실패: {video_id}")

                # 여러 영상이 있으면 대기
                if len(unique_video_ids) > 1:
                    await asyncio.sleep(3)

    except Exception as e:
        print(f"❌ 메시지 처리 중 오류: {e}")
        import traceback
        traceback.print_exc()


def main():
    """메인 함수"""
    print("🚀 Discord YouTube to Notion Bot 시작...")
    print("="*60)

    # 1. 채널 설정 로드
    channel_config = load_channel_config()

    # 2. API 키 로드
    required_keys = [
        'DISCORD_BOT_TOKEN',
        'YOUTUBE_API_KEY',
        'ANTHROPIC_API_KEY',
        'NOTION_API_KEY'
    ]

    for key in required_keys:
        value = get_secret_from_gcp(key)
        if not value:
            print(f"⚠️ {key} 로드 실패")

    # 3. 워크플로우 매니저 초기화
    global workflow_manager
    workflow_manager = DiscordWorkflowManager(channel_config)

    # 4. Discord 봇 실행
    discord_token = get_secret_from_gcp('DISCORD_BOT_TOKEN')
    if not discord_token:
        print("❌ DISCORD_BOT_TOKEN을 가져올 수 없습니다.")
        return

    print("🔌 Discord 봇 연결 중...")

    try:
        client.run(discord_token, log_handler=None)
    except Exception as e:
        print(f"❌ 봇 실행 실패: {e}")


if __name__ == "__main__":
    main()
