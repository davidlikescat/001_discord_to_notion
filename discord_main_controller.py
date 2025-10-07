import discord
import os
import asyncio
import subprocess
import logging
from dotenv import load_dotenv

# 🔇 Discord.py 로깅 레벨 조정 (경고 숨김)
logging.getLogger('discord').setLevel(logging.ERROR)
logging.getLogger('discord.client').setLevel(logging.ERROR)
logging.getLogger('discord.gateway').setLevel(logging.ERROR)

# 환경 변수 로드
load_dotenv()

# 🔧 수정된 import 구문들 (실제 클래스명에 맞춤)
from discord_sub_1 import YouTubeDetector
from discord_sub_2 import YouTubeInfoExtractor  
from discord_sub_3 import SubtitleExtractor  # ✅ 실제 클래스명
from discord_sub_4 import GeminiSummarizer    # ✅ 실제 클래스명  
from discord_sub_5 import NotionSaver         # ✅ 실제 클래스명

def get_secret_from_gcp(secret_name, project_id="n8n-ai-work-agent-automation"):
    """
    GCP Secret Manager에서 비밀값 가져오기
    로컬 .env 파일이 없거나 실패할 경우 GCP에서 직접 읽기
    """
    try:
        # 먼저 환경변수에서 시도
        env_value = os.getenv(secret_name.upper())
        if env_value:
            print(f"✅ {secret_name}: 환경변수에서 읽기 성공")
            return env_value
        
        # 환경변수가 없으면 GCP Secret Manager에서 읽기
        print(f"🔍 {secret_name}: GCP Secret Manager에서 읽는 중...")
        
        # Secret Manager에서 비밀값 가져오기
        secret_mapping = {
            'DISCORD_BOT_TOKEN': 'discord-bot-token',
            'YOUTUBE_API_KEY': 'youtube-api-key',
            'GEMINI_API_KEY': 'gemini-api-key',
            'NOTION_API_KEY': 'notion-api-key',
            'NOTION_DATABASE_ID': 'notion-database-id'
        }
        
        gcp_secret_name = secret_mapping.get(secret_name.upper())
        if not gcp_secret_name:
            print(f"❌ {secret_name}: 매핑되지 않은 시크릿")
            return None
        
        # gcloud 명령어로 시크릿 읽기
        result = subprocess.run([
            'gcloud', 'secrets', 'versions', 'access', 'latest',
            f'--secret={gcp_secret_name}',
            f'--project={project_id}'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            secret_value = result.stdout.strip()
            if secret_value:
                print(f"✅ {secret_name}: GCP Secret Manager에서 읽기 성공")
                # 환경변수로도 설정 (이후 사용을 위해)
                os.environ[secret_name.upper()] = secret_value
                return secret_value
        
        print(f"❌ {secret_name}: GCP Secret Manager 읽기 실패")
        print(f"   gcloud 오류: {result.stderr}")
        return None
        
    except subprocess.TimeoutExpired:
        print(f"❌ {secret_name}: GCP 읽기 시간초과")
        return None
    except Exception as e:
        print(f"❌ {secret_name}: GCP 읽기 오류 - {e}")
        return None

def load_all_secrets():
    """모든 필요한 시크릿을 로드"""
    print("🔐 API 키 로딩 중...")
    
    secrets = [
        'DISCORD_BOT_TOKEN',
        'YOUTUBE_API_KEY', 
        'GEMINI_API_KEY',
        'NOTION_API_KEY',
        'NOTION_DATABASE_ID'
    ]
    
    loaded_secrets = {}
    failed_secrets = []
    
    for secret in secrets:
        value = get_secret_from_gcp(secret)
        if value:
            loaded_secrets[secret] = value
        else:
            failed_secrets.append(secret)
    
    if failed_secrets:
        print(f"⚠️ 로딩 실패한 시크릿: {', '.join(failed_secrets)}")
        return False, loaded_secrets
    
    print("✅ 모든 시크릿 로딩 완료")
    return True, loaded_secrets

# 봇 설정 - 🔇 로깅 레벨 조정
intents = discord.Intents.default()
intents.message_content = True

# Discord 클라이언트 생성시 로깅 비활성화
client = discord.Client(intents=intents, enable_debug_events=False)

class DiscordWorkflowManager:
    def __init__(self):
        # 각 서브 모듈 인스턴스 생성
        self.youtube_detector = YouTubeDetector()
        self.info_extractor = YouTubeInfoExtractor()
        self.subtitle_extractor = SubtitleExtractor()  # ✅ 수정된 이름
        self.summarizer = GeminiSummarizer()
        self.notion_saver = NotionSaver()
        
        # 🔥 중복 처리 방지를 위한 캐시
        self.processing_videos = set()  # 현재 처리 중인 video_id들
        
        # 워크플로우 상태 관리
        self.workflow_steps = [
            "🎬 영상 감지",
            "📊 영상 정보 수집", 
            "📝 자막 추출",
            "🤖 AI 요약 생성",
            "💾 노션 저장"
        ]
        
        print("🚀 DiscordWorkflowManager 초기화 완료")
        self._check_module_status()
    
    def _check_module_status(self):
        """각 모듈의 상태 확인"""
        print("🔍 모듈 상태 확인:")
        print(f"   YouTubeDetector: ✅")
        print(f"   YouTubeInfoExtractor: {'✅' if self.info_extractor.api_key else '❌ YouTube API 키 없음'}")
        print(f"   SubtitleExtractor: ✅") 
        print(f"   GeminiSummarizer: {'✅' if self.summarizer.model else '❌ Gemini 모델 없음'}")
        print(f"   NotionSaver: {'✅' if self.notion_saver.api_key and self.notion_saver.database_id else '❌ Notion 설정 없음'}")
    
    async def process_youtube_workflow(self, message, video_id):
        """유튜브 영상 처리 워크플로우 실행"""
        
        # 🔥 중복 처리 방지
        if video_id in self.processing_videos:
            print(f"⏸️ 이미 처리 중인 영상: {video_id}")
            return False
        
        # 처리 중 목록에 추가
        self.processing_videos.add(video_id)
        
        processing_msg = None
        
        try:
            # Step 1: 초기 메시지
            processing_msg = await message.channel.send(
                f"🎬 영상을 분석 중입니다... `{video_id}`"
            )
            
            # Step 2: 영상 정보 추출
            await processing_msg.edit(content="📊 영상 정보를 수집하고 있습니다...")
            video_info = await self.run_step_2(video_id, processing_msg)
            if not video_info:
                return False
            
            # Step 3: 자막 추출 ✅ 수정된 메서드 호출
            await processing_msg.edit(content="📝 자막을 추출하고 있습니다...")
            transcript, transcript_source = await self.run_step_3(video_id, video_info, processing_msg)
            
            # 자막 추출 실패 시 처리
            if not transcript:
                # 영상 설명을 대체 자막으로 시도
                description = video_info.get('description', '')
                if description and len(description) > 100:  # 최소 길이 확인
                    print("ℹ️ 자막 대신 영상 설명 사용")
                    transcript = description
                    transcript_source = "description"
                else:
                    await processing_msg.edit(content="❌ 자막 추출에 실패했습니다. 영상 설명도 충분하지 않습니다.")
                    return False
            
            # Step 4: AI 요약
            await processing_msg.edit(content="🤖 AI가 영상을 요약하고 있습니다...")
            summary = await self.run_step_4(video_info, transcript, transcript_source, processing_msg)
            if not summary:
                return False
            
            # Step 5: 노션 저장
            await processing_msg.edit(content="💾 노션에 저장하고 있습니다...")
            notion_url = await self.run_step_5(video_info, summary, video_id, message, transcript_source, processing_msg)
            if not notion_url:
                return False
            
            # Step 6: 완료 메시지
            await self.send_completion_message(processing_msg, video_info, notion_url, transcript_source)
            return True
            
        except Exception as e:
            error_msg = f"❌ 워크플로우 실행 중 오류 발생: {str(e)}"
            print(error_msg)
            if processing_msg:
                await processing_msg.edit(content=error_msg)
            return False
        
        finally:
            # 🔥 처리 완료 후 목록에서 제거
            self.processing_videos.discard(video_id)
            print(f"🏁 워크플로우 정리 완료: {video_id}")
    
    async def run_step_2(self, video_id, processing_msg):
        """Step 2: 영상 정보 추출"""
        try:
            # ✅ 동기 함수를 비동기 환경에서 실행
            video_info = await asyncio.to_thread(self.info_extractor.get_video_info, video_id)
            
            if video_info:
                print(f"✅ Step 2 성공: {video_info['title']}")
                return video_info
            else:
                await processing_msg.edit(content="❌ 영상 정보를 가져올 수 없습니다.")
                print("❌ Step 2 실패: 영상 정보 없음")
                return None
        except Exception as e:
            error_msg = f"❌ Step 2 오류: {str(e)}"
            print(error_msg)
            await processing_msg.edit(content="❌ 영상 정보 추출 중 오류가 발생했습니다.")
            return None
    
    async def run_step_3(self, video_id, video_info, processing_msg):
        """Step 3: 자막 추출 - ✅ SubtitleExtractor 메서드에 맞춤"""
        try:
            # video_id로부터 유튜브 URL 생성
            youtube_url = f"https://www.youtube.com/watch?v={video_id}"
            
            # ✅ SubtitleExtractor의 실제 메서드 사용
            transcript = await asyncio.to_thread(
                self.subtitle_extractor.extract_subtitle_text, 
                youtube_url
            )
            
            # 자막 내용 확인
            if transcript and len(transcript) > 100:  # 최소 100자 이상 있는지 확인
                # 자막 소스 가져오기 (SubtitleExtractor 인스턴스에서)
                source = getattr(self.subtitle_extractor, 'subtitle_source', 'yt_dlp_auto_ko')
                
                print(f"✅ Step 3 성공: {len(transcript)} 글자")
                return transcript, source
            else:
                # 자막 길이가 너무 짧은 경우
                if transcript:
                    print(f"⚠️ Step 3 경고: 자막이 너무 짧습니다 ({len(transcript)} 글자)")
                else:
                    print("❌ Step 3 실패: 자막 추출 불가")
                    
                await processing_msg.edit(content="⚠️ 자막이 없거나 너무 짧습니다. 영상 설명을 확인 중...")
                
                # 영상 설명 확인
                description = video_info.get('description', '')
                if description and len(description) > 100:
                    print(f"ℹ️ 영상 설명 사용: {len(description)} 글자")
                    return description, "description"
                
                # 그래도 없으면 실패
                await processing_msg.edit(content="❌ 자막을 추출할 수 없습니다.")
                return None, None
                
        except Exception as e:
            error_msg = f"❌ Step 3 오류: {str(e)}"
            print(error_msg)
            # 스택 트레이스 출력
            import traceback
            traceback.print_exc()
            
            await processing_msg.edit(content="❌ 자막 추출 중 오류가 발생했습니다.")
            return None, None
    
    async def run_step_4(self, video_info, transcript, transcript_source, processing_msg):
        """Step 4: AI 요약"""
        try:
            # ✅ 이미 비동기 메서드임
            summary = await self.summarizer.summarize_with_gemini(
                video_info, transcript, transcript_source
            )
            
            if summary and "오류가 발생했습니다" not in summary:
                print(f"✅ Step 4 성공: {len(summary)} 글자 요약 생성")
                return summary
            else:
                await processing_msg.edit(content="❌ AI 요약 생성에 실패했습니다.")
                print("❌ Step 4 실패: 요약 생성 불가")
                return None
        except Exception as e:
            error_msg = f"❌ Step 4 오류: {str(e)}"
            print(error_msg)
            await processing_msg.edit(content="❌ AI 요약 중 오류가 발생했습니다.")
            return None
    
    async def run_step_5(self, video_info, summary, video_id, message, transcript_source, processing_msg):
        """Step 5: 노션 저장"""
        try:
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            discord_info = {
                'channel': message.channel.name,
                'author': message.author.display_name
            }
            
            # ✅ 이미 비동기 메서드임
            notion_url = await self.notion_saver.save_to_notion(
                video_info, summary, video_url, discord_info, transcript_source
            )
            
            if notion_url:
                print(f"✅ Step 5 성공: 노션 저장 완료")
                return notion_url
            else:
                await processing_msg.edit(content="❌ 노션 저장에 실패했습니다.")
                print("❌ Step 5 실패: 노션 저장 불가")
                return None
        except Exception as e:
            error_msg = f"❌ Step 5 오류: {str(e)}"
            print(error_msg)
            await processing_msg.edit(content="❌ 노션 저장 중 오류가 발생했습니다.")
            return None
    
    async def send_completion_message(self, processing_msg, video_info, notion_url, transcript_source):
        """완료 메시지 전송 - ✅ 자막 소스 매핑 수정"""
        try:
            source_info = {
                "yt_dlp_manual_ko": "수동 한국어 자막", 
                "yt_dlp_manual_en": "수동 영어 자막",
                "yt_dlp_auto_ko": "자동 한국어 자막",
                "yt_dlp_auto_en": "자동 영어 자막", 
                "whisper_api": "AI 음성인식",
                "description": "영상 설명란"
            }
            
            embed = discord.Embed(
                title="✅ 영상 요약 완료!",
                description=f"**{video_info['title']}**",
                color=0x00ff00
            )
            embed.add_field(name="📺 채널", value=video_info['channel'], inline=True)
            embed.add_field(name="⏱️ 길이", value=video_info['duration'], inline=True)
            
            # ✅ 안전한 숫자 변환
            try:
                view_count = int(video_info.get('view_count', 0))
                embed.add_field(name="👀 조회수", value=f"{view_count:,}회", inline=True)
            except (ValueError, TypeError):
                embed.add_field(name="👀 조회수", value="정보 없음", inline=True)
            
            embed.add_field(name="📝 자막 소스", value=source_info.get(transcript_source, "알 수 없음"), inline=True)
            embed.add_field(name="📄 노션 페이지", value=f"[바로가기]({notion_url})", inline=False)
            
            # ✅ 썸네일 안전하게 설정
            thumbnail_url = video_info.get('thumbnail', '')
            if thumbnail_url:
                embed.set_thumbnail(url=thumbnail_url)
            
            await processing_msg.edit(content="", embed=embed)
            print("✅ 워크플로우 완료!")
            
        except Exception as e:
            print(f"❌ 완료 메시지 전송 오류: {e}")
            # 오류 발생시 간단한 텍스트 메시지로 대체
            await processing_msg.edit(content=f"✅ 요약 완료! 노션 페이지: {notion_url}")

# 워크플로우 매니저 (환경 설정 이후에 초기화)
workflow_manager = None

def extract_all_text_from_message(message):
    """메시지에서 모든 텍스트 추출 (content + embeds + attachments)"""
    all_text = []
    
    # 1. 기본 메시지 내용
    if message.content:
        all_text.append(message.content)
        print(f"📝 메시지 content: {message.content}")
    
    # 2. Embed 내용 검사 (forwarded 메시지 등)
    if message.embeds:
        print(f"🔗 Embed 발견: {len(message.embeds)}개")
        for i, embed in enumerate(message.embeds):
            print(f"   Embed {i+1}:")
            
            # embed.url (주요!)
            if embed.url:
                all_text.append(embed.url)
                print(f"      URL: {embed.url}")
            
            # embed.title
            if embed.title:
                all_text.append(embed.title)
                print(f"      Title: {embed.title}")
            
            # embed.description
            if embed.description:
                all_text.append(embed.description)
                print(f"      Description: {embed.description}")
            
            # embed.fields
            if embed.fields:
                for field in embed.fields:
                    if field.value:
                        all_text.append(field.value)
                        print(f"      Field: {field.value}")
            
            # embed.footer
            if embed.footer and embed.footer.text:
                all_text.append(embed.footer.text)
                print(f"      Footer: {embed.footer.text}")
            
            # embed.author
            if embed.author and embed.author.name:
                all_text.append(embed.author.name)
                print(f"      Author: {embed.author.name}")
    
    # 3. 첨부파일 검사 (URL이 포함될 수 있음)
    if message.attachments:
        print(f"📎 첨부파일 발견: {len(message.attachments)}개")
        for attachment in message.attachments:
            if attachment.url:
                all_text.append(attachment.url)
                print(f"      첨부파일 URL: {attachment.url}")
            if attachment.filename:
                all_text.append(attachment.filename)
                print(f"      파일명: {attachment.filename}")
    
    # 4. 메시지 참조 (reply) 검사
    if message.reference and message.reference.resolved:
        ref_message = message.reference.resolved
        print(f"💬 참조 메시지 발견")
        if ref_message.content:
            all_text.append(ref_message.content)
            print(f"      참조 내용: {ref_message.content}")
    
    combined_text = " ".join(all_text)
    print(f"🔍 총 추출된 텍스트: {combined_text}")
    
    return combined_text

@client.event
async def on_ready():
    print(f'🤖 {client.user}가 로그인했습니다!')
    print(f'📦 디스코드 버전: {discord.__version__}')
    print("="*60)
    print("🔧 모듈별 기능:")
    print("1. discord_sub_1.py - 유튜브 링크 감지 (숏츠 지원)")
    print("2. discord_sub_2.py - 영상 정보 추출")
    print("3. discord_sub_3.py - 자막 추출 (yt-dlp)")
    print("4. discord_sub_4.py - AI 요약 생성 (Gemini)") 
    print("5. discord_sub_5.py - 노션 저장")
    print("🔗 지원하는 URL:")
    print("   - 일반 유튜브: youtube.com/watch?v=..., youtu.be/...")
    print("   - 유튜브 숏츠: youtube.com/shorts/...")
    print("   - Embed/Forward 메시지 지원")
    print("="*60)

@client.event
async def on_message(message):
    # 🔍 디버깅: 모든 메시지 감지 확인
    print(f"\n📩 메시지 감지됨!")
    print(f"   작성자: {message.author}")
    print(f"   채널: {message.channel.name}")
    print(f"   메시지 타입: {message.type}")
    
    # 봇 자신의 메시지는 무시
    if message.author == client.user:
        print("🤖 봇 자신의 메시지이므로 무시")
        return
    
    print(f"✅ 사용자 메시지 처리 중...")
    
    try:
        # 🔥 메시지에서 모든 텍스트 추출 (content + embeds + attachments)
        all_text = extract_all_text_from_message(message)
        
        if not all_text.strip():
            print("❌ 추출된 텍스트가 없음")
            return
        
        if workflow_manager is None:
            print("❌ 워크플로우 매니저가 아직 초기화되지 않았습니다.")
            return

        # Step 1: 유튜브 링크 감지 (숏츠 포함)
        youtube_urls = workflow_manager.youtube_detector.detect_youtube_urls(all_text)
        
        if youtube_urls:
            print(f"🎬 유튜브 링크 감지: {len(youtube_urls)}개")
            
            # 🔥 중복 제거: 동일한 video_id가 여러 개 감지될 수 있음
            unique_video_ids = list(set(youtube_urls))
            
            if len(unique_video_ids) != len(youtube_urls):
                print(f"🔄 중복 video_id 제거: {len(youtube_urls)} → {len(unique_video_ids)}")
            
            for video_id in unique_video_ids:
                print(f"▶️ 워크플로우 시작: {video_id}")
                success = await workflow_manager.process_youtube_workflow(message, video_id)
                
                if success:
                    print(f"✅ 워크플로우 성공: {video_id}")
                else:
                    print(f"❌ 워크플로우 실패: {video_id}")
                    
                # 여러 영상이 있을 경우 잠시 대기
                if len(unique_video_ids) > 1:
                    await asyncio.sleep(3)
        else:
            print("❌ 유튜브 링크 없음")
    
    except Exception as e:
        print(f"❌ 메시지 처리 중 오류: {e}")
        try:
            await message.channel.send("❌ 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.")
        except:
            pass

def check_environment():
    """환경 변수 확인 - GCP Secret Manager 통합"""
    print("🔍 환경 변수 확인:")
    
    required_vars = [
        'DISCORD_BOT_TOKEN',
        'YOUTUBE_API_KEY', 
        'GEMINI_API_KEY',
        'NOTION_API_KEY',
        'NOTION_DATABASE_ID'
    ]
    
    success, loaded_secrets = load_all_secrets()
    
    if not success:
        print("⚠️ 일부 환경 변수가 누락되었습니다.")
        return False
    
    print("✅ 모든 환경 변수가 설정되었습니다.")
    return True

if __name__ == "__main__":
    print("🚀 Discord YouTube to Notion Bot 시작...")
    print("="*60)
    
    # 환경 변수 확인
    if not check_environment():
        print("❌ 환경 설정을 완료한 후 다시 실행해주세요.")
        exit(1)

    # 워크플로우 매니저를 환경 설정 이후에 초기화
    workflow_manager = DiscordWorkflowManager()

    # Discord 토큰 확인 (GCP에서 읽기)
    DISCORD_TOKEN = get_secret_from_gcp('DISCORD_BOT_TOKEN')
    if not DISCORD_TOKEN:
        print("❌ DISCORD_BOT_TOKEN을 가져올 수 없습니다.")
        exit(1)
    
    print("🔌 Discord 봇 연결 중...")
    
    # 🔇 Discord.py 내부 경고 메시지 억제
    try:
        # 경고 메시지를 숨기고 봇 실행
        client.run(DISCORD_TOKEN, log_handler=None)
    except Exception as e:
        print(f"❌ 봇 실행 실패: {e}")
        exit(1)
