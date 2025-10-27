"""
Claude API 기반 AI 요약 생성 모듈
채널별 시스템 프롬프트를 적용하여 맞춤형 요약 제공
"""

import os
import asyncio
from typing import Dict, Optional
from anthropic import Anthropic
from dotenv import load_dotenv
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.prompts import get_system_prompt, get_user_prompt

# 환경 변수 로드
load_dotenv()


class ClaudeSummarizer:
    """
    Claude API를 사용한 영상 요약 생성
    채널별 시스템 프롬프트 지원
    """

    def __init__(self, model_name: str = "claude-3-7-sonnet-20250219"):
        """
        Args:
            model_name (str): Claude 모델명
                - claude-3-7-sonnet-20250219 (추천, 유료)
                - claude-3-5-sonnet-20241022 (안정적)
                - claude-3-haiku-20240307 (빠르고 저렴)
        """
        self.api_key = os.getenv('ANTHROPIC_API_KEY') or os.getenv('CLAUDE_API_KEY')

        if not self.api_key:
            print("⚠️ Claude API 키가 설정되지 않았습니다.")
            print("💡 .env 파일에 ANTHROPIC_API_KEY 또는 CLAUDE_API_KEY를 추가해주세요.")
            self.client = None
            return

        try:
            self.client = Anthropic(api_key=self.api_key)
            self.model_name = model_name
            print(f"🤖 ClaudeSummarizer 초기화 완료 (모델: {model_name})")

        except Exception as e:
            print(f"❌ Claude API 초기화 실패: {e}")
            self.client = None

    async def summarize_with_claude(
        self,
        video_info: Dict,
        transcript: str,
        prompt_key: str,
        max_tokens: int = 4096
    ) -> str:
        """
        Claude API로 영상 요약 생성

        Args:
            video_info (Dict): 비디오 정보
            transcript (str): 자막 텍스트
            prompt_key (str): 프롬프트 키 ('archive' 또는 'agent_references')
            max_tokens (int): 최대 응답 토큰 수

        Returns:
            str: 요약 결과
        """
        try:
            print(f"🤖 AI 요약 생성 시작 (Claude)")
            print(f"   영상: {video_info.get('title', 'Unknown')}")
            print(f"   프롬프트 키: {prompt_key}")
            print(f"   자막 길이: {len(transcript)} 글자")

            if not self.client:
                return "❌ Claude API 클라이언트가 초기화되지 않았습니다."

            # 자막이 너무 긴 경우 자르기 (Claude의 컨텍스트 윈도우 고려)
            # Claude 3.7 Sonnet: 200K 토큰
            # 대략 1 토큰 = 4글자로 계산 → 최대 약 150,000 글자
            max_transcript_length = 150000
            if len(transcript) > max_transcript_length:
                transcript = transcript[:max_transcript_length] + "\n\n... (이하 생략)"
                print(f"   ⚠️ 자막 길이 조정: {max_transcript_length} 글자로 제한")

            # 시스템 프롬프트 가져오기
            system_prompt = get_system_prompt(prompt_key)

            # 사용자 프롬프트 생성
            video_info_with_url = video_info.copy()
            video_info_with_url['url'] = video_info.get('url', '')

            user_prompt = get_user_prompt(prompt_key, video_info_with_url, transcript)

            print("   🔄 Claude API 호출 중...")

            # Claude API 호출 (비동기)
            response = await asyncio.to_thread(
                self.client.messages.create,
                model=self.model_name,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ]
            )

            if response and response.content:
                # Claude의 응답은 list 형태
                summary = response.content[0].text.strip()
                print(f"✅ AI 요약 생성 성공: {len(summary)} 글자")
                print(f"   사용 토큰: input={response.usage.input_tokens}, output={response.usage.output_tokens}")
                return summary
            else:
                print("❌ AI 응답이 비어있음")
                return "요약 생성 중 오류가 발생했습니다."

        except Exception as e:
            error_msg = f"Claude 요약 실패: {e}"
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()
            return f"요약 생성 중 오류가 발생했습니다: {str(e)}"

    def test_connection(self) -> bool:
        """Claude API 연결 테스트"""
        try:
            print("🔗 Claude API 연결 테스트")

            if not self.client:
                print("❌ API 클라이언트가 초기화되지 않았습니다.")
                return False

            # 간단한 테스트 메시지
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=50,
                messages=[
                    {
                        "role": "user",
                        "content": "Hello! Please respond with just 'OK' to confirm the connection."
                    }
                ]
            )

            if response and response.content:
                print(f"✅ 연결 성공! 응답: {response.content[0].text}")
                return True
            else:
                print("❌ 응답이 비어있습니다.")
                return False

        except Exception as e:
            print(f"❌ 연결 테스트 실패: {e}")
            return False


# 테스트용 함수
async def test_claude_summarizer():
    """ClaudeSummarizer 테스트"""
    print("🧪 ClaudeSummarizer 테스트")
    print("=" * 60)

    # 1. 환경 변수 확인
    api_key = os.getenv('ANTHROPIC_API_KEY') or os.getenv('CLAUDE_API_KEY')
    if api_key:
        print(f"✅ API 키 발견 (길이: {len(api_key)})")
    else:
        print("❌ API 키 없음")
        print("💡 .env 파일에 다음 중 하나를 추가하세요:")
        print("   ANTHROPIC_API_KEY=your_api_key")
        print("   CLAUDE_API_KEY=your_api_key")
        return

    # 2. Summarizer 초기화
    # 테스트용으로 Haiku 모델 사용 (빠르고 저렴)
    summarizer = ClaudeSummarizer(model_name="claude-3-haiku-20240307")

    # 3. 연결 테스트
    connection_ok = summarizer.test_connection()
    if not connection_ok:
        print("❌ 연결 테스트 실패")
        return

    # 4. 요약 테스트
    print("\n📝 요약 생성 테스트")
    print("-" * 60)

    test_video_info = {
        'title': 'Python 프로그래밍 기초 강의',
        'channel': 'CodeLab Korea',
        'duration': '15분 30초',
        'url': 'https://www.youtube.com/watch?v=test123'
    }

    test_transcript = """
    안녕하세요. 오늘은 Python 프로그래밍의 기초에 대해 알아보겠습니다.

    먼저 변수에 대해 설명드리겠습니다. 변수는 데이터를 저장하는 공간입니다.
    Python에서는 변수를 선언할 때 특별한 키워드가 필요하지 않습니다.

    다음으로 함수에 대해 알아보겠습니다. 함수는 재사용 가능한 코드 블록입니다.
    def greet(name): return f"안녕하세요, {name}님!" 이런 식으로 정의할 수 있습니다.
    """

    # Archive 프롬프트로 테스트
    print("\n1️⃣ Archive 프롬프트 테스트:")
    summary1 = await summarizer.summarize_with_claude(
        test_video_info,
        test_transcript,
        "archive",
        max_tokens=1000
    )
    print(f"\n📄 생성된 요약:\n{summary1}\n")

    # Agent References 프롬프트로 테스트
    print("\n2️⃣ Agent References 프롬프트 테스트:")
    test_video_info['title'] = 'AI Agent 개발 가이드'
    test_transcript = """
    AI Agent를 개발할 때는 다음 사항을 고려해야 합니다.

    1. Agent의 목적을 명확히 정의합니다.
    2. LangChain 같은 프레임워크를 활용할 수 있습니다.
    3. 메모리 관리와 컨텍스트 유지가 중요합니다.
    """

    summary2 = await summarizer.summarize_with_claude(
        test_video_info,
        test_transcript,
        "agent_references",
        max_tokens=1000
    )
    print(f"\n📄 생성된 요약:\n{summary2}\n")

    print("\n" + "=" * 60)
    print("✅ 테스트 완료")


if __name__ == "__main__":
    asyncio.run(test_claude_summarizer())
